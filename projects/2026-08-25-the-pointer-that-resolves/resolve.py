#!/usr/bin/env python3
"""Two measurements on the reference corrections selected by parse_pairs.py.

**A — does the wrong pointer resolve?** For every (year, number) a corrigendum removed,
the register is asked whether any legal act of CELEX sector 3 carries that year and that
number. This is the reader's own act: they hold a number and look it up. A wrong number
that resolves is a pointer that *works* and lands somewhere else; a wrong number that
resolves to nothing is caught by the first person who follows it.

**B — did the fix travel into the act?** The corrected act's own current text is fetched
from the Publications Office and read for the two numbers: the erroneous one the
corrigendum removed, and the corrected one it put in. An act still printing the erroneous
number is an act whose correction lives only outside it.

Both measurements are made after the selection step in parse_pairs.py, which never saw
either. Standard library only; every request recorded.
"""

import hashlib
import html
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ACTS = HERE / "acts"
SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
CELLAR = "http://publications.europa.eu/resource/celex/"
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"

sys.path.insert(0, str(HERE))
from parse_pairs import tokens, to_text  # noqa: E402  the same reader, both sides


def get(url: str, headers: dict, timeout: int = 180) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            return fh.status, fh.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:  # noqa: BLE001
        return 0, b""


def sparql(query: str, tries: int = 5) -> list[dict]:
    """The endpoint answers 503 under load; a refusal to answer is not an answer, so this
    retries with backoff and gives up loudly rather than recording an empty result."""
    url = SPARQL + "?" + urllib.parse.urlencode(
        {"query": query, "format": "application/sparql-results+json"}
    )
    for attempt in range(tries):
        status, body = get(url, {"User-Agent": UA}, timeout=600)
        if status == 200:
            return json.loads(body)["results"]["bindings"]
        wait = 4 * (attempt + 1)
        print(f"    endpoint returned {status}; retry in {wait}s", flush=True)
        time.sleep(wait)
    raise SystemExit(f"SPARQL endpoint refused {tries} times (last status {status})")


def resolve_tokens(toks: list[tuple[str, str]]) -> dict[str, list[str]]:
    """(year, number) -> every sector-3 CELEX carrying it. Asked in batches of 40."""
    found: dict[str, list[str]] = {f"{y}/{n}": [] for y, n in toks}
    for i in range(0, len(toks), 12):
        batch = toks[i:i + 12]
        values = " ".join(f'("{y}" "{n}")' for y, n in batch)
        q = f"""
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?y ?n ?celex WHERE {{
  VALUES (?y ?n) {{ {values} }}
  ?w cdm:resource_legal_year ?yy ;
     cdm:resource_legal_number_natural_celex ?nn ;
     cdm:resource_legal_id_celex ?celex .
  FILTER(STR(?yy) = ?y) FILTER(STR(?nn) = ?n)
  FILTER(STRSTARTS(STR(?celex),"3"))
}}
"""
        for row in sparql(q):
            key = f"{row['y']['value']}/{row['n']['value']}"
            celex = row["celex"]["value"]
            if celex not in found[key]:
                found[key].append(celex)
        print(f"  resolved {min(i + 12, len(toks))}/{len(toks)}", flush=True)
        time.sleep(0.5)
    return found


def act_text(celex: str) -> tuple[int, str, str | None]:
    """The act's own current English text, cached under acts/."""
    path = ACTS / (celex.replace("/", "_") + ".html")
    if path.exists():
        raw = path.read_bytes()
        return 200, to_text(raw.decode("utf-8", "replace")), hashlib.sha256(raw).hexdigest()
    status, raw = get(
        CELLAR + urllib.parse.quote(celex, safe=""),
        {"User-Agent": UA, "Accept": "application/xhtml+xml", "Accept-Language": "eng"},
    )
    time.sleep(0.4)
    if status != 200 or not raw:
        return status, "", None
    path.write_bytes(raw)
    return 200, to_text(raw.decode("utf-8", "replace")), hashlib.sha256(raw).hexdigest()


