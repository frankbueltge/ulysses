#!/usr/bin/env python3
"""repair-consequence — what the 0.6 repair does to the work this line is building.

*The gap* was named at tick 54: the sieve's own gap class made touchable, a real sentence
from a real paper, one movable typographic accident, and the committed instrument judging
every state. Its first increment is `sketch-v1.html`, and its measurement is the sweep — one
space becomes a newline, once per position: **9 of 28 break positions blind the reader**, the
paper's own break among them.

Tick 55 repaired the sieve. The first thing that happened when the sketch's own generator was
re-run under 0.6 was not a changed number. It was a **crash**, on the assertion the generator
carries about its own material:

    AssertionError: the paper's own break does not blind the instrument

E4 admits a single non-paragraph newline into the gap, so the accident the work was built on
no longer does anything. That is the correct outcome for the instrument and it takes the
demonstration away from the work.

This script measures the size of the loss rather than describing it: the same sweep, under
the repaired instrument. Nothing in `the-gap/` is rewritten — `states-tick54.json` and
`sketch-v1.html` stay exactly as they landed, and their sha256 is printed here beside the new
count, so the pair is on the record.

What follows for the work is a decision, not an arithmetic, and it is written in the score:
the honest move is NOT to withhold a repair in order to keep an artwork's material, which
would make a defect into a possession. Either the work fixes its instrument version and says
which day's sieve it is about, or the version becomes the second movable thing — the reader
moves the accident, and then moves the apparatus that judges it.

Run: python3 repair-consequence-tick55.py   (offline; writes repair-consequence-tick55.json)
"""
import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.normpath(os.path.join(HERE, "..", "warrant-trace"))
sys.path.insert(0, WT)
from warrant_trace import Profile, VERSION, normalise, sites   # noqa: E402


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    fx = load(os.path.join(WT, "faults-tick53.py"), "faults_tick53")
    prof = Profile.load(os.path.join(WT, "profiles/ruwe-1.4.json"))
    landed = json.load(open(os.path.join(HERE, "states-tick54.json"), encoding="utf-8"))
    panel = [p for p in landed["panels"] if p["kind"] == "sweep"][0]

    # the sweep, exactly as tick 54 defines it: the fixture's own control string, with one
    # space replaced by a newline, once per space position. The base string is taken from the
    # landed panel so the two runs are the same sweep and not two similar ones.
    base = panel["base"]
    positions = [i for i, c in enumerate(base) if c == " "]
    blind = []
    for i in positions:
        state = base[:i] + "\n" + base[i + 1:]
        if not sites(normalise(state), prof):
            blind.append(i)

    out = {
        "tick": 55,
        "instrument_now": VERSION,
        "instrument_at_tick_54": landed.get("instrument", "warrant-trace 0.5 (2026-08-09)"),
        "arxiv": panel["arxiv"],
        "positions": len(positions),
        "blind_positions_at_tick_54": panel["blind_positions"],
        "blind_positions_now": blind,
        "blind_at_tick_54": len(panel["blind_positions"]),
        "blind_now": len(blind),
        "paper_own_break_position": panel["fixture_position"],
        "paper_own_break_still_blinds": panel["fixture_position"] in blind,
        "landed_untouched": {
            "states-tick54.json": sha(os.path.join(HERE, "states-tick54.json")),
            "sketch-v1.html": sha(os.path.join(HERE, "sketch-v1.html")),
            "faults-tick53.py": sha(os.path.join(WT, "faults-tick53.py")),
        },
    }
    with open(os.path.join(HERE, "repair-consequence-tick55.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"the sweep of {out['arxiv']}: {len(positions)} break positions")
    print(f"  blind at tick 54 (instrument 0.5): {out['blind_at_tick_54']}")
    print(f"  blind now        ({VERSION}): {out['blind_now']}")
    print(f"  the paper's own break still blinds the instrument: "
          f"{out['paper_own_break_still_blinds']}")
    print("\nthe landed sketch and its states are untouched; their sha256 are in the json")


if __name__ == "__main__":
    main()
