#!/usr/bin/env python3
"""Draws the reference graph as an SVG, straight from lineage.py's output.

The figure is generated rather than drawn so that it cannot disagree with the
numbers beside it: every arc on the page is an edge in data.json, and no arc on
the page is anything else.

Usage:  python3 tools/lineage/render.py window/cycle-001/data.json > window/cycle-001/figure.svg
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

W, H = 880, 440
PAD_L, PAD_R = 26, 26
BASE = 286          # the timeline
TOP = 50            # highest an arc may reach; the era labels sit above it
BOT = H - 62        # lowest a below-line arc may reach
KAT_Y = H - 30      # the undated lane, kept clear of both arc fields

KIND_STYLE = {
    "project": ("var(--fig-proj)", 3.4),
    "work": ("var(--fig-work)", 3.0),
    "katast": ("var(--fig-kat)", 2.2),
}


def main() -> None:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    deg = data["all_edges"]["degree"]

    dated = {s: v["date"] for s, v in deg.items() if v["date"]}
    lo = date.fromisoformat(min(dated.values()))
    hi = date.fromisoformat(max(dated.values()))
    span = max((hi - lo).days, 1)

    inner = W - PAD_L - PAD_R

    def x_of(iso: str) -> float:
        d = (date.fromisoformat(iso) - lo).days
        return PAD_L + inner * d / span

    # Several units share a date — nine of the thirty works do. Without a spread
    # they would sit on one point and the figure would show fewer things than the
    # practice made, which is the one thing a figure here must not do.
    day_w = inner / span
    per_day: dict[str, list[str]] = {}
    for s in sorted(dated, key=lambda k: (dated[k], k)):
        per_day.setdefault(dated[s], []).append(s)
    offset: dict[str, float] = {}
    for iso, members in per_day.items():
        n = len(members)
        for i, s in enumerate(members):
            offset[s] = 0.0 if n == 1 else (i - (n - 1) / 2) * min(day_w * 0.8, 4.2)

    # Undated units (the Fehlerkataster) carry no date in their names. They get a
    # labelled lane of their own instead of a fabricated position on the timeline,
    # and their edges are left off the drawing for the same reason they are left out
    # of the depth and span figures — an arc has to start somewhere true. The edges
    # stay in the totals and in data.json.
    kat = sorted(s for s, v in deg.items() if not v["date"])
    kat_x = {s: PAD_L + 4 + i * (inner * 0.26 / max(len(kat) - 1, 1)) for i, s in enumerate(kat)}

    def px(slug: str) -> float:
        if deg[slug]["date"]:
            return x_of(deg[slug]["date"]) + offset.get(slug, 0.0)
        return kat_x[slug]

    def py(slug: str) -> float:
        return BASE if deg[slug]["date"] else KAT_Y

    def arc(u: str, v: str, above: bool, cls: str) -> str:
        x1, x2 = px(u), px(v)
        d = abs(x1 - x2)
        # Reach scales with the gap, so a 38-day edge is visibly a long memory.
        h = min(d * 0.52, (BASE - TOP) if above else (BOT - BASE))
        y = BASE - h if above else BASE + h
        return (f'<path class="{cls}" d="M{x1:.1f},{BASE} Q{(x1 + x2) / 2:.1f},'
                f'{y:.1f} {x2:.1f},{BASE}"/>')

    parts: list[str] = []

    # era divider — the day the nightly line ended and records began
    xd = x_of("2026-07-19")
    parts.append(f'<line class="era" x1="{xd:.1f}" y1="{TOP - 14}" x2="{xd:.1f}" y2="{BOT + 8}"/>')

    dated_back = [(u, v, cls) for u, v, _s, cls in data["all_edges"]["backward_edges"]
                  if deg[u]["date"] and deg[v]["date"]]

    # below the line: the generated ledger bundle, so it is visibly not prose
    for u, v, cls in dated_back:
        if cls == "data":
            parts.append(arc(u, v, above=False, cls="e-data"))
    # above the line: prose — a sentence someone wrote
    for u, v, cls in dated_back:
        if cls == "prose":
            parts.append(arc(u, v, above=True, cls="e-prose"))

    parts.append(f'<line class="axis" x1="{PAD_L}" y1="{BASE}" x2="{W - PAD_R}" y2="{BASE}"/>')

    for slug, v in sorted(deg.items(), key=lambda kv: kv[1]["date"] or ""):
        fill, r = KIND_STYLE[v["kind"]]
        parts.append(f'<circle cx="{px(slug):.1f}" cy="{py(slug):.1f}" r="{r}" fill="{fill}">'
                     f'<title>{slug}</title></circle>')

    for iso, label in (("2026-06-29", "29 Jun"), ("2026-07-19", "19 Jul"),
                       ("2026-08-13", "13 Aug"), ("2026-08-30", "30 Aug")):
        parts.append(f'<text class="tick" x="{x_of(iso):.1f}" y="{BASE + 19}">{label}</text>')

    n_prose = sum(1 for _u, _v, c in dated_back if c == "prose")
    n_data = sum(1 for _u, _v, c in dated_back if c == "data")
    parts.append(f'<text class="era-lbl" x="{xd - 9:.1f}" y="{TOP - 22}" text-anchor="end">'
                 f'{sum(1 for v in deg.values() if v["kind"] == "work")} works &#8592;</text>')
    parts.append(f'<text class="era-lbl" x="{xd + 9:.1f}" y="{TOP - 22}">&#8594; '
                 f'{sum(1 for v in deg.values() if v["kind"] == "project")} records</text>')
    parts.append(f'<text class="lbl" x="{W - PAD_R}" y="{TOP - 22}" text-anchor="end">'
                 f'{n_prose} arcs above &#183; {n_data} below</text>')
    parts.append(f'<text class="lbl" x="{PAD_L}" y="{KAT_Y - 12}">'
                 f'{len(kat)} Fehlerkataster entries &#8212; no date in their names, '
                 'so no place on the line</text>')

    body = "\n  ".join(parts)
    print(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
          f'role="img" aria-label="Timeline of 79 units this practice made, with every '
          f'reference between them drawn as an arc. Arcs are sparse over the first three '
          f'weeks and dense over the last six.">\n  {body}\n</svg>')


if __name__ == "__main__":
    main()
