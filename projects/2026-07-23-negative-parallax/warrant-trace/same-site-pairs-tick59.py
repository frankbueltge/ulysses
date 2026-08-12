#!/usr/bin/env python3
"""same-site-pairs-tick59 — how often this line's own diff counts one site twice.

Computed from landed artefacts only (`remeasure-tick58-removed.jsonl`,
`remeasure-tick58-added.jsonl`), so it can be checked without a corpus.

**The fault it measures is in the comparison layer, not in the sieve.** Two instrument
versions are diffed site by site through `remeasure-tick55.py match_key`, which identifies a
site by its value plus the last sixty characters of its window. That key was chosen at tick 50
for a good reason and its cost was named there: a repair that makes the SAME site match a
longer string would otherwise count it twice, once as lost and once as found, so the key was
anchored on the window's tail, which a widening gap does not move.

0.7 broke that assumption from the other side. Its repairs SHORTEN matches: a new stop cuts a
match off, and what remains is a shorter match that begins at a LATER occurrence of the
statistic's name. The window travels with the match, so its tail moves, so the key changes —
and the same threshold statement appears once in the removed file and once in the added file.

The tick-58 trace read one of those pairs as a fault of the sieve and named it N5's second
instance; it is not a fault of the sieve, and the site was never lost. This script asks how
many others there are, by looking for a paper, profile and value that appears on both sides of
the same diff. It reports the pairs rather than correcting anything: what was landed stays
landed, and the corrected reading is stated beside it in the trace.

The same check runs forward: `remeasure-tick59.py` classifies every site 0.8 adds against the
tick-58 removals under a strict key (same matched string) and a loose one (same paper, profile
and value), for exactly this reason.

Usage: python3 same-site-pairs-tick59.py
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def key(r):
    return (r["corpus"], r["profile"], r["arxiv"], str(r["value"]))


def main():
    removed, added = (load("remeasure-tick58-removed.jsonl"),
                      load("remeasure-tick58-added.jsonl"))
    rc, ac = collections.Counter(map(key, removed)), collections.Counter(map(key, added))
    pairs = rc & ac
    detail = []
    for k in sorted(pairs):
        r_match = next(r["match"] for r in removed if key(r) == k)
        a_match = next(r["match"] for r in added if key(r) == k)
        detail.append({"corpus": k[0], "profile": k[1], "arxiv": k[2], "value": k[3],
                       "count": pairs[k], "removed_match": r_match, "added_match": a_match,
                       "added_is_suffix_of_removed": a_match.strip() in r_match})
    out = {"tick": 59, "reads": "tick 58's landed diff",
           "removed_records": len(removed), "added_records": len(added),
           "same_site_pairs": sum(pairs.values()),
           "distinct_sites_affected": len(pairs),
           "corrected_removed": len(removed) - sum(pairs.values()),
           "corrected_added": len(added) - sum(pairs.values()),
           "pairs": detail}
    print(json.dumps(out, indent=1))
    with open(os.path.join(HERE, "same-site-pairs-tick59.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
