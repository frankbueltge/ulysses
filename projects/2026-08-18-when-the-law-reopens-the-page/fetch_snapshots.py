#!/usr/bin/env python3
"""Step 2 — corpus construction: the section XML at the two dates fixed by D3.

`after`  = 2026-08-11 for all 290 corpus sections (the issue date the corpus is frozen at).
`before` = 2017-01-01 for the reopened sections only (D2) — the first date the eCFR
           point-in-time system covers.

Bytes only. Parsing happens in `parse_moves.py`, which copies its extraction rule unchanged
from the study of 2026-08-17 (the blind step of PREREGISTRATION-01.md).

Output: data/xml/{before,after}/<title>-<section>.xml + data/snapshot-manifest.json

Usage: python3 fetch_snapshots.py
"""

import hashlib
import json
import os
import subprocess
import sys
import time

BASE = "projects/2026-08-18-when-the-law-reopens-the-page"
VERS = f"{BASE}/data/versions.json"
OUT = f"{BASE}/data/snapshot-manifest.json"
UA = "Ulysses research (artistic research practice; contact via frankbueltge.de)"
API = "https://www.ecfr.gov/api/versioner/v1/full/{d}/title-{t}.xml?section={s}"
BEFORE_DATE = "2017-01-01"
AFTER_DATE = "2026-08-11"


def fetch(url: str, dest: str, tries: int = 3) -> dict:
    status = "000"
    for n in range(tries):
        out = subprocess.run(
            ["curl", "-s", "--max-time", "180", "-A", UA, "-o", dest, "-w", "%{http_code}", url],
            capture_output=True, text=True,
        )
        status = out.stdout.strip() or "000"
        if status == "200":
            break
        time.sleep(2 * (n + 1))
    rec = {"url": url, "http": status}
    if status == "200" and os.path.exists(dest) and os.path.getsize(dest) > 0:
        b = open(dest, "rb").read()
        rec["bytes"] = len(b)
        rec["sha256"] = hashlib.sha256(b).hexdigest()
    else:
        rec["bytes"] = 0
        rec["sha256"] = None
        if os.path.exists(dest):
            os.remove(dest)
    return rec


def main() -> int:
    vers = json.load(open(VERS))["records"]
    jobs = []
    for r in vers:
        amd = [v["date"] for v in r.get("versions", []) if v.get("date", "") >= "2017-01-02"]
        jobs.append(("after", r["title"], r["section"]))
        if amd:
            jobs.append(("before", r["title"], r["section"]))

    for w in ("before", "after"):
        os.makedirs(f"{BASE}/data/xml/{w}", exist_ok=True)

    files = []
    for i, (which, title, section) in enumerate(jobs, 1):
        date = BEFORE_DATE if which == "before" else AFTER_DATE
        name = f"{title}-{section}.xml"
        dest = f"{BASE}/data/xml/{which}/{name}"
        rec = fetch(API.format(d=date, t=title, s=section), dest)
        rec.update({"which": which, "date": date, "title": title,
                    "section": section, "file": name})
        files.append(rec)
        if i % 50 == 0 or i == len(jobs):
            print(f"  {i}/{len(jobs)}", flush=True)
        time.sleep(0.35)

    with open(OUT, "w") as fh:
        json.dump({"fetched": "2026-08-18", "before_date": BEFORE_DATE,
                   "after_date": AFTER_DATE, "count": len(files), "files": files}, fh, indent=1)
    for w in ("before", "after"):
        sub = [f for f in files if f["which"] == w]
        ok = sum(1 for f in sub if f["http"] == "200")
        print(f"{w}: {ok}/{len(sub)} HTTP 200")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
