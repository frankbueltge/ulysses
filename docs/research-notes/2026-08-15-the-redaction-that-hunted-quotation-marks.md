---
date: 2026-08-15
kind: research-note
tags: [redaction, record-keeping, threshold, inward, instrument]
instrument: tools/redaction_sweep.py
---

# The redaction that hunted quotation marks

**What this is.** A complete inventory of verbatim German quotation left in this repository
after the fourth pass of the standing rule of 2026-08-15 (architect; wording private): the
record keeps the substance of Frank's messages and drops their wording, marked
*(wording private)*. Passes one to three ran on 2026-08-15 — one by this practice at 02:54,
two by Frank at 15:04 and 15:46. This is the fourth, and the first run by an instrument
rather than by hand.

## Why a fourth pass

Each earlier pass was defeated by the same defect, and each commit message names it:

| Pass | Time (UTC+2) | By | What defeated it |
|---|---|---|---|
| 1 | 02:54 | this practice | matched only quotations that fit on one line |
| 2 | 15:04 | architect | asked for four German function words before flagging |
| 3 | 15:46 | architect | asked for four German function words before flagging |

Every one of those is a **threshold** — a minimum length, a minimum count. A rule that admits
no exceptions was being enforced by a filter that does. Passes two and three each found what
the pass before had let through, which is the signature of a filter tuned for precision
against a rule that needs recall.

`tools/redaction_sweep.py` carries no threshold: one German-only token — an umlaut, an
eszett, or a stopword that is not also an English word — flags a quoted span, and the reading
is done by hand afterwards. Proper names carrying umlauts are excluded; the four-line request
head is house vocabulary and is skipped; this practice's own German-language scholarship under
`docs/foundation/` is counted separately rather than suppressed.

## The blind spot the three passes shared

All three hunted **quotation marks**. The largest survivor in the record is quotation by
**structure**: a markdown blockquote with no quotation marks anywhere in it.

Under `## Seeds from the team` in `REQUESTS-ARCHIVE.md`, two of Frank's broadcast seeds stand
in full, in German, as they were written:

- **Seed of 2026-07-26** — *ein Register geprüfter offener Datensätze steht bereit* —
  `REQUESTS-ARCHIVE.md:279–314`, 30 flagged spans.
- **Seed of 2026-07-28** — *drei Kataloge, und ihr könnt sie erweitern* —
  `REQUESTS-ARCHIVE.md:1318–1389`, 59 flagged spans.

Pass two was aimed at exactly this class — its own commit message says broadcast messages
wrapped across several lines survived pass one — and it changed 13 lines while these 89 spans
stood four screens away in the same file.

## Repaired in this pass

Three items, all of them cases where the architect's own paraphrase of the same passage already
exists elsewhere in the record. Nothing here is this practice's editorial judgement over his
words; it is his redaction carried to a copy his sweep did not reach.

1. `REQUESTS-ARCHIVE.md:244` — the *n − 1* seed of 2026-07-17, verbatim. The identical text was
   paraphrased in `journal/2026-07-17-session-37.md` by pass three, hours earlier. The archive
   copy survived. His wording is carried across.
2. `REQUESTS-ARCHIVE.md:436` — an inline quotation of his question about self-development.
3. `projects/2026-07-23-negative-parallax/REVIEW-2026-07.md:272–273` — two fragments of the
   poste-restante note of 1 August, the same passage pass two paraphrased in
   `REQUESTS-ARCHIVE.md:1880`. Carried across from his own paraphrase.

Item 3 sits in `projects/**`, which no earlier pass searched at all.

## Not repaired, and why

- **The two seed blocks above (89 spans).** Rendering the substance of some 110 lines of
  another author's broadcast prose is an editorial act at a scale where the paraphrase becomes
  the record. This practice will do it on one word from the architect, in the shape his own
  passes used, and it is his to say. Reported in `REQUESTS.md`.
- **`Entscheidung: veröffentlichen`** — four occurrences (`REQUESTS.md:286, 288, 938`;
  `projects/2026-07-23-negative-parallax/TRACE.md:302`). Two words, and the substance *is* the
  wording; it was a decision posted to a public issue thread rather than a personal message.
  Both readings are defensible, so it is reported rather than decided here.

## The mirror

The architect's pass-two commit records that the site repository mirrors these files, and that
the same redaction had to land there in the same pass or the next integration run would restore
the wording. This session's repository scope is `frankbueltge/ulysses` alone, so the three
repairs above are landed here and **unmirrored**. If the mirror is authoritative, they will be
undone.

## Residue, read and left standing

10 further flagged spans are not personal messages and stay as they are: German book and paper
titles (`atlas/README.md:97`, `journal/2026-06-28.md:3`, `projects/2026-07-19-mach-ancestor/SCORE.md:3`),
a Swedish work title read twice (`Glömskekonst`), a public seed naming a song
(`REQUESTS.md:44, 46`), this practice's own quoted request-head vocabulary
(`REQUESTS.md:626`), a machine log line (`REQUESTS-ARCHIVE.md:178`), and a German typo this
practice corrected in its own work (`projects/2026-07-24-kartographie-statt-kopie/DECISION.md:32`).
23 more spans are this practice's own German-language scholarship under `docs/foundation/`.

## What the instrument costs to run

One pass over 100+ markdown files, no network, no external cost. It exits non-zero while
anything is flagged, so it can stand in a gate; it is not in one, because 10 of its current
hits are legitimate and a gate that fires on them would be turned off within a week.

**Reproduce:** `python3 tools/redaction_sweep.py .`
**Counts after this pass's three repairs:** 103 flagged spans outside `docs/foundation/`, which
account for all of them — 89 in the two seed blocks, 4 occurrences of
`Entscheidung: veröffentlichen`, 10 residue read and left standing. 23 further spans inside
`docs/foundation/`.
