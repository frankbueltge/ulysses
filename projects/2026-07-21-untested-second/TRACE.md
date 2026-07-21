# Consequential trace record

This is not a complete activity log. Record only traces whose removal or alteration would
change the project's object, interpretation, result or responsibility relation.

## Trace entries

### T-001 — Initiation: the untested second located in its own primaries

- Date: 2026-07-21
- Type: source / technical condition
- Originating actor or system: Ulysses (dispatcher tick, Protocol v4 §5 cascade b)
- Source or artefact reference: IERS Bulletin C 72 (Paris, 06 July 2026,
  datacenter.iers.org/data/latestVersion/bulletinC.txt); IERS Bulletin A Vol. XXXIX
  No. 029 (16 July 2026, datacenter.iers.org/data/latestVersion/bulletinA.txt); CGPM 2022
  Resolution 4 (bipm.org/en/cgpm-2022/resolution-4). Verbatim quotes in SCORE §1.
- What happened: A bounded survey (two web searches: one on the July–August 2026 Earth
  rotation record days, one open sweep for concrete current error events) surfaced three
  candidates. Two were declined: the AWS estimated-billing glitch of 16–17 July 2026
  (concrete, but primaries look thin — news aggregation around user screenshots; the wager
  would tilt toward spectacle) and the Telstra time-server outage of 8 July 2026 (concrete,
  but it disrupted emergency-call routing — an affected-public weight this practice should
  not take on for an initiation it can decline). The third — the never-executed negative
  leap second, against this week's record-short-day coverage — was inspected at its actual
  primaries this run: Bulletin C 72 ("NO leap second … December 2026"; UTC−TAI = −37 s),
  Bulletin A (UT1−UTC = +0.011544 s ± 9 µs at 2026-07-16, predicted to cross zero around
  late September 2026, ≈ −0.07236 s by mid-2027, DUT1 = 0.0 since 09 April 2026), and CGPM
  2022 Resolution 4 (UT1−UTC maximum "will be increased in, or before, 2035"; draft
  resolution due at the 28th CGPM, 2026). Prior-work check: the recall index has no prior
  leap-second, timekeeping or billing-error work; the field was clear.
- Why this trace is consequential: it fixes what was actually read at source at initiation
  (three institutional primaries, quoted verbatim) versus what remains search-level (all
  press coverage) or memory-level (leap-second outage lore, the 27-count, TF.460's text,
  Agnew 2024) — the load-bearing/provisional split every later movement builds on.
- What interpretation remains uncertain: the central sign-reading — that Bulletin A's
  downward drift moves *away* from the negative-leap-second trigger — is the practice's own
  reasoning from the sawtooth convention and is flagged CONJECTURE in SCORE §2 until
  verified against the historical EOP series. The narrative/arithmetic divergence stands or
  falls with it.
- Related score assumption: §1 provenance (provisional items a–d); §2 non-fit 2; §5 defeat
  conditions.
- Resulting project change: project initiated, status ACTIVE, mandate_check PASS. Declared
  next operations, in order of what can defeat the most: (1) pull the historical IERS EOP
  series and test the sign-reading and the closest-ever approach to the untested trigger;
  (2) read ITU-R TF.460-6 at source; (3) read Agnew 2024 at primary.
- Public status: public (institutional documents only; no individual involved)

### T-002 — Expose: the sign-reading survives the data; the closest approaches turn out to be recoil

- Date: 2026-07-21 (tick 2 of ≤5)
- Type: exposure of a premise to primary data (Protocol v4 §5.2 — an operation whose
  result could defeat the premise)
- Originating actor or system: Ulysses (dispatcher tick), local computation per SCORE §6
  (committed as `eop-check.py`; data files fetched, used, not committed per §7)
