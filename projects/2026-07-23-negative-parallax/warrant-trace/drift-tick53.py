#!/usr/bin/env python3
"""drift-tick53 — D0 and D7 of the tick-53 pre-registration, by arithmetic.

D0: every e-print of today's frame that an earlier tick already fetched is compared by
sha256 against the manifest record that first read it. A silent upstream replacement of a
source under a landed measurement is the failure this check exists for.

D7: the manifest must hold exactly one record per requested id. A double-launched fetcher
produced 286 records for 187 papers at tick 48 and the same defect appeared on 2026-08-05;
it is checked, not trusted.

Usage: drift-tick53.py --manifest corpus/fetch-manifest.jsonl --ids frame-tick53-all.txt
"""
import argparse
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--ids", required=True)
    a = ap.parse_args()

    ids = [l.strip() for l in open(os.path.join(HERE, a.ids), encoding="utf-8")
           if l.strip()]
    today = load(os.path.join(HERE, a.manifest))

    # D7 — one record per id
    counts = {}
    for r in today:
        counts[r["arxiv"]] = counts.get(r["arxiv"], 0) + 1
    dupes = {k: v for k, v in counts.items() if v > 1}

    # the landed manifests of earlier ticks: first sighting of each id wins
    prior = {}
    prior_files = sorted(glob.glob(os.path.join(HERE, "fetch-manifest-tick*.jsonl")))
    for path in prior_files:
        for r in load(path):
            aid = r["arxiv"]
            if r.get("ok") and r.get("sha256") and aid not in prior:
                prior[aid] = (os.path.basename(path), r["sha256"])

    compared, identical, changed, unseen = 0, 0, [], []
    for r in today:
        aid = r["arxiv"]
        if aid in prior:
            compared += 1
            if prior[aid][1] == r.get("sha256"):
                identical += 1
            else:
                changed.append({"arxiv": aid, "prior_manifest": prior[aid][0],
                                "prior_sha256": prior[aid][1],
                                "today_sha256": r.get("sha256")})
        else:
            unseen.append(aid)

    rep = {
        "tick": 53,
        "ids_requested": len(ids),
        "manifest_records": len(today),
        "ok_records": sum(1 for r in today if r.get("ok")),
        "failed_records": [r["arxiv"] for r in today if not r.get("ok")],
        "D7_duplicate_ids": dupes,
        "D7_fires": bool(dupes) or len(today) != len(ids),
        "prior_manifests_read": [os.path.basename(p) for p in prior_files],
        "compared_against_prior": compared,
        "byte_identical": identical,
        "changed": changed,
        "D0_fires": bool(changed),
        "not_in_any_prior_manifest": unseen,
    }
    with open(os.path.join(HERE, "drift-tick53.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
