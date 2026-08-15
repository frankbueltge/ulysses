#!/usr/bin/env python3
"""Fetch /robots.txt once per host and score it against the frozen block classification.

The arms are read from data/probe-frozen-2026-08-14.json, which was hashed in
PREREGISTRATION-01.md before this script issued its first request. Nothing here writes
back to that file.

Rules are fixed in PREREGISTRATION-01.md:
  - one GET per host, no retry, redirects followed, 20 s timeout, >= 1 s between requests
  - the same user-agent as the 2026-08-14 census; no spoofing, no block worked around
  - the 63 refusing addresses are NOT requested again

Usage: python3 fetch_robots.py --frozen data/probe-frozen-2026-08-14.json --out data/robots.json
"""

import argparse
import collections
import json
import re
import subprocess
import time
import urllib.parse

UA = ("Mozilla/5.0 (compatible; Ulysses-IBR-census/1.0; artistic research; "
      "one request per address; +https://frankbueltge.de/atelier/)")

# The agent's own product token, for RFC 9309 group matching.
OWN_TOKEN = "ulysses-ibr-census"

AI_TOKENS = [
    "gptbot", "claudebot", "anthropic-ai", "ccbot", "google-extended",
    "perplexitybot", "bytespider", "applebot-extended", "meta-externalagent",
    "amazonbot", "diffbot", "omgili", "cohere-ai", "timpibot", "imagesiftbot",
    "youbot",
]

DIRECTIVE = re.compile(r"^\s*(user-agent|disallow|allow|sitemap|crawl-delay)\s*:", re.I)


def fetch(url: str, timeout: int = 20) -> dict:
    """One GET, no retry. Body capped; status and final URL recorded."""
    out = subprocess.run(
        ["curl", "-sS", "-L", "--max-redirs", "10", "--max-time", str(timeout),
         "-A", UA, "--max-filesize", "262144",
         "-w", "\n__META__ %{http_code} %{url_effective}", url],
        capture_output=True, text=True,
    )
    text = out.stdout
    meta = ""
    if "\n__META__ " in text:
        text, meta = text.rsplit("\n__META__ ", 1)
    if out.returncode != 0 and not meta:
        return {"ok": False, "status": None, "body": None, "final": None,
                "curl_error": out.stderr.strip()[:200] or f"exit {out.returncode}"}
    parts = meta.strip().split(" ", 1)
    code = int(parts[0]) if parts and parts[0].isdigit() else 0
    return {"ok": True, "status": code, "body": text[:65536],
            "final": parts[1] if len(parts) > 1 else None, "curl_error": None}


def parse_groups(body: str) -> dict[str, list[tuple[str, str]]]:
    """RFC 9309 grouping: consecutive user-agent lines share the rules that follow."""
    groups: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    current: list[str] = []
    fresh = False
    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip().lower()
        value = value.strip()
        if field == "user-agent":
            if not fresh:
                current = []
                fresh = True
            current.append(value.lower())
            groups.setdefault(value.lower(), [])
        elif field in ("allow", "disallow"):
            fresh = False
            for agent in current:
                groups[agent].append((field, value))
    return groups


def applicable(groups: dict, agent_token: str) -> tuple[str, list]:
    """The group that governs us: our own token if named, else '*', else no group."""
    for name in groups:
        if name and name != "*" and name in agent_token:
            return name, groups[name]
    if "*" in groups:
        return "*", groups["*"]
    return "", []


def pattern_re(pattern: str) -> re.Pattern:
    """RFC 9309 §2.2.3: '*' matches any run of characters, a trailing '$' anchors the end.

    Repaired 2026-08-15 after the first run (MEASUREMENT.md, 'The instrument's own error').
    The first version took the substring before the first '*' as a literal prefix, so
    `Disallow: /*?serviceType=` was read as `Disallow: /` and matched every path.
    """
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    rx = "".join(".*" if ch == "*" else re.escape(ch) for ch in body)
    return re.compile("^" + rx + ("$" if anchored else ""))


