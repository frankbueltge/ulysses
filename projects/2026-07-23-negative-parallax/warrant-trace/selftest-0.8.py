#!/usr/bin/env python3
"""Self-test for the 0.8 repair — the two faults 0.7 made, and the fourteen it must not undo.

0.8 repairs nothing the corpus complained about. It repairs what the previous repair broke,
which is a narrower job and a stricter one: every fixture in part A was RED in
`selftest-0.7.py` part D, pinned to a paper by the tick-58 hand sample, and every fixture in
part B is a case 0.7 removed correctly and 0.8 must leave removed.

That balance is the whole test. E8 and E9 are both escapes from a rule that is otherwise
right — E6's "the sign belongs to the token on its left" and E7's "a table row is not the
sentence of the row above". An escape written one notch too wide gives 0.7's whole repair
back, and the honest place to find that out is here, before the re-measure, not after it.

Part A: the two 0.7 faults, verbatim from `selftest-0.7.py` part D and from the matched
strings `remeasure-tick58-removed.jsonl` landed for them, now wanted as sites.
Part B: the removals that must survive — every other shape among the 108 sites 0.7 removed
that comes near E8 or E9, plus the parts A and C of `selftest-0.7.py` unchanged.
Part C: the 0.6 and 0.7 controls, re-run whole, because a repair to the engine is a repair to
every literature at once.
Part D: what 0.8 still does not repair, carried forward and added to.

The real test is not here. It is the tick-59 re-measure over three frames against forecasts
fixed in `../PREREGISTRATION-tick59.md` before the corpus was read, and the hand-reading of
every site 0.8 adds.

Usage:  python3 selftest-0.8.py        (exit 0 = pass)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as wt                                      # noqa: E402

# ------------------------------------------------- A: the two faults 0.7 made, now repaired
REPAIRED = [
    ("N4 the subscripted statistic (2506.22399)", "ruwe-1.4",
     r"we keep sources with RUWE _ \mathrm c < 1.4 in the final sample", 1),
    ("N4 the same paper, uwe profile", "uwe-1.25",
     r"we keep sources with RUWE _ \mathrm c < 1.4 in the final sample", 1),
    ("N4 the matched string as landed (2608.05356v1)", "iou-0.5",
     r"overlap and displacement bounds, namely mathrm IoU _ 3 mathrm D >0.12", 1),
    ("N4 the same, at the second value", "iou-0.5", r"IoU _ 3 mathrm D >0.20", 1),
    ("N4 the subscript written without spaces", "ruwe-1.4",
     r"sources with RUWE_c < 1.4 are kept", 1),
    ("N5 the column head and its cell (2604.20395v2)", "iou-0.5",
     r"Recall @ IoU\\ > 0.50 & 54.3", 1),
    ("N5 with cell separators after the break", "iou-0.5",
     r"Recall @ IoU \\ & > & 0.50 & 54.3", 1),
]

# --------------------------------------- B: and the escapes did not give back 0.7's removals
# Every string here is a matched string 0.7 removed, copied from
# `remeasure-tick58-removed.jsonl`, chosen because it comes near one of the two escapes: a
# subscript that is not the statistic's, or a row break followed by something other than a
# sign. If an escape is one notch too wide, it shows up in this list first.
#
# The wanted number in every row is **what 0.7 itself returns on that string**, run and read
# off rather than reasoned out — so the assertion here is equality with the landed version,
# and it cannot be miscalibrated by what I expect the string to do. That mattered twice while
# this file was being written. One row is `RUWE … R \\ % RUWE=1.2` (2207.02925), where I wrote
# `0` because 0.7 removed the long match: 0.7 returns `1`, because the second and shorter
# `RUWE=1.2` is a site of its own, and `remeasure-tick58-added.jsonl` shows exactly that site
# arriving on the same tick that removed the long one. It is the same shape as N6 below, found
# in a second paper. The other was a string I INVENTED to test E8's width bound, which is
# against this line's own rule for fixtures and tested nothing — E6 declines that string on the
# width bound long before E8 is reached. It is gone from this list; what replaces it is part E,
# which asserts against the rule itself rather than pretending to be a paper.
KEPT_REMOVED = [
    ("E8 not the statistic's subscript: a rate variable (2605.20436v2)", "iou-0.5",
     r"mIoU (0.6086) is achieved at \lambda_ \text cons =0.1", 0),
    ("E8 not the statistic's subscript: a maximum index (2607.21847v1)", "rhat-1.1",
     r"hat R _N( pi ) - R( pi )| < 3C_1 \eta + \max_ j=1", 0),
    ("E8 not the statistic's subscript: a run name (2409.16992)", "ruwe-1.4",
     r"RUWE_normal_mass=100_mjup_sma=1", 0),
    ("E8 not the statistic's subscript: a moved glossary key (2409.16993)", "uwe-1.25",
     r"ruwe / varpi \quad (\text M _ rm J ),\\ \text \glsxtrshort sma _ rm min = 2.1", 0),
    ("E9 a row break before a word stays a stop (2607.00357v1)", "iou-0.5",
     r"mIoU ( \uparrow ) & \multicolumn 4 c F1-score ( \uparrow ) \\ Algorithms & N =1", 0),
    ("E9 a row break before a comment stays a stop; the site is the SHORT match (2207.02925)",
     "ruwe-1.4",
     r"RUWE 0.8 plx 0.76 00374 - 3904 & WHI 1 & 0\farcs3 Sp 1987 & 2021, R \\ % RUWE=1.2", 1),
    ("E9 a row break before \\hline stays a stop (2301.03777)", "ruwe-1.4",
     r"RUWE & sigma _ disp & \alpha \tablenotemark a & a & b & c \\ \hline W1 & 1052 & <1.4",
     0),
    ("E9 a row break before a table header stays a stop (2102.13654)", "ruwe-1.4",
     r"RUWE\\ & (\arcsec) & (mag) & & (mag) & (%) & \\ \hline Abell 31 & 0.26 & >6.8", 0),
    ("E9 a row break before a cell of prose stays a stop (2304.07322)", "ruwe-1.4",
     r"RUWE> & <B_ P > \\ selection & of binaries & CMD cut & (\Delta V/ sigma _ \Delta V )"
     r">1.5", 0),
    ("E9 a row break before a designation stays a stop (2507.13783)", "ruwe-1.4",
     r"RUWE &Designation \\ \hline \hline GJ 625 & 126 & 3.3 & 80 ± 8 & 0.015( < 0.036", 0),
    ("E7 the formula stop is untouched (2607.01708v1)", "iou-0.5",
     r"mIoU = \frac 1 N \sum_ i=1", 0),
    ("E6 the plot option is untouched (2604.19609v1)", "iou-0.5",
     "ylabel= mIoU (%) , xmode=log, log basis x=10", 0),
    ("E6 the confidence threshold is untouched (2603.16241v1)", "iou-0.5",
     "we tuned the IoU, we selected conf=0.5 for all runs", 0),
    ("E6 the summation index is untouched (2607.15041v1)", "iou-0.5",
     r"IoU^ rank _i \sum_ i=1", 0),
    ("E6 the overlap ratio named r is untouched (2603.12759v1)", "iou-0.5",
     "we require an overlap ratio to r=0.5 between viewpoints", 0),
    ("P-C the reported mean is untouched (2604.18549v1)", "iou-0.5",
     "our model reaches a mIoU of 48.3", 0),
    ("P-C the subscripted reported mean is untouched (2606.12826v1)", "iou-0.5",
     r"mIoU _ mathrm ins of 70.25%", 0),
]

# ------------------------------------------------------- C: the 0.6 and 0.7 controls, whole
CONTROLS = [
    ("E6 keeps the statistic's own comparison", "ruwe-1.4",
     "we keep sources with RUWE < 1.4 throughout", 1),
    ("E6 keeps a relation word before the sign", "ruwe-1.4",
     "the RUWE for this source is 34.676, far above the limit of > 1.4", 1),
    ("E6 keeps a noun standing for the value", "ruwe-1.4",
     "we apply the RUWE cut < 1.4 to the whole sample", 1),
    ("E6 keeps a threshold written with a symbol", "iou-0.5",
     r"we evaluate at IoU thresholds \tau=0.50 and 0.75", 1),
    ("E6 keeps a spaced two-letter word (2101.10206)", "ruwe-1.4",
     "sources are selected with RUWE as < 1.4 for the final sample", 1),
    ("E6 keeps a spaced word before the sign", "ruwe-1.4",
     "a RUWE internal Gaia single star solution quality index <1.2 ,", 1),
    ("E6 keeps the table-cell site of 0.6", "ruwe-1.4",
     r"& RUWE & < & \phantom{-} 5 \\", 1),
    ("E7 keeps a site whose row break comes after it", "ruwe-1.4",
     r"& RUWE & < & 1.4 \\ next row", 1),
    ("E7 does not block an ordinary sentence", "iou-0.5",
     "a detection is correct when the IoU exceeds 0.5 for that class", 1),
    ("P-C keeps a mean that names a threshold", "iou-0.5",
     "We report mean IoU (mIoU) and instance-level average precision (AP) at IoU "
     "thresholds of 25%, 50%, and 75%", 1),
    ("P-C leaves the other literatures alone", "rhat-1.1",
     "chains were run until the mean R-hat < 1.1 for every parameter", 1),
    ("the 0.6 controls still hold: sentence", "ruwe-1.4",
     "We discuss the RUWE of each component below. The companion has a mass of 1.4 "
     "solar masses.", 0),
    ("the 0.6 controls still hold: paragraph break", "ruwe-1.4",
     "we list the ruwe of every source\n\nThe orbital period is 1.4 days", 0),
    ("the 0.6 controls still hold: \\sim", "ruwe-1.4",
     r"the RUWE of this source is \sim 1.4 for the whole sample", 0),
    ("the 0.6 controls still hold: one article", "ruwe-1.4",
     "the RUWE was below the reported 1.4 solar-mass companion", 0),
    ("the 0.6 controls still hold: footnote moved", "ruwe-1.4",
     r"the astrometry is good\footnote{We keep only sources with RUWE $<$ 1.4 .} for all", 1),
    ("the 0.6 controls still hold: IoU curve", "iou-0.5",
     "Figure 3 plots the 0.50 IoU curves for all three backbones", 0),
    ("P-A the apposition (2607.02371v1)", "iou-0.5",
     "we report mAP at IoU 0.50 for every split", 1),
    ("P-A in a table header", "iou-0.5", "Method & AP at IoU 0.3 & AP at IoU 0.5", 1),
    ("P-A must not fire on a mean", "iou-0.5", "the model lands at mIoU 82.7 on this set", 0),
    ("P-A must not reach past a word", "iou-0.5",
     "measured at the IoU curve computed for 0.5 seconds", 0),
]


# --------------------------------------- D: what 0.8 does NOT repair, recorded and not gated
# N1, N2 and N3 are carried forward unchanged from 0.7: the genitive `of`, the reported IoU
# read as a rule, and the criterion absorbed into a metric name. N4 and N5 leave this list —
# they are parts A of this file now.
#
# N6 is new, and it is not a fault of the sieve but a fault of this line's own record. Tick 58
# named `2604.17920v1` as a second instance of N5 — a threshold lost when E7's boundary fell
# across `\end{equation}`. It was not lost. `remeasure-tick58-added.jsonl`, landed the same
# hour, shows the site re-found on its own terms as `IoU thresholds from 0.5`; the two records
# are the same site under two match keys, because the key is the value plus the window's tail
# and the shorter match moved the tail. So N5 has one instance and not two, tick 58's count of
# six removed matches in two shapes is FIVE in two shapes, and the correction is entered here
# and in the trace rather than by editing what was landed.
KNOWN_RED = [
    ("N1 `of` reaches a number through a genitive", "ruwe-1.4",
     "the RUWE is discussed below the companion mass of 1.4 solar masses", 1),
    ("N2 a reported IoU read as a rule (2608.04423v1)", "iou-0.5",
     "the predicted mask reaches an IoU of 0.910 against the annotation", 1),
    ("N3 the criterion absorbed into a name (2604.01907v2)", "iou-0.5",
     "we report AP_25 and AP_50 for every method", 0),
    ("N6 (record, not sieve) the site tick 58 called lost was re-found", "iou-0.5",
     r"IoU =t , \end equation where T is the set of IoU thresholds from 0.5", 1),
]


# ------------------------------------- E: the escape's own shape, asserted against the rule
# Not fixtures and not papers. `own_subscript` decides whether the tokens between a sign and
# the statistic's name are a subscript OF that name, and its two bounds — the run must begin
# with `_`, and every item in it must be a font macro, a digit or an identifier no wider than
# E6's own symbol bound — are the whole difference between repairing N4 and handing back the
# repair 0.7 made. Asserting them here, on heads rather than sentences, keeps part B free of
# strings I made up.
SHAPE = [
    ("the pinned head, ruwe", "ruwe-1.4", r"RUWE _ mathrm c", True),
    ("the pinned head, cv", "iou-0.5", r"mathrm IoU _ 3 mathrm D", True),
    ("attached, no spaces", "ruwe-1.4", "RUWE_c", True),
    ("a nested font macro", "iou-0.5", r"IoU _ mathrm 3 textbf D", True),
    ("no underscore at all is not a subscript", "ruwe-1.4", "RUWE c", False),
    ("a long word after the underscore is prose", "ruwe-1.4", "RUWE _ selection", False),
    ("a second underscore breaks the run", "ruwe-1.4", "RUWE _ c _ verylongword", False),
    ("the stem must END with the term", "ruwe-1.4", "RUWE and lambda _ c", False),
    ("another statistic's subscript is not this one's", "rhat-1.1", r"\max _ j", False),
    ("the term inside a longer word does not count", "ruwe-1.4", "PRUWEX _ c", False),
]


def run_shape():
    bad = 0
    print("\nE — the escape's own shape (asserted against the rule, not against a paper)")
    for label, prof_id, head, want in SHAPE:
        prof = wt.Profile.load(os.path.join(HERE, "profiles", prof_id + ".json"))
        got = wt.own_subscript(wt.normalise(head).strip(), prof)
        ok = got == want
        bad += not ok
        print(f"  {label:60s} {prof_id:10s} {str(got):5s} (want {want})  "
              f"{'ok' if ok else 'FAIL'}")
    return bad


def run(cases, kind):
    bad = 0
    print(f"\n{kind}")
    for label, prof_id, text, want in cases:
        prof = wt.Profile.load(os.path.join(HERE, "profiles", prof_id + ".json"))
        got = len(wt.sites(wt.normalise(text), prof))
        ok = got == want
        bad += not ok
        print(f"  {label:60s} {prof_id:10s} sites={got} (want {want})  "
              f"{'ok' if ok else 'FAIL'}")
        if not ok:
            print(f"      {text[:110]!r}")
    return bad


def main():
    print(wt.VERSION)
    bad = run(REPAIRED, "A — the two faults 0.7 made (designed against these; not evidence)")
    bad += run(KEPT_REMOVED, "B — and the escapes did not give 0.7's removals back "
                             "(the part that can fail honestly)")
    bad += run(CONTROLS, "C — the 0.6 and 0.7 controls, re-run whole")
    run(KNOWN_RED, "D — what 0.8 does NOT repair (recorded, not gated)")
    bad += run_shape()
    if bad:
        print(f"\nFAIL — {bad} case(s) wrong")
        return 1
    print("\npass. What this does NOT show: what the two escapes do to a literature. That is "
          "measured at tick 59 — over three frames against forecasts fixed in advance, and by "
          "hand-reading every site 0.8 adds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
