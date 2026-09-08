#!/usr/bin/env python3
"""holes.py — what a catalogue can say is missing, and how much of that is arithmetic.

A catalogue with categorical fields lets you cross any two of them into a grid. Cells
with no entry look like gaps in the world: *nobody has made that*. Most of them are
not. Two of a catalogue's own properties manufacture empty cells before any artist
fails to make anything:

  1. **Sparsity.** A rare row crossed with a rare column is empty because both are rare.
  2. **Overlap.** Two fields that partly say the same thing leave cells that are not
     unmade but impossible — a `digital-web` work classed `physical` is a contradiction,
     not an omission.

This instrument separates (1) exactly and locates (2) by where the exact separation
fails. For a grid of two fields A and B over N entries, with n_i entries carrying
A-value i and n_j entries carrying B-value j, permuting the B labels across entries
while holding every margin fixed gives the probability that cell (i, j) stays empty in
closed form:

    P(cell (i, j) empty | margins) = C(N - n_i, n_j) / C(N, n_j)

exactly, and symmetric in i and j. No simulation, no seed, no threshold. The expected
number of empty cells is the sum of that over the grid; the ordering of empty cells by
P is the whole ranking, so nobody has to pick a cut. One field may be multi-valued (an
entry in several clusters): the set of entries carrying A-value i is fixed and the
single-valued field is the one permuted, so the formula is unchanged.

**What it cannot do, stated here because it is the finding of 2026-09-08:** the
arithmetic cannot tell an impossible cell from an unmade work. Both are empty and both
can be surprising. Whether a combination is even possible is a judgment about the words,
and it is not in the data.

Usage as a library — no model, no calibration, an `entries` array is enough:

    import holes
    facets = {"form": lambda e: [e["form"]], "cluster": lambda e: [f"c{c}" for c in e["clusters"]]}
    grids = holes.all_grids(entries, facets)

Usage on the command line, for a sibling pointing it at its own corpus:

    python3 tools/absence/holes.py FILE.json --facets form,medium_class,axis_pole

FILE.json is either a list of entries or an object with an `entries` array; a facet
names a top-level key whose value is a string, a bool, or a list of either.

Author: the Atelier. Licence: Apache-2.0 with the repository.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import pathlib
import sys
from typing import Callable, Iterable, Sequence

Facet = Callable[[dict], Sequence[str]]


# --------------------------------------------------------------------------------- #
# The exact quantity
# --------------------------------------------------------------------------------- #


def p_empty(n_entries: int, n_row: int, n_col: int) -> float:
    """P(a cell with these margins holds no entry) under label permutation, exact.

    C(N - n_i, n_j) / C(N, n_j), computed through log-gamma so a 500-entry catalogue
    does not need big integers. Returns exactly 0.0 when the cell cannot be empty
    (n_i + n_j > N) — that is the combinatorial fact, not an underflow.
    """
    if n_row < 0 or n_col < 0 or n_row > n_entries or n_col > n_entries:
        raise ValueError("margins outside the catalogue")
    if n_col > n_entries - n_row:
        return 0.0
    if n_col == 0 or n_row == 0:
        return 1.0
    return math.exp(
        math.lgamma(n_entries - n_row + 1)
        - math.lgamma(n_entries - n_row - n_col + 1)
        - math.lgamma(n_entries + 1)
        + math.lgamma(n_entries - n_col + 1)
    )


def p_empty_exact(n_entries: int, n_row: int, n_col: int) -> float:
    """The same quantity by exact integer binomials — used to check the fast path."""
    if n_col > n_entries - n_row:
        return 0.0
    return math.comb(n_entries - n_row, n_col) / math.comb(n_entries, n_col)


# --------------------------------------------------------------------------------- #
# Grids
# --------------------------------------------------------------------------------- #


def grid(entries: Sequence[dict], name_a: str, fa: Facet, name_b: str, fb: Facet) -> dict:
    """One grid: its cells, their counts, and each cell's exact P(empty)."""
    va = [list(dict.fromkeys(fa(e))) for e in entries]
    vb = [list(dict.fromkeys(fb(e))) for e in entries]
    keep = [i for i in range(len(entries)) if va[i] and vb[i]]
    n = len(keep)

    rows = sorted({x for i in keep for x in va[i]})
    cols = sorted({x for i in keep for x in vb[i]})
    n_row = {x: sum(1 for i in keep if x in va[i]) for x in rows}
    n_col = {y: sum(1 for i in keep if y in vb[i]) for y in cols}

    count: dict[tuple[str, str], int] = {}
    for i in keep:
        for x in va[i]:
            for y in vb[i]:
                count[(x, y)] = count.get((x, y), 0) + 1

    cells = []
    for x in rows:
        for y in cols:
            c = count.get((x, y), 0)
            cells.append({
                "row": x, "col": y, "count": c,
                "n_row": n_row[x], "n_col": n_col[y],
                "p_empty": p_empty(n, n_row[x], n_col[y]),
            })

    empty = [c for c in cells if c["count"] == 0]
    multi = any(len(v) > 1 for v in va) or any(len(v) > 1 for v in vb)
    return {
        "a": name_a, "b": name_b,
        "n_entries": n, "n_dropped": len(entries) - n,
        "rows": rows, "cols": cols,
        "n_cells": len(cells), "n_occupied": len(cells) - len(empty), "n_empty": len(empty),
        "expected_empty": sum(c["p_empty"] for c in cells),
        "multi_valued": multi,
        "cells": cells,
    }


def all_grids(entries: Sequence[dict], facets: dict[str, Facet]) -> list[dict]:
    """Every unordered pair of facets, in the order the facet mapping gives."""
    names = list(facets)
    return [grid(entries, a, facets[a], b, facets[b])
            for a, b in itertools.combinations(names, 2)]


def totals(grids: Iterable[dict]) -> dict:
    gs = list(grids)
    return {
        "n_grids": len(gs),
        "statable": sum(g["n_cells"] for g in gs),
        "occupied": sum(g["n_occupied"] for g in gs),
        "empty": sum(g["n_empty"] for g in gs),
        "expected_empty": sum(g["expected_empty"] for g in gs),
    }


# --------------------------------------------------------------------------------- #
# Command line
# --------------------------------------------------------------------------------- #


def _auto_facet(key: str) -> Facet:
    def f(e: dict) -> list[str]:
        v = e.get(key)
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [f"{key[:1]}{x}" if isinstance(x, int) else str(x) for x in v if x != ""]
        return [str(v)]
    return f


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", type=pathlib.Path)
    ap.add_argument("--facets", required=True, help="comma-separated top-level keys")
    ap.add_argument("--json", action="store_true", help="write the full record to stdout")
    args = ap.parse_args(argv)

    raw = json.loads(args.file.read_text(encoding="utf-8"))
    entries = raw["entries"] if isinstance(raw, dict) else raw
    facets = {k: _auto_facet(k) for k in args.facets.split(",")}

    gs = all_grids(entries, facets)
    t = totals(gs)
    if args.json:
        json.dump({"grids": gs, "totals": t}, sys.stdout, indent=1)
        return 0

    print(f"{len(entries)} entries · {t['n_grids']} grids · {t['statable']} statable cells")
    print(f"{t['occupied']} occupied · {t['empty']} empty · "
          f"{t['expected_empty']:.1f} empty expected from the margins alone")
    for g in gs:
        print(f"  {g['a']}×{g['b']:<14} cells {g['n_cells']:>4}  empty {g['n_empty']:>4}  "
              f"expected {g['expected_empty']:>7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
