"""Build the Jashnvare family (v0.4) from Aly's Illustrator master.

Bold letters are the .ai outlines (ai_glyphs.json, from ai_import.py). Forms Aly
did not draw are composed from the drawn ones: final = isolated + right join,
medial = initial + right join, initial forms cut from the isolated drawing.
The other weights thin or thicken the Bold strokes (stems and bars separately)
and are re-fitted to the x-height.
Digits, punctuation, diacritics and the hamza are constructed per weight (extras.py).

v0.4 follows Aly's review sheet "Jashnvare Font.pdf" (2026-11-02):
  1  ع غ medial/final: upper curves become sharp corners, serif stays right
  2  initial ب پ ت ث ن ی ل: upper serif only, no lower serif
  3  ه initial and medial: two eyes
  4  ه final: serif and corner on the right, curve on the left
  5  س initial/medial keep the curve under the first tooth
  6  ک گ initial/medial: stray horizontal dash removed
  7  م initial/medial: serif and corner on the left, curve on the right
  8  ی final (and ئ final): head removed, clean join
  9  diacritics drawn in the font's language, placed by mark positioning
  10 Persian comma redrawn
  11 final ا: serif turns outward (left), except after ل (لا)
  12 digits on the baseline; ۲ ۳ teeth with serif; ۴ ۵ redrawn; ۶ cup; ۹ square eye
  13 پ initial/medial: dots no longer lean right
  general: ASCII digits show Persian digits; presentation forms and invisible
  characters from copied text are covered so pasted text joins.

Run: python3 build_ai.py            (all weights)
     python3 build_ai.py Bold Light (some weights)
"""
import json, os, re, subprocess, sys, tempfile, unicodedata
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import pathops
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glyphs as G
import extras as E

WRITTEN = os.environ.get("RF_WRITTEN") == "1"     # separate cut with the written feel (Aly's pick 5 Nov: light)
FAMILY = "KuhmardWritten" if WRITTEN else "Kuhmard"       # کوهمَرد: the font's main name (Aly, 9 Nov 2026)
FAMILY_FA = "کوهمَرد" + (" نوشتاری" if WRITTEN else "")      # the name a Persian-language system shows
MARK_GAP = (json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "marks_drawn.json")))["meta"]["gap_median"]
            if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "marks_drawn.json")) else 55)
LINE_ASC, LINE_DESC = 900, 400   # one line height (1.3) on every system; was 920/430 Mac, 1150/560 Windows (9 Nov review)
SPACE_W = 138      # word space: Aly's استاد کهنه note (4 Nov): about 250 units between words (was 45 -> 156)
VERSION = "1.002"  # 0.86: Google Fonts Latin Core accents + Azrast credits; 0.861: dots of ث ش ژ level with ل (14 Nov 2026); 1.0: approved by Aly as the first release (14 Nov 2026); 1.001: Dutch accents attach, Urdu ٹ ڈ ڑ ے (14 Nov 2026); 1.002: Google Fonts Latin language forms caroncomb.alt, idotaccent, Catalan l·l (15 Nov 2026)
# the Azrast team, in the order of the team page (Aly, 14 Nov 2026)
TEAM = [("Aly Taghipour", "Co-founder & Technical Director"),
        ("Ali Shir Dastina", "Co-founder & Design Director"),
        ("Fateme Cheraghi", "Lead Type Designer"),
        ("Fateme Bluekey", "Type Designer")]
CREDITS = ", ".join(n for n, _ in TEAM)
AI = json.load(open(os.path.join(HERE, "ai_glyphs.json")))
GL = AI["glyphs"]
STEM, BAR, DOT = AI["meta"]["stem"], AI["meta"]["bar"], AI["meta"]["dot"]   # 135 / 89 / 107
X, ASC, DESC = 364, AI["meta"]["ascender"], AI["meta"]["descender"]          # 364 / 588 / -194
BAR_RATIO = BAR / STEM
SER = 67                   # serif reach in the master
SB, JM = 56, 70            # side bearing: free side / joining side
GAP_UP, GAP_DN = 65, 77    # dot clearance above the x-height / below the baseline

# style: stem in font units, usWeightClass
# Latin letters, digits and maths signs, re-cut from Rokkitt (OFL) by latin/latin_export.py
_LAT = os.path.join(HERE, "latin", "latin_glyphs.json")
LATIN = json.load(open(_LAT)) if os.path.exists(_LAT) else {"styles": {}}

WEIGHTS = {"Light": (73, 300), "Regular": (95, 400), "Medium": (118, 500), "Bold": (STEM, 700), "Black": (174, 900)}

# ------------------------------------------------------------------ path helpers

def P(d):
    p = pathops.Path(); parse_path(d, p.getPen())
    p.simplify(fix_winding=True)           # every drawn part filled the same way before any merge
    return p


rect, union, rrect, poly = E.rect, E.union, E.rrect, E.poly


def U(*ps):
    ps = [p for p in ps if p is not None]
    return union(*ps) if ps else None


def inter(a, b):
    return pathops.op(a, b, pathops.PathOp.INTERSECTION)


def diff(a, *bs):
    return E.diff(a, *bs)


def shift(p, dx, dy=0):
    if p is None:
        return None
    out = pathops.Path(); p.draw(TransformPen(out.getPen(), (1, 0, 0, 1, dx, dy))); return out


def xform(p, t):
    out = pathops.Path(); p.draw(TransformPen(out.getPen(), t)); return out


def mirror(p):
    """Flip horizontally inside its own bounds."""
    b = p.bounds
    out = xform(p, (-1, 0, 0, 1, b[0] + b[2], 0))
    return union(out)          # re-normalise winding


def clip(p, x0=-1e5, y0=-1e5, x1=1e5, y1=1e5):
    return inter(p, rect(x0, y0, x1, y1))


def pieces(p, y):
    """Ink spans [(x0, x1), ...] of path p on the horizontal line y."""
    s = inter(p, rect(-1e5, y - 0.5, 1e5, y + 0.5))
    rec = RecordingPen(); s.draw(rec)
    spans, cur = [], []
    for op, args in rec.value:
        if op == "moveTo":
            cur = [args[0][0]]
        elif args:
            cur.extend(a[0] for a in args)
        if op == "closePath" and cur:
            spans.append((min(cur), max(cur))); cur = []
    return sorted(spans)


def body(n, f):
    return union(*[P(d) for d in GL[n][f]["body"]])


def dots(n, f):
    return union(*[P(d) for d in GL[n][f]["dots"]]) if GL[n][f]["dots"] else None


def contours(p):
    """Split a path into its closed contours (each as its own path)."""
    rec = RecordingPen(); p.draw(rec)
    out, cur = [], None
    for op, args in rec.value:
        if op == "moveTo":
            cur = RecordingPen(); cur.moveTo(*args)
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            getattr(cur, op)(*args)
        elif op in ("closePath", "endPath"):
            cur.closePath()
            q = pathops.Path(); cur.replay(q.getPen()); out.append(q)
    return out


DOT_GAP = 65                 # clear space between a single dot and the letter (above the x-height)
DOT_SIZE = DOT               # one square dot (the master's)
DOT_ABOVE = X + DOT_GAP + DOT / 2      # centre of the lowest row of dots above a letter (ت ن ف ...)
DOT_BELOW = DESC + DOT / 2             # centre of the nearest row below (ب ی ج ...): a single dot stands on the foot of ر
NOT_DOTS = ("alefmadda", "alefhamza", "alefhamzabelow", "wawhamza", "yehhamza", "hehyeh", "gaf", "heh", "hamza")
AS_DRAWN = {("teh", "isol"), ("teh", "fina"), ("theh", "isol"), ("theh", "fina")}   # dots set inside the bowl in the 7 Nov master
MARK_TOP = X - 60            # a separate small shape whose bottom is above this is a mark (ت isolated: 327)


R_INSIDE, R_OUTSIDE = 34, 26     # the "light" strength of the written-feel trial


def written_feel(p, adv, f):
    """Show the turn of the pen: where a stem comes down into the joining stroke the inside corner
    becomes a curve, and a free corner on the baseline is rounded. Slab serifs, dots, spacing and
    the joining ends stay as they are: the last STRIP units on a joining side are never touched."""
    if p is None or not p.bounds:
        return p
    jl = f in ("init", "medi"); jr = f in ("medi", "fina")
    x_lo = STRIP + 6 if jl else -1e6
    x_hi = adv - STRIP - 6 if jr else 1e6
    rec = RecordingPen(); p.draw(rec)
    conts, cur = [], None
    for op, a in rec.value:
        if op == "moveTo":
            cur = {"start": a[0], "segs": []}
        elif op in ("closePath", "endPath"):
            conts.append(cur)
        else:
            cur["segs"].append((op, list(a)))
    out = pathops.Path(); pen = out.getPen()
    for c in conts:
        pts, segs = [c["start"]], []
        for op, a in c["segs"]:
            if op == "lineTo" and a[-1] == pts[-1]:
                continue
            segs.append((op, a)); pts.append(a[-1])
        if pts[-1] == pts[0]:
            pts.pop()
        else:
            segs.append(("lineTo", [pts[0]]))
        n = len(pts)
        radius = {}
        for i in range(n):
            if segs[i - 1][0] != "lineTo" or segs[i][0] != "lineTo":
                continue
            V, A, B = pts[i], pts[i - 1], pts[(i + 1) % n]
            if abs(V[1] - A[1]) < 0.5 and abs(V[0] - B[0]) < 0.5:
                H, U = A, B
            elif abs(V[0] - A[0]) < 0.5 and abs(V[1] - B[1]) < 0.5:
                H, U = B, A
            else:
                continue
            if U[1] < V[1] + 20:                                # the vertical edge must rise from the corner
                continue
            sx = 1 if H[0] > V[0] else -1
            probe = (V[0] + sx * 1.5, V[1] + 1.5)               # inside the wedge between the two edges
            ink = p.contains(probe)
            if abs(V[1]) <= 2 and ink:
                r = R_OUTSIDE                                   # free corner on the baseline
            elif abs(V[1] - JB) <= 3 and not ink:
                r = R_INSIDE                                    # stem meets the top of the joining stroke
            else:
                continue
            if not (x_lo <= V[0] <= x_hi):
                continue
            end = V[0] + sx * r
            if end < x_lo: r = V[0] - x_lo
            if end > x_hi: r = x_hi - V[0]
            r = min(r, abs(H[0] - V[0]), U[1] - V[1])
            if r >= 12:
                radius[i] = r
        for i in range(n):                                      # two curves sharing an edge must fit on it
            j = (i + 1) % n
            if i in radius and j in radius and segs[i][0] == "lineTo":
                L = abs(pts[j][0] - pts[i][0]) + abs(pts[j][1] - pts[i][1])
                if radius[i] + radius[j] > L:
                    k = L / (radius[i] + radius[j]) * 0.98
                    radius[i] *= k; radius[j] *= k
        step = lambda a, b, r: (a[0] + (b[0] - a[0]) / (abs(b[0] - a[0]) + abs(b[1] - a[1])) * r,
                                a[1] + (b[1] - a[1]) / (abs(b[0] - a[0]) + abs(b[1] - a[1])) * r)
        def enter(i):                                           # where the path arrives at vertex i
            return step(pts[i], pts[i - 1], radius[i]) if i in radius else pts[i]
        def leave(i):
            return step(pts[i], pts[(i + 1) % n], radius[i]) if i in radius else pts[i]
        K = 0.5523
        pen.moveTo(leave(0))
        for i in range(n):
            j = (i + 1) % n
            op, a = segs[i]
            if op == "lineTo":
                pen.lineTo(enter(j))
            else:
                getattr(pen, op)(*a)
            if j in radius:
                V, e, l = pts[j], enter(j), leave(j)
                pen.curveTo((e[0] + (V[0] - e[0]) * K, e[1] + (V[1] - e[1]) * K),
                            (l[0] + (V[0] - l[0]) * K, l[1] + (V[1] - l[1]) * K), l)
        pen.closePath()
    return union(out)


