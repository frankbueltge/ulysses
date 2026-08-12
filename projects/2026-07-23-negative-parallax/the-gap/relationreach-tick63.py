#!/usr/bin/env python3
"""relationreach-tick63 — how far does the profile's own relation vocabulary reach?

Tick 62 enumerated 866 purely typographic accidents over two pinned fragments and recovered the
printed threshold ZERO times, while a control that inserts ONE WORD — `of` — recovered it in
both, with the shipped instrument, first try. The decision that followed changed the second
work's subject: what the visitor moves is a rule of the reader, not a mark on the page.

That control was two fragments and one word chosen by hand. This run asks the mechanical
version, over the whole `B-SITE` class: for every relation alternative the shipped profile
already declares, inserted at every inter-word position of each of the four fragments, how many
of the four does the vocabulary recover?

Clauses C1, C2 and C3, their bands, what each outcome decides, the adversarial read, the blind
step and defeat conditions D-H .. D-K are fixed in `../PREREGISTRATION-tick63.md`, written at
the close of tick 62, in an earlier session, before this file existed.

Nothing is repaired here. The instrument is the shipped one, unmodified; no profile is copied,
moved or written; no file under `warrant-trace/` is touched; no mutant string enters any rate.
The run writes one JSON under `the-gap/`.

Inputs are landed files only. No corpus, no network.

Usage: python3 relationreach-tick63.py
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
SETS = "numerator-sets-tick60-B.json"

# D-B-equivalent input integrity: the hand table carries the sha landed at ticks 61 and 62.
EXPECTED_SHA = {
    "handread-tick56.csv":
        "fd26ce5127ffa78e6ede090b1ee61024a387d4a670fac8e5371bd18bdcf661a1",
}

# Pre-registration §2's parenthetical list, transcribed verbatim for AUDIT ONLY. It is never
# the source of an insertion — §2 and §5 both say the tokens are read out of the profile by the
# script. It is typed here for exactly one purpose: to check, in public, whether the list a
# reader of the pre-registration would check against is the same set the profile yields.
PREREG_LISTED = ["<", ">", "=", "at least", "no less than", "greater than", "larger than",
                 "higher than", "above", "below", "less than", "smaller than", "lower than",
                 "exceeding", "exceeds", "exceed", "set to", "fixed at", "of at least",
                 "ranging from", "from", "of"]

C2_PAPER = "2608.02980v1"       # the paper C2 forecasts the vocabulary does NOT recover


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def wtpath(name):
    return os.path.join(WT, name)


def load_profile():
    """The shipped profile, unmodified. This tick moves nothing on the instrument."""
    with open(wtpath(PROFILE), encoding="utf-8") as fh:
        return Profile(json.load(fh), wtpath(PROFILE))


# ------------------------------------------------------------------ the vocabulary
#
# §2/§5, the blind step: "read out of the profile by the script, never typed into it". The
# profile's `rel` is a regex, so reading it means expanding its alternation back into the
# literal tokens it admits. The expander below handles exactly the constructs `rel` uses —
# literals, `\s+`, `(?:a|b|c)` groups, and `?` on a single character or on a group — and
# raises on anything else rather than guessing.
def _split_top(src):
    """Split on `|` at nesting depth 0."""
    out, depth, cur = [], 0, ""
    i = 0
    while i < len(src):
        c = src[i]
        if c == "\\":
            cur += src[i:i + 2]
            i += 2
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        if c == "|" and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    out.append(cur)
    return out


def expand(src):
    """Every literal string the (restricted) regex `src` matches."""
    units = []                                  # list of lists of alternatives
    i = 0
    while i < len(src):
        if src.startswith(r"\s+", i):
            unit, i = [" "], i + 3
        elif src.startswith("(?:", i):
            depth, j = 1, i + 3
            while j < len(src) and depth:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "(":
                    depth += 1
                elif src[j] == ")":
                    depth -= 1
                j += 1
            inner = src[i + 3:j - 1]
            unit = [s for alt in _split_top(inner) for s in expand(alt)]
            i = j
        elif src[i] == "\\":
            unit, i = [src[i + 1]], i + 2
        elif src[i].isalnum() or src[i] in "<>=% -.":
            unit, i = [src[i]], i + 1
        else:
            raise ValueError("relation vocabulary: unhandled construct at %r" % src[i:])
        if i < len(src) and src[i] == "?":      # optional: this unit, or nothing
            unit = unit + [""]
            i += 1
        units.append(unit)
    out = [""]
    for unit in units:
        out = [pre + alt for pre in out for alt in unit]
    return out


def vocabulary(prof):
    """The profile's relation alternatives, as literal tokens, in the profile's own order."""
    rel = prof.raw["rel"]
    src = rel[3:-1] if rel.startswith("(?:") and rel.endswith(")") else rel
    toks, seen = [], set()
    for alt in _split_top(src):
        for tok in expand(alt):
            tok = re.sub(r"\s+", " ", tok).strip()
            if tok and tok not in seen:
                seen.add(tok)
                toks.append(tok)
    return toks


# ------------------------------------------------------------------ the enumeration
def positions(frag):
    """Every inter-word position of the fragment, as a character offset.

    §2: "insert that token at every inter-word position of the fragment, space-padded". The
    positions are the fragment's own word boundaries — the start offset of each whitespace-
    delimited token, plus the end of the string. Insertion is ` TOKEN ` at that offset, so no
    word is ever joined to another and no word is ever split: the failure mode named in the
    adversarial read §4.2 cannot occur under this padding, and the recorded mutant string lets
    a reader check that claim without re-running.
    """
    return [m.start() for m in re.finditer(r"\S+", frag)] + [len(frag)]


def mutate(frag, pos, tok):
    return frag[:pos] + " " + tok + " " + frag[pos:]


def verdict(text, prof):
    """What the shipped instrument answers on this exact string."""
    return [{"value": s["value"], "match": s["match"]} for s in sites(normalise(text), prof)]


def focus_number(fragment, prof):
    """The printed threshold, chosen by the PROFILE's own focus value, never by hand.

    Identical rule to `secondsight-tick61.focus_number` and `typographic-tick62.focus_number`
    (blind step, §5): the first numeral in the landed fragment whose value equals the profile's
    declared focus threshold, or one of its declared equivalents. Returns (literal, offset).
    """
    want = {float(prof.raw["focus_value"])}
    for eq in prof.raw.get("focus_equivalents", []):
        want.add(float(eq) / 100.0 if float(eq) > 1 else float(eq))
    for m in re.finditer(r"\d{1,3}(?:\.\d+)?", fragment):
        v = float(m.group(0))
        if v in want or (v > 1 and v / 100.0 in want):
            return m.group(0), m.start()
    return None, None


def name_span(fragment, prof, before):
    """The statistic's name immediately preceding `before`, by the profile's OWN term regex.

    C3 asks whether a recovery is produced by a token placed between the statistic's name and
    the printed number. The name is not chosen by hand: it is the last match of the profile's
    `term` pattern that ends at or before the printed number's offset.
    """
    term = re.compile(prof.raw["term"], re.I)
    last = None
    for m in term.finditer(fragment):
        if m.end() <= before:
            last = m
    return (last.group(0), last.start(), last.end()) if last else (None, None, None)


def run_fragment(aid, frag, prof, tokens):
    norm = normalise(frag)
    printed, printed_at = focus_number(frag, prof)
    base = verdict(frag, prof)
    nm, nm_start, nm_end = name_span(frag, prof, printed_at if printed_at is not None else 0)

    pos_list = positions(frag)
    recoveries, any_site = [], []
    for tok in tokens:
        for pos in pos_list:
            text = mutate(frag, pos, tok)
            got = verdict(text, prof)
            if not got:
                continue
            in_span = (nm_end is not None and printed_at is not None
                       and nm_end <= pos <= printed_at)
            rec = {"token": tok, "position": pos, "in_name_number_span": in_span,
                   "mutant": text, "sites": got}
            any_site.append(rec)
            if printed is not None:
                on_target = [s for s in got if s["value"] is not None
                             and abs(float(s["value"]) - float(printed)) < 1e-9]
                if on_target:
                    recoveries.append(dict(rec, on_target=on_target))

    by_token = {}
    for r in recoveries:
        by_token[r["token"]] = by_token.get(r["token"], 0) + 1

    # The clause is scored on §2's own parenthetical (see `deviation_note`); the wider set the
    # profile yields is reported beside it. Both are read off the SAME enumeration, so no
    # fragment is measured twice and neither number is a re-run of the other.
    strict = [r for r in recoveries if r["token"] in PREREG_LISTED]

    return {
        "arxiv": aid,
        "fragment": frag,
        "normalise_is_identity": norm == frag,
        "printed_threshold": printed,
        "printed_threshold_offset": printed_at,
        "statistic_name": nm,
        "name_span": [nm_start, nm_end],
        "shipped_on_fragment": base,
        "inter_word_positions": len(pos_list),
        "mutants_generated": len(tokens) * len(pos_list),
        "mutants_returning_any_site": len(any_site),
        "mutants_recovering_printed_value": len(recoveries),
        "recovered": bool(strict),
        "recovered_with_full_profile_vocabulary": bool(recoveries),
        "recoveries_preregistered_tokens": len(strict),
        "recoveries_by_token": by_token,
        "recovery_positions_distinct": sorted({r["position"] for r in recoveries}),
        "preregistered_recoveries_in_name_number_span": sum(1 for r in strict
                                                            if r["in_name_number_span"]),
        "all_recoveries_in_name_number_span": sum(1 for r in recoveries
                                                  if r["in_name_number_span"]),
        "c3_satisfied": (any(r["in_name_number_span"] for r in strict)
                         if strict else None),
        # D-J: every recovery in full — token, position, whole mutant string, the site's match.
        "recoveries": recoveries,
        # a site off the printed value is not a recovery, but it is evidence, and hiding it
        # would leave only the answer the forecast wanted (the rule tick 62 set).
        "sites_found": any_site,
    }


def main():
    prof = load_profile()
    voids = []

    for name, want in EXPECTED_SHA.items():
        got = sha(wtpath(name))
        if got != want:
            voids.append(f"input integrity: {name} sha {got} != landed expectation {want}")

    # ---- the vocabulary, read out of the profile
    tokens = vocabulary(prof)

    # D-H: every token this run inserts is admitted by the profile's own `rel`, checked by
    # matching each token against the compiled expression rather than by string search — the
    # profile stores `\s+`, not a space, so a substring test would be a test of the transcription.
    rel_re = re.compile(prof.raw["rel"], re.I)
    for tok in tokens:
        m = rel_re.fullmatch(tok)
        if not m:
            voids.append(f"D-H: token {tok!r} is not a full alternative of the profile's rel")

    # The audit §2's parenthetical asks for. The list a reader would check against and the set
    # the profile actually yields are compared here, and any difference is reported rather than
    # resolved quietly.
    listed, derived = set(PREREG_LISTED), set(tokens)
    only_derived, only_listed = sorted(derived - listed), sorted(listed - derived)

    # ---- the class, by its landed definition (blind step §5)
    with open(wtpath(SETS), encoding="utf-8") as fh:
        sets = json.load(fh)
    b_site = [r["arxiv"] for r in sets["only_I"] if r["label"] == "B-SITE"]
    if len(b_site) != 4:
        voids.append(f"class definition: numerator-sets-tick60-B.json yields {len(b_site)} "
                     f"B-SITE papers, the pre-registration names 4")

    frags = {}
    with open(wtpath(HANDREAD), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            frags[r["arxiv"]] = r

    results = [run_fragment(aid, frags[aid]["fragment"], prof, tokens) for aid in b_site]

    # D-I: the unmutated fragments return no site, reproducing ticks 61 and 62.
    for r in results:
        if r["shipped_on_fragment"]:
            voids.append(f"D-I: {r['arxiv']} unmutated returns "
                         f"{len(r['shipped_on_fragment'])} site(s); ticks 61/62 recorded none")
        if r["printed_threshold"] is None:
            voids.append(f"D-I: {r['arxiv']} carries no numeral at the profile's focus value")

    # ---- the clauses
    recovered = [r["arxiv"] for r in results if r["recovered"]]
    not_recovered = [r["arxiv"] for r in results if not r["recovered"]]
    c1_count = len(recovered)
    recovered_full = [r["arxiv"] for r in results
                      if r["recovered_with_full_profile_vocabulary"]]

    c3_states = [r["c3_satisfied"] for r in results if r["recovered"]]
    c3_holds = bool(c3_states) and all(c3_states)

    c1 = {"clause": "over the four B-SITE fragments the enumeration recovers the printed "
                    "threshold in exactly 3 of 4",
          "scored_on": "the 22 tokens of §2's parenthetical",
          "band": 3, "observed": c1_count, "held": c1_count == 3,
          "recovered": recovered, "not_recovered": not_recovered,
          "observed_with_full_profile_vocabulary": len(recovered_full),
          "recovered_with_full_profile_vocabulary": recovered_full,
          "the_two_sets_agree": sorted(recovered) == sorted(recovered_full)}
    c2 = {"clause": f"the paper not recovered is {C2_PAPER}",
          "observed_not_recovered": not_recovered,
          "held": not_recovered == [C2_PAPER] and c1_count == 3}
    c3 = {"clause": "for every fragment recovered, at least one recovering insertion places "
                    "the token between the statistic's name and the printed number",
          "per_paper": {r["arxiv"]: r["c3_satisfied"] for r in results if r["recovered"]},
          "held": c3_holds}
    if not c3_holds:
        voids.append("C3 refuted: C1 and C2 are reported as uninterpretable (§3), whatever "
                     "their counts")

    # per-token tally across the class — §4.3 asks for this without having to be asked
    tally = {}
    for r in results:
        for tok, n in r["recoveries_by_token"].items():
            tally[tok] = tally.get(tok, 0) + n
    papers_by_token = {}
    for r in results:
        for tok in r["recoveries_by_token"]:
            papers_by_token.setdefault(tok, []).append(r["arxiv"])

    decided = {
        3: "The relation vocabulary is the right axis for the second work, and its limit has a "
           "name: a number that is not the first in its parenthesis. The work gets one movement "
           "— the reader's relation rule — and one honest edge.",
        4: "The vocabulary reaches the whole class, the parenthesis case is not special, and "
           "the work's edge is somewhere I have not looked. Cleaner than forecast, and it costs "
           "me the interesting boundary.",
    }.get(c1_count,
          "The vocabulary reaches less than the tick-62 control implied; two hand-chosen `of`s "
          "generalise worse than they read, and the change of subject decided at tick 62 is "
          "revisited in the journal with this number beside it.")
    if not c3_holds:
        decided = ("C3 is refuted: the measurement is not about the gap between the name and "
                   "the number, and C1 and C2 say nothing until it is.")

    out = {
        "tick": 63,
        "date": "2026-08-12",
        "question": "over the whole B-SITE class, how far does the profile's OWN declared "
                    "relation vocabulary reach when the enumeration is exhaustive rather than "
                    "chosen by hand?",
        "instrument": wt.VERSION,
        "instrument_modified": False,
        "run_void": bool(voids),
        "defeat_conditions_fired": voids,
        "inputs_sha256": {n: sha(wtpath(n)) for n in
                          [PROFILE, HANDREAD, SETS, "warrant_trace.py"]},
        "class": {"definition": "B-SITE in numerator-sets-tick60-B.json (landed tick 60)",
                  "members": b_site},
        "vocabulary": {
            "source": "profiles/iou-0.5.json `rel`, expanded by this script",
            "tokens": tokens,
            "count": len(tokens),
            "preregistration_parenthetical": PREREG_LISTED,
            "in_profile_not_in_parenthetical": only_derived,
            "in_parenthetical_not_in_profile": only_listed,
            "deviation_note":
                "§2's parenthetical lists 22 tokens and omits the `thresholds? (of|at|is|was|"
                "set to)` family the profile also declares. §2's operative sentence is `every "
                "relation alternative already listed in the rel field`, read by the script, so "
                "the derived set is executed. The direction is stated because it matters here "
                "and did not at tick 62: a LARGER token set can only push C1's count UP, so — "
                "unlike tick 62's superset — it could make a point-band clause hold that the "
                "narrower set would refute. Both counts are therefore reported below, and C1 is "
                "scored on the parenthetical's own 22 tokens, the set a reader of the "
                "pre-registration would check against.",
        },
        "insertion_grammar": {
            "positions": "every inter-word position (start offset of each whitespace-delimited "
                         "token, plus end of string)",
            "padding": "` TOKEN `",
            "no_word_joined_or_split": "guaranteed by construction; see positions() docstring",
            "excluded": "nothing is deleted, no digit or existing word is altered, no token is "
                        "invented",
        },
        "clauses": {"C1": c1, "C2": c2, "C3": c3},
        "recoveries_by_token_across_class": tally,
        "papers_by_token": papers_by_token,
        "results": results,
        "what_this_decides": decided,
    }
    path = os.path.join(HERE, "relationreach-tick63.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print(wt.VERSION)
    print("vocabulary:", len(tokens), "tokens;",
          "not in §2's list:", only_derived or "none")
    print("void:", voids or "no defeat condition fired")
    for r in results:
        print(f"  {r['arxiv']:14s} printed={r['printed_threshold']} "
              f"name={r['statistic_name']!r} positions={r['inter_word_positions']} "
              f"mutants={r['mutants_generated']} any_site={r['mutants_returning_any_site']} "
              f"recoveries={r['mutants_recovering_printed_value']} "
              f"-> {'RECOVERED' if r['recovered'] else 'not recovered'} "
              f"c3={r['c3_satisfied']}")
        if r["recoveries_by_token"]:
            print("      by token:", r["recoveries_by_token"])
    print(f"C1 band 3, observed {c1_count} -> {'HELD' if c1['held'] else 'REFUTED'}")
    print(f"C2 -> {'HELD' if c2['held'] else 'REFUTED'}  not recovered: {not_recovered}")
    print(f"C3 -> {'HELD' if c3['held'] else 'REFUTED'}")
    print("across the class, by token:", tally)
    print("wrote", path)


if __name__ == "__main__":
    main()
