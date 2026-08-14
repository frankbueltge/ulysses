#!/usr/bin/env python3
"""Extract every web address printed in the CFR's incorporation-by-reference sections.

Rules E1-E6 are fixed in PREREGISTRATION-01.md and were written before this file ran.
This script issues no probe: it fetches the section text, extracts, normalises and
classifies, and freezes the result. The probe (probe_urls.py) reads that frozen file.
That order is the blind step.

Usage: python3 extract_urls.py --sections sections.json --out data/urls.json
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time

# E2: an explicit scheme, or a bare www. address (how most of these sections print them).
RE_URL = re.compile(r"https?://[^\s<>\"')\]]+")
RE_WWW = re.compile(r"(?<![\w.@/-])www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s<>\"')\]]*)?")
# E3: trailing punctuation that belongs to the sentence, not the address.
RE_TRAIL = re.compile(r"[.,;:]+$")
TAG = re.compile(r"<[^>]+>")


def section_xml(title: int, section: str, date: str) -> bytes | None:
    url = (f"https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title}.xml"
           f"?section={section}")
    out = subprocess.run(["curl", "-s", "--max-time", "120", url], capture_output=True)
    if not out.stdout or b"<" not in out.stdout[:200]:
        return None
    return out.stdout


def flatten(xml: bytes) -> str:
    text = TAG.sub(" ", xml.decode("utf-8", "replace"))
    text = text.replace("&amp;", "&").replace("&#xA7;", "§")
    return re.sub(r"\s+", " ", text)


def strip_tail(raw: str) -> str:
    """E3: trailing punctuation and unbalanced closing brackets."""
    out = raw
    while True:
        stripped = RE_TRAIL.sub("", out)
        if stripped and stripped[-1] in ")]}" and stripped.count("(") < stripped.count(")"):
            stripped = stripped[:-1]
        elif stripped and stripped[-1] in "]}" and stripped.count("[") < stripped.count("]"):
            stripped = stripped[:-1]
        if stripped == out:
            return out
        out = stripped


def normalise(raw: str) -> str | None:
    """E4: the form two printed addresses are compared in."""
    url = strip_tail(raw)
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    match = re.match(r"(?i)^(https?)://([^/?#]+)([^#]*)", url)
    if not match:
        return None
    scheme, host, rest = match.group(1).lower(), match.group(2).lower(), match.group(3)
    if "." not in host.split(":")[0]:
        return None
    if rest in ("", "/"):
        rest = ""
    return f"{scheme}://{host}{rest}"


def host_class(url: str) -> str:
    """E5: assigned from the hostname alone, before any probe."""
    host = re.sub(r"(?i)^https?://", "", url).split("/")[0].split(":")[0]
    return "federal" if host.endswith((".gov", ".mil")) else "other"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", default="sections.json")
    ap.add_argument("--date", default="2026-08-11")
    ap.add_argument("--out", default="data/urls.json")
    args = ap.parse_args()

    corpus = json.load(open(args.sections))
    rows = corpus["sections"]
    manifest, occurrences, unreachable = [], [], []

    for i, sec in enumerate(rows, 1):
        xml = section_xml(sec["title"], sec["section"], args.date)
        if xml is None:
            unreachable.append(f"{sec['title']} CFR {sec['section']}")
            print(f"[{i}/{len(rows)}] {sec['title']} CFR {sec['section']}: UNREACHABLE",
                  file=sys.stderr)
            time.sleep(0.4)
            continue
        text = flatten(xml)
        found = []
        for raw in RE_URL.findall(text) + RE_WWW.findall(text):
            url = normalise(raw)
            if url:
                found.append({"printed": strip_tail(raw), "url": url})
        manifest.append({
            "title": sec["title"], "section": sec["section"],
            "sha256": hashlib.sha256(xml).hexdigest(), "bytes": len(xml),
            "chars_text": len(text), "urls": len(found),
        })
        for f in found:
            occurrences.append({"title": sec["title"], "section": sec["section"], **f})
        print(f"[{i}/{len(rows)}] {sec['title']} CFR {sec['section']}: {len(found)} urls",
              flush=True)
        time.sleep(0.4)

    distinct: dict[str, dict] = {}
    for occ in occurrences:
        entry = distinct.setdefault(occ["url"], {
            "url": occ["url"], "host_class": host_class(occ["url"]),
            "host": re.sub(r"(?i)^https?://", "", occ["url"]).split("/")[0],
            "sections": [], "printed_forms": [],
        })
        label = f"{occ['title']} CFR {occ['section']}"
        if label not in entry["sections"]:
            entry["sections"].append(label)
        if occ["printed"] not in entry["printed_forms"]:
            entry["printed_forms"].append(occ["printed"])

    out = {
        "issue_date": args.date,
        "extracted": "2026-08-14",
        "sections_requested": len(rows),
        "sections_fetched": len(manifest),
        "sections_unreachable": unreachable,
        "occurrences": len(occurrences),
        "distinct": len(distinct),
        "federal": sum(1 for d in distinct.values() if d["host_class"] == "federal"),
        "other": sum(1 for d in distinct.values() if d["host_class"] == "other"),
        "manifest": manifest,
        "urls": sorted(distinct.values(), key=lambda d: d["url"]),
        "occurrence_list": occurrences,
    }
    json.dump(out, open(args.out, "w"), indent=1)
    print(f"\nsections fetched {len(manifest)}/{len(rows)} · occurrences {len(occurrences)} · "
          f"distinct {out['distinct']} (federal {out['federal']} / other {out['other']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