def widened(letter, marks, dx, adv, name):
    """A dot-moved alternate (9 Nov review, option b): a letter that joins on its left (یـ ـیـ بـ ...)
    whose dots must move left by n is made n wider instead, its joining stroke lengthened by n, so
    the dots stay under the letter's own stroke and the next letter moves along. Other letters
    keep the plain move."""
    form = name.split(".")[1] if "." in name else "isol"
    if marks is None:
        return letter, adv
    if dx >= 0 or form not in ("init", "medi"):
        return union(letter, shift(marks, dx)), adv
    n = -dx
    return union(shift(letter, n), rect(-3, 0, n + STRIP + 1, JB), marks), adv + n


def stroke_w(p):
    """Typical stroke width of a path: twice its deepest inside distance."""
    b = p.bounds
    m = raster(p, 1, b[0] - 2, b[3] + 2, int(b[2] - b[0]) + 4, int(b[3] - b[1]) + 4)
    return 2 * float(ndimage.distance_transform_edt(m).max())


def bridge_stubs(p, adv, f):
    """A joining stub cut off from its letter by thinning (س ش medial/final meet their stub only
    at a corner) is joined back along the joining band."""
    if p is None or not p.bounds or f == "isol":
        return p
    cs = contours(p)
    if len(cs) < 2:
        return p
    main = max(cs, key=lambda c: abs(c.area))
    adds = []
    for c in cs:
        b = c.bounds
        if c is main or b[1] < -10 or b[3] > BAR + 20:
            continue
        right = f in ("medi", "fina") and b[2] >= adv - 6
        left = f in ("init", "medi") and b[0] <= 6
        if not (right or left):
            continue
        y = (b[1] + b[3]) / 2
        sp = [s_ for s_ in pieces(main, y)]
        if right:
            ends = [s_[1] for s_ in sp if s_[1] <= b[0] + 1]
            if ends:
                adds.append(rect(max(ends) - 2, b[1], b[0] + 2, b[3]))
        else:
            starts = [s_[0] for s_ in sp if s_[0] >= b[2] - 1]
            if starts:
                adds.append(rect(b[2] - 2, b[1], min(starts) + 2, b[3]))
    return union(p, *adds) if adds else p


def _row(u, top):
    """(bottom, top) of the row of dots nearest the letter: the ink is scanned from the side
    facing the letter until its width changes."""
    b = u.bounds
    ys = np.arange(b[3] - 2, b[1], -2) if top else np.arange(b[1] + 2, b[3], 2)
    w0 = None
    for y in ys:
        sp = pieces(u, y)
        w = (sp[-1][1] - sp[0][0]) if sp else 0
        if w0 is None:
            w0 = w
        elif abs(w - w0) > 20:
            return (y + 2, b[3]) if top else (b[1], y - 2)
    return b[1], b[3]


def level_dots(name, p, resize=True, parts=False, form=None):
    """Aly, 4 Nov (ریبوزوم, مریض) and the 7 Nov master: dots sit on two shared lines, whatever
    letter carries them, centred on them (a single dot and a two-dot bar share one centre).
    Above: the lowest row centred on DOT_ABOVE. Below: the nearest row's bottom on DESC, the foot of ن and ر
    (Aly 9 Nov; a lower row of three dots hangs under it). Single dots are all one size (resize: only on
    the Bold master; other weights inherit it). parts=True returns (letter, dots) for derive()."""
    base = name.split(".")[0]
    if p is None or not p.bounds or base in NOT_DOTS:
        return (p, None) if parts else p
    keep, above, below = [], [], []
    for c in contours(p):
        b = c.bounds
        w, h = b[2] - b[0], b[3] - b[1]
        if not p.contains(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)):     # a counter (the eye of ۹), not a dot
            keep.append(c)
        elif b[1] > MARK_TOP and w < 420 and h < 260:
            above.append(c)
        elif b[3] < 10 and b[1] > DESC - 120 and w < 420 and h < 220:  # dots inside a deep bowl (چ, -406) stay
            below.append(c)
        else:
            keep.append(c)
    if not above and not below:
        return (p, None) if parts else p
    as_drawn = (base, form) in AS_DRAWN
    out = []
    if above:
        if resize and base in ("zain", "dad"):                    # a dot drawn larger: the standard dot
            fixed = []
            for c in above:
                b = c.bounds
                if abs((b[2] - b[0]) - (b[3] - b[1])) < 12 and b[2] - b[0] > DOT_SIZE + 8:
                    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                    c = rect(cx - DOT_SIZE / 2, cy - DOT_SIZE / 2, cx + DOT_SIZE / 2, cy + DOT_SIZE / 2)
                fixed.append(c)
            above = fixed
        r0, r1 = _row(union(*above), top=False)
        dy = 0 if as_drawn else DOT_ABOVE - (r0 + r1) / 2
        out += [shift(c, 0, dy) for c in above]
    if below:
        r0, r1 = _row(union(*below), top=True)
        dy = 0 if as_drawn else DESC - r0                            # Aly 9 Nov (بهترین): the row's bottom on the foot of ن and ر
        out += [shift(c, 0, dy) for c in below]
    if parts:
        return union(*keep), union(*out)
    return union(*(keep + out))


def split_marks(p):
    """(letter, marks): marks are the contours lying wholly above the x-height or below the baseline."""
    letter, marks = [], []
    for c in contours(p):
        b = c.bounds
        if b and (b[1] > MARK_TOP and b[3] - b[1] < 260 and b[2] - b[0] < 420) or (b and b[3] < 10 and b[1] > DESC - 120 and b[2] - b[0] < 420 and b[3] - b[1] < 200):
            marks.append(c)
        else:
            letter.append(c)
    U_ = lambda cs: (union(*cs) if len(cs) > 1 else cs[0]) if cs else None
    # contours come in with their own winding: rebuild through one nonzero union of the full path minus marks
    full = union(p)
    mk = U_(marks)
    return (diff(full, mk) if mk is not None else full), mk


DOT1 = split_marks(body("beh", "isol"))[1]       # one square
DOT2 = split_marks(body("teh", "isol"))[1]       # two dots: short bar
DOT3UP = split_marks(body("theh", "isol"))[1]    # three dots above
DOT3DN = split_marks(body("peh", "isol"))[1]     # three dots below
HAMZA = E.Kit(STEM, BAR, DOT).hamza(1.0)


def mark(shape, cx, y, above, dx=0):
    """Place a dot shape centred on cx; above -> its bottom at y, else its top at y."""
    b = shape.bounds
    return shift(shape, cx - (b[0] + b[2]) / 2 + dx, (y - b[1]) if above else (y - b[3]))


def band_edges(p):
    """Left and right edge of the ink inside the baseline bar band."""
    b = p.bounds
    band = inter(p, rect(b[0] - 1, 0, b[2] + 1, BAR))
    bb = band.bounds
    return (bb[0], bb[2]) if bb else (b[0], b[2])


def floor_right(p):
    """Right edge of the ink below the baseline (the bowl floor of س ص)."""
    b = p.bounds
    return inter(p, rect(b[0] - 1, DESC - 5, b[2] + 1, -60)).bounds[2]


class PolyPen(BasePen):
    def __init__(self):
        super().__init__(None); self.polys = []; self.cur = []

    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 14)[1:]:
            u = 1 - t
            self.cur.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                             u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))

    def _closePath(self):
        if len(self.cur) > 2: self.polys.append(self.cur)
        self.cur = []
    _endPath = _closePath


def raster(p, sc, ox, oy, W, H):
    """Boolean mask of path p; ox = unit x of column 0, oy = unit y of row 0 (top)."""
    m = np.zeros((H, W), bool)
    if p is None:
        return m
    pen = PolyPen(); p.draw(pen)
    for pl in pen.polys:
        im = Image.new("1", (W, H), 0)
        ImageDraw.Draw(im).polygon([((x - ox) * sc, (oy - y) * sc) for x, y in pl], fill=1)
        m ^= np.asarray(im, bool)
    return m


def counter_left(p):
    """Left edge of the largest enclosed counter (the loop of ف ق)."""
    b = p.bounds
    W, H = int(b[2] - b[0]) + 4, int(b[3] - b[1]) + 4
    m = raster(p, 1, b[0] - 2, b[3] + 2, W, H)
    holes = ndimage.binary_fill_holes(m) & ~m
    lab, n = ndimage.label(holes)
    sizes = ndimage.sum(holes, lab, range(1, n + 1))
    sl = ndimage.find_objects(lab)[int(np.argmax(sizes))]
    return b[0] - 2 + sl[1].start


# ------------------------------------------------------------------ composition

TOOTH = ("beh", "peh", "teh", "theh", "noon", "yeh")
TOOTH_MARK = {
    "beh": (DOT1, False, 0), "peh": (DOT3DN, False, -30), "teh": (DOT2, True, 0),
    "theh": (DOT3UP, True, 0), "noon": (DOT1, True, 0), "yeh": (DOT2, False, 0),
}


def cut(b, x0, y0=0):
    """Keep the part of b right of x0 and above y0. Only the stem width at the cut
    is filled down to the baseline (so the cut never leaves a notch); nothing is
    added to the right of it, so no lower serif and no flattened curve (notes 2, 5)."""
    return union(clip(b, x0=x0, y0=y0), rect(x0, 0, x0 + STEM, BAR))


def tooth():
    """The tooth of ب cut from the isolated letter, and the centre of its stem."""
    b = body("beh", "isol"); R = b.bounds[2]
    top = inter(b, rect(R - 3 * STEM, X - 40, R + 1, X + 1)).bounds
    return cut(b, top[0]), top[0] + STEM / 2


def sharpen_upper(b):
    """Note 1: turn the rounded upper-left corners of ع (outer and inner) into square ones."""
    y = X - BAR - 20
    sp = pieces(b, y)
    (L, Rs), (tl, _) = sp[0], sp[-1]
    b = diff(b, rect(Rs, BAR, tl, X - BAR))
    return union(b, rect(L, BAR, Rs, X), rect(L, X - BAR, tl + 1, X))


HEH_THIN = 0.9      # Aly 9 Nov (سپهوند): ه looked heavier than its neighbours - two small closed eyes
                    # read darker, so the walls round the eyes are thinner and the eyes larger; the
                    # joining stroke on the baseline keeps the common weight


