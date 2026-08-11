#!/usr/bin/env python3
"""cv-siteclass-tick57 — the third end of the fraction, read whole.

Tick 56 read computer vision's candidate class as a census (stratum A, 84 papers) and
its site-bearing class as a **sample** (stratum B, 24 of 121). Two things came out of
that sample, and both are estimates:

    X_B          how many site-bearing papers are not invokers at all
                 5 of 24 = 20.8 %, Wilson 95 % [9.2, 40.5] -> the ONLY interval in the
                 corrected rate's arithmetic

    invented     how many of the sieve's OWN sites are not threshold statements
                 7 of 24 = 29.2 %; of those, 3 are invented-and-invoker, the papers the
                 numerator LOSES. This was found while answering the first question and
                 was never forecast, so tick 56 declared it post-hoc and refused to make
                 it the headline. It is why 28.4 % was written as a **lower bound**.

This tick reads the remaining **97**. With 121 of 121 read, X_B becomes a count and the
corrected rate loses its interval entirely; the invented-site share becomes a census of
the class rather than an estimate over 24 papers, and the number tick 56 could only
bracket — how far the sieve's own inventions deflate this line's headline — is measured.

    frame                     the 97 unread site-bearing ids, in a read order fixed by
                              random.Random(57) BEFORE any window is seen
    windows                   the matched windows, in read order, extracted by tick 56's
                              OWN function, imported by path so no rule is retyped
    rates                     the census arithmetic over both hand tables together

The frame is the tick-56 frame's complement, computed from the landed table rather than
asserted: `strata()` re-derives the 121 from `remeasure-tick55-iou-0.5-0.6.csv` and the
24 are removed by id. If the two ever disagree the script refuses to write a frame.

Read order is randomised for the reason tick 56 gave: a reading that cannot be finished
should leave a random sample of the class behind, not its alphabetical head. The stopping
rule is in `PREREGISTRATION-tick57.md` §5 and is not a function of the labels.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# tick 56's census script is imported by path, not copied: the window rule (200-char
# de-duplication, spread over the paper rather than taken from its head), the label
# vocabulary and the strata definition are the SAME objects in both ticks, so the two
# halves of one census cannot drift apart by a retyped constant.
_spec = importlib.util.spec_from_file_location(
    "cv_census_tick56", os.path.join(HERE, "cv-census-tick56.py"))
T56 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T56)

SEED = 57
# the stratum name this tick's frame rows carry: it is what keeps the extractor's
# derived output filename out of tick 56's. See `windows()`.
STRATUM = "B-tick57"
HAND56 = "handread-tick56.csv"
HAND57 = "handread-tick57.csv"


def rows(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson(x, n, z=1.96):
    if n == 0:
        return None
    p = x / float(n)
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(100.0 * (c - s) / d, 1), round(100.0 * (c + s) / d, 1)]


def already_read():
    """The 24 ids of tick 56's stratum B, taken from the LANDED hand table."""
    return {r["arxiv"] for r in rows(HAND56) if r["stratum"] == "B"}


def frame(args):
    cand, site = T56.strata()
    read = already_read()
    stray = sorted(read - set(site))
    if stray:
        print("REFUSED: tick 56 read ids that are not in the site-bearing class today: "
              + ", ".join(stray), file=sys.stderr)
        return 1
    remaining = sorted(set(site) - read)
    order = list(remaining)
    random.Random(args.seed).shuffle(order)

    path = os.path.join(HERE, "frame-tick57.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["stratum", "read_order", "arxiv",
                                           "class_size", "read_at_tick56"])
        w.writeheader()
        for pos, aid in enumerate(order, 1):
            w.writerow({"stratum": "B", "read_order": pos, "arxiv": aid,
                        "class_size": len(site), "read_at_tick56": len(read)})
    with open(os.path.join(HERE, "frame-tick57.txt"), "w", encoding="utf-8") as fh:
        for aid in order:
            fh.write(aid + "\n")
    print(json.dumps({"seed": args.seed, "candidates": len(cand),
                      "site_bearing": len(site), "read_at_tick56": len(read),
                      "to_read_now": len(order),
                      "census_after": len(read) + len(order),
                      "sha256_frame_csv": sha256_file(path)}, indent=1))


