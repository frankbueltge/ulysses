#!/usr/bin/env python3
"""site-validity-tick56 — the third end of the fraction, found while reading the second.

The registration asked two questions of stratum B: is a site-bearing paper an invoker,
and what does that do to the denominator. Reading the sieve's OWN sites to answer it
turned up a question it had not asked: **is the site a threshold statement at all?**

Of the 24 sampled site-bearing papers, the reading records three states in the `note`
column of `handread-tick56.csv`:

    site_real=yes                a threshold statement at the focus value
    site_real=yes, non-focus     a real threshold, at some other value (NMS, association,
                                 a criterion applied at 0.1 / 0.40 / 0.80)
    site_real=NO                 no threshold statement: the sieve matched a REPORTED
                                 IoU or mIoU value, or ran its gap from the term into an
                                 index like `_i=1`

The last class matters to this line's headline in the direction opposite to class B. A
paper with an invented site is a paper the numerator LOSES: it invokes the statistic,
states no threshold, and is filed as though it had. Class B flatters the claim; this
deflates it. Both are measured here, in one tick, on one literature.

This estimate is **post-hoc**. It was not forecast in `PREREGISTRATION-tick56.md`, it
rests on 24 papers, and it is printed with its Wilson interval and never folded into the
tick's headline rate. It is written as code so the arithmetic is checkable rather than
asserted in prose.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NON_INVOKER = {"X-ENGLISH", "X-LOSS", "X-SCORE", "X-CITE", "X-QUERY", "X-NOTATION",
               "X-OTHER"}


def wilson(x, n, z=1.96):
    p = x / float(n)
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [(c - s) / d, (c + s) / d]


def main():
    hand = list(csv.DictReader(open(os.path.join(HERE, "handread-tick56.csv"),
                                    encoding="utf-8")))
    tab = [r for r in csv.DictReader(open(os.path.join(HERE,
                                                       "remeasure-tick55-iou-0.5-0.6.csv"),
                                          encoding="utf-8"))
           if r["state"] == "measured" and r["mentioned"] == "1"]
    C = sum(1 for r in tab if int(r["sites"] or 0) == 0)
    S = sum(1 for r in tab if int(r["sites"] or 0) > 0)
    I = C + S

    b = [r for r in hand if r["stratum"] == "B"]
    a = [r for r in hand if r["stratum"] == "A"]
    X_A = sum(1 for r in a if r["label"] in NON_INVOKER)
    B_strict = sum(1 for r in a if r["label"] == "B-SITE")

    def state(r):
        n = r["note"]
        if "site_real=NO" in n:
            return "invented"
        if "non-focus" in n:
            return "real_nonfocus"
        return "real_focus"

    states = {}
    for r in b:
        states[state(r)] = states.get(state(r), 0) + 1
    invented = [r for r in b if state(r) == "invented"]
    # an invented site sends the paper back to the candidate class only if the paper is
    # an invoker; a non-invoker with an invented site leaves BOTH ends and is already
    # covered by the denominator correction.
    invented_invoker = [r for r in invented if r["label"] not in NON_INVOKER]

    n = len(b)
    x_ii = len(invented_invoker)
    lo, hi = wilson(x_ii, n)
    share_nb = sum(1 for r in b if r["label"] in NON_INVOKER) / float(n)
    X_B = share_nb * S
    den = I - X_A - X_B

    def rate(extra):
        return round(100.0 * (C - X_A - B_strict + extra) / den, 1)

    out = {
        "tick": 56, "status": "POST-HOC — not forecast in the registration",
        "sample": n, "of_site_bearing_class": S,
        "site_states": states,
        "site_states_pct": {k: round(100.0 * v / n, 1) for k, v in states.items()},
        "invented_sites": len(invented),
        "invented_and_invoker": x_ii,
        "invented_and_invoker_share_pct": round(100.0 * x_ii / n, 1),
        "invented_and_invoker_ci_pct": [round(100 * lo, 1), round(100 * hi, 1)],
        "papers_owed_to_the_numerator": round(x_ii / float(n) * S, 1),
        "papers_owed_to_the_numerator_ci": [round(lo * S, 1), round(hi * S, 1)],
        "rate_both_ends_strict_pct": rate(0),
        "rate_with_invented_sites_returned_pct": rate(x_ii / float(n) * S),
        "rate_with_invented_sites_returned_ci_pct": [rate(lo * S), rate(hi * S)],
        "reading": "the registration's corrected rate is a LOWER bound, not the answer: "
                   "a fault measured in this tick and not repaired moves it upward by "
                   "roughly as much as the denominator correction moved it down.",
    }
    path = os.path.join(HERE, "site-validity-tick56.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
