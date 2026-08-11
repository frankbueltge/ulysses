#!/usr/bin/env python3
"""sites-dump-tick57 — print the sieve's OWN sites, so the site question is read from
the object it is about.

Tick 56 asked *is the site a threshold statement at all?* while reading windows cut
around **term** matches — the evidence `cv-census-tick56.py windows` produces, chosen for
the invoker question and at most three per paper, spread over the paper. That is the
right evidence for "does this paper invoke the criterion" and the wrong evidence for "is
what the sieve matched a threshold": the site is a *subset* of the term matches, and with
three windows spread over a long paper it need not be among them.

This prints the sites themselves, by calling the same `sites()` the measure tables count
— not a reimplementation of it, the function itself — so that what is judged is exactly
what the `sites` column counted.

Declared before any label of tick 57 existed, in `PREREGISTRATION-tick57.md` §2's dated
note. Because the evidence is stronger than tick 56's, the 24 papers tick 56 read are
dumped too, and any disagreement with its landed states is reported rather than absorbed.

    python3 sites-dump-tick57.py --ids frame-tick57.txt --src corpus/src
    python3 sites-dump-tick57.py --ids <(tick56 ids) --src corpus/src --out recheck.txt
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as W                                          # noqa: E402

PROFILE = os.path.join(HERE, "profiles", "iou-0.5.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ids", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default="sites-tick57.txt")
    ap.add_argument("--first", type=int, default=0, help="read_order to start at")
    ap.add_argument("--last", type=int, default=0, help="read_order to stop after")
    a = ap.parse_args()

    prof = W.Profile.load(PROFILE)
    ids = W.read_ids(os.path.join(HERE, a.ids))
    out = []
    for pos, aid in enumerate(ids, 1):
        if a.first and pos < a.first:
            continue
        if a.last and pos > a.last:
            break
        path = os.path.join(a.src, aid.replace("/", "_") + ".txt")
        if not os.path.exists(path):
            out.append(f"### {pos} {aid}  NO_SOURCE")
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = W.normalise(W.body_of(fh.read(), False))
        S = W.sites(text, prof)
        out.append(f"### {pos} {aid}  sites={len(S)}")
        for i, s in enumerate(S, 1):
            out.append(f"  [{i}] match={s['match']!r} value={s['value']!r}")
            out.append(f"      {s['window']}")
    body = "\n".join(out) + "\n"
    with open(os.path.join(HERE, a.out), "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"{len(ids)} ids -> {a.out} ({len(body)} chars)")


if __name__ == "__main__":
    main()
