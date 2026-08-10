#!/usr/bin/env python3
"""faults-tick53 — the class-B misses of the census, each pinned to a verbatim string.

Tick 47 pinned seven faults this way and tick 50 repaired them. The tick-53 census reads
the WHOLE candidate class of two frames — the 53 gaia papers and the 20 mcmc papers the
instrument files as *invokes the statistic, states no threshold* — and finds thirteen
papers stating a threshold after all (twelve gaia, one mcmc). Class B: the sieve's misses.
Three further papers state a reference level rather than a rule and are counted apart.

This file does what tick 47 did. It takes the fragment from the paper as the instrument
itself renders it, runs the SHIPPED profile over it, and records what the instrument does.
RED is the correct state of this file on the day it is written: it is a record of a defect,
not a test of a repair. A later tick that repairs the profile turns lines green, and the
ones that stay red name what the repair did not reach.

Ten fault classes over fourteen fixtures. Two were mis-attributed by hand before these
fixtures were run — the misses at gaia #41 and #48 look like the citation fault and the
apposition fault and are neither — which is the reason the fixtures exist at all. Each
fault class carries a control where the single defect is removed by hand, so the claim
'the fault is HERE' is tested and not asserted.

No fixture is invented; each is quoted from the e-print fetched on 2026-08-10, and the
arXiv id and the tick-53 read order stand beside it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from warrant_trace import Profile, normalise, sites   # noqa: E402

PROF = Profile.load(os.path.join(HERE, "profiles/ruwe-1.4.json"))

# (fault, arxiv, read_order, fragment, the value a correct instrument should find)
CASES = [
    ("G1 the relation is a macro the list lacks: \\geqslant / \\leqslant", "2601.07184", 7,
     r"we followed the prescription from [cite] and applied the condition ruwe\geqslant 1.4 , "
     r"where ruwe is the re-normalized unit weighted error", 1.4),

    ("G2 the relation is a macro the list lacks: \\gtrsim", "2603.11994", 19,
     r"This relation excludes stars with S_C(G) \gtrsim 10, large differences between observed "
     r"and predicted V and I, and large RUWE \gtrsim 3.", 3.0),
    ("G2 the relation is a macro the list lacks: \\gtrsim", "2206.08383", 33,
     r"RUWE should be around 1 for well-behaved sources, and higher values (RUWE \gtrsim 1.3) "
     r"suggests with the presence of a stellar companion", 1.3),
    ("G2 the relation is a macro the list lacks: \\gtrsim", "2506.17861", 34,
     r"the reported RUWE is 0.973, which is lower than the commonly accepted threshold in "
     r"literature of \gtrsim 1.4 to ascertain the potential presence of stellar companions", 1.4),

    ("G3 a footnote stands between the term and the relation", "2104.13148", 6,
     r"we rejected 7 sources with poor astrometric solution (renormalized unit weight error, "
     r"RUWE,\footnote https://www.cosmos.esa.int/web/gaia/dr2-known-issues > 1.4)", 1.4),
    ("G3 a footnote stands between the term and the relation", "2203.07294", 21,
     r"( i ) RUWE\footnote RUWE is the renormalised unit weight error (for astrometry) "
     r"discussed in [cite] . < 2.4 ; ( ii ) astrometric_excess_noise", 2.4),

    ("G4 term, relation and value stand in separate table cells", "2405.13395", 9,
     r"& \Cstar & < & \phantom - 0.40 \\ & & & & RUWE & < & \phantom - 5 \\ \cline 5-7", 5.0),

    ("G5 the threshold is an expression that falls back to the value", "2111.01145", 31,
     r"\beta < 0.1 AND |C*| < 5 sigma _ C^ * (G) AND fidelity >0.5 AND \verb|ruwe| < "
     r"max( \overline texttt ruwe + sigma _ texttt ruwe , 1.4)", 1.4),

    ("G6 an article stands between the relation and the value", "2111.03887", 39,
     r"The renormalized unit weight error \tt ruwe is 2.4 and this is greater than the 1.4 "
     r"level that may indicate a resolved double.", 1.4),

    # The instrument replaces every citation with <<CITE:...>>. Its own marker carries the
    # two characters the relation alphabet is built from, and the gap class excludes them.
    ("G7 the instrument's own citation marker stands in the gap", "2107.06373", 43,
     r"seven WDs have tabulated proper motion and parallax measurements with the renormalized "
     r"unit weight error <<CITE:2020arXiv201206242F,2020arXiv201203380L>> < 1.4 . We consider", 1.4),
    ("G7 the instrument's own citation marker stands in the gap", "2407.20949", 53,
     r"their textit Gaia Renormalized Unit Weight Error (RUWE, <<CITE:GaiaDR3:2023>> ), which is "
     r"an indicator of multiplicity, are lower than 1 (see Table \ref tab:parameters )", 1.0),

    # Not the apposition — the newline. Where the author's editor wrapped the line decides
    # whether the instrument sees the threshold.
    ("G8 a line break stands in the gap", "2312.03162", 48,
     "Data quality cuts follow to ensure only binaries where both stars have a RUWE internal "
     "it Gaia \nsingle star solution quality index <1.2 , imposing a final distance cut", 1.2),

    # Not the citation — the spelling. The sieve's English is correct and the paper's is not.
    ("G9 the paper misspells the term at the site", "2112.07023", 41,
     r"remove any for which the renomalised unit weight error <<CITE:gaiaedr3_astrom>> is "
     r"greater than 1.2. This cut on RUWE effectively removes those with poor astrometric "
     r"solutions", 1.2),
]

# the same fragments with the single defect removed by hand — the control that shows the
# fault is where this file says it is and not somewhere else in the sentence
CONTROLS = [
    ("G7 control: the citation marker deleted", "2107.06373",
     r"seven WDs have tabulated proper motion and parallax measurements with the renormalized "
     r"unit weight error < 1.4 . We consider", 1.4),
    ("G8 control: the line break replaced by a space", "2312.03162",
     "Data quality cuts follow to ensure only binaries where both stars have a RUWE internal "
     "it Gaia single star solution quality index <1.2 , imposing a final distance cut", 1.2),
    ("G9 control: the spelling corrected", "2112.07023",
     r"remove any for which the renormalised unit weight error is greater than 1.2.", 1.2),
]


# the mcmc census finds one strict class-B paper; its profile is a different one, so it
# runs against rhat-1.1 rather than ruwe-1.4
PROF_MCMC = Profile.load(os.path.join(HERE, "profiles/rhat-1.1.json"))

MCMC_CASES = [
    ("G10 the gap bound of 100 characters is shorter than the sentence", "2512.08173v1", 3,
     r"we evaluate the estimated potential scale reduction factor ( <<CITE:gelman1992inference>> ) "
     r"for all unknown parameters. Based on our simulation results, this factor is generally "
     r"around 1.00 or below the commonly accepted threshold of 1.1 , indicating good convergence",
     1.1),
]
MCMC_CONTROLS = [
    ("G10 control: the same relation and value, one clause apart", "2512.08173v1",
     r"the potential scale reduction factor is below the commonly accepted threshold of 1.1", 1.1),
]


def run(fault, aid, frag, want, prof=None):
    found = [s["value"] for s in sites(normalise(frag), prof or PROF)]
    ok = any(abs(float(v) - want) < 1e-9 for v in found)
    return ok, found


def main():
    out, green, red = [], 0, 0
    for fault, aid, order, frag, want in CASES:
        ok, found = run(fault, aid, frag, want)
        out.append({"kind": "case", "fault": fault, "arxiv": aid, "read_order": order,
                    "expected_value": want, "instrument_found": found, "green": ok})
        green, red = (green + 1, red) if ok else (green, red + 1)
        print(f"[{'GREEN' if ok else 'RED  '}] {fault}\n"
              f"         {aid} (#{order}) expected {want}, found {found or 'nothing'}")

    for fault, aid, order, frag, want in MCMC_CASES:
        ok, found = run(fault, aid, frag, want, PROF_MCMC)
        out.append({"kind": "case", "profile": "rhat-1.1", "fault": fault, "arxiv": aid,
                    "read_order": order, "expected_value": want,
                    "instrument_found": found, "green": ok})
        green, red = (green + 1, red) if ok else (green, red + 1)
        print(f"[{'GREEN' if ok else 'RED  '}] {fault}\n"
              f"         {aid} (mcmc #{order}) expected {want}, found {found or 'nothing'}")

    print()
    ctrl_ok = 0
    for fault, aid, frag, want in CONTROLS + [(f, a, fr, w) for f, a, fr, w in MCMC_CONTROLS]:
        prof = PROF_MCMC if "G10" in fault else PROF
        ok, found = run(fault, aid, frag, want, prof)
        ctrl_ok += 1 if ok else 0
        out.append({"kind": "control", "fault": fault, "arxiv": aid,
                    "expected_value": want, "instrument_found": found, "green": ok})
        print(f"[{'GREEN' if ok else 'RED  '}] {fault} — {aid}: found {found or 'nothing'}")

    rep = {"tick": 53, "profile": "profiles/ruwe-1.4.json (instrument 0.5)",
           "cases": len(CASES) + len(MCMC_CASES), "green": green, "red": red,
           "fault_classes": sorted({c[0].split(" ")[0] for c in CASES + MCMC_CASES}),
           "controls": len(CONTROLS) + len(MCMC_CONTROLS), "controls_green": ctrl_ok, "records": out}
    with open(os.path.join(HERE, "faults-tick53.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print(f"\n{green} green / {red} red of {len(CASES) + len(MCMC_CASES)} cases in "
          f"{len(rep['fault_classes'])} fault classes; "
          f"{ctrl_ok}/{len(CONTROLS) + len(MCMC_CONTROLS)} controls green. Red is the recorded defect.")


if __name__ == "__main__":
    main()
