#!/usr/bin/env python3
"""cv-census-tick56 — the named remainder, read; and the assumption, measured.

Tick 53 read the whole candidate class of gaia (53) and mcmc (20) and wrote computer
vision's 87 into its own §5 as the open remainder. Under the tick-55 repair the class is
**84**. This tick reads it.

It cannot reuse tick 53's arithmetic unchanged. That census corrected the numerator
exactly and corrected the denominator under one named, unmeasured assumption — that
non-invokers sit inside the candidate class. Tick 51 refuted that assumption in **this
literature**, where `overlap` has an English sense and IoU has lives outside the
correctness criterion (a loss, a reported score). So the reading is stratified:

    A  census   all 84 candidates          -> X_A, exact
    B  sample   24 of 121 site-bearing     -> X_B, an estimate WITH an interval

    corrected_rate = (C - X_A) / (I - X_A - X_B)

The interval on X_B is the only place uncertainty enters the arithmetic, and it is carried
through rather than dropped. See `PREREGISTRATION-tick56.md`.

    frame                     write both strata in a read order fixed by random.Random(56)
                              BEFORE any window is seen
    windows --stratum {A,B}   the matched windows of that stratum, in read order
    rates                     the corrected rate from the landed hand table

The read order is randomised for one reason: if the reading cannot be finished, what was
read is a random sample of the stratum rather than an alphabetical head of it. The
stopping rule is declared in the registration §5 and is not a function of the labels.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warrant_trace import Profile, body_of, normalise   # noqa: E402

# the 0.6 table — the instrument tick 55 repaired and the one this tick quotes.
TABLE = "remeasure-tick55-iou-0.5-0.6.csv"
PROFILE = "profiles/iou-0.5.json"
SAMPLE_B = 24          # fixed in the registration §1, before the draw
SEED = 56


def rows(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def strata():
    """(candidates, site_bearing) — the two ends of the fraction, from the 0.6 table."""
    cur = [r for r in rows(TABLE) if r["state"] == "measured" and r["mentioned"] == "1"]
    cand = sorted(r["arxiv"] for r in cur if int(r["sites"] or 0) == 0)
    site = sorted(r["arxiv"] for r in cur if int(r["sites"] or 0) > 0)
    return cand, site


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson(x, n, z=1.96):
    """95 % Wilson interval, in percent. Reported wherever a sample stands in for a class."""
    if n == 0:
        return None
    p = x / float(n)
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(100.0 * (c - s) / d, 1), round(100.0 * (c + s) / d, 1)]


def frame(args):
    cand, site = strata()
    rng_a = random.Random(args.seed)
    rng_b = random.Random(args.seed + 1000)     # a second stream: the draw must not be a
                                                # function of the census's shuffle
    order_a = list(cand)
    rng_a.shuffle(order_a)
    drawn = rng_b.sample(site, SAMPLE_B)
    order_b = list(drawn)
    rng_b.shuffle(order_b)

    out = []
    for pos, aid in enumerate(order_a, 1):
        out.append({"stratum": "A", "read_order": pos, "arxiv": aid,
                    "stratum_size": len(cand), "drawn_from": len(cand)})
    for pos, aid in enumerate(order_b, 1):
        out.append({"stratum": "B", "read_order": pos, "arxiv": aid,
                    "stratum_size": SAMPLE_B, "drawn_from": len(site)})

    path = os.path.join(HERE, "frame-tick56.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["stratum", "read_order", "arxiv",
                                           "stratum_size", "drawn_from"])
        w.writeheader()
        w.writerows(out)
    for s in ("A", "B"):
        with open(os.path.join(HERE, f"frame-tick56-{s}.txt"), "w", encoding="utf-8") as fh:
            for r in out:
                if r["stratum"] == s:
                    fh.write(r["arxiv"] + "\n")
    with open(os.path.join(HERE, "frame-tick56-all.txt"), "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(r["arxiv"] + "\n")
    print(json.dumps({"seed": args.seed, "candidates": len(cand),
                      "site_bearing": len(site), "sample_B": SAMPLE_B,
                      "total_to_read": len(out),
                      "sha256_frame_csv": sha256_file(path)}, indent=1))


def windows(args):
    allowed = [r for r in rows("frame-tick56.csv") if r["stratum"] == args.stratum]
    allowed.sort(key=lambda r: int(r["read_order"]))
    prof = Profile.load(os.path.join(HERE, PROFILE))
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
        # Spread over the paper, not taken from its head — tick 53's rule, kept unchanged
        # so the two censuses are read the same way: a paper's first matches are usually
        # abstract and related work, where a term is cited rather than used.
        if len(hits) > args.max:
            step = (len(hits) - 1) / float(args.max - 1) if args.max > 1 else 0
            idx = sorted({int(round(i * step)) for i in range(args.max)})
            hits = [hits[i] for i in idx]
        ws = [{"at": a, "match": g, "text": text[max(0, a - args.pad):b + args.pad]}
              for a, b, g in hits]
        out.append({"arxiv": aid, "read_order": int(meta["read_order"]),
                    "state": "measured", "n_total": len(seen), "windows": ws})
    path = os.path.join(HERE, f"windows-tick56-{args.stratum}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"{len(out)} papers -> {os.path.basename(path)}")


NON_INVOKER = {"X-ENGLISH", "X-LOSS", "X-SCORE", "X-CITE", "X-QUERY", "X-NOTATION",
               "X-OTHER"}
INVOKER = {"I-USE", "I-DISC", "I-NAME", "B-SITE", "B-SITE-WEAK"}


def rates(args):
    """Both ends of the fraction, and the interval where it belongs.

    X_A is a census count and carries no sampling error. X_B is an extrapolation from 24
    of 121 papers and carries a Wilson interval; the corrected rate is therefore reported
    as an interval, with the point value marked as the centre of an estimate rather than
    a measurement.
    """
    hand = {r["arxiv"]: r for r in rows("handread-tick56.csv")}
    cand, site = strata()
    C, S = len(cand), len(site)
    I = C + S

    a_read = [a for a in cand if a in hand]
    a_non = [a for a in a_read if hand[a]["label"] in NON_INVOKER]
    a_b = [a for a in a_read if hand[a]["label"] == "B-SITE"]
    a_bw = [a for a in a_read if hand[a]["label"] == "B-SITE-WEAK"]
    a_name = [a for a in a_read if hand[a]["label"] == "I-NAME"]
    census_complete = len(a_read) == C

    b_read = [a for a in site if a in hand]
    b_non = [a for a in b_read if hand[a]["label"] in NON_INVOKER]

    modes = {}
    for a in a_non:
        modes[hand[a]["label"]] = modes.get(hand[a]["label"], 0) + 1
    modes_b = {}
    for a in b_non:
        modes_b[hand[a]["label"]] = modes_b.get(hand[a]["label"], 0) + 1

    X_A = len(a_non)
    share_b = (len(b_non) / float(len(b_read))) if b_read else None
    ci_b = wilson(len(b_non), len(b_read)) if b_read else None

    def corrected(share, strict=False, weak=False):
        if share is None:
            return None
        X_B = share * S
        num = C - X_A - (len(a_b) if strict else 0) - (len(a_bw) if weak else 0)
        den = I - X_A - X_B
        return round(100.0 * num / den, 1) if den > 0 else None

    out = {
        "tick": 56, "literature": "cv", "instrument": "0.6",
        "design": "stratum A: census of the 84 candidates; stratum B: 24 of 121 "
                  "site-bearing papers, drawn by seed before any window was read",
        "note": "the first rate in this line with BOTH ends measured. X_A is exact; X_B "
                "is an extrapolation and carries its Wilson interval through the "
                "arithmetic rather than being reported as a point.",
        "invoking_papers": I, "candidates": C, "site_bearing": S,
        "rate_now_pct": round(100.0 * C / I, 1),
        "stratum_A": {
            "size": C, "read": len(a_read), "census_complete": census_complete,
            "non_invokers": X_A,
            "non_invoker_share_pct": round(100.0 * X_A / len(a_read), 1) if a_read else None,
            "class_B_strict": len(a_b), "class_B_weak": len(a_bw),
            "I_NAME": len(a_name),
            "modes": modes,
            "labels": {k: sum(1 for a in a_read if hand[a]["label"] == k)
                       for k in sorted({hand[a]["label"] for a in a_read})},
        },
        "stratum_B": {
            "drawn": SAMPLE_B, "read": len(b_read), "of_class": S,
            "non_invokers": len(b_non),
            "non_invoker_share_pct": round(100.0 * share_b, 1) if share_b is not None else None,
            "ci95_pct": ci_b,
            "modes": modes_b,
            "labels": {k: sum(1 for a in b_read if hand[a]["label"] == k)
                       for k in sorted({hand[a]["label"] for a in b_read})},
        },
    }
    if census_complete and share_b is not None:
        lo, hi = ci_b[0] / 100.0, ci_b[1] / 100.0
        # a LARGER non-invoker share shrinks the denominator and RAISES the rate, so the
        # rate's interval runs corrected(lo) .. corrected(hi) and is written that way
        # round; printing it in the share's order would put the numbers backwards.
        out["corrected"] = {
            "denominator_corrected_pct": corrected(share_b),
            "denominator_corrected_ci_pct": [corrected(lo), corrected(hi)],
            "both_ends_strict_pct": corrected(share_b, strict=True),
            "both_ends_strict_ci_pct": [corrected(lo, strict=True),
                                        corrected(hi, strict=True)],
            "both_ends_with_weak_pct": corrected(share_b, strict=True, weak=True),
            "X_A_exact": X_A,
            "X_B_point": round(share_b * S, 1),
            "X_B_ci": [round(lo * S, 1), round(hi * S, 1)],
        }
    else:
        out["corrected"] = None
        out["corrected_withheld_because"] = (
            "stratum A incomplete" if not census_complete else "stratum B unread")
        out["unread_A"] = [a for a in cand if a not in hand]
    path = os.path.join(HERE, "rates-tick56.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("frame")
    f.add_argument("--seed", type=int, default=SEED)
    f.set_defaults(fn=frame)
    w = sub.add_parser("windows")
    w.add_argument("--stratum", required=True, choices=["A", "B"])
    w.add_argument("--src", required=True)
    w.add_argument("--max", type=int, default=3)
    w.add_argument("--pad", type=int, default=220)
    w.set_defaults(fn=windows)
    r = sub.add_parser("rates")
    r.set_defaults(fn=rates)
    a = ap.parse_args()
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
