#!/usr/bin/env python3
"""tick 51 — the reading pack for the 37 papers the 0.5 repair moved and nobody read.

Offline except for nothing: it reads the landed tick-50 tables, the landed tick-47
hand-reading, and a corpus fetched separately by `warrant_trace.py fetch`.

What it does, in order:

  1. Recomputes, from `remeasure-tick50-<profile>-0.4.csv` against `-0.5.csv`, which papers
     left the class *invokes the statistic, states no threshold* — and splits them into
     papers that GAINED a site and papers that LOST their mention (fault F4). Tick 50
     reported the two together as one number of 47.
  2. Subtracts the 10 already hand-read at tick 47 (`handread-tick47.csv`).
  3. For every remaining paper, emits a reading pack: the new sites with their windows
     (from `remeasure-tick50-newsites.jsonl`) and every occurrence of the profile's term
     in the paper with context, so the class can be decided by reading rather than by the
     sieve that is on trial.

It classifies nothing. That step is by hand, in `handread-movers-tick51.csv`.

Usage:
  python3 movers-tick51.py --src <corpus>/src --out movers-tick51-pack.jsonl
"""
import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warrant_trace import Profile, body_of, normalise  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS = [("gaia", "ruwe-1.4"), ("mcmc", "rhat-1.1"), ("cv", "iou-0.5")]
CONTEXT = 320


def as_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def load_table(profile, version):
    path = os.path.join(HERE, f"remeasure-tick50-{profile}-{version}.csv")
    with open(path, encoding="utf-8") as fh:
        return {r["arxiv"]: r for r in csv.DictReader(fh)}


def movers():
    """{profile: {"gained": [...], "demoted": [...]}} — papers that left the closed class."""
    out = {}
    for _corpus, profile in PAIRS:
        a, b = load_table(profile, "0.4"), load_table(profile, "0.5")
        gained, demoted = [], []
        for aid, row in a.items():
            if row["state"] != "measured" or row["mentioned"] != "1" or as_int(row["sites"]) != 0:
                continue
            after = b[aid]
            if after["mentioned"] != "1":
                demoted.append(aid)
            elif as_int(after["sites"]) > 0:
                gained.append(aid)
        out[profile] = {"gained": gained, "demoted": demoted}
    return out


def already_read():
    path = os.path.join(HERE, "handread-tick47.csv")
    with open(path, encoding="utf-8") as fh:
        return {r["arxiv"]: r["class"] for r in csv.DictReader(fh)}


def new_sites():
    path = os.path.join(HERE, "remeasure-tick50-newsites.jsonl")
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                out.setdefault((r["profile"], r["arxiv"]), []).append(r)
    return out


def term_hits(text, prof, cap):
    """Every occurrence of the statistic's name, with context, deduplicated by position."""
    hits, seen = [], set()
    for m in prof.term_re.finditer(text):
        key = m.start() // 60
        if key in seen:
            continue
        seen.add(key)
        s, e = max(0, m.start() - CONTEXT), min(len(text), m.end() + CONTEXT)
        hits.append(re.sub(r"\s+", " ", text[s:e]))
    return hits[:cap], len(hits)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", required=True, help="corpus of fetched e-print sources")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap", type=int, default=60, help="term occurrences emitted per paper")
    args = ap.parse_args()

    mv, seen47, ns = movers(), already_read(), new_sites()
    profs = {p: Profile.load(os.path.join(HERE, "profiles", f"{p}.json")) for _c, p in PAIRS}

    n_papers = n_sites = 0
    with open(args.out, "w", encoding="utf-8") as out:
        for _corpus, profile in PAIRS:
            prof = profs[profile]
            for kind in ("gained", "demoted"):
                for aid in mv[profile][kind]:
                    if aid in seen47:
                        continue
                    path = os.path.join(args.src, aid + ".txt")
                    if not os.path.exists(path):
                        rec = {"profile": profile, "arxiv": aid, "kind": kind,
                               "state": "no_source"}
                        out.write(json.dumps(rec) + "\n")
                        continue
                    with open(path, encoding="utf-8", errors="replace") as fh:
                        text = normalise(body_of(fh.read()))
                    hits, total = term_hits(text, prof, args.cap)
                    sites = ns.get((profile, aid), [])
                    rec = {"profile": profile, "arxiv": aid, "kind": kind, "state": "ok",
                           "new_sites": [{"value": s["value"], "match": s["match"],
                                          "target": s["target"], "window": s["window"]}
                                         for s in sites],
                           "term_hits_total": total, "term_hits": hits}
                    out.write(json.dumps(rec) + "\n")
                    n_papers += 1
                    n_sites += len(sites)
    print(f"papers {n_papers}  new sites {n_sites}  -> {args.out}")


if __name__ == "__main__":
    main()
