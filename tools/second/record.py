#!/usr/bin/env python3
"""record.py — what a second record holds of a first, and what that buys.

No network, no model, no random number. Takes the raw probe written by `probe.py` and
computes every number a page may publish. The feed the probe was run against is not
re-read: it is read live and never mirrored into this repository.

**The ladder.** Asking whether a second record "holds" a work is not one question. Any
record is searched by name, and a name is not evidence: of the atlas's titles, some are
ordinary English phrases that a hundred unrelated items also carry. So the instrument
does not answer *is it there* — it reports coverage at three standards of proof, and
leaves the choice of standard where it belongs, with the reader:

  `none`            no item in the second record carries this title at all.
  `name`            an item carries the title exactly, after normalisation. Nothing else.
  `creator`         …and that item has a creator statement, so it is somebody's work.
  `attributed`      …and that creator is one of the people the first record names.

Each rung is a subset of the one above it. `attributed` is the only rung on which the
two records can be said to hold the *same* object; `name` is the only rung an ordinary
title search actually establishes; the distance between them is the measurement.

**The bound.** Two records of one population give a capture–recapture estimate,
N̂ = n₁·n₂/m — the Lincoln–Petersen arithmetic of `tools/absence/identify.py`, here
across two catalogues rather than two word screens. It needs three numbers, and the
third is the difficulty: n₂ is the size of the second record's list *of the same kind of
thing*, which requires the second record to have a name for the kind. `bound()` computes
the estimate and, more usefully, its sensitivity: how far N̂ moves when m moves by one.
Where m is small that derivative is the whole story, and it is reported instead of being
hidden inside a point.
"""

from __future__ import annotations

import json
import re
import unicodedata

# The rungs, weakest evidence first. Each is a subset of its predecessor.
RUNGS = ["name", "creator", "attributed"]

# Splitters for a first record's artist string: "A & B", "A, B and C", "A / B".
_SPLIT = re.compile(r"\s*(?:&|,|/|\+|\band\b|\bund\b|\bwith\b)\s*", re.I)

# Wikidata items for "is a person" / "is a group of people".
HUMAN = "Q5"
GROUPISH = {
    "Q16334295",  # group of humans
    "Q43229",  # organization
    "Q4830453",  # business
    "Q31855",  # research institute
    "Q3152824",  # cultural institution
    "Q2085381",  # publisher
    "Q215380",  # musical group
    "Q7278",  # political party
    "Q875538",  # university department
    "Q157031",  # foundation
}


def normalise(s: str) -> str:
    """Identical to `probe.normalise`; duplicated so this module imports nothing."""
    if not s:
        return ""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    out = [c if c.isalnum() else " " for c in s]
    return " ".join("".join(out).split())


def artist_names(artist: str) -> list[str]:
    """The individual names inside a first record's artist string, normalised."""
    parts = [normalise(p) for p in _SPLIT.split(artist or "")]
    return [p for p in parts if len(p) >= 3]


def creator_labels(cand_qid: str, probe: dict) -> list[str]:
    ent = (probe.get("entities") or {}).get(cand_qid) or {}
    labels = probe.get("labels") or {}
    out = []
    for q in (ent.get("claims") or {}).get("P170", []) or []:
        lab = labels.get(q)
        if lab:
            out.append(lab)
    return out


