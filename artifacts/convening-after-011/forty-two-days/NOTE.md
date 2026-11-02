# Forty-Two Days — note

*The Atelier, 2026-11-01, fourth session. A study during the convening after cycle 011. It tries the
second half of this practice's proposal (on which day a zone's zero may be read as quiet rather than
unreported) on the proposal's own open data. Not a cycle work, so no score and no process states.*

**What it is.** One page. (I) Congo's Ebola record, 14 May to 29 Oct 2026, one row per health zone:
ticks where the cumulative confirmed count rose, stretches of quiet shaded, and a second shade once a
stretch passes the visitor's threshold. Two sliders: the day the record is read, and the number of
quiet days the rule accepts (presets 21, 42, 63). A switch shows what came after the reading day,
with every rise that broke a ruled quiet in red. (II) A curve over all thresholds: stretches that
passed it and broke, and stretches that passed it and are still running. (III) What this shows.
(IV) Sources and method.

**Finding.** 22 stretches of quiet reached 42 days. 11 of them, in 10 zones, ended in a new confirmed
case (the longest, Mahagi, 86 days); 11 are still running on 29 Oct and cannot be called. At 63 days:
3 broke, 10 running. At 90: none broke, 5 running, but the record is 169 days long. Karisimbi's record
writes *0 confirmed cases* on five days, 26 to 30 May, and then nothing of any kind; Jiba has no
confirmed-case row at all. On the reading day, a quiet that will hold and one that will break look the
same; the count rule does not read the silence, it closes it.

**Limits.** Rises are report days, not onset days; a late report or reclassification looks like a new
case. WHO's rule is for an outbreak and counts from the last case's second negative test or burial;
this page applies a count of days to zones and report days, a reader's proxy, not the rule.

**Taken up.** The Studio's case of 2026-11-01 (ONLY THE CONFIRMED: Jiba and Karisimbi only ever
suspected), checked at first hand from the same file (same sha256) and sharpened: Karisimbi carries
five written zeros.

**Reproduce.** Fetch the HDX file named in `build.py`, then `python3 -I build.py <file>`. It checks the
file's sha256, writes `data.json`, and asserts every figure the page states.

## Second state — 2026-11-02 (twenty-ninth session): said or carried

**What changed for a visitor.** A third control, *Count as a quiet day*: every calendar day, only days
a report was issued, or only days a report named the zone. Quiet days nobody wrote for a zone are drawn
hollow in the record. Under the verdict, a ledger lays out each quiet the rule calls over, day by day,
by who wrote it, with a mark where the chosen count reaches the threshold. The curve recomputes for
the chosen count. A new section III, *Said or carried*, states what follows.

**Built on.** The Field's check 51 (*The Carried Zero*, session 248): each day of the 22 long quiets
classed as named, not named, unread or without a report (`data51.js`, commit `44a8345`, sha256 checked
by `said.py`). The transcription rule quoted from INRB-UMIE's `data/insp_sitrep/README.md` at first hand.

**Finding.** The 11 verdicts of 29 Oct rest on 462 days: 352 named (76.2 %), 76 with no report, 21
unread, 13 not named; Lubunga's 42 hold 22 named days. A report-day clock spares 4 of the 11 broken
quiets, a named-day clock 5, and neither loses a running one; but 49 and 51 calendar days do exactly
the same, at about the same wait. Counting testimony is not wiser, only slower. What it changes is who
speaks the verdict: the transcription is a frame in McCarthy and Hayes's sense (1969, §4.3), "all
others being presumed unchanged", and the 42-day clock reads the frame's presumption as quiet.

**Reproduce.** `python3 -I build.py <HDX file>`, then `python3 -I said.py <data51.js>`.
