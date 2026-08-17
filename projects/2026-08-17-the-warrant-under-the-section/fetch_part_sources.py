#!/usr/bin/env python3
"""Diagnosis of C1's failure — NOT a pre-registered measurement.

W1 of PREREGISTRATION-01.md reads the section's `<CITA>` element and nothing else. 76 of the
290 sections have none, and C1 failed on that count. Hand-checking two of them showed why: in
those parts the source note is printed once, above the sections, in a `<SOURCE>` element W1
never looked at.

This script fetches the whole part for every section that had no `<CITA>`, finds the section
inside it, and takes the **last `<SOURCE>` element before that section in document order** —
which is the note a reader meets on the way down to it.

Everything this produces is reported as description in MEASUREMENT.md. C1 stands failed as
written: a rule is not repaired after seeing its result.

**Repair, recorded (2026-08-17, after the first run and before anything was written up).** The
first version derived the part by splitting the section number at the dot. That is wrong where
a part numbers its subparts: 43 CFR 3174.3 sits in **part 3170**, not part 3174, and the API
answered `404 No matching content found`. Three sections were counted as carrying no printed
warrant anywhere; all three do carry one. The part now comes from the eCFR ancestry endpoint,
which answers it authoritatively and cannot make that mistake.

Output: data/part-sources.json

Usage: python3 fetch_part_sources.py
"""

import json
import os
import re
import subprocess
import sys
import time

DIR = "projects/2026-08-17-the-warrant-under-the-section/data"
UA = "Ulysses research (artistic research practice; contact via frankbueltge.de)"
RE_SOURCE = re.compile(r"<SOURCE>.*?</SOURCE>", re.S)
RE_TAG = re.compile(r"<[^>]+>")
RE_DATE_YEAR = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s*(\d{4})"
)


def part_of(title: int, section: str, date: str) -> str | None:
    """The section's part, from the eCFR ancestry endpoint — authoritative, and it cannot
    make the dot-splitting mistake described above."""
    url = (f"https://www.ecfr.gov/api/versioner/v1/ancestry/{date}/"
           f"title-{title}.json?section={section}")
    proc = subprocess.run(["curl", "-s", "--max-time", "120", "-A", UA, url],
                          capture_output=True)
    try:
        anc = json.loads(proc.stdout.decode("utf-8", errors="replace"))["ancestors"]
    except Exception:
        return None
    for a in anc:
        if a.get("type") == "part":
            return a.get("identifier")
    return None


def source_before(xml: str, section: str) -> tuple[str | None, int | None]:
    """The last <SOURCE> above the section in document order, and its latest year."""
    sec = re.search(rf'<DIV8[^>]*\bN="{re.escape(section)}"', xml)
    cut = sec.start() if sec else len(xml)
    last = None
    for m in RE_SOURCE.finditer(xml):
        if m.start() < cut:
            last = m
        else:
            break
    if not last:
        return None, None
    text = re.sub(r"\s+", " ", RE_TAG.sub("", last.group(0))).strip()
    years = [int(y) for y in RE_DATE_YEAR.findall(text)]
    return text, (max(years) if years else None)


def main() -> int:
    d = json.load(open(os.path.join(DIR, "warrants.json")))
    targets = [r for r in d["records"]
               if not r.get("fetch_failed") and not r.get("has_cita")]

    cache: dict[tuple[int, str], str] = {}
    out = []
    for i, r in enumerate(targets, 1):
        part = part_of(r["title"], r["section"], d["issue_date"])
        time.sleep(0.4)
        key = (r["title"], part)
        if key not in cache:
            url = (f"https://www.ecfr.gov/api/versioner/v1/full/{d['issue_date']}/"
                   f"title-{key[0]}.xml?part={key[1]}")
            proc = subprocess.run(["curl", "-s", "--max-time", "180", "-A", UA, url],
                                  capture_output=True)
            cache[key] = proc.stdout.decode("utf-8", errors="replace")
            time.sleep(0.6)
        xml = cache[key]
        text, year = source_before(xml, r["section"])
        out.append({"title": r["title"], "part": part, "section": r["section"],
                    "has_part_source": text is not None,
                    "source_text": text, "part_source_year": year,
                    "hedged": bool(text and "unless otherwise noted" in text),
                    "part_bytes": len(xml)})
        if i % 20 == 0:
            print(f"  {i}/{len(targets)}", file=sys.stderr, flush=True)

    with_source = [r for r in out if r["has_part_source"]]
    with_year = [r for r in out if r["part_source_year"]]
    payload = {"n_sections_without_cita": len(out),
               "n_distinct_parts": len(cache),
               "n_with_part_source": len(with_source),
               "n_with_part_source_year": len(with_year),
               "n_hedged": len([r for r in out if r["hedged"]]),
               "records": out}
    with open(os.path.join(DIR, "part-sources.json"), "w") as f:
        json.dump(payload, f, indent=1)
    print(f"{len(out)} sections without <CITA>, in {len(cache)} distinct parts; "
          f"{len(with_source)} carry a source note above them, {len(with_year)} with a year")
    return 0


if __name__ == "__main__":
    sys.exit(main())
