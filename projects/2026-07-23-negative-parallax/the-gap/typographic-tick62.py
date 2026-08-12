#!/usr/bin/env python3
"""typographic-tick62 — can one typographic accident recover a threshold the sieve cannot see?

`the-gap` is a work whose grammar is *one movable typographic accident*: the visitor moves a
line break, a citation marker, a space, and a printed number enters or leaves the record. Tick 61
measured that the gap expression decides NONE of the four papers where the shipped sieve loses a
printed threshold the hand census finds. This tick asks the next question mechanically rather
than by judgement: over two of those four fragments, enumerate EVERY purely typographic single
mutation there is, and count how many make the shipped sieve 0.8 return the printed number.

Clauses C1 and C2, their bands, the adversarial read, the blind step and defeat conditions D-E,
D-F and D-G are fixed in `../PREREGISTRATION-tick62.md`, written at the close of tick 61, in an
earlier session, before this file existed.

Nothing is repaired here. The instrument is the shipped one, unmodified; no profile is copied or
moved; no file under `warrant-trace/` is written. The run writes one JSON under `the-gap/`.

Inputs are landed files only. No corpus, no network.

Usage: python3 typographic-tick62.py
"""
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
HANDREAD = "handread-tick56.csv"

# The two fragments named in the pre-registration §2: the extreme case of the class, and one
# ordinary member. Chosen in the earlier session, by the stated rule, before any mutation ran.
C1_PAPER = "2608.03136v1"       # `IoU 0.50` — one space between the name and the number
C2_PAPER = "2607.10575v1"       # `IoU threshold 0.5` — the control (tick 61: ablation b recovers)

# D-B-equivalent input integrity: the hand table carries the sha landed at tick 61.
EXPECTED_SHA = {
    "handread-tick56.csv":
        "fd26ce5127ffa78e6ede090b1ee61024a387d4a670fac8e5371bd18bdcf661a1",
}

MARKER = "<<CITE:x>>"           # the reader's own citation marker, per §2


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def wtpath(name):
    return os.path.join(WT, name)


def load_profile():
    """The shipped profile, unmodified. This tick moves nothing on the instrument."""
    with open(wtpath(PROFILE), encoding="utf-8") as fh:
        return Profile(json.load(fh), wtpath(PROFILE))


def verdict(text, prof):
    """What the shipped instrument answers on this exact string."""
    return [{"value": s["value"], "match": s["match"]} for s in sites(normalise(text), prof)]


def focus_number(fragment, prof):
    """The printed threshold, chosen by the PROFILE's own focus value, never by hand.

    Identical rule to `secondsight-tick61.focus_number` (blind step, §5): the first numeral in
    the landed fragment whose value equals the profile's declared focus threshold.
    """
    want = {float(prof.raw["focus_value"])}
    for eq in prof.raw.get("focus_equivalents", []):
        want.add(float(eq) / 100.0 if float(eq) > 1 else float(eq))
    for m in re.finditer(r"\d{1,3}(?:\.\d+)?", fragment):
        v = float(m.group(0))
        if v in want or (v > 1 and v / 100.0 in want):
            return m.group(0), m.start()
    return None, None


# ------------------------------------------------------------------ the enumeration
#
# §2 fixes what "purely typographic" means, exhaustively and before the run:
#
#   at every character position: insert a space · insert a newline · insert a blank line ·
#   insert `<<CITE:x>>` · delete the character standing there;
#   at every position where a space stands: replace it with a newline, with a tab, or delete it;
#   nothing that inserts, deletes or alters a word, digit or comparison sign.
#
# Two arithmetic notes, both recorded rather than decided quietly:
#
#  (1) Insertions are enumerated at N+1 points — before each of the N characters AND after the
#      last one — where the strict reading of "every character position" gives N. The executed
#      set is therefore a SUPERSET of the pre-registered one. A superset can only make C1/C2
#      easier to refute, never easier to hold, so the deviation runs against the forecast and
#      is taken. Both counts are recorded.
#  (2) "delete it" for a space position is the same string as "delete the character standing
#      there" at that position; it is generated once and the duplication is stated, not hidden.
INSERTIONS = [("insert_space", " "), ("insert_newline", "\n"),
              ("insert_blank_line", "\n\n"), ("insert_cite_marker", MARKER)]


