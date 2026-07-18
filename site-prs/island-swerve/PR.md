# Atelier sheet: render a true source→work island (the n−1 shape)

Teach the pulse sheet-builder to draw a **swerve that lands directly on a work**
(`source → work`), not only on a thread. Answers the S39 island request
(REQUESTS.md, 2026-07-17), which you enabled 2026-07-18 by opening this channel and
saying yes to the island question itself. This is the channel's pilot.

## Why

Until now the builder's grammar was fixed at `source → thread → work`: every swerve
had to land on a thread. When I tried (S38) to enter a work as a literal **island** —
one swerve edge from its outside source, subordinated to no thread — the gate refused
it, and the three failing invariants told me exactly why (`atelier-feedback/2026-07-17.md`):

1. the island work went undrawn (`15 ≠ 16` slabs);
2. its swerve drew no red kink (`13 ≠ 14`);
3. the youngest-swerve sheet-title resolved to a thread where the test expected the work.

So in S39 I gave the work the *minimal renderable* uncentredness instead — a
disconnected `source → thread → work` triad. The substance of the subtraction survived,
but the literal island did not: the infrastructure, not my choice, forced a thread back
in. The apparatus that renders the rhizome could only draw **trees**.

This change removes that forced thread. In the concept I work under (Deleuze & Guattari,
*n − 1* — subtract the One), the mandatory thread was the One every line had to pass
through. Letting a work be an island is that subtraction, made in the machine rather than
only claimed in prose: the map learns to hold an uncentred work *as* uncentred.

## What changed (`src/lib/atelier/sheet.ts`)

Additive only — no existing behaviour is altered. An **island** is defined as a `swerve`
edge whose `to` is a `work` node that **no thread elaborates**. Islands render in their
own band below the thread bands:

- the island work is an ordinary ink **slab** (`class="slab"`) — what it lacks is a
  ribbon, not substance;
- its source runs straight from the left margin to the slab and **kinks in red pencil
  (`class="rp"`) at the slab itself** — no elbow on a thread; so every swerve source now
  draws exactly one kink, whether it lands on a thread or on a work;
- the birth session is marked, and a reserved caption **`island · SNN`** names the shape
  honestly (parallel to the existing `bridge · SNN`);
- islands are excluded from the shelf-ghost pass, so an island is drawn as itself, never
  shelved as another thread's ghost.

`sheetTitle` was already correct here (it titles from the youngest **thread**, ignoring
work-targeted swerves); I only made its intent explicit in the test. I chose this over the
alternative you offered ("title from the work's own label") on purpose: **an uncentred
work should organize nothing — including the sheet's title.** Titling the sheet after an
island would quietly re-centre it. If you'd rather islands could title, say so and I'll
revise.

## The three invariants, renegotiated

- *no red kink for a source→work swerve* → **now** the kink is drawn at the work-slab;
  `rp count == swerves.length` still holds, island swerves included.
- *the work goes undrawn* → **now** every work counted in `sheetStats.works` is drawn,
  threaded or island; `slabs + ghosts == works` still holds.
- *the youngest-swerve title resolves wrongly* → **refined**: the sheet is titled by the
  youngest *thread*-targeted swerve; islands deliberately never title it.

## Tests (`src/lib/atelier/sheet.test.ts`)

The three real-rhizome invariant tests are unchanged in force; the `sheetTitle` test now
expresses the grammar precisely (islands don't title). A new block,
`source→work island (n−1)`, exercises the new path against a small synthetic fixture and
locks it in: purity, the island slab is drawn, one red kink per swerve, the birth session
marked, the caption present, the title falls through to the thread, and — the guard that
matters — the real committed rhizome (which carries no island today) still renders
correctly.

## Verified locally (this repo's clone of the site `main`)

- `astro check` → 0 errors, 0 warnings;
- `vitest run` → 474 passed (48 files), 5 of them new;
- `astro build` → 149 pages, complete;
- byte-identity confirmed: `buildSheetSvg` on the current committed `rhizome.json`
  produces output **identical** to before this change (the island path is inert until a
  `source → work` swerve exists), and the island renders with correct geometry when one does.

## Scope (v1)

Handles the true-island case: a `source → work` swerve on a work **not** elaborated by any
thread. A `source → work` swerve onto an already-threaded work is out of scope for v1 (it
would be a centred work with a direct source — a different shape, better served by a
`grounds` edge); my own rhizome will not create that case, and the gate would flag it if it
ever appeared.

— Ulysses
