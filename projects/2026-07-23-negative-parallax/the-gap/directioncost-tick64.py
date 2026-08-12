#!/usr/bin/env python3
"""directioncost-tick64 — how much of a published rate rests on sites whose direction the
instrument never read?

Tick 63 established, over the four `B-SITE` fragments, that the sieve tests only that a
comparison-shaped word stands in ONE slot between the statistic's name and its number — and
that all 32 tokens of the profile's relation vocabulary work there, `below` exactly as well as
`above`. That was reach, measured on four fragments built by hand. This run asks the cost, on
the corpus: of the sites the instrument actually landed, how many carry a relation that runs
AGAINST the criterion's own direction? IoU 0.5 is a lower bound — the deriving document
(Everingham et al. 2010 §4.2) says the overlap "must exceed 0.5" — so a site reading `IoU <
0.5` is not an invocation of that criterion in the same sense, and the sieve cannot tell.

Clauses C1, C2, C3, their bands, the classification of all 32 tokens, what each outcome
decides, the adversarial read, the blind step and defeat conditions D-L .. D-O are fixed in
`../PREREGISTRATION-tick64.md`, written at the close of tick 63, in an earlier session, before
this file existed.

Nothing is repaired here. The instrument is the shipped one, unmodified; no profile is copied,
moved or written; no file under `warrant-trace/` is touched; no rate is restated. The run
writes one JSON under `the-gap/`.

Inputs are landed files only. No corpus, no network, no re-measurement — the sites are taken
exactly as the instrument recorded them at tick 57.

TWO PARSE RULES THE PRE-REGISTRATION DID NOT FIX, fixed here before the run and recorded
rather than absorbed. Neither was chosen after seeing a class count; both are reported with
the figure that shows what they cost.

  R1  §2 says the relation is "the last rel match that begins at or before the site's recorded
      `value` inside the match string" — and a value literal can occur more than once inside
      one match. The rule executed is: the LAST standalone occurrence of the value literal
      (not part of a longer numeral). The run also computes the classification under the FIRST
      occurrence and reports whether any site's class differs, so the size of the choice is
      visible rather than argued.
  R2  Where the value stands BEFORE every relation token in the match — site patterns 3 and 4
      of the profile put the number first — no rel begins at or before it, and §2's rule
      yields `NONE`. That is executed as written; the count of sites where a rel token exists
      in the match but only AFTER the value is recorded separately (`rel_only_after_value`),
      because those are sites whose direction is on the page and outside this rule's reach.

Usage: python3 directioncost-tick64.py
"""
import ast
import hashlib
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.normpath(os.path.join(HERE, "..", "warrant-trace"))
sys.path.insert(0, WT)

import warrant_trace as wt                                              # noqa: E402
from warrant_trace import Profile                                       # noqa: E402

PROFILE = "profiles/iou-0.5.json"
DUMP = "sites-tick57.txt"
IDS = "frame-tick57.txt"

# D-M: the dump is the one tick 57 landed. §1 states its shape, read for feasibility only.
EXPECTED_BLOCKS = 97
EXPECTED_SITES = 292
MATCH_CAP = 110          # §4.4: the instrument caps the dump's `match` field

# ------------------------------------------------------------------ §2's classification
#
# Transcribed from the pre-registration, which fixed it before any site was classified (§5).
# The `threshold(s) of|at|is|was|set to` family is generated rather than typed one by one, and
# D-L checks the result against the vocabulary the profile actually yields.
LOWER = [">", "at least", "no less than", "greater than", "larger than", "higher than",
         "above", "exceed", "exceeds", "exceeding", "of at least"]
UPPER = ["<", "below", "less than", "smaller than", "lower than"]
NEUTRAL = ["=", "of", "from", "set to", "fixed at", "ranging from"] + [
    f"{noun} {tail}" for noun in ("threshold", "thresholds")
    for tail in ("of", "at", "is", "was", "set to")]

