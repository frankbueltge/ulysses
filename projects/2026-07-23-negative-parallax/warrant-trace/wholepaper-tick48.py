#!/usr/bin/env python3
"""wholepaper-tick48 — is the deriving document in the paper at all?

Tick 48 of the work-line `2026-07-23-negative-parallax`, 2026-08-09.

The instrument in this directory answers "what stands at the site". It has never
asked the prior question: **is the deriving document anywhere in the paper?** Tick 47
asked it by hand for nine papers in one era of the computer-vision case and got
78 % against 0 % — the sharpest thing the line has found and the least defended.

This script asks it by code for the **first** case, `RUWE < 1.4`, over the 187 papers
the landed tick-35 table records as stating that value.

Rules are fixed in `../PREREGISTRATION-tick48.md`, written before this file produced
anything. The whole-paper pattern is **strictly narrower** than the profile's window
pattern (two alternatives that only make sense inside a window are dropped), because
narrowing can only lower the anywhere-count — the conservative direction.

Reuses `normalise`, `body_of`, `sites` and `Profile` from `warrant_trace.py` unchanged,
so the at-site half is computed by the same code that produced the shipped number.

    python3 wholepaper-tick48.py --src <dir> --frame frame-tick48-ruwe14.txt \
                                 --profile profiles/ruwe-1.4.json --out wholepaper-tick48
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warrant_trace import Profile, body_of, normalise, sites, same_value, read_ids  # noqa: E402

FOCUS = "1.4"

VERSION = "wholepaper-tick48 1.0 (2026-08-09)"

# --- the deriving document, strictly (pre-registration §3) --------------------
# Lindegren (2018), GAIA-C3-TN-LU-LL-124-01, "Re-normalising the astrometric
# chi-square in Gaia DR2" — the note in whose §6 the number 1.4 is read off a
# histogram. Dropped from the profile's window pattern: `technical\s+note` and
# `DPAC\s+technical`, which match unrelated prose once the window is removed.
TN_STRICT = re.compile(
    r"LL-?\s?124"
    r"|GAIA-C3-TN"
    r"|re-?normali[sz](?:ing|ation|ed)\s+the\s+astrometric\s+chi"
    r"|doc_fetch\.php\?id=3757412"
    r"|public-dpac-documents",
    re.I,
)

# --- the near-neighbour: Lindegren et al. 2018, A&A 616, A2 ------------------
# The profile's own note: the two Lindegren documents are "one character apart in
# most bibliographies". Measured so that a low anywhere-count for the note can be
# told apart from a literature that cites no Lindegren at all.
NEIGHBOUR = re.compile(r"2018A&A\.\.\.616A\.\.\.2L" r"|[Ll]indegren[^\n]{0,300}?\b616\b")

BIB_ENV = re.compile(r"\\begin\{thebibliography\}(.*?)(?:\\end\{thebibliography\}|\Z)", re.S)


def members(raw):
    """(name, content) for every %%%FILE member of a fetched source."""
    out = []
    for part in raw.split("%%%FILE "):
        if not part.strip():
            continue
        name, _, content = part.partition("\n")
        out.append((name.strip(), content))
    return out


def bib_region(raw):
    """Everything that is a bibliography: .bbl members + thebibliography environments.

    A paper whose arXiv submission carries no .bbl and no thebibliography has **no
    bibliography in its source at all** — its entry can be present in the published
    PDF and invisible here. That is a false-negative source for the anywhere-count
    and is counted in the open as `has_bib = 0`.
    """
    chunks = []
    for name, content in members(raw):
        if name.lower().endswith(".bbl"):
            chunks.append(content)
        else:
            chunks.extend(BIB_ENV.findall(content))
    return "\n".join(chunks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--frame", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    prof = Profile.load(args.profile)
    ids = read_ids(args.frame)
    rows, hits, misses = [], [], []

    for aid in ids:
        path = os.path.join(args.src, aid.replace("/", "_") + ".txt")
        if not os.path.exists(path):
            rows.append({"arxiv": aid, "state": "no_source", "has_bib": "", "A": "",
                         "A_bib": "", "A_body": "", "B14": "", "B_any": "", "C": "",
                         "sites_all": "", "sites14": "", "evidence": ""})
            continue
        raw = open(path, encoding="utf-8", errors="replace").read()
        bib = bib_region(raw)
        body = body_of(raw)

        m_all = TN_STRICT.search(raw)
        a = bool(m_all)
        a_bib = bool(TN_STRICT.search(bib))
        a_body = bool(TN_STRICT.search(body))

        # The at-site half, by the shipped pipeline, with the strict rule.
        #
        # `profiles/ruwe-1.4.json` carries no `focus_value` — the key was added to
        # the profile format at 0.2, after this profile was written, and the landed
        # tick-35 table therefore ORs its flags over **every** RUWE site in the
        # paper, whatever value stands there. That is how the shipped "4 papers"
        # was made. Both readings are computed here rather than one silently
        # chosen: `B14` restricts to sites carrying 1.4, `B_any` reproduces the
        # shipped definition.
        text = normalise(body)
        allsites = sites(text, prof)
        st14 = [s for s in allsites if same_value(s["value"], FOCUS)]
        b14 = any(TN_STRICT.search(s["window"]) for s in st14)
        b_any = any(TN_STRICT.search(s["window"]) for s in allsites)

        ev = ""
        if m_all:
            s0 = max(0, m_all.start() - 160)
            ev = re.sub(r"\s+", " ", raw[s0:m_all.end() + 160])
        rows.append({"arxiv": aid, "state": "measured", "has_bib": int(bool(bib.strip())),
                     "A": int(a), "A_bib": int(a_bib), "A_body": int(a_body),
                     "B14": int(b14), "B_any": int(b_any),
                     "C": int(bool(NEIGHBOUR.search(raw))), "sites_all": len(allsites),
                     "sites14": len(st14), "evidence": ev[:600]})
        (hits if a else misses).append(aid)

    with open(args.out + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if r["state"] == "measured"]
    n = len(ok)
    withbib = [r for r in ok if r["has_bib"] == 1]

    def cnt(k, sub=None):
        return sum(1 for r in (sub or ok) if r[k] == 1)

    # D5: a deterministic sample of 15 A-negative papers, no randomness anywhere
    neg = sorted(r["arxiv"] for r in ok if r["A"] == 0)
    step = max(1, len(neg) // 15)
    sample = neg[::step][:15]

    rep = {
        "version": VERSION,
        "sha256": {
            "wholepaper-tick48.py": hashlib.sha256(
                open(os.path.abspath(__file__), "rb").read()).hexdigest(),
            "warrant_trace.py": hashlib.sha256(
                open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "warrant_trace.py"), "rb").read()).hexdigest(),
            "profile": prof.sha256(),
        },
        "frame": len(ids),
        "measured": n,
        "no_source": len(ids) - n,
        "no_source_pct": round(100.0 * (len(ids) - n) / len(ids), 1),
        "has_bibliography_in_source": len(withbib),
        "A_anywhere": cnt("A"),
        "A_bibliography": cnt("A_bib"),
        "A_body_only": sum(1 for r in ok if r["A"] == 1 and r["A_bib"] == 0),
        "A_among_papers_with_bibliography": cnt("A", withbib),
        "B_at_1.4_site_strict": cnt("B14"),
        "B_at_any_ruwe_site_strict": cnt("B_any"),
        "total_ruwe_sites": sum(r["sites_all"] for r in ok),
        "total_1.4_sites": sum(r["sites14"] for r in ok),
        "C_neighbour_anywhere": cnt("C"),
        "papers_with_no_1.4_site_today": sum(1 for r in ok if r["sites14"] == 0),
        "papers_with_a_1.4_site_today": sum(1 for r in ok if r["sites14"] > 0),
        "d5_sample": sample,
        "A_positive_ids": hits,
    }
    with open(args.out + ".json", "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
