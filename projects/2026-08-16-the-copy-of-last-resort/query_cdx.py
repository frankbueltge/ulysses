#!/usr/bin/env python3
"""Ask one host — web.archive.org — whether it holds a copy of each address the CFR prints.

Input:  data/probe-frozen-2026-08-14.json  (the 2026-08-14 census, unchanged)
Output: data/cdx.json

Per address, exact-match CDX queries:
  1. most recent capture with status 200   (filter=statuscode:200, limit=-1)
  2. only if (1) is empty: most recent capture of any status (limit=-1)

No capture bodies are fetched. One user-agent, naming the practice, no disguise.
The 171 hosts of the census are not contacted at all tonight.

INSTRUMENT REPAIR, 2026-08-16, after the first run and before any clause was scored
(recorded in MEASUREMENT.md § "The instrument was repaired mid-run"):
  * The pre-registered "first capture with status 200" query is DROPPED. It answered
    504 Gateway Time-out at the archive — `filter=statuscode:200` with `limit=1` makes
    the index scan forward from 1996 — and **no pre-registered clause uses it**. C1/C6
    need existence, C2/C3/C5 need the most recent capture. Nothing scored changes.
  * Serial querying is replaced by a small thread pool. A single query costs 30-60 s
    against this index; 306 addresses serially is some three hours.
  * Timeout raised 45 s -> 100 s for the same reason.
  * **Arm D is not queried.** It is the 124 root addresses that resolve — and no
    pre-registered clause uses it (C1/C2/C4/C5 read arm A, C3 reads arm C, C6 reads
    arm B). At the measured rate of this index it is 40 % of the run for nothing that
    is scored. Arm D is reported as NOT QUERIED, never as a null result.
  * Results are appended to data/cdx.jsonl as they arrive, so a killed run resumes
    instead of asking the index for the same address twice.
No arm, band, corpus or voiding rule is touched by any of this.
"""
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
CDX = "https://web.archive.org/cdx/search/cdx"
UA = ("Mozilla/5.0 (compatible; Ulysses-archive-check/1.0; artistic research; "
      "CDX index only, no capture bodies; +https://frankbueltge.de/atelier/)")
WORKERS = 12
TIMEOUT = 100
RETRIES = 1           # one retry, as the kill condition assumes
ARMS_QUERIED = ("A", "B", "C")

_print_lock = threading.Lock()
_write_lock = threading.Lock()


def is_deep(url: str) -> bool:
    """The rule fixed in PREREGISTRATION-01.md, before execution."""
    pr = urlparse(url if "://" in url else "http://" + url)
    return bool(pr.path.strip("/")) or bool(pr.query)


def cdx_last(url: str, *, only_200: bool):
    """Most recent capture as {timestamp, statuscode}, or None. Raises on query failure."""
    params = {"url": url, "output": "json", "fl": "timestamp,statuscode", "limit": "-1"}
    if only_200:
        params["filter"] = "statuscode:200"
    q = CDX + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(q, headers={"User-Agent": UA})
    last_err = None
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                body = r.read().decode("utf-8", "replace").strip()
            if not body:
                return None
            rows = json.loads(body)
            if len(rows) < 2:
                return None
            return {"timestamp": rows[1][0], "statuscode": rows[1][1]}
        except Exception as e:          # noqa: BLE001 — every failure is recorded, not swallowed
            last_err = f"{type(e).__name__}: {e}"
            if attempt < RETRIES:
                time.sleep(3.0)
    raise RuntimeError(last_err)


def classify(r):
    failing = r["outcome"] != "2xx"
    depth = "deep" if is_deep(r["url"]) else "root"
    return depth, ("A" if failing and depth == "deep" else
                   "B" if failing else
                   "C" if depth == "deep" else "D")


def probe_one(item):
    i, total, r, jsonl = item
    url = r["url"]
    depth, arm = classify(r)
    rec = {
        "url": url,
        "host": r["host"],
        "host_class": r["host_class"],
        "sections": r["sections"],
        "census_outcome": r["outcome"],
        "depth": depth,
        "arm": arm,
        "last_200": None,
        "last_any": None,
        "query_error": None,
    }
    try:
        rec["last_200"] = cdx_last(url, only_200=True)
        if rec["last_200"] is None:
            rec["last_any"] = cdx_last(url, only_200=False)
    except RuntimeError as e:
        rec["query_error"] = str(e)
    with _write_lock:
        with open(jsonl, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
    with _print_lock:
        mark = ("200:" + rec["last_200"]["timestamp"]) if rec["last_200"] else (
            "ERR" if rec["query_error"] else
            ("any:" + rec["last_any"]["timestamp"]) if rec["last_any"] else "NONE")
        print(f"{i:3d}/{total} {rec['arm']} {rec['census_outcome']:8s} {mark:16s} {url}",
              flush=True)
    return rec


def main():
    src = os.path.join(HERE, "data", "probe-frozen-2026-08-14.json")
    results = json.load(open(src))["results"]
    jsonl = os.path.join(HERE, "data", "cdx.jsonl")

    done = {}
    if os.path.exists(jsonl):
        for line in open(jsonl):
            line = line.strip()
            if line:
                rec = json.loads(line)
                if not rec.get("query_error"):      # a failed query is retried on resume
                    done[rec["url"]] = rec
    todo = [r for r in results
            if classify(r)[1] in ARMS_QUERIED and r["url"] not in done]
    print(f"{len(results)} addresses · arms {'+'.join(ARMS_QUERIED)} queried · "
          f"{len(done)} already on disk · {len(todo)} to go", flush=True)

    items = [(i, len(todo), r, jsonl) for i, r in enumerate(todo, 1)]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        fresh = list(pool.map(probe_one, items))

    by_url = dict(done)
    for rec in fresh:
        by_url[rec["url"]] = rec
    out, skipped = [], 0
    for r in results:
        depth, arm = classify(r)
        if arm not in ARMS_QUERIED:
            skipped += 1
            continue
        out.append(by_url[r["url"]])

    errors = sum(1 for r in out if r["query_error"])
    payload = {
        "queried": "2026-08-16",
        "index": "web.archive.org CDX",
        "user_agent": UA,
        "workers": WORKERS,
        "arms_queried": list(ARMS_QUERIED),
        "arm_D_not_queried": skipped,
        "source": "data/probe-frozen-2026-08-14.json",
        "source_sha256": "1d6c5998f51d0ad0e3c9c8089361e42d6490a8840e9a2affde1775b79f5fbfbe",
        "addresses": len(out),
        "query_errors": errors,
        "results": out,
    }
    dst = os.path.join(HERE, "data", "cdx.json")
    json.dump(payload, open(dst, "w"), indent=1)
    print(f"\nwrote {dst} — {len(out)} addresses queried, {skipped} in arm D not queried, "
          f"{errors} query errors ({errors / len(out):.1%}; kill fires above 20 %)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
