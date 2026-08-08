#!/usr/bin/env python3
"""Split the tick-47 measurement into its four time strata, by code rather than by hand.

The frame is stratified; the instrument is not stratum-aware. Rather than sorting rows by
eye, this joins every output table back onto `frame-tick47.json` on the arXiv id and
aggregates per era. It computes nothing the instrument did not measure — it only groups.

    python3 era-split-tick47.py --frame frame-tick47.json \
        --measure measure-iou-0.5-tick47.csv \
        --absorbed name-absorbed-tick47.csv \
        [--handread handread-iou-0.5-tick47.csv] \
        --out era-split-tick47

Writes <out>.json (the per-era summary) and prints the tables. The hand-reading is
optional because it does not exist yet when the machine counts are first read; the
per-era criterion-site table appears only once it is supplied.

Rates are only printed where the era's no_source share is at or under D3's 15 % bar
(PREREGISTRATION-tick47.md); above it the era prints counts and the string OVER-D3.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

ERA_ORDER = ["E1", "E2", "E3", "E4"]
D3_BAR = 0.15


def load_frame(path: str) -> tuple[dict, dict]:
    with open(path, encoding="utf-8") as fh:
        rec = json.load(fh)
    era_of, quarter_of = {}, {}
    for p in rec["papers"]:
        era_of[p["id"]] = p["era"]
        quarter_of[p["id"]] = p["quarter"]
    return era_of, quarter_of


def rows(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frame", required=True)
    ap.add_argument("--measure", required=True)
    ap.add_argument("--absorbed", required=True)
    ap.add_argument("--handread")
    ap.add_argument("--src", help="corpus, for the whole-paper citation count")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    era_of, _ = load_frame(args.frame)
    summary = {e: {"era": e} for e in ERA_ORDER}

    # ---- the sieve, per era -------------------------------------------------
    unknown = set()
    for r in rows(args.measure):
        era = era_of.get(r["arxiv"])
        if era is None:
            unknown.add(r["arxiv"])
            continue
        s = summary[era]
        s["frame"] = s.get("frame", 0) + 1
        if r["state"] != "measured":
            s["no_source"] = s.get("no_source", 0) + 1
            continue
        s["readable"] = s.get("readable", 0) + 1
        s["mentioning"] = s.get("mentioning", 0) + (1 if int(r["mentioned"]) else 0)
        sites = int(r["sites"])
        s["sites"] = s.get("sites", 0) + sites
        if sites:
            s["papers_with_site"] = s.get("papers_with_site", 0) + 1

    # ---- name absorption, per era ------------------------------------------
    for r in rows(args.absorbed):
        era = era_of.get(r["arxiv"])
        if era is None or r["state"] != "measured":
            continue
        s = summary[era]
        states = int(r["states_threshold"]) > 0
        absorbed = int(r["focus_absorbed"]) > 0
        if states:
            s["states_threshold"] = s.get("states_threshold", 0) + 1
        if absorbed:
            s["carries_name"] = s.get("carries_name", 0) + 1
        if absorbed and not states:
            s["name_only"] = s.get("name_only", 0) + 1
        s["ap50_occurrences"] = s.get("ap50_occurrences", 0) + int(r["ap50"])

    # ---- the hand, per era --------------------------------------------------
    if args.handread:
        for r in rows(args.handread):
            era = era_of.get(r["arxiv"])
            if era is None:
                continue
            s = summary[era]
            role = (r.get("role") or "").strip()
            s.setdefault("roles", {})
            s["roles"][role] = s["roles"].get(role, 0) + 1
            s["handread_sites"] = s.get("handread_sites", 0) + 1
            if role != "criterion":
                continue
            s["criterion_sites"] = s.get("criterion_sites", 0) + 1
            doc = (r.get("hand_document") or "none").strip() or "none"
            s.setdefault("documents", {})
            s["documents"][doc] = s["documents"].get(doc, 0) + 1
            s.setdefault("_crit_papers", set()).add(r["arxiv"])
            if doc == "voc":
                s.setdefault("_voc_papers", set()).add(r["arxiv"])

    # ---- the deriving document at ANY site, whatever the site governs -------
    # The role split is a judgement of mine and the strict count depends on it.
    # This second count does not: it asks only whether the deriving document is
    # cited FOR THE NUMBER anywhere the number stands. Reported beside the strict
    # count so a reader can see what the judgement is worth.
    if args.handread:
        for r in rows(args.handread):
            era = era_of.get(r["arxiv"])
            if era is None or (r.get("hand_document") or "") != "voc":
                continue
            summary[era]["voc_any_role"] = summary[era].get("voc_any_role", 0) + 1

    # ---- is the document absent from the SITE, or absent from the PAPER? ----
    # Post-hoc, and declared as post-hoc: not in PREREGISTRATION-tick47.md. It was
    # written because the strict count came back at zero for E1 and the zero has two
    # very different meanings — a literature that does not know the document, and a
    # literature that has it in the bibliography and never puts it at the sentence.
    if args.handread and args.src:
        import os
        import re as _re
        anywhere = _re.compile(r"everingham", _re.I)
        for e in ERA_ORDER:
            ids = summary[e].get("_crit_papers") or set()
            hits = 0
            for aid in sorted(ids):
                path = os.path.join(args.src, aid.replace("/", "_") + ".txt")
                if not os.path.exists(path):
                    continue
                with open(path, encoding="utf-8", errors="replace") as fh:
                    if anywhere.search(fh.read()):
                        hits += 1
            summary[e]["crit_papers_citing_deriver_anywhere"] = hits

    for e in ERA_ORDER:
        s = summary[e]
        frame = s.get("frame", 0)
        s["no_source"] = s.get("no_source", 0)
        s["no_source_share"] = round(s["no_source"] / frame, 4) if frame else None
        s["over_d3"] = bool(frame and s["no_source"] / frame > D3_BAR)
        s["criterion_papers"] = len(s.pop("_crit_papers", set()) or set())
        s["voc_papers"] = len(s.pop("_voc_papers", set()) or set())
        crit = s.get("criterion_sites", 0)
        if crit:
            voc = s.get("documents", {}).get("voc", 0)
            coco = s.get("documents", {}).get("coco", 0)
            s["voc_share"] = round(voc / crit, 4)
            s["coco_share"] = round(coco / crit, 4)
            s["none_share"] = round(s.get("documents", {}).get("none", 0) / crit, 4)
        hs = s.get("handread_sites", 0)
        if hs:
            s["collision_share"] = round((hs - crit) / hs, 4)

    if unknown:
        print(f"WARNING: {len(unknown)} rows not in the frame, ignored: "
              f"{sorted(unknown)[:5]}", file=sys.stderr)

    with open(args.out + ".json", "w", encoding="utf-8") as fh:
        json.dump({"eras": [summary[e] for e in ERA_ORDER],
                   "d3_bar": D3_BAR,
                   "unknown_rows": sorted(unknown)}, fh, indent=1)

    def cell(s, key, pct=False):
        v = s.get(key)
        if v is None:
            return "-"
        if s.get("over_d3") and pct:
            return "OVER-D3"
        return f"{v*100:.1f}%" if pct else str(v)

    print(f"\n{'':26}" + "".join(f"{e:>12}" for e in ERA_ORDER))
    for label, key, pct in [
        ("frame", "frame", False),
        ("no LaTeX source", "no_source", False),
        ("  as share", "no_source_share", True),
        ("readable", "readable", False),
        ("mentioning the statistic", "mentioning", False),
        ("papers w/ threshold site", "papers_with_site", False),
        ("sites, all values", "sites", False),
        ("-- hand-read --", None, False),
        ("sites hand-read", "handread_sites", False),
        ("  of which criterion", "criterion_sites", False),
        ("  papers w/ criterion site", "criterion_papers", False),
        ("  collision share", "collision_share", True),
        ("deriving doc (VOC)", None, False),
        ("  sites", None, False),
        ("  share of criterion", "voc_share", True),
        ("  at ANY site, any role", "voc_any_role", False),
        ("  papers citing it ANYWHERE", "crit_papers_citing_deriver_anywhere", False),
        ("COCO share", "coco_share", True),
        ("no document share", "none_share", True),
        ("-- name absorption --", None, False),
        ("states threshold", "states_threshold", False),
        ("carries AP50-family name", "carries_name", False),
        ("name and never states it", "name_only", False),
    ]:
        if key is None and not label.startswith("--") and label != "  sites":
            print(label)
            continue
        if label == "  sites":
            print(f"{label:26}" + "".join(
                f"{summary[e].get('documents', {}).get('voc', '-'):>12}" for e in ERA_ORDER))
            continue
        if key is None:
            print(f"\n{label}")
            continue
        print(f"{label:26}" + "".join(f"{cell(summary[e], key, pct):>12}"
                                      for e in ERA_ORDER))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
