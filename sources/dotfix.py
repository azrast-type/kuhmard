"""Dot-collision fixes for Kuhmard, independent of kerning.

Scans a built font with test_collisions (every letter pair, every joining situation,
kerning on) and, wherever a letter's dots (or madda / hamza) come closer than the
minimum gap to the neighbouring letter, plans a contextual alternate of one letter
with only its dots moved away from the neighbour. Kerning values are never touched:
build_ai.py adds the alternates, one calt lookup per round, and copies every kern
pair of the plain glyph onto its alternate. Rounds repeat on the rebuilt font until
the scan is clean, so a move that crowds the other neighbour is caught too.

Which dots move, per pair: ordinary dots before a madda or hamza (those belong to
their alef / seat), then the smaller move; dots facing dots may share the move.

Run on its own to see the plan: python3 dotfix.py [font.otf]
"""
import re
import sys
import test_collisions as TC

MIN_GAP = 40
CAP = 160                     # never move dots further than this
SEATED = ("alefmadda", "alefhamza", "alefhamzabelow", "yehhamza", "wawhamza", "alefwasla")
DS = re.compile(r"^(.*)\.ds([lr])(\d+)$")


def resolve(g):
    """(glyph without its dot move, total move so far)."""
    m = DS.match(g)
    return (m.group(1), (-1 if m.group(2) == "l" else 1) * int(m.group(3))) if m else (g, 0)


def alt_name(orig, total):
    return f"{orig}.ds{'l' if total < 0 else 'r'}{abs(total)}"


def plan(font_path, known=None, min_gap=MIN_GAP):
    """known: {alt: (src, delta)} from earlier rounds.
    Returns (alts, rules, unsolved):
      alts  {alt: (src, delta)}  new glyphs: src with its dots moved by delta
      rules [(right, left, which, alt)]  visual pair; which glyph ('right' | 'left') becomes alt
      unsolved [(gap, text, right, left, what)]"""
    known = dict(known or {})
    TC.load(font_path)
    found = TC.scan(TC.texts())
    pairs = {}
    for (right, left, what), (g, t) in found.items():
        p = pairs.setdefault((right, left), {"gap": g, "text": t, "what": set()})
        p["what"].add(what)
        if g < p["gap"]:
            p["gap"], p["text"] = g, t
    alts, rules, unsolved = {}, [], []
    seated = lambda g: g.split(".")[0] in SEATED
    for (right, left), p in sorted(pairs.items(), key=lambda kv: kv[1]["gap"]):
        if p["what"] == {"letters"}:
            unsolved.append((p["gap"], p["text"], right, left, "letters"))   # bodies: kerning's business
            continue
        has_r, has_l = bool(TC.parts(right)[1].bounds), bool(TC.parts(left)[1].bounds)
        options = []
        for which in ("right", "left", "both"):
            if (which in ("right", "both") and not has_r) or (which in ("left", "both") and not has_l):
                continue
            s = TC.needed_shift(p["text"], left, right, which, min_gap=min_gap, cap=CAP if which != "both" else CAP // 2)
            if s is None or s == (0, 0):
                continue
            moved = {"right": [right], "left": [left], "both": [right, left]}[which]
            other = {"right": [left], "left": [right], "both": []}[which]
            ordinary = any(TC.parts(o)[1].bounds and not seated(o) for o in other + moved)
            cost = max(abs(s[0]), abs(s[1])) + (1000 if any(seated(m) for m in moved) and ordinary else 0)
            options.append((cost, which, s))
        if not options:
            unsolved.append((p["gap"], p["text"], right, left, "/".join(sorted(p["what"]))))
            continue
        _, which, (dl, dr) = min(options)
        made = []
        for w, g, dx in (("right", right, dr), ("left", left, dl)):
            if which not in (w, "both") or dx == 0:
                continue
            orig, tot = resolve(g)
            if tot + dx == 0:
                continue
            alt = alt_name(orig, tot + dx)
            if alt not in known and alt not in alts:
                alts[alt] = (g, dx)
            made.append((w, alt))
        for w, alt in made:
            rules.append((right, left, w, alt))
    return alts, rules, unsolved


if __name__ == "__main__":
    f = next((a for a in sys.argv[1:] if a.endswith(".otf")), "otf/Kuhmard-Bold.otf")
    alts, rules, unsolved = plan(f)
    print(f"{len(rules)} contextual dot moves, {len(alts)} alternates, {len(unsolved)} unsolved")
    for r, l, w, a in rules:
        print(f"  {r} → {l}: {w} becomes {a}")
    for u in unsolved:
        print("  UNSOLVED", u)
