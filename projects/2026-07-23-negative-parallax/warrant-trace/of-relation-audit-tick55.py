#!/usr/bin/env python3
"""of-relation-audit — how often the relation `of` reaches a number that is not a threshold.

N1, found by `selftest-0.6.py` while writing a control for a different repair, and older than
the repair it was written against: `of` has been in every profile's relation list since the
instrument was generalised at tick 34, so an ordinary English genitive — *the companion mass
**of** 1.4 solar masses* — produces a site with no comparison anywhere in the sentence. 0.5
does it too; nothing about 0.6 causes it.

This script does not repair it and does not judge it. It counts the shape in the corpus, in
both instrument versions, so that a defect found on an invented string is sized against real
papers before anything is said about it. Two numbers per profile:

  * sites whose matched string reaches its value through `of` (or `up to` / `at least` /
    `at most`, the other relations that are not comparisons in ordinary prose);
  * of those, how many have a word in the matched string that makes a threshold reading
    unlikely on its face — `mass`, `period`, `distance`, `order`, `factor`, `magnitude`.

The second number is a sieve inside a sieve and is reported as such: it is a shape count, not
a reading. The reading is the pre-registered hand sample of tick 55, which draws from the
sites the repair NEWLY produces and would catch an N1 instance if the draw hit one.

Usage: python3 of-relation-audit-tick55.py --prefix remeasure-tick55
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SOFT_REL = re.compile(r"(?:\bof|\bup\s+to|\bat\s+least|\bat\s+most)"
                      r"[\s&]*(?:\b(?:the|an?)\s+)?\d", re.I)
NOT_A_THRESHOLD = re.compile(r"\b(mass|masses|period|distance|order|factor|magnitude|"
                             r"radius|age|ratio|median|mean|value)\b", re.I)
PROFILES = ["ruwe-1.4", "uwe-1.25", "rhat-1.1", "iou-0.5"]


def audit(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        rep = json.load(fh)
    total = soft = flagged = 0
    examples = []
    for row in rep["rows"]:
        for s in row.get("sites", []):
            total += 1
            m = s.get("match", "")
            if SOFT_REL.search(m):
                soft += 1
                if NOT_A_THRESHOLD.search(m):
                    flagged += 1
                    if len(examples) < 12:
                        examples.append({"arxiv": row["arxiv"], "value": s.get("value"),
                                         "match": " ".join(m.split())})
    return {"sites": total, "reached_through_a_soft_relation": soft,
            "and_carrying_a_non_threshold_noun": flagged,
            "share_of_all_sites_pct": round(100.0 * soft / total, 1) if total else None,
            "examples": examples}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="remeasure-tick55")
    args = ap.parse_args()
    out = {"tick": 55, "fault": "N1 — `of` reaches a number through a genitive",
           "repaired": False, "profiles": []}
    for pid in PROFILES:
        row = {"profile": pid}
        for ver in ("0.5", "0.6"):
            row[ver] = audit(os.path.join(HERE, f"{args.prefix}-{pid}-{ver}.json"))
        out["profiles"].append(row)
        if row["0.6"]:
            print(f"{pid:10s} 0.5: {row['0.5']['reached_through_a_soft_relation']:4d} of "
                  f"{row['0.5']['sites']:5d} sites ({row['0.5']['share_of_all_sites_pct']} %)"
                  f"   0.6: {row['0.6']['reached_through_a_soft_relation']:4d} of "
                  f"{row['0.6']['sites']:5d} ({row['0.6']['share_of_all_sites_pct']} %)"
                  f"   with a non-threshold noun: "
                  f"{row['0.5']['and_carrying_a_non_threshold_noun']} -> "
                  f"{row['0.6']['and_carrying_a_non_threshold_noun']}")
    with open(os.path.join(HERE, "of-relation-audit-tick55.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote of-relation-audit-tick55.json — a shape count, not a reading")


if __name__ == "__main__":
    main()
