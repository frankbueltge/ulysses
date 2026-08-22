#!/usr/bin/env python3
"""Join the landed censuses — and one reading of the governing part — into one route file.

Nothing here fetches anything. Seven inputs are files already committed by a closed
study; the eighth, `data/part51.json`, is this project's own reading of 1 CFR part 51,
committed with the raw bytes it was read from. Every input's sha256 is written into the
output so a reader can check that the page was built from the record and not from a
retelling of it.

    python3 build_route.py

Inputs (all relative to this file):
  ../2026-08-14-the-addresses-the-law-prints/sections.json      the 290 sections
  ../2026-08-14-the-addresses-the-law-prints/data/urls.json     the 306 addresses, frozen pre-probe
  ../2026-08-14-the-addresses-the-law-prints/data/probe.json    what each address answered
  ../2026-08-16-the-copy-of-last-resort/data/cdx.json           what the public archive holds
  ../2026-08-17-the-warrant-under-the-section/data/warrants.json the citation under each section
  ../2026-08-18-when-the-law-reopens-the-page/data/moves.json    nine years of amendments
  ../2026-08-18-when-the-law-reopens-the-page/data/rescore.json  the hand-check that corrected them
  data/part51.json                                               1 CFR part 51, read 2026-08-22

Output: window/route.json

On rescore.json: the parser behind moves.json read a fax number and a street address as
edition years in two sections, and the study's owed hand-check removed both from the arm
before it scored. The published figures are the corrected ones (41 of 67, not 42 of 69), so
this build reads the correction out of the study's own file rather than re-deriving it or
quietly reproducing the raw count.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent

# The day the addresses were asked, and the day the archive was queried. Ages are
# measured from the archive query, exactly as the study that produced them measured.
PROBE_DATE = "2026-08-14"
CDX_DATE = "2026-08-16"

SOURCES = {
    "sections": "../2026-08-14-the-addresses-the-law-prints/sections.json",
    "urls": "../2026-08-14-the-addresses-the-law-prints/data/urls.json",
    "probe": "../2026-08-14-the-addresses-the-law-prints/data/probe.json",
    "cdx": "../2026-08-16-the-copy-of-last-resort/data/cdx.json",
    "warrants": "../2026-08-17-the-warrant-under-the-section/data/warrants.json",
    "moves": "../2026-08-18-when-the-law-reopens-the-page/data/moves.json",
    "rescore": "../2026-08-18-when-the-law-reopens-the-page/data/rescore.json",
    # The one input no closed study produced: 1 CFR part 51 read on 2026-08-22 by
    # `read_part51.py`, to answer what the six censuses could not. Committed with the raw
    # bytes beside it and hashed here like every other source.
    "part51": "data/part51.json",
}


def load(rel: str) -> tuple[dict, str]:
    path = (HERE / rel).resolve()
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def days_between(stamp: str, until: str) -> int | None:
    """CDX timestamps are YYYYMMDDhhmmss. Age in whole days, as the study counted it."""
    if not stamp or len(stamp) < 8:
        return None
    y, m, d = int(stamp[0:4]), int(stamp[4:6]), int(stamp[6:8])
    return (date.fromisoformat(until) - date(y, m, d)).days


def section_key(title: int | str, section: str) -> str:
    return f"{title} CFR {section}"


def main() -> None:
    data, shas = {}, {}
    for name, rel in SOURCES.items():
        data[name], shas[name] = load(rel)

    # ---- sections: the warrant under each, and what nine years of amendments did ----
    warrants = {section_key(r["title"], r["section"]): r for r in data["warrants"]["records"]}
    moves = {section_key(r["title"], r["section"]): r for r in data["moves"]["records"]}
    # The two sections the study's hand-check pulled out of the arm, by its own record.
    artefacts = {a["section"] for a in data["rescore"]["artefacts_removed"]}

    sections: dict[str, dict] = {}
    for s in data["sections"]["sections"]:
        key = section_key(s["title"], s["section"])
        w = warrants.get(key, {})
        m = moves.get(key, {})
        sections[key] = {
            "t": s["title"],
            "s": s["section"],
            "h": s.get("heading", ""),
            # the citation the law prints under the section, and where it was found
            "cita": w.get("cita_text") or None,
            "wy": w.get("warrant_year"),
            "wpath": w.get("warrant_path"),
            # No citation of its own: the note a reader meets is the one printed above the
            # section, in a `<SOURCE>` element ending "unless otherwise noted". 76 sections.
            # (warrants.json's own `offloaded` flag is a different, smaller category — the
            # four sections deferring to the List of Sections Affected — and is not used here.)
            "nocita": not w.get("has_cita", True),
            "ney": w.get("newest_edition_year"),      # newest edition the section binds
            "gap": w.get("gap"),
            "crosses": bool(w.get("crosses")),
            # nine years of amendments (2017-01-01 -> 2026-08-11)
            "amend": m.get("n_amendments_since_2017"),
            "reopened": m.get("reopened"),
            "last_amend": m.get("last_amendment"),
            # None where the section is not readable at both ends, and None for the two
            # sections the hand-check pulled out as parser artefacts.
            "moved": None if key in artefacts else m.get("moved"),
            "delta": None if key in artefacts else m.get("delta"),
            "handcheck_removed": key in artefacts,
        }

    # ---- addresses: what the law prints, and what it answered ----
    printed_forms = {u["url"]: u.get("printed_forms", []) for u in data["urls"]["urls"]}
    occurrences: dict[str, int] = {}
    for occ in data["urls"]["occurrence_list"]:
        occurrences[occ["url"]] = occurrences.get(occ["url"], 0) + 1

    archive = {r["url"]: r for r in data["cdx"]["results"]}

    addresses = []
    for r in data["probe"]["results"]:
        url = r["url"]
        a = archive.get(url)
        arch = None
        if a is not None:
            last200 = (a.get("last_200") or {}).get("timestamp")
            lastany = (a.get("last_any") or {}).get("timestamp")
            arch = {
                "arm": a.get("arm"),
                "depth": a.get("depth"),
                "q_err": a.get("query_error"),
                "last200": last200,
                "age": days_between(last200, CDX_DATE) if last200 else None,
                "lastany": lastany,
            }
        first, second = r.get("first") or {}, r.get("second") or {}
        addresses.append({
            "u": url,
            "printed": printed_forms.get(url, [url]),
            "host": r["host"],
            "cls": r["host_class"],
            "out": r["outcome"],
            "s1": first.get("status"),
            "e1": first.get("curl_error"),
            "s2": second.get("status") if second else None,
            "e2": second.get("curl_error") if second else None,
            "final": first.get("final"),
            "occ": occurrences.get(url, 0),
            "secs": r["sections"],
            "arch": arch,
        })

    # ---- the tallies the page shows, all recomputed here, none copied from prose ----
    by_outcome: dict[str, int] = {}
    for a in addresses:
        by_outcome[a["out"]] = by_outcome.get(a["out"], 0) + 1
    gives = by_outcome.get("2xx", 0)

    printing = sorted({s for a in addresses for s in a["secs"]})
    reopened = [k for k, v in sections.items() if v["reopened"]]
    scorable = [v for v in sections.values() if v["moved"] is not None]
    stayed = [v for v in scorable if v["moved"] is False]

    out = {
        "built": str(date.today()),
        "issue_date": data["urls"]["issue_date"],
        "probe_date": PROBE_DATE,
        "cdx_date": CDX_DATE,
        "before_date": data["moves"]["before_date"],
        "after_date": data["moves"]["after_date"],
        "sources": {name: {"path": rel, "sha256": shas[name]} for name, rel in SOURCES.items()},
        "totals": {
            "sections": len(sections),
            "sections_printing": len(printing),
            "addresses": len(addresses),
            "occurrences": data["urls"]["occurrences"],
            "hosts": len({a["host"] for a in addresses}),
            "federal": sum(1 for a in addresses if a["cls"] == "federal"),
            "by_outcome": by_outcome,
            "gives": gives,
            "amendments": sum(v["amend"] or 0 for v in sections.values()),
            "reopened": len(reopened),
            "scorable": len(scorable),
            "stayed": len(stayed),
        },
        "sections": sections,
        "addresses": addresses,
        # The part that governs all of the above, read as a document rather than as a rule:
        # what it says about the thing its sections print, and the two clocks it does set.
        "part51": data["part51"],
    }

    dest = HERE / "window" / "route.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    t = out["totals"]
    print(f"route.json  {dest.stat().st_size:,} bytes")
    print(f"  {t['sections']} sections, {t['sections_printing']} of them printing an address")
    print(f"  {t['addresses']} addresses, {t['occurrences']} printed occurrences, {t['hosts']} hosts")
    print(f"  outcomes: {t['by_outcome']}")
    print(f"  {t['amendments']} amendments since {out['before_date']}, {t['reopened']} sections reopened")
    print(f"  of {t['scorable']} readable at both ends, {t['stayed']} left the edition where it was")


if __name__ == "__main__":
    main()