def windows(args):
    """Tick 56's extractor, run over tick 57's frame — without touching a landed file.

    `T56.windows` hard-codes the frame it reads (`frame-tick56.csv`) and derives its
    output name from the stratum (`windows-tick56-<stratum>.json`). The first version of
    this function swapped the frame file on disk and renamed the output afterwards. That
    is the defect tick 56 found in `drift-tick53.py` — a later tick writing over an
    earlier tick's landed record — rebuilt on purpose, and it is not run.

    What is done instead touches nothing on disk: the module-level `rows` that
    `T56.windows` calls is replaced for the duration of the call, and this tick's frame
    rows carry the stratum name `B-tick57`, so the output file the extractor derives
    cannot collide with tick 56's. The extraction rules — the 200-character
    de-duplication, the spread over the paper, the profile — are the same objects, not
    copies of them.
    """
    mine = rows("frame-tick57.csv")
    for r in mine:
        r["stratum"] = STRATUM
    original = T56.rows
    T56.rows = lambda name: mine if name == "frame-tick56.csv" else original(name)
    try:
        ns = argparse.Namespace(stratum=STRATUM, src=args.src, max=args.max,
                                pad=args.pad)
        T56.windows(ns)
    finally:
        T56.rows = original
    produced = os.path.join(HERE, f"windows-tick56-{STRATUM}.json")
    os.replace(produced, os.path.join(HERE, "windows-tick57.json"))
    print("windows-tick57.json written; no landed file was opened for writing")


def corrections():
    """Label corrections against tick 56's LANDED table, applied visibly.

    Nothing landed is rewritten. `handread-tick56.csv` stays byte-identical; the
    corrections live in `correction-tick56-labels.csv` beside it, each with the evidence
    that produced it, and this function is the only place they enter an arithmetic. The
    report names them, so a rate computed here can be traced back to the table it was
    NOT computed from.
    """
    path = os.path.join(HERE, "correction-tick56-labels.csv")
    if not os.path.exists(path):
        return {}
    return {r["arxiv"]: r for r in rows("correction-tick56-labels.csv")}


