#!/usr/bin/env python3
"""Does the record work as memory?

Reads this repository and computes the reference graph between the units the
practice made and named: project records, published works, Fehlerkataster
entries. Definitions are fixed in METHOD.md beside this file and are not
changed here.

Usage
-----
    python3 tools/lineage/lineage.py [repo-root] > data.json

This practice's own layout is the default. The two sibling practices keep their
made things in differently named places, so the units are declared rather than
assumed — an instrument that only fits the repository it was born in is not a
support, it is a habit:

    --dir  <path>:<kind>    every SUBDIRECTORY of <path> is a unit of that kind
    --glob <pattern>:<kind> every FILE matching <pattern> is a unit of that kind

    # The Field, whose works land in artifacts/ and works/:
    python3 lineage.py ../field-research --dir works:work --dir artifacts:work

Giving any --dir or --glob replaces the defaults entirely.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict, deque
from datetime import date
from pathlib import Path

DEFAULT_DIRS = [("projects", "project"), ("works", "work")]
DEFAULT_GLOBS = [("works/fehlerkataster-*.md", "katast")]

TEXT_SUFFIXES = {".md", ".txt", ".json", ".html", ".py", ".csv"}
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-")


def unit_date(slug: str) -> str | None:
    m = DATE_RE.match(slug)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def collect_units(root: Path, dirs=DEFAULT_DIRS, globs=DEFAULT_GLOBS) -> dict[str, dict]:
    """Every unit, with the files that belong to it. See METHOD.md § Units."""
    units: dict[str, dict] = {}

    for rel, kind in dirs:
        base = root / rel
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            # A name starting with `_` is a form, not a unit (`projects/_template`).
            if not d.is_dir() or d.name.startswith("_"):
                continue
            units[d.name] = {"slug": d.name, "kind": kind, "date": unit_date(d.name),
                             "files": sorted(p for p in d.rglob("*") if p.is_file())}

    for pattern, kind in globs:
        for f in sorted(root.glob(pattern)):
            if f.is_file() and f.stem not in units:
                # A Fehlerkataster slug carries no date; it is drawn in a lane of its
                # own and left out of depth and span rather than given a made-up one.
                units[f.stem] = {"slug": f.stem, "kind": kind, "date": unit_date(f.stem),
                                 "files": [f]}

    # An index or table of contents is excluded by METHOD.md: every edge out of it
    # would be bookkeeping, and it would look like the best-connected thing here.
    return units


def read_text(path: Path) -> str:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def slug_pattern(slugs: list[str]) -> re.Pattern:
    """One alternation, longest first, with boundaries that stop a slug matching
    inside a longer slug (METHOD.md § Edges)."""
    if not slugs:
        return re.compile(r"(?!)")  # matches nothing, rather than everything
    ordered = sorted(slugs, key=len, reverse=True)
    body = "|".join(re.escape(s) for s in ordered)
    return re.compile(rf"(?<![0-9A-Za-z-])({body})(?![0-9A-Za-z-])")


# —————————————————————————————————————————————— the refinement of 2026-08-31 ——
# Added after the first run and after reading the raw edges, as METHOD.md § Fixed
# before running requires. It does not change a single edge or figure above; it
# SPLITS them. Reading the edges showed two bundles that the word "reference" was
# quietly covering over: a machine-written ledger inside one work naming twenty-two
# predecessors, and a frontmatter field (`composts_into:`) that every study of one
# arc carries by form. Both are real relations. Neither is an act of recall — a
# record does not remember a thing because a form has a slot for it. So each
# occurrence gets a class, and the edge takes the strongest class it has anywhere.
STRENGTH = {"prose": 3, "field": 2, "data": 1}


def occurrence_class(path: Path, text: str, target: str) -> str:
    """prose — the slug stands in running text, someone wrote it into a sentence.
    field — every occurrence in this file is the bare value of a metadata key
            (`composts_into: <slug>`), i.e. a form filled in, not a thing said.
    data  — the slug sits in a generated .json/.csv table."""
    if path.suffix.lower() in {".json", ".csv"}:
        return "data"
    esc = re.escape(target)
    total = len(re.findall(rf"(?<![0-9A-Za-z-]){esc}(?![0-9A-Za-z-])", text))
    bare = len(re.findall(rf"^\s*[a-z_]+\s*:\s*[`\"']?{esc}[`\"']?\s*$", text, re.M))
    # One sentence anywhere in the file outranks any number of filled-in fields.
    return "field" if total and bare >= total else "prose"


# ————————————————————————————————————————————— the refinement of 2026-09-01 ——
# Added after running the instrument on two sibling repositories and reading the raw
# edges, as METHOD.md § Fixed before running requires. It changes nothing in the
# 2026-08-31 measurement, whose units all carry long descriptive slugs. It matters
# only where a unit's whole slug is a bare date — `journal/2026-07-18.md`. Such a slug
# is not a name: it matches every mention of that day in any sentence, so "sixteen days
# before this night, 2026-08-14" was being counted as a reference to a note. A unit that
# cannot be named except by naming a date is unaddressable, and is therefore not a
# possible target of an edge. It stays a unit and can still be a source.
BARE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def unaddressable(slug: str) -> bool:
    return bool(BARE_DATE_RE.match(slug))


def build_edges(units: dict[str, dict]) -> dict[tuple[str, str], str]:
    pattern = slug_pattern([s for s in units if not unaddressable(s)])
    edges: dict[tuple[str, str], str] = {}
    for slug, unit in units.items():
        for f in unit["files"]:
            text = read_text(f)
            if not text:
                continue
            for hit in set(pattern.findall(text)):
                if hit == slug:
                    continue
                cls = occurrence_class(f, text, hit)
                key = (slug, hit)
                if key not in edges or STRENGTH[cls] > STRENGTH[edges[key]]:
                    edges[key] = cls
    return edges


def longest_backward_chain(units: dict[str, dict], edges) -> list[str]:
    """Longest path over backward edges only. Backward edges point strictly into the
    past, so the graph is acyclic and a simple longest-path DP is exact."""
    back: dict[str, list[str]] = defaultdict(list)
    for u, v in edges:
        du, dv = units[u].get("date"), units[v].get("date")
        if du and dv and dv < du:
            back[u].append(v)

    memo: dict[str, list[str]] = {}

    def walk(node: str) -> list[str]:
        if node in memo:
            return memo[node]
        memo[node] = [node]  # guards against a cycle from equal dates slipping through
        best: list[str] = []
        for nxt in back.get(node, []):
            cand = walk(nxt)
            if len(cand) > len(best):
                best = cand
        memo[node] = [node] + best
        return memo[node]

    return max((walk(n) for n in units), key=len, default=[])


def components(units: dict[str, dict], edges) -> list[list[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    seen: set[str] = set()
    out: list[list[str]] = []
    for n in units:
        if n in seen:
            continue
        comp, q = [], deque([n])
        seen.add(n)
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nb in adj[cur]:
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        out.append(sorted(comp))
    return sorted(out, key=len, reverse=True)


def journal_layer(root: Path, units: dict[str, dict]) -> dict:
    """The second layer, kept separate on purpose (METHOD.md § The second layer)."""
    jdir = root / "journal"
    if not jdir.is_dir():
        return {"notes": 0, "notes_naming_a_unit": 0, "units_named": 0}
    pattern = slug_pattern([s for s in units if not unaddressable(s)])
    notes = sorted(p for p in jdir.glob("*.md") if p.is_file())
    named: set[str] = set()
    with_hit = 0
    for p in notes:
        hits = set(pattern.findall(read_text(p)))
        if hits:
            with_hit += 1
            named |= hits
    return {"notes": len(notes), "notes_naming_a_unit": with_hit, "units_named": len(named),
            "units_total": len(units)}


def summarise(units: dict[str, dict], edges: dict[tuple[str, str], str]) -> dict:
    """All figures for one edge set. Called twice: once on every edge, once on the
    prose edges alone — the same instrument, read at two strengths."""
    indeg: dict[str, int] = defaultdict(int)
    outdeg: dict[str, int] = defaultdict(int)
    for u, v in edges:
        outdeg[u] += 1
        indeg[v] += 1

    orphans = sorted(s for s in units if indeg[s] == 0 and outdeg[s] == 0)

    backward, forward, undated = [], [], []
    for u, v in sorted(edges):
        du, dv = units[u].get("date"), units[v].get("date")
        cls = edges[(u, v)]
        if not du or not dv:
            undated.append([u, v, cls])
        elif dv < du:
            span = (date.fromisoformat(du) - date.fromisoformat(dv)).days
            backward.append([u, v, span, cls])
        elif dv > du:
            forward.append([u, v, cls])
        else:
            backward.append([u, v, 0, cls])

    chain = longest_backward_chain(units, edges)
    comps = components(units, edges)
    spans = sorted(e[2] for e in backward)

    by_kind: dict[str, dict] = {}
    for kind in ("project", "work", "katast"):
        members = [s for s, u in units.items() if u["kind"] == kind]
        by_kind[kind] = {
            "count": len(members),
            "orphans": sorted(s for s in members if s in orphans),
            "with_edge": sum(1 for s in members if indeg[s] or outdeg[s]),
        }

    by_class: dict[str, int] = defaultdict(int)
    for cls in edges.values():
        by_class[cls] += 1

    return {
        "generated": date.today().isoformat(),
        "method": "tools/lineage/METHOD.md",
        "units": {"total": len(units), "by_kind": by_kind},
        "edges": {
            "total": len(edges),
            "backward": len(backward),
            "forward": len(forward),
            "undated": len(undated),
        },
        "reach": {
            "units_with_at_least_one_edge": len(units) - len(orphans),
            "orphans": orphans,
            "orphan_count": len(orphans),
        },
        "depth": {"longest_backward_chain": chain, "length": max(len(chain) - 1, 0)},
        "span_days": {
            "min": spans[0] if spans else None,
            "median": spans[len(spans) // 2] if spans else None,
            "max": spans[-1] if spans else None,
            "over_7": sum(1 for s in spans if s > 7),
            "all": spans,
        },
        "components": {"count": len(comps), "largest": len(comps[0]) if comps else 0,
                       "sizes": [len(c) for c in comps]},
        "edges_by_class": dict(by_class),
        "degree": {s: {"in": indeg[s], "out": outdeg[s], "kind": units[s]["kind"],
                       "date": units[s]["date"]} for s in sorted(units)},
        "backward_edges": backward,
        "forward_edges": forward,
        "undated_edges": undated,
    }


def parse_args(argv: list[str]) -> tuple[Path, list, list]:
    root, dirs, globs = None, [], []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--dir", "--glob"):
            spec = argv[i + 1]
            target, _, kind = spec.rpartition(":")
            if not target:
                raise SystemExit(f"{a} wants <path>:<kind>, got {spec!r}")
            (dirs if a == "--dir" else globs).append((target, kind))
            i += 2
        elif root is None:
            root, i = Path(a), i + 1
        else:
            raise SystemExit(f"unexpected argument {a!r}")
    base = (root or Path(__file__).resolve().parents[2]).resolve()
    # Declaring any unit source replaces the defaults: a caller who says where the
    # units are should not silently also get this repository's own two folders.
    if dirs or globs:
        return base, dirs, globs
    return base, DEFAULT_DIRS, DEFAULT_GLOBS


def main() -> None:
    root, dirs, globs = parse_args(sys.argv[1:])
    units = collect_units(root, dirs, globs)
    if not units:
        raise SystemExit(f"no units found under {root} — declare them with --dir/--glob")
    edges = build_edges(units)
    prose_only = {k: v for k, v in edges.items() if v == "prose"}

    out = {
        "generated": date.today().isoformat(),
        "method": "tools/lineage/METHOD.md",
        "repository": root.name,
        "unit_sources": {"dirs": dirs, "globs": globs},
        "unaddressable_units": sorted(s for s in units if unaddressable(s)),
        "all_edges": summarise(units, edges),
        "prose_edges_only": summarise(units, prose_only),
        "journal_layer": journal_layer(root, units),
    }
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
