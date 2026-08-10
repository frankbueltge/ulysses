#!/usr/bin/env python3
"""denominator-tick52 — is a *mention* an *invocation*?

Every rate the fourth case reports divides by 205 mentions, and a mention is one regex
match anywhere in the LaTeX body. Tick 51 read the 37 papers the repaired sieve had moved
and found 13 of 17 bad moves were papers that never used the criterion at all. This script
asks the question of the frame instead of the movers.

Three subcommands, in the order the pre-registration fixes:

    census  --src DIR                  the machine layer over all CV mention papers
    sample  --seed 52                  draw 12 per literature, stratified in CV
    windows --src DIR --ids FILE       extract the matched windows a hand reader labels

The machine predicate is a sieve and is named one: M-NONINVOKER := bare_only or bbl_only.
`sample` writes its draw before any window is read, and `windows` refuses to run for an id
that is not in the drawn sample file, so the reading cannot quietly widen.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warrant_trace import Profile, body_of, normalise, read_ids   # noqa: E402

# The term regex of profiles/iou-0.5.json, split into the two families the pre-registration
# names. Kept as literal alternatives rather than re-derived from the profile, so that a
# later edit of the profile cannot silently redefine this tick's classes.
NAMED = re.compile(
    r"(?:\bIoUs?\b|\bmIoU\b|intersection[-\s]?over[-\s]?union"
    r"|Jaccard(?:\s+(?:index|similarity|coefficient))?"
    r"|(?:bounding[-\s]?box|bbox|box|mask)\s+overlap)", re.I)
BARE = re.compile(r"\boverlaps?\b", re.I)

LITERATURES = {
    "cv":   ("measure-iou-0.5-tick46.csv", "profiles/iou-0.5.json"),
    "gaia": ("measure-ruwe-1.4-tick35.csv", "profiles/ruwe-1.4.json"),
    "mcmc": ("measure-rhat-1.1-tick36.csv", "profiles/rhat-1.1.json"),
}


def rows(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def mention_ids(key):
    table, _ = LITERATURES[key]
    return [r["arxiv"] for r in rows(table)
            if r["state"] == "measured" and r["mentioned"] == "1"]


def bbl_spans(raw):
    """Character spans of the %%%FILE members whose name ends .bbl, in the raw text."""
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"%%%FILE ([^\n]+)\n", raw)]
    spans = []
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(raw)
        if name.strip().lower().endswith(".bbl"):
            spans.append((pos, end))
    return spans


def classify_paper(raw):
    """One record per paper: how its matches split, and where they stand."""
    text = normalise(body_of(raw, drop_comments=False))
    named = [m.span() for m in NAMED.finditer(text)]
    # a BARE hit inside a NAMED hit ("bounding box overlap") is not a bare match
    named_ranges = [(a, b) for a, b in named]
    bare = []
    for m in BARE.finditer(text):
        a, b = m.span()
        if any(x <= a and b <= y for x, y in named_ranges):
            continue
        bare.append((a, b))
    # bbl spans are computed on the *raw* text; normalise/body_of may shift offsets, so the
    # test is done on the raw text with the same two regexes rather than on mapped offsets.
    spans = bbl_spans(raw)
    def in_bbl(pos):
        return any(a <= pos < b for a, b in spans)
    raw_named = [m.start() for m in NAMED.finditer(raw)]
    raw_bare = [m.start() for m in BARE.finditer(raw)]
    raw_all = raw_named + raw_bare
    bbl_only = bool(raw_all) and all(in_bbl(p) for p in raw_all)
    return {
        "n_named": len(named), "n_bare": len(bare),
        "n_matches": len(named) + len(bare),
        "bare_only": len(named) == 0 and len(bare) > 0,
        "bbl_only": bbl_only,
        "chars": len(text),
    }


def census(args):
    ids = mention_ids("cv")
    out, missing = [], []
    for aid in ids:
        path = os.path.join(args.src, aid.replace("/", "_") + ".txt")
        if not os.path.exists(path):
            missing.append(aid)
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        rec = classify_paper(raw)
        rec["arxiv"] = aid
        rec["m_noninvoker"] = bool(rec["bare_only"] or rec["bbl_only"])
        out.append(rec)
    cols = ["arxiv", "n_matches", "n_named", "n_bare", "bare_only", "bbl_only",
            "m_noninvoker", "chars"]
    with open(os.path.join(HERE, "census-tick52.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in sorted(out, key=lambda r: r["arxiv"]):
            w.writerow({c: r[c] for c in cols})
    rep = {
        "tick": 52, "literature": "cv", "frame_tick": 46,
        "mention_papers_in_table": len(ids),
        "read_today": len(out), "not_refetched": missing,
        "bare_only": sum(1 for r in out if r["bare_only"]),
        "bbl_only": sum(1 for r in out if r["bbl_only"]),
        "m_noninvoker": sum(1 for r in out if r["m_noninvoker"]),
        "median_matches": sorted(r["n_matches"] for r in out)[len(out) // 2] if out else None,
    }
    rep["m_noninvoker_pct"] = round(100.0 * rep["m_noninvoker"] / len(out), 1) if out else None
    with open(os.path.join(HERE, "census-tick52.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print(json.dumps(rep, indent=1))


def sample(args):
    """12 per literature; CV stratified 6/6 on the machine predicate (census must exist)."""
    draw = []
    cen = {}
    cpath = os.path.join(HERE, "census-tick52.csv")
    if os.path.exists(cpath):
        cen = {r["arxiv"]: r["m_noninvoker"] == "True" for r in rows("census-tick52.csv")}
    for key in ("cv", "gaia", "mcmc"):
        ids = sorted(mention_ids(key))
        rng = random.Random(args.seed)
        if key == "cv" and cen:
            non = sorted(i for i in ids if cen.get(i))
            inv = sorted(i for i in ids if i in cen and not cen[i])
            picked = ([("M-NONINVOKER", i) for i in rng.sample(non, min(6, len(non)))]
                      + [("M-INVOKER", i) for i in rng.sample(inv, min(6, len(inv)))])
        else:
            picked = [("", i) for i in rng.sample(ids, min(12, len(ids)))]
        for stratum, aid in picked:
            draw.append({"literature": key, "stratum": stratum, "arxiv": aid,
                         "population": len(ids)})
    with open(os.path.join(HERE, "sample-tick52.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["literature", "stratum", "arxiv", "population"])
        w.writeheader()
        w.writerows(draw)
    print(f"drawn {len(draw)} papers, seed {args.seed} -> sample-tick52.csv")
    for r in draw:
        print(f"  {r['literature']:5s} {r['stratum']:14s} {r['arxiv']}")


def windows(args):
    """Matched windows for the drawn papers only — the sample file is the gate."""
    allowed = {r["arxiv"]: r for r in rows("sample-tick52.csv")}
    prof = Profile.load(os.path.join(HERE, args.profile))
    out = []
    for aid, meta in allowed.items():
        if meta["literature"] != args.literature:
            continue
        path = os.path.join(args.src, aid.replace("/", "_") + ".txt")
        if not os.path.exists(path):
            out.append({"arxiv": aid, "state": "no_source", "windows": []})
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = normalise(body_of(fh.read(), False))
        ws, seen = [], []
        for m in prof.term_re.finditer(text):
            a, b = m.span()
            if any(abs(a - p) < 200 for p in seen):
                continue
            seen.append(a)
            ws.append({"at": a, "match": m.group(0),
                       "text": text[max(0, a - 300):b + 300]})
            if len(ws) >= args.max:
                break
        out.append({"arxiv": aid, "state": "measured", "n_total": len(seen),
                    "windows": ws})
    path = os.path.join(HERE, f"windows-tick52-{args.literature}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"{len(out)} papers -> {os.path.basename(path)}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    c = s.add_parser("census"); c.add_argument("--src", required=True); c.set_defaults(f=census)
    d = s.add_parser("sample"); d.add_argument("--seed", type=int, default=52); d.set_defaults(f=sample)
    w = s.add_parser("windows")
    w.add_argument("--src", required=True)
    w.add_argument("--literature", required=True, choices=["cv", "gaia", "mcmc"])
    w.add_argument("--profile", required=True)
    w.add_argument("--max", type=int, default=6)
    w.set_defaults(f=windows)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
