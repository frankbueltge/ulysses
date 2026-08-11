#!/usr/bin/env python3
"""sample-removed-tick58 — the sites the repair takes away, drawn to be read by hand.

The mirror of `sample-newsites-tick55.py`, and it exists because 0.7 is the mirror repair.
Ticks 50 and 55 widened the sieve and had to answer for the sites they bought, so they drew
from the sites the repair NEWLY produced. 0.7 narrows it, and what it has to answer for is
the opposite: a removed site that was a real threshold statement is a threshold this line
has now stopped counting.

The draw is by seed 58, fixed in `../PREREGISTRATION-tick58.md` §2 before any removed window
was looked at, over the pooled population of every site 0.6 finds and 0.7 does not. Pooled
across corpora on purpose, for tick 55's reason: the question is asked of the repair, not of
a literature. The script writes the windows out for reading and a CSV skeleton with an empty
verdict column; the verdicts are typed in by hand, one site at a time, and the file that
lands carries them.

The computer vision frame has a second, stronger check that needs no sample at all — its
121 site-bearing papers were all hand-read at ticks 56 and 57, before this repair existed,
so `remeasure-tick58.py` looks every cleared paper up in that census. This sample is what
the other two literatures have instead, and it is also the only check that reaches a site
removed from a paper that keeps its other sites.

Usage: python3 sample-removed-tick58.py --removed remeasure-tick58-removed.jsonl -n 20
"""
import argparse
import csv
import json
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--removed", default="remeasure-tick58-removed.jsonl")
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=58)
    ap.add_argument("--out", default="sample-removed-tick58")
    args = ap.parse_args()

    pop = [json.loads(l) for l in open(args.removed, encoding="utf-8") if l.strip()]
    rnd = random.Random(args.seed)
    idx = list(range(len(pop)))
    rnd.shuffle(idx)
    drawn = [pop[i] for i in idx[:args.n]]

    with open(args.out + "-windows.txt", "w", encoding="utf-8") as fh:
        for n, s in enumerate(drawn, 1):
            fh.write(f"=== {n:02d}  {s['corpus']}/{s['profile']}  {s['arxiv']}  "
                     f"value={s['value']}  hand_state={s.get('hand_state')}\n")
            fh.write("MATCH: " + str(s["match"]) + "\n")
            fh.write("WINDOW: " + str(s["window"]) + "\n\n")

    with open(args.out + ".csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "corpus", "profile", "arxiv", "value", "hand_state",
                    "was_a_threshold_statement", "reading"])
        for n, s in enumerate(drawn, 1):
            w.writerow([n, s["corpus"], s["profile"], s["arxiv"], s["value"],
                        s.get("hand_state", ""), "", ""])
    from collections import Counter
    print(f"population {len(pop)} removed sites "
          f"({dict(Counter(s['corpus'] for s in pop))}); "
          f"drew {len(drawn)} with seed {args.seed}")
    print(f"wrote {args.out}-windows.txt and {args.out}.csv (verdict column empty)")


if __name__ == "__main__":
    main()
