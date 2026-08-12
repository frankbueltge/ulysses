#!/usr/bin/env python3
"""secondsight-tick61 — which part of the sieve decides the six papers the two readings disagree about.

Tick 60 compared the computer-vision numerators as SETS: 46 shared, 4 only the instrument's,
2 only the hand census's — six disagreements running in opposite directions and cancelling to
two. Tick 60 named the next operation as a question about the second work: *how does `the-gap`
show six disagreements that cancel to two?*

`the-gap` is, today, four panels about ONE expression — `GAP`, the character class and the bound
of 100 that decide how far a site may reach between a statistic's name and its number. This
script asks whether the six belong to that subject at all.

Forecasts, bands, defeat conditions, the adversarial read and the blind step are fixed in
`../PREREGISTRATION-tick61.md`, written before this file ran. Nothing here is a repair: the two
ablations exist only inside this process, are never written to disk, and no number they produce
enters any published rate (D-D).

Inputs are landed files only. No corpus, no network.

Usage: python3 secondsight-tick61.py
"""
import copy
import csv
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.normpath(os.path.join(HERE, "..", "warrant-trace"))
sys.path.insert(0, WT)

import warrant_trace as wt                                              # noqa: E402
from warrant_trace import Profile, normalise, sites                     # noqa: E402

PROFILE = "profiles/iou-0.5.json"
LANDED_COUNTS = "remeasure-tick59-iou-0.5-0.8.csv"
SETS = "numerator-sets-tick60-B.json"
HANDREAD = "handread-tick56.csv"
WINDOW_FILES = ("windows-tick56-A.json", "windows-tick56-B.json", "windows-tick57.json")

# D-B: the two hand tables carry the expectations landed in numerator-sets-tick60-B.py.
EXPECTED_SHA = {
    "handread-tick56.csv":
        "fd26ce5127ffa78e6ede090b1ee61024a387d4a670fac8e5371bd18bdcf661a1",
    "handread-tick57.csv":
        "1ea5bf3996a111398d47f2d280a2a22803fe949c7dc05835af1b9642a12fbc8e",
    "remeasure-tick59-iou-0.5-0.8.csv":
        "01d150b8dc7abd5d119287b2a964bc411d2235051127e4de58e90908cef09240",
}


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def wtpath(name):
    return os.path.join(WT, name)


def load_profile(rel_override=None):
    """The shipped profile, or one copy of it with a single field moved. Never written out."""
    with open(wtpath(PROFILE), encoding="utf-8") as fh:
        d = json.load(fh)
    if rel_override is not None:
        d = copy.deepcopy(d)
        d["rel"] = rel_override
    return Profile(d, wtpath(PROFILE))


# ---------------------------------------------------------------- the two ablations
#
# (a) gap width. The engine's GAP is read by Profile.__init__ when it expands {GAP} into the
#     site patterns, so moving the module constant before construction and restoring it after
#     produces one profile whose reach is 400 and changes nothing else. The bound is the ONLY
#     thing that moves: the character class, the stop guard and the marker branch are untouched.
GAP_400 = wt.GAP.replace("{0,100}?", "{0,400}?")
assert GAP_400 != wt.GAP, "the gap bound was not found where this script expects it"


def profile_gap400():
    shipped = wt.GAP
    try:
        wt.GAP = GAP_400
        return load_profile()
    finally:
        wt.GAP = shipped


# (b) relation vocabulary. The shipped profile admits `thresholds?` as a relation only when
#     `of|at|is|was|set to` follows it, so `IoU thresholds 0.5` carries no relation token. This
#     copy admits the bare word. Declared impurity (adversarial read §5.4): `rel` is also
#     `rel_re`, which E6 consults, so this moves two roles of one field at once.
def profile_bare_threshold():
    with open(wtpath(PROFILE), encoding="utf-8") as fh:
        rel = json.load(fh)["rel"]
    assert rel.endswith(")"), "rel is not the single group this ablation assumes"
    return load_profile(rel_override=rel[:-1] + r"|thresholds?)"), rel[:-1] + r"|thresholds?)"


# ---------------------------------------------------------------- measurements
def verdict(text, prof):
    """What an instrument answers on this exact string: every site, its value and its match."""
    return [{"value": s["value"], "match": s["match"]} for s in sites(normalise(text), prof)]


def focus_number(fragment, prof):
    """The printed threshold in a pinned fragment, chosen by the PROFILE's own focus value.

    Blind by construction (pre-registration §6): the number is not picked by hand, it is the
    first numeral in the hand-read fragment whose value equals the profile's focus threshold —
    0.5, or one of its declared equivalents. Returns (literal, char offset) or (None, None).
    """
    want = {float(prof.raw["focus_value"])}
    for eq in prof.raw.get("focus_equivalents", []):
        want.add(float(eq) / 100.0 if float(eq) > 1 else float(eq))
    for m in re.finditer(r"\d{1,3}(?:\.\d+)?", fragment):
        v = float(m.group(0))
        if v in want or (v > 1 and v / 100.0 in want):
            return m.group(0), m.start()
    return None, None


