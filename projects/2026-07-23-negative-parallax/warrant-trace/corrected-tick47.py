#!/usr/bin/env python3
"""corrected-tick47 — what the hand-reading does to the corpus rate, with its interval.

The corpus quantity of `closed-question-tick47.py` is an instrument reading of a class. This
script joins the hand-read classes onto it and reports the corrected rate as

    corrected = raw_rate * (A / n)

with a Wilson interval on the A-share, because a share read off twelve papers is not a
number one may write down bare. Class B (a threshold IS stated and the site patterns missed
it) is reported separately: it is not a caveat, it is the instrument's own error rate, and
the pre-registration makes it a defeat condition.

Usage: corrected-tick47.py --out corrected-tick47.json
"""
import argparse
import collections
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = {"gaia": "Gaia astrometry (RUWE/UWE)",
         "mcmc": "MCMC convergence (R-hat)",
         "cv": "computer-vision detection (IoU)"}


def wilson(k, n, z=1.96):
    """Wilson score interval — an interval that behaves at the edges, where n is 12."""
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (centre - half), 1), round(100 * (centre + half), 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--counts", default="closed-question-tick47.json")
    ap.add_argument("--handread", default="handread-tick47.csv")
    ap.add_argument("--out", default="corrected-tick47.json")
    args = ap.parse_args()

    counts = json.load(open(os.path.join(HERE, args.counts), encoding="utf-8"))
    raw = {lit["key"]: lit for lit in counts["literatures"]}
    read = list(csv.DictReader(open(os.path.join(HERE, args.handread), encoding="utf-8")))

    out = {"tick": 47, "sample_n_per_literature": 12, "literatures": []}
    for key in ("gaia", "mcmc", "cv"):
        rows = [r for r in read if r["literature"] == key]
        c = collections.Counter(r["class"] for r in rows)
        n = len(rows)
        a_share = c["A"] / n
        rec = {
            "key": key, "label": LABEL[key],
            "invoking": raw[key]["invoking"], "candidates": raw[key]["candidates"],
            "raw_rate": raw[key]["rate_of_invoking"],
            "sample": {"n": n, "A": c["A"], "B": c["B"], "C": c["C"],
                       "ambiguous": sum(1 for r in rows if r["ambiguous"])},
            "A_share_pct": round(100 * a_share, 1),
            "A_share_wilson95": wilson(c["A"], n),
            "B_share_pct": round(100 * c["B"] / n, 1),
            "C_share_pct": round(100 * c["C"] / n, 1),
            "corrected_rate": round(raw[key]["rate_of_invoking"] * a_share, 1),
            "corrected_interval": [round(raw[key]["rate_of_invoking"] * w / 100, 1)
                                   for w in wilson(c["A"], n)],
            "corrected_papers": round(raw[key]["candidates"] * a_share, 1),
        }
        out["literatures"].append(rec)
        print(f"{key:5s} raw {rec['raw_rate']:5.1f}%  A={c['A']:2d} B={c['B']:2d} C={c['C']:2d}"
              f"  -> corrected {rec['corrected_rate']:5.1f}% "
              f"[{rec['corrected_interval'][0]}, {rec['corrected_interval'][1]}]")

    raw_rank = [l["key"] for l in sorted(out["literatures"], key=lambda x: x["raw_rate"])]
    cor_rank = [l["key"] for l in sorted(out["literatures"], key=lambda x: x["corrected_rate"])]
    out["raw_ranking_low_to_high"] = raw_rank
    out["corrected_ranking_low_to_high"] = cor_rank
    out["ranking_preserved"] = raw_rank == cor_rank
    print(f"raw ranking       {' < '.join(raw_rank)}")
    print(f"corrected ranking {' < '.join(cor_rank)}")
    print(f"P4 (ranking preserved): {out['ranking_preserved']}")

    # the pre-registered conditions, evaluated by the script rather than by its author
    out["preregistered"] = {
        "P1_A_at_least_25pct_everywhere": all(l["A_share_pct"] >= 25 for l in out["literatures"]),
        "P2_cv_has_largest_C_share": max(out["literatures"], key=lambda l: l["C_share_pct"])["key"] == "cv",
        "P3_B_at_most_25pct_everywhere": all(l["B_share_pct"] <= 25 for l in out["literatures"]),
        "P4_ranking_preserved": out["ranking_preserved"],
        "D1_fires": any(l["A_share_pct"] < 25 for l in out["literatures"]),
        "D2_fires": any(l["B_share_pct"] > 25 for l in out["literatures"]),
        "D3_fires": max(out["literatures"], key=lambda l: l["C_share_pct"])["key"] != "cv",
        "D4_fires": not out["ranking_preserved"],
    }
    for k, v in out["preregistered"].items():
        print(f"  {k}: {v}")
    with open(os.path.join(HERE, args.out), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
