"""Export the Latin letters for Kuhmard from Rokkitt (SIL Open Font License) into latin_glyphs.json.

For each weight of the family the Rokkitt weight is solved so that, once the lowercase is scaled to
the Persian letter height (364), its stem equals the Persian stem of that weight. Letters (basic,
Western and Central European accents), Latin digits, a few currency signs and the kerning between
letters are written out in Kuhmard's own units. build_ai.py reads only the JSON.

Run (the fonts are downloads, so in isolated mode):
  python3 -I latin_export.py <Rokkitt-VF.ttf> <out.json>
"""
import sys, json, os, tempfile

import numpy as np
import pathops
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen

SRC, OUT = sys.argv[1], sys.argv[2]
X_P = 364
STEMS = {"Light": 73, "Regular": 95, "Medium": 118, "Bold": 151, "Black": 174}   # Bold = the 7 Nov master stem
LETTERS = (list(range(0x41, 0x5B)) + list(range(0x61, 0x7B)) + [c for c in range(0xC0, 0x100) if c not in (0xD7, 0xF7)]
           + list(range(0x100, 0x180)) + [0x1E9E])
EXTRA = [0xAA, 0xBA]
# Google Fonts Latin Core (Aly, 14 Nov 2026): Romanian, Welsh, dotless j, spacing and combining accents, signs
LETTERS += [0x218, 0x219, 0x21A, 0x21B, 0x237, 0x1E80, 0x1E81, 0x1E82, 0x1E83, 0x1E84, 0x1E85, 0x1EF2, 0x1EF3]
EXTRA += ([0xA1, 0xA8, 0xAE, 0xAF, 0xB4, 0xB6, 0xB8, 0xBF, 0x2C6, 0x2C7, 0x2D8, 0x2D9, 0x2DA, 0x2DB, 0x2DC, 0x2DD]
          + [0x300, 0x301, 0x302, 0x303, 0x304, 0x306, 0x307, 0x308, 0x30A, 0x30B, 0x30C, 0x326, 0x327, 0x328])
# numeric and mathematical glyphs (Aly, 5 Nov): digits, operators, fractions, brackets, currency, Greek used in maths
SYMBOLS = (list(range(0x30, 0x3A)) + [0x23, 0x24, 0x25, 0x26, 0x28, 0x29, 0x2A, 0x2B, 0x2D, 0x2F, 0x3C, 0x3D, 0x3E, 0x40, 0x5B, 0x5C, 0x5D,
           0x5E, 0x5F, 0x7B, 0x7C, 0x7D, 0x7E, 0xA2, 0xA3, 0xA5, 0xA7, 0xAC, 0xB0, 0xB1, 0xB5, 0xB9, 0xB2, 0xB3, 0xBC, 0xBD, 0xBE, 0xD7, 0xF7,
           0xB7, 0x2030, 0x20AC, 0x2202, 0x2205, 0x2206, 0x220F, 0x2211, 0x2212, 0x2215, 0x2219, 0x221A, 0x221E, 0x222B, 0x2248, 0x2260,
           0x2264, 0x2265, 0x03C0, 0x03A9, 0x2126, 0x25CA, 0x2044, 0x2074, 0x2122, 0x2116])
ARROWS = {0x2192: "right", 0x2190: "left", 0x2191: "up", 0x2193: "down", 0x2194: "both", 0x21C4: "right_left", 0x21C6: "left_right"}


def rect_path(x0, y0, x1, y1):
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return p


def union(*ps):
    out = pathops.Path(); pathops.union(list(ps), out.getPen()); return out


def xf(p, t):
    q = pathops.Path(); p.draw(TransformPen(q.getPen(), t)); return q


def arrow_right(x0, x1, y, t, a):
    """Shaft from x0 to the tip at x1 on height y, stroke t, head arms reaching a back and a up/down."""
    r2 = 2 ** 0.5
    cx = x1 - t / r2                                    # centre-line tip, so the outer point lands on x1
    L = a * r2
    arm = rect_path(-L, -t / 2, t / 2, t / 2)           # along -x from the tip, square start that mitres with its twin
    c = 1 / r2
    up = xf(arm, (c, -c, c, c, cx, y))                  # rotate 45 degrees: the arm runs back and up
    dn = xf(arm, (c, c, -c, c, cx, y))
    return union(rect_path(x0, y - t / 2, cx, y + t / 2), up, dn)


def arrows(t, axis, caps):
    """The arrows Rokkitt lacks, drawn with its minus-sign stroke on its maths axis."""
    sb, Lh, a = 55, 560, 150
    out = {}
    R = arrow_right(sb, sb + Lh, axis, t, a); adv = Lh + 2 * sb
    mir = lambda p: xf(p, (-1, 0, 0, 1, adv, 0))
    out["right"] = (R, adv); out["left"] = (mir(R), adv)
    half = arrow_right(adv / 2, sb + Lh, axis, t, a)
    out["both"] = (union(half, mir(half)), adv)
    cy = caps / 2; Lv = caps + 20; hw = a + t                 # vertical: tip at the capital height
    V = arrow_right(-Lv / 2, Lv / 2, 0, t, a)
    advv = round(2 * hw + 2 * sb)
    out["up"] = (xf(V, (0, 1, -1, 0, advv / 2, cy)), advv)
    out["down"] = (xf(V, (0, -1, 1, 0, advv / 2, cy)), advv)
    a2 = a * 0.62; d = a2 + t * 0.5
    top, bot = arrow_right(sb, sb + Lh, axis + d, t, a2), arrow_right(sb, sb + Lh, axis - d, t, a2)
    out["right_left"] = (union(top, mir(bot)), adv)           # rightwards over leftwards
    out["left_right"] = (union(mir(top), bot), adv)           # leftwards over rightwards
    return out



