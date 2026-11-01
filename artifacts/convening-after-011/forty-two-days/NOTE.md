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
