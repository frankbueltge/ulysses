#!/usr/bin/env python3
"""I2 — the service: what the URL RETURNS for each declared (work, language) pair.

For every expression the register lists in catalogue.json, the CELEX resource URL is asked once
with `Accept: text/html` and `Accept-Language: <lang>` — the route that produced the correction
of 2026-08-28. Status, byte count, sha256 and Content-Type go into probes.json. Bodies are read
to be hashed and are not written to disk.

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
CELLAR = "http://publications.europa.eu/resource/celex/"
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"
WORKERS = 6


def fetch(celex: str, lang: str) -> dict:
    url = CELLAR + urllib.parse.quote(celex, safe="")
    req = urllib.request.Request(
        url,
        headers={"Accept": "text/html", "Accept-Language": lang.lower(), "User-Agent": UA},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as fh:
                body = fh.read()
                return {
                    "http_status": fh.status,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "content_type": fh.headers.get("Content-Type"),
                }
        except urllib.error.HTTPError as exc:
            if exc.code in (503, 429) and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            return {
                "http_status": exc.code,
                "bytes": 0,
                "sha256": None,
                "content_type": exc.headers.get("Content-Type") if exc.headers else None,
            }
        except Exception as exc:  # noqa: BLE001 — a transport failure is a status of its own
            if attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            return {"http_status": 0, "bytes": 0, "sha256": None,
                    "content_type": f"error: {type(exc).__name__}"}
    return {"http_status": 0, "bytes": 0, "sha256": None, "content_type": "error: exhausted"}


def main() -> None:
    listings = json.loads((HERE / "catalogue.json").read_text())["listings"]
    jobs = [(c, l) for c, langs in sorted(listings.items()) for l in sorted(langs)]
    print(f"{len(jobs)} (work, language) pairs", flush=True)

    results: dict[str, dict[str, dict]] = {}
    done = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(fetch, c, l): (c, l) for c, l in jobs}
        for fut in cf.as_completed(futures):
            celex, lang = futures[fut]
            results.setdefault(celex, {})[lang] = fut.result()
            done += 1
            if done % 200 == 0:
                print(f"  probed {done}/{len(jobs)}", flush=True)

    out = {
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "route": {"url": CELLAR + "<CELEX>", "accept": "text/html",
                  "accept_language": "<lang, lowercase>"},
        "pairs": len(jobs),
        "probes": {c: dict(sorted(v.items())) for c, v in sorted(results.items())},
    }
    (HERE / "probes.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print("written", len(results), "works")


if __name__ == "__main__":
    main()
