#!/usr/bin/env python3
"""Self-test for the 0.4 repair: one threshold, two units.

0.3 unified `1.1` and `1.10` — two written forms of one number. Tick 46 met a
literature that writes one threshold as `0.5` and as `50%`: two different numbers
denoting one criterion, which no numeric comparison can see. 0.4 lets the profile
DECLARE the equivalence (`focus_equivalents`), by a human who read the literature,
and reports the strict count beside the unioned one so the repair stays visible.

This asserts the repair on a four-paper synthetic corpus, so that the claim "0.4
counts `0.5` and `50%` as one threshold, and still counts `1.1` and `1.10` as one"
is checkable without re-fetching 256 papers. It writes nothing outside a temporary
directory, and it re-runs the 0.3 case, because a repair that breaks the repair
before it is not one.

Usage:  python3 selftest-0.4.py        (exit 0 = pass)
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

IOU_PAPERS = {
    "9902.00001": r"A detection counts as correct when $\mathrm{IoU} > 0.5$.",
    "9902.00002": r"We use an overlap threshold of 50\% throughout, as is standard.",
    "9902.00003": r"Boxes are matched at IoU greater than 0.75 for the strict setting.",
    "9902.00004": r"Following prior work the IoU threshold is set to 0.50.",
}
IOU_EXPECT = {
    # 0.5, 50, 0.75, 0.50 as written forms; 0.5/0.50 are one number, 50 another
    "distinct_values": 4,
    "distinct_values_numeric": 3,
    "focus_sites": 3,               # 0.5, 50%, 0.50 — one threshold, three writings
    "focus_papers": 3,
    "focus_numeric_0_3": 2,         # what 0.3 would have counted: 0.5 and 0.50
    "focus_string_0_2": 1,          # what 0.2 would have counted: the literal "0.5"
    "focus_written_forms": ["0.5", "0.50", "50"],
    "focus_equivalents": ["50"],
}

RHAT_PAPERS = {
    "9901.00001": r"We required $\hat{R} < 1.1$ for all parameters.",
    "9901.00002": r"Convergence was assessed with $\hat{R} < 1.10$ throughout.",
}
RHAT_EXPECT = {"focus_sites": 2, "focus_numeric_0_3": 2, "focus_string_0_2": 1,
               "focus_equivalents": []}


def run(profile, papers):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        for aid, body in papers.items():
            with open(os.path.join(src, aid + ".txt"), "w", encoding="utf-8") as fh:
                fh.write("%%%FILE main.tex\n" + body + "\n")
        out = os.path.join(tmp, "out")
        cmd = [sys.executable, os.path.join(HERE, "warrant_trace.py"), "measure",
               "--profile", os.path.join(HERE, "profiles", profile),
               "--src", src, "--out", out]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stdout + proc.stderr)
            return None
        with open(out + ".json", encoding="utf-8") as fh:
            return json.load(fh)["report"]


def compare(label, got, expect):
    bad = {k: (v, expect[k]) for k, v in got.items() if v != expect[k]}
    print(f"\n{label}")
    for k, v in got.items():
        print(f"  {k:26s} {v}   expected {expect[k]}"
              + ("   MISMATCH" if k in bad else ""))
    return bad


def main():
    rep = run("iou-0.5.json", IOU_PAPERS)
    if rep is None:
        return 1
    f = rep["focus"]
    got_iou = {"distinct_values": rep["distinct_values"],
               "distinct_values_numeric": rep["distinct_values_numeric"],
               "focus_sites": f["sites"],
               "focus_papers": f["papers"],
               "focus_numeric_0_3": f["sites_numeric_match_0_3"],
               "focus_string_0_2": f["sites_string_match_0_2"],
               "focus_written_forms": f["written_forms"],
               "focus_equivalents": f["equivalents"]}
    bad = compare("the 0.4 case — 0.5 and 50% are one threshold", got_iou, IOU_EXPECT)

    rep = run("rhat-1.1.json", RHAT_PAPERS)
    if rep is None:
        return 1
    f = rep["focus"]
    got_rhat = {"focus_sites": f["sites"],
                "focus_numeric_0_3": f["sites_numeric_match_0_3"],
                "focus_string_0_2": f["sites_string_match_0_2"],
                "focus_equivalents": f["equivalents"]}
    bad |= compare("the 0.3 case, unchanged — a profile without equivalents behaves "
                   "exactly as before", got_rhat, RHAT_EXPECT)

    if bad:
        print(f"\nFAIL — {len(bad)} field(s) disagree")
        return 1
    print("\npass — one threshold in two units is counted once, the strict counts of "
          "0.3 and 0.2 are still reported beside it, and a profile that declares no "
          "equivalents is untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