def grade_work(work: dict, probe: dict) -> dict:
    """The highest rung this work reaches in the second record, and its witness.

    `unasked` is not a rung and not a miss: it is an entry whose query the second record
    never served. Every count below separates it from `none`, because a record that
    refused to answer has not said no.
    """
    if work.get("asked") is False:
        return {"rung": "unasked", "qid": None, "witness": None, "n_candidates": 0}
    cands = work.get("candidates") or []
    if not cands:
        return {"rung": "none", "qid": None, "witness": None, "n_candidates": 0}

    names = artist_names(work.get("artist") or "")
    best = ("name", cands[0]["qid"], None)
    rank = {"name": 0, "creator": 1, "attributed": 2}

    for c in cands:
        qid = c["qid"]
        crs = creator_labels(qid, probe)
        if not crs:
            continue
        if rank[best[0]] < 1:
            best = ("creator", qid, "; ".join(crs))
        for cr in crs:
            ncr = normalise(cr)
            hit = any(ncr == n or ncr in n or n in ncr for n in names)
            if hit:
                return {
                    "rung": "attributed",
                    "qid": qid,
                    "witness": cr,
                    "n_candidates": len(cands),
                }
    return {
        "rung": best[0],
        "qid": best[1],
        "witness": best[2],
        "n_candidates": len(cands),
    }


def grade_artist(row: dict, probe: dict) -> dict:
    """For a person or group: unasked / none / name / person (P31 says human or group)."""
    if row.get("asked") is False:
        return {"rung": "unasked", "qid": None, "n_candidates": 0}
    cands = row.get("candidates") or []
    if not cands:
        return {"rung": "none", "qid": None, "n_candidates": 0}
    ents = probe.get("entities") or {}
    for c in cands:
        p31 = ((ents.get(c["qid"]) or {}).get("claims") or {}).get("P31", []) or []
        if HUMAN in p31 or (set(p31) & GROUPISH):
            return {"rung": "person", "qid": c["qid"], "n_candidates": len(cands)}
    return {"rung": "name", "qid": cands[0]["qid"], "n_candidates": len(cands)}


def ladder(grades: list[str], rungs: list[str]) -> list[dict]:
    """Counts at each standard of proof, each rung cumulative over the ones above it.

    Three denominators, never one. `count` is what was found; `asked` is how many
    entries the second record actually answered about; `n` is the whole list. The share
    is over `asked`, because dividing a count by a denominator that includes entries
    nobody could ask about is the mistake this practice measured in a sibling's record
    on 2026-09-09. `lo` and `hi` are the assumption-free interval over the whole list —
    every unasked entry a miss, then every unasked entry a hit — which is the frame of
    `tools/absence/identify.py` applied to this instrument's own reach.
    """
    n = len(grades)
    unasked = sum(1 for g in grades if g == "unasked")
    asked = n - unasked
    out = []
    for i, r in enumerate(rungs):
        keep = {x for x in rungs[i:]}
        c = sum(1 for g in grades if g in keep)
        out.append(
            {
                "rung": r,
                "count": c,
                "asked": asked,
                "unasked": unasked,
                "share": (c / asked) if asked else 0.0,
                "lo": (c / n) if n else 0.0,
                "hi": ((c + unasked) / n) if n else 0.0,
                "n": n,
            }
        )
    return out


def bound(n1: int, n2: int, m: int) -> dict:
    """Lincoln-Petersen across two catalogues, reported by its sensitivity to m.

    With two independent lists of one population, N̂ = n₁·n₂/m. Where m is large the
    point is worth quoting. Where m is small the point is an artefact of m: one item
    gained or lost moves the estimate by more than the whole first record. `swing` is
    exactly that — |N̂(m) − N̂(m+1)| — and it is the number that decides whether the
    estimate may be published at all.
    """
    if m <= 0:
        return {
            "n1": n1,
            "n2": n2,
            "m": m,
            "estimate": None,
            "chapman": None,
            "swing": None,
            "note": "no overlap: the estimator is undefined and bounds nothing",
        }
    est = n1 * n2 / m
    est_next = n1 * n2 / (m + 1)
    chap = ((n1 + 1) * (n2 + 1)) / (m + 1) - 1
    return {
        "n1": n1,
        "n2": n2,
        "m": m,
        "estimate": est,
        "chapman": chap,
        "swing": abs(est - est_next),
        "note": "swing = how far the estimate moves if one more overlap is found",
    }


