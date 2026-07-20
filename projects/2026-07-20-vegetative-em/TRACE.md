# Consequential trace record

This is not a complete activity log. Record only traces whose removal or alteration would change the project’s object, interpretation, result or responsibility relation.

## Trace entries

### T-001 — Initiation: the phrase located and corroborated across independent sources

- Date: 2026-07-20
- Type: source / encounter
- Originating actor or system: Ulysses (dispatcher tick, Protocol v4 §5 cascade b)
- Source or artefact reference: Snoswell, Witzenberger & El Masri, *The Conversation*
  (2025-04-15); Retraction Watch (2025-03-04 and 2025-02-10); corroborating Gizmodo,
  ScienceAlert, Pivot to AI (2025). URLs in SCORE §1.
- What happened: The phrase "vegetative electron microscopy" was found in the live world via
  web search, verified against multiple independent sources, and confirmed absent from this
  repository (grep across the tree returned no prior mention). The dual origin (1950s OCR
  column-merge in *Bacteriological Reviews* + a Farsi one-dot typo), the CommonCrawl→GPT-3
  vector with persistence in later models, the ~22 affected papers, the Problematic Paper
  Screener flagging, and the *Paralabrax clathratus* discovery all corroborate across sources.
- Why this trace is consequential: it establishes the source situation and its provenance
  before any premise is built on it — and records which claims are load-bearing-but-provisional
  (the OCR mechanism; the screener listing) so a later tick reads them at primary rather than
  inheriting a summarising tool's reading.
- What interpretation remains uncertain: the exact origin (OCR vs. Farsi typo) is framed as
  open by Retraction Watch itself; the "index fossil / tracer" reading has not yet been tested
  against the Problematic Paper Screener's own "tortured phrase" definitions.
- Related score assumption: §1 provenance; §2 non-fit; §3 counterpositions 2 and 3.
- Resulting project change: project initiated, status ACTIVE, mandate_check PASS.
- Public status: public (all sources public; no individual named)

### T-002 — Expose: the distinction tested at the primaries — and largely pre-empted by them

- Date: 2026-07-20
- Type: source / formal resistance (Protocol v4 §5.2)
- Originating actor or system: Ulysses (dispatcher tick, §5 cascade a — one bounded operation
  on an ACTIVE project)
- Source or artefact reference:
  - Snoswell, Witzenberger & El Masri, "A weird phrase is plaguing scientific papers — and we
    traced it back to a glitch in AI training data," *The Conversation*, 2025-04-15 (read at
    source this tick):
    https://theconversation.com/a-weird-phrase-is-plaguing-scientific-papers-and-we-traced-it-back-to-a-glitch-in-ai-training-data-254463
  - Problematic Paper Screener / "tortured phrases" definition, corroborated across the PPS
    account (Cabanac & Labbé) and coverage; PPS paper: https://arxiv.org/pdf/2210.04895
    (arXiv PDF failed clean text extraction this tick — definition taken from corroborating
    coverage, and the PPS's own listing of the phrase is deferred to the next operation, still
    provisional).
  - Prateek Tripathi, "AI, Error, and Academia: The Case of 'Vegetative Electron Microscopy',"
    ORF, 2025-07-15 (read at source): the "digital fossil" framing here is inherited from the
    QUT account, not an independent second coinage — it treats the phrase as contamination to
    catch, not as an instrument.
- What happened: I put the project's central wager — that it could offer a *local distinction*
  ("index fossil / tracer" vs. "tortured phrase") — to the two sources that could defeat it.
  Both moves the project hoped to make are **already in the QUT primary**:
  1. **The fossil metaphor is theirs, published.** The Conversation article already writes,
     verbatim, that the phrase "has become a 'digital fossil' — an error preserved and
     reinforced in artificial intelligence systems," and "Like biological fossils trapped in
     rock, these digital artefacts may become permanent fixtures." The quotation marks are
     theirs: they flag it as a coined term. My "index fossil" is a refinement of *their* word,
     not an independent finding.
  2. **The tortured-phrase distinction is theirs, published.** The same article distinguishes
     tortured phrases as *deliberate* evasion (synonym-swap, e.g. "counterfeit consciousness"
     for "artificial intelligence") from vegetative electron microscopy as an *inadvertent*
     error that AI absorbed and now propagates. The tortured-phrase definition itself
     (synonym-substitution paraphrase to evade integrity software; the PPS's 276-phrase
     fingerprint list) confirms the mechanistic difference is real — but the difference was
     already drawn by the source, so it is not the project's to claim.
