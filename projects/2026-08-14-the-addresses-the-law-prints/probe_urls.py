#!/usr/bin/env python3
"""Probe every address printed in the CFR's incorporation-by-reference sections.

Rules P1-P5 are fixed in PREREGISTRATION-01.md. This script reads the frozen extraction
(data/urls.json, hashed in MEASUREMENT.md) and never writes back to it: the classification
it scores against was on disk before the first request went out.

Usage: python3 probe_urls.py --urls data/urls.json --out data/probe.json
"""

import argparse
import json
import subprocess
import time
from collections import defaultdict

UA = ("Mozilla/5.0 (compatible; Ulysses-IBR-census/1.0; artistic research; "
      "one request per address; +https://frankbueltge.de/atelier/)")


def probe(url: str, timeout: int = 20) -> dict:
    """P1: one GET, redirects followed, bounded."""
    out = subprocess.run(
        ["curl", "-sS", "-L", "--max-redirs", "10", "--max-time", str(timeout),
         "-A", UA, "-o", "/dev/null",
         "-w", "%{http_code} %{num_redirects} %{url_effective}", url],
        capture_output=True, text=True,
    )
    if out.returncode != 0 or not out.stdout.strip():
        return {"ok": False, "status": None, "curl_error": out.stderr.strip()[:200] or
                f"exit {out.returncode}", "final": None, "redirects": None}
    parts = out.stdout.strip().split(" ", 2)
    code = int(parts[0]) if parts[0].isdigit() else 0
    return {"ok": True, "status": code, "curl_error": None,
            "redirects": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
            "final": parts[2] if len(parts) > 2 else None}


def classify(first: dict, second: dict | None) -> str:
    """P3: the outcome class, decided on both probes."""
    def cls(r: dict) -> str:
        if not r["ok"] or r["status"] == 0:
            return "network"
        if 200 <= r["status"] < 300:
            return "2xx"
        if r["status"] in (403, 429):
            return "blocked"
        if 400 <= r["status"] < 500:
            return "4xx"
        if r["status"] >= 500:
            return "5xx"
        return "other"
    if cls(first) == "2xx":
        return "2xx"
    if second is None:
        return cls(first)
    # P2: failing only if both probes fail; the second probe's class wins otherwise.
    return cls(second)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", default="data/urls.json")
    ap.add_argument("--out", default="data/probe.json")
    ap.add_argument("--retry-wait", type=int, default=90)
    args = ap.parse_args()

    frozen = json.load(open(args.urls))
    urls = frozen["urls"]
    last_hit: dict[str, float] = defaultdict(float)

    def polite(host: str) -> None:
        wait = 0.5 - (time.time() - last_hit[host])  # P1: <= 2 requests/second/host
        if wait > 0:
            time.sleep(wait)
        last_hit[host] = time.time()

    results = []
    for i, rec in enumerate(urls, 1):
        polite(rec["host"])
        first = probe(rec["url"])
        results.append({**{k: rec[k] for k in ("url", "host", "host_class", "sections")},
                        "first": first, "second": None, "outcome": None})
        print(f"[{i}/{len(urls)}] {rec['url']} -> {first['status'] or first['curl_error']}",
              flush=True)

    # P2: everything that did not come back 2xx is probed again, at least 60 s later.
    retry = [r for r in results if not (r["first"]["ok"] and r["first"]["status"]
                                        and 200 <= r["first"]["status"] < 300)]
    print(f"\n{len(retry)} addresses did not return 2xx; waiting {args.retry_wait}s "
          f"before the second probe (P2)", flush=True)
    time.sleep(args.retry_wait)
    for i, r in enumerate(retry, 1):
        polite(r["host"])
        r["second"] = probe(r["url"])
        print(f"[retry {i}/{len(retry)}] {r['url']} -> "
              f"{r['second']['status'] or r['second']['curl_error']}", flush=True)

    for r in results:
        r["outcome"] = classify(r["first"], r["second"])

    # P5: the host root of every failing address (blocked excluded from D5's denominator,
    # but probed anyway so the record carries it).
    roots: dict[str, dict] = {}
    for r in results:
        if r["outcome"] == "2xx":
            continue
        root = f"https://{r['host']}/"
        if root not in roots:
            polite(r["host"])
            roots[root] = probe(root)
            print(f"[root] {root} -> "
                  f"{roots[root]['status'] or roots[root]['curl_error']}", flush=True)

    json.dump({"probed": "2026-08-14", "user_agent": UA,
               "source_sha256_note": "data/urls.json as hashed in MEASUREMENT.md",
               "results": results, "host_roots": roots}, open(args.out, "w"), indent=1)

    counts: dict[str, int] = defaultdict(int)
    for r in results:
        counts[r["outcome"]] += 1
    print("\noutcomes:", dict(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
