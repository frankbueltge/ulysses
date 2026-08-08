#!/usr/bin/env python3
"""The second quantity of tick 46: a threshold that has become part of a name.

`warrant_trace.py` counts *threshold statements* — a statistic, a relation, a number.
Computer vision has a form the other three literatures of this line do not: the number
is absorbed into the identifier of the metric. `AP50`, `mAP@0.5`, `AP@[.5:.95]` state
no comparison and need no warrant; they are not sentences about a threshold, they are
the threshold wearing a name.

This counts those occurrences separately and never mixes them into the site count,
per PREREGISTRATION-tick46.md section 4. The number that matters is the last one it
prints: papers that carry a name-absorbed form and state the threshold nowhere.

    python3 name-absorbed-tick46.py --src <corpus> --frame frame-tick46.txt \\
                                    --profile profiles/iou-0.5.json --out name-absorbed-tick46

Writes <out>.csv (one row per frame member) and <out>.json (the summary).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warrant_trace import Profile, body_of, normalise, read_ids, sites  # noqa: E402

# Written after reading the corpus's own spellings, before any count was taken.
# Each pattern is a metric NAME carrying a number, not a statement about a threshold.
FORMS = {
    # AP50 / AP_{50} / AP^{50} / mAP50 / AP-50 — the VOC point of the COCO suite.
    # A connector (_ ^ - or nothing) is REQUIRED: `AP 50` with a bare space is far
    # more often a reported result than a metric name, and this counter must not
    # borrow from the other column. Checked against the corpus before the count:
    # every form present is `AP50`, `mAP50`, `AP_{50}`, `mAP_{50}` or `mAP-50`.
    "ap50": r"\bm?AP\s*(?:[_^]\s*\{?\s*|-)?50\s*\}?(?![0-9.])",
    # AP@0.5 / mAP@.5 / AP @ 0.50 / AP@IoU=0.5
    "ap_at_half": r"\bm?AP\s*@\s*(?:IoU\s*=\s*)?0?\.50?\b",
    # AP@[.5:.95] / AP@[0.5:0.05:0.95] / AP_{50:95} / AP 50-95 — the averaged band
    "ap_band": r"\bm?AP\s*[@_]?\s*[\[\{]?\s*0?\.5\s*[:\-]\s*(?:0?\.05\s*[:\-]\s*)?0?\.95\s*[\]\}]?"
               r"|\bm?AP\s*[_^]\s*\{?\s*50\s*[:\-]\s*95\s*\}?",
    # AP75 / AP@0.75 — the strict point, counted so that AP50 is not read alone
    "ap75": r"\bm?AP\s*(?:[_^]\s*\{?\s*|-)?75\s*\}?(?![0-9.])|\bm?AP\s*@\s*0?\.75\b",
}
FOCUS_FORMS = ("ap50", "ap_at_half")   # the ones that ARE the 0.5 threshold


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--frame", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--nocomments", action="store_true")
    args = ap.parse_args()

    prof = Profile.load(args.profile)
    res = {k: re.compile(v, re.I) for k, v in FORMS.items()}
    ids = [i.replace("/", "_") for i in read_ids(args.frame)]

    rows, summary = [], {k: 0 for k in FORMS}
    papers_with = {k: 0 for k in FORMS}
    no_source = []
    absorbed_only, absorbed_papers, stated_papers = [], [], []

    for aid in ids:
        path = os.path.join(args.src, aid + ".txt")
        if not os.path.exists(path):
            no_source.append(aid)
            rows.append({"arxiv": aid, "state": "no_source", "states_threshold": "",
                         "focus_absorbed": "", **{k: "" for k in FORMS}})
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = normalise(body_of(fh.read(), args.nocomments))
        counts = {k: len(r.findall(text)) for k, r in res.items()}
        for k, n in counts.items():
            summary[k] += n
            if n:
                papers_with[k] += 1
        # does the paper state the 0.5 threshold anywhere, in either unit?
        states = any(prof.is_focus(s["value"]) for s in sites(text, prof))
        focus_absorbed = sum(counts[k] for k in FOCUS_FORMS)
        if focus_absorbed:
            absorbed_papers.append(aid)
            if not states:
                absorbed_only.append(aid)
        if states:
            stated_papers.append(aid)
        rows.append({"arxiv": aid, "state": "measured",
                     "states_threshold": int(states),
                     "focus_absorbed": focus_absorbed, **counts})

    with open(args.out + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    measured = len(ids) - len(no_source)
    report = {
        "frame": len(ids), "papers": measured, "papers_no_source": len(no_source),
        "comments_stripped": bool(args.nocomments),
        "occurrences": summary, "papers_with_form": papers_with,
        "papers_naming_the_0_5_threshold": len(absorbed_papers),
        "papers_stating_the_0_5_threshold": len(stated_papers),
        "papers_naming_but_never_stating": len(absorbed_only),
        "naming_but_never_stating_ids": absorbed_only,
    }
    with open(args.out + ".json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)

    print(f"frame {len(ids)} papers; {len(no_source)} with no readable source "
          f"(excluded from every denominator)")
    print("\nname-absorbed forms — occurrences (papers):")
    for k in FORMS:
        print(f"  {k:12s} {summary[k]:5d}  ({papers_with[k]} papers)")
    print(f"\nthe 0.5 threshold as a NAME (AP50, AP@0.5): "
          f"{len(absorbed_papers)} of {measured} papers")
    print(f"the 0.5 threshold as a STATEMENT (IoU > 0.5, overlap of 50%): "
          f"{len(stated_papers)} of {measured} papers")
    print(f"papers that carry the name and never state the threshold: "
          f"{len(absorbed_only)} of {measured}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
