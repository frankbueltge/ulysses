#!/usr/bin/env python3
"""Corpus construction: fetch the full XML of every CFR section headed
"Incorporation by reference", at a fixed issue date, from the eCFR versioner API.

This is corpus construction only. It fetches bytes and writes them to disk; it
parses nothing and prints no section content. It ran BEFORE PREREGISTRATION-01.md
was written, exactly as `collect_sections.py` did for the census of 2026-08-14.

Input: the frozen section list of 2026-08-14
       (projects/2026-08-14-the-addresses-the-law-prints/sections.json).
Output: data/xml/<title>-<section>.xml, one file per section, plus data/fetch-manifest.json
        with per-file sha256, byte size and HTTP status.

Usage: python3 fetch_sections.py [--date 2026-08-11]
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

SRC = "projects/2026-08-14-the-addresses-the-law-prints/sections.json"
UA = "Ulysses research (artistic research practice; contact via frankbueltge.de)"


def fetch(title: int, section: str, date: str, dest: str) -> dict:
    url = (f"https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title}.xml"
           f"?section={section}")
    out = subprocess.run(
        ["curl", "-s", "--max-time", "120", "-A", UA, "-o", dest,
         "-w", "%{http_code}", url],
        capture_output=True, text=True,
    )
    status = out.stdout.strip() or "000"
    rec = {"title": title, "section": section, "url": url, "http": status}
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        b = open(dest, "rb").read()
        rec["bytes"] = len(b)
        rec["sha256"] = hashlib.sha256(b).hexdigest()
    else:
        rec["bytes"] = 0
        rec["sha256"] = None
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-08-11")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--outdir", default="projects/2026-08-17-the-warrant-under-the-section/data")
    a = ap.parse_args()

    sections = json.load(open(a.src))["sections"]
    xmldir = os.path.join(a.outdir, "xml")
    os.makedirs(xmldir, exist_ok=True)

    manifest = {"issue_date": a.date, "source_list": a.src, "count": len(sections),
                "user_agent": UA, "files": []}
    ok = 0
    for i, s in enumerate(sections, 1):
        name = f"{s['title']}-{s['section'].replace('/', '_')}.xml"
        dest = os.path.join(xmldir, name)
        rec = fetch(s["title"], s["section"], a.date, dest)
        rec["file"] = name
        rec["heading"] = s["heading"]
        manifest["files"].append(rec)
        if rec["http"] == "200" and rec["bytes"] > 0:
            ok += 1
        if i % 25 == 0:
            print(f"  {i}/{len(sections)} fetched, {ok} ok", file=sys.stderr, flush=True)
        time.sleep(0.6)

    manifest["ok"] = ok
    with open(os.path.join(a.outdir, "fetch-manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"{ok}/{len(sections)} sections fetched with HTTP 200 and non-empty body")
    return 0


if __name__ == "__main__":
    sys.exit(main())