# The gap's own arithmetic, restated here for measurement only. GAP admits, per unit: a whole
# `<<…>>` marker, a newline that does not begin a blank line, any character that is not one of
# `.;:\n`, or a period followed by a digit — and refuses to start a unit at a STOP.
MARKER = re.compile(r"<<[^<>\n]*>>")
STOP_RE = re.compile(wt.STOP)


def gap_walk(span):
    """Can the gap cross this span, and in how many units? Measurement, not a verdict."""
    i, units = 0, 0
    while i < len(span):
        if STOP_RE.match(span, i):
            return {"crossable": False, "units": units, "blocked_by": "stop:" + span[i:i + 12],
                    "chars": len(span)}
        m = MARKER.match(span, i)
        if m:
            i, units = m.end(), units + 1
            continue
        c = span[i]
        if c == "\n":
            if re.match(r"\n[ \t]*\n", span[i:]):
                return {"crossable": False, "units": units, "blocked_by": "blank line",
                        "chars": len(span)}
            i, units = i + 1, units + 1
            continue
        if c in ".;:":
            if c == "." and i + 1 < len(span) and span[i + 1].isdigit():
                i, units = i + 1, units + 1
                continue
            return {"crossable": False, "units": units, "blocked_by": "char:" + c,
                    "chars": len(span)}
        i, units = i + 1, units + 1
    return {"crossable": True, "units": units, "blocked_by": None, "chars": len(span)}


def reach(fragment, prof):
    """P5: does the printed number stand within the shipped gap's reach of the statistic's name?

    Measures the span from the END of the last term match that precedes the printed number to
    the START of that number, in the normalised text the sieve would see.
    """
    text = normalise(fragment)
    lit, _ = focus_number(text, prof)
    if lit is None:
        return {"measured": False, "why": "no numeral equal to the profile's focus value"}
    npos = text.find(lit)
    terms = [m for m in prof.term_re.finditer(text) if m.end() <= npos]
    if not terms:
        return {"measured": False, "why": "no term match precedes the printed number"}
    t = terms[-1]
    span = text[t.end():npos]
    walk = gap_walk(span)
    return {"measured": True, "printed_value": lit, "term": t.group(0), "between": span,
            "within_reach": bool(walk["crossable"] and walk["units"] <= 100), **walk}


