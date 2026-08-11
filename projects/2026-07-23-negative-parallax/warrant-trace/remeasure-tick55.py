#!/usr/bin/env python3
"""remeasure-tick55 — the same three frames, read twice: by 0.5 and by the repaired 0.6.

The other half of tick 55's operation. Tick 50 set the rule and tick 51 paid for it: a
repair that is not re-measured in the same tick is an improvement that earned no finding,
and until the frames are read with it every rate this line has published carries an
unmeasured error in a known direction. So both instrument versions run over ONE freshly
fetched corpus, and every difference in the tables is the instrument and nothing else.

Its skeleton — `verify_sha`, `site_key`, `rates`, `focus_at` — is `remeasure-tick50.py`,
reused rather than rewritten, so that the two operations are comparable field by field. The
docstrings there explain why each is built the way it is; only the differences are commented
here. What is new at tick 55:

  * P8, the reproduction check. 0.5's re-run is compared field by field against the numbers
    tick 50 LANDED (`remeasure-tick50.json`). A difference is not a repair; it means the
    corpus moved under the instrument, and it is reported as that.
  * P3, the class-B check. Tick 53 read the whole candidate class of two literatures by hand
    and found 13 papers stating a threshold the sieve had missed. Those ids are read out of
    the landed census and each is asked directly: does 0.6 find a site in it now?
  * The named costs of E2 and E4 are counted, not estimated: how many newly found sites have
    a citation marker inside the matched string, and how many have an unescaped `%` in the
    window — the comment line the newline branch can now be traversed into.

Usage:
    python3 remeasure-tick55.py --work corpus/tick55 --ref corpus/tick55/ref-0.5
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

# The tick-50 script is loaded by path, not copied: its filename carries a hyphen and cannot
# be imported by name. Loading it means the helper code that produced the landed table is the
# same object code that produces this one — a copy could drift, and the whole point of the
# re-measure is that only the instrument differs.
_spec = importlib.util.spec_from_file_location(
    "remeasure_tick50", os.path.join(HERE, "remeasure-tick50.py"))
_t50 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_t50)
CORPORA, focus_at, rates = _t50.CORPORA, _t50.focus_at, _t50.rates
run_measure, site_key, verify_sha = _t50.run_measure, _t50.site_key, _t50.verify_sha

LANDED = os.path.join(HERE, "remeasure-tick50.json")
CENSUS = os.path.join(HERE, "handread-census-tick53.csv")


def match_key(s):
    """A site's identity across two instrument versions — the 0.6 replacement for `site_key`.

    Tick 50's `site_key` anchors on the window's last sixty characters, on the argument that
    "the number stands at the END of every site pattern, so the text after it does not move
    when the gap widens". That is true of a repair that widens a gap. It is false of a repair
    that MOVES TEXT — and E3 moves every footnote body to the end of the paper, so in any
    paper with footnotes the windows shift and the same site is counted once as lost and once
    as gained.

    It is not a small effect and it was not predicted: measured against this key, **113 of
    the 249 sites the tail key called new already existed under 0.5, with the same value and
    the same matched string**. Both keys are computed and both are reported; this one is the
    headline, because a site whose value and matched string are unchanged is the same site
    however its window moved.

    Its own weakness, stated: two genuinely distinct sites in one paper that carry the same
    value and the same matched string collapse into one, which undercounts a difference. That
    is the safer direction for a script whose job is to size a repair's effect.
    """
    return (str(s.get("value")), " ".join(s.get("match", "").split()))


def class_b_ids():
    """The 13 papers tick 53 hand-read as stating a threshold the sieve missed.

    Read out of the landed census rather than retyped, so the list cannot drift from the
    record it comes from. The five weaker calls (`B-SITE-WEAK` — a reference level rather
    than a rule) are returned apart and never folded into the headline, exactly as tick 53
    counted them.
    """
    strict, weak = [], []
    with open(CENSUS, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["label"] == "B-SITE":
                strict.append((row["literature"], row["arxiv"], row["stated_value"]))
            elif row["label"] == "B-SITE-WEAK":
                weak.append((row["literature"], row["arxiv"], row["stated_value"]))
    return strict, weak


def landed_0_5():
    """Tick 50's landed 0.5 table, keyed by corpus and profile."""
    with open(LANDED, encoding="utf-8") as fh:
        d = json.load(fh)
    return {(p["corpus"], p["profile"]): p["v0_5"] for p in d["profiles"]}


