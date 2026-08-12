#!/usr/bin/env python3
"""numerator-sets-tick60-B — the same two sets, after D2 fired on the first attempt.

`numerator-sets-tick60.py` rebuilt the hand census's numerator as 43 where the landed
`rates-tick57.json` publishes 48, so defeat condition D2 of `../PREREGISTRATION-tick60.md`
fired and every forecast of that run is void. That file and its JSON stay landed unchanged;
this one is the repair, and the two faults it repairs are both in the line's own tables:

**F1 — the correction file updates `label` and leaves `invoker` stale.**
`correction-tick56-labels.csv` moves `2606.22439v1` from `X-OTHER` to `I-NAME` and
`2607.27585v1` from `X-SCORE` to `I-NAME`; its own `consequence` column says both papers
become invokers. Neither row's `invoker` column was rewritten, so a reader that trusts
`invoker` disagrees with a reader that trusts `label` about exactly these two papers. Every
landed rate reads `label`. This script does too, everywhere: **invoker status is derived from
the corrected label**, and the `invoker` column is read only to be checked against it.

**F2 — `site_state` is a column in tick 57's table and a prose prefix in tick 56's.**
`handtable-tick57.py` says the note "still carries tick 56's substrings so that one parser
reads both tables". It does — but only if the parser looks there, and the first one did not.
The 24 stratum-B rows of tick 56 carry `site_real=NO`, `site_real=yes, non-focus` or
`site_real=yes` at the head of `note`; here they are parsed out of it.

Neither fault changes any published number: they are faults in how the tables can be READ,
and they surface the first time something rebuilds a set instead of re-adding a count.

Usage: python3 numerator-sets-tick60-B.py
"""
import csv
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

NON_INVOKER = {"X-ENGLISH", "X-LOSS", "X-SCORE", "X-CITE", "X-QUERY", "X-NOTATION", "X-OTHER"}
B_SITE = "B-SITE"
INVENTED, NONFOCUS, REAL = "site_real=NO", "site_real=yes, non-focus", "site_real=yes"

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
}


