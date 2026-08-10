#!/usr/bin/env python3
"""cut-fixtures-tick55 — the raw fragment behind each pinned fault, cut from the e-print.

Why this exists. The fourteen fragments of `faults-tick53.py` are quoted **after**
normalisation: they carry `<<CITE:…>>` markers and have already lost their braces. Two of
tick 55's repairs act on raw LaTeX — a footnote is lifted out of its host sentence, and
`\\phantom{…}` is dropped — on text that no longer exists in a normalised fragment. So the
landed fixtures cannot show those repairs at all, and a green count taken from them alone
understates the repair while looking like a measurement of it.

This script cuts the same sites out of the **raw** e-print, so `faults-tick55.py` can quote
what the instrument actually reads. It prints the file's sha256 beside every fragment; the
tick-53 manifest records the sha256 of the fetched archive, and the re-fetch of tick 55
checks the two against each other paper by paper.

Nothing here is landed as a result. It is the tool that produced the quotations in
`faults-tick55.py`, kept so that the cutting is reproducible rather than asserted.

Usage: python3 cut-fixtures-tick55.py --src corpus/tick55/gaia/src [--only 2104.13148]
"""
import argparse
import hashlib
import os
import re
import sys

# (fault, arxiv, corpus, anchor regex over the RAW source, chars before, chars after)
ANCHORS = [
    ("G1", "2601.07184", "gaia", r"geqslant", 200, 200),
    ("G2", "2603.11994", "gaia", r"gtrsim", 220, 160),
    ("G2", "2206.08383", "gaia", r"gtrsim\s*1\.3", 220, 160),
    ("G2", "2506.17861", "gaia", r"gtrsim\s*1\.4", 240, 160),
    ("G3", "2104.13148", "gaia", r"RUWE,\\footnote", 140, 200),
    ("G3", "2203.07294", "gaia", r"RUWE\\footnote", 120, 300),
    ("G4", "2405.13395", "gaia", r"RUWE\s*&\s*<", 160, 160),
    ("G5", "2111.01145", "gaia", r"max\(", 200, 160),
    ("G6", "2111.03887", "gaia", r"greater than the", 220, 120),
    ("G7", "2107.06373", "gaia", r"unit weight error\s*\\cite", 160, 200),
    ("G7", "2407.20949", "gaia", r"Renormalized Unit Weight Error", 120, 260),
    ("G8", "2312.03162", "gaia", r"single star solution quality index", 260, 160),
    ("G9", "2112.07023", "gaia", r"renomalised", 160, 260),
    ("G10", "2512.08173v1", "mcmc", r"potential scale reduction", 120, 340),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="a corpus src/ directory")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    for fault, aid, corpus, anchor, before, after in ANCHORS:
        if args.only and args.only != aid:
            continue
        path = os.path.join(args.src, aid.replace("/", "_") + ".txt")
        if not os.path.exists(path):
            print(f"--- {fault} {aid}: NOT FETCHED", file=sys.stderr)
            continue
        blob = open(path, "rb").read()
        raw = blob.decode("utf-8", errors="replace")
        m = re.search(anchor, raw)
        if not m:
            print(f"--- {fault} {aid}: anchor {anchor!r} NOT FOUND", file=sys.stderr)
            continue
        seg = raw[max(0, m.start() - before):m.end() + after]
        print(f"--- {fault} {aid}  sha256(flat source)={hashlib.sha256(blob).hexdigest()[:16]}")
        print(repr(seg))
        print()


if __name__ == "__main__":
    main()