def heh_two_eyes(form):
    """Note 3: initial ه with two eyes side by side, medial ه with two eyes stacked.
    Serif and corner on the right, curve on the left (as in the final form, note 4)."""
    st, top = round(STEM * HEH_THIN), round(BAR * HEH_THIN)
    if form == "init":
        W = STEM + 112 + 100 + 112 + STEM                 # outer size as drawn
        mid = round(100 * HEH_THIN)
        e = (W - 2 * st - mid) / 2
        outer = rrect(0, 0, W, X, tl=175)
        eyes = union(rrect(st, BAR, st + e, X - top, tl=85),
                     rect(st + e + mid, BAR, W - st, X - top))
        return union(diff(outer, eyes), rect(W - 1, X - BAR, W + SER, X))
    W = 2 * STEM + 131
    e = W - 2 * st
    outer = rrect(0, DESC, W, X, tl=175, bl=110)
    eyes = union(rrect(st, BAR, st + e, X - top, tl=85),
                 rrect(st, DESC + 0.85 * BAR * HEH_THIN, st + e, 0, bl=40))
    return union(diff(outer, eyes), rect(W - 1, X - BAR, W + SER, X))


def meem_loop():
    """Note 7: the loop of م mirrored, so serif and corner sit left and the curve right."""
    b = body("meem", "isol")
    xl = pieces(b, 175)[0][0]
    return mirror(clip(b, x0=xl - 1, y0=0))


def yeh_final(b):
    """Note 8: final ی without the head; only the join block above the bowl stays."""
    left_end = pieces(b, 150)[0][1]              # right edge of the raised left end
    keep_from = pieces(b, -25)[-1][0]            # where the right side of the bowl starts rising
    return diff(b, rect(left_end + 30, 0, keep_from, X + 200), rect(left_end + 30, BAR, 1e5, X + 200))


def alef_body(outward):
    """Alef stem; outward=True turns the serif to the left (note 11)."""
    b = body("alef", "isol")
    return mirror(b) if outward else b


def stem_center(b, y):
    sp = pieces(b, y)
    return (sp[0][0] + sp[0][1]) / 2 if sp else (b.bounds[0] + b.bounds[2]) / 2


def local(n, f):
    """(body, dots) of letter n in form f, in the letter's own coordinates, before joins."""
    forms = GL.get(n, {})
    if f in forms:
        bd, dt = body(n, f), dots(n, f)
        if n == "zain" and f == "fina" and split_marks(bd)[1] is None:   # drawn without its dot: take it from the isolated ز
            src = body("zain", "isol"); mk = split_marks(src)[1]
            bd = union(bd, shift(mk, bd.bounds[0] - src.bounds[0]))
        if n == "sheen" and f == "isol" and dt is None:                  # drawn without its dots: take them from the final ش
            src = body("sheen", "fina")
            dt = shift(dots("sheen", "fina"), bd.bounds[0] - src.bounds[0])
        return bd, dt
    if n in ("ain", "ghain") and f in ("medi", "fina"):
        src = "init" if f == "medi" else "isol"
        return sharpen_upper(body(n, src)), dots(n, src)
    if n == "heh":
        if f in ("init", "medi"):
            return heh_two_eyes(f), None
        if f == "fina":
            return mirror(body("heh", "isol")), None
    if n == "meem" and f in ("init", "medi"):
        return meem_loop(), None
    if n == "yeh" and f == "fina":
        return yeh_final(body("yeh", "isol")), None
    if f in forms:
        return body(n, f), dots(n, f)
    if f == "fina":
        return local(n, "isol")
    if f == "medi":
        return local(n, "init")
    # initial forms that were not drawn
    if n in TOOTH:
        t, cx = tooth()
        shape, above, dx = TOOTH_MARK[n]
        return t, mark(shape, cx, X + GAP_UP if above else -GAP_DN, above, dx)
    if n in ("seen", "sheen", "sad", "dad"):
        b = body(n, "isol")
        return cut(b, floor_right(b) - STEM), dots(n, "isol")
    if n in ("feh", "qaf"):
        b = body(n, "isol")
        return cut(b, counter_left(b) - STEM), dots(n, "isol")
    if n in ("keheh", "gaf"):
        b = body(n, "isol"); R = b.bounds[2]
        sp = pieces(b, X - BAR + 20)              # [left upturn, arm and right side]
        split = (sp[0][1] + sp[1][0]) / 2 if len(sp) > 1 else b.bounds[0]
        return union(cut(b, R - STEM), clip(b, x0=split, y0=X - BAR - 10)), None   # note 6
    if n == "lam":
        b = body(n, "isol"); R = b.bounds[2]
        top = inter(b, rect(R - 3 * STEM, ASC - 40, R + 1, ASC + 1)).bounds
        return cut(b, top[0]), None
    if n in ("tah", "zah"):
        return body(n, "isol"), dots(n, "isol")
    raise KeyError((n, f))


ALEFS = {"alef": None, "alefmadda": "madda", "alefhamza": "hamza", "alefhamzabelow": "hamzabelow", "alefwasla": None}
STUB = 72                                            # joining stub added to the لا alef (as drawn in the 4 Nov master)


def alef_form(f, variant):
    """Drawn alef: isolated serif right, final serif left (note 11). In لا the final alef
    keeps the right serif: the isolated drawing plus a joining stub."""
    if f == "fina" and variant != "la":
        return body("alef", "fina")
    b = body("alef", "isol")
    if f == "fina":
        sr = pieces(b, ASC / 2)[0][1]
        b = union(b, rect(sr - 1, 0, sr + STUB, BAR))
    return b


def no_marks(p):
    return split_marks(p)[0]


def special(n, f, variant=None):
    """Letters built on Aly's drawn letters plus a mark."""
    if n in ALEFS:
        b = alef_form(f, variant)
        cx = stem_center(b, ASC / 2)
        kind = ALEFS[n]
        if kind is None:
            return b, None
        if kind == "madda":
            return b, madda_over(b, serif_left=(f == "fina" and variant != "la"))
        if kind == "hamza":
            return b, mark(HAMZA, cx, ASC + 60, True)
        return b, mark(HAMZA, cx, -GAP_DN, False)
    if n == "hamza":
        return HAMZA, None
    if n == "wawhamza":
        b = body("waw", f); sp = pieces(b, X - 40)
        cx = (sp[0][0] + sp[-1][1]) / 2 if sp else (b.bounds[0] + b.bounds[2]) / 2
        return b, mark(HAMZA, cx, X + GAP_UP, True)
    if n == "yehhamza":
        if f in ("init", "medi"):
            t = no_marks(body("yeh", f)); cx = stem_center(t, X - 40)
            return t, mark(HAMZA, cx, X + GAP_UP + 45, True)          # a little higher (4 Nov)
        b = body("yeh", f)
        sp = pieces(b, 200)                                            # the left stem with its hook
        cx = (sp[0][0] + sp[0][1]) / 2 if sp else (b.bounds[0] + b.bounds[2]) / 2
        return b, mark(HAMZA, cx, X - 20, True)                        # above the left stem, clear of the head (5 Nov)
    if n == "ae":
        return body("heh", "isol" if f == "isol" else "fina"), None
    if n in ("tehmarbuta", "hehyeh"):
        b = body("heh", "isol" if f == "isol" else "fina")
        sp = pieces(b, X - 40); cx = (sp[0][0] + sp[-1][1]) / 2
        if n == "tehmarbuta":
            return b, mark(DOT2, cx, X + GAP_UP, True)
        return b, mark(E.scale(HAMZA, 0.8), cx, X + GAP_UP - 10, True)
    if n == "tatweel":
        return rect(0, 0, 200, BAR), None
    raise KeyError(n)


MADDA_W, MADDA_T, MADDA_TICK, MADDA_TICK_W, MADDA_GAP = 310, 80, 25, 85, 78


def madda_over(b, serif_left=False):
    """The madda of آ, redrawn after the 9 Nov review (the drawn one read as a dark block): a thin bar
    with a short tick at its outer end, a clear gap above the alef. It lines up with the alef's top
    serif on the serif side and reaches past the stem on the open side, where the tick sits."""
    top = pieces(b, ASC - 20)
    x0, x1 = top[0][0], top[-1][1]
    y = b.bounds[3] + MADDA_GAP
    bar = rect(0, MADDA_TICK, MADDA_W, MADDA_TICK + MADDA_T)
    if serif_left:                                    # final alef: serif on the left, open side right
        tick = rect(MADDA_W - MADDA_TICK_W, 0, MADDA_W, MADDA_TICK + MADDA_T)
        return shift(union(bar, tick), x0, y)
    tick = rect(0, 0, MADDA_TICK_W, MADDA_TICK + MADDA_T)
    return shift(union(bar, tick), x1 - MADDA_W, y)


SPECIAL = set(ALEFS) | {"hamza", "wawhamza", "yehhamza", "tehmarbuta", "hehyeh", "ae", "tatweel"}


JB = 89            # joining band height: every stub end is exactly [0, JB]
STRIP = 24         # width of the normalised stub end
AIN_LIP_TRIM = 0          # the 7 Nov master draws the initial ع غ lip already shortened (was 187 on the 4 Nov master)
WAW_JOIN_ADD = 34  # و final: incoming join as long as the other letters' (74); was 114 (4 Nov), shortened after the 9 Nov review
SEEN_JOIN_TRIM = 64  # سـ شـ: the outgoing join on the left was 138, the other letters' 74 (9 Nov review)
ROW_DY = {}        # per-letter vertical snap, learned from its joining forms


def edge_bottom(p, x0, x1):
    s = inter(p, rect(x0, -40, x1, JB + 40)).bounds
    return s[1] if s else 0


def snap_heights(p, tol=4.5):
    """Move the ends of every (nearly) horizontal straight edge lying within tol of a shared height
    (baseline, joining-bar top, x-height, ascender, descender) exactly onto it, so edges that
    should line up do, inside a glyph and across joins (Aly, 4 Nov: no extra line or step anywhere).
    Curves keep their drawn overshoot: the bowl of س dips 6 units under the baseline (5 Nov)."""
    if p is None:
        return None
    refs = ((0, 6.5), (JB, 6.5), (X, tol), (ASC, tol), (DESC, tol))
    def ref(y):
        for r, t in refs:
            if abs(y - r) <= t:
                return r
        return None
    rec = RecordingPen(); p.draw(rec)
    # split into contours of (op, points)
    conts, cur = [], None
    for op, args in rec.value:
        if op == "moveTo":
            cur = [(op, list(args))]
        elif op in ("closePath", "endPath"):
            conts.append(cur); cur = None
        else:
            cur.append((op, list(args)))
    out = pathops.Path(); pen = out.getPen()
    for segs in conts:
        ends = [a[-1] for _, a in segs]                     # on-curve points, in order
        if ends[-1] != ends[0]:
            segs = segs + [("lineTo", [ends[0]])]; ends.append(ends[0])
        snap = {}                                           # index of on-curve point -> new y
        for i in range(1, len(segs)):
            if segs[i][0] != "lineTo":
                continue
            (xa, ya), (xb, yb) = ends[i - 1], ends[i]
            ra, rb = ref(ya), ref(yb)
            if ra is not None and ra == rb and abs(xa - xb) > 1:
                snap[i - 1] = ra; snap[i] = ra
        if segs[-1][1][-1] == ends[0] and (len(segs) - 1) in snap:
            snap[0] = snap[len(segs) - 1]
        if 0 in snap:
            snap[len(segs) - 1] = snap[0]
        for i, (op, a) in enumerate(segs):
            pts = list(a)
            if i in snap:
                pts[-1] = (pts[-1][0], snap[i])
                if op == "curveTo" and ref(pts[-2][1]) == snap[i]:
                    pts[-2] = (pts[-2][0], snap[i])         # handle stays level with its point
            if op == "curveTo" and (i - 1) in snap and ref(pts[0][1]) == snap[i - 1]:
                pts[0] = (pts[0][0], snap[i - 1])
            getattr(pen, op)(*pts)
        pen.closePath()
    return union(out)


