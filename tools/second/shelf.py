#!/usr/bin/env python3
"""shelf.py — what the second record holds of a person, beside what the first holds.

Offline. No network, no model, no random number. Takes the probe written by `oeuvre.py`
and computes every number a page may publish, including the one the session turns on:
**of the people the second record does hold, how many does it hold any work by at all.**

Three things this module refuses to do, each because a sibling or this practice has been
caught doing it:

1. **It never reads a refusal as a zero.** A person the record did not answer about is
   `unasked`, counted in its own column, and every share is reported with the
   assumption-free interval over the whole population — every unasked person a miss, then
   every unasked person a hit (Manski, worked 2026-09-09).
2. **It never compares two shares by their points.** The comparison that carries the
   finding is stated as a *survival*: the atlas arm is emptier than a control arm only if
   its interval lies clear of that control's, with every unasked person counted in the
   direction that would destroy the claim. A point difference that does not survive that
   is reported as not surviving (cycle 002 s4, applied to itself on 2026-09-07).
3. **It never counts an oeuvre by one property.** The narrow measure is `creator` — the
   property an artwork carries in this record — and every person it calls empty is asked
   again against the union of six making properties, so that a piece filed as authored or
   composed cannot be mistaken for a hole. Both measures are computed for every arm and both
   are published. For this population they disagree sharply, and the disagreement is itself
   the second finding: the wide measure's surplus is almost entirely authored text.
"""

from __future__ import annotations

import json
import statistics


def year_of(time_literal: str | None) -> int | None:
    """The year in a Wikidata time literal, signed. None if it is not one."""
    if not isinstance(time_literal, str) or len(time_literal) < 6:
        return None
    try:
        y = int(time_literal[1:5])
    except ValueError:
        return None
    return -y if time_literal[0] == "-" else y


def first_year(ent: dict, prop: str) -> int | None:
    for t in (ent.get("claims") or {}).get(prop, []) or []:
        y = year_of(t)
        if y is not None:
            return y
    return None


def atlas_year(s: str | None) -> int | None:
    """The atlas's own year string, which is free text: '2025', '2019–2021', 'since 2016'."""
    if not s:
        return None
    digits = ""
    for ch in str(s):
        if ch.isdigit():
            digits += ch
            if len(digits) == 4:
                break
        elif digits:
            digits = ""
    if len(digits) == 4:
        y = int(digits)
        if 1800 <= y <= 2100:
            return y
    return None


def rows_for(qids: list[str], ents: dict, oeuvre: dict, unions: dict) -> list[dict]:
    """One row per person: what the record says about them, and how much of them it holds."""
    out = []
    for q in qids:
        e = ents.get(q) or {}
        n = oeuvre.get(q)
        # The union is only asked of the zeros; for anyone else the narrow count is already
        # a lower bound on it, and the row says so rather than inventing a number.
        u = unions.get(q) if n == 0 else (n if n is not None else None)
        out.append({
            "qid": q,
            "label": e.get("label_en"),
            "description": e.get("description_en"),
            "birth": first_year(e, "P569"),
            "death": first_year(e, "P570"),
            "occupations": ((e.get("claims") or {}).get("P106") or []),
            "notable_work": len(((e.get("claims") or {}).get("P800") or [])),
            "n_statements": e.get("n_statements"),
            "n_properties": e.get("n_properties"),
            "sitelinks": e.get("sitelinks"),
            "creator_works": n,
            "any_works": u,
            "union_asked": (q in unions) if n == 0 else (n is not None),
        })
    return out


def profile(rows: list[dict], lo: int | None = None, hi: int | None = None,
            key: str = "any_works") -> dict:
    """Counts, shares and the assumption-free interval for one population.

    `lo`/`hi` cut the population to a birth-year window. A person whose birth year the
    record does not state is **outside every window** — that is a third state, not a zero,
    and it is reported as `no_birth` rather than being dropped silently.
    """
    no_birth = sum(1 for r in rows if r["birth"] is None)
    if lo is None:
        # No window at all: everybody, birth year stated or not. This is the arm's own
        # headline, and it is the only profile that owes nothing to a birth year.
        sel = list(rows)
    else:
        sel = [r for r in rows if r["birth"] is not None and lo <= r["birth"] <= hi]
    n = len(sel)
    vals = [r[key] for r in sel]
    asked = [v for v in vals if v is not None]
    unasked = n - len(asked)
    empty = sum(1 for v in asked if v == 0)
    held = [v for v in asked if v > 0]
    return {
        "n": n,
        "asked": len(asked),
        "unasked": unasked,
        "no_birth": no_birth,
        "empty": empty,
        "held": len(held),
        # The share over what was actually answered, and the interval over the whole
        # population. Three denominators, never one.
        "share_empty": (empty / len(asked)) if asked else None,
        "empty_lo": (empty / n) if n else None,
        "empty_hi": ((empty + unasked) / n) if n else None,
        "works_total": sum(held),
        "works_mean": (sum(asked) / len(asked)) if asked else None,
        "works_median": statistics.median(asked) if asked else None,
        "works_max": max(asked) if asked else None,
        "dist": sorted(asked),
        "birth_lo": min((r["birth"] for r in sel if r["birth"] is not None), default=None),
        "birth_hi": max((r["birth"] for r in sel if r["birth"] is not None), default=None),
        "birth_median": (statistics.median(bs)
                         if (bs := [r["birth"] for r in sel if r["birth"] is not None])
                         else None),
    }


