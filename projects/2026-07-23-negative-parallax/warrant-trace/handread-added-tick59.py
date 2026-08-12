#!/usr/bin/env python3
"""handread-added-tick59 — every site the repair gives back, written out to be read by hand.

The mirror of `sample-removed-tick58.py`, with the sampling removed. 0.7 took sites away and
had to answer for a drawn sample of them, because 108 sites is more than a tick can read.
0.8 gives sites back, and the population it can reach is closed by construction — it lifts two
rejections 0.7 itself introduced, so everything it finds was found by 0.6 and taken by 0.7
(P3 of `../PREREGISTRATION-tick59.md`). A closed population of this size is read whole, and a
reading with no draw in it has no seed, no sampling error and nothing an outcome could steer.

That is also why this file has no `--seed` argument and why the pre-registration claims no
blinding: there is no selection step here to be blind about. The verdict column is empty when
this script writes it and is typed in one site at a time from the windows file beside it.

Usage: python3 handread-added-tick59.py --added remeasure-tick59-added.jsonl
"""
import argparse
import csv
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--added", default="remeasure-tick59-added.jsonl")
    ap.add_argument("--out", default="handread-added-tick59")
    args = ap.parse_args()

    pop = [json.loads(line) for line in open(args.added, encoding="utf-8") if line.strip()]
    with open(args.out + "-windows.txt", "w", encoding="utf-8") as fh:
        for i, r in enumerate(pop, 1):
            fh.write(f"=== {i:02d}  {r['corpus']}/{r['profile']}  {r['arxiv']}  "
                     f"value={r['value']}  in_tick58_removed={r['in_tick58_removed']}  "
                     f"hand_state={r.get('hand_state')}\n")
            fh.write(f"MATCH: {r['match']}\n")
            fh.write(f"WINDOW: {r['window']}\n\n")
    with open(args.out + ".csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "corpus", "profile", "arxiv", "value", "in_tick58_removed",
                    "hand_state", "is_a_threshold_statement", "about_the_statistic", "reading"])
        for i, r in enumerate(pop, 1):
            w.writerow([i, r["corpus"], r["profile"], r["arxiv"], r["value"],
                        r["in_tick58_removed"], r.get("hand_state"), "", "", ""])
    print(f"{len(pop)} added sites written to {args.out}-windows.txt and {args.out}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
