#!/usr/bin/env python3
"""rates-tick58 — the corrected computer vision rate under 0.6 and under 0.7, side by side.

Computed from LANDED artefacts only, so the headline of tick 58 can be checked without
re-fetching a corpus: the two measure tables this tick landed
(`remeasure-tick58-iou-0.5-0.6.csv` and `-0.7.csv`), the two hand readings
(`handread-tick56.csv`, `handread-tick57.csv`) and the label corrections
(`correction-tick56-labels.csv`).

Why it can be one arithmetic and needs no interval: the censuses of ticks 56 and 57 read
BOTH strata whole, so **every one of the 205 invoking papers carries a hand label**. The
denominator is therefore the invoking papers minus the hand-counted non-invokers, and the
numerator is the candidates the instrument produces that the hand reading calls invokers.
Nothing here is estimated and nothing is extrapolated.

What the comparison is for. Under 0.6 the instrument's own class had to be corrected twice
by hand — once for the non-invokers at each end, once for the sites the sieve invented — to
reach 33.8 %. Under 0.7 the second correction is the instrument's own work, and the question
this script answers is how far the two land apart.

Usage: python3 rates-tick58.py
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NON_INVOKER = {"X-ENGLISH", "X-LOSS", "X-SCORE", "X-CITE", "X-QUERY", "X-NOTATION", "X-OTHER"}


def hand_labels():
    """Every invoking paper's label, with the tick-57 corrections applied on top."""
    lab = {}
    for name in ("handread-tick56.csv", "handread-tick57.csv"):
        with open(os.path.join(HERE, name), encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                lab[r["arxiv"]] = r["label"]
    with open(os.path.join(HERE, "correction-tick56-labels.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            lab[r["arxiv"]] = r["corrected_label"]
    return lab


def read(version):
    with open(os.path.join(HERE, f"remeasure-tick58-iou-0.5-{version}.csv"),
             encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r["state"] != "no_source"]


def main():
    lab = hand_labels()
    out = {"tick": 58, "literature": "cv",
           "design": "census of both strata (ticks 56, 57): every invoking paper carries a "
                     "hand label, so no quantity below is estimated",
           "hand_reference": {"rate_with_invented_sites_returned_pct": 33.8,
                              "numerator": 48, "denominator": 142,
                              "source": "rates-tick57.json"},
           "versions": {}}
    for version in ("0.6", "0.7"):
        rows = read(version)
        inv = [r["arxiv"] for r in rows if r["mentioned"] == "1"]
        cand = [r["arxiv"] for r in rows if r["mentioned"] == "1" and r["sites"] == "0"]
        unlabelled = [a for a in inv if a not in lab]
        non = [a for a in inv if lab.get(a) in NON_INVOKER]
        num = [a for a in cand if a in lab and lab[a] not in NON_INVOKER]
        den = len(inv) - len(non)
        out["versions"][version] = {
            "invoking": len(inv), "candidates": len(cand), "site_bearing": len(inv) - len(cand),
            "rate_as_measured_pct": round(100.0 * len(cand) / len(inv), 1),
            "hand_non_invokers": len(non), "unlabelled_invoking_papers": unlabelled,
            "corrected_numerator": len(num), "corrected_denominator": den,
            "corrected_rate_pct": round(100.0 * len(num) / den, 1)}
    a, b = out["versions"]["0.6"], out["versions"]["0.7"]
    out["distance_from_hand_reading_papers"] = b["corrected_numerator"] - 48
    print(json.dumps(out, indent=1))
    with open(os.path.join(HERE, "rates-tick58.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
