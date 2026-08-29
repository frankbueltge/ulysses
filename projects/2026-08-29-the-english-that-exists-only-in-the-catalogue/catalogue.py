#!/usr/bin/env python3
"""I1 — the catalogue: what the register LISTS for each of the 196, language by language.

The population is read from the committed `unserved.json` of
`../2026-08-28-the-cliff-was-in-my-request` — every work whose English manifestation shape is
exactly `print` or `(none)`. Selection is by that file and by nothing measured tonight.

For each work the Publications Office SPARQL endpoint is asked for every expression, its
language, and every manifestation type listed under it. Chunked; raw counts and per-work
listings go into catalogue.json.

Standard library only.
"""

import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
PRIOR = HERE.parent / "2026-08-28-the-cliff-was-in-my-request" / "unserved.json"
SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"
CHUNK = 20

QUERY = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?celex ?lang ?type WHERE {
  ?w cdm:resource_legal_id_celex ?celex .
  FILTER(STR(?celex) IN (%s))
  ?e cdm:expression_belongs_to_work ?w ;
     cdm:expression_uses_language ?langres .
  BIND(REPLACE(STR(?langres),".*/","") AS ?lang)
  OPTIONAL { ?m cdm:manifestation_manifests_expression ?e ;
               cdm:manifestation_type ?type . }
}
"""


def population() -> list[str]:
    detail = json.loads(PRIOR.read_text())["detail_unserved"]

    def shape(items: list[str]) -> str:
        return ",".join(sorted(i.split(":")[0] for i in items)) if items else "(none)"

    return sorted(k for k, v in detail.items() if shape(v) in ("print", "(none)"))


def ask(celexes: list[str]) -> list[dict]:
    values = ", ".join('"%s"' % c for c in celexes)
    url = SPARQL + "?" + urllib.parse.urlencode(
        {"query": QUERY % values, "format": "application/sparql-results+json"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as fh:
                return json.loads(fh.read())["results"]["bindings"]
        except Exception as exc:  # noqa: BLE001 — a transport failure is retried, then raised
            if attempt == 3:
                raise SystemExit(f"SPARQL failed on chunk {celexes[0]}…: {exc}")
            time.sleep(5 * (attempt + 1))
    return []


def main() -> None:
    pop = population()
    listings: dict[str, dict[str, list[str]]] = {c: {} for c in pop}
    for start in range(0, len(pop), CHUNK):
        chunk = pop[start:start + CHUNK]
        for row in ask(chunk):
            celex = row["celex"]["value"]
            if celex not in listings:
                continue                       # the endpoint may match a CELEX we did not ask for
            lang = row["lang"]["value"]
            types = listings[celex].setdefault(lang, [])
            mtype = row.get("type", {}).get("value")
            if mtype and mtype not in types:
                types.append(mtype)
        print(f"  catalogue {start + len(chunk)}/{len(pop)}", flush=True)
        time.sleep(0.5)

    out = {
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": SPARQL,
        "population_size": len(pop),
        "works_with_no_binding": sorted(c for c, v in listings.items() if not v),
        "listings": {c: {l: sorted(t) for l, t in sorted(v.items())} for c, v in listings.items()},
    }
    (HERE / "catalogue.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print("works with no binding:", len(out["works_with_no_binding"]))


if __name__ == "__main__":
    main()
