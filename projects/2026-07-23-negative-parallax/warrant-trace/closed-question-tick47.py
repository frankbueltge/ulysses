#!/usr/bin/env python3
"""closed-question-tick47 — the fourth failure mode, read across three literatures.

Tick 46 found, in computer vision, a mode the first three readings could not produce: the
threshold is absorbed into the metric's NAME, so no site exists at which a citation for the
number could stand. This script asks the same question of every literature this line has
read, using one uniform quantity that needs no re-measurement and no network:

    invokes  = the profile's term appears in the body        (measure table: mentioned == 1)
    states   = at least one site term-relation-number        (measure table: sites   >= 1)
    candidate= invokes and not states

Denominators are papers the instrument actually READ (state == "measured"); `no_source` rows
are excluded, as in every tick since 0.2's silent-zero repair.

Two facts are asserted here rather than left for a reader to trip over:

 1. `ruwe-1.4` and `uwe-1.25` are ONE literature for this quantity. The uwe profile's term
    matches RUWE as well as UWE, so both profiles see the same invoking papers. The script
    checks that identity and refuses to report them as two if it holds.
 2. The candidate count is a CANDIDATE count. It is an instrument reading of a class, not the
    class. `sample` draws the hand-reading that decides how much of it is real.

Usage:
    closed-question-tick47.py count  --out closed-question-tick47
    closed-question-tick47.py sample --n 12 --seed 47 --out sample-tick47.csv
"""
import argparse
import csv
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# literature -> (label, measure table, the tick that built the frame, its fetch manifest)
LITERATURES = [
    ("gaia", "Gaia astrometry — RUWE / UWE, the astrometric quality cut",
     "measure-ruwe-1.4-tick35.csv", 35, "fetch-manifest-tick35.jsonl"),
    ("mcmc", "MCMC convergence — R-hat / PSRF / Gelman-Rubin",
     "measure-rhat-1.1-tick36.csv", 36, "fetch-manifest-tick36.jsonl"),
    ("cv", "Computer-vision detection — IoU, the correctness criterion",
     "measure-iou-0.5-tick46.csv", 46, "fetch-manifest-tick46.jsonl"),
]

# read for the identity check of note 1, never reported as a literature of its own
GAIA_SECOND = "measure-uwe-1.25-tick35.csv"


def rows(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def classify(table):
    measured = [r for r in table if r["state"] == "measured"]
    invoking = [r for r in measured if r["mentioned"] == "1"]
    candidates = [r for r in invoking if int(r["sites"] or 0) == 0]
    return measured, invoking, candidates


def count(args):
    out = {"tick": 47, "quantity": "invokes and states no threshold",
           "denominator": "papers with state == measured", "literatures": []}
    for key, label, table_name, tick, manifest in LITERATURES:
        measured, invoking, candidates = classify(rows(table_name))
        rec = {
            "key": key, "label": label, "table": table_name, "frame_tick": tick,
            "manifest": manifest,
            "papers_in_table": len(rows(table_name)),
            "measured": len(measured),
            "no_source": len(rows(table_name)) - len(measured),
            "invoking": len(invoking),
            "candidates": len(candidates),
            "rate_of_invoking": round(100.0 * len(candidates) / len(invoking), 1) if invoking else None,
            "rate_of_measured": round(100.0 * len(candidates) / len(measured), 1) if measured else None,
        }
        out["literatures"].append(rec)
        print(f"{key:5s} measured={rec['measured']:4d} invoking={rec['invoking']:4d} "
              f"candidates={rec['candidates']:4d}  {rec['rate_of_invoking']}% of invoking")

    # note 1, asserted: the two Gaia profiles see the same invoking set.
    a = {r["arxiv"] for r in classify(rows("measure-ruwe-1.4-tick35.csv"))[1]}
    b = {r["arxiv"] for r in classify(rows(GAIA_SECOND))[1]}
    out["gaia_profiles_share_invoking_set"] = (a == b)
    out["gaia_invoking_symmetric_difference"] = len(a ^ b)
    print(f"gaia: ruwe/uwe profiles share the invoking set: {a == b} "
          f"(symmetric difference {len(a ^ b)})")

    with open(os.path.join(HERE, args.out + ".json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    with open(os.path.join(HERE, args.out + ".csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["literature", "arxiv", "invokes", "sites", "candidate"])
        for key, _, table_name, _, _ in LITERATURES:
            measured, _, _ = classify(rows(table_name))
            for r in measured:
                inv = r["mentioned"] == "1"
                s = int(r["sites"] or 0)
                w.writerow([key, r["arxiv"], int(inv), s, int(inv and s == 0)])
    return 0


def sample(args):
    """Deterministic draw, seed declared in PREREGISTRATION-tick47.md before drawing."""
    with open(os.path.join(HERE, args.out), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["literature", "arxiv", "draw_index", "frame_tick", "manifest"])
        for key, _, table_name, tick, manifest in LITERATURES:
            _, _, candidates = classify(rows(table_name))
            ids = sorted(r["arxiv"] for r in candidates)
            rng = random.Random(args.seed)
            drawn = rng.sample(ids, min(args.n, len(ids)))
            for i, aid in enumerate(drawn, 1):
                w.writerow([key, aid, i, tick, manifest])
            print(f"{key}: drew {len(drawn)} of {len(ids)} candidates", file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("count")
    c.add_argument("--out", default="closed-question-tick47")
    c.set_defaults(fn=count)
    s = sub.add_parser("sample")
    s.add_argument("--n", type=int, default=12)
    s.add_argument("--seed", type=int, default=47)
    s.add_argument("--out", default="sample-tick47.csv")
    s.set_defaults(fn=sample)
    args = ap.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == "__main__":
    main()
