#!/usr/bin/env python3
"""Where this work-line states its refrain aspect, and how often — counted, not asserted.

Written for tick 37 (2026-08-06) to judge the build letters of 2026-08-05 and 2026-08-06
(`atelier-feedback/`), which report one failing assertion over this line's record:

    src/lib/atelier/refrain.test.ts > the real records … > the first work-line reads as the
    record states: aspects present, deferrals found
    AssertionError: expected 18 to be greater than 18

The test lives in another repository and is not readable from here. What *is* decidable from
inside this repository: which quantities of this record equal 18, when each of them last
changed, and where the aspect statements actually stand. This script answers exactly that.

Reads only SCORE.md and TRACE.md of this project. Prints counts; changes nothing.

    python3 aspect-count-tick37.py [project-dir]
"""

import re
import sys
from pathlib import Path

# The two entry markers §11 has used. The second replaced the first at tick 23 (2026-08-01);
# nothing announced the change, because nothing in this repository depended on it.
OLD_MARKER = r"(?m)^\*\*Update — "
NEW_MARKER = r"(?m)^\*\*Tick (\d+) "
DECLARATION = r"\*\*Refrain reading"


def frontmatter(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent)
    score = (root / "SCORE.md").read_text()
    trace = (root / "TRACE.md").read_text()

    fm = frontmatter(score)
    s11 = score[score.index("## 11.") :]

    # --- quantities of this record that equal 18 -------------------------------------------
    old_format = len(re.findall(OLD_MARKER, s11)) + len(re.findall(DECLARATION, s11))
    defer_cs = len(re.findall(r"defer", score))

    # --- what §11 actually carries ----------------------------------------------------------
    heads = list(re.finditer(r"(?m)^\*\*(Update — |Tick \d+ |Refrain reading)", s11))
    bounds = [h.start() for h in heads] + [len(s11)]
    entries = [s11[bounds[i] : bounds[i + 1]] for i in range(len(heads))]
    with_aspect = [e for e in entries if re.search(r"aspect", e, re.I)]

    s11_ticks = sorted({int(n) for n in re.findall(NEW_MARKER, s11)} |
                       {int(n) for n in re.findall(r"TRACE tick (\d+)", s11)})

    # --- the line's ticks, as TRACE numbers them -------------------------------------------
    nums = [int(n) for n in re.findall(r"(?m)^## Tick (\d+)", trace)]
    bodies = re.split(r"(?m)^## Tick \d+", trace)[1:]
    trace_aspect = sorted(
        n for n, b in zip(nums, bodies)
        if re.search(r"[Pp]re-opening check", b) or re.search(r"aspect", b, re.I)
    )
    highest = max(nums)
    fm_ticks = sorted(int(n) for n in re.findall(r"# tick (\d+)", fm))

    print("quantities of SCORE.md that equal 18")
    print(f"  §11 entries in the ORIGINAL marker format (**Update —) + the")
    print(f"  declaration's own refrain reading            : {old_format}")
    print(f"  occurrences of 'defer' (case-sensitive)      : {defer_cs}")
    print()
    print("what §11 carries, both formats counted")
    print(f"  entries                                      : {len(entries)}")
    print(f"  entries stating an aspect                    : {len(with_aspect)}")
    print(f"  ticks named                                  : {len(s11_ticks)}"
          f" (last {max(s11_ticks)})")
    print()
    print("the line's ticks")
    print(f"  sections in TRACE.md                         : {len(nums)}"
          f" (highest {highest}; no section for"
          f" {[n for n in range(1, highest + 1) if n not in nums] or 'none'})")
    print(f"  ticks whose TRACE states an aspect           : {len(trace_aspect)}")
    print(f"  ticks in the frontmatter refrain reading     : {len(fm_ticks)}"
          f" (last {max(fm_ticks)})")
    print(f"  ticks with no §11 entry at all               :"
          f" {[n for n in range(23, highest + 1) if n not in s11_ticks]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
