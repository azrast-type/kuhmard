"""Check that a font built from the UFO matches the font build_ai.py made.

    python3 compare_ufo_build.py otf/Kuhmard-Bold.otf from-ufo/Kuhmard-Bold.otf

Compares glyph order, outlines, advance widths, the character map, the name table, vertical
metrics and OS/2 values, then shapes thousands of strings with HarfBuzz in both fonts
(every character alone, every pair of Persian/Arabic letters, Persian words with marks,
every pair of Latin letters, Latin with combining accents, the ss01 set) and compares the
glyphs and positions. Prints the differences and exits 1 if there are any.

Needs: fontTools, uharfbuzz, skia-pathops.
"""
import itertools
import sys

import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont


def outline(gs, g):
    """The glyph's contours, each as its list of drawing steps; sorted, because fontmake may
    write a glyph's separate contours (a dot, the body) in another order, which draws the same."""
    pen = DecomposingRecordingPen(gs)
    gs[g].draw(pen)
    contours, cur = [], []
    for op, pts in pen.value:
        cur.append((op, tuple((round(x, 2), round(y, 2)) for x, y in pts)))
        if op in ("closePath", "endPath"):
            contours.append(tuple(cur))
            cur = []
    if cur:
        contours.append(tuple(cur))
    return sorted(contours)


def same_shape(gsa, gsb, g):
    """fontmake tidies outlines: it drops a point in the middle of a straight edge and turns a
    curve whose handles lie on its line into a line. The drawing steps then differ but the shape
    does not. Overlay the two shapes and measure the area that is in one and not the other."""
    import pathops

    def path(gs):
        p = pathops.Path()
        gs[g].draw(pathops.PathPen(p, gs))
        return p
    pa, pb = path(gsa), path(gsb)
    xor = pathops.op(pa, pb, pathops.PathOp.XOR)
    return abs(xor.area) < 0.5          # under half a square unit, in a 1000-unit em


def shaper(path):
    blob = hb.Blob.from_file_path(path)
    font = hb.Font(hb.Face(blob))
    return font


def shape(font, names, text, features=None, script=None, lang=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if script:
        buf.script = script
    if lang:
        buf.language = lang
    hb.shape(font, buf, features or {})
    return [(names[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def main(a_path, b_path):
    a, b = TTFont(a_path), TTFont(b_path)
    problems = []

    oa, ob = a.getGlyphOrder(), b.getGlyphOrder()
    if oa != ob:
        problems.append(f"glyph order differs ({len(oa)} vs {len(ob)})")
    gsa, gsb = a.getGlyphSet(), b.getGlyphSet()
    for g in oa:
        if g not in gsb:
            problems.append(f"missing glyph {g}")
            continue
        if a["hmtx"][g][0] != b["hmtx"][g][0]:
            problems.append(f"width {g}: {a['hmtx'][g][0]} vs {b['hmtx'][g][0]}")
        if outline(gsa, g) != outline(gsb, g) and not same_shape(gsa, gsb, g):
            problems.append(f"outline {g}")
    if a.getBestCmap() != b.getBestCmap():
        problems.append("character map differs")

    # Windows names only: fontmake leaves out the old Mac names, as Google Fonts prefers
    na = {(r.nameID, r.langID): r.toUnicode() for r in a["name"].names if r.platformID == 3}
    nb = {(r.nameID, r.langID): r.toUnicode() for r in b["name"].names if r.platformID == 3}
    for k in sorted(set(na) | set(nb)):
        if na.get(k) != nb.get(k):
            problems.append(f"name {k}: {na.get(k)!r} vs {nb.get(k)!r}")

    for table, fields in (
        ("hhea", ("ascent", "descent", "lineGap")),
        ("head", ("unitsPerEm", "macStyle", "fontRevision")),
        ("OS/2", ("usWeightClass", "usWidthClass", "fsSelection", "fsType", "achVendID", "sTypoAscender",
                  "sTypoDescender", "sTypoLineGap", "usWinAscent", "usWinDescent", "sxHeight", "sCapHeight",
                  "ulCodePageRange1", "ulCodePageRange2", "ulUnicodeRange1", "ulUnicodeRange2")),
        ("post", ("italicAngle", "underlinePosition", "underlineThickness")),
    ):
        for k in fields:
            va, vb = getattr(a[table], k), getattr(b[table], k)
            if va != vb:
                problems.append(f"{table}.{k}: {va} vs {vb}")

    # shaping
    fa, fb = shaper(a_path), shaper(b_path)
    cmap = a.getBestCmap()
    chars = [chr(c) for c in sorted(cmap) if c > 0x20]
    arabic = [c for c in chars if 0x600 <= ord(c) <= 0x6FF and not 0x64B <= ord(c) <= 0x65F and ord(c) != 0x670]
    marks = [c for c in chars if 0x64B <= ord(c) <= 0x65F or ord(c) == 0x670]
    latin = [c for c in chars if c.isalpha() and ord(c) < 0x250]
    combining = [c for c in chars if 0x300 <= ord(c) <= 0x36F]
    tests = [(c, None) for c in chars]
    tests += [(x + y, None) for x, y in itertools.product(arabic, repeat=2)]
    tests += [(x + m + y, None) for x in arabic[::3] for m in marks for y in arabic[::7]]
    words = ["کوهمرد", "الله", "لا", "بسم الله", "پهلوان ۱۲۳۴", "ثلث", "شلغم", "ژله", "ؤلف", "مُحَمَّد", "ٹیلی ڈاک گاڑی ہے",
             "کتاب‌خانه", "نستعلیق", "زیبا ۵۶۷۸۹۰", "«سلام»؛ چطوری؟", "فارسی Latin ۱۲۳ 123", "ـــــ", "یییی", "ببببب"]
    tests += [(w, None) for w in words]
    tests += [(x + y, None) for x, y in itertools.product(latin, repeat=2)]
    tests += [(x + c, None) for x in latin[::2] for c in combining]
    tests += [("íj́ ÍJ́ ij̈ Kuhmard Bold — azrast.com 0123456789 (a,b) \"x\"", None)]
    tests += [(w, {"ss01": True}) for w in ("123 ٪ ، ؛ ؟", "فارسی 123")]
    tests += [("123 ., ; ? %", None)]
    na_, nb_ = a.getGlyphOrder(), b.getGlyphOrder()
    bad = 0
    for text, feats in tests:
        ra, rb = shape(fa, na_, text, feats), shape(fb, nb_, text, feats)
        if ra != rb:
            bad += 1
            if bad <= 15:
                problems.append(f"shaping {text!r}: {ra} vs {rb}")
    if bad > 15:
        problems.append(f"... {bad} shaping differences in all")

    print(f"{len(oa)} glyphs, {len(tests)} shaping tests")
    if problems:
        print(f"{len(problems)} DIFFERENCES")
        for p in problems:
            print("  ", p)
        sys.exit(1)
    print("IDENTICAL: outlines, widths, character map, names, metrics and shaping all match")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