# ---------------------------------------------------------------- inputs
def landed_counts():
    out = {}
    with open(wtpath(LANDED_COUNTS), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            # a blank `sites` is a paper the frame never measured; the six are all measured.
            out[r["arxiv"]] = int(r["sites"]) if r["sites"] != "" else None
    return out


def hand_fragments():
    out = {}
    with open(wtpath(HANDREAD), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["arxiv"]] = {"fragment": r["fragment"], "note": r["note"], "label": r["label"]}
    return out


def windows():
    out = {}
    for name in WINDOW_FILES:
        with open(wtpath(name), encoding="utf-8") as fh:
            for r in json.load(fh):
                out[r["arxiv"]] = {"source": name, "n_total": r["n_total"],
                                   "windows": [w["text"] for w in r["windows"]]}
    return out


def main():
    prof = load_profile()
    prof400 = profile_gap400()
    profbare, bare_rel = profile_bare_threshold()

    with open(wtpath(SETS), encoding="utf-8") as fh:
        sets = json.load(fh)
    only_i = [r["arxiv"] for r in sets["only_I"]]        # the sieve's numerator only: B-SITE
    only_h = [r["arxiv"] for r in sets["only_H"]]        # the hand census's only: invented site
    six = only_i + only_h

    counts, frags, wins = landed_counts(), hand_fragments(), windows()

    voids = []
    for name, want in EXPECTED_SHA.items():
        got = sha(wtpath(name))
        if got != want:
            voids.append(f"D-B: {name} sha {got} != landed expectation {want}")

    papers = {}
    for aid in six:
        w = wins[aid]
        found = []
        for text in w["windows"]:
            found += verdict(text, prof)
        complete = w["n_total"] == len(w["windows"])
        landed = counts[aid]
        rec = {"arxiv": aid, "side": "only_I (B-SITE)" if aid in only_i else "only_H (invented site)",
               "window_source": w["source"], "term_matches_in_paper": w["n_total"],
               "windows_landed": len(w["windows"]), "window_coverage_complete": complete,
               "landed_sites_0.8": landed, "sites_over_windows": len(found),
               "matches_over_windows": found,
               "hand_note": frags.get(aid, {}).get("note"),
               "hand_label": frags.get(aid, {}).get("label")}
        if len(found) > landed:
            voids.append(f"D-A: {aid} finds {len(found)} over windows, landed says {landed}")
        elif complete and len(found) != landed:
            voids.append(f"D-A: {aid} complete coverage but {len(found)} != landed {landed}")
        papers[aid] = rec

    # ---- Operation B, on the four B-SITE papers, over their landed pinned fragments as well
    #      as their windows. The fragment is the sentence the tick-56 hand reading pinned; it is
    #      landed and byte-identical, and it is where the printed number provably stands.
    for aid in only_i:
        rec, frag = papers[aid], frags[aid]["fragment"]
        want, _ = focus_number(normalise(frag), prof)
        shipped_on_frag = verdict(frag, prof)

        def run(p):
            got = verdict(frag, p)
            # adversarial read §5.3: a recovery whose value is not the printed threshold is
            # not a recovery.
            on_target = [s for s in got if want is not None and s["value"] is not None
                         and abs(float(s["value"]) - float(want)) < 1e-9]
            return {"sites": got, "recovers": bool(on_target and not shipped_on_frag),
                    "on_target": on_target}

        a, b = run(prof400), run(profbare)
        rec["fragment"] = frag
        rec["printed_threshold"] = want
        rec["shipped_on_fragment"] = shipped_on_frag
        rec["ablation_a_gap400"] = a
        rec["ablation_b_bare_threshold"] = b
        rec["recovered_by"] = ("both" if a["recovers"] and b["recovers"] else
                               "a_gap_width" if a["recovers"] else
                               "b_relation_vocabulary" if b["recovers"] else "neither")
        rec["reach"] = reach(frag, prof)

    # ---- forecasts
    b_site_counts = [papers[a]["sites_over_windows"] for a in only_i]
    h_counts = [papers[a]["sites_over_windows"] for a in only_h]
    rec_by = {a: papers[a]["recovered_by"] for a in only_i}
    by_b = [a for a, v in rec_by.items() if v in ("b_relation_vocabulary", "both")]
    by_a_only = [a for a, v in rec_by.items() if v == "a_gap_width"]
    classes_of_b = sorted({papers[a]["hand_note"] for a in by_b})
    in_reach = [a for a in only_i if papers[a]["reach"].get("within_reach")]

    scored = {
        "P1": {"claim": "0 sites over windows for all four B-SITE papers",
               "observed": dict(zip(only_i, b_site_counts)),
               "held": all(c == 0 for c in b_site_counts),
               "weight": "none — restates landed arithmetic (adversarial read §5.1)"},
        "P2": {"claim": "exactly 1 site over windows for each invented-site paper",
               "observed": dict(zip(only_h, h_counts)),
               "held": all(c == 1 for c in h_counts),
               "weight": "none — restates landed arithmetic (adversarial read §5.1)"},
        "P3": {"claim": "ablation (b), the relation vocabulary, recovers >= 3 of the 4",
               "band": "3 or 4", "observed_recovered_by_b": by_b,
               "distinct_fault_classes": classes_of_b,
               "held": len(by_b) >= 3 and len(classes_of_b) >= 2,
               "weight_cap": "held only if the recoveries span >= 2 distinct fault classes "
                             "(pre-registration §5.2)"},
        "P4": {"claim": "ablation (a), gap width alone, recovers at most 1 of the 4",
               "band": "0 or 1", "observed_recovered_by_a_only": by_a_only,
               "held": len(by_a_only) <= 1},
        "P5": {"claim": "in all four, the printed number stands within the shipped gap's reach",
               "observed_within_reach": in_reach,
               "held": len(in_reach) == 4,
               "consequence_if_held": "the gap expression decides none of the four, and the "
                                      "sketch as drawn cannot show them"},
    }

    out = {
        "tick": 61,
        "date": "2026-08-12",
        "question": "which part of the committed sieve decides the six papers the two readings "
                    "disagree about — and does the second work's subject cover them?",
        "instrument": wt.VERSION,
        "run_void": bool(voids),
        "defeat_conditions_fired": voids,
        "ablations": {
            "a_gap400": {"what": "GAP bound 100 -> 400, nothing else",
                         "adopted": False, "written_to_disk": False},
            "b_bare_threshold": {"what": "profile rel admits a bare `thresholds?`",
                                 "rel_used": bare_rel, "adopted": False,
                                 "written_to_disk": False},
        },
        "inputs_sha256": {n: sha(wtpath(n)) for n in
                          [PROFILE, LANDED_COUNTS, SETS, HANDREAD, "warrant_trace.py"]
                          + list(WINDOW_FILES)},
        "papers": [papers[a] for a in six],
        "forecasts": scored,
    }
    path = os.path.join(HERE, "secondsight-tick61.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print(wt.VERSION)
    print("void:", voids or "no defeat condition fired")
    for a in six:
        p = papers[a]
        print(f"  {a:14s} {p['side']:26s} landed={p['landed_sites_0.8']} "
              f"windows={p['sites_over_windows']} recovered_by={p.get('recovered_by','-')} "
              f"reach={p.get('reach',{}).get('within_reach','-')} "
              f"units={p.get('reach',{}).get('units','-')}")
    for k, v in scored.items():
        print(f"  {k}: {'HELD' if v['held'] else 'REFUTED'}  {v['claim']}")
    print("wrote", path)


if __name__ == "__main__":
    main()
