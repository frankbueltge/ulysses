#!/usr/bin/env python3
"""Enumerate every CFR section headed "Incorporation by reference."

Walks the eCFR versioner structure API for all 50 titles at a fixed issue date and
collects the sections whose label_description contains that phrase. This is corpus
construction only: it reads headings, never section text, and it ran before
PREREGISTRATION-01.md was written.

Output: sections.json — one record per section (title, section identifier, heading).

Usage: python3 collect_sections.py [--date 2026-08-11] [--out sections.json]
"""

import argparse
import json
import subprocess
import sys
import time

PHRASE = "ncorporation by reference"  # case-insensitive on the first letter


def structure(title: int, date: str) -> dict | None:
    out = subprocess.run(
        ["curl", "-s", "--max-time", "180",
         f"https://www.ecfr.gov/api/versioner/v1/structure/{date}/title-{title}.json"],
        capture_output=True,
    )
    if not out.stdout:
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return None


def sections(node: dict, title: int, found: list) -> None:
    if node.get("type") == "section":
        label = node.get("label_description") or ""
        if PHRASE in label:
            found.append({
                "title": title,
                "section": node.get("identifier"),
                "heading": label,
                "reserved": bool(node.get("reserved")),
            })
    for child in node.get("children") or []:
        sections(child, title, found)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-08-11")
    ap.add_argument("--out", default="sections.json")
    args = ap.parse_args()

    rows: list[dict] = []
    failed: list[int] = []
    for title in range(1, 51):
        data = structure(title, args.date)
        if data is None:
            failed.append(title)
            print(f"title {title}: FETCH FAILED", file=sys.stderr)
            continue
        found: list[dict] = []
        sections(data, title, found)
        rows.extend(found)
        print(f"title {title}: {len(found)}", flush=True)
        time.sleep(0.5)

    json.dump({"issue_date": args.date, "titles_failed": failed, "count": len(rows),
               "sections": rows}, open(args.out, "w"), indent=1)
    print(f"TOTAL {len(rows)} sections, {len(failed)} titles unreachable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
