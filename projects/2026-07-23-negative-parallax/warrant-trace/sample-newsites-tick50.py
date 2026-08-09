#!/usr/bin/env python3
"""sample-newsites-tick50 — draw the 20 new sites the pre-registration promised to read.

The repair of 0.5 widens a gap, loosens two boundaries and lengthens two relation lists.
Every one of those buys sites, and a sieve that buys sites cheaply has stopped understating
by starting to overstate. `../PREREGISTRATION-tick50.md` P6 forecasts that at least 14 of 20
sites the repair newly finds are genuine threshold statements, and D5 says what happens if
they are not: 0.5's rates become an upper bound rather than a correction.

The draw is uniform over the pooled population of new sites, with `random.Random(50)` — the
seed is the tick number, declared in the pre-registration before the population existed. It
is pooled rather than stratified because pooled is what was written; the per-corpus
composition of the draw is reported as it falls, and if a corpus goes unrepresented that is
stated rather than repaired after the fact.

Usage: python3 sample-newsites-tick50.py --in remeasure-tick50-newsites.jsonl \\
                                         --out sample-newsites-tick50.csv
"""
import argparse
import csv
import json
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="remeasure-tick50-newsites.jsonl")
    ap.add_argument("--out", default="sample-newsites-tick50.csv")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=50)
    args = ap.parse_args()

    pop = [json.loads(l) for l in open(args.inp, encoding="utf-8") if l.strip()]
    by_corpus = {}
    for r in pop:
        by_corpus[r["corpus"]] = by_corpus.get(r["corpus"], 0) + 1
    print(f"population: {len(pop)} new sites — "
          + ", ".join(f"{k} {v}" for k, v in sorted(by_corpus.items())))

    n = min(args.n, len(pop))
    draw = random.Random(args.seed).sample(pop, n)
    drawn = {}
    for r in draw:
        drawn[r["corpus"]] = drawn.get(r["corpus"], 0) + 1
    print(f"drawn: {n} — " + ", ".join(f"{k} {v}" for k, v in sorted(drawn.items())))
    for k in by_corpus:
        if k not in drawn:
            print(f"  NOT REPRESENTED in the draw: {k} — stated, not repaired")

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "corpus", "profile", "arxiv", "value", "target", "cite_keys",
                    "class", "evidence", "match"])
        for i, r in enumerate(draw, 1):
            w.writerow([i, r["corpus"], r["profile"], r["arxiv"], r["value"],
                        r.get("target", ""), (r.get("cite_keys") or "")[:80], "", "",
                        (r.get("match") or "")[:300]])
    with open(args.out.replace(".csv", "-windows.txt"), "w", encoding="utf-8") as fh:
        for i, r in enumerate(draw, 1):
            fh.write(f"### {i}  {r['corpus']} / {r['profile']} / {r['arxiv']}  "
                     f"value={r['value']}  target={r.get('target')}\n")
            fh.write(f"MATCH: {r.get('match')}\n")
            fh.write(f"CITES: {r.get('cite_keys')}\n")
            fh.write(f"WINDOW: {r.get('window')}\n\n")
    print(f"wrote {args.out} and its windows file — the `class` column is filled by hand: "
          f"T = a genuine threshold statement on this statistic, "
          f"R = a reported/observed value rather than a criterion, "
          f"X = not this statistic or not a number governing anything")


if __name__ == "__main__":
    main()
