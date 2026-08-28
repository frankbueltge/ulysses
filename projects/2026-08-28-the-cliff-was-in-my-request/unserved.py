#!/usr/bin/env python3
"""Post-hoc, declared as post-hoc: what the register lists for the 372 works that neither
route serves.

A1 failed. The failure is the interesting half of the night, and it has a factual question
under it: are those 372 works declared-and-absent, or declared-and-held-in-a-form this route
does not hand over? The register is asked for the manifestation types of each work's English
expression. Nothing here was pre-registered and nothing here is scored.

Standard library only.
"""

import collections
import json
import pathlib
import sys
import time
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "2026-08-25-the-pointer-that-resolves"))
from resolve import SPARQL, UA, get  # noqa: E402

Q = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?celex ?type (COUNT(?item) AS ?items) WHERE {
  VALUES ?celex { %s }
  ?w cdm:resource_legal_id_celex ?celex .
  ?e cdm:expression_belongs_to_work ?w ;
     cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> .
  ?m cdm:manifestation_manifests_expression ?e .
  OPTIONAL { ?m cdm:manifestation_type ?type }
  OPTIONAL { ?item cdm:item_belongs_to_manifestation ?m }
} GROUP BY ?celex ?type
"""


def ask(celexes: list[str]) -> list[dict]:
    values = " ".join('"%s"^^<http://www.w3.org/2001/XMLSchema#string>' % c for c in celexes)
    url = SPARQL + "?" + urllib.parse.urlencode(
        {"query": Q % values, "format": "application/sparql-results+json"})
    for attempt in range(5):
        status, body = get(url, {"User-Agent": UA}, timeout=600)
        if status == 200:
            return json.loads(body)["results"]["bindings"]
        time.sleep(4 * (attempt + 1))
    raise SystemExit(f"SPARQL refused (last status {status})")


def main() -> None:
    man = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    unserved = [r["celex"] for r in man["records"] if r["http_status"] != 200]
    served = [r["celex"] for r in man["records"] if r["http_status"] == 200][:200]
    print(f"unserved by either route: {len(unserved)}")

    def types_for(group: list[str]) -> dict[str, set]:
        found: dict[str, set] = {c: set() for c in group}
        for i in range(0, len(group), 25):
            for row in ask(group[i:i + 25]):
                t = row.get("type", {}).get("value", "(no type)")
                n = int(row["items"]["value"])
                found[row["celex"]["value"]].add(f"{t}:{n}")
            time.sleep(0.4)
            print(f"  {min(i + 25, len(group))}/{len(group)}", flush=True)
        return found

    un = types_for(unserved)
    sv = types_for(served)

    def summarise(found: dict[str, set]) -> dict:
        shapes = collections.Counter(
            ",".join(sorted(t.split(":")[0] for t in v)) or "(none)" for v in found.values())
        with_items = sum(1 for v in found.values()
                         if any(int(t.split(":")[1]) > 0 for t in v))
        return {"works": len(found), "with_at_least_one_item": with_items,
                "manifestation_shapes": dict(shapes.most_common(12))}

    out = {"measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "note": "post-hoc; not pre-registered, not scored",
           "unserved_by_either_route": summarise(un),
           "served_comparison_first_200": summarise(sv),
           "detail_unserved": {k: sorted(v) for k, v in un.items()}}
    (HERE / "unserved.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "detail_unserved"}, indent=1))


if __name__ == "__main__":
    main()
