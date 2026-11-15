"""Letter designs for the Jashnvare family, drawn on the grid measured from the
1974 Tehran International Film Festival lettering (سومین جشنواره جهانی فیلم تهران).

Design units (scaled 1.4x into a 1000-unit em at build time). Baseline y=0 is
the bottom of the joining bar. Vertical metrics are fixed across weights;
stroke thickness comes from configure(), and shapes are built from strokes
plus constant counters, so lighter weights come out narrower.

Each design returns a body: width, ink shapes, white shapes (counters cut
after rounding) and dots (added last so they never fuse with letters).
"""

X = 260           # x-height (tooth tops, bowl tops)
A = 460           # ascender (alef, lam, dot tops)
D = -210          # descender
GAP = 110         # white between teeth
LC = 90           # loop counter width

SV = SH = SD = DOT_W = DOT_H = HT = None


def configure(sv, sh):
    """Set the stroke system for one weight."""
    global SV, SH, SD, DOT_W, DOT_H, HT
    SV, SH, SD = sv, sh, sv
    DOT_W = round(0.95 * sv + 8)
    DOT_H = min(round(DOT_W * 1.62), A - X - 35)
    HT = max(30, round(0.5 * sv))   # hamza stroke


def up():
    return (A - DOT_H, A)


def dn():
    return (D, D + DOT_H)


class B:
    def __init__(self, w):
        self.w = w
        self.ink = []    # ('r', x0, y0, x1, y1, radius) | ('p', [pts])
        self.white = []
        self.dots = []   # (x0, y0, x1, y1)
        self.jl_to = None    # where a left-join bar stops (body x); default near the right end
        self.jr_from = None  # where a right-join bar starts (body x); default last stem

    def r(self, x0, y0, x1, y1, rad=None):
        self.ink.append(('r', x0, y0, x1, y1, rad)); return self

    def cut(self, x0, y0, x1, y1, rad=None):
        self.white.append(('r', x0, y0, x1, y1, rad)); return self

    def poly(self, pts):
        self.ink.append(('p', pts)); return self

    def cutpoly(self, pts):
        self.white.append(('p', pts)); return self

    def dot(self, cx, ys, n=1, w=None, h=None):
        w = w or DOT_W
        y0 = ys[0]
        y1 = y0 + h if h is not None else ys[1]
        g = max(12, round(0.16 * SV))
        if n == 1:
            xs = [cx - w / 2]
        elif n == 2:
            xs = [cx - w - g / 2, cx + g / 2]
        else:
            xs = [cx - 1.5 * w - g, cx - w / 2, cx + w / 2 + g]
        for x in xs:
            self.dots.append((x, y0, x + w, y1))
        return self


# ---------------------------------------------------------------- primitives

def tooth():
    return B(SV).r(0, 0, SV, X)


def teeth3():
    p = SV + GAP
    w = 2 * p + SV
    b = B(w)
    for i in range(3):
        b.r(i * p, 0, i * p + SV, X)
    return b.r(0, 0, w, SH)


def u_width():
    return 2 * SV + 210


def deep_u(b, x0, right_top=X, left_top=X):
    """U that drops to the descender (ن / ل / س / ص finals)."""
    w = u_width()
    b.r(x0, D, x0 + SV, left_top)
    b.r(x0 + w - SV, D, x0 + w, right_top)
    b.r(x0, D, x0 + w, D + SD)
    return w


def loop_width(cw=LC):
    return cw + 2 * SV


def loop(b, x0, cw=LC, top=X):
    w = loop_width(cw)
    b.r(x0, 0, x0 + w, top)
    b.cut(x0 + SV, SH, x0 + SV + cw, top - SH)
    return w


def j_tail(b, x_conn, up_to=-40):
    """Descending J: connector down from x_conn, foot to the left, upturn."""
    b.r(x_conn, D, x_conn + SV, SH)
    b.r(0, D, x_conn + SV, D + SD)
    b.r(0, D, SV, up_to)
    return b


