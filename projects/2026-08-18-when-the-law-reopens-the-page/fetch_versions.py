#!/usr/bin/env python3
"""Step 1 — corpus construction: the recorded version history of every CFR section
headed "Incorporation by reference".

Fetches dates only. No section text is retrieved here and no edition year is parsed,
so nothing this file writes can reach the clauses of PREREGISTRATION-01.md except C1
and C2, both of which are fixed in that file before this ran.

Input:  projects/2026-08-17-the-warrant-under-the-section/data/warrants.json (290 sections)
Output: data/versions.json — one record per section: every version date the eCFR holds.

Usage: python3 fetch_versions.py
"""

import json
import os
import subprocess
import sys
import time

SRC = "projects/2026-08-17-the-warrant-under-the-section/data/warrants.json"
OUT = "projects/2026-08-18-when-the-law-reopens-the-page/data/versions.json"
UA = "Ulysses research (artistic research practice; contact via frankbueltge.de)"
API = "https://www.ecfr.gov/api/versioner/v1/versions/title-{t}.json?section={s}"


def get(url: str) -> tuple[str, str]:
    out = subprocess.run(
        ["curl", "-s", "--max-time", "90", "-A", UA, "-w", "\n%{http_code}", url],
        capture_output=True, text=True,
    )
    body = out.stdout
    if "\n" in body:
        body, status = body.rsplit("\n", 1)
    else:
        status = "000"
    return body, status.strip()


def main() -> int:
    corpus = json.load(open(SRC))["records"]
    sections = sorted({(r["title"], r["section"]) for r in corpus})
    print(f"{len(sections)} sections")

    records = []
    for i, (title, section) in enumerate(sections, 1):
        url = API.format(t=title, s=section)
        body, status = get(url)
        rec = {"title": title, "section": section, "url": url, "http": status}
        if status == "200":
            try:
                d = json.loads(body)
                cv = d.get("content_versions", [])
                rec["n_records"] = len(cv)
                rec["versions"] = [
                    {"date": c.get("date"),
                     "amendment_date": c.get("amendment_date"),
                     "issue_date": c.get("issue_date"),
                     "substantive": c.get("substantive"),
                     "removed": c.get("removed")}
                    for c in cv
                ]
            except json.JSONDecodeError:
                rec["parse_failed"] = True
        records.append(rec)
        if i % 25 == 0 or i == len(sections):
            print(f"  {i}/{len(sections)}", flush=True)
        time.sleep(0.4)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({"corpus": len(sections), "fetched": "2026-08-18",
                   "records": records}, fh, indent=1)
    ok = sum(1 for r in records if r["http"] == "200")
    print(f"{ok}/{len(records)} HTTP 200 -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
