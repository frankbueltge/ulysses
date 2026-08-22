#!/usr/bin/env python3
"""Read 1 CFR part 51 itself, and count what it says about addresses.

Every other input to this page was committed by a closed census. This one is not: it
is a reading made on 2026-08-22, of the primary the page already quotes, to answer the
one question a cold reader asked that the page could not answer — *when an address in
the CFR goes dead, is anyone obliged to notice?*

Part 51 is the part that governs incorporation by reference and sets the condition the
whole work turns on. It is 10 KB. The reading is a term count and two quotations, and
anyone can repeat it from the URL below in one request.

    python3 read_part51.py

Writes `data/part51-raw.xml` (the bytes as fetched) and `data/part51.json` (the reading,
with the raw file's sha256 in it). Fetches once; re-run only to re-date the reading.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

ISSUE_DATE = "2026-08-11"   # the same eCFR issue date the census was enumerated from
URL = f"https://www.ecfr.gov/api/versioner/v1/full/{ISSUE_DATE}/title-1.xml?part=51"

# The words a regulation would have to use to say anything about the thing its sections
# actually print. Counted case-insensitively over the whole part.
TERMS = ["address", "URL", "uniform resource", "internet", "website", "web site",
         "online", "hyperlink", "link", "web page", "webpage"]


def flatten(xml: str) -> str:
    text = re.sub(r"<[^>]+>", "", xml)
    text = html.unescape(text)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


def sentence_at(text: str, marker: str) -> str:
    """The paragraph beginning at `marker`, up to the next paragraph letter or section."""
    i = text.index(marker)
    rest = text[i:]
    end = re.search(r"\n|\s\([a-z]\)\s", rest[len(marker):])
    return re.sub(r"\s+", " ", (rest[:len(marker) + end.start()] if end else rest[:600])).strip()


def main() -> None:
    DATA.mkdir(exist_ok=True)
    raw_path, out_path = DATA / "part51-raw.xml", DATA / "part51.json"

    if raw_path.exists():
        raw = raw_path.read_bytes()
        fetched = json.loads(out_path.read_text())["fetched"] if out_path.exists() else None
    else:
        with urllib.request.urlopen(URL, timeout=60) as r:
            raw = r.read()
        raw_path.write_bytes(raw)
        fetched = None
    fetched = fetched or str(date.today())

    text = flatten(raw.decode("utf-8"))
    counts = {t: len(re.findall(re.escape(t), text, re.I)) for t in TERMS}

    # The two duties part 51 does impose once an incorporation is in force. Quoted so the
    # reading can be checked against the part rather than believed.
    removal = sentence_at(text, "(b) If a regulation containing an incorporation by reference")
    change = sentence_at(text, "(a) An agency that seeks approval for a change to a publication")
    condition = sentence_at(text, "(a) Section 552(a) of title 5")
    # The one duty in the part that touches how a reader is to get the material at all.
    # It is a duty on the preamble of the final rule: discharged at the incorporation.
    obtain = sentence_at(text, "(2) Discuss, in the preamble of the final rule")

    for label, quote in (("removal", removal), ("change", change),
                         ("condition", condition), ("obtain", obtain)):
        if len(quote) < 60:
            raise SystemExit(f"{label}: quotation did not parse — {quote!r}")

    out = {
        "part": "1 CFR part 51",
        "url": URL,
        "issue_date": ISSUE_DATE,
        "fetched": fetched,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "words": len(text.split()),
        "sections": sorted(set(re.findall(r"§ (51\.\d+)", text))),
        "terms": counts,
        "terms_total": sum(counts.values()),
        "removal_clause": removal,
        "change_clause": change,
        "condition_clause": condition,
        "obtain_clause": obtain,
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"1 CFR part 51 — {out['bytes']:,} bytes, {out['words']:,} words, "
          f"{len(out['sections'])} sections")
    print(f"  sha256 {out['sha256']}")
    for t, n in counts.items():
        print(f"  {t!r:20} {n}")
    print(f"  total: {out['terms_total']}")


if __name__ == "__main__":
    main()
