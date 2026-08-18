#!/usr/bin/env python3
"""Step 6 — re-score after the hand-verification the pre-registration owed.

PREREGISTRATION-01.md: "Artefacts found by hand are removed from the numerator and the
clause is re-scored." Where the artefact is the *before* value, the section cannot be
scored at that end at all, so it leaves the arm as well as the numerator — the stricter
reading, and the one that costs this study its margin rather than protecting it.

The artefacts are listed here explicitly, each with the string that fooled the extraction
rule, so the removal is auditable and nobody has to take my word for it. Nothing else is
removed.

Usage: python3 rescore.py
"""

import json
import statistics
import sys

BASE = "projects/2026-08-18-when-the-law-reopens-the-page"

# Found by hand in data/handcheck.txt, 2026-08-18. Each entry names the text the copied
# extraction rule read as an edition year.
ARTEFACTS = {
    (46, "160.076-5"): {
        "end": "before", "read": 1924,
        "actually": "a fax number — 'telephone 202-372-1392 or fax 202-372-1924'",
        "effect": "counted as a move of 97 years; leaves the arm",
    },
    (24, "3280.4"): {
        "end": "both", "read": "2025 -> 2021",
        "actually": "a street address ('2025 M Street, NW') at the before end and a UL "
                    "standard number ('UL 2021-1997', whose edition is 1997) at the after end",
        "effect": "the corpus's only retreat; both ends artefact, leaves the arm",
    },
}

# Flagged by hand but NOT removed — a genuine ambiguity, reported as a sensitivity check.
FLAGGED = {
    (40, "1066.1010"): {
        "read": 2026,
        "note": "'California 2026 and Subsequent Model Year … Test Procedures' — the year is "
                "the document's model-year scope, not a printed edition year. Defensible "
                "either way; kept, and the effect of dropping it is printed below.",
    },
}


def thaw(arm: list[dict]) -> tuple[int, int, float | None]:
    moved = [r for r in arm if r["moved"]]
    pct = 100.0 * len(moved) / len(arm) if arm else None
    return len(moved), len(arm), pct


def main() -> int:
    recs = json.load(open(f"{BASE}/data/moves.json"))["records"]
    arm0 = [r for r in recs if r["scorable_both_ends"]]

    n_moved, n_arm, pct0 = thaw(arm0)
    arm1 = [r for r in arm0 if (r["title"], r["section"]) not in ARTEFACTS]
    m1, a1, pct1 = thaw(arm1)
    arm2 = [r for r in arm1 if (r["title"], r["section"]) not in FLAGGED]
    m2, a2, pct2 = thaw(arm2)

    d0 = sorted(r["delta"] for r in arm0 if r["moved"])
    d1 = sorted(r["delta"] for r in arm1 if r["moved"])

    out = {
        "C3_as_scored": {"moved": n_moved, "arm": n_arm, "pct": round(pct0, 1),
                         "band": 60.0, "verdict": "HELD" if pct0 >= 60 else "FAILED"},
        "C3_after_handcheck": {"moved": m1, "arm": a1, "pct": round(pct1, 1),
                               "band": 60.0, "verdict": "HELD" if pct1 >= 60 else "FAILED"},
        "C3_sensitivity_also_dropping_flagged": {
            "moved": m2, "arm": a2, "pct": round(pct2, 1),
            "band": 60.0, "verdict": "HELD" if pct2 >= 60 else "FAILED"},
        "C5_as_scored": {"median_delta": statistics.median(d0), "arm": len(d0)},
        "C5_after_handcheck": {"median_delta": statistics.median(d1), "arm": len(d1)},
        "retreats_after_handcheck": sum(1 for r in arm1 if r["retreat"]),
        "artefacts_removed": [{"section": f"{t} CFR {s}", **v} for (t, s), v in ARTEFACTS.items()],
        "flagged_kept": [{"section": f"{t} CFR {s}", **v} for (t, s), v in FLAGGED.items()],
        "margin": {
            "C3_sections_from_failing": max(
                0, m1 - int(-(-60 * a1 // 100)) + (1 if (60 * a1) % 100 else 0)),
            "note": "C3 fails at 59.9 %; the printed pct and arm are the honest form of this.",
        },
    }
    with open(f"{BASE}/data/rescore.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
