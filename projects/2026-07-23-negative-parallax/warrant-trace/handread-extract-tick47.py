#!/usr/bin/env python3
"""handread-extract-tick47 — put the sampled papers in front of a reader, not a regex.

For every paper in the tick-47 sample, this prints the context of every occurrence of the
profile's term, using the instrument's own normalisation and body extraction, so the reading
sees exactly the text the instrument saw. The point is class B of the pre-registration: a
threshold that IS stated somewhere and that the site patterns did not match — which the
measure table cannot show, because it only records what matched.

Occurrences are deduplicated by position (as `sites()` does) and capped per paper; the true
occurrence count is printed either way, so a cap never hides a page.

The extracted windows are written to a scratch directory and are NOT committed: they are
verbatim source text, and this repository lands derived tables, manifests and code.

Usage:
    handread-extract-tick47.py --sample sample-tick47.csv --src <scratch dir> --out <scratch dir>
"""
import argparse
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as wt                                     # noqa: E402

PROFILES = {"gaia": "profiles/ruwe-1.4.json",
            "mcmc": "profiles/rhat-1.1.json",
            "cv": "profiles/iou-0.5.json"}
NEAR = 300          # characters either side of an occurrence
CAP = 12            # occurrences printed per paper


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sample", default="sample-tick47.csv")
    ap.add_argument("--src", required=True, help="dir holding <lit>-src/ corpora")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(os.path.join(HERE, args.sample), encoding="utf-8")))
    for lit, prof_path in PROFILES.items():
        prof = wt.Profile.load(os.path.join(HERE, prof_path))
        ids = [r["arxiv"] for r in rows if r["literature"] == lit]
        out_path = os.path.join(args.out, f"extract-{lit}.txt")
        with open(out_path, "w", encoding="utf-8") as out:
            for aid in ids:
                path = os.path.join(args.src, f"{lit}-src", aid.replace("/", "_") + ".txt")
                if not os.path.exists(path):
                    out.write(f"\n===== {aid} :: NO SOURCE FILE =====\n")
                    continue
                raw = open(path, encoding="utf-8", errors="replace").read()
                text = wt.normalise(wt.body_of(raw))
                hits = list(prof.term_re.finditer(text))
                sites = wt.sites(text, prof)
                out.write(f"\n===== {aid} [{lit}] occurrences={len(hits)} "
                          f"instrument_sites={len(sites)} chars={len(text)} =====\n")
                seen, shown = set(), 0
                for m in hits:
                    key = m.start() // 200
                    if key in seen:
                        continue
                    seen.add(key)
                    shown += 1
                    if shown > CAP:
                        break
                    s = max(0, m.start() - NEAR)
                    e = min(len(text), m.end() + NEAR)
                    win = re.sub(r"\s+", " ", text[s:e])
                    out.write(f"--- [{shown}] @{m.start()} :: {win}\n")
                if shown > CAP:
                    out.write(f"--- (+{len(seen) - CAP} further deduplicated occurrences "
                              f"not printed)\n")
        print(f"{lit}: {len(ids)} papers -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