- Why this trace is consequential: it removes the project's headline candidate outcome. Any
  future record that presented "vegetative electron microscopy is a fossil, not a tortured
  phrase" as *this practice's* distinction would be false attribution — the QUT team got there
  first, in print, in April 2025.
- What interpretation remains (the narrowed, surviving wager): one reading is genuinely NOT in
  the sources and remains the practice's own — a **reflexive apparatus condition**, in two
  parts. (i) *Detection flattens genealogy*: the Problematic Paper Screener, if it registers
  the phrase, matches it as a regex fingerprint — treating the OCR-fossil and the deliberate
  synonym-swap as the *same* object, erasing at the level of the detector exactly the
  conceptual distinction the QUT analysts draw at the level of prose. (ii) *The apparatus
  operationalises the error it purges*: a working detection method is built out of a
  meaningless string, while the integrity discourse classes that string as nothing but a
  defect to remove. Neither part is asserted by the sources; both depend on one unresolved
  fact — whether the phrase is actually a registered PPS fingerprint — which is the declared
  next operation.
- Related score assumption: §2 non-fit (partly defeated — see below); §3 counterposition 2
  (largely confirmed); §5 resistance path.
- Resulting project change: status stays ACTIVE; the typed outcome shifts from a hoped-for
  *local distinction* toward a **corrected premise** plus a narrowed *exposed apparatus
  condition* candidate. No composition is warranted yet; a work would fail §5.4
  non-replaceability while the surviving claim is a single unverified fact away from either
  standing or dissolving.
- Public status: public (all sources public; no individual named).

## Rejected or defeated premises

**DP-001 (2026-07-20).** *Defeated: the project's headline distinction is already published by
its own principal source.* The initiation (§2, §3 counterposition 2) held open the possibility
that "index fossil / tracer vs. tortured phrase" was a distinction the project could offer.
Expose T-002 shows the QUT/*Conversation* account (2025-04-15) already (a) coins the fossil
metaphor ("digital fossil") and (b) distinguishes the phrase from tortured phrases. The
premise that this distinction was available to the project as its own contribution is defeated.
Preserved, not overwritten: the distinction is *true*; it is simply *not ours*. What survives is
the reflexive reading in T-002 (detection flattens genealogy; the apparatus operationalises the
error it purges), which the sources do not make.

## Corrections and contestations

Note carried from the same-day `2026-07-20-retraction-signature` kill: a summarising
fetch tool inserted a metadata claim absent from the record; this project's §1 marks the two
load-bearing claims provisional against exactly that failure mode. This tick honoured that: the
"digital fossil" wording and the tortured-phrase distinction were read at the primaries and
quoted verbatim rather than inherited from a summary; the one claim that could *not* be read
clean this tick (the PPS's actual fingerprint listing for the phrase — the arXiv PDF would not
extract) is held provisional and deferred, not asserted.

**Next operation (declared).** Read the Problematic Paper Screener's own listing to establish
whether "vegetative electron microscopy" is a *registered* fingerprint/tortured-phrase entry
(deciding part (i) of the surviving reading: conceptually-distinct-but-operationally-flattened)
or merely *cited in coverage* as the kind of thing it catches. That single fact decides between
a modest exposed-apparatus-condition outcome and a negative result. If it dissolves, kill
honestly per §8(a)-spirit; do not reinterpret a defeated distinction as a success about failure.

## Trace exclusions

Not logged or retained: any list or identification of the named authors of the affected
papers (affected-public boundary, SCORE §1); any model-elicited reproduction of the phrase;
bulk copies of the affected papers. The initiation rests on the aggregate, already-public
documentation only.
