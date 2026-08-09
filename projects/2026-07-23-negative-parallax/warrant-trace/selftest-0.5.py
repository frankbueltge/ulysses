#!/usr/bin/env python3
"""Self-test for the 0.5 repair: the seven faults, and the seven ways of over-repairing them.

`faults-tick47.py` is the record of a defect: eight verbatim fragments from papers the
hand-reading of tick 47 found the sieve had misread, with the expectations describing 0.4's
FAULTY behaviour. That file goes red the moment the repair lands, and it is meant to — it
records a state, it does not gate anything.

This file is its inverse and its complement. Part A asserts that each of the seven faults is
gone. Part A is **not evidence**: the repair was designed against exactly these strings, so
passing it is construction, not discovery, and `../PREREGISTRATION-tick50.md` §0 says so.

Part B is the part that can fail honestly. Every one of these repairs widens something — a
gap, a boundary, a relation list — and a widened sieve buys sites and sells precision. Part B
is a set of fragments that must **not** become sites: a sentence boundary the gap must still
respect, an abbreviation it must not cross, a word the R-hat term must still refuse, a number
standing near a term with no criterion in sight. If part A passes and part B fails, the
instrument has stopped understating by starting to overstate, which is not a repair.

Neither part is the real test. That one is at tick 50 in the corpus: a hand-read sample of
the sites the repair NEWLY finds, whose precision is forecast in the pre-registration before
the count exists. A self-test on invented strings cannot tell you what a sieve does to a
literature.

Usage:  python3 selftest-0.5.py        (exit 0 = pass)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as wt                                      # noqa: E402

# ---------------------------------------------------------------- A: the faults are gone
# (fault, profile, verbatim fragment from a real paper, sites wanted, term-match wanted)
REPAIRED = [
    ("F1", "ruwe-1.4",
     "the Renormalised Unit Weight Error (RUWE) for this source is 34.676, "
     "far above the limit of > 1.4 for poor astrometric fits suggested by X", 1, True),
    ("F1", "ruwe-1.4",
     "the renormalized unit weighted errors (ruwe) for these stars amounted to 3.62 and "
     "2.51, values that are much greater than the cut-off of 1.4 suggested by X", 1, True),
    ("F2", "ruwe-1.4", "ruwe_1<1.4 and ruwe_2<1.4 .", 1, True),
    ("F3", "ruwe-1.4", "texttt ruwe \\textless 1.4 .", 1, True),
    ("F4", "rhat-1.1", "It follows that R \\ll \\phi \\circ \\P .", 0, False),
    ("F5", "iou-0.5", "average precision (AP), each at the 0.50 IoU threshold", 1, True),
    ("F6", "iou-0.5", "The mAP_50 metric represents the mean AP under IoU of 0.50", 1, True),
    ("F7", "iou-0.5", "mAP averaged over IoU thresholds from 0.50 to 0.95", 1, True),
]

# ---------------------------------------------------------- B: the repairs did not flood
# Each fragment names which repair could have swallowed it. These are the cases where a
# wider gap, a looser boundary or a longer relation list would produce a site that is not
# one. A failure here is the repair over-reaching, and it costs precision in the corpus.
CONTROLS = [
    ("F1 must still stop at a sentence", "ruwe-1.4",
     "We discuss the RUWE of each component below. The companion has a mass of 1.4 "
     "solar masses.", 0),
    ("F1 must not cross an abbreviation", "ruwe-1.4",
     "The RUWE column is described in the documentation, e.g. 1.4 is quoted widely "
     "there", 0),
    ("F1 must still stop at a semicolon", "ruwe-1.4",
     "we list the ruwe for every source; the orbital period is 1.4 days", 0),
    ("F2 must not match an embedding word", "ruwe-1.4",
     "the ruwex statistic was below 1.4 throughout", 0),
    ("F4 must still refuse ordinary English", "rhat-1.1",
     "It is somewhat surprising that R exceeds 1.1 in that regime", 0),
    ("F4 must still ACCEPT the LaTeX form", "rhat-1.1",
     "we required $\\hat{R} < 1.1$ for every parameter", 1),
    ("F5 must require a criterion noun", "iou-0.5",
     "Figure 3 plots the 0.50 IoU curves for all three backbones", 0),
    ("F6 must not turn a fraction into a threshold", "iou-0.5",
     "the mean overlap of the tracker output is reported per sequence", 0),
]


def run(cases, kind):
    bad = 0
    print(f"\n{kind}")
    for label, prof_id, text, want_sites, *rest in cases:
        prof = wt.Profile.load(os.path.join(HERE, "profiles", prof_id + ".json"))
        t = wt.normalise(text)
        got_sites = len(wt.sites(t, prof))
        ok = got_sites == want_sites
        if rest:
            got_term = bool(prof.term_re.search(t))
            ok = ok and got_term == rest[0]
            extra = f" term={got_term} (want {rest[0]})"
        else:
            extra = ""
        bad += not ok
        print(f"  {label:34s} {prof_id:10s} sites={got_sites} (want {want_sites}){extra}"
              f"  {'ok' if ok else 'FAIL'}")
        if not ok:
            print(f"      {text[:100]}")
    return bad


def main():
    print(wt.VERSION)
    bad = run(REPAIRED, "A — the seven faults are repaired "
                        "(designed against these strings; not evidence)")
    bad += run(CONTROLS, "B — and the repairs did not flood "
                         "(the part that can fail honestly)")
    if bad:
        print(f"\nFAIL — {bad} case(s) wrong")
        return 1
    print("\npass — the seven pinned faults are gone and the eight controls are still "
          "refused. What this does NOT show: what the repair does to a literature. That "
          "is measured in the corpus at tick 50, against a forecast written first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
