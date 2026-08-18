#!/usr/bin/env python3
"""Step 7 — description. Runs AFTER scoring and produces no clause and no verdict.

Everything here is descriptive statistics over data/moves.json, printed so the prose in
MEASUREMENT.md can be checked line by line. Nothing here was pre-registered and nothing
here is reported as held or failed.

Usage: python3 describe.py > data/describe.txt
"""

import json
import statistics
import sys

BASE = "projects/2026-08-18-when-the-law-reopens-the-page"
ARTEFACTS = {(46, "160.076-5"), (24, "3280.4")}


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def main() -> int:
    recs = json.load(open(f"{BASE}/data/moves.json"))["records"]
    key = lambda r: (r["title"], r["section"])  # noqa: E731

    reopened = [r for r in recs if r["reopened"]]
    untouched = [r for r in recs if not r["reopened"]]
    absent_2017 = [r for r in reopened if r.get("before_http") == "404"]
    had_before = [r for r in reopened if r.get("before_http") == "200"]
    arm = [r for r in reopened if r["scorable_both_ends"] and key(r) not in ARTEFACTS]
    moved = [r for r in arm if r["moved"]]
    flat = [r for r in arm if not r["moved"] and not r["retreat"]]

    print("== the corpus ==")
    print(f"sections: {len(recs)}")
    print(f"reopened (amended on or after 2017-01-02): {len(reopened)}")
    print(f"  of which did not exist on 2017-01-01 (HTTP 404 at the before date): {len(absent_2017)}")
    print(f"  of which had a 2017 text: {len(had_before)}")
    print(f"not reopened: {len(untouched)}")
    print(f"amendments recorded since 2017 across the corpus: "
          f"{sum(r['n_amendments_since_2017'] for r in recs)}")

    print("\n== the C3 arm (after hand-check) ==")
    print(f"scorable at both ends: {len(arm)}  (dropout from {len(had_before)} with a 2017 text: "
          f"{len(had_before) - len(arm)} — no extractable edition year at one end, or artefact)")
    print(f"moved: {len(moved)}   did not move: {len(flat)}   retreats: "
          f"{sum(1 for r in arm if r['retreat'])}")
    print(f"median years gained where it moved: {med([r['delta'] for r in moved])}")
    big = max(moved, key=lambda r: r["delta"])
    print(f"largest genuine move: {big['title']} CFR {big['section']} "
          f"{big['before_edition']} -> {big['after_edition']} ({big['delta']} years)")

    # An amendment dated after the `after` snapshot (2026-08-11) is not visible in the text
    # that snapshot holds and is not credited to it. 43 CFR 11.18 is the one case: it was
    # amended again on 2026-08-12, the day after the corpus was frozen.
    vers = {(v["title"], v["section"]): sorted(
        x["date"] for x in v.get("versions", []) if x.get("date", "") >= "2017-01-02")
        for v in json.load(open(f"{BASE}/data/versions.json"))["records"]}

    def last_in_window(r):
        return max([d for d in vers[key(r)] if d <= "2026-08-11"], default=None)

    print("\n== the sections the law reopened and left standing ==")
    print("(last amendment counted only up to the snapshot date, 2026-08-11)")
    flat_w = [r for r in flat if last_in_window(r)]
    for r in sorted(flat_w, key=last_in_window, reverse=True):
        lw = last_in_window(r)
        stale = int(lw[:4]) - r["after_edition"]
        print(f"  {r['title']:>2} CFR {r['section']:<12} last amended {lw}  "
              f"binds {r['after_edition']}  ({stale} years older than the amendment)")
    ages = [int(last_in_window(r)[:4]) - r["after_edition"] for r in flat_w]
    print(f"median distance between the amendment and the edition it left standing: {med(ages)} years")
    print(f"amended in 2025 or 2026 and still binding pre-2015 material: "
          f"{sum(1 for r in flat_w if last_in_window(r) >= '2025' and r['after_edition'] < 2015)}")

    print("\n== edition years, 2026-08-11 ==")
    print(f"median, whole corpus:        {med([r['after_edition'] for r in recs])}")
    print(f"median, reopened:            {med([r['after_edition'] for r in reopened])}")
    print(f"median, not reopened:        {med([r['after_edition'] for r in untouched])}")
    print(f"oldest, not reopened:        {min([r['after_edition'] for r in untouched if r['after_edition']])}")
    print(f"not reopened and binding pre-2000 material: "
          f"{sum(1 for r in untouched if r['after_edition'] and r['after_edition'] < 2000)}"
          f" of {sum(1 for r in untouched if r['after_edition'])}")

    print("\n== the sections that did not exist in 2017 ==")
    firsts = [r["first_amendment"][:4] for r in absent_2017]
    from collections import Counter
    print(f"first appearance by year: {sorted(Counter(firsts).items())}")
    print(f"median edition year they bind today: {med([r['after_edition'] for r in absent_2017])}")

    print("\n== the printed source note (2026-08-17) beside the amendment record (tonight) ==")
    both = [r for r in recs if r["printed_warrant_year"] and r["last_version_date"]]
    agree = [r for r in both if int(r["last_version_date"][:4]) == r["printed_warrant_year"]]
    print(f"sections where the year printed beneath the section equals the year of its "
          f"latest recorded version: {len(agree)}/{len(both)}")
    diffs = [int(r["last_version_date"][:4]) - r["printed_warrant_year"] for r in both]
    print(f"median difference (version record minus printed note): {med(diffs)} years")
    return 0


if __name__ == "__main__":
    sys.exit(main())
