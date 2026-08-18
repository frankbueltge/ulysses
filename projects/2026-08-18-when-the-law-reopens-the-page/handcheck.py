#!/usr/bin/env python3
"""Step 5 — print the sections the pre-registration owes a hand-check on, with the
sentences the extraction rule read at each date, so a human (or the next session) can
verify them against the eCFR pages named.

Owed by PREREGISTRATION-01.md:
  · the ten largest edition moves
  · ten reopened sections that did NOT move — the first ten in sorted title/section order
  · every retreat, without exception

Prints the eCFR point-in-time URL for both dates beside each case.

Usage: python3 handcheck.py > data/handcheck.txt
"""

import json
import re
import sys

BASE = "projects/2026-08-18-when-the-law-reopens-the-page"
URL = ("https://www.ecfr.gov/api/versioner/v1/full/{d}/title-{t}.xml?section={s}")
SITE = "https://www.ecfr.gov/on/{d}/title-{t}/section-{s}"

sys.path.insert(0, BASE)
from parse_moves import RE_CITA, RE_DIV8, RE_EDNOTE, RE_P, edition_years, flatten  # noqa: E402


def year_context(path: str, year: int) -> list[str]:
    raw = open(path, encoding="utf-8", errors="replace").read()
    div = RE_DIV8.search(raw)
    body = div.group(0) if div else raw
    stripped = RE_EDNOTE.sub(" ", RE_CITA.sub(" ", body))
    hits = []
    for p in (flatten(x) for x in RE_P.findall(stripped)):
        if not p:
            continue
        for m in re.finditer(r"(?<!\d)%d(?!\d)" % year, p):
            if year in edition_years([p]):
                hits.append(p[max(0, m.start() - 120):m.start() + 60].strip())
    return hits[:2]


def show(r: dict, why: str) -> None:
    t, s = r["title"], r["section"]
    print(f"\n=== {why}: {t} CFR {s} "
          f"({r['before_edition']} -> {r['after_edition']}, delta {r['delta']}) ===")
    print(f"  amendments since 2017: {r['n_amendments_since_2017']} "
          f"({r['first_amendment']} … {r['last_amendment']})")
    print(f"  printed source-note year (2026-08-17 measurement): {r['printed_warrant_year']}")
    print(f"  before  {SITE.format(d='2017-01-01', t=t, s=s)}")
    print(f"  after   {SITE.format(d='2026-08-11', t=t, s=s)}")
    for which, ey in (("before", r["before_edition"]), ("after", r["after_edition"])):
        if ey is None:
            continue
        for c in year_context(f"{BASE}/data/xml/{which}/{t}-{s}.xml", ey):
            print(f"    [{which} {ey}] …{c}…")


def main() -> int:
    recs = json.load(open(f"{BASE}/data/moves.json"))["records"]
    arm = [r for r in recs if r["scorable_both_ends"]]

    moved = sorted([r for r in arm if r["moved"]], key=lambda r: -r["delta"])
    for r in moved[:10]:
        show(r, "LARGEST MOVE")

    flat = [r for r in arm if not r["moved"] and not r["retreat"]]
    flat = sorted(flat, key=lambda r: (r["title"], r["section"]))
    for r in flat[:10]:
        show(r, "REOPENED, DID NOT MOVE")

    retreats = [r for r in arm if r["retreat"]]
    for r in retreats:
        show(r, "RETREAT")
    print(f"\n(retreats in corpus: {len(retreats)}; reopened-and-flat: {len(flat)}; "
          f"moves: {len(moved)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
