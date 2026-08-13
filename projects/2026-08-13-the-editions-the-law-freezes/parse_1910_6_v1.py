#!/usr/bin/env python3
"""Census of the editions frozen by 29 CFR 1910.6 (incorporation by reference).

Parse rules are fixed in PREREGISTRATION-01.md (E1-E6) and were written before this file.
Input: the section XML as served by the eCFR versioner API.
Output: entries.json (one record per entry) and a summary on stdout.

Usage: python3 parse_1910_6.py <section.xml> [--json entries.json]
"""

import hashlib
import json
import re
import sys
from collections import Counter

THIS_YEAR = 2026

# E3: a reaffirmation marker, stripped before the edition year is read.
RE_REAFFIRM = re.compile(r"\(\s*R\s*\.?\s*(\d{2,4})\s*\)")
# E2a: an explicit four-digit year.
RE_YEAR4 = re.compile(r"(?<!\d)(19\d{2}|20[0-2]\d)(?!\d)")
# E2b: a hyphenated two-digit suffix on a designation token, e.g. A11.1-65, B30.2-43.
# The token before the hyphen must contain a digit (a designation, not a word).
RE_DESIG2 = re.compile(r"(?<![\w.-])([A-Z][A-Za-z0-9.]*\d[A-Za-z0-9.]*)-(\d{2})(?![\d\w-])")
# A free online location for the document itself (C6). Organisation home pages are not this.
RE_URL = re.compile(r"(https?://\S+|www\.\S+)")

RESERVED = re.compile(r"^\(\s*[^)]{0,12}\s*\)\s*(-\s*\(\s*[^)]{0,12}\s*\)\s*)?\[Reserved\]\s*$")
# An organisation header: paragraph letter + organisation + address/phone/website, no IBR approval.
RE_PARA_LETTER = re.compile(r"^\(([a-z])\)")
RE_ENTRY_NUM = re.compile(r"^\((\d+)\)")


def flatten(p):
    s = re.sub(r"<[^>]+>", "", p)
    s = s.replace("&#xA7;", "§").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


def is_entry(text):
    """E1: a paragraph that names an incorporated document."""
    if not text or RESERVED.match(text):
        return False
    if "[Reserved]" in text and len(text) < 40:
        return False
    # Numbered list items inside the organisation lists are the entries.
    if not RE_ENTRY_NUM.match(text):
        return False
    # Guard: the introductory (a)(1)/(2) prose is numbered too but carries no designation.
    if "IBR approved" in text or "approved for" in text:
        return True
    # Some entries omit the phrase; require a designation-looking token instead.
    return bool(re.search(r"[A-Z]{2,}[\s ]?[A-Z]?[\w.]*[-\s]\d", text))


def edition_year(text):
    """E2/E3/E4: the first year attached to the primary designation."""
    reaffirmations = [m.group(1) for m in RE_REAFFIRM.finditer(text)]
    stripped = RE_REAFFIRM.sub(" ", text)
    # Cut the citation tail: everything from "IBR approved" / "approved for" onwards names
    # CFR sections, not editions.
    head = re.split(r"IBR approved|IB approved|approved for", stripped)[0]
    cands = []
    for m in RE_YEAR4.finditer(head):
        cands.append((m.start(), int(m.group(1)), "y4", m.group(0)))
    for m in RE_DESIG2.finditer(head):
        yy = int(m.group(2))
        # Two-digit years in this section are 20th century throughout.
        cands.append((m.start(), 1900 + yy, "d2", m.group(0)))
    cands.sort()
    if not cands:
        return None, reaffirmations, None
    pos, year, kind, token = cands[0]
    return year, reaffirmations, token


def main():
    path = sys.argv[1]
    raw = open(path, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    xml = raw.decode("utf-8")
    paras = [flatten(p) for p in re.findall(r"<P>(.*?)</P>", xml, re.S)]

    org = None
    entries = []
    for text in paras:
        m = RE_PARA_LETTER.match(text)
        if m and not RE_ENTRY_NUM.match(text):
            org = text[:120]
        if not is_entry(text):
            continue
        year, reaff, token = edition_year(text)
        urls = RE_URL.findall(text)
        entries.append(
            {
                "text": text,
                "org_header": org,
                "edition_year": year,
                "edition_token": token,
                "reaffirmations": reaff,
                "urls": urls,
                "age": (THIS_YEAR - year) if year else None,
            }
        )

    dated = [e for e in entries if e["edition_year"]]
    undated = [e for e in entries if not e["edition_year"]]
    years = sorted(e["edition_year"] for e in dated)
    median = years[len(years) // 2] if years else None

    print(f"source sha256      : {digest}")
    print(f"paragraphs         : {len(paras)}")
    print(f"C1 entries         : {len(entries)}")
    print(f"   dated           : {len(dated)}")
    print(f"C3 unversioned     : {len(undated)}")
    if years:
        print(f"C2 median edition  : {median}  (age {THIS_YEAR - median})")
        print(f"   oldest / newest : {years[0]} / {years[-1]}")
        le71 = sum(1 for y in years if y <= 1971)
        print(f"C4 <= 1971         : {le71}/{len(years)} = {100*le71/len(years):.1f} %")
        band = sum(1 for y in years if 1943 <= y <= 1979)
        ge90 = sum(1 for y in years if y >= 1990)
        print(f"C5 1943-1979       : {band}/{len(years)} = {100*band/len(years):.1f} %")
        print(f"C5 >= 1990         : {ge90}/{len(years)} = {100*ge90/len(years):.1f} %")
        print("   decades         : " + ", ".join(
            f"{d}s:{n}" for d, n in sorted(Counter((y // 10) * 10 for y in years).items())))
    with_url = [e for e in entries if e["urls"]]
    print(f"C6 entries with any URL : {len(with_url)}")
    for e in with_url[:20]:
        print("   ", e["urls"], "|", e["text"][:110])
    print(f"reaffirmed entries : {sum(1 for e in entries if e['reaffirmations'])}")

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump({"source_sha256": digest, "entries": entries}, open(out, "w"), indent=1)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
