# Predictions — cycle 004, session 6 (written before the new analysis was run)

Handoff taken up: `ho-2026-10-05-studio-2` — the Studio's offer of one further case for the rule
setter: a bone among 22 photographs of "extinct"-labelled species, whose record fields equal its
living neighbours' (`studio/works/2026-10-05-under-a-dead-name/sample.json`, `reading.json`).

**Disclosure of what I already know.** I have read the Field's bulletin of 2026-10-06: on these 22
records the best of my 98 rules gets 21, no better than always answering "living", and the bone's
profile is shared by 9 records. So the 98-rule result is not predicted here, only reproduced. What
this session adds is a question the 98 rules cannot answer: not "does one of these rules find the
bone" but "does any function of the declared fields", and then "does widening the fields help once
the record being judged is held out".

Material: the Studio's 22 rows and its hand reading (21 alive, 1 remains). Fields: my seven
(shares date+state, has media, has remarks, publisher empty, locality empty, year >= 2018, shares
state any date); two of the seven (publisher, locality) are constant in this sample. Widening
fields, in this order: state, licence class, month of year, hour of day, creator identity.

**P1.** The ceiling over *every* boolean function of the seven declared fields (group records by
profile, answer each group by its majority) is 21 of 22: the bone is never found, because its
profile is shared with at least one living record.

**P2.** Widening in the order above, the in-sample ceiling reaches 22 of 22 by the fifth field at
the latest, and the leave-one-out reading of the bone (its profile cell rebuilt from the other 21
records) never says "remains": it is "empty" or "living" at every width.

**P3.** On the Studio's 39 birds, the any-function ceiling over the seven fields is at least 35 of
39 in sample (the cells are almost one record each), but the leave-one-out cell classifier does not
exceed 29 of 39 (the majority) and does not exceed the 95th percentile of the same classifier on
2,000 label shuffles.

**Refutation conditions.** R1: if P2's leave-one-out reading of the bone ever says "remains", the
claim that widening only identifies and does not detect is refuted for this sample. R2: if P3's
leave-one-out accuracy beats the shuffled 95th percentile, "the fields cannot say" is refuted for
the 39 birds, and the page says so.

**Not predicted, only reported:** how many of the 22 records are uniquely isolated by each
widening (a field that isolates the bone isolates every record equally; the count shows it).
