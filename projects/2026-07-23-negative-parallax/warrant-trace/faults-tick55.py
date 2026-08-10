#!/usr/bin/env python3
"""faults-tick55 — the same ten fault classes, cut from the RAW e-print this time.

`faults-tick53.py` is landed, and it stays landed and byte-identical: it is the record of a
defect and it keeps that job. This file exists because of a property of it that only became
visible when a repair had to be tested against it.

**The tick-53 fragments are quoted after normalisation.** They carry `<<CITE:…>>` markers —
the instrument's own rendering of a citation — and their braces are already gone. Fed back
through `normalise`, they behave like source text, which is why the file worked at all. But
two of tick 55's repairs act on raw LaTeX: a footnote is lifted out of the sentence it hangs
on, and `\\phantom{…}` is dropped because it typesets nothing. Neither can be seen in a
fragment whose braces were stripped before it was written down, so the landed fixtures cannot
show those repairs working, and a green count taken from them alone understates the repair
while looking like a measurement of it.

That the tick-53 fragments are renderings and not source is not asserted here. It is checked:
`normalise` at version 0.5, run over the raw fragment of 2104.13148 or 2107.06373 below,
reproduces the tick-53 fixture string **verbatim**.

So this file quotes the same fourteen sites from the e-print itself. Every fragment is cut by
`cut-fixtures-tick55.py` from the source fetched on 2026-08-10 — re-fetched for this tick and
verified byte-identical to the manifest that first read it — and the sha256 of the flat source
file stands beside each id below.

One translation is named rather than hidden. In 2312.03162 (G8) the line break that hides the
threshold is a **carriage return** in the file. The instrument opens its sources in text mode,
so Python's universal-newline translation turns it into `\\n` before any regex sees it; the
fragment is quoted here as the instrument reads it, with the byte it came from named. The
fault is the same fault either way, and which character it is was never in the record.

Expected state under 0.6: twelve green, two red — G5 (a threshold that is an expression
falling back to the value) and G10 (term and number in different sentences), both DECLINED in
`../PREREGISTRATION-tick55.md` §1 with their reasons. Red here is a repair not attempted, not
a repair that failed.

Run: python3 faults-tick55.py   (offline; writes faults-tick55.json)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warrant_trace import Profile, normalise, sites   # noqa: E402

PROF = Profile.load(os.path.join(HERE, "profiles/ruwe-1.4.json"))
PROF_MCMC = Profile.load(os.path.join(HERE, "profiles/rhat-1.1.json"))

# (fault, arxiv, sha256 prefix of the flat source, raw fragment, the value a correct
#  instrument should find)
CASES = [
    ("G1 the relation is a macro the list lacks: \\geqslant", "2601.07184", "baef4f50061c776b",
     "we followed the prescription from \\cite{gdr3_validation_2021} and applied the "
     "condition  \n    $ruwe\\geqslant 1.4$, where $ruwe$ is the re-normalized unit weighted "
     "\n    error \\citep{Lindegren2018}.", 1.4),

    ("G2 the relation is a macro the list lacks: \\gtrsim", "2603.11994", "776dbf38cf22393a",
     "This relation excludes stars with $S_C(G) \\gtrsim$ 10, large differences between "
     "observed and predicted V and I ($\\delta V, I \\gtrsim$ 0.1), and large RUWE "
     "$\\gtrsim$ 3.", 3.0),
    ("G2 the relation is a macro the list lacks: \\gtrsim", "2206.08383", "c2fb130ab9e5f09a",
     "RUWE should be around 1 for well-behaved sources, and higher values (RUWE$\\gtrsim$1.3) "
     "suggests with the presence of a stellar companion \\citep{Ziegler2020, Wood2021}.", 1.3),
    ("G2 the relation is a macro the list lacks: \\gtrsim", "2506.17861", "b8860e83d8e0e219",
     "For TOI-7149, the reported RUWE is 0.973, which is lower than the commonly accepted "
     "threshold in literature of $\\gtrsim$ 1.4 to ascertain the potential presence of "
     "stellar companions in binary studies \\citep{penoyre_binary_2020}.", 1.4),

    ("G3 a footnote stands between the term and the relation", "2104.13148", "5645dd4453a17275",
     "we rejected 7 sources with poor astrometric solution (renormalized unit weight error, "
     "RUWE,\\footnote{https://www.cosmos.esa.int/web/gaia/dr2-known-issues}$>$1.4).", 1.4),
    ("G3 a footnote stands between the term and the relation", "2203.07294", "168337486a2f67c2",
     "in order to use the stars with the most reliable astrometric measures: ($i$) "
     "RUWE\\footnote{RUWE is the renormalised unit weight error (for astrometry) discussed "
     "in \\citet{Lindegren+21}.} $< 2.4$; ($ii$) astrometric\\_excess\\_noise", 2.4),

    ("G4 term, relation and value stand in separate table cells", "2405.13395",
     "cad2d9e221ff37f4",
     "       &           &                & & $\\Delta(\\BPRP)$ & > & $-$0.50 mag"
     "                  \\\\\n       &           &                & & RUWE            & < & "
     "\\phantom{$-$}5               \\\\\n\\cline{5-7}", 5.0),

    ("G5 the threshold is an expression that falls back to the value", "2111.01145",
     "53dc68ef1965335d",
     "$\\beta < 0.1$ AND $|C*| \\leq 5\\, \\sigma_{C^{*}}(G) $ AND fidelity~$>0.5$ AND "
     "\\verb|ruwe|\\,$<$\\,max($\\overline{\\texttt{ruwe}}$\\,+\\,$\\sigma_{\\texttt{ruwe}}$, "
     "1.4)\\\\", 1.4),

    ("G6 an article stands between the relation and the value", "2111.03887", "297513a06d614ca9",
     "The renormalized unit weight error {\\tt ruwe} is 2.4 and this is greater than the 1.4 "
     "level that may indicate a resolved double.", 1.4),

    ("G7 the instrument's own citation marker stands in the gap", "2107.06373",
     "82f70751f6aacca0",
     "seven WDs have tabulated proper motion and parallax measurements with the renormalized "
     "unit weight error \\citep[RUWE,][]{2020arXiv201206242F,2020arXiv201203380L} "
     "$\\leq 1.4$.  We consider", 1.4),
    ("G7 the instrument's own citation marker stands in the gap", "2407.20949",
     "99b4fa4f834b6a42",
     "their \\textit{Gaia} Renormalized Unit Weight Error (RUWE, "
     "\\citealp{GaiaDR3:2023A&A...674A...1G}), which is an indicator of multiplicity, are "
     "lower than 1 (see Table \\ref{tab:parameters})", 1.0),

    # In the file this line break is a CARRIAGE RETURN; the reader's universal-newline
    # translation makes it the \n quoted here, before any regex sees it.
    ("G8 a line break stands in the gap", "2312.03162", "24a9b370195999b1",
     "Data quality cuts follow to ensure only binaries where both stars have a RUWE internal "
     "{\\it Gaia}\nsingle star solution quality index $<1.2$, imposing a final distance cut "
     "of 130 pc.", 1.2),

    ("G9 the paper misspells the term at the site", "2112.07023", "95d4da6937153b41",
     "and then remove any for which the renomalised unit weight error "
     "\\citep[RUWE;][]{gaiaedr3_astrom} is greater than 1.2. This cut on RUWE effectively "
     "removes those with poor astrometric solutions", 1.2),
]

MCMC_CASES = [
    # Tick 53 called this class "the gap bound of 100 characters is shorter than the
    # sentence". The raw text says otherwise, and `g10-double-block-tick55.py` proves it: the
    # term stands in one sentence and the number in the next, carried by the anaphor *this
    # factor*, and a full stop is not a bound. Two blocks, each sufficient alone.
    ("G10 the term and the number stand in different sentences", "2512.08173v1",
     "4085ea7564ffd55d",
     "For monitoring the convergence of the posterior samples across all methods, we "
     "evaluate the estimated potential scale reduction factor (\\cite{gelman1992inference}) "
     "for all unknown parameters. Based on our simulation results, this factor is generally "
     "around $1.00$ or below the commonly accepted threshold of $1.1$, indicating good "
     "convergence of the chains.", 1.1),
]


def run(fault, frag, want, prof=None):
    found = [s["value"] for s in sites(normalise(frag), prof or PROF)]
    ok = any(abs(float(v) - want) < 1e-9 for v in found)
    return ok, found


def main():
    out, green, red = [], 0, 0
    rows = [(f, a, s, fr, w, PROF) for f, a, s, fr, w in CASES]
    rows += [(f, a, s, fr, w, PROF_MCMC) for f, a, s, fr, w in MCMC_CASES]
    for fault, aid, sha, frag, want, prof in rows:
        if frag == "PENDING":
            continue
        ok, found = run(fault, frag, want, prof)
        out.append({"fault": fault, "arxiv": aid, "source_sha256_prefix": sha,
                    "expected_value": want, "instrument_found": found, "green": ok})
        green, red = (green + 1, red) if ok else (green, red + 1)
        print(f"[{'GREEN' if ok else 'RED  '}] {fault}\n"
              f"         {aid} ({sha}) expected {want}, found {found or 'nothing'}")

    declined = sorted({r["fault"].split(" ")[0] for r in out
                       if not r["green"]})
    rep = {"tick": 55, "instrument": "0.6", "fixtures": "raw e-print source",
           "cases": len(out), "green": green, "red": red, "red_classes": declined,
           "records": out}
    with open(os.path.join(HERE, "faults-tick55.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print(f"\n{green} green / {red} red of {len(out)} cases. Red is a repair DECLINED in the "
          f"pre-registration, not one that failed: {', '.join(declined) or 'none'}.")


if __name__ == "__main__":
    main()
