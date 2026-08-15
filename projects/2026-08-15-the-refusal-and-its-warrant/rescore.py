#!/usr/bin/env python3
"""Re-derive the per-address verdicts from the stored robots.txt bodies, with the
repaired wildcard matcher. Issues no request: it reads data/robots.json only.

Writes data/robots-rescored.json and prints the before/after so the repair is
visible in the record rather than silently applied.
"""

import importlib.util
import json
import urllib.parse

spec = importlib.util.spec_from_file_location("fr", "fetch_robots.py")
fr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fr)

R = json.load(open("data/robots.json"))
H = {h["host"]: h for h in R["hosts"]}

changed = []
for v in R["verdicts"]:
    h = H[v["host"]]
    old = v["verdict"]
    if h["served"] == "served":
        rules = fr.parse_groups(h["body"]).get(h["group"], []) if h["group"] else []
        pv = fr.path_verdict(rules, v["path"])
        new = "RULE_COVERS" if pv == "disallowed" else "RULE_PERMITS"
    else:
        new = old
    if new != old:
        changed.append((v["host"], v["path"], old, new))
    v["verdict"] = new

R["repaired"] = ("2026-08-15: wildcard matching in path_verdict repaired; verdicts "
                 "re-derived from the stored bodies, no host requested again")
json.dump(R, open("data/robots-rescored.json", "w"), indent=1)

print(f"verdicts changed by the repair: {len(changed)}")
for host, path, old, new in changed:
    print(f"  {host:28s} {path[:40]:42s} {old} -> {new}")
