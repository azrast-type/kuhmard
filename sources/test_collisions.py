"""Collision scan for Kuhmard: dots (and marks) that touch or crowd a neighbouring letter.

For every pair of letters in every joining situation they can meet in typed text,
shape the pair with HarfBuzz (kerning on, exactly as users see it) and measure the
smallest gap between
  - the dots of one letter and the other letter (body or dots),
  - for letters that are not joined: the two letters' bodies.
Joined letters touch at their joining stroke by design; that contact is ignored.

Run: python3 test_collisions.py [font.otf] [min_gap]
"""
import sys
import numpy as np
import pathops
import uharfbuzz as hb
from scipy import ndimage
from fontTools.ttLib import TTFont
from fontTools.pens.transformPen import TransformPen

FONT = next((a for a in sys.argv[1:] if a.endswith(".otf")), "otf/Kuhmard-Bold.otf")
MIN_GAP = float(next((a for a in sys.argv[1:] if a.replace(".", "").isdigit()), 40))
KR = 2                                             # font units per pixel

tt = gs = order = GCLASS = font = None


def load(path):
    global tt, gs, order, GCLASS, font, _cache
    tt = TTFont(path); gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
    GCLASS = tt["GDEF"].table.GlyphClassDef.classDefs
    font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    _cache = {}


X = 364
_cache = {}
if __name__ == "__main__":
    load(FONT)


def parts(name):
    """(letter, dots) of a glyph: dots = contours wholly above the x-height or below the baseline."""
    if name in _cache:
        return _cache[name]
    p = pathops.Path(); gs[name].draw(p.getPen()); p.simplify(fix_winding=True)
    from fontTools.pens.recordingPen import RecordingPen
    rec = RecordingPen(); p.draw(rec)
    contours, cur = [], None
    for op, a in rec.value:
        if op == "moveTo":
            cur = RecordingPen(); cur.moveTo(*a)
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            getattr(cur, op)(*a)
        elif op in ("closePath", "endPath"):
            cur.closePath(); q = pathops.Path(); cur.replay(q.getPen()); contours.append(q)
    letter, dots = pathops.Path(), pathops.Path()
    for c in contours:
        b = c.bounds
        is_dot = b and ((b[1] > X - 60 and b[3] - b[1] < 260 and b[2] - b[0] < 420) or
                        (b[3] < 10 and b[1] > -300 and b[2] - b[0] < 420 and b[3] - b[1] < 200))
        c.draw((dots if is_dot else letter).getPen())
    letter.simplify(fix_winding=True); dots.simplify(fix_winding=True)
    _cache[name] = (letter, dots)
    return _cache[name]


