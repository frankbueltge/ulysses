#!/usr/bin/env python3
"""The failing assertion over this record, read as a series instead of a number.

SUPERSEDED 2026-08-07 (tick 42) by `assertion-precision-tick42.py`. The body below is
left unchanged: it is the artefact that produced a statement now corrected, and under
this line's own rule (tick 33) a correction is a second trace, never an erasure of the
first. The defect: `ASSERTION` matches both operands with `(\\d+)`, so a right-hand
operand of `17.5` is read as `17`. Seven of the twenty landed builds report a fractional
right-hand operand, and on the truncated reading the two sides looked equal in every
build — which is what the tick-39 record says, and what is wrong. Do not read this
script's output as a finding.

Tick 39 (2026-08-06). The site build has reported one failing assertion over this
work-line's record since 2026-08-05:

    src/lib/atelier/refrain.test.ts > the real records … > the first work-line reads
    as the record states: aspects present, deferrals found
    AssertionError: expected N to be greater than N

Tick 37 read one letter and treated N as a count to be raised. That was the mistake this
script exists to correct. The letters are versioned files in `atelier-feedback/`, and
their history carries **six** distinct builds with three values of N — 17, 17, 18, 19 —
each build landing at a known time against a known state of `main`. A single number is a
riddle; a series against a timeline is a measurement.

What this does, reading only this repository:

  1. extracts (build time, N) from every landed revision of the build letters;
  2. pairs each build with the state of `main` it could have seen;
  3. computes a battery of candidate quantities of SCORE.md / TRACE.md at those states;
  4. reports every candidate whose series equals the observed series of N.

It changes nothing and needs no network. The fixture itself lives in a repository this
practice cannot read; every statement this script supports is about *which quantities of
this record are consistent with the numbers reported*, never about what the fixture does.

    python3 assertion-pair-tick39.py [repo-root]
"""

import re
import subprocess
import sys
from pathlib import Path

PROJ = "projects/2026-07-23-negative-parallax"
LETTERS = "atelier-feedback"
ASSERTION = re.compile(r"expected (\d+) to be greater than (\d+)")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True).stdout


def show(root, rev, path):
    return git(root, "show", f"{rev}:{path}")


# --- 1. the letters, as a series ----------------------------------------------------

def letter_series(root):
    """(iso time, left, right) for every landed revision of a build letter that quotes
    the assertion. Newest last. The letter files are rewritten in place by the build, so
    the series lives in git history, not in the working tree — which is why tick 37,
    reading only the working tree, saw one value where there were three."""
    out = []
    files = sorted(p.name for p in (root / LETTERS).glob("2026-*.md"))
    for f in files:
        path = f"{LETTERS}/{f}"
        revs = git(root, "log", "--format=%h %aI", "--", path).strip().splitlines()
        for line in revs:
            rev, when = line.split()
            m = ASSERTION.search(show(root, rev, path))
            if m:
                out.append((when, rev, int(m.group(1)), int(m.group(2))))
    return sorted(out)


# --- 2. the states of main a build could have seen -----------------------------------

def landings(root):
    """(iso time, rev) for every commit that changed this work-line's record."""
    lines = git(root, "log", "--format=%h %aI", "--",
                f"{PROJ}/SCORE.md", f"{PROJ}/TRACE.md").strip().splitlines()
    return sorted((w, r) for r, w in (l.split() for l in lines))


def state_at(land, when):
    seen = [rev for t, rev in land if t <= when]
    return seen[-1] if seen else None


# --- 3. candidate quantities ---------------------------------------------------------

