#!/usr/bin/env python3
"""numerator-sets-tick60 — the two numerators as SETS, not as counts.

`rates-tick59.py` reports that the instrument's corrected computer vision numerator is 50 and
the hand census's is 48 over the same denominator of 142: 35.2 % against 33.8 %, "two papers
apart". Two papers apart in COUNT. This script asks whether they are two papers apart in
MEMBERSHIP, which is the question the exposition needs and which no landed file answers.

Scores `../PREREGISTRATION-tick60.md`. Reads landed artefacts only — no corpus, no network —
and writes new files only; it never opens a landed file for writing (D4).

Set I: the instrument's numerator at profile 0.8, exactly as rates-tick59.py counts it.
Set H: the hand census's numerator, rebuilt from the reading tables by the rule recorded in
       rates-tick57.json (stratum-A invokers that are not B-SITE, plus stratum-B invented-site
       invokers that state no threshold).

Usage: python3 numerator-sets-tick60.py
"""
import csv
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

NON_INVOKER = {"X-ENGLISH", "X-LOSS", "X-SCORE", "X-CITE", "X-QUERY", "X-NOTATION", "X-OTHER"}

# sha256 of every input, fixed in §2 of the pre-registration before the forecast was written.
EXPECTED_SHA = {
    "handread-tick56.csv":
        "fd26ce5127ffa78e6ede090b1ee61024a387d4a670fac8e5371bd18bdcf661a1",
    "handread-tick57.csv":
        "1ea5bf3996a111398d47f2d280a2a22803fe949c7dc05835af1b9642a12fbc8e",
    "correction-tick56-labels.csv":
        "49597e341a22516a3f8b6f33268617a5776e085497b692a98ca6e9b224d784d4",
    "remeasure-tick59-iou-0.5-0.8.csv":
        "01d150b8dc7abd5d119287b2a964bc411d2235051127e4de58e90908cef09240",
    "remeasure-tick59-iou-0.5-0.7.csv":
        "e0e931b8896a3a49314e8b272395b349b2ed88aa4c63d30406c2c79b1dff3104",
    "rates-tick59.json":
        "c6197f225f2c63671d82ee219c6dafe9d154eae3a22fe694c1212eaf3d1d6bc1",
    "rates-tick57.json":
        "e8ba04606a884c19d84c2e16c417c5699dba8fb902f20edec1b3e68bdf25d370",
}

B_SITE = "B-SITE"
INVENTED = "site_real=NO"


def sha256(name):
    with open(os.path.join(HERE, name), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def rows(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def hand_tables():
    """Every read paper, with the tick-57 label corrections applied, keyed by arXiv id."""
    rec = {}
    for name in ("handread-tick56.csv", "handread-tick57.csv"):
        for r in rows(name):
            rec[r["arxiv"]] = dict(r, _table=name)
    for r in rows("correction-tick56-labels.csv"):
        if r["arxiv"] in rec:
            rec[r["arxiv"]]["label"] = r["corrected_label"]
    return rec


def main():
    bad_sha = {n: sha256(n) for n in EXPECTED_SHA if sha256(n) != EXPECTED_SHA[n]}

    hand = hand_tables()
    measured = {r["arxiv"]: r for r in rows("remeasure-tick59-iou-0.5-0.8.csv")
                if r["state"] != "no_source"}

    invoking = [a for a, r in measured.items() if r["mentioned"] == "1"]
    candidates = {a for a in invoking if measured[a]["sites"] == "0"}

    # Set I — the instrument's numerator at 0.8.
    I = {a for a in candidates
         if a in hand and hand[a]["label"] not in NON_INVOKER}

    # Set H — the hand census's numerator.
    H_strict = {a for a, r in hand.items()
                if r["stratum"] == "A" and r["invoker"] == "1" and r["label"] != B_SITE}
    H_returned = {a for a, r in hand.items()
                  if r["stratum"] == "B" and r["invoker"] == "1"
                  and r.get("site_state") == INVENTED and r.get("states_threshold") == "no"}
    H = H_strict | H_returned

    only_I = sorted(I - H)
    only_H = sorted(H - I)
    unlabelled = sorted(a for a in (I | H) if a not in hand)

    def why(a):
        """One line per disagreeing paper: what each side saw."""
        r = hand.get(a, {})
        m = measured.get(a, {})
        return {"arxiv": a, "stratum": r.get("stratum"), "label": r.get("label"),
                "invoker": r.get("invoker"), "site_state": r.get("site_state"),
                "states_threshold": r.get("states_threshold"),
                "sites_at_0.8": m.get("sites"), "sites_at_0.7": None,
                "note": (r.get("note") or "")[:180]}

    at07 = {r["arxiv"]: r["sites"] for r in rows("remeasure-tick59-iou-0.5-0.7.csv")}
    detail_I, detail_H = [], []
    for a in only_I:
        d = why(a)
        d["sites_at_0.7"] = at07.get(a)
        detail_I.append(d)
    for a in only_H:
        d = why(a)
        d["sites_at_0.7"] = at07.get(a)
        detail_H.append(d)

    b_site_ids = sorted(a for a, r in hand.items() if r["label"] == B_SITE)
    b_site_in_only_I = sorted(set(b_site_ids) & set(only_I))
    repair_kept_site = [d for d in detail_H
                        if d["site_state"] == INVENTED and d["sites_at_0.8"] not in ("0", None)]

    out = {
        "tick": 60,
        "literature": "cv",
        "question": ("do the instrument's numerator (50) and the hand census's numerator (48) "
                     "name the same papers, or do their disagreements cancel?"),
        "inputs_sha256_mismatch": bad_sha,
        "sizes": {"invoking": len(invoking), "candidates_at_0.8": len(candidates),
                  "I": len(I), "H": len(H), "H_strict": len(H_strict),
                  "H_returned": len(H_returned),
                  "intersection": len(I & H), "symmetric_difference": len(I ^ H),
                  "only_I": len(only_I), "only_H": len(only_H)},
        "unlabelled_in_either_set": unlabelled,
        "only_I": detail_I,
        "only_H": detail_H,
        "b_site_papers": b_site_ids,
        "b_site_papers_in_only_I": b_site_in_only_I,
        "invented_site_invokers_the_sieve_still_credits": [d["arxiv"] for d in repair_kept_site],
        "withheld_paper_2607.05311v1_in_only_I": "2607.05311v1" in only_I,
    }

    s = out["sizes"]
    out["forecasts"] = {
        "P1_reconstruction_I_50_H_48": s["I"] == 50 and s["H"] == 48,
        "P2_symdiff_ge_6": s["symmetric_difference"] >= 6,
        "P3_symdiff_le_12": s["symmetric_difference"] <= 12,
        "P4_only_I_in_4_7_and_gt_only_H":
            4 <= s["only_I"] <= 7 and s["only_I"] > s["only_H"],
        "P5_exactly_4_b_site_in_only_I": len(b_site_in_only_I) == 4,
        "P6_repair_left_an_invented_site_invoker": len(repair_kept_site) >= 1,
        "P7_withheld_paper_in_only_I": out["withheld_paper_2607.05311v1_in_only_I"],
    }
    out["defeats"] = {
        "D1_unlabelled_paper": bool(unlabelled),
        "D2_reconstruction_off": not out["forecasts"]["P1_reconstruction_I_50_H_48"],
        "D3_input_hash_changed": bool(bad_sha),
    }

    print(json.dumps(out, indent=1))
    with open(os.path.join(HERE, "numerator-sets-tick60.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
