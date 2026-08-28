#!/usr/bin/env python3
"""The two measurements of 2026-08-25, run on tonight's population.

Everything that reads or judges is imported from
`../2026-08-25-the-pointer-that-resolves/resolve.py` and `parse_pairs.py` — the SPARQL
resolution of an erroneous number, the token reader, the text stripper. **One thing is
changed, and it is the night's own subject:** the corrected act's text is fetched with a
fallback from `application/xhtml+xml` to `text/html`.

Fetching a pre-2004 act with the first route alone returns 404, which is the defect this
project measures. Using the unchanged fetcher here would have produced a small `M`, a VOID
H2', and a number that was an artefact of the same header for the second time in four days.
Which route answered is recorded per act.

Standard library only.
"""

import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
PRIOR_DIR = HERE.parent / "2026-08-25-the-pointer-that-resolves"
sys.path.insert(0, str(PRIOR_DIR))
from parse_pairs import to_text, tokens  # noqa: E402
from resolve import CELLAR, SPARQL, UA, get, resolve_tokens  # noqa: E402

ACTS = HERE / "acts"
ROUTES = ("application/xhtml+xml", "text/html")


def act_text(celex: str) -> tuple[int, str, str | None, str | None]:
    """The act's own current English text, by whichever route answers first."""
    for route in ROUTES:
        cached = ACTS / f"{urllib.parse.quote(celex, safe='')}.{route.split('/')[-1]}"
        if cached.exists():
            raw = cached.read_bytes()
            return 200, to_text(raw.decode("utf-8", "replace")), \
                hashlib.sha256(raw).hexdigest(), route
        status, raw = get(CELLAR + urllib.parse.quote(celex, safe=""),
                          {"User-Agent": UA, "Accept": route, "Accept-Language": "eng"})
        time.sleep(0.3)
        if status == 200 and raw:
            cached.write_bytes(raw)
            return 200, to_text(raw.decode("utf-8", "replace")), \
                hashlib.sha256(raw).hexdigest(), route
        last = status
    return last, "", None, None


def main() -> None:
    ACTS.mkdir(exist_ok=True)
    pairs = json.loads((HERE / "pairs.json").read_text(encoding="utf-8"))

    selected = []
    for rec in pairs["records"]:
        for p in rec["pairs"]:
            if not p["reference_correction"]:
                continue
            for wrong in p["erroneous_tokens"]:
                selected.append({
                    "corrigendum": rec["celex"], "date": rec["date"],
                    "corrects": rec["corrects"], "locus": p["locus"],
                    "for": p["for"][:300], "read": p["read"][:300],
                    "wrong": tuple(wrong),
                    "read_tokens": [tuple(t) for t in p["read_tokens"]],
                })
    print(f"selected reference corrections: {len(selected)}", flush=True)

    uniq = sorted({s["wrong"] for s in selected})
    print(f"distinct erroneous numbers: {len(uniq)}", flush=True)
    resolved = resolve_tokens([tuple(t) for t in uniq])

    bases = sorted({b for s in selected for b in s["corrects"]})
    print(f"corrected acts to read: {len(bases)}", flush=True)
    act_tok: dict[str, dict] = {}
    for i, celex in enumerate(bases, 1):
        status, text, sha, route = act_text(celex)
        act_tok[celex] = {"http_status": status, "sha256": sha, "route": route,
                          "tokens": sorted(tokens(text)) if text else None}
        if i % 25 == 0:
            print(f"  read {i}/{len(bases)}", flush=True)

    rows = []
    for s in selected:
        key = f"{s['wrong'][0]}/{s['wrong'][1]}"
        hits = resolved.get(key, [])
        travelled = []
        for b in s["corrects"]:
            info = act_tok.get(b, {})
            toks = info.get("tokens")
            if toks is None:
                travelled.append({"act": b, "readable": False,
                                  "http_status": info.get("http_status")})
                continue
            tset = {tuple(t) for t in toks}
            travelled.append({
                "act": b, "readable": True, "sha256": info.get("sha256"),
                "route": info.get("route"),
                "still_names_wrong": tuple(s["wrong"]) in tset,
                "names_corrected": any(tuple(x) in tset for x in s["read_tokens"]),
            })
        rows.append({
            "corrigendum": s["corrigendum"], "date": s["date"], "corrects": s["corrects"],
            "locus": s["locus"], "for": s["for"], "read": s["read"],
            "wrong_number": key, "wrong_resolves_to": hits,
            "wrong_pointer_is_live": bool(hits),
            "in_enacting_terms": bool(re.search(r"\bArticle", s["locus"], re.I)),
            "corrected_act": travelled,
        })

    out = {
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sparql_endpoint": SPARQL,
        "document_route": CELLAR + "<celex>  (Accept: application/xhtml+xml, then text/html)",
        "population": "the 1,559 corrigenda served only by the second route",
        "selected_reference_corrections": len(rows),
        "distinct_erroneous_numbers": len(uniq),
        "rows": rows,
    }
    (HERE / "measurement.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                           encoding="utf-8")

    live = sum(1 for r in rows if r["wrong_pointer_is_live"])
    print(f"\nA  wrong pointers that resolve to a real act : {live}/{len(rows)}")
    read_ok = [t for r in rows for t in r["corrected_act"] if t["readable"]]
    still = sum(1 for t in read_ok if t["still_names_wrong"])
    print(f"B  corrected acts still naming the wrong one : {still}/{len(read_ok)}")


if __name__ == "__main__":
    main()
