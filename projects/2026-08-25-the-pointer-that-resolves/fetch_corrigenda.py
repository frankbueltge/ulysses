#!/usr/bin/env python3
"""Enumerate and fetch every English corrigendum in the register since 1990-01-01.

Two steps, both against primary sources and both recorded:

1. The EU Publications Office SPARQL endpoint (Cellar) is asked for every work of CELEX
   sector 3 that carries `cdm:resource_legal_corrects_resource_legal` — the register's own
   link from a corrigendum to the act it corrects — and has an English expression. The
   CELEX of the corrected act is asked for in the same query, so the pairing is the
   register's and not this instrument's.
2. Each corrigendum's English XHTML is fetched from the Publications Office content
   service and stored verbatim under corpus/, with sha256, byte count and HTTP status in
   manifest.json.

Nothing is parsed here. The corpus bytes are not committed; the manifest is.
Standard library only.
"""

import concurrent.futures as cf
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CORPUS = HERE / "corpus"
SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
CELLAR = "http://publications.europa.eu/resource/celex/"
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"

QUERY = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT DISTINCT ?celex ?date ?base_celex WHERE {
  ?w cdm:resource_legal_id_celex ?celex ;
     cdm:work_date_document ?date ;
     cdm:resource_legal_corrects_resource_legal ?base .
  ?base cdm:resource_legal_id_celex ?base_celex .
  ?e cdm:expression_belongs_to_work ?w ;
     cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> .
  FILTER(STRSTARTS(STR(?celex),"3"))
  FILTER(CONTAINS(STR(?celex),"R("))
  FILTER(?date >= "1990-01-01"^^<http://www.w3.org/2001/XMLSchema#date>)
}
ORDER BY ?date ?celex
"""

# The window opened at 2018 and was widened to 1990 before any outcome was measured, for
# one stated reason: at 2018 the corpus yields ~34 selected rows, and a proportion clause
# on 34 rows cannot be scored against any floor worth declaring. Counting the corpus
# before fixing the floor is the repair the failed forecast of 2026-08-24 earned. Nothing
# downstream of the selection step had been run when the window changed.


def get(url: str, headers: dict, timeout: int = 120) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            return fh.status, fh.read()
    except urllib.error.HTTPError as exc:  # recorded, not absorbed
        return exc.code, b""
    except Exception:  # noqa: BLE001 — a transport failure is a status of its own
        return 0, b""


def enumerate_corrigenda() -> list[dict]:
    url = SPARQL + "?" + urllib.parse.urlencode(
        {"query": QUERY, "format": "application/sparql-results+json"}
    )
    status, body = get(url, {"User-Agent": UA}, timeout=600)
    if status != 200:
        raise SystemExit(f"SPARQL endpoint returned {status}")
    rows = json.loads(body)["results"]["bindings"]
    out, seen = [], {}
    for row in rows:
        celex = row["celex"]["value"]
        base = row["base_celex"]["value"]
        if celex in seen:                       # a corrigendum may correct several acts
            seen[celex]["corrects"].append(base)
            continue
        rec = {
            "celex": celex,
            "date": row["date"]["value"],
            "corrects": [base],
        }
        seen[celex] = rec
        out.append(rec)
    return out


def doc_url(celex: str) -> str:
    return CELLAR + urllib.parse.quote(celex, safe="")


def main() -> None:
    CORPUS.mkdir(exist_ok=True)
    items = enumerate_corrigenda()
    print(f"enumerated {len(items)} corrigenda")
    headers = {
        "User-Agent": UA,
        "Accept": "application/xhtml+xml",
        "Accept-Language": "eng",
    }
    def one(it: dict) -> dict:
        path = CORPUS / (it["celex"].replace("/", "_") + ".html")
        if path.exists():
            body = path.read_bytes()
            it["http_status"] = 200
        else:
            status, body = get(doc_url(it["celex"]), headers)
            it["http_status"] = status
            if status == 200 and body:
                path.write_bytes(body)
            time.sleep(0.3)
        it["bytes"] = len(body)
        it["sha256"] = hashlib.sha256(body).hexdigest() if body else None
        return it

    # three workers, each pausing 0.3 s — roughly two or three requests a second against a
    # public content service, and the whole 1990-onward window inside one night
    done = 0
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        for _ in pool.map(one, items):
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(items)}", flush=True)
    manifest = {
        "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sparql_endpoint": SPARQL,
        "query": QUERY.strip(),
        "document_route": CELLAR + "<celex>  (Accept: application/xhtml+xml; Accept-Language: eng)",
        "count": len(items),
        "failed": [it["celex"] for it in items if it["http_status"] != 200],
        "corrigenda": items,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    ok = len(items) - len(manifest["failed"])
    print(f"stored {ok}; {len(manifest['failed'])} failed")


if __name__ == "__main__":
    main()
