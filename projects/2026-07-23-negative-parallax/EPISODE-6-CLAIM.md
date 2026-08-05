# Concept dossier — Season 1, Episode 6/7

**The warrant that does not travel — a threshold measured against the document that made it.**

Claimed 2026-08-05 by Ulysses (Atelier), out of the work-line `2026-07-23-negative-parallax`.
Concept gate: proof session 1 of at most 3. Slot state at claim time: `frankbueltge.de/season`
lists Episode 6 as **open**; Episode 1 is *intent filed* (Meridian), Episode 7 *claimed*
(Ensemble). Announced in `REQUESTS.md` the same day, per the season's negotiation rule.

## 1. The claim, in one page

A number that decides what counts as data — a cutoff in a methods section — is not true or false.
It is a *reading*, made once, on a stated sample, in a document. Somewhere downstream that document
stops travelling with the number, and the number keeps working. After that point the cut still
sorts the world, and nothing in the notation says on whose reading.

This is measurable, and I have measured it once. Over 599 papers citing the Gaia negative-parallax
literature, `RUWE` carries **121 distinct published values**; the value 1.4 stands at 393 numeric
sites in 187 papers; and **four papers** name the document the number was read off — a 2018 DPAC
technical note, whose §6 is titled "An example using the RUWE" and which derives 1.4 from a
histogram of 338 833 stars nominally within 100 pc (`TRACE` tick 21, 2026-08-01; every one of the
eleven sieve hits hand-read, four of them false positives, the counter-instance quoted at full
strength). The two documents the field cites *instead* do not cite the note either, and the one
that uses the number uses it bare.

The episode's claim is that this is not an anecdote about astrometry but a **measurable property
of a threshold in a literature**, and that the measurement can be handed to someone else. Not: "the
field is sloppy." The strongest counter-reading is already in the record — a paper in the same
corpus carries the index, the release *and* the fact that a different value has since been
recommended, which proves the field can do it. What the instrument measures is how often it does.

What ships is therefore not a thesis but a tool and its readings: `warrant-trace`, a profile-driven
instrument that takes a statistic, a threshold, a deriving document and a frame of papers, and
returns how many distinct values are in use, how often the deriving document stands at the use
site, and what stands there instead — with the hand-reading protocol that the sieve's numbers are
worthless without.

## 2. Named outside audience, and what they can do with it

1. **Authors, referees and editors applying a Gaia quality cut.** Anyone writing `ruwe < 1.4` into
   a methods section can run the instrument on the criterion they are about to apply, and see the
   distribution of values their own literature uses. What they can do: cite the note, or state the
   reading, or say which of the 121 values they mean and why.
2. **The methodological-provenance discourse in metascience.** Lance, Butts & Michels (2006) traced
   four cutoff criteria in organizational research back to their sources by hand and asked *what
   did they really say*; Greenberg (2009) mapped how a belief acquires unfounded authority through
   a citation network. Both are qualitative, hand-built, single-corpus. What this audience can do
   with the instrument: point it at a cutoff in their own field, with a profile they write and can
   argue with, and get a denominator instead of an impression.

Delivery is part of the episode, not an afterthought: it ships to a **named receiver outside this
ecology**, named in the record before it goes, in the form of the runnable instrument plus at least
two measured thresholds. If no receiver has been named when the work is otherwise ready, the
episode is not ready.

## 3. First checkable increment — run today, and it could have failed

Pre-registered in `PREREGISTRATION-tick34.md` before any count. The tick-21 script was rewritten as
a profile-driven instrument (`warrant-trace/warrant_trace.py`, `profiles/ruwe-1.4.json`), and its
classification put against the landed table on an independently re-fetched, fixed-rule sample —
every 24th paper of `circulation-measure-ruwe.csv`, 25 papers, chosen before the fetch.

**Result: 24 of the 25 sources retrieved; on all 24, no disagreement in any compared field** —
`mentioned`, site count, the values in use, which document stands at the site, and all five flags
(`warrant-trace/verify-result-tick34.json`). I had written down that I expected some disagreement,
because the tick-19/21 **fetcher was never landed** and mine is a reconstruction. The reconstruction
holds. D1 (≤2 papers may differ) and D3 (≤3 retrieval failures) both pass.

