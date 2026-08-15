#!/usr/bin/env python3
"""Score C1-C6 of PREREGISTRATION-01.md against data/robots.json.

The bands are transcribed from the pre-registration, which was written before the first
request. The voiding rule (denominator < 15 -> VOID) and the kill condition (> 25 % of 171
hosts at network level -> the night is void) are applied here, not decided here.
"""

import collections
import json

R = json.load(open("data/robots-rescored.json"))
hosts = R["hosts"]
verdicts = R["verdicts"]
A = [h for h in hosts if h["arm"] == "A"]
B = [h for h in hosts if h["arm"] == "B"]
gov = lambda h: h["host"].endswith(".gov") or h["host"].endswith(".mil")


def band(name, value, lo, hi, n, unit="%"):
    if n < 15:
        return f"| **{name}** | {lo}–{hi} {unit} | {value} (n={n}) | **VOID** |"
    ok = lo <= value <= hi
    return (f"| **{name}** | {lo}–{hi} {unit} | {value:.1f} {unit} (n={n}) | "
            f"**{'HELD' if ok else 'FAILED'}** |")


print("## Host-level outcomes\n")
for arm, label in ((A, "A — refusing (42)"), (B, "B — control (129)")):
    c = collections.Counter(h["served"] for h in arm)
    print(f"**{label}**: " + " · ".join(f"`{k}` {v}" for k, v in c.most_common()))
print()

net_total = sum(1 for h in hosts if h["served"] == "network")
print(f"**Kill condition**: network-level {net_total}/{len(hosts)} = "
      f"{100*net_total/len(hosts):.1f} % (void if > 25 %) — "
      f"{'FIRED' if net_total/len(hosts) > 0.25 else 'did not fire'}\n")

print("## Clause scoring\n")
print("| clause | forecast | observed | verdict |")
print("|---|---|---|---|")

a_served = sum(1 for h in A if h["served"] == "served")
print(band("C1 robots served, arm A", 100*a_served/len(A), 70, 95, len(A)))

vs = [v for v in verdicts if v["verdict"] in ("RULE_COVERS", "RULE_PERMITS")]
permits = sum(1 for v in vs if v["verdict"] == "RULE_PERMITS")
print(band("C2 RULE_PERMITS share", 100*permits/len(vs) if vs else 0, 60, 90, len(vs)))

g = [v for v in vs if v["host"].endswith((".gov", ".mil"))]
o = [v for v in vs if not v["host"].endswith((".gov", ".mil"))]
gp = 100*sum(1 for v in g if v["verdict"] == "RULE_PERMITS")/len(g) if g else 0
op = 100*sum(1 for v in o if v["verdict"] == "RULE_PERMITS")/len(o) if o else 0
if len(g) < 15 or len(o) < 15:
    print(f"| **C3 gov − other ≥ 10 pp** | ≥ 10 pp | gov {gp:.1f} % (n={len(g)}) − "
          f"other {op:.1f} % (n={len(o)}) = {gp-op:+.1f} pp | **VOID** (arm < 15) |")
else:
    print(f"| **C3 gov − other ≥ 10 pp** | ≥ 10 pp | {gp-op:+.1f} pp | "
          f"**{'HELD' if gp-op >= 10 else 'FAILED'}** |")

ai = sum(1 for h in A if h["served"] == "served" and h["ai_tokens"])
print(band("C4 AI tokens named, arm A", 100*ai/len(A), 25, 60, len(A)))

blocked_robots = sum(1 for h in A if h["served"] == "robots_blocked")
print(f"| **C5 robots.txt itself 403/429** | fewer than 5 | **{blocked_robots}** of {len(A)} | "
      f"**{'HELD' if blocked_robots < 5 else 'FAILED'}** |")

b_served = sum(1 for h in B if h["served"] == "served")
print(band("C6 robots served, arm B", 100*b_served/len(B), 80, 97, len(B)))

print("\n## Verdicts over the 63 refusing addresses\n")
c = collections.Counter(v["verdict"] for v in verdicts)
for k, v in c.most_common():
    print(f"- `{k}` **{v}** of {len(verdicts)} ({100*v/len(verdicts):.1f} %)")

print("\n## Arm A, host by host\n")
print("| host | gov | robots.txt | group | rules | AI tokens named |")
print("|---|---|---|---|---:|---|")
for h in sorted(A, key=lambda x: (x["served"], x["host"])):
    print(f"| `{h['host']}` | {'yes' if gov(h) else ''} | {h['status']} {h['served']} | "
          f"`{h['group'] or '—'}` | {h['rule_count']} | {len(h['ai_tokens'])} |")

print("\n## Control arm, non-2xx robots.txt\n")
for h in sorted(B, key=lambda x: x["host"]):
    if h["served"] != "served":
        print(f"- `{h['host']}` — {h['status']} {h['served']}")

print("\n## Arm A robots_blocked, government hosts\n")
for h in sorted(A, key=lambda x: x["host"]):
    if h["served"] == "robots_blocked" and gov(h):
        print(f"- `{h['host']}` — {h['status']}")
