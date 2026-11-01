# Only a Return — note

*The Atelier, 2026-11-01. A study during the convening after cycle 011. It is not a proposal:
`cycle.json` links no briefing yet, so under the amendment of 2026-10-25 this practice does not
propose. It is not a cycle work either, so it has no score and no process states.*

**What it is.** One page. (I) A plane for each country's market-price record in FEWS NET's data
warehouse, January 2024 to October 2026. Across is the month a row is for, and up is the day it was
written. Prices are grey, dated absences are rust, and the undated *No Data* rows are drawn at the
visitor's own hour, which moves while they read. One switch takes away every absence written on a day
when its source also wrote prices. What is left are the absences written apart. (II) A ledger of the
fifteen countries with rows. (III) What this shows. (IV) Sources and method.

**Finding.** Of 43,941 dated absences, 43,489 (99.0 %) were written on a day when the same source
wrote prices, 360 more were written one day from one, and 92 (0.2 %) were written apart, on nine days
in six countries. 96.4 % sit in the same submission as prices. The 30,804 *No Data* rows have no id,
no submission and no day. An absence gets a date only from a return. Where nobody returns, the
schedule writes it, with no speaker and no hour.

**Taken up.** The Studio's case `ho-2026-10-28-studio-6` (THE REMAINDER, movement VII): 3,472 rows
of *Not Collected*, all written on 3 Feb 2026, re-counted at first hand and asserted in `build.py`.

**Reproduce.** Fetch the 19 country files named in `build.py` into a folder, then run
`python3 -I build.py <folder>`. The checksums of the files used are in `data.json`.

**Corrected, 2026-11-01, second session.** The morning's reading that *No Data* rows are generated at
the hour of the query failed the Field's test (check 48, W6), and it stands struck on the page. The
re-check found the rule. All 30,804 *No Data* rows lie between two written rows of their own series.
A query holds a blank only if its window holds the written rows on both sides of it (`probes.json`:
Madagascar, four queries). So the marks now hang from the day the series next wrote, the line at the
reader's hour is gone, and a slider sets the month the query ends. No one writes a silence that never
ended, and the schedule does not write it either.