def mask(p, dx, ox, oy, W, H):
    from PIL import Image, ImageDraw
    from fontTools.pens.basePen import BasePen
    class PP(BasePen):
        def __init__(s): super().__init__(None); s.polys = []; s.cur = []
        def _moveTo(s, q): s.cur = [q]
        def _lineTo(s, q): s.cur.append(q)
        def _curveToOne(s, a, b, c):
            p0 = s.cur[-1]
            for t in np.linspace(0, 1, 10)[1:]:
                u = 1 - t
                s.cur.append((u**3*p0[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*c[0], u**3*p0[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*c[1]))
        def _closePath(s):
            if len(s.cur) > 2: s.polys.append(s.cur)
            s.cur = []
        _endPath = _closePath
    m = np.zeros((H, W), bool)
    if p is None or not p.bounds:
        return m
    pp = PP(); p.draw(pp)
    for poly in pp.polys:
        im = Image.new("1", (W, H), 0)
        ImageDraw.Draw(im).polygon([((x + dx - ox) / KR, (oy - y) / KR) for x, y in poly], fill=1)
        m ^= np.asarray(im, bool)
    return m


def gap(pa, xa, pb, xb, ox, oy, W, H):
    ma, mb = mask(pa, xa, ox, oy, W, H), mask(pb, xb, ox, oy, W, H)
    if not ma.any() or not mb.any():
        return 1e9
    if (ma & mb).any():
        return 0.0
    return ndimage.distance_transform_edt(~ma)[mb].min() * KR


def shaped(text):
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf, {})
    x, out = 0, []
    for i, p in zip(buf.glyph_infos, buf.glyph_positions):
        n = order[i.codepoint]
        if GCLASS.get(n) != 3:
            out.append((n, x + p.x_offset))
        x += p.x_advance
    return out


def joined(left, right):
    """True when the visual-left glyph joins the visual-right one (right joins on its left side,
    left joins on its right side)."""
    form = lambda n: n.split(".")[1] if "." in n else "isol"
    return form(right) in ("init", "medi") and form(left) in ("medi", "fina")


def pair_geometry(t, left, right):
    L = shaped(t)
    for (na, xa), (nb, xb) in zip(L, L[1:]):
        if na == left and nb == right:
            return xa, xb
    return None


def needed_shift(t, left, right, which, min_gap=None, cap=160):
    """How far the dots must move (units, + = right) so the pair clears min_gap.
    which: 'left' moves the left letter's dots left, 'right' moves the right letter's dots right,
    'both' moves both apart by the same amount each. Returns (dx_left, dx_right) or None."""
    min_gap = MIN_GAP if min_gap is None else min_gap
    pos = pair_geometry(t, left, right)
    if not pos:
        return None
    xa, xb = pos
    la, da = parts(left); lb, db = parts(right)
    x0 = min(xa, xb) - 400; x1 = max(xa + gs[left].width, xb + gs[right].width) + 400
    ox, oy, W, H = x0, 900, int((x1 - x0) / KR), int(1300 / KR)
    def ok(dl, dr):
        A = [(la, xa), (da, xa + dl)] if da.bounds else [(la, xa)]
        B = [(lb, xb), (db, xb + dr)] if db.bounds else [(lb, xb)]
        for p1, x1_ in A:
            for p2, x2_ in B:
                if (p1 is la and p2 is lb):
                    continue                       # letter to letter is the kerning's business
                if gap(p1, x1_, p2, x2_, ox, oy, W, H) < min_gap:
                    return False
        return True
    for s in range(0, cap + 1, 5):
        dl = -s if which in ("left", "both") else 0
        dr = s if which in ("right", "both") else 0
        if ok(dl, dr):
            return dl, dr
    return None


def scan(texts):
    found = {}
    for t in texts:
        L = shaped(t)
        for (na, xa), (nb, xb) in zip(L, L[1:]):           # na is left of nb
            la, da = parts(na); lb, db = parts(nb)
            x0 = min(xa, xb) - 300; x1 = max(xa + gs[na].width, xb + gs[nb].width) + 300
            ox, oy, W, H = x0, 900, int((x1 - x0) / KR), int(1300 / KR)
            j = joined(na, nb)
            checks = []
            if da.bounds: checks.append(("dots of the left letter", da, xa, pathops.op(lb, db, pathops.PathOp.UNION) if db.bounds else lb, xb))
            if db.bounds: checks.append(("dots of the right letter", db, xb, pathops.op(la, da, pathops.PathOp.UNION) if da.bounds else la, xa))
            if not j: checks.append(("letters", la, xa, lb, xb))
            for what, p1, x1_, p2, x2_ in checks:
                g = gap(p1, x1_, p2, x2_, ox, oy, W, H)
                if g < MIN_GAP:
                    key = (nb, na, what)
                    if key not in found or g < found[key][0]:
                        found[key] = (g, t)
    return found


LETTERS = "اآأإبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیئءةؤ"
DUAL = "بپتثجچحخسشصضطظعغفقکگلمنهیئ"


def texts():
    out = []
    for a in LETTERS:
        for b in LETTERS:
            out.append(a + b)                    # a alone/initial, b after it
            if a in DUAL:
                out.append("ب" + a + b)          # a medial/final
            out.append(a + b + "ب")              # b initial/medial
    return out


if __name__ == "__main__":
    found = scan(texts())
    print(f"{len(texts())} letter pairs scanned · {len(found)} with a gap under {MIN_GAP:.0f} units")
    for (nb, na, what), (g, t) in sorted(found.items(), key=lambda kv: kv[1][0]):
        print(f"  {g:5.0f}  {t:6s}  {nb} → {na}  ({what})")
    sys.exit(1 if found else 0)
