#!/usr/bin/env python3
"""rates-tick52 — what the reading of the denominator does to the three rates.

The quantity the fourth case reports is *invokes the statistic and states no threshold*.
Its denominator has always been `mentioned` — one regex match anywhere in the body. This
tick hand-read 12 papers per literature and labelled each an invoker or not.

A non-invoker does not merely inflate the denominator. It almost always sits in the
NUMERATOR too, because a paper that never uses the criterion states no threshold for it.
So the correction removes papers from both, and the direction of the move is not obvious
in advance — which is why it is computed here rather than asserted.

    corrected_rate = (candidates - non_invoker_candidates) / (invoking - non_invokers)

Point estimates use the sample's own share; the interval is the Wilson 95 % interval on
that share, carried through the same arithmetic. Computer vision is a STRATIFIED sample
(the machine sieve of `denominator-tick52.py census` defines the strata), so its share is
the weighted one and its interval is the stratified normal interval, which at n = 6 per
stratum is wide enough to be reported as a warning rather than a measurement.

Usage:  rates-tick52.py --out rates-tick52.json
"""
import argparse
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# the 0.5 measure tables — the instrument the line currently quotes
TABLES = {"gaia": "remeasure-tick50-ruwe-1.4-0.5.csv",
          "mcmc": "remeasure-tick50-rhat-1.1-0.5.csv",
          "cv":   "remeasure-tick50-iou-0.5-0.5.csv"}

# the tables the samples were DRAWN from (pre-registration §4: the landed measure table)
DRAWN_FROM = {"gaia": "measure-ruwe-1.4-tick35.csv",
              "mcmc": "measure-rhat-1.1-tick36.csv",
              "cv":   "measure-iou-0.5-tick46.csv"}