def hamza(b, x, y, k=1.0):
    """ء: a small 'c' opening right, with a foot kicking left."""
    t = HT * k
    W, H = 135 * k + 0.4 * t, 175 * k
    f = 0.8 * t                                   # foot height
    b.r(x, y + f, x + W, y + H, 0.45 * t)
    b.cut(x + t, y + f + 0.85 * t, x + W + 4, y + H - 0.85 * t, 0.3 * t)
    b.r(x - 45 * k, y, x + t, y + f + 2, 0.4 * t)
    return W, H


# ---------------------------------------------------------------- letters
# Each function takes form in {isol, init, medi, fina} and returns a body.

def alef(f):
    return B(SV).r(0, 0, SV, A)


def alef_madda(f):
    w = SV + 110
    b = B(w).r(55, 0, 55 + SV, A - 120)
    return b.r(0, A - SH, w, A)


def alef_hamza_above(f):
    b = B(SV + 70).r(35, 0, 35 + SV, X + 20)
    hamza(b, 20, X + 70, 0.85)
    return b


def alef_hamza_below(f):
    b = B(SV + 70).r(35, 0, 35 + SV, A)
    hamza(b, 20, D + 15, 0.85)
    return b


def hamza_isol(f):
    b = B(190)
    hamza(b, 45, 0, 1.05)
    return b


def beh_like(f, n, below):
    if f in ('init', 'medi'):
        b = tooth()
        cx = SV / 2
    elif f == 'fina':
        w = SV + 280
        b = B(w).r(0, 0, SV, X).r(0, 0, w, SH)
        cx = SV + 110
    else:
        w = 2 * SV + 220
        b = B(w).r(0, 0, SV, X).r(0, 0, w, SH).r(w - SV, 0, w, 150)
        cx = w / 2
    if n:
        b.dot(cx, dn() if below else up(), n)
    return b


def noon(f):
    if f in ('init', 'medi'):
        return tooth().dot(SV / 2, up())
    b = B(u_width())
    deep_u(b, 0)
    return b.dot(b.w / 2, (X - DOT_H, X))


def yeh(f, dots=False, hz=False):
    """ی: a bowl hanging below the baseline, raised on the left.
    Isolated form opens with a small hook at the top right."""
    if f in ('init', 'medi'):
        b = tooth()
        if hz:
            hamza(b, -20, X + 40, 0.8)
        else:
            b.dot(SV / 2, dn(), 2)
        return b
    bw = 2 * SV + 200                  # bowl
    if f == 'fina':
        w = bw + 90
        b = B(w)
        b.r(bw - SV, D, bw, SH)        # neck from the join
        b.r(bw - SV, 0, w, SH)         # join runs in on the baseline
    else:
        w = bw + 110
        b = B(w)
        b.r(bw - SV, D, bw, X)         # neck up to the hook
        b.r(bw - SV, X - SH, w, X)     # hook arm
        b.r(w - 0.85 * SV, X - 125, w, X)   # hook tip turns down
    b.r(0, D, bw, D + SD)              # bowl floor
    b.r(0, D, SV, 115)                 # raised left end
    b.jr_from = bw - SV
    if hz:
        hamza(b, SV + 35, 45, 0.85)
    return b


def jeem_like(f, dot):
    if f in ('init', 'medi'):
        w = round(0.85 * SV) + 205
        b = B(w).r(0, X - SH, w, X).r(w - 0.85 * SV, 0, w, X)
        b.r(0, 0, w, SH)
        if dot == 'below1':
            b.dot(w / 2 - 35, dn())
        elif dot == 'below3':
            b.dot(w / 2, dn(), 3)
        elif dot == 'above1':
            b.dot(w / 2, up())
        return b
    w = 2 * SV + 250
    tongue = round(0.6 * w)
    b = B(w)
    b.r(0, X - SH, w, X)               # top arm
    b.r(0, D, SV, X)                   # left wall to descender
    b.r(0, D, w, D + SD)               # foot
    b.r(w - 0.85 * SV, 0, w, X)        # right wall
    b.r(tongue, 0, w, SH)              # baseline tongue
    cx = (SV + tongue) / 2
    if dot == 'below1':
        b.dot(cx, (-70, -70 + DOT_H))
    elif dot == 'below3':
        sw = round(0.72 * DOT_W)
        sh = round(0.66 * DOT_H)
        b.dot(cx - sw / 2 - 6, (-80, -80 + sh), w=sw)
        b.dot(cx + sw / 2 + 6, (-80, -80 + sh), w=sw)
        b.dot(cx, (-80 + sh + 12, -80 + 2 * sh + 12), w=sw)
    elif dot == 'above1':
        b.dot(w / 2, up())
    b.jr_from = w - 0.85 * SV
    return b