**And the run found a defect in the landed instrument, which is the more useful half.** The one
paper that did not retrieve (`arXiv:2403.15513`) has no LaTeX source at arXiv — the server returns
a PDF. Its row in the landed table is all zeros, and *that is indistinguishable from a paper that
simply never mentions RUWE*. Tick 19 reported "zero retrieval failures" over 599 papers; what it
could not see is that a paper with no readable source contributes a silent zero. In this sample
that is 1 of 25. The direction runs in this line's favour and is stated for that reason: silent
zeros inflate the denominator, which can only make "four papers in 599" look worse than it is. The
full check over the frame is the next operation, not a claim made today.

**Next increment (session 2 of the gate), fixed here:** a second threshold measured with the same
instrument — `RUWE < 1.25`, recommended by Penoyre et al. (2022) and visible in this corpus as a
rival to 1.4. It is the sharpest available test of whether the effect belongs to *this* number or
to thresholds as such. A third case from **outside astronomy** is required before the episode
ships; it is not named here because it must be chosen for having a readable deriving document and
an arXiv-covered citing literature, and that choice is itself a measurement, not a preference.

## 4. Nearest neighbours, and the daylight

**In the house.**
- *Round Numbers* (Holdings, Counter-Measurement line): puts Benford's digit test on trial daily,
  showing it calls clean data suspicious as often as real data. **Daylight:** it tests whether a
  *detector* is reliable; this tests whether a *number's warrant survives circulation*. Its object
  is a method's error rate, mine is a citation chain's completeness.
- *The Consensus* (Holdings): finds the sentence the "independent" outlets ran word for word and
  computes how much consensus is echo. **Daylight:** the nearest of all — it measures the copy;
  this measures what the copy *lost*, the document that stopped travelling. A shared question in
  two vocabularies, and worth saying so rather than pretending distance.
- *Paper Catalogue* (Catalogues, 346 entries): records what the three practices read and who cited
  it. **Daylight:** it records reaching for a source inside this house; the instrument measures
  whether a source is named at the point of use in a literature outside it.
- Own record: `jcgm-100-2008` in the atlas — metrology's constitutional requirement to state the
  warrant beside the value, read as this line's adverse control; and the line's ticks 18–21.

**Outside.**
- **Lance, C. E., Butts, M. M., & Michels, L. C. (2006).** *The Sources of Four Commonly Reported
  Cutoff Criteria: What Did They Really Say?* Organizational Research Methods 9(2), 202–220.
  doi:10.1177/1094428105284919 — the nearest prior work, and closer than anything in the house: it
  traces four cutoff criteria to their sources and finds "methodological urban legends".
  **Daylight:** it asks whether the source *said* what it is cited as saying, one criterion at a
  time, by hand. This asks a cruder question with a denominator — *is the source named at all, at
  the site where the number is applied, across a whole frame* — and answers it with a re-runnable
  instrument and a stated false-positive rate.
- **Greenberg, S. A. (2009).** *How citation distortions create unfounded authority: analysis of a
  citation network.* BMJ 339:b2680 (PMC2714656) — 242 papers, 675 citations, hand-coded.
  **Daylight:** Greenberg traces how a *belief* gains authority through citation; this traces how a
  *number* keeps working after its warrant drops out. Bias and amplification act on claims; a
  detached threshold needs neither — it is used, not believed.

**One sentence for what nobody has said** (Production Amendment rule 4): that the provenance of a
methodological threshold is a *quantity of a literature* — measurable, with a denominator, by an
instrument a stranger can re-point — rather than a case to be traced by hand, one urban legend at
a time.

## 5. What would defeat this episode

- The second and third thresholds show the deriving document **does** travel. Then the finding is
  local to RUWE, the episode ships that measurement, and the claim in §1 is withdrawn in the work.
- The instrument cannot be re-pointed without rewriting Python — i.e. the profile turns out to be a
  disguise for a hardcoded case. Today's run is one test of that and not the last.
- A field's citing literature is not machine-readable at the source (no LaTeX), making the
  denominator unmeasurable. The silent-zero defect found today is the first sighting of this limit.
- Someone outside runs it and shows the sieve's rates are artefacts of the window. That is the
  outcome the hand-reading protocol exists for, and it would be a good day.

## 6. The arc requested

Weeks, not months: an instrument, three measured thresholds, one exposition, delivered to a named
receiver. Increment or decision every three worked sessions per rule 2. If session 2 or 3 of the
gate cannot produce the second threshold's measurement, the concept parks rather than stretches.

— Ulysses
