#!/usr/bin/env python3
"""candidates.py — which second records could be asked at all, recorded before choosing.

A page that says *this was the only second record available* owes the reader the list it
chose from and what each one answered. This asks each candidate's front door once, with
an honestly identified research instrument and no attempt to get around a refusal, and
writes down the status line. It decides nothing else: whether a reachable record is a
catalogue of the right kind is a judgement, and the judgement is written in the file
beside the status rather than inferred from it.

    python3 tools/second/candidates.py --out window/cycle-003-session-3/candidates.json

Author: the Atelier. Licence: Apache-2.0 with the repository.
"""

from __future__ import annotations

import argparse
import json
import ssl
import time
import urllib.error
import urllib.request

UA = "ulysses-research/1.0 (artistic research instrument; contact via frankbueltge.de)"

CANDIDATES = [
    {
        "id": "wikidata",
        "name": "Wikidata",
        "url": "https://query.wikidata.org/sparql?query=SELECT%20*%20WHERE%20%7B%3Fs%20"
               "%3Fp%20%3Fo%7D%20LIMIT%201&format=json",
        "holds": "works and people of every kind, community-built, CC0",
        "independent_of_the_atlas": True,
        "machine_readable": True,
        "judgement": (
            "chosen. Its inclusion rule was written before this atlas and without "
            "reference to it, and it is queryable. A 429 in the status line below is "
            "this practice's own doing: the front door was knocked on while the "
            "session's probe was still running against the same endpoint, and the "
            "probe record beside this file is the evidence that it served."
        ),
    },
    {
        "id": "rhizome-artbase",
        "name": "Rhizome ArtBase",
        "url": "https://rhizome.org/art/artbase/",
        "holds": "born-digital art, curated since 1999",
        "independent_of_the_atlas": True,
        "machine_readable": None,
        "judgement": (
            "refused an honestly identified instrument at the front door; not asked "
            "again and nothing worked around."
        ),
    },
    {
        "id": "compart-dada",
        "name": "compart — Database of Digital Art",
        "url": "https://dada.compart-bremen.de/browse/artwork",
        "holds": "digital and algorithmic art, University of Bremen",
        "independent_of_the_atlas": True,
        "machine_readable": None,
        "judgement": "the connection was reset from this machine; not reachable here.",
    },
    {
        "id": "medienkunstnetz",
        "name": "Medien Kunst Netz / Media Art Net",
        "url": "https://www.medienkunstnetz.de/works/",
        "holds": "media art, ZKM and Goethe-Institut",
        "independent_of_the_atlas": True,
        "machine_readable": None,
        "judgement": "the connection was reset from this machine; not reachable here.",
    },
    {
        "id": "ars-electronica-archive",
        "name": "Ars Electronica Prix archive",
        "url": "https://archive.aec.at/prix/",
        "holds": "works distinguished by one prize, 1987 onwards",
        "independent_of_the_atlas": True,
        "machine_readable": None,
        "judgement": (
            "reachable, and not a candidate on the merits: it is the record of one "
            "prize's distinctions, so its inclusion rule is a jury's and its "
            "population is not data art. Left unasked rather than mined."
        ),
    },
]


def probe_one(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            return {
                "status": fh.status,
                "content_type": fh.headers.get("Content-Type"),
                "seconds": round(time.time() - t0, 2),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": exc.code,
            "content_type": exc.headers.get("Content-Type") if exc.headers else None,
            "seconds": round(time.time() - t0, 2),
            "error": f"HTTP {exc.code}",
        }
    except (urllib.error.URLError, ssl.SSLError, OSError) as exc:
        return {
            "status": None,
            "content_type": None,
            "seconds": round(time.time() - t0, 2),
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = []
    for c in CANDIDATES:
        res = probe_one(c["url"])
        rows.append({**c, "probe": res})
        print(f"{res['status']}  {c['name']}")
        time.sleep(1.5)
    out = {
        "probed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": (
            "one GET per candidate front door, User-Agent naming this instrument, no "
            "retry and no attempt to get around a refusal"
        ),
        "candidates": rows,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
