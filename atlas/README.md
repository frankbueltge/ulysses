# Atlas of Artistic Research

A curated, machine-readable reservoir of verified external sources for this atelier.

## Why this exists

Your own research says it (Shumailov 2023; Gerstgrasser 2024; Jangjoo/Marsili/Roudi 2025,
all anchored in this atlas): a closed self-training loop collapses — unless real points from
another distribution keep entering it. This atlas is that other distribution, kept clean and
verifiable: *low-background steel* to forge from, so the sessions do not only feed on their
own output. It was seeded on 2026-07-14 with 57 verified entries and extended the same day
to 77 (after review: inner-canon anchors and coverage gaps added). It is deliberately
weighted toward the one field the atelier practices nightly but has never read: the
methodology of artistic research itself (Frayling, Borgdorff, Schwab, Mersch, and the
practice-as-research debate), alongside the method-philosophy of the swerve (rhizome,
clinamen, diffraction, chance, constraint, not-knowing) and the research literature on
machine creativity and self-consuming loops.

The atlas also **anchors the inner canon**: the works the journal already cites — the
cybernetics line (Wiener, Bateson, von Foerster, Maturana/Varela), Track A's four stations
(Tynianov, Colby/Weber/Hilf, Fredrikzon, Somaini), Track B's materials (Stein, Strachey,
Menkman, Jones) — live here as verified primary records, so the reservoir holds the sources
themselves and not only the journal's memory of them. Two of these anchors carry repairs:
Tynianov's Literary Fact gets its citable English edition (Station 1 was search-verified
only), and the Somaini entry corrects the genealogy's dating (October no. 196 is Spring
2026 per Crossref, not 2025).

One repair is built in: *The Conflict of the Faculties* was cited from snippets in the very
first journal entry (2026-06-28), its full text deferred after a failed OAPEN fetch — and
never revisited. The atlas entry carries a retrievable copy (Leiden repository; OAPEN throws
ECONNRESET, verified again 2026-07-14).

## Schema (`atlas.json`, one array)

```
{ "id": "kebab-slug",
  "author": "…", "work": "…", "year": 1980,
  "type": "buch|paper|manifest|essay",
  "url": "…", "doi": "…", "arxiv": "…",      // only the applicable fields are set
  "tags": ["…"],
  "summary": "1-3 sentences: what the work is; access status noted (open access / paywalled)",
  "relevance": "1 sentence: why it matters for Error as Method / bridge to a track",
  "added_by": "fable|ulysses|frank|reader",
  "status": "seed|read|worked",
  "session_read": "YYYY-MM-DD"                // set by you, when you actually read it
}
```

**Status lifecycle** (you maintain it):
- `seed` — admitted to the atlas, not yet read. Every new entry starts here.
- `read` — you actually read the work (not a snippet, not a summary). Set `session_read`.
- `worked` — the work has entered one of your works or a sustained line of argument.

**Year convention:** first publication in the original language; standard translations are
named in the summary. Lucretius is carried as `-55` (composed c. 55 BC).

## Admission rule (the hard one)

An entry is admitted only with a **verified, retrievable identifier** — a `url` that resolves,
a `doi`, or an `arxiv` ID — checked at admission time. Nothing is invented: no work, no
author, no year, no URL. What cannot be verified stays out (see gaps below). Access is
stated honestly in the summary: *open access* means you can fetch the full text at the given
URL; *paywalled* means the entry documents existence and location, and you will need
secondary routes to the text.

You may **extend the atlas** (`added_by: "ulysses"`) under the same rule: verify before you
admit, tag from the vocabulary below, start at `status: "seed"` even for your own additions.

## Tag vocabulary

Fixed, three axes. The rhizome will later build its long-range edges (the clinamen draws)
from these — keep them consistent, do not improvise new tags in entries. If the vocabulary
is missing something, propose the new tag here in the README first, then use it.

| Axis | Tags |
|---|---|
| methode | `rhizom` · `clinamen/aleatorik` · `practice-as-research` · `diffraktion` · `constraint/oulipo` |
| thema | `epistemologie` · `fehler` · `nicht-wissen` · `maschine/ki` · `ästhetik` · `beobachter` |
| feld | `artistic-research` · `philosophie` · `kybernetik` · `computation` |

## Living sources (not entries — the schema holds works, not journals)

- **Journal for Artistic Research (JAR)** — peer-reviewed, fully open access, ISSN 2235-0225,
  founded 2011, founding editor Michael Schwab: https://www.jar-online.net/
- **Research Catalogue** — the exposition platform JAR runs on; searchable archive of
  artistic-research expositions: https://www.researchcatalogue.net/

## Honest gaps (state of the seed, 2026-07-14)

- **Paywalled, existence verified but full text not freely retrievable:** Barad's *Diffracting
  Diffraction* (Taylor & Francis), Haraway's *Situated Knowledges* (JSTOR; university mirrors
  circulate), the Science version of Epstein et al. (arXiv companion given instead), Mersch's
  *Epistemologien des Ästhetischen*, Schwab's *Experimental Systems*, Fredrikzon's *Rethinking
  Error* (Duke UP — the free promotional window closed 31 Jan 2026; Fehlerkataster F-004
  stands), Somaini's *Latent Spaces* (MIT Press), and most of the books. The atlas points at
  them anyway — knowing where a text lives is worth more than pretending it does not exist.
- **Left out for verification reasons:** Mersch's essay „Was heißt, im Ästhetischen forschen?"
  (2015) exists only as a self-hosted PDF at dieter-mersch.de; its original venue could not be
  independently confirmed, so it was not admitted. Candidate for later admission if a venue
  is verified.
- **Weak or fragile URLs, honestly flagged:** *The Third Mind* (Burroughs/Gysin) has no
  surviving stable publisher page (Wikipedia as locator only). Strachey's Encounter scan
  blocks automated fetching (David Link's Variantology PDF is the machine-readable route,
  named in the entry). Maharaj's journal is dead — the Wayback capture is the record.
  Mignolo/Vázquez sits behind an anti-bot challenge (Wayback fallback in the entry). Stein's
  *How to Write* has no open-access scan (Open Library record only). Xenakis' publisher page
  rejects bots.
- **Coverage gaps, known and open:** artistic-research primary texts from Asia, Africa and
  Latin America remain thin — the decolonial entries added (Tuhiwai Smith, Santos, Maharaj,
  Mignolo/Vázquez) are epistemology and methodology, not artistic-research practice texts;
  sound studies beyond Xenakis and Cage; the enactivist line after Varela.

## Provenance

Seeded and extended by Fable (a parallel session steered by Frank, 2026-07-14): candidates
drawn from the artistic-research canon, from your own genealogy and works, and from arXiv;
each verified against publisher pages, repositories, DOI resolvers or arXiv metadata before
admission; summaries written against the verified records, not from memory. Errors are
possible regardless — if you find one, correct the entry and note the correction in your
journal. That, after all, is the method.
