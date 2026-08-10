#!/usr/bin/env python3
"""g10-double-block — what actually stops the instrument at the one mcmc miss.

Tick 53 pinned ten fault classes and named the tenth *"the gap bound of 100 characters is
shorter than the sentence"*. Tick 55 declines to repair it, so the name had to be checked
before it was carried forward as a reason.

It is wrong, and it is wrong in a way this line has now seen twice. The fragment is blocked
**twice over**, and each block is sufficient on its own:

  * a **full stop** stands between the statistic's name and its number — the term is in one
    sentence and the threshold in the next, carried by the anaphor *this factor*. No bound
    reaches across it: at 10 000 characters the instrument still finds nothing.
  * the **bound** is genuinely too short as well — with the full stop replaced by a comma
    and nothing else changed, 100 characters still finds nothing and 200 finds the number.

So tick 53's name is not a diagnosis: raising the bound alone changes nothing, and the class
cannot be closed by widening. It is the same shape as the finding tick 54 made against tick
53's G9 — a fault class named after one cause that has two, where the control removed both
at once. That is now two of ten.

The declining is unchanged: crossing a full stop means letting a threshold in one sentence
attach to a statistic named in another, which is the widening tick 50 measured and paid for.

Run: python3 g10-double-block-tick55.py   (offline; writes g10-double-block-tick55.json)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warrant_trace as W                                            # noqa: E402

# 2512.08173v1, mcmc read order 3 — quoted at tick 53 as the instrument renders it.
PRINTED = (r"we evaluate the estimated potential scale reduction factor ( "
           r"<<CITE:gelman1992inference>> ) for all unknown parameters. Based on our "
           r"simulation results, this factor is generally around 1.00 or below the commonly "
           r"accepted threshold of 1.1 , indicating good convergence")
# the control: ONE character of the paper's own text changed, the full stop into a comma
COMMA = PRINTED.replace("parameters. Based", "parameters, based")
BOUNDS = (100, 200, 400, 1000, 10000)
BASE = r"(?:<<[^<>\n]*>>|\n(?![ \t]*\n)|[^.;:\n]|\.(?=\d)){0,%d}?"


def found(text, bound):
    W.GAP = BASE % bound
    prof = W.Profile.load(os.path.join(HERE, "profiles/rhat-1.1.json"))
    return [s["value"] for s in W.sites(W.normalise(text), prof)]


def main():
    rows = []
    for b in BOUNDS:
        a, c = found(PRINTED, b), found(COMMA, b)
        rows.append({"bound": b, "as_printed": a, "full_stop_as_comma": c})
        print(f"bound {b:>6}: as printed -> {a or 'nothing':<10} "
              f"full stop replaced by a comma -> {c or 'nothing'}")
    verdict = {
        "sentence_boundary_sufficient_alone":
            all(not r["as_printed"] for r in rows),
        "bound_sufficient_alone":
            not rows[0]["full_stop_as_comma"] and bool(rows[1]["full_stop_as_comma"]),
    }
    print("\nthe full stop alone blocks it at every bound tried: "
          f"{verdict['sentence_boundary_sufficient_alone']}")
    print("the bound alone blocks it with the full stop removed:  "
          f"{verdict['bound_sufficient_alone']}")
    out = {"tick": 55, "instrument": W.VERSION, "arxiv": "2512.08173v1",
           "fault_class_as_named_at_tick_53":
               "G10 the gap bound of 100 characters is shorter than the sentence",
           "rows": rows, "verdict": verdict,
           "correction": ("the fragment is blocked twice, each block sufficient alone: a full "
                          "stop between the term and the number, and the bound. Tick 53 named "
                          "only the second, and the second alone does not close the class.")}
    with open(os.path.join(HERE, "g10-double-block-tick55.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
