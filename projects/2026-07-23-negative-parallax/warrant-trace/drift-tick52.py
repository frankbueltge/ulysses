#!/usr/bin/env python3
"""drift-tick52 — D0 of PREREGISTRATION-tick52.md.

Every computer-vision e-print re-fetched today, byte-compared by sha256 against the
manifest of tick 46, the tick that first read this frame. A mismatch would mean today's
denominator is computed over a different text than the numerator it corrects, and it is
reported as drift, not smoothed over. The sources themselves are never committed.

Usage:  drift-tick52.py --new <fetch-manifest.jsonl> --old fetch-manifest-tick46.jsonl
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                out[rec["arxiv"]] = rec          # last record wins: a retry supersedes
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--new", required=True)
    ap.add_argument("--old", default=os.path.join(HERE, "fetch-manifest-tick46.jsonl"))
    ap.add_argument("--out", default=os.path.join(HERE, "drift-tick52.json"))
    a = ap.parse_args()

    old, new = load(a.old), load(a.new)
    res = {"tick": 52, "old_manifest": os.path.basename(a.old),
           "records_today": len(new), "checked": 0, "match": 0,
           "mismatch": [], "absent_from_old": [], "not_ok_today": [],
           "not_ok_at_tick46": []}
    for aid, rec in new.items():
        if not rec.get("ok"):
            res["not_ok_today"].append({"arxiv": aid, "error": rec.get("error")})
        if aid not in old:
            res["absent_from_old"].append(aid)
            continue
        if not old[aid].get("ok"):
            res["not_ok_at_tick46"].append(aid)
        res["checked"] += 1
        if old[aid].get("sha256") == rec.get("sha256"):
            res["match"] += 1
        else:
            res["mismatch"].append({"arxiv": aid, "then": old[aid].get("sha256"),
                                    "now": rec.get("sha256")})
    res["d0_fires"] = bool(res["mismatch"])
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: v for k, v in res.items()
                      if k in ("records_today", "checked", "match", "d0_fires")}, indent=1))
    if res["mismatch"]:
        print("MISMATCH:", json.dumps(res["mismatch"], indent=1))


if __name__ == "__main__":
    main()
