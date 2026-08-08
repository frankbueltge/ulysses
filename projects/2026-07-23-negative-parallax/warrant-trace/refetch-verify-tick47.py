#!/usr/bin/env python3
"""refetch-verify-tick47 — is the frame the same bytes it was when it was counted?

Defeat condition D5 of PREREGISTRATION-tick47.md. Each sampled paper is re-fetched from
arXiv today; its sha256 is compared against the manifest of the tick that first read it
(tick 35 on 2026-08-05, tick 36 on 2026-08-05, tick 46 on 2026-08-08). A mismatch means the
earlier count was a count over a different text, and it is a finding about this line's
re-derivability, not a nuisance.

The re-fetched sources themselves are NOT committed: this repository lands derived tables,
manifests and code, never redistributed source text.

Usage:
    refetch-verify-tick47.py --refetch <dir with refetch-<lit>.jsonl> --out refetch-verify-tick47.json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFESTS = {"gaia": "fetch-manifest-tick35.jsonl",
             "mcmc": "fetch-manifest-tick36.jsonl",
             "cv": "fetch-manifest-tick46.jsonl"}


def load(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                out[rec["arxiv"]] = rec
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refetch", required=True)
    ap.add_argument("--out", default="refetch-verify-tick47.json")
    args = ap.parse_args()

    result = {"tick": 47, "checked": 0, "match": 0, "mismatch": [], "absent": [],
              "per_literature": {}}
    for lit, manifest in MANIFESTS.items():
        old = load(os.path.join(HERE, manifest))
        new = load(os.path.join(args.refetch, f"refetch-{lit}.jsonl"))
        m = mism = 0
        for aid, rec in new.items():
            result["checked"] += 1
            if aid not in old:
                result["absent"].append({"literature": lit, "arxiv": aid})
                continue
            if old[aid].get("sha256") == rec.get("sha256"):
                m += 1
                result["match"] += 1
            else:
                mism += 1
                result["mismatch"].append({
                    "literature": lit, "arxiv": aid,
                    "then": old[aid].get("sha256"), "then_utc": old[aid].get("fetched_utc"),
                    "then_bytes": old[aid].get("bytes"),
                    "now": rec.get("sha256"), "now_utc": rec.get("fetched_utc"),
                    "now_bytes": rec.get("bytes")})
        result["per_literature"][lit] = {"n": len(new), "match": m, "mismatch": mism}
        print(f"{lit:5s} n={len(new):3d} match={m:3d} mismatch={mism:3d}")
    with open(os.path.join(HERE, args.out), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    print(f"total checked={result['checked']} match={result['match']} "
          f"mismatch={len(result['mismatch'])} absent_from_old_manifest={len(result['absent'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
