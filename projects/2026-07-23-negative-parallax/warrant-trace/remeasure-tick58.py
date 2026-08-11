#!/usr/bin/env python3
"""remeasure-tick58 — the same three frames, read twice: by 0.6 and by the repaired 0.7.

The other half of tick 58's operation, and the third time this line has run it: a repair
that is not re-measured in the same tick is an improvement that earned no finding. Both
instrument versions run over ONE freshly fetched corpus, so every difference in the tables
is the instrument and nothing else.

What is different this time is the direction. 0.5 and 0.6 repaired faults that made the
sieve miss sites, and their hand check drew a sample of the sites the repair NEWLY found.
0.7 removes sites, so the checks run the other way and there are two of them:

  * **The census is the judge.** All 121 site-bearing papers of the computer vision frame
    were hand-read at ticks 56 and 57, for a different question and before this repair
    existed. Every paper 0.7 clears is looked up in it. A cleared paper the census read as
    stating a real threshold is a FALSE CLEARING and is reported as one (P3); the share of
    cleared papers the census independently calls invented is the repair's precision (P2).
  * **A sample of the removed sites is hand-read**, drawn by seed 58 from every frame
    before any of them is looked at (`sample-removed-tick58.py`).

Its skeleton — `verify_sha`, `rates`, `focus_at`, `run_measure` — is `remeasure-tick50.py`
and `match_key` is `remeasure-tick55.py`, both loaded by path rather than copied, so that
the helper code that produced the landed tables is the same object code that produces this
one. Only what is new at tick 58 is commented here.

Usage:
    python3 remeasure-tick58.py --work <dir> --ref <dir holding 0.6> [--nocomments]
"""
import argparse
import csv
import importlib.util
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_t50 = _load("remeasure_tick50", "remeasure-tick50.py")
_t55 = _load("remeasure_tick55", "remeasure-tick55.py")
CORPORA, focus_at, rates = _t50.CORPORA, _t50.focus_at, _t50.rates
run_measure, verify_sha = _t50.run_measure, _t50.verify_sha
match_key = _t55.match_key

LANDED55 = os.path.join(HERE, "remeasure-tick55.json")
HAND56 = os.path.join(HERE, "handread-tick56.csv")
HAND57 = os.path.join(HERE, "handread-tick57.csv")
CENSUS53 = os.path.join(HERE, "handread-census-tick53.csv")