def sha256(name):
    with open(os.path.join(HERE, name), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def rows(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def site_state(r):
    """F2: the column where tick 57 wrote it, the note prefix where tick 56 did."""
    if r.get("site_state"):
        return r["site_state"]
    note = r.get("note") or ""
    for state in (NONFOCUS, INVENTED, REAL):        # NONFOCUS first: it contains REAL
        if note.startswith(state):
            return state
    return None


def hand_tables():
    rec = {}
    for name in ("handread-tick56.csv", "handread-tick57.csv"):
        for r in rows(name):
            rec[r["arxiv"]] = dict(r, _table=name)
    stale = []
    for r in rows("correction-tick56-labels.csv"):
        a = r["arxiv"]
        if a in rec:
            was_inv = rec[a]["invoker"]
            rec[a]["label"] = r["corrected_label"]
            if (r["corrected_label"] not in NON_INVOKER) != (was_inv == "1"):
                stale.append({"arxiv": a, "invoker_column": was_inv,
                              "corrected_label": r["corrected_label"]})
    for a, r in rec.items():
        r["_invoker"] = r["label"] not in NON_INVOKER      # F1: label is the authority
        r["_site_state"] = site_state(r)
    return rec, stale


def main():
    bad_sha = {n: sha256(n) for n in EXPECTED_SHA if sha256(n) != EXPECTED_SHA[n]}
    hand, stale = hand_tables()
    measured = {r["arxiv"]: r for r in rows("remeasure-tick59-iou-0.5-0.8.csv")
                if r["state"] != "no_source"}
    at07 = {r["arxiv"]: r["sites"] for r in rows("remeasure-tick59-iou-0.5-0.7.csv")}

    invoking = [a for a, r in measured.items() if r["mentioned"] == "1"]
    candidates = {a for a in invoking if measured[a]["sites"] == "0"}

    I = {a for a in candidates if a in hand and hand[a]["_invoker"]}
    H_strict = {a for a, r in hand.items()
                if r["stratum"] == "A" and r["_invoker"] and r["label"] != B_SITE}
    H_returned = {a for a, r in hand.items()
                  if r["stratum"] == "B" and r["_invoker"]
                  and r["_site_state"] == INVENTED
                  and (r.get("states_threshold") or "no") == "no"}
    H = H_strict | H_returned

    only_I, only_H = sorted(I - H), sorted(H - I)
    unlabelled = sorted(a for a in (I | H) if a not in hand)
    unparsed_B = sorted(a for a, r in hand.items()
                        if r["stratum"] == "B" and r["_site_state"] is None)

    def detail(a):
        r, m = hand.get(a, {}), measured.get(a, {})
        return {"arxiv": a, "stratum": r.get("stratum"), "label": r.get("label"),
                "site_state": r.get("_site_state"),
                "states_threshold": r.get("states_threshold") or "no",
                "sites_at_0.7": at07.get(a), "sites_at_0.8": m.get("sites"),
                "note": (r.get("note") or "")[:200]}

    d_I = [detail(a) for a in only_I]
    d_H = [detail(a) for a in only_H]
    b_site = sorted(a for a, r in hand.items() if r["label"] == B_SITE)
    b_site_only_I = sorted(set(b_site) & set(only_I))
    kept_site = [d["arxiv"] for d in d_H
                 if d["site_state"] == INVENTED and d["sites_at_0.8"] not in ("0", None)]

    out = {
        "tick": 60, "run": "B (after D2)", "literature": "cv",
        "question": ("do the instrument's numerator (50) and the hand census's numerator (48) "
                     "name the same papers, or do their disagreements cancel?"),
        "repairs": {"F1_stale_invoker_column": stale,
                    "F2_site_state_in_prose": "tick 56 stratum-B rows parsed from note prefix"},
        "inputs_sha256_mismatch": bad_sha,
        "sizes": {"invoking": len(invoking), "candidates_at_0.8": len(candidates),
                  "I": len(I), "H": len(H), "H_strict": len(H_strict),
                  "H_returned": len(H_returned), "intersection": len(I & H),
                  "symmetric_difference": len(I ^ H),
                  "only_I": len(only_I), "only_H": len(only_H)},
        "rates_pct": {"I": round(100.0 * len(I) / 142, 1), "H": round(100.0 * len(H) / 142, 1)},
        "unlabelled_in_either_set": unlabelled,
        "stratum_B_rows_with_no_readable_site_state": unparsed_B,
        "only_I": d_I, "only_H": d_H,
        "b_site_papers": b_site, "b_site_papers_in_only_I": b_site_only_I,
        "invented_site_invokers_the_sieve_still_credits": kept_site,
        "withheld_paper_2607.05311v1_in_only_I": "2607.05311v1" in only_I,
    }
    s = out["sizes"]
    out["reconstruction_reproduces_landed"] = (s["I"] == 50 and s["H"] == 48)
    out["forecasts_VOID_scored_for_the_record_only"] = {
        "P1_reconstruction_I_50_H_48": out["reconstruction_reproduces_landed"],
        "P2_symdiff_ge_6": s["symmetric_difference"] >= 6,
        "P3_symdiff_le_12": s["symmetric_difference"] <= 12,
        "P4_only_I_in_4_7_and_gt_only_H": 4 <= s["only_I"] <= 7 and s["only_I"] > s["only_H"],
        "P5_exactly_4_b_site_in_only_I": len(b_site_only_I) == 4,
        "P6_repair_left_an_invented_site_invoker": len(kept_site) >= 1,
        "P7_withheld_paper_in_only_I": out["withheld_paper_2607.05311v1_in_only_I"],
    }
    print(json.dumps(out, indent=1))
    with open(os.path.join(HERE, "numerator-sets-tick60-B.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