def rows(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(HERE, "rates-tick52.json"))
    a = ap.parse_args()

    hand = rows("handread-denominator-tick52.csv")
    census = {r["arxiv"]: r["m_noninvoker"] == "True" for r in rows("census-tick52.csv")}
    out = {"tick": 52, "note": "denominators read, not assumed", "literatures": {}}

    for lit in ("gaia", "mcmc", "cv"):
        cur = {r["arxiv"]: r for r in rows(TABLES[lit])}
        drawn = {r["arxiv"]: r for r in rows(DRAWN_FROM[lit])}
        sample = [r for r in hand if r["literature"] == lit]

        # the frame as the 0.5 instrument sees it today
        measured = [r for r in cur.values() if r["state"] == "measured"]
        invoking = [r for r in measured if r["mentioned"] == "1"]
        candidates = [r for r in invoking if int(r["sites"] or 0) == 0]

        # the sample, and what each labelled paper does in the current table
        non = [r for r in sample if r["invoker"] == "0"]
        still = [r for r in sample if cur.get(r["arxiv"], {}).get("mentioned") == "1"]
        non_still = [r for r in non if cur.get(r["arxiv"], {}).get("mentioned") == "1"]
        non_cand = [r for r in non_still
                    if int(cur[r["arxiv"]]["sites"] or 0) == 0]

        rec = {
            "sample_n": len(sample),
            "drawn_from": DRAWN_FROM[lit],
            "current_table": TABLES[lit],
            "sample_noninvokers": len(non),
            "sample_dropped_by_0_5": len(sample) - len(still),
            "sample_noninvokers_still_counted": len(non_still),
            "of_those_in_the_numerator": len(non_cand),
            "invoking_now": len(invoking),
            "candidates_now": len(candidates),
            "rate_now_pct": round(100.0 * len(candidates) / len(invoking), 1) if invoking else None,
        }

        if lit == "cv":
            # stratified: weights from the census, shares from 6 + 6
            strata = {}
            for s in ("M-NONINVOKER", "M-INVOKER"):
                sub = [r for r in sample if r["stratum"] == s]
                k = sum(1 for r in sub if r["invoker"] == "0")
                W = sum(1 for a, v in census.items() if v == (s == "M-NONINVOKER"))
                strata[s] = {"n": len(sub), "noninvokers": k, "population": W}
            tot = sum(v["population"] for v in strata.values())
            f = sum(v["population"] / tot * (v["noninvokers"] / v["n"]) for v in strata.values())
            var = 0.0
            for v in strata.values():
                Wh = v["population"] / tot
                p = v["noninvokers"] / v["n"]
                fpc = 1 - v["n"] / v["population"] if v["population"] else 0
                var += Wh * Wh * p * (1 - p) / v["n"] * fpc
            se = math.sqrt(var)
            lo, hi = max(0.0, f - 1.96 * se), min(1.0, f + 1.96 * se)
            rec["strata"] = strata
            rec["share_estimator"] = "stratified"
            rec["se"] = round(se, 4)
        else:
            f = len(non_still) / len(still) if still else 0.0
            lo, hi = wilson(len(non_still), len(still))
            rec["share_estimator"] = "simple"

        rec["noninvoker_share_pct"] = round(100.0 * f, 1)
        rec["noninvoker_share_ci95_pct"] = [round(100.0 * lo, 1), round(100.0 * hi, 1)]

        # correction: a non-invoker leaves the denominator, and leaves the numerator too
        # in the proportion the sample measured
        share_in_num = (len(non_cand) / len(non_still)) if non_still else 1.0
        rec["share_of_noninvokers_in_numerator"] = round(share_in_num, 3)

        def corrected(fr):
            N = len(invoking) * (1 - fr)
            C = len(candidates) - len(invoking) * fr * share_in_num
            return (100.0 * C / N) if N > 0 else None

        rec["rate_corrected_pct"] = round(corrected(f), 1)
        rec["rate_corrected_ci95_pct"] = [round(corrected(hi), 1), round(corrected(lo), 1)]
        if rec["rate_corrected_pct"] is not None and rec["rate_corrected_pct"] < 0:
            rec["corrected_note"] = ("the estimated non-invoker count exceeds the whole "
                                     "candidate class: reported as exhaustion of the class, "
                                     "never as a negative rate")

        # THE DIRECT QUANTITY. The class at issue is the candidates, so ask the sampled
        # papers that ARE candidates today what they are. Small, and not extrapolated.
        cand_sample = [r for r in sample
                       if cur.get(r["arxiv"], {}).get("mentioned") == "1"
                       and int(cur[r["arxiv"]]["sites"] or 0) == 0]
        rec["candidates_in_sample"] = len(cand_sample)
        rec["candidates_in_sample_noninvoker"] = sum(1 for r in cand_sample
                                                     if r["invoker"] == "0")
        if lit == "cv":
            rec["candidates_in_sample_caveat"] = (
                "6 of these come from the oversampled M-NONINVOKER stratum; the raw "
                "fraction is biased upward and must not be quoted unweighted")
        out["literatures"][lit] = rec

    # the two unstratified literatures pooled: a direct, unweighted reading of the class
    k = sum(out["literatures"][l]["candidates_in_sample_noninvoker"] for l in ("gaia", "mcmc"))
    n = sum(out["literatures"][l]["candidates_in_sample"] for l in ("gaia", "mcmc"))
    lo, hi = wilson(k, n)
    out["pooled_unstratified_numerator"] = {
        "literatures": ["gaia", "mcmc"], "candidates_sampled": n, "non_invokers": k,
        "share_pct": round(100.0 * k / n, 1) if n else None,
        "ci95_pct": [round(100.0 * lo, 1), round(100.0 * hi, 1)],
        "note": "computer vision excluded: its draw is stratified and would bias this upward"}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    for lit, r in out["literatures"].items():
        print(f"{lit:5s} invoking={r['invoking_now']:4d} cand={r['candidates_now']:3d} "
              f"rate={r['rate_now_pct']:5.1f}%  non-invokers={r['noninvoker_share_pct']:5.1f}% "
              f"{r['noninvoker_share_ci95_pct']}  ->  corrected {r['rate_corrected_pct']:5.1f}% "
              f"{r['rate_corrected_ci95_pct']}")


if __name__ == "__main__":
    main()