def dal_like(f, dot):
    """د: right stem, short top arm reaching left, long base."""
    w = SV + 200
    b = B(w)
    b.r(w - SV, 0, w, X)
    b.r(w - SV - 75, X - SH, w, X)     # short top arm
    b.r(0, 0, w, round(1.15 * SH))     # long base
    if dot:
        b.dot(w - SV / 2 - 20, up())
    return b


def reh_like(f, n):
    """ر: a stem that drops below the baseline and kicks left."""
    w = SV + 190
    b = B(w)
    top = 175 if f == 'isol' else SH
    b.r(w - SV, D, w, top)
    b.r(0, D, w, D + SD)
    if n:
        y0 = top + 40
        if n == 1:
            b.dot(w - SV / 2, (y0, y0 + DOT_H))
        else:
            b.dot(w - SV / 2 - 60, (y0, y0 + DOT_H), 3)
    return b


def seen_like(f, n):
    if f in ('init', 'medi'):
        b = teeth3()
        cx = b.w / 2
    else:
        uw = u_width()
        p = SV + GAP
        w = uw + 2 * p
        b = B(w)
        deep_u(b, 0)
        for x in (uw + GAP, uw + GAP + p):
            b.r(x, 0, x + SV, X)
        b.r(uw - SV, 0, w, SH)
        cx = uw + GAP + SV / 2
    if n:
        b.dot(cx, up(), n)
    return b


def sad_like(f, dot):
    cw = 160
    if f in ('init', 'medi'):
        b = B(loop_width(cw))
        loop(b, 0, cw)
        cx = b.w / 2
    else:
        uw = u_width()
        b = B(uw - SV + loop_width(cw))
        deep_u(b, 0)
        loop(b, uw - SV, cw)
        cx = uw - SV + loop_width(cw) / 2
    if dot:
        b.dot(cx, up())
    return b


def tah_like(f, dot):
    cw = 170
    b = B(loop_width(cw))
    loop(b, 0, cw)
    b.r(0, 0, SV, A)
    if dot:
        b.dot(SV + 45 + DOT_W / 2, up())
    return b


def ain_head_open(b, x0, w):
    """ع opening: a 'c' open to the right, upper lip rising to a horn."""
    b.r(x0, 0, x0 + SV, X)                        # back
    b.r(x0, X - SH, x0 + w, X)                    # upper lip
    b.r(x0 + w - 0.75 * SV, X - SH, x0 + w, X + 100)   # horn
    return b


def ain_cup_width():
    return 2 * SV + 90


def ain_cup(b, x0):
    """Medial ع: a cup with slanted walls, open at the top."""
    w = ain_cup_width()
    b.poly([(x0, X), (x0 + w, X), (x0 + w - 45, 0), (x0 + 45, 0)])
    b.cutpoly([(x0 + SV, X + 10), (x0 + w - SV, X + 10), (x0 + w / 2, X - 120)])
    return w


