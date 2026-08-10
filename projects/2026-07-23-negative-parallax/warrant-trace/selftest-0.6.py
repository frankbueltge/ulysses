#!/usr/bin/env python3
"""Self-test for the 0.6 repair: the eight repaired classes, and the ways of over-repairing.

Same shape as `selftest-0.5.py`, and for the same reason. Part A asserts that each repaired
fault class is gone; part A is **not evidence**, because the repair was designed against
these strings — `../PREREGISTRATION-tick55.md` §1 says so before the fact.

Part B is the part that can fail honestly. Every one of 0.6's repairs widens something: the
gap now steps over a citation marker and over a single newline, the relation list gained four
macros, the step from a relation to its number admits an article and a table-cell separator,
and one letter of the RUWE term became optional. Each widening has a control here that must
NOT become a site: the sentence boundary the gap must still respect, the paragraph break a
newline must still be, the `\\sim` that is not a comparison, the word an article must not
reach past.

Part C is new at 0.6 and belongs to the footnote repair. E3 moves a footnote out of its host
sentence, and the first draft of it deleted the body — which would have bought sites at the
host site and silently lost any threshold stated inside a footnote. The two cases here hold
the repair to both halves.

The real test is not here. It is in the corpus at tick 55: a hand-read sample of the sites
0.6 finds and 0.5 does not, drawn by a seed fixed before any window was read.

Usage:  python3 selftest-0.6.py        (exit 0 = pass)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as wt                                      # noqa: E402

# ---------------------------------------------------- A: the repaired classes are repaired
# (class, profile, fragment in the form the instrument reads, sites wanted)
REPAIRED = [
    ("G1 \\geqslant", "ruwe-1.4", r"the condition ruwe\geqslant 1.4 was applied", 1),
    ("G1 \\leqslant", "ruwe-1.4", r"one quality condition is ruwe \leqslant 1.4", 1),
    ("G2 \\gtrsim", "ruwe-1.4", r"stars with large RUWE \gtrsim 3 are excluded", 1),
    ("G2 \\lesssim", "ruwe-1.4", r"we keep sources with ruwe \lesssim 1.4 only", 1),
    ("G3 footnote", "ruwe-1.4",
     r"(renormalized unit weight error, RUWE,\footnote{https://www.example.org/a.b/c} $>$ 1.4)", 1),
    ("G4 table cells", "ruwe-1.4", r"& RUWE & < & \phantom{-} 5 \\", 1),
    ("G6 an article", "ruwe-1.4",
     "the renormalized unit weight error is 2.4 and this is greater than the 1.4 level", 1),
    ("G7 cite marker", "ruwe-1.4",
     r"the renormalized unit weight error \citep[RUWE,][]{a2020,b2020} $\leq 1.4$ .", 1),
    ("G8 a line break", "ruwe-1.4",
     "both stars have a RUWE internal Gaia\nsingle star solution quality index <1.2 ,", 1),
    ("G9 the misspelling", "ruwe-1.4",
     r"remove any for which the renomalised unit weight error \citep{x} is greater than 1.2.", 1),
    ("G9 the spelling", "ruwe-1.4",
     "remove any for which the renormalised unit weight error is greater than 1.2.", 1),
]

# ------------------------------------------------------ B: and the repairs did not flood
CONTROLS = [
    ("E2 must still stop at a full stop", "ruwe-1.4",
     "we discuss the RUWE of each component \\citep{x} . The companion period is 1.4 days", 0),
    ("E2 must still stop at a semicolon", "ruwe-1.4",
     "we list the ruwe \\citep{x} ; the orbital period is 1.4 days", 0),
    ("E4 must still refuse a paragraph break", "ruwe-1.4",
     "we list the ruwe of every source\n\nThe orbital period is 1.4 days", 0),
    ("E4 must still refuse it with a blank-ish line", "ruwe-1.4",
     "we list the ruwe of every source\n   \nThe orbital period is 1.4 days", 0),
    ("E1 must not make \\sim a comparison", "ruwe-1.4",
     r"the RUWE of this source is \sim 1.4 for the whole sample", 0),
    ("P-A must admit at most ONE article", "ruwe-1.4",
     "the RUWE was below the reported 1.4 solar-mass companion", 0),
    ("P-B must not admit an unrelated word", "ruwe-1.4",
     "the renormalised unit weight estimator was below 1.4 throughout", 0),
    ("the 0.5 controls still hold: sentence", "ruwe-1.4",
     "We discuss the RUWE of each component below. The companion has a mass of 1.4 "
     "solar masses.", 0),
    ("the 0.5 controls still hold: e.g.", "ruwe-1.4",
     "The RUWE column is described in the documentation, e.g. 1.4 is quoted widely there", 0),
    ("the 0.5 controls still hold: embedding", "ruwe-1.4",
     "the ruwex statistic was below 1.4 throughout", 0),
    ("the 0.5 controls still hold: English R", "rhat-1.1",
     "It is somewhat surprising that R exceeds 1.1 in that regime", 0),
    ("the 0.5 controls still hold: IoU curve", "iou-0.5",
     "Figure 3 plots the 0.50 IoU curves for all three backbones", 0),
]

# ------------------------------------------- C: the footnote is moved out, and not deleted
FOOTNOTE = [
    ("a threshold INSIDE a footnote survives the move", "ruwe-1.4",
     r"the astrometry is good\footnote{We keep only sources with RUWE $<$ 1.4 .} for all", 1),
    ("and the host sentence is no longer split by it", "ruwe-1.4",
     r"the RUWE\footnote{RUWE is the renormalised unit weight error (for astrometry) "
     r"discussed in \citet{x} .} < 2.4 ; the second cut", 1),
]


# ------------------------------------------------- D: a defect this file found, unrepaired
# Written as a control for P-A, failed, and turned out to be about neither P-A nor 0.6: the
# string below is a site under 0.5 as well. A bare `of` has been in three profiles' relation
# lists since tick 21 and was added to the fourth at 0.5 to bring it into line — so `the
# companion mass of 1.4 solar masses` reaches the number through an ordinary English
# genitive, with no comparison anywhere in the sentence.
#
# It is left RED here on purpose, in the form `faults-tick47.py` established: a record of a
# defect is not a gate. It is not repaired at this tick because no instance of it has been
# pinned in a paper — every fault 0.6 repairs was found in the corpus by hand-reading, and
# repairing an invented string would reverse that order. What it costs is stated rather than
# guessed: the direction is OVERSTATEMENT of sites, and a false site carries no deriving
# document, so it lowers the fraction this line's shipped reading reports — the direction
# that flatters the claim. How often the shape occurs is counted at tick 55 by
# `of-relation-audit-tick55.py`, over the sites the corpus actually contains.
KNOWN_RED = [
    ("N1 `of` reaches a number through a genitive", "ruwe-1.4",
     "the RUWE is discussed below the companion mass of 1.4 solar masses", 1),
]


def run(cases, kind):
    bad = 0
    print(f"\n{kind}")
    for label, prof_id, text, want in cases:
        prof = wt.Profile.load(os.path.join(HERE, "profiles", prof_id + ".json"))
        got = len(wt.sites(wt.normalise(text), prof))
        ok = got == want
        bad += not ok
        print(f"  {label:44s} {prof_id:10s} sites={got} (want {want})  "
              f"{'ok' if ok else 'FAIL'}")
        if not ok:
            print(f"      {text[:110]!r}")
    return bad


def main():
    print(wt.VERSION)
    bad = run(REPAIRED, "A — the eight repaired classes "
                        "(designed against these strings; not evidence)")
    bad += run(CONTROLS, "B — and the repairs did not flood "
                         "(the part that can fail honestly)")
    bad += run(FOOTNOTE, "C — the footnote is moved out of its sentence, not deleted")
    run(KNOWN_RED, "D — a defect this file found and 0.6 does NOT repair "
                   "(recorded, not gated; 0.5 does the same)")
    if bad:
        print(f"\nFAIL — {bad} case(s) wrong")
        return 1
    print("\npass. What this does NOT show: what the repair does to a literature. That is "
          "measured in the corpus at tick 55, over three frames, against forecasts written "
          "before the corpus was read.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