def candidates(root, rev):
    score = show(root, rev, f"{PROJ}/SCORE.md")
    trace = show(root, rev, f"{PROJ}/TRACE.md")
    s11 = score[score.index("## 11."):] if "## 11." in score else ""
    c = {}

    tick_nums = [int(n) for n in re.findall(r"(?m)^## Tick (\d+)", trace)]
    top = max(tick_nums, default=0)
    c["trace_sections"] = len(tick_nums)
    c["highest_tick"] = top
    c["half_highest_tick"] = top // 2
    c["half_trace_sections"] = len(tick_nums) // 2

    heads = list(re.finditer(r"(?m)^\*\*(Update — |Tick \d+ |Refrain reading)", s11))
    bounds = [h.start() for h in heads] + [len(s11)]
    entries = [s11[bounds[i]:bounds[i + 1]] for i in range(len(heads))]
    c["s11_entries"] = len(entries)
    c["half_s11_entries"] = len(entries) // 2
    c["s11_with_aspect"] = sum(1 for e in entries if re.search(r"aspect", e, re.I))
    c["s11_numbered"] = len(re.findall(r"(?m)^\*\*Tick \d+ ", s11))
    c["s11_numbered_with_aspect"] = sum(
        1 for e in entries if e.startswith("**Tick ") and re.search(r"aspect", e, re.I))

    bodies = re.split(r"(?m)^## Tick \d+", trace)[1:]
    c["trace_sec_with_aspect"] = sum(1 for b in bodies if re.search(r"aspect", b, re.I))
    c["trace_sec_aspect_named"] = sum(
        1 for b in bodies
        if re.search(r"aspect[^.\n]{0,40}(territory|home|opening)", b, re.I))
    c["trace_sec_defer"] = sum(1 for b in bodies if re.search(r"defer", b, re.I))

    # per-tick coverage: for each tick number the record knows, is an aspect stated for
    # it anywhere in either file?
    known = sorted(set(tick_nums) | {int(n) for n in re.findall(r"(?m)^\*\*Tick (\d+) ", s11)})
    per_tick = 0
    for n in known:
        blocks = re.findall(rf"(?ms)^## Tick {n} —.*?(?=^## Tick |\Z)", trace)
        blocks += re.findall(rf"(?ms)^\*\*Tick {n} \(.*?(?=^\*\*Tick |\Z)", s11)
        blocks += re.findall(rf"(?m)^\s*# tick {n} —.*$", score)
        if any(re.search(r"aspect|territory|home|opening", b, re.I) for b in blocks):
            per_tick += 1
    c["ticks_with_an_aspect_stated"] = per_tick
    c["ticks_known"] = len(known)
    c["half_ticks_known"] = len(known) // 2

    c["score_defer"] = len(re.findall(r"defer", score, re.I))
    c["trace_defer"] = len(re.findall(r"defer", trace, re.I))
    return c


# --- 4. match ------------------------------------------------------------------------

def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
    letters = letter_series(root)
    land = landings(root)

    print("the assertion as reported, build by build")
    print("  build (UTC)            letter  N_left  N_right  state of main it could see")
    states = []
    for when, rev, left, right in letters:
        st = state_at(land, when)
        states.append(st)
        print(f"  {when[:16].replace('T', ' ')}       {rev}    {left:>3}     {right:>3}"
              f"    {st}")

    obs_left = [l for _, _, l, _ in letters]
    obs_right = [r for _, _, _, r in letters]
    print(f"\n  observed left  : {obs_left}")
    print(f"  observed right : {obs_right}")
    print(f"  the two operands are {'equal in every build' if obs_left == obs_right else 'NOT always equal'}")

    uniq = sorted(set(s for s in states if s))
    table = {s: candidates(root, s) for s in uniq}
    print(f"\ncandidate quantities of this record, at the {len(uniq)} states the builds saw")
    keys = sorted(table[uniq[0]])
    w = max(len(k) for k in keys)
    order = [s for s in states]
    print("  " + "quantity".ljust(w) + "  series across the builds above")
    hits = []
    for k in keys:
        series = [table[s][k] for s in order]
        mark = ""
        if series == obs_left:
            mark = "   <== matches the reported series"
            hits.append(k)
        print("  " + k.ljust(w) + "  " + str(series) + mark)

    print("\nquantities of this record whose series equals the reported one: "
          + (", ".join(hits) if hits else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
