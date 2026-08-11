#!/usr/bin/env python3
"""name-check-tick57 — one mechanical test of a label, not a re-reading.

Why it exists. This tick found two of its own labels wrong in the same way, and then a
third in tick 56's landed table: a paper that never writes the *term* at a threshold —
or never writes it at all — but reports `AP_50` / `mAP50` / `AP@0.5` in live text. Such
a paper IS an invoker; its criterion lives wholly in the metric's name. Read from windows
cut around the term, it looks like a non-invoker, because the name is not the term.

    2604.01907v2   one term match in the whole paper (`overlap of 50 frames`), and
                   AP_25 / AP_50 result tables.        first read X-ENGLISH -> I-NAME
    2604.19609v1   two sites, both pgfplots axis options, and `82.7 mAP50` in the text.
                                                        first read X-SCORE  -> I-NAME
    2607.27585v1   tick 56's, `IoU of 0.9008` and an $AP_{50}$/$AP_{75}$ table.
                                                        landed X-SCORE      -> I-NAME

Three in the 44 papers a human eye had passed. That rate has no business staying
unmeasured in `X_A` = 39, which sits in the denominator of every rate this tick reports —
so the same test is run over the 39 papers tick 56's census called non-invokers.

What this is NOT: a re-reading of stratum A, which `PREREGISTRATION-tick57.md` §5 puts
out of scope. It returns a COUNT OF FLAGS and quotes the line that raised each one. A
flag is a paper worth re-reading, not a label. Nothing here changes a number in
`rates-tick57.json`; the result is reported as post-hoc, exactly as tick 56 reported the
finding that occasioned this tick.

The comment test matters and is not cosmetic: `2605.20436v2` carries five `mAP50` rows,
every one of them inside a `%`-commented table. A check that ignored comments would have
called a withdrawn table a metric.
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# the AP@0.5 family, in the spellings this corpus actually uses. Deliberately narrow:
# a bare `mAP` is NOT matched, because it names no threshold and would flag every
# detection paper in the class.
NAME = re.compile(r"(m?AP\s*[@_^{\\ ]{0,10}\s*(?:0?\.?50?|50)\b|AP\s*_?\s*\{?\s*50"
                  r"|mAP@?\[?\.?5)", re.I)
NON_INVOKER = {"X-ENGLISH", "X-LOSS", "X-SCORE", "X-CITE", "X-QUERY", "X-NOTATION",
               "X-OTHER"}


def live_hits(path):
    """Lines carrying an AP@50-family name that are NOT LaTeX comments."""
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.lstrip().startswith("%"):
                continue
            if NAME.search(line):
                out.append(re.sub(r"\s+", " ", line).strip()[:200])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--hand", required=True, help="hand table to test")
    ap.add_argument("--stratum", default="A")
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with open(os.path.join(HERE, a.hand), encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["stratum"] == a.stratum]
    tested = [r for r in rows if r["label"] in NON_INVOKER]

    flagged, clean, missing = [], 0, []
    for r in tested:
        path = os.path.join(a.src, r["arxiv"].replace("/", "_") + ".txt")
        if not os.path.exists(path):
            missing.append(r["arxiv"])
            continue
        hits = live_hits(path)
        if hits:
            flagged.append({"arxiv": r["arxiv"], "landed_label": r["label"],
                            "live_hits": len(hits), "lines": hits[:3]})
        else:
            clean += 1

    rep = {
        "tick": 57, "status": "POST-HOC - not forecast in the registration",
        "what_this_is": "a mechanical flag over labels, not a re-reading; a flag is a "
                        "paper worth re-reading and is not itself a corrected label",
        "hand_table": a.hand, "stratum": a.stratum,
        "rows_in_stratum": len(rows), "tested_non_invokers": len(tested),
        "no_source": missing,
        "flagged": len(flagged), "clean": clean,
        "flag_rate_pct": round(100.0 * len(flagged) / len(tested), 1) if tested else None,
        "detail": flagged,
        "calibration": "the same test over the 44 site-bearing non-invoker readings of "
                       "ticks 56-57 flagged 3, and all 3 were confirmed by hand as "
                       "I-NAME: 2604.01907v2, 2604.19609v1, 2607.27585v1",
    }
    with open(os.path.join(HERE, a.out), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "detail"}, indent=1))
    for f in flagged:
        print(f"  FLAG {f['arxiv']}  landed={f['landed_label']}  hits={f['live_hits']}")
        for l in f["lines"][:1]:
            print(f"       {l[:150]}")


if __name__ == "__main__":
    main()