def site_states():
    """Every site-bearing computer vision paper, with the state its hand reading gave it.

    The classification rule is `cv-siteclass-tick57.py rates().site_state`, copied so that
    the two halves of the census — tick 57's own column and tick 56's free-text note — are
    read here by exactly the rule that produced the landed figures. Values: `invented`
    (no site is a threshold statement), `real_nonfocus`, `real_focus`.
    """
    out = {}
    for path in (HAND56, HAND57):
        with open(path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("site_state"):
                    state = {"site_real=NO": "invented",
                             "site_real=yes, non-focus": "real_nonfocus"}.get(
                                 r["site_state"], "real_focus")
                else:
                    n = r.get("note", "")
                    state = ("invented" if "site_real=NO" in n
                             else "real_nonfocus" if "non-focus" in n else "real_focus")
                out[r["arxiv"]] = state
    return out


def class_b_ids(literature):
    """The papers tick 53 hand-read as stating a threshold the sieve had missed.

    Read out of the landed census rather than retyped — the same call `remeasure-tick55.py`
    makes, returning `(literature, arxiv, stated_value)` and keeping the five weaker calls
    apart, exactly as tick 53 counted them. The reason it exists here is P8: a repair that
    removes sites can undo an earlier repair that found them, and this is the place that
    would show it.
    """
    strict, weak = _t55.class_b_ids()
    return ([x for x in strict if x[0] == literature],
            [x for x in weak if x[0] == literature])


def by_paper(rows):
    return {r["arxiv"]: r for r in rows if r.get("state") != "no_source"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--ref", required=True, help="directory holding the 0.6 reference")
    ap.add_argument("--out-prefix", default="remeasure-tick58")
    ap.add_argument("--nocomments", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated corpus keys")
    args = ap.parse_args()
    only = [k for k in args.only.split(",") if k]

    suffix = "-nocomments" if args.nocomments else ""
    states = site_states()
    landed55 = {(p["corpus"], p["profile"]): p.get("v0_6")
                for p in json.load(open(LANDED55, encoding="utf-8"))["profiles"]}
    out = {"tick": 58, "nocomments": bool(args.nocomments),
           "profiles": [], "sha": [], "reproduction": [], "class_b": []}
    removed = open(f"{args.out_prefix}{suffix}-removed.jsonl", "w", encoding="utf-8")
    added = open(f"{args.out_prefix}{suffix}-added.jsonl", "w", encoding="utf-8")

    for key, sub, prof_ids in CORPORA:
        if only and key not in only:
            continue
        src = os.path.join(args.work, sub, "src")
        frame = os.path.join(args.work, sub, "ids.txt")
        sha = verify_sha(args.work, key, sub)
        out["sha"].append(sha)
        print(f"\n=== {key}: {sha['identical']}/{sha['compared']} e-prints byte-identical "
              f"to the original manifest; {sha['mismatched']} differ")

        for pid in prof_ids:
            r6 = run_measure(os.path.join(args.ref, "warrant_trace.py"),
                             os.path.join(args.ref, "profiles"), pid, src, frame,
                             f"{args.out_prefix}{suffix}-{pid}-0.6", args.nocomments)
            r7 = run_measure(os.path.join(HERE, "warrant_trace.py"),
                             os.path.join(HERE, "profiles"), pid, src, frame,
                             f"{args.out_prefix}{suffix}-{pid}-0.7", args.nocomments)
            a, b = rates(r6["report"], r6["rows"]), rates(r7["report"], r7["rows"])

            # D11, the reproduction check: today's 0.6 against the 0.6 tick 55 LANDED. A
            # difference here is not a repair — it means the corpus moved under the
            # instrument, and it is reported as that rather than absorbed into the diff.
            ref = landed55.get((key, pid)) or {}
            diffs = {k: [ref[k], a[k]] for k in ("frame", "measured", "no_source", "invoking",
                                                 "with_site", "sites", "candidates")
                     if k in ref and ref[k] != a[k]}
            out["reproduction"].append({"corpus": key, "profile": pid,
                                        "reproduces_landed_0_6": not diffs,
                                        "differences": diffs})

            p6, p7 = by_paper(r6["rows"]), by_paper(r7["rows"])
            cleared, gained, per_paper = [], [], []
            n_removed = n_added = 0
            for aid, row6 in p6.items():
                row7 = p7.get(aid, {"sites": []})
                k6 = Counter(match_key(s) for s in row6["sites"])
                k7 = Counter(match_key(s) for s in row7["sites"])
                gone, new = k6 - k7, k7 - k6
                for s in row6["sites"]:
                    if gone.get(match_key(s)):
                        gone[match_key(s)] -= 1
                        n_removed += 1
                        removed.write(json.dumps({"corpus": key, "profile": pid,
                                                  "arxiv": aid, "value": s.get("value"),
                                                  "match": s.get("match"),
                                                  "window": s.get("window"),
                                                  "hand_state": states.get(aid)}) + "\n")
                for s in row7["sites"]:
                    if new.get(match_key(s)):
                        new[match_key(s)] -= 1
                        n_added += 1
                        added.write(json.dumps({"corpus": key, "profile": pid,
                                                "arxiv": aid, "value": s.get("value"),
                                                "match": s.get("match"),
                                                "window": s.get("window")}) + "\n")
                if row6["sites"] and not row7["sites"]:
                    cleared.append(aid)
                if not row6["sites"] and row7["sites"]:
                    gained.append(aid)
                if len(row6["sites"]) != len(row7["sites"]):
                    per_paper.append({"arxiv": aid, "sites_0_6": len(row6["sites"]),
                                      "sites_0_7": len(row7["sites"]),
                                      "hand_state": states.get(aid)})

            # P2 and P3, and they are one lookup: the census read all 121 site-bearing
            # papers of this frame before the repair existed, so the papers 0.7 clears
            # split into ones it was right about and ones it was wrong about, with no
            # judgement of mine in between.
            census = Counter(states.get(a) for a in cleared)
            judged = [a for a in cleared if states.get(a)]
            precision = (round(100.0 * census.get("invented", 0) / len(judged), 1)
                         if judged else None)

            strict, weak = class_b_ids(key)
            b_found = []
            for kind, group in (("strict", strict), ("weak", weak)):
                for _lit, aid, value in group:
                    if aid in p7:
                        b_found.append({"arxiv": aid, "kind": kind, "hand_value": value,
                                        "sites_0_6": len(p6[aid]["sites"]),
                                        "sites_0_7": len(p7[aid]["sites"])})
            if b_found:
                strict_rows = [x for x in b_found if x["kind"] == "strict"]
                out["class_b"].append({"corpus": key, "profile": pid, "papers": b_found,
                                       "strict_still_found": sum(1 for x in strict_rows
                                                                 if x["sites_0_7"]),
                                       "strict_of": len(strict_rows)})

            out["profiles"].append({
                "corpus": key, "profile": pid, "v0_6": a, "v0_7": b,
                "sites_removed": n_removed, "sites_added": n_added,
                "papers_cleared": sorted(cleared), "papers_gained": sorted(gained),
                "cleared_by_hand_state": dict(census),
                "cleared_judged_by_census": len(judged),
                "precision_against_census_pct": precision,
                "papers_changed": per_paper})
            print(f"  {pid}: sites {a['sites']} -> {b['sites']} "
                  f"(-{n_removed} +{n_added}); candidates {a['candidates']} -> "
                  f"{b['candidates']}; rate {a['rate_of_invoking']} -> "
                  f"{b['rate_of_invoking']} %; cleared {len(cleared)}, gained {len(gained)}"
                  + (f"; precision vs census {precision} %" if precision is not None else ""))

    removed.close()
    added.close()
    with open(f"{args.out_prefix}{suffix}.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {args.out_prefix}{suffix}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
