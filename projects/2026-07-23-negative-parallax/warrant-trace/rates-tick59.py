#!/usr/bin/env python3
"""rates-tick59 — the corrected computer vision rate under 0.7 and under 0.8, side by side.

`rates-tick58.py` with one thing changed: the two measure tables it reads are this tick's.
Everything else is deliberately identical — the same hand labels, the same non-invoker
vocabulary, the same arithmetic — so that a difference between the two files' outputs is the
instrument and not a change of method. That is why the code is repeated rather than imported
through a shared module: the two scripts must be readable side by side by someone checking
whether the rate moved for the reason claimed.

Computed from LANDED artefacts only: the two measure tables tick 59 lands
(`remeasure-tick59-iou-0.5-0.7.csv` and `-0.8.csv`), the two hand readings
(`handread-tick56.csv`, `handread-tick57.csv`) and the label corrections
(`correction-tick56-labels.csv`). No corpus is needed to check it.

The forecast this scores is P5 of `../PREREGISTRATION-tick59.md`: because 0.8 restores sites
only in papers that already carry others, no paper changes class and the corrected rate should
not move at all. A repair that changes no rate is still a finding — it says the fault it fixed
was invisible at the level this line publishes.

Usage: python3 rates-tick59.py
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
    with open(os.path.join(HERE, f"remeasure-tick59-iou-0.5-{version}.csv"),
             encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r["state"] != "no_source"]


def main():
    lab = hand_labels()
    out = {"tick": 59, "literature": "cv",
           "design": "census of both strata (ticks 56, 57): every invoking paper carries a "
                     "hand label, so no quantity below is estimated",
           "hand_reference": {"rate_with_invented_sites_returned_pct": 33.8,
                              "numerator": 48, "denominator": 142,
                              "source": "rates-tick57.json"},
           "landed_0_7_reference": {"corrected_rate_pct": 35.2, "source": "rates-tick58.json"},
           "versions": {}}
    for version in ("0.7", "0.8"):
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
    b = out["versions"]["0.8"]
    out["distance_from_hand_reading_papers"] = b["corrected_numerator"] - 48
    out["moved_from_landed_0_7"] = round(b["corrected_rate_pct"] - 35.2, 1)
    print(json.dumps(out, indent=1))
    with open(os.path.join(HERE, "rates-tick59.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