FIELDS = ("frame", "measured", "no_source", "invoking", "with_site", "sites",
          "candidates", "rate_of_invoking")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--ref", required=True, help="directory holding the 0.5 reference")
    ap.add_argument("--out-prefix", default="remeasure-tick55")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    only = [k for k in args.only.split(",") if k]

    strict, weak = class_b_ids()
    landed = landed_0_5()
    out = {"tick": 55, "profiles": [], "sha": [], "reproduction": [],
           "class_b": {"strict": [], "weak": []}}
    newsites_path = f"{args.out_prefix}-newsites.jsonl"
    newsites = open(newsites_path, "w", encoding="utf-8")
    rows_by = {}

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
            r5 = run_measure(os.path.join(args.ref, "warrant_trace.py"),
                             os.path.join(args.ref, "profiles"), pid, src, frame,
                             f"{args.out_prefix}-{pid}-0.5", False)
            r6 = run_measure(os.path.join(HERE, "warrant_trace.py"),
                             os.path.join(HERE, "profiles"), pid, src, frame,
                             f"{args.out_prefix}-{pid}-0.6", False)
            a, b = rates(r5["report"], r5["rows"]), rates(r6["report"], r6["rows"])
            rows_by[(key, pid)] = {r["arxiv"]: r for r in r6["rows"]}

            # P8: 0.5 today against 0.5 as landed at tick 50.
            ref = landed.get((key, pid), {})
            diff = {f: [ref.get(f), a[f]] for f in FIELDS if ref.get(f) != a[f]}
            out["reproduction"].append({"corpus": key, "profile": pid,
                                        "reproduces_landed_0_5": not diff,
                                        "differences": diff})

            rows5 = {r["arxiv"]: r for r in r5["rows"]}
            gained = lost = marker_in_match = pct_in_window = 0
            tail_gained = tail_lost = 0
            papers_gained, papers_lost = [], []
            for row6 in r6["rows"]:
                aid = row6["arxiv"]
                if row6.get("state") == "no_source":
                    continue
                row5 = rows5.get(aid, {})
                k5 = Counter(match_key(s) for s in row5.get("sites", []))
                k6 = Counter(match_key(s) for s in row6.get("sites", []))
                new, gone = k6 - k5, k5 - k6
                gained += sum(new.values())
                lost += sum(gone.values())
                # tick 50's key, kept beside it so the two are comparable and the size of its
                # window-shift artefact is on the record rather than in a sentence
                t5 = {site_key(s) for s in row5.get("sites", [])}
                t6 = {site_key(s) for s in row6.get("sites", [])}
                tail_gained += len(t6 - t5)
                tail_lost += len(t5 - t6)
                if new:
                    papers_gained.append(aid)
                if gone:
                    papers_lost.append(aid)
                for s in row6.get("sites", []):
                    if match_key(s) not in new:
                        continue
                    match = s.get("match", "")
                    win = s.get("window", "")
                    # the two named costs of §1, counted rather than estimated
                    has_marker = "<<CITE:" in match or "<<FN>>" in match
                    has_pct = any(ln.count("%") and "\\%" not in ln
                                  for ln in win.split("\n"))
                    marker_in_match += 1 if has_marker else 0
                    pct_in_window += 1 if has_pct else 0
                    newsites.write(json.dumps({
                        "corpus": key, "profile": pid, "arxiv": aid,
                        "value": s.get("value"), "match": match,
                        "cite_keys": s.get("cite_keys"), "target": s.get("target"),
                        "marker_in_match": has_marker, "percent_in_window": has_pct,
                        "window": " ".join(win.split())}) + "\n")

            entry = {"corpus": key, "profile": pid, "v0_5": a, "v0_6": b,
                     "sites_gained": gained, "sites_lost": lost,
                     "sites_gained_tick50_tail_key": tail_gained,
                     "sites_lost_tick50_tail_key": tail_lost,
                     "papers_gaining_a_site": len(papers_gained),
                     "papers_losing_a_site": len(papers_lost),
                     "new_sites_with_marker_in_match": marker_in_match,
                     "new_sites_with_percent_in_window": pct_in_window,
                     "mentions_delta": b["invoking"] - a["invoking"],
                     "rate_delta": (None if a["rate_of_invoking"] is None
                                    else round(b["rate_of_invoking"] - a["rate_of_invoking"], 1))}
            if pid == "ruwe-1.4":
                entry["focus_1_4_0_5"] = focus_at(r5["rows"], "1.4", "cite_tn")
                entry["focus_1_4_0_6"] = focus_at(r6["rows"], "1.4", "cite_tn")
                sub_f = os.path.join(HERE, "frame-tick48-ruwe14.txt")
                if os.path.exists(sub_f):
                    ids = {l.split("#")[0].strip().replace("/", "_")
                           for l in open(sub_f, encoding="utf-8") if l.split("#")[0].strip()}
                    entry["shipped_frame_0_5"] = focus_at(r5["rows"], "1.4", "cite_tn", ids)
                    entry["shipped_frame_0_6"] = focus_at(r6["rows"], "1.4", "cite_tn", ids)
                    entry["shipped_frame_n"] = len(ids)
                    entry["shipped_as_published"] = {"papers": 187, "sites_at_1_4": 397,
                                                     "sites_with_note": 4}
            out["profiles"].append(entry)
            print(f"  {pid:10s} sites {a['sites']:5d} -> {b['sites']:5d}   "
                  f"invoking {a['invoking']:4d} -> {b['invoking']:4d}   "
                  f"candidates {a['candidates']:4d} -> {b['candidates']:4d}   "
                  f"rate {a['rate_of_invoking']} -> {b['rate_of_invoking']} %"
                  f"   [0.5 reproduces tick 50: {'yes' if not diff else 'NO ' + str(diff)}]")

    # P3 — each hand-read class-B paper asked directly
    prof_for = {"gaia": "ruwe-1.4", "mcmc": "rhat-1.1"}
    for bucket, items in (("strict", strict), ("weak", weak)):
        for lit, aid, stated in items:
            pid = prof_for[lit]
            row = rows_by.get((lit, pid), {}).get(aid)
            if row is None:
                out["class_b"][bucket].append({"arxiv": aid, "literature": lit,
                                               "hand_read_value": stated,
                                               "found": None, "note": "not in this run"})
                continue
            vals = [s.get("value") for s in row.get("sites", [])]
            out["class_b"][bucket].append({
                "arxiv": aid, "literature": lit, "hand_read_value": stated,
                "found": bool(vals), "values_0_6": vals})
    for bucket in ("strict", "weak"):
        got = sum(1 for r in out["class_b"][bucket] if r.get("found"))
        out["class_b"][bucket + "_found"] = got
        print(f"\nclass B ({bucket}): 0.6 finds a site in {got} of "
              f"{len(out['class_b'][bucket])} hand-read papers")

    newsites.close()
    with open(f"{args.out_prefix}.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {args.out_prefix}.json and {newsites_path}")


if __name__ == "__main__":
    main()
