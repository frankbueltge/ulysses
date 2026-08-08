#!/usr/bin/env python3
"""Dump every use site at a profile's focus value, with its bibliography resolved.

Why this exists. Both measurements of this line ended with the same sentence: the
sieve's numbers are worthless until the load-bearing sites are read by hand, and at
tick 35 the sieve's deriving-document flag returned 0 of 38 where hand-reading found
3 — because a citation key cannot be resolved to a document from the window it
stands in. Resolving it needs the bibliography, which `body_of()` deliberately drops.

So the hand-reading step, done ad hoc at ticks 21 and 35, becomes a subcommand of
its own: for every site carrying the focus value it prints the citing paper, the
matched string, the window, the citation keys inside the window, and — the part that
was manual — the bibliography entry each of those keys resolves to, taken from the
same source file. What it does not do is decide anything. The classification stays a
human reading, and the CSV it feeds is written by hand.

    python3 handread_sites.py --profile profiles/rhat-1.1.json --src corpus/src
    python3 handread_sites.py --profile profiles/rhat-1.1.json --src corpus/src \
                              --value 1.01 --out sites.jsonl
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warrant_trace as W                                          # noqa: E402

BIBITEM = re.compile(r"\\bibitem(?:\[[^\]]*\])?\s*\{([^}]*)\}(.*?)(?=\\bibitem|\\end\{thebibliography\}|\Z)",
                     re.S)
BIBENTRY = re.compile(r"@\w+\s*\{\s*([^,]+),(.*?)(?=\n@|\Z)", re.S)


def bibliography(raw):
    """key -> entry text, from .bbl members, thebibliography, or an inline .bib."""
    out = {}
    for key, body in BIBITEM.findall(raw):
        out[key.strip()] = re.sub(r"\s+", " ", body)[:700]
    for key, body in BIBENTRY.findall(raw):
        out.setdefault(key.strip(), re.sub(r"\s+", " ", body)[:700])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--value", default=None,
                    help="value to dump; defaults to the profile's focus_value")
    ap.add_argument("--out", default=None, help="also write JSONL here")
    a = ap.parse_args()

    prof = W.Profile.load(a.profile)
    value = a.value or prof.focus_value
    if value is None:
        sys.exit("no --value and the profile has no focus_value")
    # 0.4: with no --value, select the sites the profile calls its own — including
    # every declared unit of one threshold (0.5 and 50%). The string comparison that
    # stood here would have hidden exactly the sites the 0.4 repair exists to find,
    # and hidden them in the step that decides the numbers. With an explicit --value
    # the comparison stays a numeric one over that value alone.
    if a.value is None:
        selects = prof.is_focus
    else:
        selects = lambda v: W.same_value(v, str(value))               # noqa: E731

    records = []
    for fn in sorted(os.listdir(a.src)):
        if not fn.endswith(".txt"):
            continue
        raw = open(os.path.join(a.src, fn), encoding="utf-8", errors="replace").read()
        text = W.normalise(W.body_of(raw))
        hits = [s for s in W.sites(text, prof) if selects(s["value"])]
        if not hits:
            continue
        bib = bibliography(raw)
        for s in hits:
            keys = [k for chunk in s["cite_keys"].split() for k in chunk.split(",") if k]
            records.append({
                "arxiv": fn[:-4],
                "match": s["match"],
                "value": s["value"],
                "target_sieve": s["target"],
                "flags": {k: v for k, v in s["flags"].items() if v},
                "cite_keys": keys,
                "bib": {k: bib.get(k, "<<key not found in this source's bibliography>>")
                        for k in keys},
                "window": s["window"],
            })

    for i, r in enumerate(records, 1):
        print(f"\n=== [{i}] {r['arxiv']}  |  {r['match']}  |  sieve target: {r['target_sieve']}")
        print("    flags:", ", ".join(r["flags"]) or "none")
        print("    window:", r["window"][:900])
        for k, entry in r["bib"].items():
            print(f"    cite {k}: {entry[:400]}")
    print(f"\n{len(records)} sites at value {value}, in "
          f"{len({r['arxiv'] for r in records})} papers.")

    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
