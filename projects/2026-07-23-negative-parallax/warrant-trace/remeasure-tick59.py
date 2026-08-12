#!/usr/bin/env python3
"""remeasure-tick59 — the same three frames, read twice: by 0.7 and by the repaired 0.8.

The fourth time this line has run the operation, and the first time it runs against a repair
whose whole population is known in advance. 0.8 lifts two rejections that 0.7 itself
introduced — E8, the statistic's own subscript; E9, the row break before a comparison sign —
so everything 0.8 can find was found by 0.6 and taken by 0.7. That is P3 of
`../PREREGISTRATION-tick59.md`, and it is checked here against the landed
`remeasure-tick58-removed.jsonl` rather than assumed: **a site 0.8 adds that is not in that
file is an escape reaching further than its own description**, and it is reported as one.

Because the population is closed and small, the hand check is not a sample. Every added site
is written to `remeasure-tick59-added.jsonl` with its window, and every one of them is read.

Its skeleton — `verify_sha`, `rates`, `run_measure` — is `remeasure-tick50.py` and `match_key`
is `remeasure-tick55.py`, both loaded by path rather than copied, so the helper code that
produced the landed tables is the same object code that produces this one. The 0.7 side runs
from a `--ref` directory holding the instrument exactly as it was committed at tick 58; its
sha256 is recorded in the output, so the comparison names the object it compared against.

Usage:
    python3 remeasure-tick59.py --work <dir> --ref <dir holding 0.7> [--nocomments]
"""
import argparse
import csv
import hashlib
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
_t58 = _load("remeasure_tick58", "remeasure-tick58.py")
CORPORA, rates = _t50.CORPORA, _t50.rates
run_measure, verify_sha = _t50.run_measure, _t50.verify_sha
match_key = _t55.match_key
site_states = _t58.site_states

LANDED58 = os.path.join(HERE, "remeasure-tick58.json")
REMOVED58 = os.path.join(HERE, "remeasure-tick58-removed.jsonl")


