#!/usr/bin/env python3
"""Step 4 — score the six clauses of PREREGISTRATION-01.md.

Every band below is copied from that file and is not touched after seeing a result.
The voiding rule (an arm under 10 sections → void, not failed) and the feasibility-peek
re-score (10 CFR 300.13 excluded) are applied as written there.

Usage: python3 score.py
"""

import json
import statistics
import sys

BASE = "projects/2026-08-18-when-the-law-reopens-the-page"
PEEK = (10, "300.13")
MIN_ARM = 10


def verdict(value, band, cmp_: str, arm: int) -> str:
    if arm < MIN_ARM:
        return "VOID"
    if value is None:
        return "VOID"
    ok = value >= band if cmp_ == ">=" else value <= band
    return "HELD" if ok else "FAILED"


def score(records: list[dict], label: str) -> dict:
    n = len(records)
    out = {"label": label, "corpus": n}

    # C1 — coverage of the version history (fetch_versions.py, all HTTP 200)
    covered = sum(1 for r in records if r.get("after_http") == "200")
    c1 = 100.0 * covered / n
    out["C1"] = {"value_pct": round(c1, 1), "band": 95.0, "arm": n,
                 "verdict": verdict(c1, 95.0, ">=", n),
                 "detail": f"{covered}/{n} sections returned a section snapshot"}

    # C2 — reopening rate
    reopened = [r for r in records if r["reopened"]]
    c2 = 100.0 * len(reopened) / n
    out["C2"] = {"value_pct": round(c2, 1), "band": 50.0, "arm": n,
                 "verdict": verdict(c2, 50.0, ">=", n),
                 "detail": f"{len(reopened)}/{n} amended on or after 2017-01-02"}

    # C3 — the thaw rate
    arm3 = [r for r in reopened if r["scorable_both_ends"]]
    moved = [r for r in arm3 if r["moved"]]
    c3 = 100.0 * len(moved) / len(arm3) if arm3 else None
    out["C3"] = {"value_pct": round(c3, 1) if c3 is not None else None, "band": 60.0,
                 "arm": len(arm3), "verdict": verdict(c3, 60.0, ">=", len(arm3)),
                 "detail": f"{len(moved)}/{len(arm3)} reopened sections bind newer material "
                           f"in 2026 than in 2017"}

    # C4 — the untouched remainder
    untouched = [r for r in records if not r["reopened"] and r.get("after_edition") is not None]
    med4 = statistics.median(r["after_edition"] for r in untouched) if untouched else None
    out["C4"] = {"value": med4, "band": 2010, "arm": len(untouched),
                 "verdict": verdict(-med4 if med4 is not None else None,
                                    -2010, ">=", len(untouched)),
                 "detail": f"median newest edition year of {len(untouched)} sections "
                           f"not amended since 2017"}

    # C5 — the size of a move
    deltas = [r["delta"] for r in moved]
    med5 = statistics.median(deltas) if deltas else None
    out["C5"] = {"value": med5, "band": 5, "arm": len(deltas),
                 "verdict": verdict(med5, 5, ">=", len(deltas)),
                 "detail": f"median years gained by the {len(deltas)} sections that moved"}

    # C6 — parser agreement with 2026-08-17
    both = [r for r in records
            if r.get("after_edition") is not None and r.get("prior_newest_edition_year") is not None]
    agree = [r for r in both if r["after_edition"] == r["prior_newest_edition_year"]]
    c6 = 100.0 * len(agree) / len(both) if both else None
    out["C6"] = {"value_pct": round(c6, 1) if c6 is not None else None, "band": 98.0,
                 "arm": len(both), "verdict": verdict(c6, 98.0, ">=", len(both)),
                 "detail": f"{len(agree)}/{len(both)} agree with yesterday's extraction"}

    # description, not a clause
    retreats = [r for r in arm3 if r["retreat"]]
    flat = [r for r in arm3 if not r["moved"] and not r["retreat"]]
    out["description"] = {
        "reopened_unscorable": len(reopened) - len(arm3),
        "retreats": len(retreats),
        "flat": len(flat),
        "bytes_differ_among_reopened": sum(1 for r in reopened if r["bytes_differ"]),
        "median_after_edition_all": statistics.median(
            [r["after_edition"] for r in records if r.get("after_edition") is not None]),
        "median_after_edition_reopened": statistics.median(
            [r["after_edition"] for r in reopened if r.get("after_edition") is not None]),
    }
    return out


def main() -> int:
    d = json.load(open(f"{BASE}/data/moves.json"))
    recs = d["records"]
    full = score(recs, "full corpus")
    nopeek = score([r for r in recs if (r["title"], r["section"]) != PEEK],
                   "without the feasibility-peek section (10 CFR 300.13)")

    result = {"before_date": d["before_date"], "after_date": d["after_date"],
              "scored": "2026-08-18", "full": full, "without_peek": nopeek}
    with open(f"{BASE}/data/score.json", "w") as fh:
        json.dump(result, fh, indent=1)

    for s in (full, nopeek):
        print(f"\n== {s['label']} (n={s['corpus']}) ==")
        for c in ("C1", "C2", "C3", "C4", "C5", "C6"):
            v = s[c]
            val = v.get("value_pct", v.get("value"))
            print(f"  {c} {v['verdict']:6} value={val} band={v['band']} arm={v['arm']}"
                  f"  — {v['detail']}")
        print(f"  description: {json.dumps(s['description'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