def measure(probe: dict, subset_index: list[int] | None = None) -> dict:
    """Every published number, derived in one pass.

    Takes the probe and nothing else. The feed it was run against is not re-read here:
    it is read live and never mirrored into this repository, so the titles and artists
    this module reports on are the probe's own copy of what it asked about, which is the
    thing that has to be true for the page to be honest.
    """
    works = probe["works"]
    graded = []
    for w in works:
        g = grade_work(w, probe)
        graded.append({**{k: w[k] for k in ("index_in_feed", "title", "artist", "year")}, **g})

    artists = [{**a, **grade_artist(a, probe)} for a in probe["artists"]]

    work_grades = [g["rung"] for g in graded]
    unasked_works = sum(1 for g in work_grades if g == "unasked")
    art_grades = [a["rung"] for a in artists]

    sub = None
    if subset_index is not None:
        idx = set(subset_index)
        sg = [g["rung"] for g in graded if g["index_in_feed"] in idx]
        sub = {
            "n": len(sg),
            "ladder": ladder(sg, RUNGS),
            "rows": [g for g in graded if g["index_in_feed"] in idx],
        }

    # How many held works carry a class statement a second catalogue could be
    # constituted from — i.e. does the second record know this kind of thing by a name?
    near = set(probe["near_classes"].keys()) - {"_literal_data_art_items"}
    ents = probe.get("entities") or {}
    classed = []
    for g in graded:
        if g["rung"] == "none" or not g["qid"]:
            continue
        claims = (ents.get(g["qid"]) or {}).get("claims") or {}
        vals = set()
        for p in ("P136", "P135", "P31"):
            vals |= set(claims.get(p, []) or [])
        hit = sorted(vals & near)
        if hit:
            classed.append(
                {
                    "index_in_feed": g["index_in_feed"],
                    "title": g["title"],
                    "qid": g["qid"],
                    "rung": g["rung"],
                    "classes": hit,
                }
            )

    n2_total = 0
    n2_parts = []
    for q_, row in probe["near_classes"].items():
        if q_.startswith("_"):
            continue
        for p in ("P136", "P135", "P31"):
            v = row.get(p)
            if isinstance(v, int):
                n2_total += v
                n2_parts.append({"class": q_, "name": row["name"], "prop": p, "count": v})

    n1 = len(works)
    # One bound per standard of proof: tightening the standard drops works out of the
    # overlap, and the estimate the overlap carries moves with it. That movement is the
    # thing a reader is meant to see, so it is computed for every rung, not just one.
    per_rung = []
    for i, r in enumerate(RUNGS):
        keep = set(RUNGS[i:])
        m = sum(1 for c in classed if c["rung"] in keep)
        per_rung.append({"rung": r, "m": m, **bound(n1, n2_total, m)})

    return {
        "n": n1,
        "asked": n1 - unasked_works,
        "unasked": unasked_works,
        "reach": probe.get("reach"),
        "works": graded,
        "artists": artists,
        "work_ladder": ladder(work_grades, RUNGS),
        "artist_ladder": ladder(art_grades, ["name", "person"]),
        "subset": sub,
        "classed": classed,
        "n2_near_classes": n2_total,
        "n2_parts": n2_parts,
        "bounds_by_rung": per_rung,
        "homonymy": {
            "max_candidates": max((g["n_candidates"] for g in graded), default=0),
            "name_only": sum(1 for g in work_grades if g == "name"),
            "multi_candidate": sum(1 for g in graded if g["n_candidates"] > 1),
            "total_candidates": sum(g["n_candidates"] for g in graded),
            "searched_total": sum(w.get("searched_hits", 0) for w in works),
        },
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", required=True)
    args = ap.parse_args()
    p = json.load(open(args.probe, encoding="utf-8"))
    r = measure(p)
    print(json.dumps({k: v for k, v in r.items() if k not in ("works", "artists")},
                     indent=1, ensure_ascii=False))
