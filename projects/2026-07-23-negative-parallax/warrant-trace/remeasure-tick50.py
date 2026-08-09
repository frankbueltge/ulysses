#!/usr/bin/env python3
"""remeasure-tick50 — the same three frames, read twice: by 0.4 and by the repaired 0.5.

The repair of tick 50 fixes seven faults that a hand-reading pinned to verbatim fragments.
Six of them understate sites, which is the direction that flatters this line's claim. A
repair without a re-measure would be an improvement that earned no finding, so this script
is the other half of the operation: it runs BOTH instrument versions over ONE freshly
fetched corpus, so that every difference in the tables is the instrument and nothing else.

Why both versions over the fresh corpus, rather than 0.5 against the landed 0.4 tables:
the landed tables were computed over corpora that no longer exist on disk (this instrument
redistributes no source text). Re-fetching reproduces them only if arXiv still serves the
same bytes — which `--verify-sha` checks paper by paper against the original manifests, and
which is a finding either way. Running 0.4 again here means the diff cannot smuggle in a
corpus difference, an arXiv difference or a Python difference.

What it writes, per frame and profile:
    remeasure-tick50-<key>-0.4.csv/.json     0.4 over today's corpus
    remeasure-tick50-<key>-0.5.csv/.json     0.5 over today's corpus
    remeasure-tick50-compare.json            the diff, the rates, and the new-site census
    remeasure-tick50-newsites.jsonl          every site 0.5 finds and 0.4 did not, with its
                                             window — the population the hand-reading draws
                                             its sample of 20 from (pre-registration P6)

Usage:
    python3 remeasure-tick50.py --work <dir> --out-prefix remeasure-tick50 [--nocomments]

`--work` holds one subdirectory per corpus, each with ids.txt, src/ and sha-baseline.json.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# corpus key -> (subdirectory, [profile ids]).  The two Gaia profiles share one corpus and
# one invoking set (tick 47 §0.1); they are two readings of one literature, never two.
CORPORA = [
    ("gaia", "gaia", ["ruwe-1.4", "uwe-1.25"]),
    ("mcmc", "mcmc", ["rhat-1.1"]),
    ("cv",   "cv",   ["iou-0.5"]),
]


def verify_sha(work, key, sub):
    """Every re-fetched e-print against the sha256 the original manifest recorded.

    D6 of the pre-registration: a mismatch means the frame is not byte-stable and that
    every earlier count over that paper counted a different text. It is reported, never
    smoothed.
    """
    base = json.load(open(os.path.join(work, sub, "sha-baseline.json"), encoding="utf-8"))
    now = {}
    man = os.path.join(work, sub, "fetch-manifest.jsonl")
    # A retry manifest is read if one is present, and it is kept as a SEPARATE file on
    # purpose. The fetcher reads its skip-set once at start, so a FAILED record can never
    # be retried into the same manifest (README, "How it errs"); appending the retry to
    # the main manifest would also break the one arithmetic check that catches a
    # double-launched fetch — records must equal frame ids. So the retry is declared
    # rather than merged, and what it retried is named in the trace.
    retry = os.path.join(work, sub, "fetch-manifest-retry.jsonl")
    for path in (man, retry):
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("sha256"):
                now[r["arxiv"]] = r["sha256"]
    common = sorted(set(base) & set(now))
    mismatch = [a for a in common if base[a] != now[a]]
    return {"corpus": key, "baseline_ids": len(base), "refetched_ids": len(now),
            "compared": len(common), "identical": len(common) - len(mismatch),
            "mismatched": len(mismatch), "mismatched_ids": mismatch,
            "manifest_records": sum(1 for l in open(man, encoding="utf-8") if l.strip()),
            "not_refetched": sorted(set(base) - set(now))}


def run_measure(script, profiles_dir, prof_id, src, frame, out, nocomments):
    cmd = [sys.executable, script, "measure",
           "--profile", os.path.join(profiles_dir, prof_id + ".json"),
           "--src", src, "--frame", frame, "--out", out]
    if nocomments:
        cmd.append("--nocomments")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit(f"measure failed for {prof_id} with {script}")
    with open(out + ".json", encoding="utf-8") as fh:
        return json.load(fh)


def site_key(s):
    """A site's identity across two instrument versions.

    Anchored on the window's TAIL, and that is the whole difficulty. A site's window runs
    420 characters either side of the matched string, so the obvious key — the window's
    opening characters — is exactly the thing the repair moves: 0.5's wider gap makes the
    SAME site match a longer string that starts earlier, and the same site would then be
    counted twice, once as newly found and once as lost. The number stands at the END of
    every site pattern, so the text after it does not move when the gap widens. The key is
    therefore the value plus the last sixty characters of the window.

    It is not perfect: two sites carrying the same value in one paper within sixty
    characters of the same trailing text collapse into one. That undercounts a difference,
    which is the safer direction for a script whose job is to size the repair's effect.
    """
    return (str(s.get("value")), " ".join(s.get("window", "").split())[-60:])


def rates(rep, rows):
    measured = [r for r in rows if r.get("state") != "no_source"]
    invoking = [r for r in measured if r.get("mentioned")]
    cand = [r for r in invoking if not r["sites"]]
    return {"frame": len(rows), "measured": len(measured),
            "no_source": len(rows) - len(measured),
            "invoking": len(invoking),
            "with_site": sum(1 for r in measured if r["sites"]),
            "sites": sum(len(r["sites"]) for r in measured),
            "candidates": len(cand),
            "rate_of_invoking": round(100.0 * len(cand) / len(invoking), 1) if invoking else None,
            "candidate_ids": sorted(r["arxiv"] for r in cand)}


def focus_at(rows, value, flag, restrict=None):
    """Sites carrying a given value, and how many of them carry a given flag.

    Written here rather than taken from the report's `focus` block because the ruwe-1.4
    profile carries no `focus_value` (a defect the record noted at tick 48), and adding
    one now would put a change into the profiles that is not one of the seven repairs.
    The diff must isolate the repair, so the reading is computed instead of configured.
    """
    n_sites = n_flag = 0
    papers, flag_papers = set(), set()
    for r in rows:
        if r.get("state") == "no_source":
            continue
        if restrict is not None and r["arxiv"] not in restrict:
            continue
        for s in r["sites"]:
            if str(s.get("value")) == value:
                n_sites += 1
                papers.add(r["arxiv"])
                if s["flags"].get(flag):
                    n_flag += 1
                    flag_papers.add(r["arxiv"])
    return {"value": value, "sites": n_sites, "papers": len(papers),
            "flag": flag, "sites_with_flag": n_flag,
            "papers_with_flag": sorted(flag_papers)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--ref", required=True, help="directory holding the 0.4 reference")
    ap.add_argument("--out-prefix", default="remeasure-tick50")
    ap.add_argument("--nocomments", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated corpus keys")
    args = ap.parse_args()
    only = [k for k in args.only.split(",") if k]

    suffix = "-nocomments" if args.nocomments else ""
    out = {"tick": 50, "nocomments": bool(args.nocomments),
           "corpora": [], "profiles": [], "sha": []}
    newsites_path = f"{args.out_prefix}{suffix}-newsites.jsonl"
    newsites = open(newsites_path, "w", encoding="utf-8")

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
            r4 = run_measure(os.path.join(args.ref, "warrant_trace.py"),
                             os.path.join(args.ref, "profiles"), pid, src, frame,
                             f"{args.out_prefix}{suffix}-{pid}-0.4", args.nocomments)
            r5 = run_measure(os.path.join(HERE, "warrant_trace.py"),
                             os.path.join(HERE, "profiles"), pid, src, frame,
                             f"{args.out_prefix}{suffix}-{pid}-0.5", args.nocomments)
            a, b = rates(r4["report"], r4["rows"]), rates(r5["report"], r5["rows"])

            rows4 = {r["arxiv"]: r for r in r4["rows"]}
            gained = lost = 0
            papers_gained, papers_lost = [], []
            for aid, row5 in ((r["arxiv"], r) for r in r5["rows"]):
                row4 = rows4.get(aid, {})
                if row5.get("state") == "no_source":
                    continue
                k4 = {site_key(s) for s in row4.get("sites", [])}
                k5 = {site_key(s) for s in row5.get("sites", [])}
                new, gone = k5 - k4, k4 - k5
                gained += len(new)
                lost += len(gone)
                if new:
                    papers_gained.append(aid)
                if gone:
                    papers_lost.append(aid)
                for s in row5.get("sites", []):
                    if site_key(s) in new:
                        newsites.write(json.dumps({
                            "corpus": key, "profile": pid, "arxiv": aid,
                            "value": s.get("value"), "match": s.get("match"),
                            "cite_keys": s.get("cite_keys"), "target": s.get("target"),
                            "window": " ".join(s.get("window", "").split())}) + "\n")

            entry = {"corpus": key, "profile": pid, "v0_4": a, "v0_5": b,
                     "sites_gained": gained, "sites_lost": lost,
                     "papers_gaining_a_site": len(papers_gained),
                     "papers_losing_a_site": len(papers_lost),
                     "mentions_delta": b["invoking"] - a["invoking"],
                     "rate_delta": (None if a["rate_of_invoking"] is None
                                    else round(b["rate_of_invoking"] - a["rate_of_invoking"], 1))}
            if pid == "ruwe-1.4":
                entry["focus_1_4_0_4"] = focus_at(r4["rows"], "1.4", "cite_tn")
                entry["focus_1_4_0_5"] = focus_at(r5["rows"], "1.4", "cite_tn")
                # P5 of the pre-registration is about the SHIPPED reading, whose frame is
                # the 187 papers that state RUWE < 1.4 — and that frame is a strict subset
                # of these 599 (checked: 187 of 187). Restricting to it makes the repaired
                # count directly comparable with what left the house: 397 sites at 1.4, 4
                # of them carrying the deriving technical note at the site.
                sub = os.path.join(HERE, "frame-tick48-ruwe14.txt")
                if os.path.exists(sub):
                    ids = {l.split("#")[0].strip().replace("/", "_")
                           for l in open(sub, encoding="utf-8") if l.split("#")[0].strip()}
                    entry["shipped_frame_0_4"] = focus_at(r4["rows"], "1.4", "cite_tn", ids)
                    entry["shipped_frame_0_5"] = focus_at(r5["rows"], "1.4", "cite_tn", ids)
                    entry["shipped_frame_n"] = len(ids)
                    entry["shipped_as_published"] = {"papers": 187, "sites_at_1_4": 397,
                                                     "sites_with_note": 4}
            out["profiles"].append(entry)
            print(f"  {pid:10s} sites {a['sites']:5d} -> {b['sites']:5d}   "
                  f"invoking {a['invoking']:4d} -> {b['invoking']:4d}   "
                  f"candidates {a['candidates']:4d} -> {b['candidates']:4d}   "
                  f"rate {a['rate_of_invoking']} -> {b['rate_of_invoking']} %")

    newsites.close()
    with open(f"{args.out_prefix}{suffix}.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {args.out_prefix}{suffix}.json and {newsites_path}")


if __name__ == "__main__":
    main()
