#!/usr/bin/env python3
"""Post-hoc verification — is the file that comes back *this* corrigendum?

**Not pre-registered, not scored.** Written after the five clauses were settled, because scoring
turned up two things the clauses were not built to see:

1. **71 of 179 items are byte-identical to another item** (137 distinct sha256 over 179 items).
   The register hands one file back under several different CELEX addresses.
2. **The text layer is offset.** These PDFs carry subset fonts whose glyph codes sit 29 below the
   characters they stand for, so a naive extractor reports a shifted alphabet. The character
   *count* behind clause C1 is unaffected; what a reader reads is not English until the shift is
   undone.

This pass re-fetches every item, undoes the shift, and asks a plain question of each served file:
does it name the act its own CELEX names?

**What this instrument cannot do, stated before its numbers are read.** `readable.extract_text`
decodes `FlateDecode` content streams only and reads literal and hex strings between `BT`/`ET`.
It recovers 1,430 characters from a 140,799-byte scan — a fraction of the page. A **positive**
here (the number is found) is therefore solid; a **negative is not evidence of absence**, only
that the recovered fragment does not carry it. Every count below is reported in that asymmetry.
"""

import json
import pathlib
import re
import time
import urllib.request

from readable import extract_text

HERE = pathlib.Path(__file__).resolve().parent
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"
PAGE = re.compile(rb"/Type\s*/Page[^s]")


def unshift(text: str, k: int = 29) -> str:
    """Undo the subset-font offset. Every code is shifted, digits included.

    An earlier version of this function shifted only codes already in the printable range, which
    silently dropped every digit — the glyph for `1` is code 0x14, below the range that version
    tested. It made the substantive check answer `false` for every row, and it did, until it was
    found by reading the raw output instead of the summary. The defect is recorded rather than
    quietly repaired.
    """
    out = []
    for ch in text:
        code = ord(ch)
        if code == 0:                          # high byte of a two-byte glyph code
            continue
        shifted = code + k
        out.append(chr(shifted) if 32 <= shifted < 127 else ch)
    return "".join(out)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as fh:
                return fh.read()
        except Exception:                      # noqa: BLE001 — retried, then given up on
            if attempt == 2:
                return b""
            time.sleep(4 * (attempt + 1))
    return b""


def act_number(celex: str) -> str:
    """`31992L0012R(05)` -> `12`, the sequence number of the act being corrected."""
    m = re.match(r"^\d(\d{4})[A-Z](\d{4})R\(\d+\)$", celex)
    return m.group(2).lstrip("0") if m else ""


def act_year(celex: str) -> str:
    m = re.match(r"^\d(\d{4})[A-Z]\d{4}R\(\d+\)$", celex)
    return m.group(1)[2:] if m else ""


def main() -> None:
    records = [r for r in json.loads((HERE / "items.json").read_text())["records"] if r["present"]]
    rows = []
    for n, rec in enumerate(records, 1):
        body = fetch(rec["url"])
        text = unshift(extract_text(body))
        digits = re.sub(r"\D", "", text)
        seq, year = act_number(rec["celex"]), act_year(rec["celex"])
        rows.append({
            "celex": rec["celex"],
            "sha256": rec["no_accept"]["sha256"],
            "bytes": len(body),
            "pdf_pages": len(PAGE.findall(body)),
            "chars_recovered": len(text),
            "act": f"{seq}/{year}",
            # The Journal prints a regulation as "No 1600/95" and a directive as "94/11/EC" —
            # sequence-then-year in one case, year-then-sequence in the other. An earlier version
            # of this check tested only the first order and would have scored every corrected
            # directive as a miss. Both orders are tested; a hit under either counts.
            "act_number_in_recovered_text": bool(
                seq and (f"{seq}{year}" in digits or f"{year}{seq}" in digits)),
            "corrigendum_headings_recovered": len(re.findall(r"Corrigendumto", text)),
        })
        if n % 40 == 0:
            print(f"  verified {n}/{len(records)}", flush=True)

    shared = {}
    for r in rows:
        shared.setdefault(r["sha256"], []).append(r["celex"])
    groups = {h: cs for h, cs in shared.items() if len(cs) > 1}

    found = sum(1 for r in rows if r["act_number_in_recovered_text"])
    out = {
        "note": "post-hoc; not pre-registered, not scored; a negative is not evidence of absence",
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "items": len(rows),
        "distinct_payloads": len(shared),
        "items_sharing_a_payload": sum(len(cs) for cs in groups.values()),
        "largest_group": max((len(cs) for cs in groups.values()), default=0),
        "act_number_found_in_recovered_text": found,
        "median_pages": sorted(r["pdf_pages"] for r in rows)[len(rows) // 2],
        "median_chars_recovered": sorted(r["chars_recovered"] for r in rows)[len(rows) // 2],
        "shared_payload_groups": {h: sorted(cs) for h, cs in sorted(groups.items())},
        "rows": sorted(rows, key=lambda r: r["celex"]),
    }
    (HERE / "verification.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    for k in ("items", "distinct_payloads", "items_sharing_a_payload", "largest_group",
              "act_number_found_in_recovered_text", "median_pages", "median_chars_recovered"):
        print(k, "=", out[k])


if __name__ == "__main__":
    main()
