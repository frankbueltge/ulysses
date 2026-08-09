#!/usr/bin/env python3
"""handread-check-tick50 — the repair against the hand-reading that found the faults.

NOT PRE-REGISTERED. `../PREREGISTRATION-tick50.md` forecasts six quantities and this is not
one of them; it was written after the pre-registration, while the corpus was still being
fetched, and it is reported as a supplementary check rather than as a forecast that
survived. Saying so is the whole reason the sentence is here.

What it does. Tick 47 hand-read 36 papers the sieve had filed as *invokes the statistic,
states no threshold*, and gave each a class with a verbatim quotation as evidence
(`handread-tick47.csv`):

    A — a genuine closed question: the statistic is used as a criterion and no threshold
        value for it appears anywhere in the text.
    B — the paper DOES state a threshold and the sieve missed it. These eight are the
        faults; they are what 0.5 was built to find.
    C — not a criterion: the term appears in some other sense.

That gives an independent test the invented strings of `selftest-0.5.py` cannot give, in
both directions at once:

    a repair that works  ->  the class-B papers now carry a site
    a repair that floods ->  the class-A papers now carry one too, and they should not,
                             because a hand-reader looked and found no threshold in them

The second direction is the one worth having. Class A is 16 papers of ground truth on which
the correct answer is *no site*, established by reading rather than by the instrument whose
error is in question.

Usage: python3 handread-check-tick50.py --work <dir> --ref <0.4 dir> \\
                                        --out handread-check-tick50.json
"""
import argparse
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = {"gaia": ("gaia", "ruwe-1.4"), "mcmc": ("mcmc", "rhat-1.1"),
          "cv": ("cv", "iou-0.5")}


def sites_for(script, profiles_dir, prof_id, src, ids, tmp):
    frame = tmp + ".ids"
    with open(frame, "w", encoding="utf-8") as fh:
        fh.write("\n".join(ids) + "\n")
    cmd = [sys.executable, script, "measure",
           "--profile", os.path.join(profiles_dir, prof_id + ".json"),
           "--src", src, "--frame", frame, "--out", tmp]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit("measure failed")
    with open(tmp + ".json", encoding="utf-8") as fh:
        rows = json.load(fh)["rows"]
    return {r["arxiv"]: r for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--handread", default=os.path.join(HERE, "handread-tick47.csv"))
    ap.add_argument("--out", default="handread-check-tick50.json")
    args = ap.parse_args()

    hand = list(csv.DictReader(open(args.handread, encoding="utf-8")))
    out = {"tick": 50, "preregistered": False,
           "source": os.path.basename(args.handread), "literatures": [], "papers": []}

    for lit, (sub, pid) in CORPUS.items():
        rows = [h for h in hand if h["literature"] == lit]
        if not rows:
            continue
        ids = [h["arxiv"] for h in rows]
        src = os.path.join(args.work, sub, "src")
        tmp = os.path.join(args.work, f"handcheck-{lit}")
        m4 = sites_for(os.path.join(args.ref, "warrant_trace.py"),
                       os.path.join(args.ref, "profiles"), pid, src, ids, tmp + "-04")
        m5 = sites_for(os.path.join(HERE, "warrant_trace.py"),
                       os.path.join(HERE, "profiles"), pid, src, ids, tmp + "-05")
        tally = {}
        for h in rows:
            aid = h["arxiv"].replace("/", "_")
            r4, r5 = m4.get(aid, {}), m5.get(aid, {})
            n4 = len(r4.get("sites", [])) if r4.get("state") != "no_source" else None
            n5 = len(r5.get("sites", [])) if r5.get("state") != "no_source" else None
            cls = h["class"]
            t = tally.setdefault(cls, {"n": 0, "sites_0_4": 0, "sites_0_5": 0,
                                       "no_source": 0})
            t["n"] += 1
            if n4 is None or n5 is None:
                t["no_source"] += 1
            else:
                t["sites_0_4"] += bool(n4)
                t["sites_0_5"] += bool(n5)
            out["papers"].append({"literature": lit, "arxiv": h["arxiv"], "class": cls,
                                  "fault": h.get("fault", ""), "sites_0_4": n4,
                                  "sites_0_5": n5,
                                  "evidence": h.get("evidence", "")[:200]})
        out["literatures"].append({"literature": lit, "profile": pid, "by_class": tally})
        print(f"\n{lit} ({pid})")
        for cls in sorted(tally):
            t = tally[cls]
            print(f"  class {cls}: {t['n']:2d} papers — "
                  f"0.4 found a site in {t['sites_0_4']}, 0.5 in {t['sites_0_5']}"
                  + (f", {t['no_source']} unreadable" if t["no_source"] else ""))

    b = [p for p in out["papers"] if p["class"] == "B"]
    a = [p for p in out["papers"] if p["class"] == "A"]
    out["summary"] = {
        "class_B_total": len(b),
        "class_B_found_by_0_5": sum(1 for p in b if p["sites_0_5"]),
        "class_B_found_by_0_4": sum(1 for p in b if p["sites_0_4"]),
        "class_A_total": len(a),
        "class_A_falsely_sited_by_0_5": sum(1 for p in a if p["sites_0_5"]),
        "class_A_falsely_sited_by_0_4": sum(1 for p in a if p["sites_0_4"]),
    }
    s = out["summary"]
    print(f"\nthe eight faults: 0.5 finds a site in {s['class_B_found_by_0_5']} of "
          f"{s['class_B_total']} papers a hand-reader says state a threshold "
          f"(0.4 found {s['class_B_found_by_0_4']})")
    print(f"the cost: 0.5 finds a site in {s['class_A_falsely_sited_by_0_5']} of "
          f"{s['class_A_total']} papers a hand-reader says state none "
          f"(0.4 found {s['class_A_falsely_sited_by_0_4']}) — every one of these is a "
          f"site the repair invented and must be read")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