def rates(args):
    """The corrected rate with BOTH ends counted, and the third end counted too."""
    cand, site = T56.strata()
    C, S = len(cand), len(site)
    I = C + S
    corr = corrections()
    hand = {}
    for name in (HAND56, HAND57):
        for r in rows(name):
            r["_from"] = name
            if r["arxiv"] in corr:
                r["_landed_label"] = r["label"]
                r["label"] = corr[r["arxiv"]]["corrected_label"]
            hand[r["arxiv"]] = r

    def site_state(r):
        """Tick 57 writes the state in its own column; tick 56 buried it in `note`.

        Both are read here, and the tick-56 branch is the same string test its own
        script used, so the two halves are classified by one rule.
        """
        if r.get("site_state"):
            return {"site_real=NO": "invented",
                    "site_real=yes, non-focus": "real_nonfocus"}.get(r["site_state"],
                                                                    "real_focus")
        n = r["note"]
        if "site_real=NO" in n:
            return "invented"
        if "non-focus" in n:
            return "real_nonfocus"
        return "real_focus"

    def states_threshold(r):
        # tick 56 recorded no such column; all three of its invented-and-invoker papers
        # are I-NAME, which means by definition that the number is stated nowhere, and
        # the corrected fourth (2607.27585v1) was checked the same way: 0 threshold-
        # shaped sentences. So the tick-56 default of "no" is a checked default.
        return r.get("states_threshold", "no") == "yes"

    a_read = [a for a in cand if a in hand]
    a_non = [a for a in a_read if hand[a]["label"] in T56.NON_INVOKER]
    a_b = [a for a in a_read if hand[a]["label"] == "B-SITE"]
    a_bw = [a for a in a_read if hand[a]["label"] == "B-SITE-WEAK"]
    X_A = len(a_non)

    b_read = [a for a in site if a in hand]
    b_non = [a for a in b_read if hand[a]["label"] in T56.NON_INVOKER]
    census_B = len(b_read) == S

    states, modes_b, labels_b = {}, {}, {}
    for a in b_read:
        s = site_state(hand[a])
        states[s] = states.get(s, 0) + 1
        labels_b[hand[a]["label"]] = labels_b.get(hand[a]["label"], 0) + 1
    for a in b_non:
        modes_b[hand[a]["label"]] = modes_b.get(hand[a]["label"], 0) + 1

    invented_invoker = [a for a in b_read
                        if site_state(hand[a]) == "invented"
                        and hand[a]["label"] not in T56.NON_INVOKER]
    returned = [a for a in invented_invoker if not states_threshold(hand[a])]

    X_B = len(b_non)
    R = len(returned)
    den = I - X_A - X_B

    def rate(num_extra=0, strict=False, weak=False):
        num = C - X_A - (len(a_b) if strict else 0) - (len(a_bw) if weak else 0) + num_extra
        return round(100.0 * num / den, 1) if den > 0 else None

    def by_half(pred):
        return {"tick56": sum(1 for a in b_read
                              if hand[a]["_from"] == HAND56 and pred(hand[a])),
                "tick57": sum(1 for a in b_read
                              if hand[a]["_from"] == HAND57 and pred(hand[a]))}

    out = {
        "tick": 57, "literature": "cv", "instrument": "0.6",
        "design": "census of BOTH classes: stratum A 84/84 (tick 56), stratum B "
                  f"{len(b_read)}/{S} (tick 56: 24, tick 57: {len(b_read) - 24}). "
                  "No sampling error enters any figure below.",
        "corrections_applied": [{"arxiv": k, "from": v["landed_label"],
                                 "to": v["corrected_label"], "found_by": v["found_by"]}
                                for k, v in corr.items()],
        "invoking_papers": I, "candidates": C, "site_bearing": S,
        "rate_as_landed_pct": round(100.0 * C / I, 1),
        "stratum_A": {"size": C, "read": len(a_read), "non_invokers": X_A,
                      "class_B_strict": len(a_b), "class_B_weak": len(a_bw),
                      "NOT re-read at tick 57": True},
        "stratum_B": {
            "size": S, "read": len(b_read), "census_complete": census_B,
            "non_invokers": X_B,
            "non_invoker_share_pct": round(100.0 * X_B / len(b_read), 1) if b_read else None,
            "non_invokers_by_half": by_half(lambda r: r["label"] in T56.NON_INVOKER),
            "tick56_estimate_pct": 20.8, "tick56_ci_pct": [9.2, 40.5],
            "tick56_X_B_point": 25.2, "tick56_X_B_ci": [11.1, 49.0],
            "modes": modes_b, "labels": labels_b,
        },
        "site_validity": {
            "read": len(b_read), "states": states,
            "states_pct": {k: round(100.0 * v / len(b_read), 1)
                           for k, v in states.items()},
            "invented_by_half": by_half(lambda r: site_state(r) == "invented"),
            "invented_and_invoker": len(invented_invoker),
            "returned_to_numerator": R,
            "withheld_because_it_states_a_threshold":
                [a for a in invented_invoker if states_threshold(hand[a])],
            "I_NAME_among_invented_invokers":
                sum(1 for a in invented_invoker if hand[a]["label"] == "I-NAME"),
            "tick56_estimate": {"invented_pct": 29.2, "invented_and_invoker_pct": 12.5,
                                "papers_owed_point": 15.1, "papers_owed_ci": [5.3, 37.5]},
        },
    }
    if census_B and len(a_read) == C:
        out["corrected"] = {
            "denominator_corrected_pct": rate(),
            "both_ends_strict_pct": rate(strict=True),
            "both_ends_with_weak_pct": rate(strict=True, weak=True),
            "with_invented_sites_returned_pct": rate(num_extra=R, strict=True),
            "X_A_exact": X_A, "X_B_exact": X_B, "returned_exact": R,
            "denominator": den,
            "interval": "none - every quantity in this fraction is a count",
        }
    else:
        out["corrected"] = None
        out["corrected_withheld_because"] = (
            "stratum B incomplete" if not census_B else "stratum A incomplete")
        out["unread_B"] = [a for a in site if a not in hand]
        out["partial_estimate"] = {
            "non_invoker_share_pct": round(100.0 * X_B / len(b_read), 1) if b_read else None,
            "ci95_pct": wilson(X_B, len(b_read)),
        }
    path = os.path.join(HERE, "rates-tick57.json")
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
    w.add_argument("--src", required=True)
    w.add_argument("--max", type=int, default=3)
    w.add_argument("--pad", type=int, default=220)
    w.set_defaults(fn=windows)
    r = sub.add_parser("rates")
    r.set_defaults(fn=rates)
    args = ap.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == "__main__":
    main()