def removed_at_58():
    """The 108 sites 0.7 took, keyed two ways — P3's population.

    Strict key is (corpus, profile, arxiv, value, the matched string with whitespace
    collapsed); loose key drops the matched string, because 0.8 can restore a site whose
    match is LONGER than the one 0.7 removed — E9 lets a match cross a row break, so the
    string grows leftwards from the same value. Both are reported: strict says "the same
    match came back", loose says "the same value in the same paper came back", and a site in
    neither is outside the closed population.
    """
    strict, loose = set(), set()
    with open(REMOVED58, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            base = (r["corpus"], r["profile"], r["arxiv"], str(r.get("value")))
            loose.add(base)
            strict.add(base + (" ".join((r.get("match") or "").split()),))
    return strict, loose


def by_paper(rows):
    return {r["arxiv"]: r for r in rows if r.get("state") != "no_source"}


def sha256_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--ref", required=True, help="directory holding the 0.7 reference")
    ap.add_argument("--out-prefix", default="remeasure-tick59")
    ap.add_argument("--nocomments", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated corpus keys")
    args = ap.parse_args()
    only = [k for k in args.only.split(",") if k]

    suffix = "-nocomments" if args.nocomments else ""
    states = site_states()
    strict58, loose58 = removed_at_58()
    landed58 = {(p["corpus"], p["profile"]): p.get("v0_7")
                for p in json.load(open(LANDED58, encoding="utf-8"))["profiles"]}
    out = {"tick": 59, "nocomments": bool(args.nocomments),
           "ref_sha256": sha256_of(os.path.join(args.ref, "warrant_trace.py")),
           "profiles": [], "sha": [], "reproduction": []}
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
            r7 = run_measure(os.path.join(args.ref, "warrant_trace.py"),
                             os.path.join(args.ref, "profiles"), pid, src, frame,
                             f"{args.out_prefix}{suffix}-{pid}-0.7", args.nocomments)
            r8 = run_measure(os.path.join(HERE, "warrant_trace.py"),
                             os.path.join(HERE, "profiles"), pid, src, frame,
                             f"{args.out_prefix}{suffix}-{pid}-0.8", args.nocomments)
            a, b = rates(r7["report"], r7["rows"]), rates(r8["report"], r8["rows"])

            # D11: today's 0.7 against the 0.7 tick 58 LANDED. A difference is not the
            # repair — it means the corpus moved under the instrument, and it voids the
            # frame by the pre-registration's own defeat condition.
            ref = landed58.get((key, pid)) or {}
            diffs = {k: [ref[k], a[k]] for k in ("frame", "measured", "no_source", "invoking",
                                                 "with_site", "sites", "candidates")
                     if k in ref and ref[k] != a[k]}
            out["reproduction"].append({"corpus": key, "profile": pid,
                                        "reproduces_landed_0_7": not diffs,
                                        "differences": diffs})

            p7, p8 = by_paper(r7["rows"]), by_paper(r8["rows"])
            cleared, gained, per_paper = [], [], []
            n_removed = n_added = 0
            in_strict = in_loose = outside = 0
            for aid, row7 in p7.items():
                row8 = p8.get(aid, {"sites": []})
                k7 = Counter(match_key(s) for s in row7["sites"])
                k8 = Counter(match_key(s) for s in row8["sites"])
                gone, new = k7 - k8, k8 - k7
                for s in row7["sites"]:
                    if gone.get(match_key(s)):
                        gone[match_key(s)] -= 1
                        n_removed += 1
                        removed.write(json.dumps({"corpus": key, "profile": pid,
                                                  "arxiv": aid, "value": s.get("value"),
                                                  "match": s.get("match"),
                                                  "window": s.get("window")}) + "\n")
                for s in row8["sites"]:
                    if new.get(match_key(s)):
                        new[match_key(s)] -= 1
                        n_added += 1
                        base = (key, pid, aid, str(s.get("value")))
                        m = " ".join((s.get("match") or "").split())
                        where = ("strict" if base + (m,) in strict58
                                 else "loose" if base in loose58 else "OUTSIDE")
                        in_strict += where == "strict"
                        in_loose += where == "loose"
                        outside += where == "OUTSIDE"
                        added.write(json.dumps({"corpus": key, "profile": pid, "arxiv": aid,
                                                "value": s.get("value"),
                                                "match": s.get("match"),
                                                "in_tick58_removed": where,
                                                "hand_state": states.get(aid),
                                                "window": s.get("window")}) + "\n")
                if row7["sites"] and not row8["sites"]:
                    cleared.append(aid)
                if not row7["sites"] and row8["sites"]:
                    gained.append(aid)
                if len(row7["sites"]) != len(row8["sites"]):
                    per_paper.append({"arxiv": aid, "sites_0_7": len(row7["sites"]),
                                      "sites_0_8": len(row8["sites"]),
                                      "hand_state": states.get(aid)})

            closed = (round(100.0 * (in_strict + in_loose) / n_added, 1) if n_added else None)
            out["profiles"].append({
                "corpus": key, "profile": pid, "v0_7": a, "v0_8": b,
                "sites_removed": n_removed, "sites_added": n_added,
                "added_in_tick58_removed_strict": in_strict,
                "added_in_tick58_removed_loose": in_loose,
                "added_outside_closed_population": outside,
                "closed_population_pct": closed,
                "papers_cleared": sorted(cleared), "papers_gained": sorted(gained),
                "papers_changed": per_paper})
            print(f"  {pid}: sites {a['sites']} -> {b['sites']} "
                  f"(+{n_added} -{n_removed}); candidates {a['candidates']} -> "
                  f"{b['candidates']}; rate {a['rate_of_invoking']} -> "
                  f"{b['rate_of_invoking']} %; cleared {len(cleared)}, gained {len(gained)}"
                  + (f"; inside closed population {closed} %" if closed is not None else ""))

    removed.close()
    added.close()
    with open(f"{args.out_prefix}{suffix}.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {args.out_prefix}{suffix}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