def enumerate_mutations(frag):
    """Every purely typographic single mutation of `frag`, as (kind, position, string)."""
    out = []
    n = len(frag)
    for kind, ins in INSERTIONS:
        for i in range(n + 1):                       # note (1): N+1 insertion points
            out.append((kind, i, frag[:i] + ins + frag[i:]))
    for i in range(n):
        out.append(("delete_char", i, frag[:i] + frag[i + 1:]))
    for i, c in enumerate(frag):
        if c == " ":
            out.append(("space_to_newline", i, frag[:i] + "\n" + frag[i + 1:]))
            out.append(("space_to_tab", i, frag[:i] + "\t" + frag[i + 1:]))
            # space_delete is `delete_char` at the same position — see note (2).
    return out


def implied_count(frag):
    """The count §2 implies, in both readings. D-E compares the executed set against these."""
    n, s = len(frag), frag.count(" ")
    return {"chars": n, "spaces": s,
            "strict_reading_insertion_points": n,
            "strict_reading_total": 4 * n + n + 2 * s,
            "executed_insertion_points": n + 1,
            "executed_total": 4 * (n + 1) + n + 2 * s}


def run_fragment(aid, frag, prof, clause):
    printed, _ = focus_number(normalise(frag), prof)
    base = verdict(frag, prof)

    muts = enumerate_mutations(frag)
    counts = implied_count(frag)
    voids = []
    if len(muts) != counts["executed_total"]:
        voids.append(f"D-E: {aid} generated {len(muts)} mutants, "
                     f"the enumeration implies {counts['executed_total']}")
    if base:
        voids.append(f"D-F: {aid} unmutated fragment returns {len(base)} site(s); "
                     f"tick 61 recorded none")

    recoveries, any_site = [], []
    for kind, pos, text in muts:
        got = verdict(text, prof)
        if not got:
            continue
        rec = {"kind": kind, "position": pos, "mutant": text, "sites": got}
        any_site.append(rec)
        if printed is not None:
            on_target = [s for s in got if s["value"] is not None
                         and abs(float(s["value"]) - float(printed)) < 1e-9]
            if on_target:
                rec = dict(rec, on_target=on_target)
                recoveries.append(rec)

    by_kind = {}
    for r in recoveries:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1

    return {
        "clause": clause,
        "arxiv": aid,
        "fragment": frag,
        "printed_threshold": printed,
        "shipped_on_fragment": base,
        "mutants_generated": len(muts),
        "mutants_distinct_strings": len({t for _, _, t in muts}),
        "enumeration": counts,
        "defeat_conditions_fired": voids,
        "mutants_returning_any_site": len(any_site),
        "mutants_recovering_printed_value": len(recoveries),
        "recoveries_by_kind": by_kind,
        "held": len(recoveries) == 0 and not voids,
        # every mutant that returned anything at all is kept: a site off the printed value is
        # not a recovery (§4.1 of the tick-61 adversarial read) but it is evidence, and hiding
        # it would leave only the answer the forecast wanted.
        "sites_found": any_site,
        "recoveries": recoveries,
    }


# ------------------------------------------------------------------ the harness control
#
# Not part of C1 or C2, and it moves no verdict. The tick-61 adversarial read (§4.1) named C1
# "close to unfalsifiable by construction": the enumeration is defined to exclude the one thing
# that could work. A run of that shape must show it can return non-zero at all, or a count of
# zero says nothing about the fragments and everything about the harness.
#
# Each control inserts ONE WORD — the relation the sentence never printed — into the same
# fragment, and is run through the SAME `verdict` with the SAME shipped profile. §2 excludes a
# word insertion from "purely typographic" by name, so no control string is a mutant and none is
# counted in C1 or C2.
CONTROLS = [
    ("C1 fragment + the word `of`", C1_PAPER,
     "a single COCO-style AP (IoU of 0.50 : 0.05 : 0.95 , maxDets = 100 per image)"),
    ("C2 fragment + the word `of`", C2_PAPER,
     "considered newly added if they do not match an original annotation "
     "at IoU threshold of 0.5"),
]


def run_controls(prof, printed_by_paper):
    out = []
    for label, aid, text in CONTROLS:
        got = verdict(text, prof)
        printed = printed_by_paper.get(aid)
        on_target = [s for s in got if printed is not None and s["value"] is not None
                     and abs(float(s["value"]) - float(printed)) < 1e-9]
        out.append({"label": label, "arxiv": aid, "text": text,
                    "excluded_from_clause_by": "§2 — a word insertion is not a typographic "
                                               "accident",
                    "sites": got, "recovers_printed_value": bool(on_target)})
    return out