def ain_like(f, dot):
    if f == 'init':
        w = SV + 190
        b = B(w)
        ain_head_open(b, 0, w)
        b.jl_to = SV + 90                         # short lower lip: mouth stays open
        cx = (w - 0.75 * SV) / 2
    elif f == 'medi':
        b = B(ain_cup_width())
        ain_cup(b, 0)
        cx = b.w / 2
    elif f == 'fina':
        cw = ain_cup_width()
        w = cw + 170 + SV
        b = B(w)
        ain_cup(b, w - cw)
        b.r(0, D, SV, SH)                         # tail wall
        b.r(0, 0, w - cw + 50, SH)                # baseline into the tail
        b.r(0, D, w - 30, D + SD)                 # tail floor, opening right
        b.jr_from = w - cw + 40
        cx = w - cw / 2
    else:
        w = SV + 210
        b = B(w)
        ain_head_open(b, 0, w)
        b.r(0, D, SV, X)
        b.r(0, 0, round(0.72 * w), SH)            # waist
        b.r(0, D, w, D + SD)                      # tail floor
        cx = (w - 0.75 * SV) / 2
    if dot:
        b.dot(cx, up())
    return b


def feh_like(f, n, qaf=False):
    lw = loop_width()
    if f in ('init', 'medi'):
        b = B(lw)
        loop(b, 0)
        cx = lw / 2
    else:
        w = lw + 260
        b = B(w)
        loop(b, w - lw)
        if qaf:
            j_tail(b, w - lw, -40)
        else:
            b.r(0, 0, w, SH).r(0, 0, SV, 150)
        cx = w - lw / 2
    if n:
        b.dot(cx, up(), n)
    return b


def kaf_like(f, gaf=False):
    g = max(65, round(0.7 * SV))
    if f in ('init', 'medi'):
        w = SV + 150
        b = B(w).r(w - SV, 0, w, A).r(0, A - SH, w, A)
        if gaf:
            b.r(0, A - 2 * SH - g, w, A - SH - g)
        return b
    w = SV + 400
    b = B(w)
    b.r(w - SV, 0, w, A).r(w - SV - 150, A - SH, w, A)
    if gaf:
        b.r(w - SV - 150, A - 2 * SH - g, w, A - SH - g)
    b.r(0, 0, w, SH).r(0, 0, SV, 150)
    return b


def lam(f):
    if f in ('init', 'medi'):
        return B(SV).r(0, 0, SV, A)
    b = B(u_width())
    deep_u(b, 0, right_top=A)
    return b


def meem(f):
    cw = 100
    lw = loop_width(cw)
    if f in ('init', 'medi'):
        b = B(lw)
        loop(b, 0, cw)
        return b
    w = lw + 240
    b = B(w)
    loop(b, w - lw, cw)
    b.r(0, X - SH, w, X)
    b.r(0, D, SV, X)
    return b


def heh(f, dots=0):
    if f in ('init', 'medi'):
        w = 2 * SV + LC
        b = B(w).r(0, D, w, X)
        b.cut(SV, SH, SV + LC, X - SH)
        b.cut(SV, D + SH, SV + LC, 0)
    elif f == 'fina':
        b = B(loop_width(100))
        loop(b, 0, 100)
    else:
        w = 2 * SV + LC
        b = B(w).r(0, D, w, X)
        b.cut(SV, D + SH, SV + LC, X - SH - 5)
    if dots:
        b.dot(b.w / 2, up(), dots)
    return b


def waw(f, hz=False):
    """و: loop on the baseline, stem dropping from its right side, foot left."""
    lw = loop_width()
    w = lw + 60
    b = B(w)
    loop(b, 60)
    b.r(w - SV, D, w, SH)
    b.r(0, D, w, D + round(0.85 * SD))
    if hz:
        hamza(b, 60 + SV * 0.4, X + 45, 0.8)
    return b


def tatweel(f):
    return B(200).r(0, 0, 200, SH, 0)


# ---------------------------------------------------------------- digits

