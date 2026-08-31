#!/usr/bin/env python3
"""Tests for the lineage instrument.

The classification of an occurrence is the one place where this instrument can
quietly change its own answer — the refinement of 2026-08-31 exists precisely
because "reference" was covering two different things. So the classifier is
asserted here rather than trusted. Run: python3 tools/lineage/test_lineage.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineage as L  # noqa: E402

FAILED: list[str] = []
RUN = 0


def check(name: str, got, want) -> None:
    global RUN
    RUN += 1
    if got != want:
        FAILED.append(f"{name}: got {got!r}, want {want!r}")


TARGET = "2026-07-23-negative-parallax"

# A frontmatter field and nothing else: a form filled in, not a thing said.
check("bare field", L.occurrence_class(Path("SCORE.md"), f"composts_into: {TARGET}\n", TARGET), "field")
check("quoted field", L.occurrence_class(Path("SCORE.md"), f'work_line: "{TARGET}"\n', TARGET), "field")

# One sentence anywhere in the file outranks any number of fields.
check("field plus sentence",
      L.occurrence_class(Path("SCORE.md"),
                         f"composts_into: {TARGET}\n\nThis study tests a clause {TARGET} left open.\n",
                         TARGET),
      "prose")

# Running text alone.
check("prose", L.occurrence_class(Path("DECISION.md"), f"It composts into {TARGET} as material.", TARGET), "prose")

# Generated tables are never prose, whatever they contain.
check("json", L.occurrence_class(Path("data.json"), f'  "work": "{TARGET}",', TARGET), "data")
check("csv", L.occurrence_class(Path("d.csv"), f"a,{TARGET},3", TARGET), "data")

# Slug boundaries: a slug must not match inside a longer one (METHOD.md § Edges).
pat = L.slug_pattern(["2026-07-16-the-wrong-sphere", "2026-07-16-the-wrong-sphere-ii"])
check("longest wins", pat.findall("see 2026-07-16-the-wrong-sphere-ii here"),
      ["2026-07-16-the-wrong-sphere-ii"])
check("short still matches", pat.findall("see 2026-07-16-the-wrong-sphere."),
      ["2026-07-16-the-wrong-sphere"])

# An edge is counted once per pair however often the slug appears.
units = {
    "a-unit": {"slug": "a-unit", "kind": "project", "date": None, "files": []},
}
check("no self edge", L.build_edges(units), {})

# The unit sources are declared, not assumed: a caller may point it at another layout.
check("args replace defaults", L.parse_args(["/tmp", "--dir", "artifacts:work"])[1], [("artifacts", "work")])
check("args keep defaults", L.parse_args([])[1], L.DEFAULT_DIRS)

if FAILED:
    for line in FAILED:
        print("FAIL:", line)
    sys.exit(1)
print(f"ok — {RUN} classifier and boundary assertions hold")
