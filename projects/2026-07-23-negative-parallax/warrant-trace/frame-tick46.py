#!/usr/bin/env python3
"""Build the tick-46 frame from the arXiv API, and keep the code that built it.

`warrant-trace/README.md` names the frame as the episode's sharpest limitation: the
instrument takes a frame and does not build one, and of the three shipped readings
only case 3's frame is re-derivable from committed code. This file is the fourth
case refusing to repeat that. It writes two artefacts:

    frame-tick46.json   queries, timestamps, drop rule, and every member with its
                        categories, title and submission date
    frame-tick46.txt    the ids file, one per line, for `warrant_trace.py fetch`
                        and for `measure --frame`

The queries and the drop rule are fixed in PREREGISTRATION-tick46.md §3 before this
ran. Nothing here chooses the frame's size; the API's answer is the frame.

    python3 frame-tick46.py --out .

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

# Pre-registered 2026-08-08, before the build. F1 wins duplicates.
QUERIES = {
    "F1": ('cat:cs.CV AND abs:"object detection"', 130),
    "F2": ('cat:cs.CV AND abs:"instance segmentation"', 130),
}


def query(search: str, want: int) -> list[dict]:
    url = API + "?" + urllib.parse.urlencode({
        "search_query": search,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": want,
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as fh:
        feed = ET.fromstring(fh.read())
    out = []
    for e in feed.findall(ATOM + "entry"):
        full = e.findtext(ATOM + "id", "").rsplit("/", 1)[-1]        # 2607.24378v1
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
    ap.add_argument("--out", default=".", help="directory for the two artefacts")
    args = ap.parse_args()

    built = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    papers, seen, duplicates = [], set(), []
    for name, (search, want) in QUERIES.items():
        try:
            entries = query(search, want)
        except Exception as exc:                       # recorded, never silent
            print(f"frame-tick46: {name} unreachable: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            return 3
        for e in entries:
            if e["base"] in seen:
                duplicates.append(e["base"])
                continue
            seen.add(e["base"])
            e["frame"] = name
            papers.append(e)
        print(f"{name}: {len(entries)} returned", file=sys.stderr)
        time.sleep(3)

    record = {
        "built_utc": built,
        "queries": {k: v[0] for k, v in QUERIES.items()},
        "requested_each": {k: v[1] for k, v in QUERIES.items()},
        "drop_rule": "duplicates by arXiv id without version; F1 wins. No other drop.",
        "duplicates": len(duplicates),
        "duplicate_ids": sorted(set(duplicates)),
        "size": len(papers),
        "papers": papers,
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "frame-tick46.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
    with open(os.path.join(args.out, "frame-tick46.txt"), "w", encoding="utf-8") as fh:
        for p in papers:
            fh.write(p["id"] + "\n")
    print(f"frame: {len(papers)} papers ({len(duplicates)} duplicates dropped)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