def digit(n):
    p = SV + GAP
    if n == 0:
        b = B(DOT_W); b.dot(DOT_W / 2, (40, 40 + DOT_H))
    elif n == 1:
        b = B(SV).r(0, D, SV, X)
    elif n == 2:
        w = p + SV
        b = B(w).r(0, D, SV, X).r(0, 0, w, SH).r(p, 0, w, X)
    elif n == 3:
        w = 2 * p + SV
        b = B(w).r(0, D, SV, X).r(0, 0, w, SH).r(p, 0, p + SV, X).r(2 * p, 0, w, X)
    elif n == 4:
        # ۴: stem with two arms reaching right, each turning back on itself
        w = SV + 200
        b = B(w).r(0, D, SV, X)
        b.r(0, X - SH, w, X).r(w - 0.85 * SV, X - 100, w, X)
        b.r(0, 0, w - 25, SH).r(w - 25 - 0.85 * SV, 0, w - 25, 85)
    elif n == 5:
        # ۵: rounded heart, dimpled at the top
        w = 2 * SV + 120
        b = B(w)
        b.r(0, -40, w, X, 0.5 * w)
        b.r(0, 60, w, X, 0.3 * SV)
        b.cut(SV, -40 + round(1.2 * SH), w - SV, X - SH, 0.48 * (w - 2 * SV))
        b.cutpoly([(w / 2 - 38, X + 5), (w / 2 + 38, X + 5), (w / 2, X - SH - 8)])
    elif n == 6:
        w = SV + 210
        b = B(w).r(w - SV, D, w, X).r(0, X - SH, w, X).r(0, X - 150, SV, X)
    elif n == 7:
        w = 2 * SV + 130
        b = B(w).r(0, D, SV, X).r(w - SV, D, w, X).r(0, D, w, D + SD)
    elif n == 8:
        w = 2 * SV + 130
        b = B(w).r(0, D, SV, X).r(w - SV, D, w, X).r(0, X - SH, w, X)
    elif n == 9:
        w = 2 * SV + LC + 10
        b = B(w).r(w - SV, D, w, X)
        b.r(0, 40, w, X); b.cut(SV, 40 + SH, w - SV, X - SH)
    return b


# ---------------------------------------------------------------- punctuation

def punct(name):
    dw, dh = DOT_W, round(DOT_W * 1.15)
    if name == 'period':
        return B(dw).r(0, 0, dw, dh, 0.45 * dw)
    if name == 'colon':
        return B(dw).r(0, 0, dw, dh, 0.45 * dw).r(0, dh + 60, dw, 2 * dh + 60, 0.45 * dw)
    if name == 'exclam':
        return B(SV).r(0, 0, SV, dh, 0.45 * SV).r(0, dh + 60, SV, A)
    if name == 'arabiccomma':
        return B(dw + 40).r(0, 0, dw, dh + 20, 0.45 * dw).r(40, dh - 30, dw + 40, dh + 110, 0.4 * dw)
    if name == 'arabicsemicolon':
        b = B(dw + 40).r(20, 0, dw + 20, dh, 0.45 * dw)
        return b.r(0, dh + 60, dw, 2 * dh + 70, 0.45 * dw).r(40, 2 * dh + 20, dw + 40, 2 * dh + 150, 0.4 * dw)
    if name == 'arabicquestion':
        w = SV + 190
        b = B(w)
        b.r(0, A - SH, w, A).r(0, 240, SV, A).r(0, 240, SV + 100, 240 + SH).r(SV, 160, SV + 100, 240 + SH)
        b.r(SV, 0, SV + 100, 110, 45)
        return b
    if name == 'hyphen':
        return B(220).r(0, 110, 220, 110 + SH)
    if name == 'parenleft':
        w = SV + 70
        return B(w).r(0, D + 40, SV, A - 20).r(0, A - 20 - SH, w, A - 20).r(0, D + 40, w, D + 40 + SH)
    if name == 'parenright':
        w = SV + 70
        return B(w).r(w - SV, D + 40, w, A - 20).r(0, A - 20 - SH, w, A - 20).r(0, D + 40, w, D + 40 + SH)
    if name in ('guillemotleft', 'guillemotright'):
        t = 0.6 * SV
        def chev(x0, left):
            pts = [(0, 130), (120, 260), (120 + t, 260 - t), (t + 30, 130), (120 + t, t), (120, 0)]
            if not left:
                pts = [(150 + t - x, y) for x, y in pts]
            return [(x + x0, y) for x, y in pts]
        b = B(260 + t)
        b.poly(chev(0, name == 'guillemotleft'))
        b.poly(chev(110, name == 'guillemotleft'))
        return b
    raise KeyError(name)