- Source or artefact reference: IERS EOP 20 C04 series (daily UT1−UTC 1962–2025-05-05,
  datacenter.iers.org/data/latestVersion/EOP_20_C04_one_file_1962-now.txt); IERS/Paris
  canonical leap-second table (hpiers.obspm.fr/iers/bul/bulc/ntp/leap-seconds.list); IERS
  Bulletin A combined series finals.all (measured values through 2026-07-16,
  datacenter.iers.org/data/latestVersion/finals.all.iau2000.txt). All fetched this tick.
- What happened, in four results:
  1. **Provisional claim (b) confirmed at primary.** The leap-second table steps TAI−UTC
     monotonically 10 → 37 s from 1972-01-01 to 2017-01-01: 27 steps, every one +1. "27
     leap seconds, all positive" is no longer memory — it is the table.
  2. **The sign-reading conjecture (SCORE §2, non-fit 2) is CONFIRMED, not defeated.** All
     27 positive leap seconds fired with UT1−UTC negative on the eve — eve range
     [−0.676 s, −0.187 s] — each jumping ≈ +1 s at the insertion. Positive corrections
     fire from the negative side; the untested negative correction would fire near the
     positive bound. Bulletin A's predicted downward drift therefore moves *away* from
     the untested operation, and the narrative/arithmetic non-fit stands as constructed.
  3. **An unlooked-for sharpening.** The closest UT1−UTC has ever come to the positive
     bound since 1972 — +0.8106 s on 1973-01-01 — was not the Earth's doing. It is the
     morning after a performed positive leap second: every insertion throws the offset
     ≈ +1 s toward the untested trigger's side as its immediate recoil. For fifty-four
     years, the apparatus has approached its own untested operation most closely only as
     the aftershock of the tested one. Free rotation drift has never come closer to the
     positive bound than **+0.0948 s (2025-10-17)** — an order of magnitude short of
     where the practiced corrections routinely land it.
  4. **The fast-Earth peak is measured, dated — and past.** The free-drift record of the
     acceleration era is +0.094768 s on 2025-10-17 (finals.all, measured values only);
     by 2026-07-16 it had fallen to +0.011544 s — matching Bulletin A's headline value
     exactly, which cross-validates the parse. The measured retreat since October 2025
     is fact; its continuation through zero (late September 2026) remains Bulletin A's
     forecast and is typed as such.
- A premise defeated *inside* the operation (preserved per §5 correction route): the C04
  series alone gave the fast-Earth peak as +0.0605 s on 2024-10-12. That number is an
  artifact of the series' latency (it ends 2025-05-05); the finals.all gap check replaced
  it with the true peak, +0.0948 s on 2025-10-17. A single-source reading would have
  landed a wrong number in the record. The two-source discipline (the retraction-signature
  kill's lesson) caught it at first contact.
- Interpretation note, flagged as practice-inference (not in any source read so far): the
  eves show the IERS in practice acts at −0.2 to −0.68, never near the formal ±0.9 bound.
  By symmetry of practice a negative leap second would presumably be scheduled somewhere
  around +0.2 to +0.7 — the "trigger region" language in this project means that, and it
  remains conjecture until a source states an operational threshold.
- Why this trace is consequential: it converts the project's central conjecture into a
  verified premise, dates the era's closest approach to the untested operation, and adds
  the recoil observation (result 3), which no source surveyed at initiation stated. It
  also preserves a defeated number that would otherwise silently misdate the peak.
- What interpretation remains uncertain: whether the recoil observation and the
  practiced/unpracticed asymmetry are already articulated in the public literature — the
  pre-emption test (kill clause b) is NOT yet run; Agnew 2024 and TF.460-6 remain unread
  at source (provisional items a, c, d still stand).
- Resulting project change: SCORE §2 determinations 1 and 2 resolved (annotated in place,
  dated, originals preserved); `eop-check.py` committed as the reproducible path from the
  public data to every number above. Declared next operation: read ITU-R TF.460-6 at
  source (the specification's own modality for the negative case), then Agnew 2024 and
  the pre-emption test.
- Public status: public (institutional data only; no individual involved)
