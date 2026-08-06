#!/usr/bin/env python3
"""Self-test for the 0.3 repair: one threshold, two written forms.

Tick 36 hand-read twelve sites at R-hat 1.1 where the machine report said ten: two
of them are written `1.10`, and 0.2 compared the focus value as a string. Tick 38
found the same string identity under `distinct_values`, which both landed reports
publish as "distinct values in use" — 121 written forms against 115 numbers in the
RUWE frame, 22 against 20 in the R-hat frame.

This asserts the repair on a two-paper synthetic corpus, so that the claim "0.3
counts `1.1` and `1.10` as one threshold" is checkable without re-fetching 230
papers. It writes nothing outside a temporary directory.

Usage:  python3 selftest-0.3.py        (exit 0 = pass)
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PAPERS = {
    "9901.00001": r"We required $\hat{R} < 1.1$ for all parameters.",
    "9901.00002": r"Convergence was assessed with $\hat{R} < 1.10$ throughout.",
}
EXPECT = {"sites": 2, "distinct_values": 2, "distinct_values_numeric": 1,
          "focus_sites": 2, "focus_papers": 2, "focus_string_match_0_2": 1,
          "focus_written_forms": ["1.1", "1.10"]}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        for aid, body in PAPERS.items():
            with open(os.path.join(src, aid + ".txt"), "w", encoding="utf-8") as fh:
                fh.write("%%%FILE main.tex\n" + body + "\n")
        out = os.path.join(tmp, "out")
        cmd = [sys.executable, os.path.join(HERE, "warrant_trace.py"), "measure",
               "--profile", os.path.join(HERE, "profiles", "rhat-1.1.json"),
               "--src", src, "--out", out]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stdout + proc.stderr)
            return 1
        with open(out + ".json", encoding="utf-8") as fh:
            rep = json.load(fh)["report"]

    got = {"sites": rep["sites"],
           "distinct_values": rep["distinct_values"],
           "distinct_values_numeric": rep["distinct_values_numeric"],
           "focus_sites": rep["focus"]["sites"],
           "focus_papers": rep["focus"]["papers"],
           "focus_string_match_0_2": rep["focus"]["sites_string_match_0_2"],
           "focus_written_forms": rep["focus"]["written_forms"]}
    bad = {k: (v, EXPECT[k]) for k, v in got.items() if v != EXPECT[k]}
    for k, v in got.items():
        print(f"  {k:26s} {v}   expected {EXPECT[k]}"
              + ("   MISMATCH" if k in bad else ""))
    if bad:
        print(f"\nFAIL — {len(bad)} field(s) disagree")
        return 1
    print("\npass — 1.1 and 1.10 are counted as one threshold, and the written-form "
          "count is still reported beside the numeric one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
