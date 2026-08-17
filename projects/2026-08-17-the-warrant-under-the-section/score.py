#!/usr/bin/env python3
"""Score the six clauses of PREREGISTRATION-01.md against data/warrants.json.

Bands are copied unchanged from the pre-registration and are not derived from the data.
C3, C5 and C6 are scored twice: with and without the three sections read during
feasibility (29 CFR 1910.6, 6 CFR 37.4, 40 CFR 282.2), as the pre-registration requires.

Usage: python3 score.py [--in data/warrants.json]
"""

import argparse
import json
import statistics
import sys

FEASIBILITY = {(29, "1910.6"), (6, "37.4"), (40, "282.2")}
KILL_MIN_FETCHED = 250
VOID_MIN_ARM = 10
C5_VOID_MIN = 8


def arms(recs):
    live = [r for r in recs if not r.get("fetch_failed")]
    P = [r for r in live if r.get("warrant_year")]
    E = [r for r in P if r.get("newest_edition_year")]
    O = [r for r in live if r.get("offloaded")]
    return live, P, E, O


def pct(n, d):
    return 100.0 * n / d if d else float("nan")


def report(recs, corpus, label):
    live, P, E, O = arms(recs)
    out = {}
    cross3 = [r for r in E if r["gap"] >= 3]

    out["n_live"] = len(live)
    out["n_P"] = len(P)
    out["n_E"] = len(E)
    out["n_O"] = len(O)

    # C1 — coverage (floor check)
    c1 = pct(len(P), corpus)
    out["C1"] = {"value": round(c1, 1), "band": ">= 85 %", "held": c1 >= 85}

    # C2 — the warrant usually covers
    covered = [r for r in E if r["newest_edition_year"] <= r["warrant_year"]]
    c2 = pct(len(covered), len(E))
    out["C2"] = {"value": round(c2, 1), "n": f"{len(covered)}/{len(E)}",
                 "band": ">= 70 %", "held": c2 >= 70,
                 "void": len(E) < VOID_MIN_ARM}

    # C3 — crossings exist and are not rare
    out["C3"] = {"value": len(cross3), "band": ">= 10", "held": len(cross3) >= 10,
                 "void": len(E) < VOID_MIN_ARM}

    # C4 — the offloaded warrant
    out["C4"] = {"value": len(O), "band": ">= 5", "held": len(O) >= 5}

    # C5 — the mechanism
    Eo = [r for r in E if r["offloaded"]]
    En = [r for r in E if not r["offloaded"]]
    r_o = pct(len([r for r in Eo if r["gap"] >= 3]), len(Eo))
    r_n = pct(len([r for r in En if r["gap"] >= 3]), len(En))
    diff = r_o - r_n
    out["C5"] = {"rate_offloaded": round(r_o, 1), "n_offloaded": len(Eo),
                 "rate_other": round(r_n, 1), "n_other": len(En),
                 "difference_pp": round(diff, 1), "band": ">= 30 pp",
                 "held": diff >= 30, "void": len(Eo) < C5_VOID_MIN}

    # C6 — how far back the printed warrants reach
    pre2000 = [r for r in P if r["warrant_year"] < 2000]
    out["C6"] = {"value": len(pre2000), "band": "15-60",
                 "held": 15 <= len(pre2000) <= 60}

    # Description, not clauses.
    out["desc"] = {
        "warrant_year_median": statistics.median([r["warrant_year"] for r in P]) if P else None,
        "warrant_year_min": min([r["warrant_year"] for r in P]) if P else None,
        "warrant_year_max": max([r["warrant_year"] for r in P]) if P else None,
        "gap_median_crossing": statistics.median([r["gap"] for r in cross3]) if cross3 else None,
        "gap_max": max([r["gap"] for r in E]) if E else None,
        "median_years_per_section_offloaded":
            statistics.median([r["n_edition_years"] for r in Eo]) if Eo else None,
        "median_years_per_section_other":
            statistics.median([r["n_edition_years"] for r in En]) if En else None,
        "dropout_no_edition_year": len(P) - len(E),
        "warrant_path_fallback": len([r for r in P if r["warrant_path"] == "fallback_any_year"]),
        "no_cita": len([r for r in live if not r.get("has_cita")]),
    }
    out["top_gaps"] = sorted(
        [{"title": r["title"], "section": r["section"], "gap": r["gap"],
          "warrant_year": r["warrant_year"], "newest_edition_year": r["newest_edition_year"],
          "offloaded": r["offloaded"], "cita": (r["cita_text"] or "")[:120]}
         for r in E], key=lambda x: -x["gap"])[:12]
    return {label: out}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp",
                    default="projects/2026-08-17-the-warrant-under-the-section/data/warrants.json")
    a = ap.parse_args()
    d = json.load(open(a.inp))
    recs, corpus = d["records"], d["corpus"]

    live = [r for r in recs if not r.get("fetch_failed")]
    if len(live) < KILL_MIN_FETCHED:
        print(json.dumps({"KILL": f"only {len(live)} of {corpus} sections fetched "
                                  f"(< {KILL_MIN_FETCHED}); study stops per the "
                                  f"pre-registration's kill condition"}, indent=1))
        return 0

    result = {}
    result.update(report(recs, corpus, "all"))
    clean = [r for r in recs if (r.get("title"), r.get("section")) not in FEASIBILITY]
    result.update(report(clean, corpus - 3, "without_feasibility_three"))
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
