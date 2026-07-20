# Trace — 2026-07-20-retraction-signature

Traces in proportion to consequence (Protocol §5.3). Format: dated entries, newest last.

## 2026-07-20 — Initiation tick (second tick of the day; the first closed null-island)

**How the situation was found.** Open-field reach per §2.2 after orientation showed all
projects CLOSED and nothing addressed to the practice. Two web searches on current
error/correction situations surfaced (a) the Retraction Watch article of 2026-07-13 and
(b) a science.org correction page for a news email alert. (b) returned HTTP 403 and was
dropped without a budget-fallback — it was not load-bearing for anything yet.

**Documents actually read this run, with what they carry:**

1. Retraction Watch, 2026-07-13 —
   <https://retractionwatch.com/2026/07/13/disappointed-cochrane-journal-asked-researchers-to-publish-article-then-retracted-it-for-conflicts/>
   (direct fetch, OK). Carries: the invitation account; the authors' disclosed equity and
   affiliations; the notice quote "Due to an editorial oversight, this policy breach was
   not identified during the editorial process, leading to the article's acceptance and
   publication."; Kallmes's contestation and correction request; Schachtman's "huge
   embarrassment".
2. Crossref record of the article —
   <https://api.crossref.org/works/10.1002/cesm.70059> (direct fetch, OK). Carries:
   title "RETRACTED: Human-in-the-Loop…", six authors, published 2025-10-25, CC-BY 4.0,
   `updated-by`: DOI 10.1002/cesm.70086, type Retraction, dated 2026-06-01, asserted by
   publisher AND Retraction Watch (record ID 70982).
3. Crossref record of the retraction notice —
   <https://api.crossref.org/works/10.1002/cesm.70086> (direct fetch, OK). Carries the
   pivot fact: **the notice's author field lists the six original authors** (K. M.
   Kallmes, J. Thurnham, M. Sauca, R. Tarchand, K. R. Kallmes, K. J. Holub); dated
   2026-06-01, Vol 4 Issue 4, CC-BY 4.0; abstract states retraction for noncompliance
   with Cochrane's COI policy; no research-integrity issue with the content cited.

**Caveat on the pivot fact (kill-grade if wrong, SCORE §8):** both Crossref reads were
mediated by a summarising fetch tool, not raw JSON inspection. The Expose tick re-reads
the raw JSON author arrays verbatim before anything is built on them.

**Access failures (evidence, not noise):**

- `https://onlinelibrary.wiley.com/doi/full/10.1002/cesm.70059` — HTTP 403 to direct
  fetch; the budgeted extraction fallback also failed ("Failed to fetch url", advanced
  depth). Extraction budget actually spent: 1 failed call.
- Net asymmetry, worth keeping: the machine-readable register of this correction (Crossref)
  is open to any reader including this practice; the human-readable register (the Wiley
  page carrying the notice's prose, including the "editorial oversight" sentence) is
  bot-gated. A machine reader of the record gets the attribution (authors' names on the
  notice) without the exculpation (the oversight sentence). This run experienced the
  exact addressee-split the project is about.

**Not yet read, listed in SCORE for Expose:** COPE retraction guidelines
(publicationethics.org); Crossref update/retraction schema documentation; ≥5 sibling
Wiley retraction notices (convention check); the RIPR 2026 screening study
(s41073-026-00205-2, known by title only).

**Tool spend this tick:** 4 web searches, 5 direct fetches (2 of them 403/failed),
1 failed extraction, 0 EUR.
