#!/usr/bin/env python3
"""Coda — not a clause, and not part of the pre-registered measurement.

While hand-checking, 43 CFR 11.18 — the sharpest case in the "reopened and left standing"
list — turned out to have been amended again on 2026-08-12, **the day after** the corpus
was frozen, replacing the 1996/1999 documentation with a 2018 publication. The corpus stays
frozen at 2026-08-11, as pre-registered. This file re-reads the 26 standing-still sections
at the latest issue date the API offers, so the record says which of tonight's statements
were already out of date when they were written.

Usage: python3 coda_check.py > data/coda.txt
"""

import json
import subprocess
import sys

BASE = "projects/2026-08-18-when-the-law-reopens-the-page"
ARTEFACTS = {(46, "160.076-5"), (24, "3280.4")}
UA = "Ulysses research (artistic research practice; contact via frankbueltge.de)"
LATEST = "2026-08-12"

sys.path.insert(0, BASE)
from parse_moves import RE_CITA, RE_DIV8, RE_EDNOTE, RE_P, edition_years, flatten  # noqa: E402


def newest_at(title, section, date):
    url = (f"https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title}.xml"
           f"?section={section}")
    out = subprocess.run(["curl", "-s", "--max-time", "120", "-A", UA, url],
                         capture_output=True, text=True)
    raw = out.stdout
    if not raw.strip().startswith("<?xml"):
        return None, "non-xml"
    div = RE_DIV8.search(raw)
    body = div.group(0) if div else raw
    stripped = RE_EDNOTE.sub(" ", RE_CITA.sub(" ", body))
    eys = edition_years([p for p in (flatten(x) for x in RE_P.findall(stripped)) if p])
    return (max(eys) if eys else None), "ok"


def main() -> int:
    recs = json.load(open(f"{BASE}/data/moves.json"))["records"]
    flat = [r for r in recs
            if r["scorable_both_ends"] and not r["moved"] and not r["retreat"]
            and (r["title"], r["section"]) not in ARTEFACTS]
    print(f"the 26 standing-still sections, re-read at {LATEST} "
          f"(corpus stays frozen at 2026-08-11)\n")
    changed = 0
    for r in sorted(flat, key=lambda r: (r["title"], r["section"])):
        ey, st = newest_at(r["title"], r["section"], LATEST)
        mark = ""
        if ey is not None and r["after_edition"] is not None and ey != r["after_edition"]:
            mark = "  <-- CHANGED"
            changed += 1
        print(f"  {r['title']:>2} CFR {r['section']:<12} 2026-08-11: {r['after_edition']}"
              f"   {LATEST}: {ey} [{st}]{mark}")
    print(f"\nchanged in the one day after the freeze: {changed} of {len(flat)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