def main() -> None:
    ACTS.mkdir(exist_ok=True)
    pairs = json.loads((HERE / "pairs.json").read_text(encoding="utf-8"))

    # ---- the selected set: every reference correction, with its base act -------------
    selected = []
    for rec in pairs["records"]:
        for p in rec["pairs"]:
            if not p["reference_correction"]:
                continue
            for wrong in p["erroneous_tokens"]:
                selected.append(
                    {
                        "corrigendum": rec["celex"],
                        "date": rec["date"],
                        "corrects": rec["corrects"],
                        "locus": p["locus"],
                        "for": p["for"][:300],
                        "read": p["read"][:300],
                        "wrong": tuple(wrong),
                        "read_tokens": [tuple(t) for t in p["read_tokens"]],
                    }
                )
    print(f"selected reference corrections: {len(selected)}")

    # ---- A: does the wrong pointer resolve? ------------------------------------------
    uniq = sorted({s["wrong"] for s in selected})
    print(f"distinct erroneous numbers: {len(uniq)}")
    resolved = resolve_tokens([tuple(t) for t in uniq])

    # ---- B: did the fix travel into the act? -----------------------------------------
    bases = sorted({b for s in selected for b in s["corrects"]})
    print(f"corrected acts to read: {len(bases)}")
    act_tok: dict[str, dict] = {}
    for i, celex in enumerate(bases, 1):
        status, text, sha = act_text(celex)
        act_tok[celex] = {
            "http_status": status,
            "sha256": sha,
            "tokens": sorted(tokens(text)) if text else None,
        }
        if i % 25 == 0:
            print(f"  read {i}/{len(bases)}", flush=True)

    # ---- join --------------------------------------------------------------------
    rows = []
    for s in selected:
        key = f"{s['wrong'][0]}/{s['wrong'][1]}"
        hits = resolved.get(key, [])
        row = {
            "corrigendum": s["corrigendum"],
            "date": s["date"],
            "corrects": s["corrects"],
            "locus": s["locus"],
            "for": s["for"],
            "read": s["read"],
            "wrong_number": key,
            "wrong_resolves_to": hits,
            "wrong_pointer_is_live": bool(hits),
            "in_enacting_terms": bool(re.search(r"\bArticle", s["locus"], re.I)),
        }
        # B is only answerable where the act was readable
        travelled = []
        for b in s["corrects"]:
            info = act_tok.get(b, {})
            toks = info.get("tokens")
            if toks is None:
                travelled.append({"act": b, "readable": False, "http_status": info.get("http_status")})
                continue
            tset = {tuple(t) for t in toks}
            travelled.append(
                {
                    "act": b,
                    "readable": True,
                    "sha256": info.get("sha256"),
                    "still_names_wrong": tuple(s["wrong"]) in tset,
                    "names_corrected": any(t in tset for t in [tuple(x) for x in s["read_tokens"]]),
                }
            )
        row["corrected_act"] = travelled
        rows.append(row)

    out = {
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sparql_endpoint": SPARQL,
        "document_route": CELLAR + "<celex>  (Accept: application/xhtml+xml; Accept-Language: eng)",
        "selected_reference_corrections": len(rows),
        "distinct_erroneous_numbers": len(uniq),
        "rows": rows,
    }
    (HERE / "measurement.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    live = sum(1 for r in rows if r["wrong_pointer_is_live"])
    print(f"\nA  wrong pointers that resolve to a real act : {live}/{len(rows)}")
    read_ok = [t for r in rows for t in r["corrected_act"] if t["readable"]]
    still = sum(1 for t in read_ok if t["still_names_wrong"])
    print(f"B  corrected acts still naming the wrong one : {still}/{len(read_ok)}")


if __name__ == "__main__":
    main()
