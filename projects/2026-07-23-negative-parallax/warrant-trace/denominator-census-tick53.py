#!/usr/bin/env python3
"""denominator-census-tick53 — read the whole candidate class, not a sample of it.

Tick 52 asked whether a *mention* is an *invocation* and answered it on six candidate
papers. Six papers buy a Wilson interval sixty points wide; the record says so in its own
words, refuses to extend the sample after seeing which way it pointed, and names the size
the question needs. This tick does not draw a larger sample. It reads the **entire
candidate class** in the two literatures where the class is small enough to be read whole:

    candidate := the 0.5 instrument measures the paper, finds the term (`mentioned == 1`)
                 and finds no site at the focus value (`sites == 0`)

That is exactly the class the fourth reading's numerator is built from — *invokes the
statistic and states no threshold* — so a census of it removes sampling error from the
numerator correction entirely. What a census cannot remove is my judgement, one paper at
a time; that stays the load-bearing step, as in every tick of this line.

    frame                    write the candidate ids of gaia and mcmc, in a read order
                             fixed by `random.Random(53)` BEFORE any window is seen
    windows --literature L   the matched windows of the frame's papers, in read order
    rates                    census-corrected rates from the landed hand table

The read order is randomised for one reason: if the reading cannot be finished, what was
read is a random sample of the class rather than an alphabetical head of it. The stopping
rule is declared in `PREREGISTRATION-tick53.md` §5 and is not a function of the labels.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warrant_trace import Profile, body_of, normalise   # noqa: E402

# the 0.5 tables — the instrument this line currently quotes (tick 50), corrected for the
# movers at tick 51. Candidate counts at the time of writing: gaia 53, mcmc 20, cv 87.
TABLES = {"gaia": ("remeasure-tick50-ruwe-1.4-0.5.csv", "profiles/ruwe-1.4.json"),
          "mcmc": ("remeasure-tick50-rhat-1.1-0.5.csv", "profiles/rhat-1.1.json"),
          "cv":   ("remeasure-tick50-iou-0.5-0.5.csv",  "profiles/iou-0.5.json")}

IN_SCOPE = ("gaia", "mcmc")   # cv's 87 are the named remainder, §5 of the registration


def rows(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def candidates(lit):
    table, _ = TABLES[lit]
    return sorted(r["arxiv"] for r in rows(table)
                  if r["state"] == "measured" and r["mentioned"] == "1"
                  and int(r["sites"] or 0) == 0)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def frame(args):
    out = []
    for lit in IN_SCOPE:
        ids = candidates(lit)
        order = list(ids)
        random.Random(args.seed).shuffle(order)
        for pos, aid in enumerate(order, 1):
            out.append({"literature": lit, "read_order": pos, "arxiv": aid,
                        "class_size": len(ids)})
    path = os.path.join(HERE, "frame-tick53.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["literature", "read_order", "arxiv",
                                           "class_size"])
        w.writeheader()
        w.writerows(out)
    for lit in IN_SCOPE:
        ipath = os.path.join(HERE, f"frame-tick53-{lit}.txt")
        with open(ipath, "w", encoding="utf-8") as fh:
            for r in out:
                if r["literature"] == lit:
                    fh.write(r["arxiv"] + "\n")
    print(json.dumps({"seed": args.seed,
                      "classes": {l: len(candidates(l)) for l in IN_SCOPE},
                      "total": len(out),
                      "sha256_frame_csv": sha256_file(path)}, indent=1))


def windows(args):
    allowed = [r for r in rows("frame-tick53.csv") if r["literature"] == args.literature]
    allowed.sort(key=lambda r: int(r["read_order"]))
    _, profile = TABLES[args.literature]
    prof = Profile.load(os.path.join(HERE, profile))
    out = []
    for meta in allowed:
        aid = meta["arxiv"]
        path = os.path.join(args.src, aid.replace("/", "_") + ".txt")
        if not os.path.exists(path):
            out.append({"arxiv": aid, "read_order": int(meta["read_order"]),
                        "state": "no_source", "windows": []})
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = normalise(body_of(fh.read(), False))
        hits, seen = [], []
        for m in prof.term_re.finditer(text):
            a, b = m.span()
            if any(abs(a - p) < 200 for p in seen):
                continue
            seen.append(a)
            hits.append((a, b, m.group(0)))
        # Windows are spread evenly over the paper, not taken from its head. A paper's
        # first three matches are usually its abstract and introduction, where a term is
        # cited rather than used; taking the head would systematically show me the
        # citation and hide the methods section. Chosen before any window was read.
        if len(hits) > args.max:
            step = (len(hits) - 1) / float(args.max - 1) if args.max > 1 else 0
            idx = sorted({int(round(i * step)) for i in range(args.max)})
            hits = [hits[i] for i in idx]
        ws = [{"at": a, "match": g, "text": text[max(0, a - args.pad):b + args.pad]}
              for a, b, g in hits]
        out.append({"arxiv": aid, "read_order": int(meta["read_order"]),
                    "state": "measured", "n_total": len(seen), "windows": ws})
    path = os.path.join(HERE, f"windows-tick53-{args.literature}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"{len(out)} papers -> {os.path.basename(path)}")


def rates(args):
    """Census arithmetic. No interval on the share: the class is read whole.

    corrected_rate = (candidates - non_invoker_candidates) / (invoking - non_invokers)

    with the assumption stated in the registration §3 and NOT hidden here: for gaia and
    mcmc, non-invokers are taken to sit inside the candidate class, because a paper with a
    site at the focus value states `ruwe < 1.4` / `R-hat < 1.1` and is using the thing.
    Tick 51's class C is the known exception and was found in computer vision, which this
    census does not cover.
    """
    hand = {r["arxiv"]: r for r in rows("handread-census-tick53.csv")}
    out = {"tick": 53, "design": "census of the candidate class, gaia + mcmc",
           "note": "both ends of the fraction are read: non-invokers leave numerator and "
                   "denominator, class-B papers leave the numerator only (they state a "
                   "threshold, so they are not what the numerator claims, but they do "
                   "invoke the statistic).",
           "literatures": {}}
    pooled_n = pooled_x = 0
    for lit in IN_SCOPE:
        table, _ = TABLES[lit]
        cur = rows(table)
        measured = [r for r in cur if r["state"] == "measured"]
        invoking = [r for r in measured if r["mentioned"] == "1"]
        cand = [r["arxiv"] for r in invoking if int(r["sites"] or 0) == 0]
        read = [a for a in cand if a in hand]
        non = [a for a in read if hand[a]["invoker"] == "0"]
        bsite = [a for a in read if hand[a]["label"] == "B-SITE"]
        bweak = [a for a in read if hand[a]["label"] == "B-SITE-WEAK"]
        modes = {}
        for a in non:
            modes[hand[a]["label"]] = modes.get(hand[a]["label"], 0) + 1
        C, I, X, B, Bw = len(cand), len(invoking), len(non), len(bsite), len(bweak)
        complete = len(read) == C
        # the corrections, computed only on a complete census; on a partial read the
        # numbers below are reported as a random sample and marked as such
        den, corr, corr_b, corr_bw = I - X, None, None, None
        if complete and den > 0:
            corr = round(100.0 * (C - X) / den, 1)          # denominator read
            corr_b = round(100.0 * (C - X - B) / den, 1)     # both ends read, strict
            corr_bw = round(100.0 * (C - X - B - Bw) / den, 1)  # weak calls included
        out["literatures"][lit] = {
            "invoking": I, "candidates": C, "read": len(read),
            "census_complete": complete,
            "non_invokers": X,
            "non_invoker_share_pct": round(100.0 * X / len(read), 1) if read else None,
            "class_B_strict": B, "class_B_weak": Bw,
            "class_B_share_pct": round(100.0 * B / len(read), 1) if read else None,
            "rate_now_pct": round(100.0 * C / I, 1),
            "rate_denominator_corrected_pct": corr,
            "rate_both_ends_corrected_pct": corr_b,
            "rate_both_ends_with_weak_calls_pct": corr_bw,
            "modes": modes,
            "labels": {k: sum(1 for a in read if hand[a]["label"] == k)
                       for k in sorted({hand[a]["label"] for a in read})},
        }
        pooled_n += len(read)
        pooled_x += X
    out["pooled"] = {"read": pooled_n, "non_invokers": pooled_x,
                     "share_pct": round(100.0 * pooled_x / pooled_n, 1) if pooled_n else None,
                     "tick52_sample": {"read": 6, "non_invokers": 4, "share_pct": 66.7,
                                       "ci95_pct": [30.0, 90.3]},
                     "inside_tick52_interval": None}
    p = out["pooled"]["share_pct"]
    p52 = out["pooled"]["tick52_sample"]["ci95_pct"]
    out["pooled"]["inside_tick52_interval"] = (p is not None and p52[0] <= p <= p52[1])
    g, m = out["literatures"]["gaia"], out["literatures"]["mcmc"]
    out["forecasts"] = {
        "P1 gaia non-invoker share in [20,60] pct": 20.0 <= g["non_invoker_share_pct"] <= 60.0,
        "P2 mcmc non-invoker share in [20,60] pct": 20.0 <= m["non_invoker_share_pct"] <= 60.0,
        "P5 pooled share inside tick52 CI": out["pooled"]["inside_tick52_interval"],
        "P6 gaia denominator-corrected rate in (0,12) pct":
            g["rate_denominator_corrected_pct"] is not None
            and 0.0 < g["rate_denominator_corrected_pct"] < 12.0,
        "D8 class B (strict) at most 6 of 73":
            (g["class_B_strict"] + m["class_B_strict"]) <= 6,
    }
    with open(os.path.join(HERE, "rates-tick53.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    f = s.add_parser("frame"); f.add_argument("--seed", type=int, default=53)
    f.set_defaults(fn=frame)
    w = s.add_parser("windows")
    w.add_argument("--src", required=True)
    w.add_argument("--literature", required=True, choices=list(TABLES))
    w.add_argument("--max", type=int, default=4)
    w.add_argument("--pad", type=int, default=260)
    w.set_defaults(fn=windows)
    r = s.add_parser("rates"); r.set_defaults(fn=rates)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
