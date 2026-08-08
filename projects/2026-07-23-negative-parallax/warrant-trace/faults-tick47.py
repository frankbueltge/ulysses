#!/usr/bin/env python3
"""faults-tick47 — the six faults the hand-reading found, each pinned to a string.

The hand-reading of tick 47 says the instrument missed thresholds that are plainly stated and
counted a paper that never mentions the statistic. This file does not assert that; it
reproduces it. Every case is a verbatim fragment from a sampled paper, run through the
instrument as it stands today (0.4). The expectations below describe the CURRENT, FAULTY
behaviour: the file is red once the repair lands, and that is what it is for — 0.5's selftest
will be this file with the expectations inverted.

    F1 engine   an intervening decimal number blocks the site window: the gap class is
                [^.;:\\n] and `34.676,` contains a period.
    F2 profile  a subscripted identifier is not a term match: \\bruwe\\b fails before `_`.
    F3 engine   LaTeX relations \\textless / \\textgreater are not normalised to < / >.
    F4 profile  the R-hat term has no left boundary, so `that R` matches `hat R`.
    F5 profile  a value standing BEFORE the term (`the 0.50 IoU threshold`) is a site only
                for < and >, not for prose.
    F6 profile  the CV relation list has no bare `of`, so `IoU of 0.50` is not a site —
                and that site carries a citation.
    F7 profile  a sweep (`IoU thresholds from 0.50 to 0.95`) states threshold values that no
                relation in the list reaches.

Usage: faults-tick47.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as wt                                      # noqa: E402

CASES = [
    # (fault, profile, verbatim fragment, expected sites today, expected term-match today)
    ("F1", "ruwe-1.4",
     "the Renormalised Unit Weight Error (RUWE) for this source is 34.676, "
     "far above the limit of > 1.4 for poor astrometric fits suggested by X", 0, True),
    ("F1", "ruwe-1.4",
     "the renormalized unit weighted errors (ruwe) for these stars amounted to 3.62 and "
     "2.51, values that are much greater than the cut-off of 1.4 suggested by X", 0, True),
    ("F2", "ruwe-1.4", "ruwe_1<1.4 and ruwe_2<1.4 .", 0, False),
    ("F3", "ruwe-1.4", "texttt ruwe \\textless 1.4 .", 0, True),
    ("F4", "rhat-1.1", "It follows that R \\ll \\phi \\circ \\P .", 0, True),
    ("F5", "iou-0.5", "average precision (AP), each at the 0.50 IoU threshold", 0, True),
    ("F6", "iou-0.5", "The mAP_50 metric represents the mean AP under IoU of 0.50", 0, True),
    ("F7", "iou-0.5", "mAP averaged over IoU thresholds from 0.50 to 0.95", 0, True),
]


def main():
    print(wt.VERSION)
    bad = 0
    for fault, prof_id, text, want_sites, want_term in CASES:
        prof = wt.Profile.load(os.path.join(HERE, "profiles", prof_id + ".json"))
        t = wt.normalise(text)
        got_sites = len(wt.sites(t, prof))
        got_term = bool(prof.term_re.search(t))
        ok = (got_sites == want_sites) and (got_term == want_term)
        bad += not ok
        print(f"{fault} {prof_id:10s} sites={got_sites} (expect {want_sites})  "
              f"term={got_term} (expect {want_term})  {'reproduced' if ok else 'NOT REPRODUCED'}")
        print(f"     {text[:96]}")
    print(f"\n{len(CASES) - bad}/{len(CASES)} faults reproduced against {wt.VERSION}")
    # exit 0 either way: this file records a state, it does not gate anything
    return 0


if __name__ == "__main__":
    sys.exit(main())