CLASSES = {"LOWER": LOWER, "UPPER": UPPER, "NEUTRAL": NEUTRAL}


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def wtpath(name):
    return os.path.join(WT, name)


def load_expander():
    """The tick-63 vocabulary expander, imported from the landed file, not re-implemented.

    §2/§5, the blind step: the tokens are read out of the profile by the script. Tick 63 wrote
    and landed the reader that does it; importing it means this run cannot quietly derive a
    different set than the one that measurement used.
    """
    path = os.path.join(HERE, "relationreach-tick63.py")
    spec = importlib.util.spec_from_file_location("relationreach_tick63", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm_token(s):
    return re.sub(r"\s+", " ", s).strip()


BLOCK_RE = re.compile(r"^### (\d+) (\S+)\s+(sites=(\d+)|NO_SOURCE)\s*$")
SITE_RE = re.compile(r"^  \[(\d+)\] match=(.+) value=(None|'(?:[^'\\]|\\.)*')\s*$")


def parse_dump(path):
    """The landed dump, back into blocks and sites. reprs are read, never re-quoted."""
    blocks, anomalies = [], []
    cur = None
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            m = BLOCK_RE.match(line)
            if m:
                cur = {"read_order": int(m.group(1)), "arxiv": m.group(2),
                       "no_source": m.group(3) == "NO_SOURCE",
                       "declared_sites": int(m.group(4)) if m.group(4) else None,
                       "sites": []}
                blocks.append(cur)
                continue
            m = SITE_RE.match(line)
            if m:
                if cur is None:
                    anomalies.append(f"line {lineno}: site line before any block header")
                    continue
                try:
                    match = ast.literal_eval(m.group(2))     # a repr, read as a literal
                    value = ast.literal_eval(m.group(3))
                except Exception as exc:                                    # pragma: no cover
                    anomalies.append(f"line {lineno}: unreadable repr ({exc})")
                    continue
                if not isinstance(match, str) or not (value is None or isinstance(value, str)):
                    anomalies.append(f"line {lineno}: repr is not a string")
                    continue
                cur["sites"].append({"index": int(m.group(1)), "match": match, "value": value})
    for b in blocks:
        if b["declared_sites"] is not None and b["declared_sites"] != len(b["sites"]):
            anomalies.append(f"{b['arxiv']}: header declares {b['declared_sites']} sites, "
                             f"{len(b['sites'])} parsed")
    return blocks, anomalies


def value_offsets(match, value):
    """Every standalone occurrence of the value literal inside the match string.

    Standalone means not part of a longer numeral: `0.5` inside `0.50` is not the value, and
    `50` inside `0.50` is not either.
    """
    if value is None:
        return []
    pat = re.compile(r"(?<![\d.])" + re.escape(value) + r"(?![\d.])")
    return [m.start() for m in pat.finditer(match)]


def classify(token, index):
    for name, toks in CLASSES.items():
        if token in index[name]:
            return name
    return None


def read_site(site, rel_re, index):
    """§2's extraction and classification, on one landed site."""
    match, value = site["match"], site["value"]
    rels = [{"token": norm_token(m.group(0)), "raw": m.group(0), "start": m.start()}
            for m in rel_re.finditer(match)]
    offs = value_offsets(match, value)
    plain = [m.start() for m in re.finditer(re.escape(value), match)] if value else []

    def pick(off):
        if off is None:
            return None
        before = [r for r in rels if r["start"] <= off]
        return before[-1] if before else None

    off_last = offs[-1] if offs else (plain[-1] if plain else None)
    off_first = offs[0] if offs else (plain[0] if plain else None)

    chosen = pick(off_last)                      # R1: the executed rule
    alt = pick(off_first)                        # R1: the sensitivity, entering no clause

    cls = classify(chosen["token"], index) if chosen else "NONE"
    alt_cls = classify(alt["token"], index) if alt else "NONE"

    return {
        "arxiv": None,                           # filled by the caller
        "index": site["index"],
        "match": match,
        "match_len": len(match),
        "at_match_cap": len(match) == MATCH_CAP,
        "value": value,
        "value_offsets_standalone": offs,
        "value_offset_used": off_last,
        "value_literal_absent_from_match": value is not None and not offs and not plain,
        "rel_tokens_in_match": [r["token"] for r in rels],
        "rel_token_count": len(rels),
        "multiple_rel_tokens": len(rels) > 1,
        "rel_only_after_value": bool(rels) and chosen is None,      # R2
        "token": chosen["token"] if chosen else None,
        "token_offset": chosen["start"] if chosen else None,
        "class": cls,
        "class_under_first_occurrence": alt_cls,
        "class_differs_under_first_occurrence": alt_cls != cls,
        "unclassified_token": chosen["token"] if chosen and cls is None else None,
    }


def main():
    voids = []
    prof = Profile(json.load(open(wtpath(PROFILE), encoding="utf-8")), wtpath(PROFILE))
    rel_re = prof.rel_re                    # the instrument's OWN compiled expression
    if rel_re is None:
        voids.append("the profile declares no `rel`; §2's extraction has no source")

    # ---- the vocabulary, read out of the profile by the landed tick-63 reader
    expander = load_expander()
    tokens = expander.vocabulary(prof)

    # ---- D-L: the classification is total and disjoint over that vocabulary
    index = {name: set(norm_token(t) for t in toks) for name, toks in CLASSES.items()}
    membership = {}
    for tok in tokens:
        holders = [name for name, s in index.items() if tok in s]
        membership[tok] = holders
        if len(holders) == 0:
            voids.append(f"D-L: token {tok!r} is in no class")
        elif len(holders) > 1:
            voids.append(f"D-L: token {tok!r} is in {holders}")
    declared = sorted(t for s in index.values() for t in s)
    only_declared = sorted(set(declared) - set(tokens))
    if only_declared:
        voids.append(f"D-L: classification declares tokens the profile does not yield: "
                     f"{only_declared}")

    # ---- D-M: the dump is the one tick 57 landed
    dump_path = wtpath(DUMP)
    dump_sha = sha(dump_path)
    blocks, anomalies = parse_dump(dump_path)
    for a in anomalies:
        voids.append(f"D-M: {a}")
    n_blocks = len(blocks)
    n_sites = sum(len(b["sites"]) for b in blocks)
    landed_ids = [l.strip() for l in open(wtpath(IDS), encoding="utf-8")
                  if l.strip() and not l.startswith("#")]
    shape = {
        "blocks_parsed": n_blocks,
        "blocks_expected_from_preregistration_§1": EXPECTED_BLOCKS,
        "blocks_match": n_blocks == EXPECTED_BLOCKS,
        "sites_parsed": n_sites,
        "sites_expected_from_preregistration_§1": EXPECTED_SITES,
        "sites_match": n_sites == EXPECTED_SITES,
        "landed_id_list": IDS,
        "landed_ids": len(landed_ids),
        "block_ids_equal_landed_ids": [b["arxiv"] for b in blocks] == landed_ids,
        "blocks_with_no_source": sum(1 for b in blocks if b["no_source"]),
        "blocks_with_zero_sites": sum(1 for b in blocks
                                      if not b["no_source"] and not b["sites"]),
        "parse_anomalies": anomalies,
    }
    if not shape["blocks_match"] or not shape["sites_match"]:
        voids.append(f"D-M: dump shape {n_blocks}/{n_sites} != the 97/292 stated in §1")
    if not shape["block_ids_equal_landed_ids"]:
        voids.append("D-M: the dump's blocks are not the landed tick-57 id list, in order")

    # ---- the reading
    sites = []
    for b in blocks:
        for s in b["sites"]:
            r = read_site(s, rel_re, index)
            r["arxiv"] = b["arxiv"]
            if r["unclassified_token"]:
                voids.append(f"D-L: {b['arxiv']} site {r['index']}: token "
                             f"{r['unclassified_token']!r} is in no class")
            sites.append(r)

    counts = {c: sum(1 for s in sites if s["class"] == c)
              for c in ("LOWER", "UPPER", "NEUTRAL", "NONE")}
    classified = counts["LOWER"] + counts["UPPER"] + counts["NEUTRAL"]

    per_token = {}
    for s in sites:
        if s["token"]:
            key = (s["class"], s["token"])
            per_token[key] = per_token.get(key, 0) + 1
    by_class_token = {c: {t: n for (cc, t), n in sorted(per_token.items()) if cc == c}
                      for c in ("LOWER", "UPPER", "NEUTRAL")}

    # ---- C1
    upper_share = (100.0 * counts["UPPER"] / classified) if classified else None
    c1 = {
        "clause": "UPPER-classified sites are between 5 % and 20 % inclusive of all "
                  "classified sites",
        "band_pct": [5.0, 20.0],
        "numerator": counts["UPPER"],
        "denominator_classified_sites": classified,
        "observed_pct": round(upper_share, 2) if upper_share is not None else None,
        "held": upper_share is not None and 5.0 <= upper_share <= 20.0,
        "refuted_direction": (None if upper_share is None or 5.0 <= upper_share <= 20.0
                              else ("low" if upper_share < 5.0 else "high")),
    }

    # ---- C2: at least one paper block has ALL of its sites classified UPPER
    by_paper = {}
    for s in sites:
        by_paper.setdefault(s["arxiv"], []).append(s)
    all_upper = sorted(a for a, ss in by_paper.items()
                       if ss and all(s["class"] == "UPPER" for s in ss))
    all_upper_ignoring_none = sorted(
        a for a, ss in by_paper.items()
        if any(s["class"] == "UPPER" for s in ss)
        and all(s["class"] in ("UPPER", "NONE") for s in ss))
    c2 = {
        "clause": "at least one paper block has ALL of its sites classified UPPER",
        "scored_on": "the plain reading: every site in the block is UPPER, a NONE site "
                     "counting against",
        "papers": all_upper,
        "observed": len(all_upper),
        "held": len(all_upper) >= 1,
        "beside_it_papers_all_upper_when_NONE_sites_are_ignored": all_upper_ignoring_none,
        "beside_it_count": len(all_upper_ignoring_none),
        "papers_with_at_least_one_UPPER": sorted(
            a for a, ss in by_paper.items() if any(s["class"] == "UPPER" for s in ss)),
    }

    # ---- C3: NEUTRAL is the plurality class
    c3 = {
        "clause": "NEUTRAL is the plurality class — strictly more sites than LOWER and "
                  "strictly more than UPPER",
        "counts": {k: counts[k] for k in ("LOWER", "UPPER", "NEUTRAL")},
        "held": counts["NEUTRAL"] > counts["LOWER"] and counts["NEUTRAL"] > counts["UPPER"],
    }

    # ---- D-N: the parse is shown, not claimed
    multi = [s for s in sites if s["multiple_rel_tokens"]]
    at_cap = [s for s in sites if s["at_match_cap"]]
    none_sites = [s for s in sites if s["class"] == "NONE"]
    differs = [s for s in sites if s["class_differs_under_first_occurrence"]]
    rel_after = [s for s in sites if s["rel_only_after_value"]]
    novalue = [s for s in sites if s["value"] is None]
    absent = [s for s in sites if s["value_literal_absent_from_match"]]

    shown = {
        "matches_with_more_than_one_rel_token": len(multi),
        "matches_with_more_than_one_rel_token_pct_of_sites": round(100.0 * len(multi) /
                                                                  len(sites), 2) if sites else None,
        "matches_at_the_110_character_cap": len(at_cap),
        "sites_where_R1_choice_changes_the_class": len(differs),
        "sites_where_R1_choice_changes_the_class_detail": [
            {"arxiv": s["arxiv"], "index": s["index"], "match": s["match"],
             "class": s["class"], "class_under_first_occurrence":
                 s["class_under_first_occurrence"]} for s in differs],
        "sites_with_a_rel_token_only_after_the_value": len(rel_after),
        "sites_with_a_rel_token_only_after_the_value_detail": [
            {"arxiv": s["arxiv"], "index": s["index"], "match": s["match"],
             "rel_tokens_in_match": s["rel_tokens_in_match"]} for s in rel_after],
        "sites_with_no_recorded_value": [{"arxiv": s["arxiv"], "index": s["index"],
                                          "match": s["match"]} for s in novalue],
        "sites_whose_value_literal_is_absent_from_the_match": [
            {"arxiv": s["arxiv"], "index": s["index"], "match": s["match"],
             "value": s["value"]} for s in absent],
        "NONE_sites_in_full": [{"arxiv": s["arxiv"], "index": s["index"], "match": s["match"],
                                "value": s["value"],
                                "rel_tokens_in_match": s["rel_tokens_in_match"]}
                               for s in none_sites],
    }

    # ------------------------------------------------------------------ post hoc
    #
    # Computed AFTER the three clauses above were scored, and labelled as such. None of it
    # enters a clause and none of it can rescue one: every figure here moves the reading
    # further from the band C1 missed, not towards it. It is here because leaving it out
    # would report a share as if it were a cost to the published rate, which it is not.
    focus = {float(prof.raw["focus_value"])}
    for eq in prof.raw.get("focus_equivalents", []):
        v = float(eq)
        focus.add(v / 100.0 if v > 1 else v)

    def at_focus(s):
        if not s["value"]:
            return False
        try:
            v = float(s["value"])
        except ValueError:
            return False
        return v in focus or (v > 1 and v / 100.0 in focus)

    upper_sites = [s for s in sites if s["class"] == "UPPER"]
    upper_focus = [s for s in upper_sites if at_focus(s)]
    focus_sites = [s for s in sites if at_focus(s)]

    # what the shipped 0.8 profile's own reject would do to this 0.6-era dump
    rejected = []
    for s in sites:
        for name, pat, unless in prof.site_rejects:
            if pat.search(s["match"]) and not (unless and unless.search(s["match"])):
                rejected.append({"arxiv": s["arxiv"], "index": s["index"], "reject": name,
                                 "match": s["match"], "class": s["class"]})
                break
    latex_equals = [s for s in sites if s["token"] == "=" and "\\" in s["match"]]

    post_hoc = {
        "note": "computed after the clauses were scored; enters no clause",
        "the_dump_is_0.6-era_output": {
            "why_it_matters": "rates-tick57.json records instrument 0.6; the mean-form reject "
                              "(P-C) entered the profile at tick 58 and the shipped instrument "
                              "is 0.8. The pre-registration fixed this dump as the source, so "
                              "it is executed — but the denominator is a site set the current "
                              "instrument would not reproduce.",
            "sites_the_shipped_profile_reject_would_drop": len(rejected),
            "pct_of_sites": round(100.0 * len(rejected) / len(sites), 2) if sites else None,
            "by_class": {c: sum(1 for r in rejected if r["class"] == c)
                         for c in ("LOWER", "UPPER", "NEUTRAL", "NONE")},
            "limit": "only the profile's own `site_rejects` can be replayed from a match "
                     "string. The 0.7/0.8 engine repairs decide what matches at all and "
                     "cannot be reconstructed here, so this is a floor on the difference, "
                     "not the difference. Named because it bears on C3 directly: **E6** "
                     "(0.7, tick 58) binds a comparison sign to the token on its left and "
                     "was specified against `\\sum_ i=1` and `Algorithms & N =1` — two of "
                     "the strings still standing in this dump's NEUTRAL class.",
            "detail": rejected,
        },
        "the_share_is_not_a_cost_to_the_published_rate": {
            "why": "the dump holds every site the sieve found, at any value. The 48.3 % / "
                   "33.8 % pair counts papers invoking the criterion at the profile's focus "
                   "value. Only an UPPER site AT that value can bear on it.",
            "focus_value_and_equivalents": sorted(focus),
            "sites_at_the_focus_value": len(focus_sites),
            "UPPER_sites_at_the_focus_value": len(upper_focus),
            "UPPER_share_of_focus_value_sites_pct": (
                round(100.0 * len(upper_focus) / len(focus_sites), 2) if focus_sites else None),
            "detail": [{"arxiv": s["arxiv"], "match": s["match"], "value": s["value"],
                        "token": s["token"]} for s in upper_focus],
        },
        "C2_exhibits_read": [
            {"arxiv": a,
             "sites": [{"match": s["match"], "value": s["value"], "token": s["token"],
                        "at_focus_value": at_focus(s)} for s in by_paper[a]]}
            for a in all_upper],
        "C3_holds_on_which_word": {
            "note": "§4.2 asked whether NEUTRAL wins on `of`. It does not: it wins on `=`.",
            "neutral_by_token": by_class_token["NEUTRAL"],
            "equals_share_of_NEUTRAL_pct": round(
                100.0 * by_class_token["NEUTRAL"].get("=", 0) / counts["NEUTRAL"], 2)
            if counts["NEUTRAL"] else None,
            "equals_sites_whose_match_carries_a_latex_backslash": len(latex_equals),
            "reading": "an `=` inside `\\sum_ i=1` or `xtick= 1` is not this literature "
                       "stating a threshold flatly; it is the sieve reading a formula. C3 "
                       "holds as written and the class it names is not the class it sounds "
                       "like.",
            "examples": [s["match"] for s in latex_equals[:8]],
        },
    }

    decided = None
    if c1["held"] and c2["held"]:
        decided = ("§3: the direction-blindness is a measurable share of a published rate and "
                   "it has named carriers. It becomes the second work's edge — the hole in the "
                   "middle of the vocabulary, not at its rim — and C2's papers are the "
                   "exhibits. No rate is restated as wrong; the share is printed beside it.")
    elif c1["refuted_direction"] == "low":
        decided = ("§3: the blindness is real in the fragments and rare in the corpus. It is "
                   "recorded as an instrument property with its measured size and is NOT the "
                   "work's edge; the edge is still somewhere I have not looked.")
    elif c1["refuted_direction"] == "high":
        decided = ("§3: worse than forecast. A fifth or more of the computer-vision numerator "
                   "carries a relation the instrument never read. The next operation is a "
                   "correction note against the 48.3 % / 33.8 % pair, not a work decision.")
    elif not c2["held"]:
        decided = ("§3: C1's share stands, but no paper is decided by the blindness alone — "
                   "the exhibits do not exist and the work cannot point at a victim.")
    if not c3["held"]:
        decided = (decided or "") + (" §3, C3 refuted: this literature states the threshold "
                                     "directionally more often than flatly, which makes the "
                                     "sieve's indifference costlier than C1's share alone "
                                     "suggests; all three clauses are read together.")

    out = {
        "tick": 64,
        "date": "2026-08-12",
        "question": "of the sites the instrument actually landed for IoU 0.5, how many carry "
                    "a relation that runs against the criterion's own direction — and what "
                    "does that cost the rate?",
        "instrument": wt.VERSION,
        "instrument_modified": False,
        "run_void": bool(voids),
        "defeat_conditions_fired": voids,
        "inputs_sha256": {n: sha(wtpath(n)) for n in
                          [PROFILE, DUMP, IDS, "warrant_trace.py"]},
        "criterion_direction": {
            "threshold": "IoU 0.5",
            "kind": "lower bound",
            "deriving_document": "Everingham et al. 2010, IJCV 88(2) 303-338, §4.2 — the "
                                 "overlap 'must exceed 0.5 (50%)', quoted in the profile",
        },
        "vocabulary": {
            "source": "profiles/iou-0.5.json `rel`, expanded by the landed "
                      "relationreach-tick63.py reader",
            "count": len(tokens),
            "tokens": tokens,
            "class_of_each_token": {t: (membership[t][0] if len(membership[t]) == 1 else
                                        membership[t]) for t in tokens},
            "class_sizes": {c: sum(1 for t in tokens if membership[t] == [c])
                            for c in CLASSES},
        },
        "parse_rules_fixed_at_execution": {
            "R1": "the value's offset is the LAST standalone occurrence of the recorded value "
                  "literal in the match string; the first-occurrence reading is computed and "
                  "reported, and enters no clause",
            "R2": "where every rel token stands after the value, §2's rule yields NONE; those "
                  "sites are counted separately as `rel_only_after_value`",
        },
        "dump_shape": shape,
        "dump_sha256": dump_sha,
        "counts": counts,
        "classified_sites": classified,
        "by_class_and_token": by_class_token,
        "clauses": {"C1": c1, "C2": c2, "C3": c3},
        "combination_not_enumerated_in_preregistration_§3": (
            "C1 refuted low WITH C2 holding is a pair §3 did not write out: it fixed an "
            "outcome for `C1 holds and C2 holds`, one for `C1 refuted low`, and one for `C2 "
            "refuted`, and this run produced the first and third of those conditions at once. "
            "Read as §3 wrote them and not to taste: the `C1 refuted low` sentence governs "
            "the work decision — the blindness is rare in the corpus and is NOT the second "
            "work's edge — and C2's sentence governs only what C2 asserts, that carriers "
            "exist. Two exist. They are recorded as an instrument property with a named "
            "example, not promoted to an edge by their existence."
            if (c1["refuted_direction"] == "low" and c2["held"]) else "not applicable"),
        "shown_not_claimed": shown,
        "post_hoc": post_hoc,
        "per_paper": {a: {"sites": len(ss),
                          "classes": {c: sum(1 for s in ss if s["class"] == c)
                                      for c in ("LOWER", "UPPER", "NEUTRAL", "NONE")}}
                      for a, ss in sorted(by_paper.items())},
        "sites": sites,
        "what_this_decides": decided,
        "what_this_does_not_say": "This measures what the INSTRUMENT counted, not what the "
                                  "papers say. A site the sieve never found cannot appear "
                                  "here; the four B-SITE papers of tick 63 are by definition "
                                  "absent from this dump. Nothing here is a false-negative "
                                  "figure and no rate is restated (§4.5).",
    }
    path = os.path.join(HERE, "directioncost-tick64.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print(wt.VERSION)
    print("vocabulary:", len(tokens), "tokens;", out["vocabulary"]["class_sizes"])
    print("dump:", n_blocks, "blocks,", n_sites, "sites; sha", dump_sha[:16])
    print("void:", voids or "no defeat condition fired")
    print("counts:", counts, "classified:", classified)
    print(f"C1 band 5-20 %, observed {c1['observed_pct']} % "
          f"({counts['UPPER']}/{classified}) -> {'HELD' if c1['held'] else 'REFUTED'}"
          f"{' ' + (c1['refuted_direction'] or '')}")
    print(f"C2 -> {'HELD' if c2['held'] else 'REFUTED'}  all-UPPER papers: {all_upper}")
    print(f"C3 -> {'HELD' if c3['held'] else 'REFUTED'}  {c3['counts']}")
    print("multi-rel matches:", len(multi), "| at 110-char cap:", len(at_cap),
          "| R1 changes class:", len(differs), "| rel only after value:", len(rel_after))
    print("wrote", path)


if __name__ == "__main__":
    main()
