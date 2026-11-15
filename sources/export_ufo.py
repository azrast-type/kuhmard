"""Write the UFO source of Kuhmard from a build (Google Fonts builds fonts from UFO sources).

    python3 export_ufo.py otf/Kuhmard-Bold.otf features/Kuhmard-Bold.fea ../sources-ufo/Kuhmard-Bold.ufo

build_ai.py draws every letter, places the dots and writes the feature code; this script
carries all of it into a UFO, which fontmake / gftools builder turn back into the same font:
the outlines, advance widths, character map, glyph order, every OpenType feature (GDEF, GSUB,
GPOS, from the .fea the build wrote), and the font info (names, including the Persian menu
name, vertical metrics, OS/2 and post values). compare_ufo_build.py checks the round trip.

Needs: fontTools, ufoLib2.
"""
import sys

import ufoLib2
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.ttLib import TTFont


def bits(value, size):
    return [i for i in range(size) if value >> i & 1]


def export(otf_path, fea_path, ufo_path):
    f = TTFont(otf_path)
    order = f.getGlyphOrder()
    gs = f.getGlyphSet()
    hmtx = f["hmtx"].metrics
    cmap = f.getBestCmap()
    unis = {}
    for cp, g in sorted(cmap.items()):
        unis.setdefault(g, []).append(cp)

    ufo = ufoLib2.Font()
    for g in order:
        glyph = ufo.newGlyph(g)
        glyph.width = hmtx[g][0]
        glyph.unicodes = unis.get(g, [])
        gs[g].draw(SegmentToPointPen(glyph.getPointPen()))
    ufo.lib["public.glyphOrder"] = order

    name = f["name"]
    n = lambda i: name.getDebugName(i)
    os2, hhea, head, post = f["OS/2"], f["hhea"], f["head"], f["post"]
    major, minor = divmod(round(head.fontRevision * 1000), 1000)
    info = ufo.info
    info.familyName = n(1)
    info.styleName = n(2)
    info.styleMapFamilyName = n(1)
    info.styleMapStyleName = n(2).lower()            # "bold": sets the bold bits in OS/2 and head
    info.versionMajor, info.versionMinor = major, minor
    info.copyright = n(0)
    info.unitsPerEm = head.unitsPerEm
    info.ascender = os2.sTypoAscender
    info.descender = os2.sTypoDescender
    info.xHeight = os2.sxHeight
    info.capHeight = os2.sCapHeight
    info.italicAngle = post.italicAngle
    info.openTypeHeadFlags = bits(head.flags, 16)
    info.openTypeHeadLowestRecPPEM = head.lowestRecPPEM
    info.openTypeHheaAscender = hhea.ascent
    info.openTypeHheaDescender = hhea.descent
    info.openTypeHheaLineGap = hhea.lineGap
    info.openTypeNameDesigner = n(9)
    info.openTypeNameDesignerURL = n(12)
    info.openTypeNameManufacturer = n(8)
    info.openTypeNameManufacturerURL = n(11)
    info.openTypeNameLicense = n(13)
    info.openTypeNameLicenseURL = n(14)
    info.openTypeNameUniqueID = n(3)
    info.openTypeNameVersion = n(5)
    # names in other languages (the Persian menu name, Windows language 0x0429)
    info.openTypeNameRecords = [
        {"nameID": r.nameID, "platformID": r.platformID, "encodingID": r.platEncID,
         "languageID": r.langID, "string": r.toUnicode()}
        for r in name.names if r.platformID == 3 and r.langID != 0x409]
    info.openTypeOS2VendorID = os2.achVendID
    info.openTypeOS2Type = bits(os2.fsType, 16)      # [] = installable (fsType 0)
    info.openTypeOS2WeightClass = os2.usWeightClass
    info.openTypeOS2WidthClass = os2.usWidthClass
    info.openTypeOS2Selection = [b for b in bits(os2.fsSelection, 16) if b not in (0, 5, 6)]
    info.openTypeOS2Panose = [getattr(os2.panose, k) for k in (
        "bFamilyType", "bSerifStyle", "bWeight", "bProportion", "bContrast", "bStrokeVariation",
        "bArmStyle", "bLetterForm", "bMidline", "bXHeight")]
    info.openTypeOS2FamilyClass = [os2.sFamilyClass >> 8, os2.sFamilyClass & 0xFF]
    info.openTypeOS2UnicodeRanges = sorted(os2.getUnicodeRanges())
    info.openTypeOS2CodePageRanges = bits(os2.ulCodePageRange1, 32) + [32 + b for b in bits(os2.ulCodePageRange2, 32)]
    info.openTypeOS2TypoAscender = os2.sTypoAscender
    info.openTypeOS2TypoDescender = os2.sTypoDescender
    info.openTypeOS2TypoLineGap = os2.sTypoLineGap
    info.openTypeOS2WinAscent = os2.usWinAscent
    info.openTypeOS2WinDescent = os2.usWinDescent
    info.openTypeOS2SubscriptXSize = os2.ySubscriptXSize
    info.openTypeOS2SubscriptYSize = os2.ySubscriptYSize
    info.openTypeOS2SubscriptXOffset = os2.ySubscriptXOffset
    info.openTypeOS2SubscriptYOffset = os2.ySubscriptYOffset
    info.openTypeOS2SuperscriptXSize = os2.ySuperscriptXSize
    info.openTypeOS2SuperscriptYSize = os2.ySuperscriptYSize
    info.openTypeOS2SuperscriptXOffset = os2.ySuperscriptXOffset
    info.openTypeOS2SuperscriptYOffset = os2.ySuperscriptYOffset
    info.openTypeOS2StrikeoutSize = os2.yStrikeoutSize
    info.openTypeOS2StrikeoutPosition = os2.yStrikeoutPosition
    info.postscriptFontName = n(6)
    info.postscriptFullName = n(4)
    info.postscriptWeightName = f["CFF "].cff.topDictIndex[0].Weight
    info.postscriptUnderlinePosition = post.underlinePosition
    info.postscriptUnderlineThickness = post.underlineThickness
    info.postscriptIsFixedPitch = bool(post.isFixedPitch)

    ufo.features.text = open(fea_path, encoding="utf-8").read()
    ufo.save(ufo_path, overwrite=True)
    print("saved", ufo_path, len(order), "glyphs")


if __name__ == "__main__":
    export(*sys.argv[1:4])