def path_verdict(rules: list[tuple[str, str]], path: str) -> str:
    """Longest-match wins; Allow wins ties (RFC 9309 §2.2.2)."""
    best_len, best = -1, None
    for field, pattern in rules:
        # An empty Disallow means "allow everything"; an empty Allow is a no-op.
        if pattern == "":
            continue
        if not pattern_re(pattern).match(path):
            continue
        length = len(pattern)
        if length > best_len or (length == best_len and field == "allow"):
            best_len, best = length, field
    if best is None:
        return "allowed"
    return "disallowed" if best == "disallow" else "allowed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", default="data/probe-frozen-2026-08-14.json")
    ap.add_argument("--out", default="data/robots.json")
    args = ap.parse_args()

    frozen = json.load(open(args.frozen))
    results = frozen["results"]

    by_host: dict[str, list[dict]] = collections.defaultdict(list)
    for rec in results:
        by_host[rec["host"]].append(rec)

    arm_a = sorted(h for h, rs in by_host.items()
                   if any(r["outcome"] == "blocked" for r in rs))
    arm_b = sorted(h for h, rs in by_host.items()
                   if {r["outcome"] for r in rs} == {"2xx"})
    print(f"arm A (refusing) {len(arm_a)} hosts · arm B (control) {len(arm_b)} hosts")

    hosts = [(h, "A") for h in arm_a] + [(h, "B") for h in arm_b]
    out = []
    for i, (host, arm) in enumerate(hosts, 1):
        if i > 1:
            time.sleep(1.0)  # >= 1 s between requests, and every host is distinct
        res = fetch(f"https://{host}/robots.txt")
        body = res.get("body") or ""
        has_directive = any(DIRECTIVE.match(ln) for ln in body.splitlines())
        status = res.get("status")

        if not res["ok"] or status in (None, 0):
            served = "network"
        elif 200 <= status < 300:
            served = "served" if has_directive else "no_directives"
        elif status in (403, 429):
            served = "robots_blocked"
        elif status in (404, 410):
            served = "absent"
        elif 400 <= status < 500:
            served = "other_4xx"
        else:
            served = "other"

        groups = parse_groups(body) if served == "served" else {}
        group_name, rules = applicable(groups, OWN_TOKEN)
        ai_named = sorted({t for t in AI_TOKENS if t in groups})

        out.append({
            "host": host, "arm": arm, "status": status, "served": served,
            "curl_error": res.get("curl_error"), "final": res.get("final"),
            "bytes": len(body), "group": group_name,
            "rule_count": len(rules), "ai_tokens": ai_named,
            "body": body if served == "served" else body[:400],
        })
        print(f"[{i:3d}/{len(hosts)}] {arm} {host:38s} {status} {served}"
              f"{' ai:' + ','.join(ai_named) if ai_named else ''}")

    # Per-address verdicts, Arm A only, against the frozen blocked set.
    robots_by_host = {r["host"]: r for r in out}
    verdicts = []
    for rec in results:
        if rec["outcome"] != "blocked":
            continue
        r = robots_by_host[rec["host"]]
        path = urllib.parse.urlsplit(rec["url"]).path or "/"
        if r["served"] == "served":
            rules = parse_groups(r["body"]).get(r["group"], []) if r["group"] else []
            pv = path_verdict(rules, path)
            verdict = "RULE_COVERS" if pv == "disallowed" else "RULE_PERMITS"
        elif r["served"] in ("absent", "no_directives"):
            verdict = "NO_FILE"
        elif r["served"] == "robots_blocked":
            verdict = "ROBOTS_BLOCKED"
        else:
            verdict = "UNSETTLED"
        verdicts.append({"url": rec["url"], "host": rec["host"], "path": path,
                         "sections": rec["sections"], "robots": r["served"],
                         "group": r["group"], "verdict": verdict})

    json.dump({"fetched": "2026-08-15", "user_agent": UA,
               "frozen_source": args.frozen,
               "arm_a": arm_a, "arm_b": arm_b,
               "hosts": out, "verdicts": verdicts},
              open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}: {len(out)} hosts, {len(verdicts)} blocked addresses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
