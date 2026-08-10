#!/usr/bin/env python3
"""gapstates-tick54 — the states of the sketch, computed by the instrument itself.

The work this feeds is about one thing: the gap class of the sieve that read 590 papers
for this line. In `warrant_trace.py` it is a single expression —

    GAP = r"(?:[^.;:\\n]|\\.(?=\\d)){0,100}?"

— and it decides whether a threshold a paper states exists for the reader. Four characters
and one bound: newline, colon, semicolon, period (unless a digit follows), and 100
characters. Tick 53 read the whole candidate class by hand, found thirteen papers stating a
threshold the sieve had filed as stating none, and pinned ten fault classes to verbatim
fragments in `../warrant-trace/faults-tick53.py`, four of them with a control in which the
single defect is removed by hand.

This script does NOT reimplement the sieve, and the sketch it feeds does not either. It
imports the fragments from that landed fixture file (so no string is retyped here and any
divergence is impossible), runs the SHIPPED instrument over each state, and writes what the
instrument answered. Every verdict the visitor sees was produced by the committed sieve on
this machine, not by a browser reimplementation of it.

Three of the four panels are the fixture's own pair — the fragment as fetched, and the
fixture's own control. The fourth panel (the newline) is a **sweep**: the control string
with exactly one space replaced by a newline, once per space position. Nothing is added or
removed; the word sequence is the fixture's, and only which whitespace character sits in one
position changes. That is the whole claim of the panel — where an author's editor wrapped
the line decides whether the number exists — so the sweep is the measurement, not a
decoration of it.

Outputs `states-tick54.json` and, from `sketch-v1.template.html`, the self-contained
`sketch-v1.html`. Both carry the sha256 of the instrument and the profile that judged.
"""
import hashlib
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.normpath(os.path.join(HERE, "..", "warrant-trace"))
sys.path.insert(0, WT)
from warrant_trace import Profile, normalise, sites  # noqa: E402


