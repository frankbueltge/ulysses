#!/usr/bin/env python3
"""forecast-tick50 — the six forecasts of the pre-registration, scored against the census.

Reads only artefacts committed beside it: `remeasure-tick50.json` (both instrument versions
over one corpus), `corrected-tick47.json` (the 12-paper sample correction this tick was
partly built to test), `sample-newsites-tick50.csv` (the hand-reading of 20 new sites) and
`handread-check-tick50.json` (the 36 papers of tick 47 re-read by both versions).

One thing it computes that the pre-registration did not think to: **P3 as written compares
two different quantities**, and the comparison is therefore not a fair test of tick 47's
sample. Tick 47's corrected rate is `raw x A-share`, where the A-share removes BOTH the
papers whose threshold the sieve missed (class B) AND the papers where the term is not a
criterion at all (class C). Instrument 0.5 repairs B and does nothing about C. So the
repaired census rate estimates `raw x (A+C)/n`, which is a LARGER quantity, and P3 asked
whether a larger quantity lands inside an interval built for a smaller one. That is my
error in the pre-registration, not a property of the literatures. The matched comparison is
computed here beside the one that was written, and both are reported.

Usage: python3 forecast-tick50.py --out forecast-tick50.json
"""
import argparse
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE_OF = {"gaia": "ruwe-1.4", "mcmc": "rhat-1.1", "cv": "iou-0.5"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="forecast-tick50.json")
    args = ap.parse_args()

    rem = json.load(open(os.path.join(HERE, "remeasure-tick50.json"), encoding="utf-8"))
    t47 = json.load(open(os.path.join(HERE, "corrected-tick47.json"), encoding="utf-8"))
    hand = list(csv.DictReader(open(os.path.join(HERE, "sample-newsites-tick50.csv"),
                                    encoding="utf-8")))
    hcheck = json.load(open(os.path.join(HERE, "handread-check-tick50.json"),
                            encoding="utf-8"))
    by_prof = {e["profile"]: e for e in rem["profiles"]}
    t47_by = {L["key"]: L for L in t47["literatures"]}

    out = {"tick": 50, "instrument": "warrant-trace 0.5", "verdicts": {}, "detail": {}}

    # ---- P1: direction -------------------------------------------------------------
    p1 = {}
    for pid in ("ruwe-1.4", "uwe-1.25", "iou-0.5"):
        e = by_prof[pid]
        p1[pid] = {"sites_0_4": e["v0_4"]["sites"], "sites_0_5": e["v0_5"]["sites"],
                   "rose": e["v0_5"]["sites"] > e["v0_4"]["sites"]}
    r = by_prof["rhat-1.1"]
    p1["rhat-1.1"] = {"sites_0_4": r["v0_4"]["sites"], "sites_0_5": r["v0_5"]["sites"],
                      "sites_did_not_fall": r["v0_5"]["sites"] >= r["v0_4"]["sites"],
                      "mentions_0_4": r["v0_4"]["invoking"],
                      "mentions_0_5": r["v0_5"]["invoking"],
                      "mentions_fell": r["v0_5"]["invoking"] < r["v0_4"]["invoking"]}
    out["detail"]["P1"] = p1
    out["verdicts"]["P1"] = all(v.get("rose", True) and v.get("sites_did_not_fall", True)
                                and v.get("mentions_fell", True) for v in p1.values())

    # ---- P2: rates fall everywhere -------------------------------------------------
    p2 = {}
    for key, pid in PROFILE_OF.items():
        e = by_prof[pid]
        p2[key] = {"rate_0_4": e["v0_4"]["rate_of_invoking"],
                   "rate_0_5": e["v0_5"]["rate_of_invoking"],
                   "fell": e["v0_5"]["rate_of_invoking"] < e["v0_4"]["rate_of_invoking"]}
    out["detail"]["P2"] = p2
    out["verdicts"]["P2"] = all(v["fell"] for v in p2.values())

    # ---- P3: census inside tick 47's interval, as written AND as it should have been -
    p3 = {}
    for key, pid in PROFILE_OF.items():
        e, L = by_prof[pid], t47_by[key]
        census = e["v0_5"]["rate_of_invoking"]
        lo, hi = L["corrected_interval"]
        s = L["sample"]
        n = s["A"] + s["B"] + s["C"]
        matched = round(L["raw_rate"] * (s["A"] + s["C"]) / n, 1)
        p3[key] = {"census_rate_0_5": census,
                   "as_written_interval": [lo, hi], "as_written_inside": lo <= census <= hi,
                   "matched_prediction": matched,
                   "matched_gap": round(census - matched, 1),
                   "note": "matched = raw x (A+C)/n, the quantity 0.5 actually estimates"}
    out["detail"]["P3"] = p3
    out["verdicts"]["P3"] = all(v["as_written_inside"] for v in p3.values())

    # ---- P4: the ranking -----------------------------------------------------------
    order = sorted(PROFILE_OF, key=lambda k: by_prof[PROFILE_OF[k]]["v0_5"]["rate_of_invoking"])
    out["detail"]["P4"] = {"census_ranking_low_to_high": order,
                           "tick47_corrected_ranking": t47["corrected_ranking_low_to_high"],
                           "tick47_raw_ranking": t47["raw_ranking_low_to_high"],
                           "rates": {k: by_prof[PROFILE_OF[k]]["v0_5"]["rate_of_invoking"]
                                     for k in PROFILE_OF}}
    out["verdicts"]["P4"] = order == t47["corrected_ranking_low_to_high"]

    # ---- P5: the shipped headline --------------------------------------------------
    e = by_prof["ruwe-1.4"]
    pub = e["shipped_as_published"]
    p5 = {"as_published": pub,
          "shipped_frame_0_4_today": {k: e["shipped_frame_0_4"][k]
                                      for k in ("sites", "papers", "sites_with_flag")},
          "shipped_frame_0_5": {k: e["shipped_frame_0_5"][k]
                                for k in ("sites", "papers", "sites_with_flag")},
          "note_papers_0_4": e["shipped_frame_0_4"]["papers_with_flag"],
          "note_papers_0_5": e["shipped_frame_0_5"]["papers_with_flag"],
          "full_frame_0_4": {k: e["focus_1_4_0_4"][k]
                             for k in ("sites", "papers", "sites_with_flag")},
          "full_frame_0_5": {k: e["focus_1_4_0_5"][k]
                             for k in ("sites", "papers", "sites_with_flag")},
          "full_frame_note_papers_0_5": e["focus_1_4_0_5"]["papers_with_flag"]}
    p5["note_site_shift_on_shipped_frame"] = (e["shipped_frame_0_5"]["sites_with_flag"]
                                              - e["shipped_frame_0_4"]["sites_with_flag"])
    out["detail"]["P5"] = p5
    out["verdicts"]["P5"] = abs(p5["note_site_shift_on_shipped_frame"]) <= 2

    # ---- P6: precision of the new sites --------------------------------------------
    tally = {}
    for h in hand:
        tally[h["class"]] = tally.get(h["class"], 0) + 1
    genuine = tally.get("T", 0)
    out["detail"]["P6"] = {"n": len(hand), "classes": tally, "genuine": genuine,
                           "threshold": 14,
                           "class_key": {"T": "a genuine threshold statement",
                                         "R": "a reported value, not a criterion",
                                         "X": "the captured number is not this statistic"}}
    out["verdicts"]["P6"] = genuine >= 14

    # ---- the check that matters for the RATES, and was not forecast ----------------
    s = hcheck["summary"]
    out["detail"]["ground_truth_not_preregistered"] = {
        "class_B_papers": s["class_B_total"],
        "class_B_now_sited_by_0_5": s["class_B_found_by_0_5"],
        "class_A_papers": s["class_A_total"],
        "class_A_falsely_sited_by_0_5": s["class_A_falsely_sited_by_0_5"],
        "reading": "the sites the repair adds are unreliable (P6), but the papers it moves "
                   "OUT of the candidate set are not: in the 24 papers where a hand-reader "
                   "established the truth, 0.5 recovers 7 of 8 real thresholds and removes "
                   "no genuine closed question."}

    out["defeats"] = {"D1_any_frame_lost_sites": not out["verdicts"]["P1"],
                      "D2_census_outside_interval": not out["verdicts"]["P3"],
                      "D3_ranking_differs": not out["verdicts"]["P4"],
                      "D4_shipped_note_moved": not out["verdicts"]["P5"],
                      "D5_new_sites_below_70pct": not out["verdicts"]["P6"],
                      "D6_sha_mismatch": any(c["mismatched"] for c in rem["sha"])}

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    for k in sorted(out["verdicts"]):
        print(f"  {k}: {'HOLDS' if out['verdicts'][k] else 'DEFEATED'}")
    print("  defeats firing: " + (", ".join(k for k, v in out["defeats"].items() if v)
                                  or "none"))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
