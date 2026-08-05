#!/usr/bin/env python3
"""Silent-zero audit of the tick-19/21 measurement — work-line 2026-07-23-negative-parallax.

Tick 34 found that a paper with no LaTeX source at arXiv contributes an all-zero row to
`circulation-measure-ruwe.csv`, and that such a row is indistinguishable from a paper
that was read and does not mention the statistic. The published figure of this line —
four papers of 599 name the deriving document — has 599 in its denominator. This script
decides, for every paper in that frame, whether its zeros were earned.

It joins three files:

  * the fetch manifest written by `warrant-trace/warrant_trace.py fetch` over the whole
    frame (one JSON record per paper: bytes, sha256, members, ok);
  * the landed table `circulation-measure-ruwe.csv` (tick 21, 2026-08-01);
  * the re-measurement written by `warrant_trace.py measure --frame`, which carries an
    explicit `no_source` state (instrument 0.2, the repair this audit obliged).

Per paper it returns one of five verdicts:

  NO_SOURCE_ZEROS   no readable source, and the landed row is all zeros
                    -> the zeros were never earned; the paper is outside the frame
  NO_SOURCE_NONZERO no readable source, but the landed row carries data
                    -> the source WAS readable in July and is not now (a version change)
  TRUE_ZERO         source read, landed row zero, re-measurement zero
  AGREE             source read, landed row and re-measurement agree, non-zero
  DISAGREE          source read, and the two disagree -> hand-read, cause assigned

Usage:
    python3 silent-zero-audit-tick35.py --manifest fetch-manifest.jsonl \\
        --landed circulation-measure-ruwe.csv --now measure.csv --out audit.csv

No network, no paid service. The corpus itself is not redistributed.
"""
import argparse
import csv
import json

ZERO_FIELDS = ["ruwe_mentioned", "ruwe_sites", "ruwe_cite_lindegren", "ruwe_cite_tn",
               "ruwe_prov", "ruwe_prov_dr2", "ruwe_hedge", "pos_sites", "pos_attributed",
               "neg_sites", "neg_attributed"]
COMPARE = [("ruwe_mentioned", "mentioned"), ("ruwe_sites", "sites"),
           ("ruwe_values", "values"), ("ruwe_cite_targets", "targets"),
           ("ruwe_cite_lindegren", "flag_cite_lindegren"),
           ("ruwe_cite_tn", "flag_cite_tn"), ("ruwe_prov", "flag_prov"),
           ("ruwe_prov_dr2", "flag_prov_dr2"), ("ruwe_hedge", "flag_hedge")]


def all_zero(row):
    return (all(row.get(f, "0") in ("0", "") for f in ZERO_FIELDS)
            and row.get("ruwe_values", "") == ""
            and row.get("pos_values", "") == ""
            and row.get("neg_values", "") == "")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--landed", required=True)
    ap.add_argument("--now", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    man = {}
    with open(a.manifest, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                man[r["arxiv"].replace("/", "_")] = r
    landed = {r["arxiv"].replace("/", "_"): r
              for r in csv.DictReader(open(a.landed, encoding="utf-8", newline=""))}
    now = {r["arxiv"]: r
           for r in csv.DictReader(open(a.now, encoding="utf-8", newline=""))}

    out, counts = [], {}
    for aid, lrow in landed.items():
        m = man.get(aid, {})
        readable = bool(m.get("ok")) and int(m.get("members", 0)) > 0
        nrow = now.get(aid, {})
        az = all_zero(lrow)
        diffs = []
        if readable and nrow.get("state") == "measured":
            for lcol, ncol in COMPARE:
                if lcol in lrow and ncol in nrow and str(lrow[lcol]) != str(nrow[ncol]):
                    diffs.append(f"{lcol}:{lrow[lcol]!r}->{nrow[ncol]!r}")
        if not readable:
            verdict = "NO_SOURCE_ZEROS" if az else "NO_SOURCE_NONZERO"
        elif diffs:
            verdict = "DISAGREE"
        elif az:
            verdict = "TRUE_ZERO"
        else:
            verdict = "AGREE"
        counts[verdict] = counts.get(verdict, 0) + 1
        out.append({"arxiv": aid, "verdict": verdict,
                    "fetch_ok": int(readable), "members": m.get("members", 0),
                    "bytes": m.get("bytes", ""), "fetch_error": m.get("error", ""),
                    "landed_all_zero": int(az),
                    "landed_mentioned": lrow.get("ruwe_mentioned", ""),
                    "now_mentioned": nrow.get("mentioned", ""),
                    "diffs": "; ".join(diffs)})

    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        for r in sorted(out, key=lambda r: (r["verdict"], r["arxiv"])):
            w.writerow(r)

    frame = len(landed)
    silent = counts.get("NO_SOURCE_ZEROS", 0)
    print(f"frame                 : {frame} papers")
    for k in sorted(counts):
        print(f"  {k:18s} {counts[k]}")
    read = frame - silent - counts.get("NO_SOURCE_NONZERO", 0)
    print(f"\ndenominator as published : {frame}")
    print(f"denominator earned       : {read}  "
          f"(papers whose source this audit could actually read)")
    if read:
        print(f"the tick-21 headline restated: 4 of {read} papers name the deriving "
              f"document = {100.0*4/read:.2f}%  (published as 4 of {frame} = "
              f"{100.0*4/frame:.2f}%)")


if __name__ == "__main__":
    main()
