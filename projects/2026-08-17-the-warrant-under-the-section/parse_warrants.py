#!/usr/bin/env python3
"""The warrant under the section: parse each IBR section's printed source note against
the newest edition year the section binds.

Parse rules W1, W2, W3, W3a and the crossing definition are fixed in PREREGISTRATION-01.md
and were written before this file. Nothing here reads a band or scores a clause — that is
`score.py`, which copies the bands from the pre-registration.

Input:  data/xml/*.xml (frozen corpus, sha256 in data/fetch-manifest.json)
Output: data/warrants.json — one record per section.

Usage: python3 parse_warrants.py [--dir data] [--out data/warrants.json]
"""

import argparse
import json
import os
import re
import sys

# W1: a year inside a date. Source notes print "June 27, 1974" / "Feb. 10, 1984".
RE_DATE_YEAR = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s*(\d{4})"
)
# W1 fallback, used only when a CITA carries no month-anchored date at all.
RE_ANY_YEAR = re.compile(r"(?<!\d)(19\d{2}|20[0-2]\d)(?!\d)")
# W3: an explicit four-digit edition year in the section's own paragraphs.
RE_YEAR4 = re.compile(r"(?<!\d)(19\d{2}|20[0-2]\d)(?!\d)")
# W3a: the 25 characters before a candidate year mark it as a citation year, not an edition.
W3A_MARKERS = ("FR ", "Federal Register", "Pub. L", "U.S.C", "Stat.", "CFR")

RE_CITA = re.compile(r"<CITA\b.*?</CITA>", re.S)
RE_EDNOTE = re.compile(r"<EDNOTE\b.*?</EDNOTE>", re.S)
RE_DIV8 = re.compile(r"<DIV8\b.*?</DIV8>", re.S)
RE_P = re.compile(r"<P\b[^>]*>(.*?)</P>", re.S)
RE_TAG = re.compile(r"<[^>]+>")

ENTITIES = {"&#xA7;": "§", "&amp;": "&", "&#x2014;": "—", "&quot;": '"',
            "&#x201C;": "“", "&#x201D;": "”", "&lt;": "<", "&gt;": ">"}


def flatten(s: str) -> str:
    s = RE_TAG.sub("", s)
    for k, v in ENTITIES.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip()


def warrant_year(cita_texts: list[str]) -> tuple[int | None, str]:
    """W1: the latest year in a date inside the section's source note(s)."""
    years, path = [], "none"
    for t in cita_texts:
        found = [int(y) for y in RE_DATE_YEAR.findall(t)]
        if found:
            years += found
            path = "date"
    if not years:
        for t in cita_texts:
            found = [int(y) for y in RE_ANY_YEAR.findall(t)]
            if found:
                years += found
                path = "fallback_any_year"
    if not years:
        return None, path
    return max(years), path


def edition_years(paragraphs: list[str]) -> list[int]:
    """W3 + W3a: explicit four-digit edition years in the section's own paragraphs."""
    out = []
    for p in paragraphs:
        for m in RE_YEAR4.finditer(p):
            before = p[max(0, m.start() - 25):m.start()]
            if any(k in before for k in W3A_MARKERS):
                continue
            out.append(int(m.group(1)))
    return out


def parse_file(path: str) -> dict:
    raw = open(path, encoding="utf-8", errors="replace").read()
    div = RE_DIV8.search(raw)
    body = div.group(0) if div else raw

    citas = [flatten(c) for c in RE_CITA.findall(body)]
    ednotes = [flatten(e) for e in RE_EDNOTE.findall(body)]
    stripped = RE_EDNOTE.sub(" ", RE_CITA.sub(" ", body))
    paragraphs = [flatten(p) for p in RE_P.findall(stripped)]
    paragraphs = [p for p in paragraphs if p]

    wy, wpath = warrant_year(citas)
    eys = edition_years(paragraphs)
    rec = {
        "file": os.path.basename(path),
        "has_cita": bool(citas),
        "cita_text": citas[0] if citas else None,
        "n_cita": len(citas),
        "warrant_year": wy,
        "warrant_path": wpath,
        "offloaded": any("List of CFR Sections Affected" in e for e in ednotes),
        "n_paragraphs": len(paragraphs),
        "n_edition_years": len(eys),
        "newest_edition_year": max(eys) if eys else None,
        "one_div8": bool(div),
    }
    if wy is not None and eys:
        rec["gap"] = max(eys) - wy
        rec["crosses"] = max(eys) > wy
    else:
        rec["gap"] = None
        rec["crosses"] = None
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="projects/2026-08-17-the-warrant-under-the-section/data")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    manifest = json.load(open(os.path.join(a.dir, "fetch-manifest.json")))
    by_file = {f["file"]: f for f in manifest["files"]}

    records = []
    for f in sorted(os.listdir(os.path.join(a.dir, "xml"))):
        if not f.endswith(".xml"):
            continue
        meta = by_file.get(f, {})
        if meta.get("http") != "200" or not meta.get("bytes"):
            records.append({"file": f, "fetch_failed": True,
                            "title": meta.get("title"), "section": meta.get("section")})
            continue
        rec = parse_file(os.path.join(a.dir, "xml", f))
        rec["title"] = meta.get("title")
        rec["section"] = meta.get("section")
        rec["sha256"] = meta.get("sha256")
        records.append(rec)

    out = a.out or os.path.join(a.dir, "warrants.json")
    with open(out, "w") as fh:
        json.dump({"corpus": manifest["count"], "issue_date": manifest["issue_date"],
                   "records": records}, fh, indent=1)
    print(f"{len(records)} sections parsed -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
