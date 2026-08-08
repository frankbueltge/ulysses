#!/usr/bin/env python3
"""Build the tick-47 frame: four two-year strata, quartered, one rule everywhere.

Tick 46 read 256 papers from one edge of a literature and wrote against itself that
"a literature that has used this threshold since 2010 is not read by reading its newest
edge". This builds the frame that tests it: the same query in four two-year windows,
each split into its 8 calendar quarters, 8 papers taken per quarter.

The quartering is the point. The obvious rule -- the N most recent papers in a window --
would put the 2014-2015 sample entirely in late 2015, and each era would then be selected
by a differently-shaped rule. Fixed in PREREGISTRATION-tick47.md section 3 before this ran.

Writes:

    frame-tick47.json   queries, windows, per-quarter yields and shortfalls, drop rule,
                        and every member with its era, quarter, categories and date
    frame-tick47.txt    the ids file, one per line, for `warrant_trace.py fetch`
                        and for `measure --frame`
    frame-tick47-<ERA>.txt   the same, split per era, because every rate is per era

    python3 frame-tick47.py --out .

Exit codes: 0 built, 3 the API could not be reached.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "https://export.arxiv.org/api/query"
UA = "ulysses-warrant-trace/0.4 (artistic research; one request per 3 s)"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"

# Pre-registered 2026-08-08 before the build. Earliest era wins duplicates.
QUERY = 'cat:cs.CV AND abs:"object detection"'
PER_QUARTER = 8
ERAS = {
    "E1": ("2014-01-01", "2015-12-31"),
    "E2": ("2017-01-01", "2018-12-31"),
    "E3": ("2020-01-01", "2021-12-31"),
    "E4": ("2024-07-01", "2026-06-30"),
}


def quarters(start: str, end: str) -> list[tuple[str, str, str]]:
    """The 8 calendar quarters spanned by a two-year window, as API date stamps."""
    sy, sm = int(start[:4]), int(start[5:7])
    out = []
    y, m = sy, sm
    while True:
        # quarter starting at (y, m); m is always 1, 4, 7 or 10 by construction
        em_y, em_m = (y, m + 3) if m + 3 <= 12 else (y + 1, m + 3 - 12)
        lo = f"{y:04d}{m:02d}010000"
        # exclusive upper bound written as the last minute of the previous day
        hi_y, hi_m = em_y, em_m
        hi = f"{hi_y:04d}{hi_m:02d}010000"
        label = f"{y}Q{(m - 1) // 3 + 1}"
        out.append((label, lo, hi))
        if f"{em_y:04d}-{em_m:02d}" > end[:7]:
            break
        y, m = em_y, em_m
        if len(out) >= 8:
            break
    return out[:8]


def query(search: str, want: int) -> list[dict]:
    url = API + "?" + urllib.parse.urlencode({
        "search_query": search,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": want,
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as fh:
        feed = ET.fromstring(fh.read())
    out = []
    for e in feed.findall(ATOM + "entry"):
        full = e.findtext(ATOM + "id", "").rsplit("/", 1)[-1]
        base = re.sub(r"v\d+$", "", full)
        primary = e.find(ARXIV + "primary_category")
        out.append({
            "id": full,
            "base": base,
            "cats": [c.get("term") for c in e.findall(ATOM + "category")],
            "primary": primary.get("term") if primary is not None else "",
            "title": " ".join((e.findtext(ATOM + "title") or "").split()),
            "published": e.findtext(ATOM + "published", ""),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=".", help="directory for the artefacts")
    args = ap.parse_args()

    built = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    papers, seen, duplicates, yields = [], set(), [], []

    for era, (start, end) in ERAS.items():
        for label, lo, hi in quarters(start, end):
            search = f'{QUERY} AND submittedDate:[{lo} TO {hi}]'
            try:
                entries = query(search, PER_QUARTER)
            except Exception as exc:                    # recorded, never silent
                print(f"frame-tick47: {era} {label} unreachable: "
                      f"{type(exc).__name__}: {exc}", file=sys.stderr)
                return 3
            kept = 0
            for e in entries:
                if e["base"] in seen:
                    duplicates.append(e["base"])
                    continue
                seen.add(e["base"])
                e["era"], e["quarter"] = era, label
                papers.append(e)
                kept += 1
            yields.append({"era": era, "quarter": label, "returned": len(entries),
                           "kept": kept, "short": PER_QUARTER - len(entries)})
            print(f"{era} {label}: {len(entries)} returned, {kept} kept",
                  file=sys.stderr)
            time.sleep(3)

    per_era = {}
    for p in papers:
        per_era[p["era"]] = per_era.get(p["era"], 0) + 1

    record = {
        "built_utc": built,
        "query": QUERY,
        "eras": ERAS,
        "per_quarter": PER_QUARTER,
        "sampling_rule": ("each era split into its 8 calendar quarters; the API's 8 most "
                          "recent matching papers taken per quarter, sortBy=submittedDate "
                          "descending. Pre-registered before the build."),
        "drop_rule": "duplicates by arXiv id without version; the earliest era wins.",
        "quarter_yields": yields,
        "short_quarters": [y for y in yields if y["returned"] < PER_QUARTER],
        "duplicates": len(duplicates),
        "duplicate_ids": sorted(set(duplicates)),
        "size": len(papers),
        "size_per_era": per_era,
        "papers": papers,
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "frame-tick47.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
    with open(os.path.join(args.out, "frame-tick47.txt"), "w", encoding="utf-8") as fh:
        for p in papers:
            fh.write(p["id"] + "\n")
    for era in ERAS:
        path = os.path.join(args.out, f"frame-tick47-{era}.txt")
        with open(path, "w", encoding="utf-8") as fh:
            for p in papers:
                if p["era"] == era:
                    fh.write(p["id"] + "\n")

    print(f"frame: {len(papers)} papers {per_era} "
          f"({len(duplicates)} duplicates dropped)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
