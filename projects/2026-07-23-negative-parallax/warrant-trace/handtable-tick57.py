#!/usr/bin/env python3
"""handtable-tick57 — the reading, written as a table.

One row per paper of `frame-tick57.txt`, in read order. The `label` and `note` columns
are the reading; the `fragment` column is taken VERBATIM from the paper by re-running the
sieve's own `sites()` over the same corpus file, so no evidence string is retyped from a
window into a table by hand. Where a paper's decisive evidence is not at a site — a
metric NAME carrying the threshold, an absent site — the fragment is the site the sieve
DID match, and the note says what the reading rested on instead.

Column `site_state` is written explicitly here rather than buried in prose inside `note`,
which is how tick 56 had to record it. The three permitted values are the three strings
`PREREGISTRATION-tick57.md` §2 fixes, and `note` still carries tick 56's substrings so
that one parser reads both tables.

Column `states_threshold` is new and exists for one case the tick-56 rule does not cover.
That rule returns an invented-site paper to the numerator if the paper invokes the
criterion. But a paper can have an invented site AND state a real threshold the sieve
missed — `2607.05311v1` does exactly that ("IoU values range from 0 ... with a threshold
of 0.5 typically adopted for positive detection assignment"), and returning it to the
class *states no threshold at all* would be false of it. Only invented-site invokers with
`states_threshold=no` are returned.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as W                                          # noqa: E402

PROFILE = os.path.join(HERE, "profiles", "iou-0.5.json")
SRC = os.path.join(HERE, "corpus", "src")

YES, NONFOCUS, NO = "site_real=yes", "site_real=yes, non-focus", "site_real=NO"

# read_order: (label, site_state, site_index_for_fragment, note)
# site_index is 1-based into the sieve's own site list; 0 means "no site quoted".
R = {
 1: ("I-USE", YES, 1, "AP at IoU thresholds of 25/50/75 %; the sieve caught the 25 and the same match names 50"),
 2: ("I-USE", YES, 2, ""),
 3: ("I-USE", YES, 1, "mask recall at IoU > 0.5"),
 4: ("I-USE", YES, 1, ""),
 5: ("I-NAME", NONFOCUS, 1, "sites are an occlusion proxy at IoU>0.1; the criterion enters only as AP@0.5 in a name"),
 6: ("I-USE", YES, 1, "IoU > 0.5 throughout, as the matching criterion"),
 7: ("I-USE", YES, 2, "one site is `overlap of 200` pixels between crops and is invented; the 0.50 site is real"),
 8: ("I-USE", YES, 2, "one site is a reported mean IoU of 0.67 for another method"),
 9: ("X-SCORE", NO, 1, "three sites, all reported values; IoU is the quality number, no threshold role"),
 10: ("I-NAME", NO, 1, "`overlap of 50 frames` between clips. The paper NEVER writes IoU and reports AP_25/AP_50 tables: the criterion is wholly absorbed into the name. Corrected from a first reading of X-ENGLISH by the AP@50-name check"),
 11: ("X-SCORE", NO, 1, "sites are reported mIoU_ins percentages"),
 12: ("I-USE", YES, 1, ""),
 13: ("I-USE", YES, 1, "AP at IoU thresholds of 25 % and 50 %"),
 14: ("X-SCORE", NO, 1, "the site is a reported enclosing-box IoU of 0.89"),
 15: ("I-USE", YES, 1, ""),
 16: ("I-USE", YES, 2, "IoU>0.5 defines TP in the paper's own equation"),
 17: ("X-SCORE", NO, 4, "five sites: three reported mIoU values, two where the gap ran from the term into `\\frac 1 N \\sum_ i=1`"),
 18: ("I-USE", YES, 1, ""),
 19: ("I-USE", YES, 2, "table headers IoU=0.3/0.5/0.7 for 3D mAP"),
 20: ("I-USE", YES, 1, "boxes matched at class-agnostic IoU > 0.5"),
 21: ("I-USE", YES, 1, ""),
 22: ("I-USE", YES, 2, "Match_50 defined as IoU of at least 0.5; other sites are reported mean IoU values"),
 23: ("I-USE", YES, 1, ""),
 24: ("X-OTHER", NONFOCUS, 1, "the real site is an NMS threshold of 0.6; the paper's metric is mIoU. Second site is `mIoU is achieved at an input resolution of 640` and is invented"),
 25: ("I-USE", NONFOCUS, 1, "sites are NMS at 0.3 and tracking at 0.4; the paper DOES state `mAP at IoU 0.50` and the sieve missed it — an apposition with no relation token"),
 26: ("X-SCORE", NO, 1, "thirteen sites, all reported mIoU percentages"),
 27: ("I-USE", YES, 1, ""),
 28: ("I-USE", YES, 1, ""),
 29: ("I-USE", YES, 1, ""),
 30: ("X-OTHER", YES, 1, "a real threshold AT 0.5 in another role: masks overlapping a neighbour above 0.5 are discarded. The paper's metric is the Dice score"),
 31: ("I-USE", YES, 1, ""),
 32: ("I-USE", YES, 1, ""),
 33: ("I-USE", YES, 1, "AP@50 and AP@25; a second site is NMS at 0.5"),
 34: ("I-USE", YES, 1, ""),
 35: ("I-USE", YES, 1, ""),
 36: ("I-USE", YES, 1, ""),
 37: ("I-USE", YES, 1, ""),
 38: ("I-USE", YES, 2, "a coarse evidence criterion at 0.15 stands beside the mAP50 statement"),
 39: ("I-USE", YES, 1, ""),
 40: ("I-USE", YES, 1, ""),
 41: ("I-USE", YES, 3, "two of three sites are invented — a reported mIoU and a table header — and the third is real"),
 42: ("X-OTHER", NONFOCUS, 1, "an identity-association gate at IoU > 0.02, not the correctness criterion"),
 43: ("X-SCORE", NO, 1, "both sites are reported mIoU percentages"),
 44: ("I-USE", YES, 1, ""),
 45: ("X-SCORE", NO, 1, "THIRTY-ONE sites, every one of them a reported IoU value or a hyperparameter sweep. The only mAP50 in the file is inside `%`-commented table rows"),
 46: ("X-ENGLISH", NO, 1, "`overlap ratio to r=0.5` between panoramic viewpoints"),
 47: ("I-USE", YES, 1, "AP for car at IoU=0.5, pedestrian and cyclist at 0.25"),
 48: ("I-USE", YES, 1, ""),
 49: ("I-NAME", YES, 1, "the only site is NMS at 0.5, real; the correctness threshold is stated nowhere and the metric is each benchmark's `primary metric` mAP"),
 50: ("I-USE", YES, 1, ""),
 51: ("I-USE", YES, 1, ""),
 52: ("I-USE", YES, 3, "the paper's own criterion is at 0.1; the 0.50 site is a FUTURE-WORK sentence recommending mask AP at 0.50 and 0.75"),
 53: ("I-NAME", YES, 1, "greedy NMS at IoU 0.5, real; the competition metric is mAP and no correctness threshold is stated"),
 54: ("I-USE", YES, 2, ""),
 55: ("X-SCORE", NO, 1, "five sites, all reported occ-mIoU values and one gate hyperparameter"),
 56: ("X-SCORE", NO, 1, "both sites ran from the term into `\\sum_ i=1`; IoU is a mask-consistency score"),
 57: ("I-USE", YES, 1, ""),
 58: ("I-NAME", NO, 1, "both sites are pgfplots AXIS OPTIONS (`ylabel= mIoU (%) , xmode=log, log basis x=10`). The paper reports 82.7 mAP50 in live text: an invoker whose threshold is wholly in the name. Corrected from a first reading of X-SCORE by the AP@50-name check"),
 59: ("X-SCORE", NO, 1, "the site is a reported mIoU of 48.3"),
 60: ("I-USE", YES, 1, ""),
 61: ("I-USE", YES, 2, "one site ran into a summation index; the other states 0.50 to 0.95"),
 62: ("I-USE", YES, 2, "a metrics paper that computes AP@50 as a baseline against its own measure"),
 63: ("I-NAME", NONFOCUS, 1, "sites are box-stabilisation thresholds at 0.6/0.7; the reported metric is mAP_50 and the number is nowhere stated"),
 64: ("I-NAME", NONFOCUS, 1, "the site is the RPN assignment threshold 0.7/0.3; validation mAP is the metric and the correctness number is not stated"),
 65: ("I-USE", YES, 1, "AP@25 and AP@50; a second site filters candidates at 60 %"),
 66: ("I-USE", NONFOCUS, 1, "the criterion applied at 0.75 (AP^75); no site at 0.5"),
 67: ("I-USE", YES, 1, ""),
 68: ("X-ENGLISH", NO, 1, "projection overlap of hand bones; the number is a DSC value"),
 69: ("I-USE", YES, 1, ""),
 70: ("I-USE", YES, 2, "AP under point-wise IoU thresholds of 0.3 and 0.5"),
 71: ("X-ENGLISH", NO, 1, "overlap between feature clusters, and the number is an accuracy"),
 72: ("I-USE", YES, 2, "the first site is a flight overlap of 75 % and is invented"),
 73: ("I-NAME", YES, 1, "IoU < 0.5 filters pseudo-labels — a real threshold in another role. Reported metrics are COCO mAP and DOTA mAP with no correctness number stated"),
 74: ("I-USE", YES, 1, ""),
 75: ("I-DISC", NO, 1, "a survey. Both sites are invented — `IoU values range from 0` and a `\\sum` — AND the paper states the threshold in the same sentence the sieve broke: `with a threshold of 0.5 typically adopted for positive detection assignment`. states_threshold=yes: it does NOT return to the numerator"),
 76: ("I-USE", NONFOCUS, 1, "Recall@100 at a stricter IoU threshold of 75 %"),
 77: ("I-USE", YES, 3, "five of nine sites are reported mean IoU values; the COCO protocol sentence is real"),
 78: ("X-SCORE", NO, 1, "all four sites are table headers `mIoU ( \\uparrow ) & ... N =1`"),
 79: ("I-USE", YES, 1, ""),
 80: ("X-OTHER", NONFOCUS, 1, "cross-epoch association gates at 0.05/0.10/0.30; the reported metrics are accuracy, macro F1 and macro IoU"),
 81: ("I-USE", YES, 1, ""),
 82: ("I-USE", YES, 1, ""),
 83: ("X-SCORE", NO, 1, "the site is a reported mIoU (SS) of 50.9"),
 84: ("I-USE", YES, 1, ""),
 85: ("I-USE", YES, 1, "mAP at 0.5 IoU threshold; a second site is an `O2M NMS IoU threshold` whose value the gap read as 2"),
 86: ("I-DISC", YES, 1, "a survey: the metric table defines mAP at a fixed IoU=0.50 without applying it to data of its own"),
 87: ("I-USE", YES, 1, "`subscripts 50 and 75 denote IoU thresholds`"),
 88: ("I-NAME", YES, 2, "the real site is HBB-NMS at 0.50; the reported metric is mAP_0.50:0.95 and AP50, with the correctness number stated nowhere"),
 89: ("I-USE", YES, 1, ""),
 90: ("I-USE", YES, 1, ""),
 91: ("I-USE", YES, 2, ""),
 92: ("X-OTHER", YES, 1, "NMS at IoU > 0.5 — a real threshold at the focus value in another role; the paper's metrics are AJI and Dice"),
 93: ("I-NAME", NO, 1, "the gap ran from the term across a comma into `conf=0.5`: `IoU, we selected conf=0.5`. The paper's own metric is IoU@0.5, an absorbed name, and it states no threshold: states_threshold=no, so it RETURNS to the numerator"),
 94: ("X-ENGLISH", NO, 1, "front and side flight overlaps of 80 % and 75 %"),
 95: ("I-USE", YES, 1, ""),
 96: ("I-USE", YES, 1, ""),
 97: ("I-USE", YES, 1, "AP_25 and AP_50 at 25 % and 50 % IoU thresholds"),
}

NON_INVOKER = {"X-ENGLISH", "X-LOSS", "X-SCORE", "X-CITE", "X-QUERY", "X-NOTATION",
               "X-OTHER"}
# invented-site invokers that DO state a threshold elsewhere: they are not candidates.
STATES_THRESHOLD = {75}


def main():
    prof = W.Profile.load(PROFILE)
    ids = W.read_ids(os.path.join(HERE, "frame-tick57.txt"))
    out = []
    for pos, aid in enumerate(ids, 1):
        label, state, idx, note = R[pos]
        path = os.path.join(SRC, aid.replace("/", "_") + ".txt")
        text = W.normalise(W.body_of(open(path, encoding="utf-8",
                                          errors="replace").read(), False))
        S = W.sites(text, prof)
        frag = S[idx - 1]["match"] if idx and idx <= len(S) else ""
        full = state if not note else f"{state} - {note}"
        out.append({"stratum": "B", "read_order": pos, "arxiv": aid, "label": label,
                    "invoker": 0 if label in NON_INVOKER else 1,
                    "site_state": state,
                    "states_threshold": "yes" if pos in STATES_THRESHOLD else "no",
                    "sites": len(S), "fragment": frag, "note": full})
    path = os.path.join(HERE, "handread-tick57.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["stratum", "read_order", "arxiv", "label",
                                           "invoker", "site_state", "states_threshold",
                                           "sites", "fragment", "note"])
        w.writeheader()
        w.writerows(out)
    n = len(out)
    print(f"{n} rows -> handread-tick57.csv")
    print("non-invokers:", sum(1 for r in out if r["invoker"] == 0))
    for s in (YES, NONFOCUS, NO):
        print(f"  {s}: {sum(1 for r in out if r['site_state'] == s)}")
    ii = [r for r in out if r["site_state"] == NO and r["invoker"] == 1]
    print("invented AND invoker:", len(ii),
          "| of these, returned:", sum(1 for r in ii if r["states_threshold"] == "no"),
          "| I-NAME among them:", sum(1 for r in ii if r["label"] == "I-NAME"))


if __name__ == "__main__":
    main()