def load_fixture():
    """Import the landed fault fixture by path — its filename is not an identifier."""
    path = os.path.join(WT, "faults-tick53.py")
    spec = importlib.util.spec_from_file_location("faults_tick53", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, path


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def verdict(frag, prof):
    """What the shipped instrument answers on this exact string."""
    return [s["value"] for s in sites(normalise(frag), prof)]


def gap_chars(frag, prof):
    """Characters between the end of the term match and the relation that follows it.

    Derived, not authoritative: it locates the profile's own `term` and `rel` patterns in the
    normalised text and reports the distance the GAP would have to cross. Returns None when
    either pattern is absent — the panels state it as a measured distance, never as a cause.
    """
    text = normalise(frag)
    t = prof.term_re.search(text)
    if not t:
        return None
    r = re.search(prof.raw.get("rel", ""), text[t.end():])
    return None if not r else r.start()


def main():
    fx, fxpath = load_fixture()
    ruwe, rhat = fx.PROF, fx.PROF_MCMC

    def case(fault_prefix, cases):
        for row in cases:
            if row[0].startswith(fault_prefix):
                return row
        raise KeyError(fault_prefix)

    # --- the switch panels ---------------------------------------------------------------
    #
    # Each state is labelled with what it IS, because two of the fixture's controls are not
    # what a visitor would assume from the word "control":
    #
    #   faithful  — the paper's own words; only whitespace, or a mark the READER added, moved
    #   edited    — shortened or rewritten by hand; not a sentence any paper contains
    #
    # And G9's control turned out not to isolate one defect at all. Building this panel is
    # what found it; the audit is in `fixture_audit` below and the panel now shows the two
    # single-change states the fixture never ran.

    G9_CASE = case("G9", fx.CASES)[3]
    G9_MARKER = " <<CITE:gaiaedr3_astrom>>"

    def st(label, text, prof, faithful, caveat=None):
        found = verdict(text, prof)
        return {"label": label, "text": text, "found": found, "sees": bool(found),
                "faithful": faithful, "caveat": caveat,
                "gap_chars": gap_chars(text, prof)}

    panels = []

    fault, aid, _, frag, want = case("G7", fx.CASES)
    _, _, _, cfrag, _ = case("G7", [(c[0], c[1], None, c[2], c[3]) for c in fx.CONTROLS])
    panels.append({
        "id": "G7", "kind": "switch", "title": "the mark the reader makes itself",
        "note": "The instrument rewrites every citation in a source as `<<CITE:…>>`. The colon "
                "in its own marker is one of the four characters its gap forbids — so the "
                "reader is blinded by the mark it made. Nothing here is the paper's fault: "
                "delete the reader's own mark and the printed number returns.",
        "knob": "the reader's citation marker", "arxiv": aid, "fixture_fault": fault,
        "profile": "ruwe-1.4", "stated_value": want,
        "states": [st("present", frag, ruwe, True),
                   st("deleted", cfrag, ruwe, True,
                      "the deleted mark is the reader's, not the paper's")]})

    fault, aid, _, frag, want = case("G9", fx.CASES)
    _, _, _, cfrag, _ = case("G9", [(c[0], c[1], None, c[2], c[3]) for c in fx.CONTROLS])
    panels.append({
        "id": "G9", "kind": "switch", "title": "two accidents, and I had named one",
        "note": "The paper writes *renomalised*. The reader's English is correct and the "
                "paper's is not, and the paper wins. But the same sentence also carries the "
                "reader's own citation marker — and correcting only the spelling, or removing "
                "only the marker, leaves the number invisible either way. Two independent "
                "accidents, each sufficient on its own. The tick-53 record calls this paper "
                "the spelling fault and says so as a correction of an earlier attribution; "
                "it is both, and this panel is where that was found.",
        "knob": "which accident is removed", "arxiv": aid, "fixture_fault": fault,
        "profile": "ruwe-1.4", "stated_value": want,
        "states": [st("as printed", frag, ruwe, True),
                   st("spelling corrected only", frag.replace("renomalised", "renormalised"),
                      ruwe, True),
                   st("marker deleted only", frag.replace(G9_MARKER, ""), ruwe, True),
                   st("both, sentence intact",
                      frag.replace("renomalised", "renormalised").replace(G9_MARKER, ""),
                      ruwe, True),
                   st("both, and shortened (the fixture's control)", cfrag, ruwe, False,
                      "hand-shortened as well — not a sentence the paper contains, and the "
                      "state beside it shows the shortening was never needed")]})

    fault, aid, _, frag, want = case("G10", fx.MCMC_CASES)
    _, _, _, cfrag, _ = case("G10", [(c[0], c[1], None, c[2], c[3]) for c in fx.MCMC_CONTROLS])
    panels.append({
        "id": "G10", "kind": "switch", "title": "one clause too far",
        "note": "Nothing is malformed here. The statistic and its threshold stand in one "
                "sentence of ordinary prose, and more than 100 characters stand between them "
                "— one clause more than the bound the reader was given. The second state is "
                "the same claim written short by hand, to show that only the distance is "
                "doing the work.",
        "knob": "the distance between name and rule", "arxiv": aid, "fixture_fault": fault,
        "profile": "rhat-1.1", "stated_value": want,
        "states": [st("as written in the paper", frag, rhat, True),
                   st("the same claim, written short", cfrag, rhat, False,
                      "written by hand for the control — not the paper's sentence")]})

    # the audit that building the panels produced
    fixture_audit = {
        "claim_in_tick_53": "each fault class carries a control where the single defect is "
                            "removed by hand, so the claim 'the fault is HERE' is tested",
        "holds_for": ["G7 (single deletion)", "G8 (whitespace only)"],
        "fails_for": {
            "G9": {
                "what_the_control_does": "corrects the spelling AND deletes the citation "
                                         "marker AND truncates the sentence",
                "measured": {
                    "spelling corrected, marker kept": verdict(
                        G9_CASE.replace("renomalised", "renormalised"), ruwe),
                    "marker deleted, spelling kept": verdict(
                        G9_CASE.replace(G9_MARKER, ""), ruwe),
                    "both, sentence otherwise intact": verdict(
                        G9_CASE.replace("renomalised", "renormalised")
                               .replace(G9_MARKER, ""), ruwe),
                },
                "consequence": "neither single change restores the number: the paper is "
                               "blinded twice over, and tick 53's hand-correction of this "
                               "attribution ('it is the spelling, not the citation fault') "
                               "excluded a cause that is also true",
            },
            "G10": {
                "what_the_control_does": "replaces the paper's sentence with a shorter one "
                                         "written by hand",
                "consequence": "legitimate as a demonstration that distance is the operative "
                               "quantity, but it is not the paper's text and the sketch says so",
            },
        },
        "not_repaired_here": "faults-tick53.py is landed and is left byte-identical; its "
                             "sha256 is recorded above. This audit is the tick-54 record.",
    }

    # --- the sweep: one newline, walked through the sentence, once per space position ---
    fault, aid, order, frag, want = case("G8", fx.CASES)
    _, _, _, cfrag, _ = case("G8 control", [(c[0], c[1], None, c[2], c[3]) for c in fx.CONTROLS])
    positions = [i for i, ch in enumerate(cfrag) if ch == " "]
    sweep = []
    for i in positions:
        text = cfrag[:i] + "\n" + cfrag[i + 1:]
        found = verdict(text, ruwe)
        sweep.append({"pos": i, "found": found, "sees": bool(found),
                      "before": cfrag[:i], "after": cfrag[i + 1:]})
    blind = [s["pos"] for s in sweep if not s["sees"]]
    # Which sweep position is the paper's own? The fetched fragment breaks the line as
    # `"Gaia \nsingle"` — a space AND a newline where the control has one space — so it is
    # not literally a member of the sweep. Deleting the newline must return the control
    # exactly; the break then sits at the space that precedes it. Asserted, not assumed.
    fx_pos = None
    nl = frag.find("\n")
    if nl >= 0 and frag[:nl] + frag[nl + 1:] == cfrag and cfrag[nl - 1] == " ":
        fx_pos = nl - 1
        assert fx_pos in blind, "the paper's own break does not blind the instrument"
    panels.append({
        "id": "G8", "kind": "sweep", "title": "where the line happened to wrap",
        "note": "One space becomes a newline, and nothing else changes. The gap class "
                "excludes `\\n`, so a line break the author never chose — an editor's wrap, "
                "a formatting convention — decides whether the number exists for the reader.",
        "knob": "the position of the line break", "arxiv": aid, "fixture_fault": fault,
        "profile": "ruwe-1.4", "stated_value": want, "base": cfrag,
        "positions": positions, "blind_positions": blind, "fixture_position": fx_pos,
        "states": sweep,
    })

    rep = {
        "tick": 54,
        "generated_by": "gapstates-tick54.py",
        "gap_expression": r"(?:[^.;:\n]|\.(?=\d)){0,100}?",
        "instrument": {
            "warrant_trace.py": sha(os.path.join(WT, "warrant_trace.py")),
            "profiles/ruwe-1.4.json": sha(os.path.join(WT, "profiles/ruwe-1.4.json")),
            "profiles/rhat-1.1.json": sha(os.path.join(WT, "profiles/rhat-1.1.json")),
            "faults-tick53.py": sha(fxpath),
        },
        "provenance": "Every fragment is imported from faults-tick53.py, where it is quoted "
                      "from the e-print fetched on 2026-08-10 and recorded with its arXiv id "
                      "and the tick-53 read order. No string is retyped in this file; the two "
                      "single-change variants of G9 are produced from the imported fragment by "
                      "one `str.replace` each, both visible above.",
        "fixture_audit": fixture_audit,
        "panels": panels,
    }
    out = os.path.join(HERE, "states-tick54.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)

    tmpl = os.path.join(HERE, "sketch-v1.template.html")
    if os.path.exists(tmpl):
        with open(tmpl, encoding="utf-8") as fh:
            html = fh.read()
        html = html.replace("/*STATES*/", json.dumps(rep, ensure_ascii=False))
        with open(os.path.join(HERE, "sketch-v1.html"), "w", encoding="utf-8") as fh:
            fh.write(html)

    for p in panels:
        print(f"\n{p['id']}  {p['title']}  (arXiv:{p['arxiv']}, states {p['stated_value']})")
        if p["kind"] == "switch":
            for s in p["states"]:
                print(f"      {s['label']:<44} -> {s['found'] or 'nothing'}"
                      f"{'' if s['faithful'] else '   [hand-edited]'}")
        else:
            print(f"      {len(p['positions'])} break positions, "
                  f"{len(p['blind_positions'])} of them blind the reader"
                  f"; the paper's own break is at {p['fixture_position']}")
    print(f"\nwritten: {os.path.basename(out)}")


if __name__ == "__main__":
    main()