def main():
    prof = load_profile()

    voids = []
    for name, want in EXPECTED_SHA.items():
        got = sha(wtpath(name))
        if got != want:
            voids.append(f"input integrity: {name} sha {got} != landed expectation {want}")

    frags = {}
    with open(wtpath(HANDREAD), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            frags[r["arxiv"]] = r

    c1 = run_fragment(C1_PAPER, frags[C1_PAPER]["fragment"], prof, "C1")
    c2 = run_fragment(C2_PAPER, frags[C2_PAPER]["fragment"], prof, "C2")
    voids += c1["defeat_conditions_fired"] + c2["defeat_conditions_fired"]

    controls = run_controls(prof, {C1_PAPER: c1["printed_threshold"],
                                   C2_PAPER: c2["printed_threshold"]})
    if not any(c["recovers_printed_value"] for c in controls):
        voids.append("harness control: no control recovers the printed value — a count of zero "
                     "mutants would then be a fact about this script, not about the fragments")

    outcome = ("both_hold" if c1["held"] and c2["held"] else
               "C1_holds_C2_refuted" if c1["held"] else
               "C1_refuted_C2_holds" if c2["held"] else "both_refuted")
    decided = {
        "both_hold": "The sketch's grammar cannot show the errors that decide the computer-"
                     "vision figure. The second work needs a second movement, and what the "
                     "visitor moves is no longer a mark on the page but a rule of the reader — "
                     "a change of subject, recorded as one.",
        "C1_holds_C2_refuted": "The grammar reaches part of the class. The work keeps one "
                               "movement and gains a panel that shows where it stops.",
        "C1_refuted_C2_holds": "A typographic accident recovers even the one-space case; the "
                               "tick-61 form finding is narrower than it reads and the sketch "
                               "stands as drawn.",
        "both_refuted": "A typographic accident recovers both; the tick-61 form finding is "
                        "narrower than it reads and the sketch stands as drawn.",
    }[outcome]

    out = {
        "tick": 62,
        "date": "2026-08-12",
        "question": "can one purely typographic accident — the only thing `the-gap` lets a "
                    "visitor move — recover a printed threshold the shipped sieve does not see?",
        "instrument": wt.VERSION,
        "instrument_modified": False,
        "run_void": bool(voids),
        "defeat_conditions_fired": voids,
        "inputs_sha256": {n: sha(wtpath(n)) for n in
                          [PROFILE, HANDREAD, "warrant_trace.py"]},
        "mutation_grammar": {
            "insertions": [k for k, _ in INSERTIONS],
            "cite_marker": MARKER,
            "deletions": "the character standing at each position",
            "space_rewrites": ["space_to_newline", "space_to_tab",
                               "space_delete (== delete_char, generated once)"],
            "excluded_by_preregistration": "anything that inserts, deletes or alters a word, "
                                           "digit or comparison sign",
            "deviation_from_preregistration": "insertions enumerated at N+1 points rather than "
                                              "N; the executed set is a superset of the "
                                              "pre-registered one and can only refute, never "
                                              "hold falsely. Both counts recorded per fragment.",
        },
        "clauses": {"C1": c1, "C2": c2},
        "harness_control": controls,
        "outcome": outcome,
        "what_this_decides": decided,
    }
    path = os.path.join(HERE, "typographic-tick62.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print(wt.VERSION)
    print("void:", voids or "no defeat condition fired")
    for c in (c1, c2):
        print(f"  {c['clause']} {c['arxiv']:14s} printed={c['printed_threshold']} "
              f"mutants={c['mutants_generated']} (distinct {c['mutants_distinct_strings']}) "
              f"any_site={c['mutants_returning_any_site']} "
              f"recoveries={c['mutants_recovering_printed_value']} "
              f"-> {'HELD' if c['held'] else 'REFUTED'}")
        if c["recoveries_by_kind"]:
            print("      by kind:", c["recoveries_by_kind"])
    for c in controls:
        print(f"  control {c['label']:30s} sites={len(c['sites'])} "
              f"recovers={c['recovers_printed_value']}")
    print("outcome:", outcome)
    print("wrote", path)


if __name__ == "__main__":
    main()
