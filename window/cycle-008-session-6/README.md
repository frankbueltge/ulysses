# The Narrowest Class — cycle 008, session 6 (2026-10-17)

Built on the Field's study 21 (*The odds written down*, field-research@94b13b2): the US Geological
Survey's first written aftershock odds for 255 mainshocks, scored against its own catalogue. One
warning per mainshock (the lowest whole magnitude at or above the forecast's floor, one week; 252
qualify). Every combination of one to three of six facts (region, mainshock size, model, year, the
stated chance's band, issue delay) is a reference class; each class with at least N warnings is judged
against the Poisson-binomial distribution its stated odds imply (two-sided 5 %), and its power against
a halving of every chance is recorded. The page shows, for any warning, every class it belongs to and
their verdicts, marks the narrowest, and lets the visitor make a class by hand.

Reading (reach outside, philosophy of probability, read in full text): Hájek, "The reference class
problem is your problem too", *Synthese* 156 (2007) 563–585, pp. 568, 569, 583, 584.

Predictions written before the analysis: `PREDICTION.md` (3 of 3 held; refutation condition did not fire).

Rebuild: `python3 -I build.py <field-research checkout at 94b13b2>` (asserts the two input hashes,
seeded), then `node verify.mjs` (30 checks in a real browser, 390 px light and 1100 px dark).

**Corrected 2026-10-18** (the Field's study 22, checked here by an exact re-judging in
`presentations/cycle-008/exposition/null.py`): the 38 warnings whose narrowest classes disagree,
both able to tell, are what one common factor of overstatement makes by chance (38 or more in 59 %
of 1,000 such worlds). Finding 3 stands as a description of what a reader gets; it no longer stands
as evidence that the forecasts differ by class. The page carries the dated note under finding 3.
