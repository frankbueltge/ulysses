#!/usr/bin/env python3
"""POST-HOC, 2026-08-24. Not pre-registered. Writes replay_repaired.json.

`replay.py` ran once and attached 46 deletion instructions to an annex; the census of
2026-08-23 found 62 (74 with its own post-hoc repair) in a differently split corpus. The
gap is the failure PREREGISTRATION §5.3 named in advance as the likeliest silent one: the
mapping from the amending act's own annex to the base act's annex is the hinge, and the
expression required the two annex names to be adjacent —

    Annex I is amended in accordance with Annex I to this Decision

— while the Journal's actual formula names the base act in between:

    Annex I to Implementing Decision (EU) 2019/1956 is amended in accordance with
    Annex I to this Decision

This file widens the two mapping expressions by exactly that much and re-runs. Its figures
are published BESIDE the pre-registered ones and never in place of them: `replay.json`
carries the scored result. `replay.py` is left exactly as it was executed.
"""

import json
import pathlib
import re

import replay

HERE = pathlib.Path(__file__).resolve().parent

ACT = r"(?:\s+to\s+(?:Commission\s+)?(?:Implementing\s+)?(?:Decision|Regulation)\s*\(EU\)\s*\d{4}/\d+)?"
WIDE_AMEND = re.compile(
    rf"Annex\s+([IVX]+[A-C]?){ACT}\s+is amended in accordance with Annex\s+([IVX]+[A-C]?)\s+to this Decision")
WIDE_INSERT = re.compile(
    rf"Annex\s+([IVX]+[A-C]?){ACT}\s*,\s*as set out in Annex\s+([IVX]+[A-C]?)\s+to this Decision\s*,\s*is inserted")

if __name__ == "__main__":
    scored_amend, scored_insert = replay.MAP_AMEND_RE, replay.MAP_INSERT_RE

    replay.MAP_AMEND_RE, replay.MAP_INSERT_RE = WIDE_AMEND, WIDE_INSERT
    replay.main()
    out = json.loads((HERE / "replay.json").read_text())
    out["POST_HOC"] = (
        "Produced by repair.py after replay.py had been scored once. The mapping "
        "expressions are widened to allow the base act to be named between the two annex "
        "names. Nothing else differs. Not retro-fitted into PREREGISTRATION.md.")
    (HERE / "replay_repaired.json").write_text(json.dumps(out, indent=1) + "\n")

    # both runs are deterministic: restore replay.json to the scored run by re-running it
    replay.MAP_AMEND_RE, replay.MAP_INSERT_RE = scored_amend, scored_insert
    replay.main()
