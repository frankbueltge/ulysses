#!/usr/bin/env python3
"""Post-hoc validity check: is a `network` failure the host's, or this machine's?

Not pre-registered, and it changes no clause score. This machine reaches the internet
through a proxy, and a proxy failure and a dead host produce the same curl exit code.
So every host that failed at the network level is resolved here independently of the
proxy, three times, alongside a live control and a nonsense control.

Usage: python3 check_dns.py --probe data/probe.json --out data/dns.json
"""

import argparse
import json
import socket
import time

CONTROL_LIVE = "www.astm.org"
CONTROL_DEAD = "this-host-does-not-exist-9tq.example"


def resolve(host: str, tries: int = 3) -> list[str]:
    """Three attempts; the codes are kept so a temporary failure is not read as a dead host."""
    trials = []
    for _ in range(tries):
        try:
            socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
            trials.append("OK")
            break
        except socket.gaierror as err:
            trials.append(str(err.errno))
            time.sleep(0.4)
    return trials


def verdict(trials: list[str]) -> str:
    if trials[-1] == "OK":
        return "resolves"
    if all(t in ("-2", "-5") for t in trials):   # NXDOMAIN / no address record
        return "no address record"
    return "not settled"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", default="data/probe.json")
    ap.add_argument("--out", default="data/dns.json")
    args = ap.parse_args()

    probe = json.load(open(args.probe))
    hosts = sorted({r["host"] for r in probe["results"] if r["outcome"] == "network"})
    out = {"checked": "2026-08-14", "controls": {}, "hosts": {}}
    for name, host in (("live", CONTROL_LIVE), ("dead", CONTROL_DEAD)):
        out["controls"][name] = {"host": host, "trials": resolve(host)}
    for host in hosts:
        trials = resolve(host)
        out["hosts"][host] = {"trials": trials, "verdict": verdict(trials)}
        print(f"{host:30} {trials} -> {out['hosts'][host]['verdict']}")

    json.dump(out, open(args.out, "w"), indent=1)
    dead = [h for h, v in out["hosts"].items() if v["verdict"] == "no address record"]
    print(f"\n{len(dead)} of {len(hosts)} hosts have no address record on any attempt")
    print("controls:", {k: v["trials"] for k, v in out["controls"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