TCHEH_TAIL = 246            # isolated / final چ: the tail's lower stroke ends here (was 434)


def open_eyes(bd, k=1 - HEH_THIN):
    """Aly 9 Nov: the eyes of ه grow into their walls by k of each wall's width (half of that from
    each side of a wall two eyes share), so the closed letter reads as light as its neighbours.
    The joining stroke on the baseline (0..JB) is never thinned."""
    cs = contours(bd)
    holes = [c for c in cs if not bd.contains(((c.bounds[0] + c.bounds[2]) / 2, (c.bounds[1] + c.bounds[3]) / 2))]
    if not holes:
        return bd
    solid = union(*[c for c in cs if not any(c is h for h in holes)])
    hbs = [h.bounds for h in holes]

    def wall(x, y, step):                        # ink run from (x, y) outwards; is a hole on the far side?
        d = 0
        while bd.contains((x + step * (d + 1), y)) if step in (-1, 1) else bd.contains((x, y + step // 2 * (d + 1))):
            d += 1
            if d > 400:
                break
        fx, fy = (x + step * (d + 2), y) if step in (-1, 1) else (x, y + step // 2 * (d + 2))
        shared = any(b[0] <= fx <= b[2] and b[1] <= fy <= b[3] for b in hbs)
        return d * (k / 2 if shared else k)

    out = []
    for h, b in zip(holes, hbs):
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        gl, gr = wall(b[0] - 1, cy, -1), wall(b[2] + 1, cy, 1)
        gb = 0 if abs(b[1] - JB) < 6 else wall(cx, b[1] - 1, -2)          # sits on the joining stroke: kept
        gt = 0 if abs(b[3]) < 6 else wall(cx, b[3] + 1, 2)                # hangs from the joining stroke: kept
        sx = (b[2] - b[0] + gl + gr) / (b[2] - b[0]); sy = (b[3] - b[1] + gb + gt) / (b[3] - b[1])
        out.append(xform(h, (sx, 0, 0, sy, b[0] - gl - b[0] * sx, b[1] - gb - b[1] * sy)))
    return diff(solid, *out)


def to_height(p, top, y0=X + 40):
    """Stretch everything above y0 so the shape ends exactly at `top` (only the stem gets longer)."""
    t0 = p.bounds[3]
    if abs(t0 - top) < 1:
        return p
    k = (top - y0) / (t0 - y0)
    rec = RecordingPen(); p.draw(rec)
    out = pathops.Path(); pen = out.getPen()
    for op, args in rec.value:
        getattr(pen, op)(*[(x, y if y <= y0 else y0 + (y - y0) * k) for x, y in args])
    return out


def retouch(n, f, bd):
    """Review round of 5 Nov (Aly's team), in glyph coordinates."""
    if n == "heh" and f in ("init", "medi"):
        return open_eyes(bd)
    if n == "lam":
        return to_height(bd, ASC)                 # Aly 9 Nov (دانیال): ل as tall as ا
    if n == "digit9":
        # 9 Nov: the counter of ۹ sits in the middle of the bowl, top to bottom (it was drawn high)
        cs = contours(bd)
        holes = [c for c in cs if any(o is not c and o.bounds[0] <= c.bounds[0] and o.bounds[2] >= c.bounds[2]
                                      and o.bounds[1] <= c.bounds[1] and o.bounds[3] >= c.bounds[3] for o in cs)]
        if holes:
            h = holes[0]; hb = h.bounds
            solid = union(*[c for c in cs if c is not h])
            col = inter(solid, rect(hb[0] + 5, -1e4, hb[2] - 5, 1e4)).bounds      # the bowl above and below the counter
            dy = (col[1] + col[3]) / 2 - (hb[1] + hb[3]) / 2
            return diff(solid, shift(h, 0, dy))
    if n == "tcheh" and f in ("isol", "fina") and min(c.bounds[1] for c in contours(bd)) < DESC - 120:
        # (only for a drawing that hangs the dots deep inside the bowl) the three dots sit beside a
        # shorter tail, on the same line as every dot below (like ج)
        cs = contours(bd); main = max(cs, key=lambda c: abs(c.area))
        d = union(*[c for c in cs if c is not main])
        main = diff(main, rect(TCHEH_TAIL, -400, 5000, -20))
        return union(main, shift(d, TCHEH_TAIL + 62 - d.bounds[0], -106 - d.bounds[3]))
    if n == "noon" and f in ("isol", "fina"):
        # the dot sits exactly midway between the two arms
        cs = contours(bd); main = max(cs, key=lambda c: abs(c.area))
        d = union(*[c for c in cs if c is not main])
        sp = pieces(main, JB + 60)                       # the left arm is shorter than the dot's height
        if len(sp) >= 2:
            cx = (sp[0][1] + sp[1][0]) / 2
            return union(main, shift(d, cx - (d.bounds[0] + d.bounds[2]) / 2))
    if n in ("yeh", "teh") and f == "init":
        # the two dots are centred on the tooth as seen (stem and its serif), not on the stem alone
        cs = contours(bd); main = max(cs, key=lambda c: abs(c.area))
        d = union(*[c for c in cs if c is not main])
        sp = pieces(main, X - 20)
        if sp:
            cx = (sp[0][0] + sp[-1][1]) / 2
            return union(main, shift(d, cx - (d.bounds[0] + d.bounds[2]) / 2))
    return bd


def compose(n, f, variant=None):
    """Bold master: (body with joins, dots, advance) in glyph space.
    On a joining side the glyph edge sits at the end of the drawn joining stub,
    so neighbouring letters meet stub to stub as in the drawing. Every stub end is
    snapped to the same band [0, JB], so joins never show a step or a ridge."""
    bd, dt = special(n, f, variant) if n in SPECIAL else local(n, f)
    jl = f in ("init", "medi"); jr = f in ("medi", "fina")
    if n in ("ain", "ghain") and f == "init":
        l0 = band_edges(bd)[0]
        bd = clip(bd, x0=l0 + AIN_LIP_TRIM)
    if n in ("ain", "ghain") and f == "medi":
        # medial ع غ keep the whole head (top bar, both slants, closed triangle);
        # only the lower lip on the left is shortened, to the same reach the head has on the right
        head = inter(bd, rect(-1e5, X - BAR, 1e5, X + 1)).bounds
        band = inter(bd, rect(-1e5, -1, 1e5, JB + 1)).bounds
        reach = max(0, band[2] - head[2])
        cut_at = head[0] - max(reach, 83)
        bd = diff(bd, rect(-1e5, -60, cut_at, JB + 2))
    if n in ("seen", "sheen") and jl:
        l0 = band_edges(bd)[0]
        bd = clip(bd, x0=l0 + SEEN_JOIN_TRIM)
    if n in ("waw", "wawhamza") and jr:
        r0 = band_edges(bd)[1]
        bd = union(bd, rect(r0 - 2, 0, r0 + WAW_JOIN_ADD, JB))
    b = bd.bounds
    l, r = band_edges(bd)
    # vertical snap: the stub end sits exactly on the baseline
    if jl or jr:
        dy = -(edge_bottom(bd, r - STRIP, r) if jr else edge_bottom(bd, l, l + STRIP))
        ROW_DY.setdefault(n, dy)
    else:
        dy = ROW_DY.get(n, 0)
    if dy:
        bd = shift(bd, 0, dy); dt = shift(dt, 0, dy)
    x0 = l if jl else b[0] - SB              # glyph origin, in body coordinates
    x1 = r if jr else b[2] + SB              # advance edge
    bd = shift(bd, -x0); dt = shift(dt, -x0)
    bd = snap_heights(bd)
    adv = x1 - x0
    if jl:
        bd = union(diff(bd, rect(-50, -30, STRIP, JB + 25)), clip(bd, x0=-50, y0=JB + 25, x1=STRIP), clip(bd, x0=-50, y1=-30, x1=STRIP),
                   rect(-3, 0, STRIP + 1, JB))
    if jr:
        bd = union(diff(bd, rect(adv - STRIP, -30, adv + 50, JB + 25)), clip(bd, x0=adv - STRIP, y0=JB + 25, x1=adv + 50),
                   clip(bd, x0=adv - STRIP, y1=-30, x1=adv + 50), rect(adv - STRIP - 1, 0, adv, JB))   # ends on the edge: only the right letter's join overlaps (9 Nov review)
    if n == "tatweel":
        # the stretch stroke fills its whole width in every form: an app that justifies text by
        # inserting it unshaped (isolated) drew a dashed line (5 Nov)
        return rect(-3, 0, 200, JB), dt, 200          # overlaps only into the letter on its left (9 Nov review)
    return retouch(n, f, bd), dt, adv


# ------------------------------------------------------------------ weights

SC = 2
PADX, TOP, BOT = 80, 900, -420


def trace(mask, ox, oy):
    H, W = mask.shape
    with tempfile.TemporaryDirectory() as td:
        pbm = os.path.join(td, "g.pbm"); svg = os.path.join(td, "g.svg")
        Image.fromarray(np.where(mask, 0, 255).astype("uint8")).convert("1").save(pbm)
        subprocess.run(["potrace", pbm, "-s", "-o", svg, "-t", "6", "-a", "0.55", "-O", "0.2"], check=True)
        txt = open(svg).read()
    rec = RecordingPen()
    sx = 0.1 / SC
    tp = TransformPen(rec, (sx, 0, 0, sx, ox, oy - H / SC))
    for d in re.findall(r'\sd="([^"]+)"', txt):
        parse_path(d, tp)
    p = pathops.Path(); rec.replay(p.getPen())
    p.simplify(fix_winding=True, keep_starting_points=False)
    return p


def morph(m, hx, vy):
    """Erode (positive) or dilate (negative) by hx px horizontally and vy px vertically."""
    a = m.astype(np.uint8)
    for size, amt in (((1, 2 * abs(hx) + 1), hx), ((2 * abs(vy) + 1, 1), vy)):
        if amt > 0: a = ndimage.minimum_filter(a, size=size)
        elif amt < 0: a = ndimage.maximum_filter(a, size=size)
    return a.astype(bool)


def weight_params(stem_t):
    h = (STEM - stem_t) / 2
    v = (BAR - stem_t * BAR_RATIO) / 2
    return h, v


def derive(bd, dt, adv, stem_t, thin=None, thin_w=0):
    """Re-weight a Bold master: returns (path, advance). thin: strokes much thinner than a stem
    (the second bar of گ, thin_w units wide), thinned in proportion so they never vanish."""
    h, v = weight_params(stem_t)
    W = int((adv + 2 * PADX) * SC); H = int((TOP - BOT) * SC)
    ox, oy = -PADX, TOP
    mb = morph(raster(bd, SC, ox, oy, W, H), round(h * SC), round(v * SC))
    if thin is not None:
        r = round(thin_w * (1 - stem_t / STEM) / 2 * SC)
        mb |= morph(raster(thin, SC, ox, oy, W, H), r, r)
    md = morph(raster(dt, SC, ox, oy, W, H), round(v * SC), round(v * SC))
    k = X / (X - 2 * v)
    T = (1, 0, 0, k, -h, -v * k)
    if dt is None or not dt.bounds or not (mb & md).any() and not _touch(mb, md):
        return xform(trace(mb | md, ox, oy), T), adv - 2 * h
    # a heavier weight can close the gap between a mark and its letter (madda on آ in Black):
    # trace them apart and keep the master's gap
    body, marks = xform(trace(mb, ox, oy), T), xform(trace(md, ox, oy), T)
    g0 = _gap(bd, dt)
    up = (dt.bounds[1] + dt.bounds[3]) > (bd.bounds[1] + bd.bounds[3])
    step = 0
    while _gap(body, shift(marks, 0, step if up else -step)) < g0 - 2 and step < 200:
        step += 4
    return union(body, shift(marks, 0, step if up else -step)), adv - 2 * h


def _touch(ma, mb):
    """True when two rasters touch or come within a pixel."""
    return (ndimage.binary_dilation(ma, iterations=2) & mb).any()


def _gap(a, b):
    """Smallest distance between two paths, in font units."""
    ba, bb = a.bounds, b.bounds
    x0, y1 = min(ba[0], bb[0]) - 20, max(ba[3], bb[3]) + 20
    W = int((max(ba[2], bb[2]) + 20 - x0) / KR); H = int((y1 - min(ba[1], bb[1]) + 20) / KR)
    ma, mb = ink_mask(a, x0, y1, W, H), ink_mask(b, x0, y1, W, H)
    if (ma & mb).any():
        return 0.0
    return ndimage.distance_transform_edt(~ma)[mb].min() * KR


# ------------------------------------------------------------------ copied text support

ZERO_WIDTH = [0x200B, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
              0x2066, 0x2067, 0x2068, 0x2069, 0xFEFF, 0x00AD, 0x061C, 0x2060]
SPACES = {0x0009: 840, 0x2002: 500, 0x2003: 1000, 0x2007: 420, 0x2008: 150, 0x2009: 120, 0x200A: 60, 0x202F: 120, 0x3000: 1000}
LAMALEF = {"0627": "alef", "0622": "alefmadda", "0623": "alefhamza", "0625": "alefhamzabelow"}


def presentation_forms(names_by_cp, have):
    """cmap entries for Arabic presentation forms (text copied from PDFs uses them)."""
    out, ligs = {}, {}
    tag2form = {"<isolated>": "isol", "<final>": "fina", "<initial>": "init", "<medial>": "medi"}
    for cp in list(range(0xFB50, 0xFE00)) + list(range(0xFE70, 0xFEFF)):
        dec = unicodedata.decomposition(chr(cp)).split()
        if len(dec) < 2 or dec[0] not in tag2form:
            continue
        form = tag2form[dec[0]]
        codes = dec[1:]
        if len(codes) == 1:
            base = names_by_cp.get(int(codes[0], 16))
            if not base:
                continue
            g = base if form == "isol" else f"{base}.{form}"
            if g in have:
                out[cp] = g
        elif len(codes) == 2 and codes[0] == "0644" and codes[1] in LAMALEF:
            g = f"lam_{LAMALEF[codes[1]]}" + ("" if form == "isol" else ".fina")
            ligs[g] = (form, LAMALEF[codes[1]])
            out[cp] = g
    return out, ligs


# ------------------------------------------------------------------ anchors

def anchors(path, adv, name=""):
    """Top and bottom attachment points for diacritics.
    Horizontal: the centre of the letter itself (dots and joining stubs left out) at the
    height where the mark sits: the middle of its top for marks above, of its foot for
    marks below. Narrow letters (ا, a tooth, ل's stem) use the stem's centre.
    Vertical: clear of everything already above or below (dots, ascenders, bowls)."""
    if path is None or not path.bounds:
        return (adv / 2, X + MARK_GAP), (adv / 2, -MARK_GAP)
    form = name.split(".")[-1] if "." in name else "isol"
    jl = form in ("init", "medi"); jr = form in ("medi", "fina")
    letter = split_marks(path)[0] or path
    x0 = STRIP + 10 if jl else -1e4
    x1 = adv - STRIP - 10 if jr else 1e4
    body = inter(letter, rect(x0, -1e4, x1, 1e4))
    bb = body.bounds or letter.bounds
    def centre(y0, y1):
        s = inter(body, rect(-1e4, y0, 1e4, y1)).bounds
        return (s[0] + s[2]) / 2 if s else (bb[0] + bb[2]) / 2
    mid = pieces(body, (BAR + X) / 2)
    narrow = (bb[2] - bb[0]) <= 2.1 * STEM
    if narrow and mid:
        cx_top = cx_bot = (mid[0][0] + mid[-1][1]) / 2
    else:
        cx_top = centre(bb[3] - BAR - 30, bb[3] + 1)
        cx_bot = centre(bb[1] - 1, bb[1] + BAR + 30)
    def clear(cx, top):
        w = inter(path, rect(cx - 120, -1e4, cx + 120, 1e4)).bounds
        if top:
            return max(w[3], X) if w else X
        return min(w[1], 0) if w else 0
    return (round(cx_top), round(clear(cx_top, True) + MARK_GAP)), (round(cx_bot), round(clear(cx_bot, False) - MARK_GAP))





# ------------------------------------------------------------------ kerning (Aly, 4 Nov)

KR = 4  # raster units per pixel for collision checks


def ink_mask(p, ox, oy, W, H):
    return raster(p, 1 / KR, ox, oy, W, H)


def side_ws(p, adv, side, y0, y1):
    """Whitespace between the ink and the glyph edge on one side, within the band y0..y1."""
    s = inter(p, rect(-1e4, y0, 1e4, y1)).bounds if p is not None else None
    if not s:
        return None
    return s[0] if side == "left" else adv - s[2]


def min_distance(pa, adv_a, pb, adv_b, kern):
    """Smallest gap between glyph a (on the right) and glyph b (on its left) after kerning."""
    ox, oy = -adv_b - 200, 1300
    W, H = int((adv_a + adv_b + 400) / KR), int(1900 / KR)
    ma = ink_mask(pa, ox, oy, W, H)
    mb = ink_mask(shift(pb, -adv_b - kern), ox, oy, W, H)     # kern < 0 moves b right
    if not ma.any() or not mb.any():
        return 1e9, None
    d = ndimage.distance_transform_edt(~ma)
    hit = d[mb]
    return hit.min() * KR, None


def row_gap(pa, adv_a, pb, adv_b, kern):
    """Smallest horizontal gap, row by row, between glyph a (on the right) and glyph b (on its left)
    after kerning; only rows where both have ink count, so a serif high up does not hide a wide gap below."""
    ox, oy = -adv_b - 200, 1300
    W, H = int((adv_a + adv_b + 400) / KR), int(1900 / KR)
    ma = ink_mask(pa, ox, oy, W, H)
    mb = ink_mask(shift(pb, -adv_b - kern), ox, oy, W, H)
    rows = ma.any(1) & mb.any(1)
    if not rows.any():
        return None
    first_a = np.where(ma[rows].any(1), ma[rows].argmax(1), 0)
    last_b = mb.shape[1] - 1 - mb[rows][:, ::-1].argmax(1)
    return float((first_a - last_b - 1).min() * KR)


def serif_side(p, top_band=70):
    """'left' / 'right' when the glyph's top carries a serif reaching past its stem on that side."""
    if p is None or not p.bounds:
        return None
    letter = split_marks(p)[0]
    b = letter.bounds
    top = inter(letter, rect(-1e4, b[3] - 35, 1e4, b[3])).bounds
    below = inter(letter, rect(-1e4, b[3] - top_band - 120, 1e4, b[3] - top_band - 40)).bounds
    if not top or not below:
        return None
    if top[0] < below[0] - 35 and abs(top[2] - below[2]) < 20:
        return "left"
    if top[2] > below[2] + 35 and abs(top[0] - below[0]) < 20:
        return "right"
    return None


def kerning(paths, bases, letter_glyphs):
    global_letters = letter_glyphs
    """Returns (pair lines, extra glyphs for shifted dots, substitution lines).
    1  ر ز ژ: the space on their left to the next letter -20 %; if the next letter's
       dots would touch the tail, those dots move left in a contextual alternate.
    2  a left serif (final ا) facing a right serif (ر ...): the space between -5 %.
    Spacing elsewhere is untouched, so the rhythm stays."""
    firsts = [g for g in bases if g.split(".")[0] in ("reh", "zain", "jeh") and g.split(".")[-1] in ("reh", "zain", "jeh", "fina")]
    seconds = [g for g in letter_glyphs if "." not in g or g.endswith(".init")]
    seconds += [g for g in paths if g.startswith("lam_") and not g.endswith(".fina")]
    pairs, alts, subs = [], {}, []
    # reference (red): the gap Aly marked between connected ا and ر, as it showed in v0.61 (فارسی): 119 units
    RED = 119
    CLEAR = min(RED, 45)                      # never closer than this anywhere else (tail, dots)
    for a in firsts:
        pa, adv_a = paths[a]
        la = split_marks(pa)[0]; ta = la.bounds[3]
        bnd = (ta - BAR, ta)
        wa = side_ws(la, adv_a, "left", *bnd)
        for bname in seconds:
            pb, adv_b = paths[bname]
            lb = split_marks(pb)[0]
            wb = side_ws(lb, adv_b, "right", *bnd)
            if wb is None:                      # nothing on that height: use the letter's x-height zone
                wb = side_ws(lb, adv_b, "right", BAR, X)
            if wa is None or wb is None:
                continue
            k = -round((wa + wb) - RED)        # blue becomes red
            if k >= 0:
                continue
            dist, _ = min_distance(pa, adv_a, pb, adv_b, k)
            if dist < CLEAR:
                letter_b, marks_b = split_marks(pb)
                d_letter, _ = min_distance(pa, adv_a, letter_b, adv_b, k)
                if d_letter >= CLEAR and marks_b is not None:   # only the dots are in the way: move them left
                    need = CLEAR - dist + 10
                    while need < 200 and min_distance(pa, adv_a, union(letter_b, shift(marks_b, -need)), adv_b, k)[0] < CLEAR:
                        need += 5                                # move until the clearance is really there
                    alt = f"{bname}.rk{int(need)}"
                    if alt not in alts:
                        alts[alt] = widened(letter_b, marks_b, -need, adv_b, bname)
                    subs.append((a, bname, alt))
                else:                                            # the letters themselves: stop at the clearance
                    while k < 0 and min_distance(pa, adv_a, pb, adv_b, k)[0] < CLEAR:
                        k += 5
            if k:
                pairs.append(f"    pos {a} {bname} <{k} 0 {k} 0>;")
    print(f"red gap {RED:.0f} units (ـا to ر), clearance {CLEAR:.0f}")
    # serif facing serif
    lefts = [g for g in letter_glyphs if serif_side(paths[g][0]) == "left" and (g.endswith(".fina") or "." not in g)]
    rights = [g for g in seconds if serif_side(paths[g][0]) == "right"]
    kd = {}
    for a in lefts:
        pa, adv_a = paths[a]
        la = split_marks(pa)[0]; ta = la.bounds[3]
        for bname in rights:
            pb, adv_b = paths[bname]
            lb = split_marks(pb)[0]; tb = lb.bounds[3]
            y1 = tb if bname.split(".")[0] in ("reh", "zain", "jeh") else min(ta, tb)
            y0 = y1 - BAR
            wa = side_ws(la, adv_a, "left", y0, y1); wb = side_ws(lb, adv_b, "right", y0, y1)
            if wa is None or wb is None:
                continue
            if bname.split(".")[0] in ("reh", "zain", "jeh"):
                k = -round((wa + wb) - RED) if (wa + wb) > RED else 0
            else:
                k = -round(0.05 * (wa + wb))
            if k:
                kd[(a, bname)] = k
    # 3  after a letter that does not join on its left (ا د ذ و ؤ ة ۀ ..., alone or final), the nearest
    #    row-by-row gap to the next letter is the plain gap of ا to ن (Aly, 4 Nov: هریوان, و to ا as
    #    ا to ن; استاد, ـا to د). A top serif on either side had pushed stems ~66 units apart.
    #    Next to ر ز ژ the red gap stays. Only tightens; ر ز ژ as first letters keep rule 1.
    plain = row_gap(split_marks(paths["alef"][0])[0], paths["alef"][1], split_marks(paths["noon"][0])[0], paths["noon"][1], 0)
    joins_left = {g.split(".")[0] for g in letter_glyphs if g.endswith(".init")}
    finals = [g for g in bases if g in paths and not g.endswith((".init", ".medi"))
              and g.split(".")[0] not in joins_left | {"reh", "zain", "jeh"} and ".rk" not in g
              and (g.split(".")[0] in G.LETTERS or g.split(".")[0] in ("alefwasla", "hehyeh", "ae", "alefmadda", "alefhamza", "alefhamzabelow", "wawhamza", "tehmarbuta")
                   or g.startswith("lam_"))]
    for a in finals:
        la = split_marks(paths[a][0])[0]; adv_a = paths[a][1]
        for bname in seconds:
            lb = split_marks(paths[bname][0])[0]; adv_b = paths[bname][1]
            target = RED if bname.split(".")[0] in ("reh", "zain", "jeh") else plain
            g0 = row_gap(la, adv_a, lb, adv_b, 0)
            if g0 is None or g0 - target <= 6:
                continue
            k = -round(g0 - target)
            while k < 0 and min_distance(la, adv_a, lb, adv_b, k)[0] < CLEAR:
                k += 5
            if k < kd.get((a, bname), 0):
                kd[(a, bname)] = k
    print(f"plain gap (ا to ن) {plain:.0f} units")
    pairs += [f"    pos {a} {b} <{k} 0 {k} 0>;" for (a, b), k in kd.items() if k]
    return pairs, alts, subs, lefts, rights


# ------------------------------------------------------------------ font

def charstring(path, adv):
    pen = T2CharStringPen(adv, None)
    if path is not None:
        path.draw(pen)
    return pen.getCharString()


def build(style, dot_rounds=()):
    """dot_rounds: rounds from dotfix.plan, each {"alts": {alt: (src, dx)}, "rules": [(right, left, which, alt)]}."""
    stem_t, wclass = WEIGHTS[style]
    h, v = weight_params(stem_t)
    kit = E.Kit(stem_t, stem_t * BAR_RATIO, DOT - 2 * v)
    order = [".notdef", "space", "zwnj", "zwj", "zerowidth"]
    cmap = {0x20: "space", 0xA0: "space", 0x200C: "zwnj", 0x200D: "zwj"}
    widths = {".notdef": 500, "space": SPACE_W, "zwnj": 0, "zwj": 0, "zerowidth": 0}
    lsb = {".notdef": 50, "space": 0, "zwnj": 0, "zwj": 0, "zerowidth": 0}
    for cp in ZERO_WIDTH + [0x000A, 0x000D, 0x0085, 0x2028, 0x2029]:
        cmap[cp] = "zerowidth"
    cs, paths, bases, marks_top, marks_bot = {}, {}, [], [], []
    nd = T2CharStringPen(500, None)
    for (x0, y0, x1, y1), cw in (((50, 0, 450, 600), False), ((100, 50, 400, 550), True)):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if cw: pts = pts[::-1]
        nd.moveTo(pts[0]); [nd.lineTo(p) for p in pts[1:]]; nd.closePath()
    cs[".notdef"] = nd.getCharString()
    for n in ("space", "zwnj", "zwj", "zerowidth"):
        cs[n] = charstring(None, widths[n])
    for cp, w in SPACES.items():
        g = f"space{cp:04X}"
        cs[g] = charstring(None, w); widths[g] = w; lsb[g] = 0; order.append(g); cmap[cp] = g

    subs = {f: [] for f in ("init", "medi", "fina")}

    TALL = alef_body(False).bounds[3]         # top of ا and ل (586 in Bold)

    def add(gname, path, adv, cps, base=True):
        # Aly 14 Nov (ثل): dots above that rise just past the top of ا / ل (three dots of ث ش ژ: 602)
        # read as a misaligned step next to a tall letter; bring their top down onto the tall line
        if base and path is not None and path.bounds and path.bounds[3] > TALL:
            lt, mk = split_marks(path)
            if mk is not None and mk.bounds and TALL < mk.bounds[3] <= TALL + 40 and mk.bounds[1] > X:
                path = union(lt, shift(mk, 0, TALL - mk.bounds[3]))
        cs[gname] = charstring(path, adv)
        widths[gname] = adv
        lsb[gname] = int(path.bounds[0]) if path is not None and path.bounds else 0
        order.append(gname); paths[gname] = (path, adv)
        if base:
            bases.append(gname)
        for cp in cps:
            cmap[cp] = gname
        print(".", end="", flush=True)

    def letter(name, f, variant=None):
        bd, dt, adv = compose(name, f, variant)
        if style == "Bold":
            return level_dots(name, union(bd, dt) if dt is not None else bd, form=f), adv
        m = union(bd, dt) if dt is not None else bd
        if name == "hamza":                                   # ء is mark-thin: thinned in proportion
            path, adv = derive(None, None, adv, stem_t, thin=m, thin_w=stroke_w(m))
        elif name == "gaf":                                   # گ's second bar: thinned in proportion
            bar = union(*[c for c in contours(m) if c.bounds[1] > X - 25])
            rest = union(*[c for c in contours(m) if c.bounds[1] <= X - 25])
            path, adv = derive(rest, None, adv, stem_t, thin=bar, thin_w=stroke_w(bar))
        else:
            lt, dots = level_dots(name, m, parts=True, form=f)   # dot size and lines fixed on the master
            if dots is None:                                  # nothing to level: derive as drawn
                path, adv = derive(bd, dt, adv, stem_t)
            else:
                path, adv = derive(lt, dots, adv, stem_t)
        path = bridge_stubs(path, adv, f)
        return level_dots(name, path, resize=False, form=f), adv   # re-weighted dots back on the lines

    names_by_cp = {}
    letters = dict(G.LETTERS)
    letters["heh"] = ([0x0647, 0x06BE, 0x06C1], "D", None)       # ھ ہ draw as ه
    letters["alefwasla"] = ([0x0671], "R", None)                 # ٱ
    letters["hehyeh"] = ([0x06C0], "R", None)                    # ۀ
    letters["ae"] = ([0x06D5], "R", None)                        # ە
    for name, (cps, jt, fn) in letters.items():
        for cp in cps:
            names_by_cp[cp] = name
        forms = {"D": ["isol", "init", "medi", "fina"], "R": ["isol", "fina"], "U": ["isol"]}[jt]
        for f in forms:
            gname = name if f == "isol" else f"{name}.{f}"
            path, w = letter(name, f)
            add(gname, path, round(w), cps if f == "isol" else [])
            if f != "isol":
                subs[f].append(f"    sub {name} by {gname};")
    # لا keeps the right serif on its alef (note 11)
    for a in ("alef", "alefmadda", "alefhamza", "alefhamzabelow"):
        path, w = letter(a, "fina", "la")
        add(f"{a}.fina.la", path, round(w), [])

    # Urdu ٹ ڈ ڑ ے (Google Fonts Arabic Core; Aly 14 Nov 2026). The small ط is Kuhmard's own ط,
    # scaled down and thickened back to the weight of a dot bar; it takes the place of the dots of
    # ث / ذ / ز. ے is the head of ی on a flat tail that runs left on the baseline and turns up at its
    # end like the final ی.
    def small_tah(h=150, grow=14):
        t = paths["tah"][0]; b = t.bounds; s = (h - 2 * grow) / (b[3] - b[1])
        t = xform(t, (s, 0, 0, s, -b[0] * s, -b[1] * s))
        st = pathops.Path(); t.draw(st.getPen())
        st.stroke(2 * grow, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 4)
        t = union(t, st); b = t.bounds
        return shift(t, -(b[0] + b[2]) / 2, -b[1])
    ST = small_tah()
    for uname, src, cp, forms in (("tteh", "theh", 0x0679, ("isol", "init", "medi", "fina")),
                                  ("ddal", "thal", 0x0688, ("isol", "fina")),
                                  ("rreh", "zain", 0x0691, ("isol", "fina"))):
        for f in forms:
            sname = src if f == "isol" else f"{src}.{f}"
            lt, mk = split_marks(paths[sname][0]); mb = mk.bounds
            y = min(mb[1], TALL - (ST.bounds[3] - ST.bounds[1]))
            gname = uname if f == "isol" else f"{uname}.{f}"
            add(gname, union(lt, shift(ST, (mb[0] + mb[2]) / 2, y)), widths[sname], [cp] if f == "isol" else [])
            if f != "isol":
                subs[f].append(f"    sub {uname} by {gname};")
    yh = paths["yeh"][0]; L = 330
    head = union(inter(yh, rect(336, 89, 900, 400)), rect(336, 0, 496, 100))
    tail = union(rect(56, 0, 496 + L, 89), rect(56, 0, 209, 252), rect(209, 164, 276, 252))
    add("yehbarree", union(shift(head, L), tail), widths["yeh"] + L, [0x06D2])
    add("yehbarree.fina", union(tail, rect(56, 0, 496 + L + 120, 89)), 496 + L + 120, [])
    subs["fina"].append("    sub yehbarree by yehbarree.fina;")

    # digits: Aly's drawings (Persian, Arabic-Indic and keyboard digits share one design)
    for n in range(10):
        path, w = letter(f"digit{n}", "isol")
        add(f"digit{n}", path, round(w), [0x06F0 + n, 0x0660 + n, 0x30 + n])
    # punctuation: drawn comma, question mark and full stop; the rest composed from them
    drawn = {}
    for pname, cps in (("arabiccomma", [0x060C]), ("arabicquestion", [0x061F]), ("period", [0x002E, 0x06D4])):
        path, w = letter(pname, "isol")
        add(pname, path, round(w), cps); drawn[pname] = path

    def fit(p, cps, name):
        b = p.bounds
        add(name, shift(p, SB - b[0]), round(SB + (b[2] - b[0]) + SB), cps)

    dotp = drawn["period"]; db = dotp.bounds; dh = db[3] - db[1]; dw = db[2] - db[0]
    dot0 = shift(dotp, -db[0], -db[1])                      # full stop at (0, 0)
    com = drawn["arabiccomma"]; cb = com.bounds
    com0 = shift(com, -cb[0], -cb[1])
    fit(union(dot0, shift(com0, 0, dh + 120)), [0x061B], "arabicsemicolon")
    fit(union(dot0, shift(dot0, 0, dh + 150)), [0x003A], "colon")
    fit(union(dot0, rect((dw - STEM * stem_t / STEM) / 2, dh + 90, (dw + stem_t) / 2, ASC)), [0x0021], "exclam")
    fit(union(dot0, shift(dot0, dw + 70), shift(dot0, 2 * (dw + 70))), [0x2026], "ellipsis")
    fit(shift(dot0, 0, 180 - dh / 2), [0x00B7], "periodcentered")
    fit(shift(E.scale(dot0, 1.3), 0, 180 - 0.65 * dh), [0x2022], "bullet")
    lat = xform(com0, (-1, 0, 0, -1, 0, 0))                  # Latin comma: the Persian one turned over,
    lat = shift(lat, -lat.bounds[0], dh - lat.bounds[3])      # head on the baseline, tail below
    fit(lat, [0x002C], "comma")
    fit(union(shift(dot0, 0, dh + 150), lat), [0x003B], "semicolon")
    fit(E.scale(com0, 0.72), [0x066C], "thousandsep")
    fit(mirror(drawn["arabicquestion"]), [0x003F], "question")
    for pname, cps in E.PUNCT.items():
        if pname in ("period", "colon", "exclam", "arabiccomma", "arabicsemicolon", "arabicquestion"):
            continue
        fit(kit.punct(pname), cps + ([0x0025] if pname == "percent" else []), pname)
    for sname, cps in E.SYMBOLS.items():
        fit(kit.symbol(sname), cps, sname)
    # diacritics: zero width, centred on x=0
    drawn_marks = json.load(open(os.path.join(HERE, "marks_drawn.json")))["marks"] if os.path.exists(os.path.join(HERE, "marks_drawn.json")) else {}
    for mname, (p, where) in kit.marks().items():
        if mname in drawn_marks:                      # Aly's drawing (signs.ai, 4 Nov)
            p = P(drawn_marks[mname]["d"]); where = drawn_marks[mname]["where"]
        add(mname, p, 0, [E.MARKS[mname]], base=False)
        (marks_top if where == "top" else marks_bot).append(mname)

    # copied text: presentation forms and lam-alef ligatures
    pf, ligs = presentation_forms(names_by_cp, set(order))
    for g, (form, alef) in ligs.items():
        lam_g = "lam.init" if form == "isol" else "lam.medi"
        lp, la = paths[lam_g]; ap, aa = paths[f"{alef}.fina.la"]
        add(g, union(ap, shift(lp, aa)), la + aa, [])      # alef sits left of lam
    cmap.update(pf)
    letter_glyphs = [g for g in bases if g.split(".")[0] in letters and not g.endswith(".la") and not g.startswith("lam_")]
    kpairs, kalts, ksubs, klefts, krights = kerning(paths, bases, letter_glyphs)
    print("right serifs:", krights)
    for g, (p, w) in kalts.items():
        add(g, p, round(w), [])
    if WRITTEN and style == "Bold":                # after kerning, which stays measured on the plain outlines
        for g in bases:
            if (g.split(".")[0] in letters or g.startswith("lam_")) and not g.startswith("tatweel"):
                bits = g.split(".")
                form = bits[1] if len(bits) > 1 and bits[1] in ("init", "medi", "fina") else "isol"
                q = written_feel(paths[g][0], paths[g][1], form)
                paths[g] = (q, paths[g][1])
                cs[g] = charstring(q, widths[g]); lsb[g] = int(q.bounds[0])
    ds_src = {}                                    # dot moves (dotfix): only the dots move, kerning stays
    for rd in dot_rounds:
        for g, (src, dx) in rd["alts"].items():
            if g in paths:
                continue
            lt, mk = split_marks(paths[src][0])
            q, w = widened(lt, mk, dx, paths[src][1], src)
            add(g, q, round(w), [])
            ds_src[g] = src
    # Latin: a character the font did not have gets its glyph directly; where a Persian-style glyph
    # already holds the character (digits, + = % ( ) ...), the Latin one is an alternate that shows
    # in Latin text (locl under script latn) and everywhere with stylistic set 1
    lat = LATIN["styles"].get(style)
    latin, latin_swaps, latin_marks = [], {}, []   # latin_marks: combining accents U+0300-036F (zero width, GDEF marks)
    if lat:
        for gname, g in lat["glyphs"].items():
            taken = [cp for cp in g["cps"] if cp in cmap]
            if taken:
                alt = gname + ".latn"
                add(alt, P(g["d"]), g["adv"], [], base=False)
                for cp in taken:
                    latin_swaps.setdefault(cmap[cp], alt)
                latin.append(alt)
            else:
                add(gname, P(g["d"]), g["adv"], g["cps"], base=False)
                (latin_marks if all(0x300 <= cp <= 0x36F for cp in g["cps"]) else latin).append(gname)
    # Google Fonts Latin Core language forms (1.002, Aly 15 Nov 2026), cut from Rokkitt's own letters:
    #   caroncomb.alt: the apostrophe caron of ď ľ ť Ľ, for d l t L followed by U+030C
    #   idotaccent: Turkish, Azerbaijani, Crimean Tatar, Kazakh, Tatar i keeps its dot (locl)
    #   periodcentered.loclCAT (.case): the Catalan dot of l·l / L·L, spaced as Rokkitt's ŀ / Ŀ
    lang_forms = {}
    if lat and all(n in paths for n in ("uni0064", "uni010F", "uni0069", "uni006C", "uni0140", "uni004C", "uni013F")):
        caron_bases = {}
        for comp, base in (("uni010F", "uni0064"), ("uni013E", "uni006C"), ("uni0165", "uni0074"), ("uni013D", "uni004C")):
            if comp in paths and base in paths:
                part = diff(paths[comp][0], paths[base][0])
                caron_bases[base] = (part, part.bounds)
        part, (cx0, cy0, _, _) = caron_bases["uni0064"]
        add("caroncomb.alt", shift(part, -round(cx0), 0), 0, [], base=False)
        lang_forms["caron_anchor"] = {b: (round(bb[0] - cx0 + round(cx0)), round(bb[1] - cy0)) for b, (_, bb) in caron_bases.items()}
        add("idotaccent", paths["uni0069"][0], paths["uni0069"][1], [], base=False)
        latin.append("idotaccent")
        l_adv, L_adv = paths["uni006C"][1], paths["uni004C"][1]
        dot_l = diff(paths["uni0140"][0], paths["uni006C"][0])
        add("periodcentered.loclCAT", shift(dot_l, -l_adv), paths["uni0140"][1] - l_adv, [], base=False)
        dot_L = diff(paths["uni013F"][0], paths["uni004C"][0])
        add("periodcentered.loclCAT.case", shift(dot_L, -L_adv), paths["uni013F"][1] - L_adv, [], base=False)
        latin += ["periodcentered.loclCAT", "periodcentered.loclCAT.case"]
        lang_forms["dots"] = [g for g in ("periodcentered", "uni00B7", "uni00B7.latn") if g in paths]
    print()
    print(f"latin: {len(latin)} glyphs, {len(latin_swaps)} shown only in Latin text")
    print(f"kerning: {len(kpairs)} pairs, {len(kalts)} dot-shifted alternates; left serifs {klefts}; right serifs {len(krights)} glyphs")

    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    ps = f"{FAMILY}-{style}"; full = f"{FAMILY} {style}"
    fb.setupCFF(ps, {"FullName": full, "FamilyName": FAMILY, "Weight": style}, cs, {})
    fb.setupHorizontalMetrics({g: (widths[g], lsb[g]) for g in order})
    fb.setupHorizontalHeader(ascent=LINE_ASC, descent=-LINE_DESC)
    rib = style in ("Regular", "Bold")
    names = {
        "familyName": FAMILY if rib else f"{FAMILY} {style}",
        "styleName": style if rib else "Regular",
        "uniqueFontIdentifier": f"{ps}-{VERSION}",
        "fullName": full, "psName": ps, "version": f"Version {VERSION}",
        "copyright": "Copyright 2026 The Kuhmard Project Authors (https://github.com/azrast-type/kuhmard)."
                     " Letterforms after the lettering of the 3rd Tehran International Film Festival (1974)."
                     + (" Latin letters, digits and signs adapted from " + LATIN["source"] + "." if lat else ""),
        # credits: the Azrast team (Aly, 14 Nov 2026)
        "manufacturer": "Azrast",
        "designer": CREDITS,
        "vendorURL": "https://azrast.com",
        "designerURL": "https://azrast.com",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                              "This license is available with a FAQ at: https://openfontlicense.org",
        "licenseInfoURL": "https://openfontlicense.org",
    }
    if not rib:
        names["typographicFamily"] = FAMILY; names["typographicSubfamily"] = style
    fb.setupNameTable(names)
    # the Persian name, for menus in a Persian-language system (Windows, language 0x0429)
    nt = fb.font["name"]
    for nid in ((1, 2) if rib else (1, 2, 16, 17)):
        en = nt.getName(nid, 3, 1, 0x409)
        if en is None:
            continue
        txt = str(en)
        if nid in (1, 16):
            txt = FAMILY_FA if (nid == 16 or rib) else f"{FAMILY_FA} {style}"
        nt.setName(txt, nid, 3, 1, 0x0429)
    nt.setName(FAMILY_FA + " " + style, 4, 3, 1, 0x0429)
    fb.setupOS2(sTypoAscender=LINE_ASC, sTypoDescender=-LINE_DESC, sTypoLineGap=0,
                usWinAscent=LINE_ASC, usWinDescent=LINE_DESC, sxHeight=X, sCapHeight=ASC, usWeightClass=wclass,
                fsSelection=(0x20 if style == "Bold" else 0x40) | 0x80, achVendID="AZRS", version=4,
                fsType=0)  # 0 = installable, as the OFL and Google Fonts require; AZRS = Azrast (to register with Microsoft)
    fb.font["head"].macStyle = 1 if style == "Bold" else 0
    fb.font["head"].fontRevision = float(VERSION)  # matches "Version x.xxx" in the name table
    fb.setupPost()

    # ---- features
    fea = ["languagesystem DFLT dflt;", "languagesystem arab dflt;", "languagesystem arab FAR;"]
    if lat:
        fea.append("languagesystem latn dflt;")
    LANGS_I = ("TRK", "AZE", "CRT", "KAZ", "TAT")          # i keeps its dot (idotaccent)
    if lang_forms:
        fea += [f"languagesystem latn {t};" for t in LANGS_I + ("CAT",)]
    fea.append("@BASES = [" + " ".join(bases + latin) + "];")
    fea.append("@MARKS = [" + " ".join(marks_top + marks_bot + latin_marks + (["caroncomb.alt"] if lang_forms else []) + ["zwnj", "zwj", "zerowidth"]) + "];")
    fea.append("table GDEF { GlyphClassDef @BASES, , @MARKS, ; } GDEF;")
    if latin_swaps:
        sw = "\n".join(f"    sub {a} by {b};" for a, b in latin_swaps.items())
        fea.append("feature locl {\n    script latn;\n" + sw + "\n} locl;")
    if lang_forms:
        dots = "[" + " ".join(lang_forms["dots"]) + "]"
        loc = ["feature locl {", "    script latn;"]
        for t in LANGS_I:
            loc += [f"    language {t};", "    lookup locl_i { sub uni0069 by idotaccent; } locl_i;" if t == LANGS_I[0] else "    lookup locl_i;"]
        loc += ["    language CAT;", "    lookup locl_cat {",
                f"        sub uni006C {dots}' uni006C by periodcentered.loclCAT;",
                f"        sub uni004C {dots}' uni004C by periodcentered.loclCAT.case;",
                "    } locl_cat;", "} locl;"]
        fea.append("\n".join(loc))
        fea.append('feature ss01 {\n    featureNames { name "Latin digits and signs"; };\n' + sw + "\n} ss01;")
    for f in ("init", "medi", "fina"):
        fea.append(f"feature {f} {{\n" + "\n".join(subs[f]) + f"\n}} {f};")
    la = "\n".join(f"    sub [lam.init lam.medi] {a}.fina' by {a}.fina.la;" for a in ("alef", "alefmadda", "alefhamza", "alefhamzabelow"))
    # Aly 9 Nov: الله takes its shadda on the second lam by itself (not when one is typed: no IgnoreMarks)
    allah = "  lookup allah {\n    sub [alef alef.fina] lam.init lam.medi' [heh.fina heh.medi] by lam.medi shadda;\n  } allah;"
    fea.append(f"feature rlig {{\n{la}\n{allah}\n}} rlig;")
    if ksubs:
        cs_ = "\n".join(f"    sub {a} {b}' by {alt};" for a, b, alt in ksubs)
        fea.append(f"feature calt {{\n    lookupflag IgnoreMarks;\n{cs_}\n}} calt;")
    for i, rd in enumerate(dot_rounds):
        made = {}
        for r, l, w, alt in rd["rules"]:
            made.setdefault(r if w == "right" else l, set()).add(alt)
        ctx = lambda g: "[" + " ".join([g] + sorted(made.get(g, ()))) + "]"   # a neighbour changed in the same round still counts
        lines = [f"    sub {r}' {ctx(l)} by {alt};" if w == "right" else f"    sub {ctx(r)} {l}' by {alt};"
                 for r, l, w, alt in rd["rules"]]
        fea.append(f"feature calt {{\n  lookup dots{i + 1} {{\n    lookupflag IgnoreMarks;\n" + "\n".join(lines) + f"\n  }} dots{i + 1};\n}} calt;")
    kp = "\n".join(kpairs)
    def _k(a, b):
        for l in kpairs:
            p = l.split()
            if p[1] == a and p[2] == b:
                return l.split("<")[1].split()[0]
        return "0"
    alt_pairs = "\n".join(f"    pos {a} {alt} <{_k(a, b)} 0 {_k(a, b)} 0>;" for a, b, alt in ksubs)
    klines = [l for l in (kp + "\n" + alt_pairs).split("\n") if l.strip()]
    for g, src in ds_src.items():                  # a dot-moved glyph kerns exactly like its source
        for l in list(klines):
            t = l.split()
            if src in (t[1], t[2]):
                klines.append("    pos " + " ".join(g if x == src else x for x in t[1:3]) + " " + " ".join(t[3:]))
    fea.append("feature kern {\n    lookupflag IgnoreMarks;\n" + "\n".join(dict.fromkeys(klines)) + "\n} kern;")
    if lat:
        have = set(latin)
        for side, groups in (("KL", lat["kern_left"]), ("KR", lat["kern_right"])):
            for i, grp in enumerate(groups):
                fea.append(f"@{side}{i} = [" + " ".join(g for g in grp if g in have) + "];")
        pairs = "\n".join(f"    pos @KL{l} @KR{r} {k};" for l, r, k in lat["kern"])
        fea.append("@LATN = [" + " ".join(latin) + "];")
        # the word space is the Persian one (narrow); after a Latin glyph it opens to Rokkitt's own space
        fea.append("feature kern {\n  lookup latn_pairs {\n" + pairs + "\n  } latn_pairs;\n  lookup latn_space {\n"
                   f"    pos @LATN space' {lat['space'] - SPACE_W};\n  }} latn_space;\n}} kern;")
    fea.append("markClass [" + " ".join(marks_top) + "] <anchor 0 0> @TOP;")
    fea.append("markClass [" + " ".join(marks_bot) + "] <anchor 0 0> @BOT;")
    rows = []
    for g in bases:
        p, adv = paths[g]
        (tx, ty), (bx, by) = anchors(p, adv, g)
        rows.append(f"    pos base {g} <anchor {tx} {ty}> mark @TOP <anchor {bx} {by}> mark @BOT;")
    fea.append("feature mark {\n" + "\n".join(rows) + "\n} mark;")
    # Latin combining accents (Google Fonts, Dutch íj́; Aly 14 Nov 2026): Rokkitt draws them for the
    # lowercase, so a top accent hangs from the x-height (364) and a bottom one from the baseline; each
    # Latin letter carries its top anchor at its own top and its bottom anchor on the baseline, centred
    # on the ink there (the stem of i and j, not the hook)
    if latin_marks:
        ltop = [m for m in latin_marks if paths[m][0].bounds[1] > 150]
        lbot = [m for m in latin_marks if m not in ltop]
        for m in ltop:
            b = paths[m][0].bounds
            fea.append(f"markClass {m} <anchor {round((b[0] + b[2]) / 2)} {X}> @LTOP;")
        for m in lbot:
            b = paths[m][0].bounds
            fea.append(f"markClass {m} <anchor {round((b[0] + b[2]) / 2)} 0> @LBOT;")
        lrows = []
        for g in latin:
            p = paths[g][0]
            if p is None or not p.bounds:
                continue
            top = p.bounds[3]
            tb, bb = inter(p, rect(-1e5, top - 60, 1e5, top + 1)).bounds, inter(p, rect(-1e5, 0, 1e5, 60)).bounds
            tx = round((tb[0] + tb[2]) / 2) if tb[2] > tb[0] else round((p.bounds[0] + p.bounds[2]) / 2)
            bx = round((bb[0] + bb[2]) / 2) if bb[2] > bb[0] else tx
            lrows.append(f"    pos base {g} <anchor {tx} {round(max(top, X))}> mark @LTOP <anchor {bx} 0> mark @LBOT;")
        fea.append("feature mark {\n  lookup latn_marks {\n" + "\n".join(lrows) + "\n  } latn_marks;\n} mark;")
        if ltop and "uni0131" in paths and "uni0237" in paths:      # i and j drop their dot under a top accent
            fea.append("feature ccmp {\n    sub uni0069' [" + " ".join(ltop) + "] by uni0131;\n"
                       "    sub uni006A' [" + " ".join(ltop) + "] by uni0237;\n} ccmp;")
    if lang_forms:                                  # d l t L + U+030C draw as ď ľ ť Ľ
        ca = lang_forms["caron_anchor"]
        fea.append("feature ccmp {\n    sub [" + " ".join(ca) + "] uni030C' by caroncomb.alt;\n} ccmp;")
        fea.append("markClass caroncomb.alt <anchor 0 0> @LCARON;")
        fea.append("feature mark {\n  lookup latn_caron {\n" + "\n".join(
            f"    pos base {b} <anchor {x} {y}> mark @LCARON;" for b, (x, y) in ca.items()) + "\n  } latn_caron;\n} mark;")
    mk = []
    for m in marks_top:
        b = paths[m][0].bounds
        mk.append(f"    pos mark {m} <anchor 0 {round(b[3] + 40)}> mark @TOP;")
    for m in marks_bot:
        b = paths[m][0].bounds
        mk.append(f"    pos mark {m} <anchor 0 {round(b[1] - 40)}> mark @BOT;")
    fea.append("feature mkmk {\n" + "\n".join(mk) + "\n} mkmk;")
    addOpenTypeFeaturesFromString(fb.font, "\n".join(fea))
    # keep the feature code as a file too: export_ufo.py puts it in the UFO source (Google Fonts)
    os.makedirs(os.path.join(HERE, "features"), exist_ok=True)
    with open(os.path.join(HERE, "features", f"{ps}.fea"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(fea) + "\n")
    fb.font["OS/2"].recalcCodePageRanges(fb.font)  # Fontbakery: code pages must be set

    os.makedirs(os.path.join(HERE, "otf"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "woff2"), exist_ok=True)
    out = os.path.join(HERE, "otf", f"{ps}.otf")
    fb.save(out)
    fb.font.flavor = "woff2"
    fb.save(os.path.join(HERE, "woff2", f"{ps}.woff2"))
    print("saved", out, len(order), "glyphs")


def build_with_dotfix(style, rounds_max=4):
    """Build, scan for crowded dots, add the dot moves, rebuild; repeat until the scan is clean."""
    import dotfix
    otf = os.path.join(HERE, "otf", f"{FAMILY}-{style}.otf")
    rounds = []
    build(style, rounds)
    for _ in range(rounds_max):
        known = {a: v for rd in rounds for a, v in rd["alts"].items()}
        alts, rules, unsolved = dotfix.plan(otf, known)
        print(f"dot round {len(rounds) + 1}: {len(rules)} moves, {len(alts)} new alternates, {len(unsolved)} unsolved")
        for u in unsolved:
            print("   unsolved", u)
        if not rules:
            break
        rounds.append({"alts": alts, "rules": rules})
        build(style, rounds)
    json.dump(rounds, open(os.path.join(HERE, f"dotfix-{style}{'-written' if WRITTEN else ''}.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    for st in (sys.argv[1:] or list(WEIGHTS)):
        build_with_dotfix(st)
