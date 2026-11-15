"""Constructed glyphs for Jashnvare v0.4: digits, punctuation, diacritics, the hamza mark.

Drawn in the master's vocabulary (square corners, rounded bends where the letters
have them, a serif = a short top spur pointing right) with stroke values passed in,
so every weight builds its own copy at its own stem and bar instead of being eroded.

All coordinates are font units, baseline y=0. Digits sit on the baseline, DIGIT_H tall.
"""
import pathops

K = 0.5523  # cubic quarter-circle factor


def rect(x0, y0, x1, y1):
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()
    return p


def poly(pts):
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo(pts[0])
    for q in pts[1:]:
        pen.lineTo(q)
    pen.closePath()
    return p


def rrect(x0, y0, x1, y1, tl=0, tr=0, br=0, bl=0):
    """Rectangle with its own radius per corner (counter-clockwise from bottom-left)."""
    w, h = x1 - x0, y1 - y0
    c = lambda r: max(0.0, min(r, w / 2, h / 2))
    tl, tr, br, bl = c(tl), c(tr), c(br), c(bl)
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo((x0 + bl, y0))
    pen.lineTo((x1 - br, y0))
    if br: pen.curveTo((x1 - br + br * K, y0), (x1, y0 + br - br * K), (x1, y0 + br))
    pen.lineTo((x1, y1 - tr))
    if tr: pen.curveTo((x1, y1 - tr + tr * K), (x1 - tr + tr * K, y1), (x1 - tr, y1))
    pen.lineTo((x0 + tl, y1))
    if tl: pen.curveTo((x0 + tl - tl * K, y1), (x0, y1 - tl + tl * K), (x0, y1 - tl))
    pen.lineTo((x0, y0 + bl))
    if bl: pen.curveTo((x0, y0 + bl - bl * K), (x0 + bl - bl * K, y0), (x0 + bl, y0))
    pen.closePath()
    return p


def union(*ps):
    ps = [p for p in ps if p is not None]
    out = pathops.Path(); pathops.union(ps, out.getPen()); return out


def diff(a, *bs):
    out = a
    for b in bs:
        out = pathops.op(out, b, pathops.PathOp.DIFFERENCE)
    return out


def shift(p, dx, dy=0):
    from fontTools.pens.transformPen import TransformPen
    out = pathops.Path(); p.draw(TransformPen(out.getPen(), (1, 0, 0, 1, dx, dy))); return out


def scale(p, k, cx=0, cy=0):
    from fontTools.pens.transformPen import TransformPen
    out = pathops.Path(); p.draw(TransformPen(out.getPen(), (k, 0, 0, k, cx - k * cx, cy - k * cy))); return out


DIGIT_H = 470


