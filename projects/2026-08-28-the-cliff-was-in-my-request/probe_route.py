#!/usr/bin/env python3
"""Ask the 1,931 corrigenda the first route refused, with the route the register's own
manifestation list names.

The population is read from the committed manifest of
`../2026-08-25-the-pointer-that-resolves/manifest.json` — every work whose `http_status` was
not 200 under `Accept: application/xhtml+xml`. Selection is by that field and by nothing
measured tonight.

Each work is asked once at the same URL with `Accept: text/html`. Status, byte count and
sha256 go into this project's manifest.json; the bytes go to corpus/ and are not committed.

A `300 Multiple Choices` is recorded as itself (§5.3 of PREREGISTRATION.md): it is neither a
service nor a refusal, and it counts against A1.

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
PRIOR = HERE.parent / "2026-08-25-the-pointer-that-resolves" / "manifest.json"
CORPUS = HERE / "corpus"
CELLAR = "http://publications.europa.eu/resource/celex/"
ACCEPT = "text/html"
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"


def fetch(celex: str) -> dict:
    url = CELLAR + urllib.parse.quote(celex, safe="")
    req = urllib.request.Request(
        url, headers={"Accept": ACCEPT, "Accept-Language": "eng", "User-Agent": UA}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as fh:
                body = fh.read()
                return {"http_status": fh.status, "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "content_type": fh.headers.get("Content-Type"), "_body": body}
        except urllib.error.HTTPError as exc:
            if exc.code in (503, 429) and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            return {"http_status": exc.code, "bytes": 0, "sha256": None,
                    "content_type": exc.headers.get("Content-Type") if exc.headers else None,
                    "_body": b""}
        except Exception as exc:  # noqa: BLE001
            if attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            return {"http_status": 0, "bytes": 0, "sha256": None,
                    "content_type": f"error: {type(exc).__name__}", "_body": b""}
    return {"http_status": 0, "bytes": 0, "sha256": None, "content_type": None, "_body": b""}


def main() -> None:
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    population = [r for r in prior["corrigenda"] if r["http_status"] != 200]
    print(f"population refused by the first route: {len(population)}", flush=True)

    CORPUS.mkdir(exist_ok=True)
    out: list[dict] = []
    done = 0
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch, r["celex"]): r for r in population}
        for fut in cf.as_completed(futures):
            r = futures[fut]
            got = fut.result()
            body = got.pop("_body")
            if got["http_status"] == 200 and body:
                safe = urllib.parse.quote(r["celex"], safe="")
                (CORPUS / f"{safe}.html").write_bytes(body)
            out.append({"celex": r["celex"], "date": r["date"], "corrects": r["corrects"],
                        "first_route_status": r["http_status"], **got})
            done += 1
            if done % 200 == 0:
                print(f"  {done}/{len(population)}", flush=True)

    out.sort(key=lambda r: (r["date"], r["celex"]))
    served = sum(1 for r in out if r["http_status"] == 200)
    manifest = {
        "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "population": "works of the 2026-08-25 corpus refused by Accept: application/xhtml+xml",
        "population_source": "../2026-08-25-the-pointer-that-resolves/manifest.json",
        "document_route": f"{CELLAR}<celex>  (Accept: {ACCEPT}; Accept-Language: eng)",
        "count": len(out),
        "served_200": served,
        "records": out,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"served 200: {served}/{len(out)} = {100 * served / len(out):.1f}%")


if __name__ == "__main__":
    main()
