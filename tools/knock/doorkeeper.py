#!/usr/bin/env python3
"""doorkeeper.py — what a site tells machines about who may read it.

For each host it fetches `/robots.txt` once and answers three questions from
the text of that file alone:

  Q1  May an ordinary, honestly identified research instrument read a
      published work here?  (`can_fetch` for our own User-Agent.)
  Q2  If not — who may?  The named agents that are granted a rule less
      restrictive than the one given to everyone else.
  Q3  Is the permission structure a BLOCKLIST (everyone allowed, named
      agents refused) or an ALLOWLIST (everyone refused, named agents
      admitted)?  This is the structural variable.

What this measures, exactly: what the site DECLARES to machines. robots.txt is
advisory; a site may declare a refusal and serve the bytes anyway, or declare
nothing and refuse at the socket. Nothing here is a claim about what any host
actually serves, and nothing here is a claim about anyone's motives.

One request per host, nothing else fetched, nothing submitted anywhere.

Usage: python3 tools/knock/doorkeeper.py hosts.json out.json
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone

UA_INSTRUMENT = (
    "Ulysses-Atelier-Reachability-Census/1.0 "
    "(+https://github.com/frankbueltge/ulysses; "
    "artistic-research reachability probe; 1 request per host)"
)
TIMEOUT = 40
DELAY_S = 1.5


def fetch_robots(root: str):
    url = root.rstrip("/") + "/robots.txt"
    req = urllib.request.Request(url, headers={"User-Agent": UA_INSTRUMENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace")
            return {"status": r.status, "text": body, "error": None,
                    "content_type": r.headers.get("Content-Type", ""),
                    "is_html": looks_like_html(body)}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "text": "", "error": f"HTTP {exc.code}",
                "content_type": "", "is_html": False}
    except Exception as exc:
        return {"status": None, "text": "",
                "error": f"{type(exc).__name__}: {str(exc)[:160]}",
                "content_type": "", "is_html": False}


def looks_like_html(body: str) -> bool:
    """A page served where the rules file should be is not a rules file.

    Some hosts answer /robots.txt with HTTP 200 and an HTML document — a
    challenge page, or their ordinary error page. Read as robots.txt that
    parses to no rules at all, i.e. to `everything permitted`, which is the
    opposite of what the host is doing. It must be classed apart.
    """
    head = body.lstrip()[:400].lower()
    return head.startswith("<") or "<html" in head or "<!doctype html" in head


def parse_groups(text: str):
    """robots.txt as {agent-lowercase: [(directive, value), ...]}.

    Consecutive `User-agent:` lines share the block that follows them, which is
    how allowlists are written; the parser must keep that or it miscounts.
    """
    groups, pending, cur = {}, [], []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "user-agent":
            if cur:            # a rule block ended; the next agents start a new one
                pending, cur = [], []
            pending.append(val.lower())
            groups.setdefault(val.lower(), [])
        elif key in ("disallow", "allow", "crawl-delay"):
            cur.append((key, val))
            for agent in pending:
                groups[agent].append((key, val))
    return groups


def classify(groups):
    """BLOCKLIST, ALLOWLIST, OPEN, CLOSED, or NONE — from the `*` group and the rest."""
    star = groups.get("*")
    named = [a for a in groups if a != "*"]
    if not groups:
        return "NONE", False, named
    star_blocks_all = bool(star) and any(
        k == "disallow" and v in ("/",) for k, v in star
    )
    star_allows_root = not star_blocks_all
    if star_blocks_all and named:
        return "ALLOWLIST", star_blocks_all, named
    if star_blocks_all and not named:
        return "CLOSED", star_blocks_all, named
    if named and star_allows_root:
        return "BLOCKLIST", star_blocks_all, named
    return "OPEN", star_blocks_all, named


def named_admitted(groups, blocked_star: bool):
    """Agents whose block is less restrictive than the one given to `*`."""
    out = []
    for agent, rules in groups.items():
        if agent == "*":
            continue
        blocks_all = any(k == "disallow" and v == "/" for k, v in rules)
        if blocked_star and not blocks_all:
            out.append(agent)
    return sorted(out)


def main(hosts_path: str, out_path: str):
    with open(hosts_path) as fh:
        spec = json.load(fh)
    rows = []
    for h in spec["hosts"]:
        root, probe = h["root"], h.get("probe_path", "/")
        got = fetch_robots(root)
        rec = dict(h)
        rec["robots_status"] = got["status"]
        rec["robots_error"] = got["error"]
        rec["robots_bytes"] = len(got["text"].encode("utf-8"))
        rec["content_type"] = got.get("content_type", "")

        if got.get("is_html"):
            rec.update(structure="HTML-IN-PLACE-OF-RULES", permits_instrument=None,
                       named_agents=[], admitted=[], n_named=0,
                       note=("HTTP 200 with an HTML document where robots.txt "
                             "should be: the file that tells machines the rules "
                             "was not delivered to this machine. Nothing is "
                             "concluded about what the host permits"))
            rows.append(rec)
            print(f"{h['id']:<22} HTML-IN-PLACE-OF-RULES  "
                  f"({rec['robots_bytes']} B, {rec['content_type']})", flush=True)
            time.sleep(DELAY_S)
            continue

        if got["error"] or not got["text"].strip():
            rec.update(structure="UNDETERMINED", permits_instrument=None,
                       named_agents=[], admitted=[], n_named=0,
                       note=("no robots.txt reached from this session — "
                             "this is our egress, or the file is absent; "
                             "either way nothing is concluded here"))
            rows.append(rec)
            print(f"{h['id']:<22} UNDETERMINED  ({got['error']})", flush=True)
            time.sleep(DELAY_S)
            continue

        rp = urllib.robotparser.RobotFileParser()
        rp.parse(got["text"].splitlines())
        permits = bool(rp.can_fetch(UA_INSTRUMENT, root.rstrip("/") + probe))
        groups = parse_groups(got["text"])
        structure, star_blocks, named = classify(groups)
        admitted = named_admitted(groups, star_blocks)
        rec.update(structure=structure, permits_instrument=permits,
                   named_agents=sorted(named), n_named=len(named),
                   admitted=admitted, note="")
        rows.append(rec)
        print(f"{h['id']:<22} {structure:<13} permits={permits}  "
              f"named={len(named)} admitted={len(admitted)}", flush=True)
        time.sleep(DELAY_S)

    payload = {
        "instrument": "tools/knock/doorkeeper.py",
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ua_instrument": UA_INSTRUMENT,
        "measures": "declared permission in robots.txt, not what a host serves",
        "rows": rows,
    }
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
    print(f"\nwrote {out_path}  ({len(rows)} hosts)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