class Kit:
    """Glyph constructors for one weight."""

    def __init__(self, stem, bar, dot, ser=67):
        self.S, self.B, self.D = stem, bar, dot
        self.ser = ser * stem / 135          # serif reach scales with the stem
        self.H = DIGIT_H

    # ---------------------------------------------------------- marks
    def hamza(self, k=1.0):
        """Small 'c' opening right with a foot kicking left; bottom-left at (0, 0)."""
        t = max(26, 0.41 * self.S) * k
        W, H = 150 * k, 175 * k
        f = 0.62 * t
        body = rect(0, f, W, H)
        mouth = rect(t, f + 0.8 * t, W + 1, H - 0.8 * t)
        foot = rect(-45 * k, 0, t, f + 1)
        return union(diff(body, mouth), foot)

    def marks(self):
        """{name: (path, 'top'|'bot')}; top marks sit on y=0, bottom marks hang from y=0."""
        t = max(30, 0.42 * self.S)              # mark stroke
        out = {}
        fat = poly([(-80, 0), (25, 0), (80, 62), (-25, 62)])
        fat = scale(fat, t / 42)
        out['fatha'] = (fat, 'top')
        out['kasra'] = (shift(fat, 0, -fat.bounds[3]), 'bot')
        out['fathatan'] = (union(fat, shift(fat, 0, fat.bounds[3] + 0.9 * t)), 'top')
        k2 = union(fat, shift(fat, 0, fat.bounds[3] + 0.9 * t))
        out['kasratan'] = (shift(k2, 0, -k2.bounds[3]), 'bot')
        # damma: a small square و — ring on a stem with a foot
        r = 1.0 * t
        ring = diff(rect(-48 - r / 2, 64, 48 + r / 2, 64 + 96 + r / 2), rect(-48 + r / 2, 64 + r, 48 - r / 2, 64 + 96 + r / 2 - r))
        tail = rect(48 + r / 2 - r, 0, 48 + r / 2, 66)
        foot = rect(-60, 0, 48 + r / 2, 0.75 * r)
        dam = union(ring, tail, foot)
        dam = shift(dam, -(dam.bounds[0] + dam.bounds[2]) / 2)
        out['damma'] = (dam, 'top')
        d2 = union(scale(dam, 0.8), shift(scale(dam, 0.8), 0.8 * (dam.bounds[2] - dam.bounds[0]) + 0.6 * t))
        out['dammatan'] = (shift(d2, -(d2.bounds[0] + d2.bounds[2]) / 2), 'top')
        # sukun: small square ring
        s = 105 + 0.4 * t
        out['sukun'] = (diff(rect(-s / 2, 0, s / 2, s), rect(-s / 2 + t, t, s / 2 - t, s - t)), 'top')
        # shadda: three short teeth on a bar
        w = 200 + 0.6 * t
        sh = union(rect(-w / 2, 0, w / 2, 0.85 * t), rect(-w / 2, 0, -w / 2 + t, 105),
                   rect(-t / 2, 0, t / 2, 105), rect(w / 2 - t, 0, w / 2, 105))
        out['shadda'] = (sh, 'top')
        out['superalef'] = (rect(-0.55 * t, 0, 0.55 * t, 175), 'top')
        hz = scale(self.hamza(0.8), 1)
        out['hamzaabove'] = (shift(hz, -(hz.bounds[0] + hz.bounds[2]) / 2), 'top')
        out['hamzabelow'] = (shift(hz, -(hz.bounds[0] + hz.bounds[2]) / 2, -hz.bounds[3]), 'bot')
        md = union(rect(-95, 0, 95, 0.95 * t), rect(-95, 0, -95 + 0.95 * t, 0.95 * t + 26), rect(95 - 0.95 * t, -26, 95, 0.95 * t))
        out['maddah'] = (shift(md, 0, -md.bounds[1]), 'top')
        return out

    # ---------------------------------------------------------- digits
    def serif_r(self, x_right, top):
        return rect(x_right - 1, top - self.B, x_right + self.ser, top)

    def digit(self, n):
        S, B, H, D = self.S, self.B, self.H, self.D
        J = round(0.50 * H)                    # cup floor for ۲ ۳ ۶
        if n == 0:
            s = D * 1.05
            return rect(0, H * 0.42 - s / 2, s, H * 0.42 + s / 2)
        if n == 1:
            return rect(0, 0, S, H)
        if n == 2:
            W = 2 * S + 125
            return union(rect(0, 0, S, H), rect(0, J, W, J + B), rect(W - S, J, W, H), self.serif_r(W, H))
        if n == 3:
            g = 100; mid = 0.85 * S
            W = 2 * S + mid + 2 * g
            return union(rect(0, 0, S, H), rect(0, J, W, J + B), rect(S + g, J, S + g + mid, H),
                         rect(W - S, J, W, H), self.serif_r(W, H))
        if n == 4:
            # stem with an epsilon on its right: top arm turns down, lower arm (longer) turns up
            W1, W2 = S + 165, S + 245
            M = round(0.20 * H)
            t = 0.8 * S
            return union(rect(0, 0, S, H),
                         rect(0, H - B, W1, H), rect(W1 - t, H - B - 60, W1, H),
                         rect(0, M, W2, M + B), rect(W2 - t, M, W2, M + B + 70))
        if n == 5:
            # inverted heart: round bottom, pointed top
            W = 2 * S + 130
            shoulder = round(0.58 * H)
            outer = union(rrect(0, 0, W, shoulder + 2, bl=W / 2, br=W / 2),
                          poly([(0, shoulder), (W, shoulder), (W / 2, H)]))
            ci = W - 2 * S
            inner = union(rrect(S, 1.15 * B, W - S, shoulder + 1, bl=ci / 2, br=ci / 2),
                          poly([(S, shoulder), (W - S, shoulder), (W / 2, H - 1.55 * S)]))
            return diff(outer, inner)
        if n == 6:
            W = 2 * S + 125
            return union(rect(W - S, 0, W, H), rect(0, J, W, J + B), rect(0, J, S, H))
        if n == 7:
            W = 2 * S + 140
            return union(rect(0, 0, S, H), rect(W - S, 0, W, H), rrect(0, 0, W, B, bl=0.5 * S, br=0.5 * S),
                         rect(0, B / 2, W, B))
        if n == 8:
            W = 2 * S + 140
            return union(rect(0, 0, S, H), rect(W - S, 0, W, H), rect(0, H - B, W, H))
        if n == 9:
            W = 2 * S + 115
            top = round(0.42 * H)
            return union(rect(W - S, 0, W, H), diff(rect(0, top, W, H), rect(S, top + B, W - S, H - B)))
        raise KeyError(n)


    # ---------------------------------------------------------- symbols for pasted text
    def symbol(self, name):
        """Square-style symbols so pasted text never falls back to another font."""
        S, B, H = self.S, self.B, self.H
        t = 0.85 * S                                  # vertical stroke for symbols
        q = lambda x: rect(x, 390, x + 0.62 * S, 560)  # one straight quote
        if name == 'quotedbl':
            return union(q(0), q(0.62 * S + 55))
        if name == 'quotesingle':
            return q(0)
        if name in ('quotedblleft', 'quotedblright'):
            return union(q(0), q(0.62 * S + 55))
        if name in ('quoteleft', 'quoteright'):
            return q(0)
        if name == 'slash':
            return poly([(0, -120), (t, -120), (300 + t, 620), (300, 620)])
        if name == 'backslash':
            return poly([(300, -120), (300 + t, -120), (t, 620), (0, 620)])
        if name == 'plus':
            w = 360
            return union(rect(0, 180 - B / 2, w, 180 + B / 2), rect(w / 2 - t / 2, 0, w / 2 + t / 2, 360))
        if name == 'minus':
            return rect(0, 180 - B / 2, 360, 180 + B / 2)
        if name == 'equal':
            if (265 - B / 2) - (95 + B) >= 30:
                return union(rect(0, 95, 360, 95 + B), rect(0, 265 - B / 2, 360, 265 + B / 2))
            g = 50                                       # heavy weights: keep the two bars apart
            return union(rect(0, 180 - g / 2 - B, 360, 180 - g / 2), rect(0, 180 + g / 2, 360, 180 + g / 2 + B))
        if name == 'multiply':
            k = 0.62 * S
            return union(poly([(0, 30), (k, 30), (330, 330), (330 - k, 330)]), poly([(330, 30), (330 - k, 30), (0, 330), (k, 330)]))
        if name == 'asterisk':
            k = 0.55 * S
            return union(rect(150 - k / 2, 300, 150 + k / 2, 600), poly([(0, 380), (k, 360), (300, 520), (300 - k, 540)]),
                         poly([(300, 380), (300 - k, 360), (0, 520), (k, 540)]))
        if name == 'less':
            return poly([(0, 180), (330, 380), (330, 380 - 1.1 * B), (1.6 * B, 180), (330, -20 + 1.1 * B), (330, -20)])
        if name == 'greater':
            return poly([(330, 180), (0, 380), (0, 380 - 1.1 * B), (330 - 1.6 * B, 180), (0, -20 + 1.1 * B), (0, -20)])
        if name in ('bracketleft', 'bracketright', 'braceleft', 'braceright'):
            w = S + 95
            base = union(rect(0, -190, S, 640), rect(0, 640 - B, w, 640), rect(0, -190, w, -190 + B))
            if name.startswith('brace'):
                base = union(base, rect(-90, 225 - B / 2, 1, 225 + B / 2))
            if name.endswith('right'):
                from fontTools.pens.transformPen import TransformPen
                b = base.bounds
                out = pathops.Path(); base.draw(TransformPen(out.getPen(), (-1, 0, 0, 1, b[0] + b[2], 0)))
                base = union(out)
            return base
        if name == 'bar':
            return rect(0, -190, t, 640)
        if name == 'underscore':
            return rect(0, -190, 420, -190 + B)
        if name == 'numbersign':
            k = 0.6 * S
            return union(rect(80, 0, 80 + k, 520), rect(260, 0, 260 + k, 520), rect(0, 150, 420, 150 + B), rect(0, 340, 420, 340 + B))
        if name == 'divide':
            d = 0.8 * self.D
            return union(rect(0, 180 - B / 2, 360, 180 + B / 2), rect(180 - d / 2, 290, 180 + d / 2, 290 + d), rect(180 - d / 2, 70 - d, 180 + d / 2, 70))
        if name == 'dollar':
            k = 0.8 * S; h = 470
            w = 330 if 165 - 0.3 * S - k >= 15 else 2 * (k + 0.3 * S + 30)   # heavy weights: open the counters
            S_ = union(rect(0, h - B, w, h), rect(0, h / 2, k, h), rect(0, h / 2 - B / 2, w, h / 2 + B / 2),
                       rect(w - k, 0, w, h / 2), rect(0, 0, w, B))
            return union(S_, rect(w / 2 - 0.3 * S, -90, w / 2 + 0.3 * S, h + 90))
        if name == 'ampersand':
            k = 0.8 * S
            top = diff(rect(40, 260, 300, 520), rect(40 + k, 260 + B, 300 - k, 520 - B))
            low = diff(rect(0, 0, 330, 300), rect(k, B, 330 - k, 300 - B))
            leg = poly([(250, 0), (250 + k, 0), (430, 200), (430 - k, 200)])
            return union(top, low, leg)
        if name == 'at':
            k = 0.7 * S; w = 560
            ring = diff(rect(0, -80, w, 480), rect(k, -80 + B, w - k, 480 - B))
            ring = diff(ring, rect(w - k - 1, -80, w + 1, 120))
            inner = diff(rect(150, 90, 400, 330), rect(150 + k, 90 + B, 400 - k, 330 - B))
            return union(ring, inner, rect(400 - k, 90, w, 90 + B))
        if name == 'asciicircum':
            k = 0.62 * S
            return union(poly([(0, 330), (k, 330), (170, 520), (170 - k / 2, 560)]), poly([(340, 330), (340 - k, 330), (170, 520), (170 + k / 2, 560)]))
        if name == 'grave':
            return poly([(0, 560), (0.7 * S, 560), (0.7 * S + 90, 430), (90, 430)])
        if name == 'asciitilde':
            return union(rect(0, 150, 0.8 * S, 150 + 1.6 * B), rect(0, 150 + 0.6 * B, 200, 150 + 1.6 * B),
                         rect(200 - 0.8 * S, 150, 200, 150 + 1.6 * B), rect(200 - 0.8 * S, 150, 400, 150 + B))
        if name == 'degree':
            d = 230
            return diff(rect(0, 560 - d, d, 560), rect(0.55 * S, 560 - d + 0.55 * S, d - 0.55 * S, 560 - 0.55 * S))
        if name == 'perthousand':
            dd = 0.8 * self.D
            return union(rect(0, H - dd, dd, H), rect(250 - dd + 60, 0, 250 + 60, dd), rect(250 + 110, 0, 250 + 110 + dd, dd),
                         poly([(30, 0), (30 + 0.6 * S, 0), (280, H), (280 - 0.6 * S, H)]))
        if name in ('guilsinglleft', 'guilsinglright'):
            t2 = 0.75 * S
            p = poly([(0, 190), (130, 360), (130 + t2, 360), (t2, 190), (130 + t2, 20), (130, 20)])
            if name == 'guilsinglright':
                from fontTools.pens.transformPen import TransformPen
                b = p.bounds
                out = pathops.Path(); p.draw(TransformPen(out.getPen(), (-1, 0, 0, 1, b[0] + b[2], 0)))
                p = union(out)
            return p
        if name == 'copyright':
            k = 0.55 * S
            ring = diff(rect(0, -20, 560, 540), rect(k, -20 + k, 560 - k, 540 - k))
            c = diff(rect(160, 130, 400, 390), rect(160 + k, 130 + 0.8 * B, 400 + 1, 390 - 0.8 * B))
            return union(ring, c)
        raise KeyError(name)


    # ---------------------------------------------------------- punctuation
    def _comma(self):
        """Persian comma: a turned comma. Square head on the baseline, a broad tail
        rising to the upper right."""
        D = self.D
        head = rect(0, 0, D, D)
        tail = poly([(0.18 * D, D - 2), (D, D - 2), (D + 0.62 * D, D + 1.25 * D), (0.18 * D + 0.62 * D, D + 1.25 * D)])
        return union(head, tail)

    def punct(self, name):
        S, B, D, H = self.S, self.B, self.D, self.H
        dot = lambda x, y: rect(x, y, x + D, y + D)
        if name == 'period':
            return dot(0, 0)
        if name == 'colon':
            return union(dot(0, 0), dot(0, 250))
        if name == 'exclam':
            return union(dot(0, 0), rect((D - S) / 2, 170, (D + S) / 2, H + 80))
        if name == 'arabiccomma':
            # Persian comma: a turned comma, square dot low with a tail rising to the right
            return self._comma()
        if name == 'arabicsemicolon':
            return union(dot(0, 0), shift(self._comma(), 0, D + 95))
        if name == 'arabicquestion':
            # mirrored question mark: hook opens to the left
            W = 2 * S + 150
            cx = W / 2
            mid = round(0.52 * H)
            return union(rect(0, H - B, W, H), rect(W - 0.8 * S, H - B - 70, W, H),   # top arm + tick
                         rect(0, mid, S, H), rect(0, mid, cx + S / 2, mid + B),       # left side + floor
                         rect(cx - S / 2, 160, cx + S / 2, mid + B),                  # stem
                         dot(cx - D / 2, 0))
        if name == 'hyphen':
            return rect(0, 150, 230, 150 + B)
        if name == 'endash':
            return rect(0, 150, 420, 150 + B)
        if name == 'emdash':
            return rect(0, 150, 840, 150 + B)
        if name == 'parenleft':
            w = S + 95
            return union(rect(0, -190, S, 600), rect(0, 600 - B, w, 600), rect(0, -190, w, -190 + B))
        if name == 'parenright':
            w = S + 95
            return union(rect(w - S, -190, w, 600), rect(0, 600 - B, w, 600), rect(0, -190, w, -190 + B))
        if name in ('guillemotleft', 'guillemotright'):
            t = 0.75 * S
            ch = lambda x0: poly([(x0, 190), (x0 + 130, 360), (x0 + 130 + t, 360), (x0 + t, 190),
                                  (x0 + 130 + t, 20), (x0 + 130, 20)])
            p = union(ch(0), ch(150 + 0.6 * t))
            if name == 'guillemotright':
                from fontTools.pens.transformPen import TransformPen
                b = p.bounds
                out = pathops.Path(); p.draw(TransformPen(out.getPen(), (-1, 0, 0, 1, b[0] + b[2], 0)))
                p = union(out)
            return p
        if name == 'decimalsep':          # ٫
            return poly([(0, -40), (0.55 * S, -40), (0.55 * S + 70, 150), (70, 150)])
        if name == 'percent':             # ٪
            dd = 0.8 * D
            return union(rect(0, H - dd, dd, H), rect(250 - dd + 60, 0, 250 + 60, dd),
                         poly([(30, 0), (30 + 0.6 * S, 0), (280, H), (280 - 0.6 * S, H)]))
        raise KeyError(name)


