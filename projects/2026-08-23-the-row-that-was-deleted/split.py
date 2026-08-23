"""The blind split, fixed before any deletion instruction was read.

The extractor's vocabulary has to come from somewhere, and a vocabulary read off the whole
corpus is a selection step that can see the outcome (PROTOCOL v6 §4, the blind step). So the
91 amending acts are sorted by CELEX and every 4th taken as DEVELOPMENT: the extractor is
built by reading those and only those. The clauses are scored on the 68 acts held out.

Written before the first instruction was read. The rule is arithmetic on a sorted list; it
cannot be tuned toward a result it has not seen.
"""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "2026-08-21-the-citation-that-stopped"


def act_kind(title: str) -> str:
    low = title.lower()
    if low.startswith("corrigendum"):
        return "CORRIGENDUM"
    if "amending" in low:
        return "AMENDING"
    if "correcting" in low:
        return "CORRECTING"
    return "FULL_LIST"


def load():
    man = json.loads((SRC / "manifest.json").read_text())
    return man["acts"]


def amending(acts):
    return sorted((a for a in acts if act_kind(a["title"]) == "AMENDING"),
                  key=lambda a: a["celex"])


def split(acts):
    am = amending(acts)
    dev = [a for i, a in enumerate(am) if i % 4 == 0]
    held = [a for i, a in enumerate(am) if i % 4 != 0]
    return dev, held


if __name__ == "__main__":
    dev, held = split(load())
    print(f"amending {len(dev) + len(held)}  development {len(dev)}  held out {len(held)}")
    print("development CELEX:", " ".join(a["celex"] for a in dev))