# ---------------------------------------------------------------- catalogue
# name: (codepoints, joining, design)    joining: 'D' dual, 'R' right, 'U' none

LETTERS = {
    'alef':        ([0x0627], 'R', alef),
    'alefmadda':   ([0x0622], 'R', alef_madda),
    'alefhamza':   ([0x0623], 'R', alef_hamza_above),
    'alefhamzabelow': ([0x0625], 'R', alef_hamza_below),
    'hamza':       ([0x0621], 'U', hamza_isol),
    'beh':         ([0x0628], 'D', lambda f: beh_like(f, 1, True)),
    'peh':         ([0x067E], 'D', lambda f: beh_like(f, 3, True)),
    'teh':         ([0x062A], 'D', lambda f: beh_like(f, 2, False)),
    'theh':        ([0x062B], 'D', lambda f: beh_like(f, 3, False)),
    'jeem':        ([0x062C], 'D', lambda f: jeem_like(f, 'below1')),
    'tcheh':       ([0x0686], 'D', lambda f: jeem_like(f, 'below3')),
    'hah':         ([0x062D], 'D', lambda f: jeem_like(f, None)),
    'khah':        ([0x062E], 'D', lambda f: jeem_like(f, 'above1')),
    'dal':         ([0x062F], 'R', lambda f: dal_like(f, False)),
    'thal':        ([0x0630], 'R', lambda f: dal_like(f, True)),
    'reh':         ([0x0631], 'R', lambda f: reh_like(f, 0)),
    'zain':        ([0x0632], 'R', lambda f: reh_like(f, 1)),
    'jeh':         ([0x0698], 'R', lambda f: reh_like(f, 3)),
    'seen':        ([0x0633], 'D', lambda f: seen_like(f, 0)),
    'sheen':       ([0x0634], 'D', lambda f: seen_like(f, 3)),
    'sad':         ([0x0635], 'D', lambda f: sad_like(f, False)),
    'dad':         ([0x0636], 'D', lambda f: sad_like(f, True)),
    'tah':         ([0x0637], 'D', lambda f: tah_like(f, False)),
    'zah':         ([0x0638], 'D', lambda f: tah_like(f, True)),
    'ain':         ([0x0639], 'D', lambda f: ain_like(f, False)),
    'ghain':       ([0x063A], 'D', lambda f: ain_like(f, True)),
    'feh':         ([0x0641], 'D', lambda f: feh_like(f, 1)),
    'qaf':         ([0x0642], 'D', lambda f: feh_like(f, 2, qaf=True)),
    'keheh':       ([0x06A9, 0x0643], 'D', lambda f: kaf_like(f)),
    'gaf':         ([0x06AF], 'D', lambda f: kaf_like(f, gaf=True)),
    'lam':         ([0x0644], 'D', lambda f: lam(f)),
    'meem':        ([0x0645], 'D', lambda f: meem(f)),
    'noon':        ([0x0646], 'D', lambda f: noon(f)),
    'waw':         ([0x0648], 'R', lambda f: waw(f)),
    'wawhamza':    ([0x0624], 'R', lambda f: waw(f, hz=True)),
    'heh':         ([0x0647], 'D', lambda f: heh(f)),
    'tehmarbuta':  ([0x0629], 'R', lambda f: heh(f, dots=2)),
    'yeh':         ([0x06CC, 0x064A, 0x0649], 'D', lambda f: yeh(f)),
    'yehhamza':    ([0x0626], 'D', lambda f: yeh(f, hz=True)),
    'tatweel':     ([0x0640], 'D', tatweel),
}

PERSIAN_DIGITS = 0x06F0
ARABIC_DIGITS = 0x0660

PUNCT = {
    'period': [0x002E, 0x06D4], 'colon': [0x003A], 'exclam': [0x0021],
    'arabiccomma': [0x060C], 'arabicsemicolon': [0x061B], 'arabicquestion': [0x061F],
    'hyphen': [0x002D], 'parenleft': [0x0028], 'parenright': [0x0029],
    'guillemotleft': [0x00AB], 'guillemotright': [0x00BB],
}