PUNCT = {
    'period': [0x002E, 0x06D4], 'colon': [0x003A], 'exclam': [0x0021],
    'arabiccomma': [0x060C], 'arabicsemicolon': [0x061B], 'arabicquestion': [0x061F],
    'hyphen': [0x002D, 0x2010, 0x2011], 'endash': [0x2013, 0x2012], 'emdash': [0x2014, 0x2015],
    'parenleft': [0x0028, 0xFD3E], 'parenright': [0x0029, 0xFD3F],
    'guillemotleft': [0x00AB], 'guillemotright': [0x00BB],
    'decimalsep': [0x066B], 'percent': [0x066A],
}

MARKS = {
    'fatha': 0x064E, 'damma': 0x064F, 'kasra': 0x0650, 'sukun': 0x0652, 'shadda': 0x0651,
    'fathatan': 0x064B, 'dammatan': 0x064C, 'kasratan': 0x064D, 'superalef': 0x0670,
    'hamzaabove': 0x0654, 'hamzabelow': 0x0655, 'maddah': 0x0653,
}

SYMBOLS = {
    'quotedbl': [0x0022], 'quotesingle': [0x0027], 'quotedblleft': [0x201C, 0x201E], 'quotedblright': [0x201D],
    'quoteleft': [0x2018], 'quoteright': [0x2019, 0x201A], 'slash': [0x002F, 0x060D], 'backslash': [0x005C],
    'plus': [0x002B], 'minus': [0x2212], 'equal': [0x003D], 'multiply': [0x00D7], 'asterisk': [0x002A, 0x066D],
    'less': [0x003C], 'greater': [0x003E], 'bracketleft': [0x005B], 'bracketright': [0x005D],
    'braceleft': [0x007B], 'braceright': [0x007D], 'bar': [0x007C], 'underscore': [0x005F],
    'numbersign': [0x0023], 'divide': [0x00F7],
    'dollar': [0x0024], 'ampersand': [0x0026], 'at': [0x0040], 'asciicircum': [0x005E], 'grave': [0x0060],
    'asciitilde': [0x007E], 'degree': [0x00B0], 'perthousand': [0x2030, 0x0609], 'guilsinglleft': [0x2039],
    'guilsinglright': [0x203A], 'copyright': [0x00A9],
}
