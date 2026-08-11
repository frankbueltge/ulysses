#!/usr/bin/env python3
"""Self-test for the 0.7 repair — the first one whose fixtures are the sieve's own output.

Same shape as `selftest-0.6.py`, with one difference that matters. There, part A held
fragments the repair was designed against and was therefore not evidence. Here every string
in part A is a **matched string this instrument produced**, copied verbatim from
`sites-tick57.txt`, the landed dump of all 344 sites of the computer vision frame — and each
one belongs to a paper the tick-57 hand census read as stating no threshold at all. So part A
is still not evidence that the repair is right in the corpus (it was designed against these
strings), but it is at least a test against things the instrument really did, rather than
against sentences written to be repaired.

Part B is the part that can fail honestly, and at 0.7 it carries more weight than usual,
because every repair here REMOVES sites. Each removal has a control that must survive it: the
comparison that belongs to the statistic, the article the step still admits, the threshold
written with a symbol, the mean form that names a threshold anyway, the table site whose row
break comes after its value.

Part C holds the one repair that adds: the apposition.

Part D keeps the defect this file's predecessor found and did not repair, and adds the two
0.7 declines, so that what the instrument still cannot do stays in front of a reader.

The real test is not here. It is the tick-58 re-measure over three frames, against forecasts
written before the corpus was read, and the seed-58 hand sample of the sites 0.7 removes.

Usage:  python3 selftest-0.7.py        (exit 0 = pass)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as wt                                      # noqa: E402

# --------------------------------------------- A: the invented sites, verbatim, are gone
# (class, profile, fragment as the instrument itself printed it, sites wanted)
REPAIRED = [
    ("E6 conf= (2603.16241v1)", "iou-0.5",
     "we tuned the IoU, we selected conf=0.5 for all runs", 0),
    ("E6 pgfplots axis option (2604.19609v1)", "iou-0.5",
     "ylabel= mIoU (%) , xmode=log, log basis x=10", 0),
    ("E6 a table column (2607.00357v1)", "iou-0.5",
     r"mIoU ( \uparrow ) & \multicolumn 4 c F1-score ( \uparrow ) \\ Algorithms & N =1", 0),
    ("E6 a summation index (2607.15041v1)", "iou-0.5",
     r"IoU^ rank _i \sum_ i=1", 0),
    ("E6 an overlap ratio named r (2603.12759v1)", "iou-0.5",
     "we require an overlap ratio to r=0.5 between viewpoints", 0),
    ("E6+E7 the metric's own definition (2607.01708v1)", "iou-0.5",
     r"mIoU = \frac 1 N \sum_ i=1", 0),
    ("P-C a reported improvement (2603.28297v1)", "iou-0.5",
     "the mIoU improvements <0.5 are within noise", 0),
    ("P-C a reported mean (2604.18549v1)", "iou-0.5", "our model reaches a mIoU of 48.3", 0),
    ("P-C a reported mean, percent (2603.28297v1)", "iou-0.5",
     "the network attains a mIoU of 89.04% on the test split", 0),
    ("P-C a reported mean, parenthesised (2605.11300v1)", "iou-0.5",
     "we report a mIoU (SS) of 50.9 for the single-scale setting", 0),
    ("P-C a reported mean, compared (2603.28297v1)", "iou-0.5",
     "all three backbones reach mIoU > 90% on this benchmark", 0),
    ("P-C a mean written out (2607.01708v1)", "iou-0.5",
     "we obtain a mean IoU (mIoU) of 0.728 over the validation set", 0),
]

# ----------------------------------------- B: and the removals did not take the real sites
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
]

# ------------------------------------------------------ C: the one repair that adds a site
APPOSITION = [
    ("P-A the apposition (2607.02371v1)", "iou-0.5",
     "we report mAP at IoU 0.50 for every split", 1),
    ("P-A in a table header", "iou-0.5", "Method & AP at IoU 0.3 & AP at IoU 0.5", 1),
    ("P-A must not fire on a mean", "iou-0.5", "the model lands at mIoU 82.7 on this set", 0),
    ("P-A must not reach past a word", "iou-0.5",
     "measured at the IoU curve computed for 0.5 seconds", 0),
]


# --------------------------------------- D: what 0.7 does NOT repair, recorded and not gated
# The first is 0.6's own red case, unchanged: `of` reaches a number through an English
# genitive, and it has done so in every profile since tick 21. 0.7 repairs the ONE form of it
# with a mechanical property — the mean — and leaves the rest, because `an IoU of 0.910` and
# `an IoU of 0.50` differ in what the sentence is doing and not in anything a regex holds.
# N4 and N5 are new, and 0.7 CAUSED them: they are the cost of its own two engine repairs,
# found by the seed-58 hand sample and by reading all 84 removed matches. E6 reads the tail of
# the statistic's OWN subscript as a foreign variable (`RUWE _ \mathrm c < 1.4` at the focus
# value; `IoU _ 3 \mathrm D > 0.20`), and E7's row break falls between a table's column head
# and the cell that carries its threshold (`IoU\\ > 0.50`). Six of the 84 removed matches are
# one of these two, and both are the next tick's operation together with its re-measure — not
# this one's, because a tick that repairs the instrument it is measuring leaves no version in
# which the measurement holds.
# The second is the decline the tick-57 census named: a paper whose criterion lives wholly in
# `AP_50` or `mAP@50` and never writes the term at a threshold. Four labels in that census
# were wrong for this reason. No regex over the term can reach it; it needs a second detector,
# which is a change to what the instrument measures and therefore its own operation.
KNOWN_RED = [
    ("N1 `of` reaches a number through a genitive", "ruwe-1.4",
     "the RUWE is discussed below the companion mass of 1.4 solar masses", 1),
    ("N2 a reported IoU read as a rule (2608.04423v1)", "iou-0.5",
     "the predicted mask reaches an IoU of 0.910 against the annotation", 1),
    ("N3 the criterion absorbed into a name (2604.01907v2)", "iou-0.5",
     "we report AP_25 and AP_50 for every method", 0),
    ("N4 the subscripted statistic (2506.22399, 2608.05356v1)", "ruwe-1.4",
     r"we keep sources with RUWE _ \mathrm c < 1.4 in the final sample", 0),
    ("N5 a table column head and its cell (2604.20395v2)", "iou-0.5",
     r"Recall @ IoU\\ > 0.50 & 54.3", 0),
]


def run(cases, kind):
    bad = 0
    print(f"\n{kind}")
    for label, prof_id, text, want in cases:
        prof = wt.Profile.load(os.path.join(HERE, "profiles", prof_id + ".json"))
        got = len(wt.sites(wt.normalise(text), prof))
        ok = got == want
        bad += not ok
        print(f"  {label:48s} {prof_id:10s} sites={got} (want {want})  "
              f"{'ok' if ok else 'FAIL'}")
        if not ok:
            print(f"      {text[:110]!r}")
    return bad


def main():
    print(wt.VERSION)
    bad = run(REPAIRED, "A — the invented sites, verbatim from sites-tick57.txt "
                        "(designed against these; not evidence)")
    bad += run(CONTROLS, "B — and the removals did not take the real sites "
                         "(the part that can fail honestly)")
    bad += run(APPOSITION, "C — the apposition, the one repair that adds")
    run(KNOWN_RED, "D — what 0.7 does NOT repair (recorded, not gated)")
    if bad:
        print(f"\nFAIL — {bad} case(s) wrong")
        return 1
    print("\npass. What this does NOT show: what the repair does to a literature, and "
          "whether a site it removes was real. Both are measured at tick 58 — over three "
          "frames against forecasts fixed in advance, and by a seed-58 hand sample of the "
          "removed sites.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
