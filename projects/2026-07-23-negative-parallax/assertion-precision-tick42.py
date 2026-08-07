#!/usr/bin/env python3
"""The failing assertion over this record, read with its fractional digits.

Tick 42 (2026-08-07). Supersedes `assertion-pair-tick39.py`, which is left in place
unchanged as the artefact that produced the statement corrected here.

What tick 39 got right: the build letters are files each build rewrites in place, so the
assertion has to be read as a series out of git history, not as one number out of the
working tree. What tick 39 got wrong: it matched both operands with the pattern `(\\d+)`.
Four of the builds it read report a right-hand operand of **17.5**, and `(\\d+)` returns
`17` from that string. On that truncated reading the two operands looked equal in every
build, and the record of tick 39 says so. They are not.

The correction is not incidental to this work-line. The line's subject is that error is
lodged in the relation between a value and its own claimed precision; the instrument
built to read this assertion dropped the precision and reported the relation as equality.

What this does, reading only this repository and no network:

  1. extracts (build time, revision, left, right) from every landed revision of a build
     letter that quotes the assertion, with `[\\d.]+` on both operands;
  2. pairs each build with the state of `main` it could have seen;
  3. tests the right-hand operand against `highest tick / 2` — exact division, no floor;
  4. reports the left-hand operand's series and tests it against a battery of candidate
     quantities of SCORE.md and TRACE.md.

Every statement it supports is about which quantities of *this* record are consistent
with the numbers reported. The fixture lives in a repository this practice cannot read,
and nothing here is a claim about what the fixture does.

    python3 assertion-precision-tick42.py [repo-root]
"""

import csv
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

PROJ = "projects/2026-07-23-negative-parallax"
LETTERS = "atelier-feedback"

# The correction. Tick 39 used `(\d+)` here on both operands.
ASSERTION = re.compile(r"expected ([\d.]+) to be greater than ([\d.]+)")
TRUNCATING = re.compile(r"expected (\d+) to be greater than (\d+)")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True).stdout


def show(root, rev, path):
    return git(root, "show", f"{rev}:{path}")


def letter_series(root):
    """(iso time, rev, left, right, right_as_tick_39_read_it) per landed letter revision."""
    out = []
    for p in sorted((root / LETTERS).glob("2026-*.md")):
        path = f"{LETTERS}/{p.name}"
        for line in git(root, "log", "--format=%h %aI", "--", path).strip().splitlines():
            rev, when = line.split()
            body = show(root, rev, path)
            m = ASSERTION.search(body)
            if not m:
                continue
            t = TRUNCATING.search(body)
            out.append((when, rev, Fraction(m.group(1)), Fraction(m.group(2)),
                        Fraction(t.group(2)) if t else None))
    return sorted(out)


def landings(root):
    lines = git(root, "log", "--format=%h %aI", "--",
                f"{PROJ}/SCORE.md", f"{PROJ}/TRACE.md").strip().splitlines()
    return sorted((w, r) for r, w in (l.split() for l in lines))


def state_at(land, when):
    seen = [rev for t, rev in land if t <= when]
    return seen[-1] if seen else None


