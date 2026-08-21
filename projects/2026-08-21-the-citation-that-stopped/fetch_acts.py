#!/usr/bin/env python3
"""Enumerate and fetch the Official Journal's harmonised-standards acts.

Two steps, both against primary sources and both recorded:

1. The EU Publications Office SPARQL endpoint (Cellar) is asked for every legal act of
   CELEX sector 3, document date >= 2018-01-01, whose English title contains
   "harmonised standards".
2. Each act's English HTML is fetched from EUR-Lex and stored verbatim under corpus/,
   with its sha256, byte count and HTTP status in manifest.json.

Nothing is parsed here. Standard library only.
"""

import hashlib
import json
import pathlib
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CORPUS = HERE / "corpus"
SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
EURLEX = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:"
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"

QUERY = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?celex ?date ?title WHERE {
  ?work cdm:resource_legal_id_celex ?celex .
  ?work cdm:work_date_document ?date .
  ?exp cdm:expression_belongs_to_work ?work ;
       cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> ;
       cdm:expression_title ?title .
  FILTER(STRSTARTS(STR(?celex),"3"))
  FILTER(?date >= "2018-01-01"^^<http://www.w3.org/2001/XMLSchema#date>)
  FILTER(CONTAINS(LCASE(STR(?title)), "harmonised standards"))
}
ORDER BY ?date
"""


def get(url: str, timeout: int = 120) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            return fh.status, fh.read()
    except urllib.error.HTTPError as exc:                     # recorded, not absorbed
        return exc.code, b""


def enumerate_acts() -> list[dict]:
    url = SPARQL + "?" + urllib.parse.urlencode(
        {"query": QUERY, "format": "application/sparql-results+json"}
    )
    status, body = get(url, timeout=300)
    if status != 200:
        raise SystemExit(f"SPARQL endpoint returned {status}")
    rows = json.loads(body)["results"]["bindings"]
    acts, seen = [], set()
    for row in rows:
        celex = row["celex"]["value"]
        if celex in seen:
            continue
        seen.add(celex)
        acts.append(
            {
                "celex": celex,
                "date": row["date"]["value"],
                "title": row["title"]["value"],
            }
        )
    return acts


def main() -> None:
    CORPUS.mkdir(exist_ok=True)
    acts = enumerate_acts()
    print(f"enumerated {len(acts)} acts")
    for i, act in enumerate(acts, 1):
        path = CORPUS / f"{act['celex']}.html"
        if path.exists():
            body = path.read_bytes()
            act["http_status"] = 200
        else:
            status, body = get(EURLEX + act["celex"])
            act["http_status"] = status
            if status == 200 and body:
                path.write_bytes(body)
            time.sleep(1.0)                                   # one request a second
        act["bytes"] = len(body)
        act["sha256"] = hashlib.sha256(body).hexdigest() if body else None
        if i % 25 == 0:
            print(f"  {i}/{len(acts)}")
    manifest = {
        "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sparql_endpoint": SPARQL,
        "query": QUERY.strip(),
        "eurlex_pattern": EURLEX + "<celex>",
        "act_count": len(acts),
        "failed": [a["celex"] for a in acts if a["http_status"] != 200],
        "acts": acts,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"stored {len(acts) - len(manifest['failed'])} acts; {len(manifest['failed'])} failed")


if __name__ == "__main__":
    main()