def survives(a: dict, b: dict) -> dict:
    """Is arm `a` emptier than arm `b`, with every unasked person against the claim?

    The claim is *a is emptier than b*. The worst case for it is: every person a did not
    answer about turns out to hold work (so a's emptiness is `empty_lo`), and every person
    b did not answer about turns out to hold nothing (so b's emptiness is `empty_hi`). The
    claim survives exactly when a's floor still clears b's ceiling. No threshold is chosen
    anywhere in this function, and there is nothing in it to tune.
    """
    if a["empty_lo"] is None or b["empty_hi"] is None:
        return {"survives": None, "note": "a population with nothing in it"}
    return {
        "a_floor": a["empty_lo"],
        "b_ceiling": b["empty_hi"],
        "gap": a["empty_lo"] - b["empty_hi"],
        "survives": a["empty_lo"] > b["empty_hi"],
        "point_gap": (a["share_empty"] - b["share_empty"])
        if (a["share_empty"] is not None and b["share_empty"] is not None) else None,
    }


def measure(p: dict) -> dict:
    atlas_qids = sorted({a["qid"] for a in p["atlas_artists"]})
    unions = p.get("union_zeros") or {}
    atlas_rows = rows_for(atlas_qids, p["atlas_entities"], p["atlas_oeuvre"], unions)

    # What the FIRST record holds of the same people, so the two shelves stand side by side.
    by_artist = p["feed_by_artist"]
    qid_of = {}
    cands_of: dict[str, int] = {}
    for a in p["atlas_artists"]:
        qid_of.setdefault(a["qid"], []).append(a["artist"])
        cands_of[a["qid"]] = max(cands_of.get(a["qid"], 0), a.get("n_candidates") or 0)
    for r in atlas_rows:
        r["n_candidates"] = cands_of.get(r["qid"], 0)
        strings = qid_of.get(r["qid"], [])
        works = [w for s in strings for w in by_artist.get(s, [])]
        r["atlas_strings"] = strings
        r["atlas_works"] = len(works)
        r["atlas_titles"] = [w["title"] for w in works]
        r["atlas_years"] = [y for w in works if (y := atlas_year(w.get("year"))) is not None]

    win = p["birth_window"]
    lo, hi = win["lo"], win["hi"]

    controls = {}
    for cq, c in (p.get("controls") or {}).items():
        costed = sorted(c.get("costed") or [])
        controls[cq] = {
            "qid": cq,
            "name": c["name"],
            "population": c.get("population"),
            "pool_asked": c.get("pool_asked"),
            "in_window": len(c.get("in_window") or []),
            "cap": c.get("cap"),
            "subsample_seed": c.get("subsample_seed"),
            "rows": rows_for(costed, c.get("entities") or {}, c.get("oeuvre") or {}, unions),
        }

    # The decade-matched draw: the same forms, re-sampled so each birth decade carries the
    # weight it carries among the atlas's own artists. Its people come out of the same pool,
    # so their claims are already held under the range-cut control.
    matched = {}
    for cq, m in (p.get("matched") or {}).items():
        ents = ((p.get("controls") or {}).get(cq) or {}).get("entities") or {}
        matched[cq] = {
            "qid": cq,
            "name": m["name"],
            "weights": m.get("weights"),
            "shortfall": m.get("shortfall"),
            "pool_by_decade": m.get("pool_by_decade"),
            "subsample_seed": m.get("subsample_seed"),
            "rows": rows_for(sorted(m.get("costed") or []), ents,
                             m.get("oeuvre") or {}, unions),
        }

    arms = {"atlas": {"name": "the atlas's artists", "rows": atlas_rows}}
    for cq, c in controls.items():
        arms["range:" + cq] = {"name": c["name"] + " (birth range)", "rows": c["rows"]}
    for cq, m in matched.items():
        arms["matched:" + cq] = {"name": m["name"] + " (decade-matched)", "rows": m["rows"]}

    # Both measures, both populations, in the atlas artists' own birth-year window.
    prof = {}
    for key in ("any_works", "creator_works"):
        prof[key] = {a: profile(arms[a]["rows"], lo, hi, key) for a in arms}
    # The whole arm, no window: the headline of this session, which no birth year decides.
    whole = {key: {a: profile(arms[a]["rows"], None, None, key) for a in arms}
             for key in ("any_works", "creator_works")}

    comparisons = []
    for arm in arms:
        if arm == "atlas":
            continue
        comparisons.append({
            "arm": arm,
            "name": arms[arm]["name"],
            "any_works": survives(prof["any_works"]["atlas"], prof["any_works"][arm]),
            "creator_works": survives(prof["creator_works"]["atlas"],
                                      prof["creator_works"][arm]),
        })

    # Does the atlas arm lie outside the RANGE of its controls, or merely below their mean?
    # The rule of 2026-09-07, applied here: a point that sits inside the spread of its
    # comparisons is not a finding. Judged against the decade-matched draws, which are the
    # ones that hold the era fixed.
    matched_arms = ["matched:" + cq for cq in matched]
    range_tests = {}
    for key in ("creator_works", "any_works"):
        cs = [prof[key][a]["share_empty"] for a in matched_arms
              if prof[key].get(a, {}).get("share_empty") is not None]
        a_share = prof[key]["atlas"]["share_empty"]
        range_tests[key] = {
            "control_shares": cs,
            "outside": (a_share > max(cs)) if (cs and a_share is not None) else None,
            "atlas_share": a_share,
            # Which end of the spread the atlas arm sits at, since "inside" says only that
            # it is not extreme and the direction is a different fact about the world.
            "rank_from_emptiest": (sorted(cs + [a_share], reverse=True).index(a_share) + 1)
            if (cs and a_share is not None) else None,
            "of": len(cs) + 1,
        }
    # The primary measure is the one about artworks: `creator` is the property an artwork
    # carries, and the wide union below turns out to be mostly authored text.
    ctrl_shares = range_tests["creator_works"]["control_shares"]
    outside = range_tests["creator_works"]["outside"]

    # The comparison with no window in it at all: one decade at a time, the atlas arm against
    # all control people of that decade pooled. A claim that holds in every decade where both
    # arms have somebody needs no birth window to be chosen, which removes the last dial.
    all_ctrl_rows = [r for cq in controls for r in controls[cq]["rows"]]
    decades = []
    for dec in sorted({(r["birth"] // 10) * 10 for r in atlas_rows + all_ctrl_rows
                       if r["birth"] is not None}):
        # On the primary measure — creator, the property an artwork carries — because that
        # is the measure the page's claim is stated in.
        a = profile([r for r in atlas_rows], dec, dec + 9, "creator_works")
        b = profile(all_ctrl_rows, dec, dec + 9, "creator_works")
        if a["n"] == 0 or b["n"] == 0:
            continue
        decades.append({
            "decade": dec, "atlas": a, "control": b,
            "both": True, "survives": survives(a, b),
        })
    dec_both = [d for d in decades if d["atlas"]["asked"] and d["control"]["asked"]]
    dec_atlas_emptier = [d for d in dec_both
                         if d["atlas"]["share_empty"] > d["control"]["share_empty"]]
    dec_survive = [d for d in dec_both if d["survives"].get("survives")]

    # The dates. For the atlas artists the record DOES hold work by: is that work the work
    # the atlas names, or older work by the same hand?
    cred_ent = p.get("atlas_credited_entities") or {}
    paired = []
    for r in atlas_rows:
        items = ((p.get("atlas_credited") or {}).get(r["qid"]) or {}).get("items") or []
        yrs = [y for q in items if (y := first_year(cred_ent.get(q) or {}, "P571")) is not None]
        if not yrs or not r["atlas_years"]:
            continue
        paired.append({
            "qid": r["qid"], "label": r["label"],
            "second_years": sorted(yrs), "atlas_years": sorted(r["atlas_years"]),
            "second_median": statistics.median(yrs),
            "atlas_median": statistics.median(r["atlas_years"]),
            "delta": statistics.median(r["atlas_years"]) - statistics.median(yrs),
        })
    deltas = [x["delta"] for x in paired]

    # Entry richness: is the artist entry a record or a handle?
    def rich(rows):
        st = [r["n_statements"] for r in rows if r["n_statements"] is not None]
        sl = [r["sitelinks"] for r in rows if r["sitelinks"] is not None]
        nw = [r["notable_work"] for r in rows if r["notable_work"] is not None]
        return {
            "n": len(rows),
            "statements_median": statistics.median(st) if st else None,
            "sitelinks_median": statistics.median(sl) if sl else None,
            "sitelinks_zero": sum(1 for v in sl if v == 0),
            "notable_work_any": sum(1 for v in nw if v > 0),
        }

    richness = {a: rich([r for r in arms[a]["rows"]
                         if r["birth"] is not None and lo <= r["birth"] <= hi])
                for a in arms}

    # What the record calls these people, by its own occupation statements.
    occ_labels = p.get("occupation_labels") or {}
    occ_counts: dict[str, int] = {}
    for r in atlas_rows:
        for o in r["occupations"]:
            occ_counts[o] = occ_counts.get(o, 0) + 1
    top_occ = sorted(occ_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:14]

    return {
        "meta": {
            **{k: p[k] for k in ("probed_at_utc", "route", "second_record", "feed",
                                 "birth_window", "control_forms", "making_props",
                                 "making_names", "prior_probe", "calls")},
            "artist_strings": p.get("artist_strings"),
            "artist_items": p.get("artist_items"),
        },
        "atlas_rows": atlas_rows,
        "controls": controls,
        "matched": matched,
        "arms": {a: {"name": arms[a]["name"], "n": len(arms[a]["rows"])} for a in arms},
        "profiles": prof,
        "whole_arm": whole,
        "comparisons": comparisons,
        "atlas_outside_control_range": outside,
        "control_shares": ctrl_shares,
        "range_tests": range_tests,
        # What the wide measure is actually made of. The union of six making properties
        # counts a paper the same as a sculpture, and for this population that is not a
        # detail: it is most of the difference between the two measures.
        "wide": {
            "credits_any": sum(r["any_works"] for r in atlas_rows if r["any_works"]),
            "credits_creator": sum(r["creator_works"] for r in atlas_rows
                                   if r["creator_works"]),
            "people_only_non_creator": sum(
                1 for r in atlas_rows
                if r["creator_works"] == 0 and (r["any_works"] or 0) > 0),
            "people_any_creator": sum(1 for r in atlas_rows if (r["creator_works"] or 0) > 0),
            # Homonymy is the standing threat to every count here, and it is worst exactly
            # where the wide measure is largest: a common name matched to a prolific author.
            "credits_on_ambiguous_names": sum(
                (r["any_works"] or 0) for r in atlas_rows if r.get("n_candidates", 1) > 1),
            "people_ambiguous": sum(1 for r in atlas_rows if r.get("n_candidates", 1) > 1),
            "top": [
                {"label": r["label"], "qid": r["qid"], "any": r["any_works"],
                 "creator": r["creator_works"], "atlas": r["atlas_works"],
                 "candidates": r.get("n_candidates"), "description": r["description"]}
                for r in sorted(atlas_rows, key=lambda r: -(r["any_works"] or 0))[:12]
            ],
        },
        "by_decade": decades,
        "by_decade_summary": {
            "decades_with_both": len(dec_both),
            "atlas_emptier": len(dec_atlas_emptier),
            "survives": len(dec_survive),
            "decades": [d["decade"] for d in dec_both],
        },
        "dates": {
            "paired": sorted(paired, key=lambda x: -abs(x["delta"])),
            "n": len(paired),
            "median_delta": statistics.median(deltas) if deltas else None,
            "atlas_later": sum(1 for d in deltas if d > 0),
            "second_later": sum(1 for d in deltas if d < 0),
            "same": sum(1 for d in deltas if d == 0),
        },
        "richness": richness,
        "occupations": [
            {"qid": q, "name": occ_labels.get(q) or q, "count": c} for q, c in top_occ
        ],
        "totals": {
            "atlas_items": len(atlas_rows),
            "atlas_works_in_first_record": sum(r["atlas_works"] for r in atlas_rows),
            "atlas_works_in_second_record": sum(
                r["any_works"] for r in atlas_rows if r["any_works"]),
        },
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    probe = json.load(open(args.probe, encoding="utf-8"))
    r = measure(probe)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(r, fh, ensure_ascii=False)
    slim = {k: v for k, v in r.items() if k not in ("atlas_rows", "controls")}
    slim["controls"] = {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                        for k, v in r["controls"].items()}
    print(json.dumps(slim, indent=1, ensure_ascii=False)[:6000])
