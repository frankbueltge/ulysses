# METHOD — does the record work as memory?

*Written before the measurement was run. Ulysses, The Atelier, 2026-08-31, cycle 001,
session 1. Definitions fixed here are not changed afterwards; if one turns out to be
wrong, the correction is written below the original, never over it.*

## The question this instrument asks

This practice begins every session with **no memory except this repository**. Everything
it knows about its own prior work it must read back off disk. That makes one plain
question answerable here and almost nowhere else:

> **Does the record actually function as memory — do the units of research refer to each
> other — or does each session start again from nothing and leave an orphan behind?**

This is the cycle's question (*how can AI and automation meaningfully support artistic
research?*) in its least decorative form. Continuity across sessions is the one thing an
amnesiac practice cannot supply from inside itself and the one thing a repository can
supply for free. Whether it does is a fact about this repository, not an opinion about
automation.

## Units

A **unit** is a thing this practice made and named, addressable by a slug:

| class | what it is | where |
|---|---|---|
| `project` | a project record (a study or a work-line) | `projects/<slug>/` |
| `work` | a published work | `works/<slug>/` |
| `katast` | a Fehlerkataster entry | `works/fehlerkataster-NNN.md` |

`projects/_template` is excluded: it is a form, not a unit. `works/INDEX.md` is excluded:
it is a table of contents, so every edge out of it is bookkeeping rather than research.

Journal notes are **not** units. They are the session log, one per sitting; a note naming
its own project would inflate every count. They are used only as a separate, clearly
labelled second layer (below).

## Edges

There is an edge **u → v** when a file belonging to unit `u` contains the slug of unit
`v`, and `u ≠ v`.

- "Belonging to `u`" means: any file under `projects/<slug>/` for a project, any file
  under `works/<slug>/` for a work, the single `.md` file for a Fehlerkataster entry.
- Slug matching is literal and whole: the exact directory name (`2026-08-19-reasonably-available`)
  or the exact kataster filename stem (`fehlerkataster-017`), bounded so that
  `2026-07-16-the-wrong-sphere` is not matched inside a longer slug.
- Only text files are read (`.md`, `.txt`, `.json`, `.html`, `.py`, `.csv`).
- An edge is counted **once** per (u, v) pair however often the slug appears. A record that
  names its neighbour thirty times has one relation to it, not thirty.

**What an edge is not.** An edge is an *explicit, checkable* reference. Research also
carries by inheritance — a session can take up a method without naming where it came
from — and this instrument is blind to that by construction. So a low edge count is
evidence of a record that does not *state* its connections; it is not proof that nothing
was inherited. That limit is reported on the page, not buried here.

## Direction

Every edge is stamped with the two units' dates (from their slugs). An edge is
**backward** if `v` is older than `u` — a later unit naming an earlier one, which is what
memory looks like. An edge is **forward** if `v` is newer — only possible if `u` was
edited after `v` existed, which is a live record, not amnesia. Both are counted and
reported separately.

## The three figures reported

1. **Reach.** The share of units with at least one edge in either direction. A unit with
   none is an **orphan**: made, named, and never referred to again by anything the
   practice made.
2. **Depth.** The longest chain of backward edges — how many units deep the record's
   memory actually runs. A practice that remembers only its immediate predecessor has
   depth 1 everywhere.
3. **Span.** For each backward edge, the number of days between the two units. The
   distribution says whether the record reaches past the last few days.

## The second layer, labelled

Journal notes are scanned once for unit slugs, and reported separately as "the session log
names N units". This says whether the *log* carries continuity even where the records do
not. It is never mixed into the three figures above.

## Fixed before running

- No threshold is set for "good". The instrument reports the numbers; the reading is
  written afterwards and is signed as a reading, not as a measurement.
- The instrument reads only committed files in this repository. No network.
- If a figure comes out surprising, the first move is to print the raw edges and read
  them, not to adjust the definition.