def candidates(root, rev):
    """Quantities of this record at one state of main."""
    score = show(root, rev, f"{PROJ}/SCORE.md")
    trace = show(root, rev, f"{PROJ}/TRACE.md")
    s11 = score[score.index("## 11."):] if "## 11." in score else ""
    fm = score[:score.index("\n---", 4)] if score.startswith("---") else ""
    c = {}

    nums = [int(n) for n in re.findall(r"(?m)^## Tick (\d+)", trace)]
    bodies = re.split(r"(?m)^## Tick \d+", trace)[1:]
    top = max(nums, default=0)
    c["highest_tick"] = Fraction(top)
    c["half_highest_tick_exact"] = Fraction(top, 2)
    c["half_highest_tick_floored"] = Fraction(top // 2)
    c["trace_sections"] = Fraction(len(nums))
    c["half_trace_sections_exact"] = Fraction(len(nums), 2)

    heads = list(re.finditer(r"(?m)^\*\*(Update — |Tick \d+ |Refrain reading)", s11))
    bounds = [h.start() for h in heads] + [len(s11)]
    entries = [s11[bounds[i]:bounds[i + 1]] for i in range(len(heads))]
    c["s11_entries"] = Fraction(len(entries))
    c["half_s11_entries_exact"] = Fraction(len(entries), 2)
    c["s11_with_aspect"] = Fraction(sum(1 for e in entries if re.search(r"aspect", e, re.I)))
    c["s11_numbered"] = Fraction(len(re.findall(r"(?m)^\*\*Tick \d+ ", s11)))
    c["s11_update_marker"] = Fraction(len(re.findall(r"(?m)^\*\*Update — ", s11)))
    c["s11_bold_aspect_word"] = Fraction(
        len(re.findall(r"(?i)\*\*(?:territory|home|opening)\*\*", s11)))

    c["trace_sec_with_aspect"] = Fraction(sum(1 for b in bodies if re.search(r"aspect", b, re.I)))
    c["trace_sec_aspect_named"] = Fraction(sum(
        1 for b in bodies
        if re.search(r"(?i)aspect[^.\n]{0,60}(territory|home|opening)", b)))
    c["trace_sec_bold_aspect_word"] = Fraction(sum(
        1 for b in bodies if re.search(r"(?i)\*\*(?:territory|home|opening)\*\*", b)))
    c["trace_sec_preopening"] = Fraction(sum(1 for b in bodies if re.search(r"(?i)pre-opening", b)))
    c["trace_sec_defer"] = Fraction(sum(1 for b in bodies if re.search(r"defer", b, re.I)))
    c["trace_sec_aspect_and_defer"] = Fraction(sum(
        1 for b in bodies if re.search(r"aspect", b, re.I) and re.search(r"defer", b, re.I)))
    c["fm_tick_comments"] = Fraction(len(re.findall(r"# tick (\d+)", fm)))

    known = sorted(set(nums) | {int(n) for n in re.findall(r"(?m)^\*\*Tick (\d+) ", s11)})
    per_tick = 0
    for n in known:
        blocks = re.findall(rf"(?ms)^## Tick {n} —.*?(?=^## Tick |\Z)", trace)
        blocks += re.findall(rf"(?ms)^\*\*Tick {n} \(.*?(?=^\*\*Tick |\Z)", s11)
        blocks += re.findall(rf"(?m)^\s*# tick {n} —.*$", score)
        if any(re.search(r"(?i)aspect|territory|home|opening", b) for b in blocks):
            per_tick += 1
    c["ticks_with_an_aspect_stated"] = Fraction(per_tick)
    c["ticks_known"] = Fraction(len(known))
    c["half_ticks_known_exact"] = Fraction(len(known), 2)
    c["half_ticks_known_floored"] = Fraction(len(known) // 2)
    return c


def fmt(x):
    return str(int(x)) if x.denominator == 1 else f"{float(x):g}"


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
    letters = letter_series(root)
    if not letters:
        print("no landed build letter quotes the assertion")
        return 1
    land = landings(root)

    states = [state_at(land, when) for when, *_ in letters]

    print("the assertion, build by build, with its fractional digits")
    print("  build (UTC)         letter   left   right   tick-39 read right as   state")
    for (when, rev, left, right, trunc), st in zip(letters, states):
        flag = "" if trunc == right else "  <- truncated"
        print(f"  {when[:16].replace('T', ' ')}    {rev}  {fmt(left):>5}  {fmt(right):>6}"
              f"   {fmt(trunc) if trunc is not None else '-':>20}{flag}   {st}")

    truncated = [r for *_, r, t in ((w, v, l, r, t) for w, v, l, r, t in letters) if r != t]
    print(f"\n  builds whose right-hand operand tick 39 read wrongly: {len(truncated)}"
          f" of {len(letters)}")
    obs_l = [l for _, _, l, _, _ in letters]
    obs_r = [r for _, _, _, r, _ in letters]
    print(f"  operands equal in every build (tick 39's statement): "
          f"{'yes' if obs_l == obs_r else 'NO — ' + str(sum(1 for a, b in zip(obs_l, obs_r) if a != b)) + ' builds differ'}")

    uniq = sorted(set(states), key=states.index)
    table = {s: candidates(root, s) for s in uniq}

    print("\nthe right-hand operand against the record")
    ok = all(table[s]["half_highest_tick_exact"] == r for s, r in zip(states, obs_r))
    flo = all(table[s]["half_highest_tick_floored"] == r for s, r in zip(states, obs_r))
    print(f"  right == highest tick / 2, exact division : {'holds in all ' + str(len(letters)) + ' builds' if ok else 'fails'}")
    print(f"  right == floor(highest tick / 2)          : {'holds' if flo else 'fails — this is the form tick 39 and 41 carried'}")

    print("\nthe left-hand operand against a battery of quantities of this record")
    print("  observed left : " + str([fmt(x) for x in obs_l]))
    hits = []
    for k in sorted(table[uniq[0]]):
        series = [table[s][k] for s in states]
        mark = ""
        if series == obs_l:
            hits.append(k)
            mark = "   <== matches"
        print(f"  {k:30s} {[fmt(x) for x in series]}{mark}")
    print("\n  quantities whose series equals the left operand: "
          + (", ".join(hits) if hits else "NONE — the left operand is not identified from here"))

    print("\nwhere this line's TRACE sections state their refrain aspect (working tree)")
    trace = (root / PROJ / "TRACE.md").read_text()
    nums = [int(n) for n in re.findall(r"(?m)^## Tick (\d+)", trace)]
    bodies = re.split(r"(?m)^## Tick \d+", trace)[1:]
    probes = [("aspect", r"(?i)aspect"),
              ("bold aspect word", r"(?i)\*\*(?:territory|home|opening)\*\*"),
              ("refrain", r"(?i)refrain"),
              ("pre-opening", r"(?i)pre-opening")]
    print("  tick  " + "  ".join(f"{n:>16}" for n, _ in probes))
    for n, b in list(zip(nums, bodies))[-10:]:
        print(f"  {n:4d}  " + "  ".join(
            f"{('yes' if re.search(p, b) else '—'):>16}" for _, p in probes))
    print("  (the aspect statements of the most recent ticks stand in SCORE.md §11 and in the")
    print("   frontmatter refrain reading, not in these sections.)")

    out = root / PROJ / "assertion-series-tick42.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["build_utc", "letter_rev", "left", "right",
                    "right_as_tick39_read_it", "state_rev", "highest_tick",
                    "half_highest_tick_exact"])
        for (when, rev, left, right, trunc), st in zip(letters, states):
            w.writerow([when, rev, fmt(left), fmt(right),
                        fmt(trunc) if trunc is not None else "",
                        st, fmt(table[st]["highest_tick"]),
                        fmt(table[st]["half_highest_tick_exact"])])
    print(f"\nwritten: {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
