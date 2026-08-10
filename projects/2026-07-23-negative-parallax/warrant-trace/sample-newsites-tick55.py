#!/usr/bin/env python3
"""sample-newsites-tick55 — the twenty sites of the repair that get read by hand.

A repair that produces more sites has to answer for them. Tick 50 widened the gap, drew
twenty of the sites the widening newly produced, read them, and found **9 of 20** were
threshold statements at all — which is how this line knows the size of what it bought. The
same operation is run here for 0.6, with the same sample size and the same question, so the
two repairs are comparable.

The draw is by seed 55, fixed in `../PREREGISTRATION-tick55.md` P7 before any window of this
tick was read, over the pooled population of every site 0.6 finds and 0.5 does not. The
script writes the windows out for reading and a CSV skeleton with an empty verdict column;
the verdicts are typed in by hand, one site at a time, and the file that lands carries them.

Usage: python3 sample-newsites-tick55.py --newsites remeasure-tick55-newsites.jsonl -n 20
"""
import argparse
import csv
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--newsites", default="remeasure-tick55-newsites.jsonl")
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=55)
    ap.add_argument("--out", default="sample-newsites-tick55")
    args = ap.parse_args()

    pop = [json.loads(l) for l in open(args.newsites, encoding="utf-8") if l.strip()]
    # one row per site; the population is pooled across corpora and profiles on purpose —
    # the question "did the repair buy sites or noise" is asked of the repair, not of a
    # literature, and a stratified draw would answer a different question.
    rnd = random.Random(args.seed)
    idx = list(range(len(pop)))
    rnd.shuffle(idx)
    drawn = [pop[i] for i in idx[:args.n]]

    with open(args.out + "-windows.txt", "w", encoding="utf-8") as fh:
        for n, s in enumerate(drawn, 1):
            fh.write(f"=== {n:02d}  {s['corpus']}/{s['profile']}  {s['arxiv']}  "
                     f"value={s['value']}  marker_in_match={s['marker_in_match']}  "
                     f"percent_in_window={s['percent_in_window']}\n")
            fh.write("MATCH: " + s["match"] + "\n")
            fh.write("WINDOW: " + s["window"] + "\n\n")

    with open(args.out + ".csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "corpus", "profile", "arxiv", "value", "marker_in_match",
                    "percent_in_window", "is_threshold_statement", "reading"])
        for n, s in enumerate(drawn, 1):
            w.writerow([n, s["corpus"], s["profile"], s["arxiv"], s["value"],
                        int(s["marker_in_match"]), int(s["percent_in_window"]), "", ""])
    print(f"population {len(pop)} new sites; drew {len(drawn)} with seed {args.seed}")
    print(f"wrote {args.out}-windows.txt and {args.out}.csv (verdict column empty)")


if __name__ == "__main__":
    main()