def outline(tt, g):
    gs = tt.getGlyphSet(); p = pathops.Path(); gs[g].draw(p.getPen(glyphSet=gs)); p.simplify(fix_winding=True)
    return p


def measure(tt):
    cm = tt.getBestCmap()
    xh = outline(tt, cm[ord("x")]).bounds[3]
    cap = outline(tt, cm[ord("H")]).bounds[3]
    I = outline(tt, cm[ord("I")])
    band = pathops.Path(); pen = band.getPen()
    pen.moveTo((-2000, cap / 2 - 1)); pen.lineTo((4000, cap / 2 - 1)); pen.lineTo((4000, cap / 2 + 1)); pen.lineTo((-2000, cap / 2 + 1)); pen.closePath()
    b = pathops.op(I, band, pathops.PathOp.INTERSECTION).bounds
    return xh, cap, b[2] - b[0]


def solve(stem_target):
    ax = [a for a in TTFont(SRC)["fvar"].axes if a.axisTag == "wght"][0]
    lo, hi = ax.minValue, ax.maxValue
    for _ in range(11):
        w = (lo + hi) / 2
        tt = instancer.instantiateVariableFont(TTFont(SRC), {"wght": w})
        xh, cap, stem = measure(tt)
        if stem * X_P / xh < stem_target: lo = w
        else: hi = w
    w = round((lo + hi) / 2)
    tt = instancer.instantiateVariableFont(TTFont(SRC), {"wght": w})
    return w, tt


out = {"source": "Rokkitt, Copyright 2016 The Rokkit Project Authors (https://github.com/googlefonts/RokkittFont), SIL Open Font License 1.1", "styles": {}}
for style, target in STEMS.items():
    w, tt = solve(target)
    xh, cap, stem = measure(tt)
    s = X_P / xh
    cm = tt.getBestCmap(); hm = tt["hmtx"]
    glyphs = {}
    def put(name, g, cps, path=None, adv=None):
        if path is None:
            p = outline(tt, g)
            q = pathops.Path(); p.draw(TransformPen(q.getPen(), (s, 0, 0, s, 0, 0)))
        else:
            q = path
        pen = SVGPathPen(None, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
        q.draw(pen)
        glyphs[name] = {"d": pen.getCommands(), "adv": round(hm[g][0] * s) if adv is None else round(adv), "cps": cps}
    by_glyph = {}
    for cp in LETTERS + EXTRA + SYMBOLS:
        if cp in cm:
            by_glyph.setdefault(cm[cp], []).append(cp)
    names = {}
    for g, cps in by_glyph.items():
        names[g] = "uni%04X" % cps[0]
        put(names[g], g, cps)
    mb = outline(tt, cm[0x2212]).bounds                        # the minus sign gives the maths stroke and axis
    t, axis = (mb[3] - mb[1]) * s, (mb[1] + mb[3]) / 2 * s
    for cp, kind in ARROWS.items():
        if cp not in cm:
            path, adv = arrows(t, axis, cap * s)[kind]
            put("uni%04X" % cp, None, [cp], path, adv)
    # kerning between letters, read from the shaped font
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, "i.ttf"); tt.save(f)
        font = hb.Font(hb.Face(hb.Blob.from_file_path(f)))
    letters = [(g, cps[0]) for g, cps in by_glyph.items() if cps[0] in LETTERS]
    K = np.zeros((len(letters), len(letters)), int)
    feats = {"kern": True, "liga": False, "clig": False, "calt": False, "dlig": False}
    for i, (ga, ca) in enumerate(letters):
        for j, (gb, cb) in enumerate(letters):
            buf = hb.Buffer(); buf.add_str(chr(ca) + chr(cb)); buf.guess_segment_properties(); hb.shape(font, buf, feats)
            if len(buf.glyph_infos) != 2:
                continue
            k = (buf.glyph_positions[0].x_advance - hm[ga][0]) * s
            if abs(k) >= 4:
                K[i, j] = round(k)
    # glyphs with the same row (or column) kern alike: one class each
    def classes(M):
        seen = {}
        for i in range(M.shape[0]):
            seen.setdefault(M[i].tobytes(), []).append(i)
        return [v for v in seen.values()]
    L = [c for c in classes(K) if K[c[0]].any()]; R = [c for c in classes(K.T) if K[:, c[0]].any()]
    kern = [[li, ri, int(K[lc[0], rc[0]])] for li, lc in enumerate(L) for ri, rc in enumerate(R) if K[lc[0], rc[0]]]
    out["styles"][style] = {"wght": w, "scale": round(s, 5), "stem": round(stem * s), "caps": round(cap * s), "space": round(hm[cm[0x20]][0] * s),
                            "glyphs": glyphs, "kern_left": [[names[letters[i][0]] for i in c] for c in L],
                            "kern_right": [[names[letters[i][0]] for i in c] for c in R], "kern": kern}
    print(style, "Rokkitt weight", w, "stem", round(stem * s), "(target %d)" % target, "caps", round(cap * s), "glyphs", len(glyphs),
          "kern classes", len(L), "x", len(R), "pairs", len(kern), "space", out["styles"][style]["space"])
json.dump(out, open(OUT, "w"))
print("saved", OUT, os.path.getsize(OUT) // 1024, "KB")
