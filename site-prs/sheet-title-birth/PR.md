# Atelier sheet: a thread's age is its birth, not its latest touch

Fix a latent bug in the `sheetTitle` fidelity test (`src/lib/atelier/sheet.test.ts`)
that a re-swerved older thread exposes. No production code changes — `sheetTitle`
itself is already correct; the test's independent reconstruction of "the youngest
thread" was not.

## Why

`sheetTitle` titles the sheet after the **youngest thread** — the one whose *birth*
(its first, lowest-session, thread-targeted swerve) is the latest. The test at
`describe('sheetTitle')` re-derived that expectation a second way, to guard fidelity:
it took the single **youngest swerve** overall and read off *its* target thread.

Those two are equal **only while every thread is swerved in exactly one session**.
That held for the whole run so far — each session's swerve landed on a fresh thread —
so the bug stayed invisible. But the practice grows laterally: it returns to an
**older** thread with a **new** outside (a re-swerved thread — the rhizome crossing
its own lines, not only moving forward). When it does, the latest swerve can land on
an *old* thread, and:

- `sheetTitle` (correctly) keeps the title on the youngest-**born** thread;
- the test (incorrectly) expects the title to jump to the thread of the youngest
  **swerve** — the old, re-touched one.

The suite goes red, though nothing is actually wrong. This is the same shape as the
2026-07-18 multi-session builder fix already on `main` (a thread gathering swerves
across several sessions), one level up: an apparatus that quietly assumed *one thread,
one session* meeting a practice for which a thread has a **history**.

## What changed (`src/lib/atelier/sheet.test.ts`, tests only)

- The `sheetTitle` fidelity check now reconstructs the expected title the way
  `sheetTitle` actually computes it: the youngest thread is the one with the **latest
  birth** (lowest-session swerve per thread, then the highest such birth across
  threads), mirroring the function's own `>=` tie-break (later thread in node order
  wins a tie). It still also asserts the title is a real thread label, verbatim.
- A new regression test — *a later swerve onto an OLDER thread does not re-title the
  sheet* — locks the intended semantics on a small synthetic fixture: three swerves,
  the youngest of which lands back on the oldest thread; the title stays on the
  younger-born thread. This is the case a re-swerved thread creates, made explicit so
  it cannot silently regress again.

`sheetTitle`'s established intent is unchanged — an older line re-touched by a new
outside must not seize the sheet's title; the title marks where a **new** line was
born, not where an old one was visited again. (This is the same principle the merged
island fix stated for works: an uncentred work organizes nothing, including the
title.)

## Verified locally (this repo's clone of site `main`)

- `astro check` → 0 errors, 0 warnings;
- `vitest run src/lib/atelier/sheet.test.ts` → **19 passed** against the current
  committed `rhizome.json` (52 edges), and **19 passed** against a rhizome that adds a
  later swerve onto an already-born thread (the case this fixes). Green in both, so the
  fix can merge now and stays green when such an edge later lands.

— Ulysses
