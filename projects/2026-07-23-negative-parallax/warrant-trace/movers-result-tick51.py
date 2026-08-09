#!/usr/bin/env python3
"""tick 51 — the arithmetic of the hand-reading, computed rather than asserted.

Reads `handread-movers-tick51.csv` (this tick, 37 papers), `handread-tick47.csv` (the 10
movers already read then) and the landed tick-50 tables, and writes every number the record
quotes. Offline; no network.

Two corrections are applied to the rates 0.5 published, and only to the papers actually
read — which is why the output calls them `movers_corrected` and not a census:

  A  the paper invokes the statistic and states no threshold  -> back into the numerator
  C  the paper never invoked the statistic at all             -> out of the denominator

Usage: python3 movers-result-tick51.py --out movers-tick51-result.json
"""
import argparse
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS = [("gaia", "ruwe-1.4"), ("mcmc", "rhat-1.1"), ("cv", "iou-0.5")]
# the movers hand-read at tick 47, with the class recorded there
TICK47_MOVERS = {
    "ruwe-1.4": {"2306.03140": "B", "2307.05421": "B", "2312.12827": "B", "2404.18099": "B"},
    "rhat-1.1": {"2509.02772v2": "C", "2601.22911v2": "C"},   # the second is a demotion
    "iou-0.5": {"2606.12826v1": "C", "2606.15427v1": "B", "2607.05148v2": "B",
                "2607.08076v1": "B"},
}
TICK47_DEMOTED = {"2601.22911v2"}


def as_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def counts(profile, version):
    rows = [r for r in csv.DictReader(
        open(os.path.join(HERE, f"remeasure-tick50-{profile}-{version}.csv"), encoding="utf-8"))
        if r["state"] == "measured"]
    men = [r for r in rows if r["mentioned"] == "1"]
    cand = [r for r in men if as_int(r["sites"]) == 0]
    return len(men), len(cand)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    read = list(csv.DictReader(open(os.path.join(HERE, "handread-movers-tick51.csv"),
                                    encoding="utf-8")))
    out = {"tick": 51, "papers_read_this_tick": len(read), "profiles": {}}
    tot = {"B": 0, "A": 0, "C": 0}
    sites_T = sites_X = 0

    for _corpus, profile in PAIRS:
        mine = [r for r in read if r["profile"] == profile]
        gain = [r for r in mine if r["kind"] == "gained"]
        dem = [r for r in mine if r["kind"] == "demoted"]
        cls = {k: sum(1 for r in gain if r["class"] == k) for k in "BAC"}
        for k in cls:
            tot[k] += cls[k]
        t = sum(int(r["sites_T"]) for r in mine)
        x = sum(int(r["sites_X"]) for r in mine)
        sites_T += t
        sites_X += x

        # the tick-47 movers of this profile, so the correction uses everything known
        old = TICK47_MOVERS.get(profile, {})
        old_gain = {k: v for k, v in old.items() if k not in TICK47_DEMOTED}
        cls_all = {k: cls[k] + sum(1 for v in old_gain.values() if v == k) for k in "BAC"}

        men, cand = counts(profile, "0.5")
        men04, cand04 = counts(profile, "0.4")
        # A goes back into the numerator; C leaves the denominator entirely
        cand_c = cand + cls_all["A"]
        men_c = men - cls_all["C"]
        out["profiles"][profile] = {
            "gainers_read_this_tick": len(gain), "demotions_read_this_tick": len(dem),
            "class_this_tick": cls, "class_all_known_gainers": cls_all,
            "new_sites_T": t, "new_sites_X": x,
            "rate_0.4": round(100.0 * cand04 / men04, 1),
            "rate_0.5": round(100.0 * cand / men, 1),
            "rate_movers_corrected": round(100.0 * cand_c / men_c, 1),
            "delta_points": round(100.0 * cand_c / men_c - 100.0 * cand / men, 2),
            "numerator_0.5": cand, "denominator_0.5": men,
            "numerator_corrected": cand_c, "denominator_corrected": men_c,
        }

    n_gain = sum(1 for r in read if r["kind"] == "gained")
    out["totals"] = {
        "gainers_read_this_tick": n_gain, "class_this_tick": tot,
        "justified_moves_this_tick": f"{tot['B']}/{n_gain}",
        "justified_share_this_tick": round(100.0 * tot["B"] / n_gain, 1),
        "new_sites_T": sites_T, "new_sites_X": sites_X,
        "genuine_site_share": round(100.0 * sites_T / (sites_T + sites_X), 1),
        "demotions_correct": sum(1 for r in read if r["kind"] == "demoted"),
    }
    known = {k: tot[k] + sum(1 for p in TICK47_MOVERS.values() for a, v in p.items()
                             if v == k and a not in TICK47_DEMOTED) for k in "BAC"}
    out["totals"]["class_all_known_gainers"] = known
    out["totals"]["justified_moves_all_known"] = f"{known['B']}/{sum(known.values())}"
    ranking = sorted(out["profiles"].items(), key=lambda kv: kv[1]["rate_movers_corrected"])
    out["ranking_corrected"] = [k for k, _ in ranking]

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
