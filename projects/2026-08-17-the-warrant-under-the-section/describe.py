#!/usr/bin/env python3
"""Description, not clauses: the combined warrant rule.

The pre-registered rule W1 reads only the section's own `<CITA>`. This script reports what the
corpus looks like when the warrant a reader actually meets is used instead — the section's own
note where it has one, otherwise the last `<SOURCE>` note above it (data/part-sources.json).

Nothing here is scored against a band. C1 stands failed as written; these are the numbers that
say why.

Usage: python3 describe.py
"""

import json
import os
import statistics
import sys

DIR = "projects/2026-08-17-the-warrant-under-the-section/data"


def main() -> int:
    w = json.load(open(os.path.join(DIR, "warrants.json")))
    ps = json.load(open(os.path.join(DIR, "part-sources.json")))
    recs = [r for r in w["records"] if not r.get("fetch_failed")]
    pmap = {(r["title"], r["section"]): r for r in ps["records"]}

    comb, none = [], []
    for r in recs:
        y, level = r.get("warrant_year"), "section"
        if not y:
            p = pmap.get((r["title"], r["section"]))
            if p and p.get("part_source_year"):
                y, level = p["part_source_year"], "part"
            else:
                none.append((r["title"], r["section"]))
                continue
        comb.append({**r, "wy": y, "level": level})

    E = [r for r in comb if r.get("newest_edition_year")]
    cross = sorted([r for r in E if r["newest_edition_year"] - r["wy"] >= 3],
                   key=lambda r: -(r["newest_edition_year"] - r["wy"]))

    print(f"combined coverage: {len(comb)}/{len(recs)} = {100*len(comb)/len(recs):.1f} %")
    print(f"no printed warrant anywhere: {none or 'none'}")
    print(f"warrant at section level: {len([r for r in comb if r['level']=='section'])}, "
          f"above the section: {len([r for r in comb if r['level']=='part'])} "
          f"(of which hedged 'unless otherwise noted': {ps['n_hedged']})")
    print(f"median warrant year {statistics.median([r['wy'] for r in comb])}, "
          f"oldest {min(r['wy'] for r in comb)}, "
          f"pre-2000 {len([r for r in comb if r['wy'] < 2000])}")
    print(f"arm E (combined): {len(E)}   crossings gap >= 3: {len(cross)}")
    for r in cross:
        print(f"  {r['title']} CFR {r['section']:<12} {r['wy']} -> "
              f"{r['newest_edition_year']}  gap {r['newest_edition_year']-r['wy']:>2}  "
              f"({r['level']} level)")
    print("oldest printed warrants:")
    for r in sorted(comb, key=lambda x: x["wy"])[:6]:
        print(f"  {r['title']} CFR {r['section']:<12} {r['wy']}  ({r['level']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
