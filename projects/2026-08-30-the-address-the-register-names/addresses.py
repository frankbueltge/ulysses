#!/usr/bin/env python3
"""I1 — the addresses: what item URI the register names for each English manifestation.

Population: every CELEX in `detail_unserved` of
`../2026-08-28-the-cliff-was-in-my-request/unserved.json` — the 372 works published as unserved
on 2026-08-28. Selection is by that committed file and by nothing measured tonight.

For each work the Publications Office SPARQL endpoint is asked for its English expressions, the
manifestations under them with their type, and each `cdm:item_belongs_to_manifestation` item URI.

Standard library only.
"""

import json
import pathlib
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
PRIOR = HERE.parent / "2026-08-28-the-cliff-was-in-my-request" / "unserved.json"
SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"
CHUNK = 15

QUERY = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?celex ?lang ?m ?type ?item WHERE {
  ?w cdm:resource_legal_id_celex ?celex .
  FILTER(STR(?celex) IN (%s))
  ?e cdm:expression_belongs_to_work ?w ;
     cdm:expression_uses_language ?langres .
  BIND(REPLACE(STR(?langres),".*/","") AS ?lang)
  FILTER(?lang = "ENG")
  ?m cdm:manifestation_manifests_expression ?e ;
     cdm:manifestation_type ?type .
  OPTIONAL { ?item cdm:item_belongs_to_manifestation ?m }
}
"""


def shape(items: list[str]) -> str:
    return ",".join(sorted(i.split(":")[0] for i in items)) if items else "(none)"


def population() -> tuple[list[str], dict[str, str]]:
    detail = json.loads(PRIOR.read_text())["detail_unserved"]
    return sorted(detail), {c: shape(v) for c, v in detail.items()}


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
    pop, shapes = population()
    print(f"{len(pop)} works", flush=True)
    found: dict[str, dict[str, dict]] = {c: {} for c in pop}

    for start in range(0, len(pop), CHUNK):
        chunk = pop[start:start + CHUNK]
        for row in ask(chunk):
            celex = row["celex"]["value"]
            if celex not in found:
                continue                   # the endpoint may match a CELEX we did not ask for
            man = row["m"]["value"]
            rec = found[celex].setdefault(man, {"type": row["type"]["value"], "items": []})
            item = row.get("item", {}).get("value")
            if item and item not in rec["items"]:
                rec["items"].append(item)
        print(f"  addresses {min(start + CHUNK, len(pop))}/{len(pop)}", flush=True)
        time.sleep(0.4)

    out = {
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": SPARQL,
        "population_size": len(pop),
        "shape_from_committed_file": shapes,
        "works_with_no_binding": sorted(c for c in pop if not found[c]),
        "manifestations": {c: {m: {"type": r["type"], "items": sorted(r["items"])}
                               for m, r in sorted(v.items())}
                           for c, v in sorted(found.items())},
    }
    (HERE / "addresses.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    items = sum(len(r["items"]) for v in found.values() for r in v.values())
    print("works with no ENG binding:", len(out["works_with_no_binding"]), "· item URIs:", items)


if __name__ == "__main__":
    main()
