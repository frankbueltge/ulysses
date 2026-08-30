#!/usr/bin/env python3
"""I2 and I3 — the file at the address, asked twice.

I2: each English item URI from `addresses.json`, fetched once with **no Accept header at all**.
I3: every item that came back 200 is asked a second time at the identical URL, this time with
    `Accept: <the MIME type of the register's own listed type>`.

Status, byte count, sha256, Content-Type and the first 8 bytes go into `items.json`. Payloads are
hashed, tested by `readable.py` in the same process, and are not written to disk.

Standard library only.
"""

import concurrent.futures as cf
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.request

from readable import classify

HERE = pathlib.Path(__file__).resolve().parent
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"
WORKERS = 5

ACCEPT_FOR = {
    "pdf": "application/pdf",
    "pdfa1b": "application/pdf",
    "pdfa2a": "application/pdf",
    "xhtml": "application/xhtml+xml",
    "fmx4": "application/xml",
}
MAGIC_FOR = {
    "pdf": b"%PDF",
    "pdfa1b": b"%PDF",
    "pdfa2a": b"%PDF",
    "xhtml": b"<",
    "fmx4": b"<",
}


def get(url: str, accept: str | None) -> tuple[dict, bytes]:
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as fh:
                body = fh.read()
                return ({"http_status": fh.status, "bytes": len(body),
                         "sha256": hashlib.sha256(body).hexdigest(),
                         "content_type": fh.headers.get("Content-Type"),
                         "magic": body[:8].hex()}, body)
        except urllib.error.HTTPError as exc:
            if exc.code in (503, 429) and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            return ({"http_status": exc.code, "bytes": 0, "sha256": None,
                     "content_type": exc.headers.get("Content-Type") if exc.headers else None,
                     "magic": None}, b"")
        except Exception as exc:  # noqa: BLE001 — a transport failure is a status of its own
            if attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            return ({"http_status": 0, "bytes": 0, "sha256": None,
                     "content_type": f"error: {type(exc).__name__}", "magic": None}, b"")
    return ({"http_status": 0, "bytes": 0, "sha256": None,
             "content_type": "error: exhausted", "magic": None}, b"")


def one(celex: str, mtype: str, url: str) -> dict:
    rec = {"celex": celex, "type": mtype, "url": url}
    open_probe, body = get(url, None)                       # I2 — no Accept header
    rec["no_accept"] = open_probe
    magic = MAGIC_FOR.get(mtype, b"")
    rec["present"] = bool(open_probe["http_status"] == 200
                          and open_probe["bytes"] >= 1000
                          and magic and body.startswith(magic))
    if rec["present"] and magic == b"%PDF":
        rec["readability"] = classify(body)                 # I4 — local, on the bytes in hand
    if rec["present"]:
        typed, _ = get(url, ACCEPT_FOR[mtype])              # I3 — same URL, naming the type
        rec["typed_accept"] = {"accept": ACCEPT_FOR[mtype], **typed}
    return rec


def main() -> None:
    src = json.loads((HERE / "addresses.json").read_text())
    jobs = [(c, r["type"], u)
            for c, mans in sorted(src["manifestations"].items())
            for r in mans.values() for u in r["items"]]
    print(f"{len(jobs)} item URIs", flush=True)

    out = []
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(one, *j) for j in jobs]
        for n, fut in enumerate(cf.as_completed(futures), 1):
            out.append(fut.result())
            if n % 25 == 0:
                print(f"  fetched {n}/{len(jobs)}", flush=True)

    out.sort(key=lambda r: (r["celex"], r["url"]))
    payload = {
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "route_i2": "GET <item URI>, no Accept header",
        "route_i3": "GET <same item URI>, Accept: the MIME type of the register's listed type",
        "items": len(out),
        "records": out,
    }
    (HERE / "items.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
    print("present:", sum(1 for r in out if r["present"]), "of", len(out))


if __name__ == "__main__":
    main()
