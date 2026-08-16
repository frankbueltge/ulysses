#!/usr/bin/env python3
"""Score the six pre-registered clauses of 2026-08-16-the-copy-of-last-resort.

Bands come from PREREGISTRATION-01.md and are hard-coded here unchanged.
Reads data/cdx.json; writes nothing. Every number in MEASUREMENT.md comes from this.
"""
import json
import os
import statistics
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = date(2026, 8, 16)          # the anchor fixed in the pre-registration


def age_days(ts):
    d = datetime.strptime(ts[:8], "%Y%m%d").date()
    return (TODAY - d).days


def med(xs):
    return statistics.median(xs) if xs else None


def main():
    data = json.load(open(os.path.join(HERE, "data", "cdx.json")))
    R = data["results"]
    errs = [r for r in R if r["query_error"]]
    err_rate = len(errs) / len(R)

    print(f"addresses {len(R)} · query errors {len(errs)} ({err_rate:.1%})")
    print(f"KILL CONDITION (>20% query failure): "
          f"{'FIRED — study unrun' if err_rate > 0.20 else 'not fired'}\n")
    if err_rate > 0.20:
        return

    arms = {k: [r for r in R if r["arm"] == k and not r["query_error"]] for k in "ABCD"}
    for k in "ABCD":
        print(f"arm {k}: n={len(arms[k])}")
    print()

    def has200(r):
        return r["last_200"] is not None

    def age200(r):
        return age_days(r["last_200"]["timestamp"])

    A, B, C = arms["A"], arms["B"], arms["C"]

    # C1 — a copy exists at all: arm A, >= 70 %
    s = sum(map(has200, A)) / len(A)
    print(f"C1  arm A with a 200 capture: {sum(map(has200,A))}/{len(A)} = {s:.1%} "
          f"(band >= 70%) -> {'HELD' if s >= 0.70 else 'FAILED'}")

    # C2 — the copy is stale: median age of last 200 in arm A > 365 d
    aA = [age200(r) for r in A if has200(r)]
    mA = med(aA)
    print(f"C2  arm A median age of most recent 200: {mA} d (n={len(aA)}, band > 365 d) "
          f"-> {'HELD' if mA is not None and mA > 365 else 'FAILED'}")

    # C3 — living control fresher: arm C median < 180 d AND < arm A median
    aC = [age200(r) for r in C if has200(r)]
    mC = med(aC)
    ok3 = mC is not None and mC < 180 and mA is not None and mC < mA
    print(f"C3  arm C median age: {mC} d (n={len(aC)}, band < 180 d and < arm A) "
          f"-> {'HELD' if ok3 else 'FAILED'}")

    # C4 — no copy anywhere: >= 3 arm-A addresses with no capture of any status
    none_at_all = [r for r in A if r["last_200"] is None and r["last_any"] is None]
    print(f"C4  arm A with no capture of any status: {len(none_at_all)} (band >= 3) "
          f"-> {'HELD' if len(none_at_all) >= 3 else 'FAILED'}")
    for r in none_at_all:
        print(f"      {r['census_outcome']:8s} {r['url']}  {r['sections']}")

    # C5 — blocked vs 4xx inside arm A: blocked median more recent by > 365 d
    bl = [age200(r) for r in A if r["census_outcome"] == "blocked" and has200(r)]
    fx = [age200(r) for r in A if r["census_outcome"] == "4xx" and has200(r)]
    mb, mf = med(bl), med(fx)
    void5 = len(bl) < 10 or len(fx) < 10
    gap = (mf - mb) if (mb is not None and mf is not None) else None
    print(f"C5  blocked median {mb} d (n={len(bl)}) vs 4xx median {mf} d (n={len(fx)}); "
          f"gap {gap} d (band > 365 d, blocked fresher) -> "
          f"{'VOID (arm < 10)' if void5 else ('HELD' if gap is not None and gap > 365 else 'FAILED')}")

    # C6 — front doors: arm B, >= 90 % with a 200 capture
    s6 = sum(map(has200, B)) / len(B)
    print(f"C6  arm B with a 200 capture: {sum(map(has200,B))}/{len(B)} = {s6:.1%} "
          f"(band >= 90%) -> {'HELD' if s6 >= 0.90 else 'FAILED'}")

    # Descriptives that are not clauses
    print("\n-- not pre-registered, reported as description --")
    for k in "ABCD":
        arm = arms[k]
        a = [age200(r) for r in arm if has200(r)]
        print(f"arm {k}: {sum(map(has200,arm))}/{len(arm)} have a 200 capture; "
              f"median age {med(a)} d; oldest {max(a) if a else None} d")
    print("\narm A, three-way split by census outcome:")
    for oc in ("4xx", "blocked", "network"):
        sub = [r for r in A if r["census_outcome"] == oc]
        a = [age200(r) for r in sub if has200(r)]
        print(f"  {oc:8s} n={len(sub)}  with-200={len(a)}  median age={med(a)}")
    print("\narm A, ten oldest most-recent-200 captures:")
    for r in sorted([r for r in A if has200(r)], key=age200, reverse=True)[:10]:
        print(f"  {age200(r):5d} d  {r['last_200']['timestamp'][:8]}  {r['census_outcome']:8s} "
              f"{r['url']}  {r['sections'][:2]}")


if __name__ == "__main__":
    main()
