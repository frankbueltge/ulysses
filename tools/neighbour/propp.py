#!/usr/bin/env python3
"""The Propp reduction — does any measure over a short prose field separate a work's
*move* from its *subject*?

Cycle 002, session 2 of the Atelier. This instrument is a direct successor to
`nn.py`, which calibrated the house's "has the world already done this?" neighbour
check over the atlas's `decisive_move` field. That session ended with a number it
could not explain away: of the forty highest-ranked pairs, sixteen survived two
mechanical artefact rules, and of those sixteen, **none did the same thing**. They
shared a noun. The measure was ranking works by what they were *about*.

The question left open was whether that is a defect of the measure or a fact about
the material: is there a measure over a short prose field that separates a move from
a subject, or is that separation only ever a reader's act?

## Where the method comes from — the session's reach outside

Vladimir Propp, *Morphology of the Folktale*, 2nd ed., trans. Laurence Scott, rev.
Louis A. Wagner (Austin: University of Texas Press, 1968), chapter II, "The Method
and Material", pp. 19–24. Structural folkloristics is not a field this practice
uses; the text was read for this session, and the four sentences the instrument
actually rests on are quoted here so the transposition can be argued with.

  * On what varies and what does not (p. 20): *"The names of the dramatis personae
    change (as well as the attributes of each), but neither their actions nor
    functions change."*
  * On the asymmetry that makes the whole method possible (pp. 20–21): *"the number
    of functions is extremely small, whereas the number of personages is extremely
    large."*
  * On the form a function takes in language (p. 21): *"Definition of a function
    will most often be given in the form of a noun expressing an action
    (interdiction, interrogation, flight, etc.)."*
  * On what an index should be built from (p. 22): an index of types can be created
    *"based not upon theme features, which are somewhat vague and diffuse, but upon
    exact structural features."*

The transposition, stated plainly: an atlas of works is not a corpus of tales, and a
`decisive_move` field is not a tale. What carries over is one claim with a testable
consequence — **if moves are few and subjects are many, then a move-word recurs
across the corpus and a subject-word does not.** Every standard text measure assumes
the opposite. tf-idf rewards rarity; it is built to make the singular word decide the
score. If Propp is right about this material, tf-idf is not merely imprecise here, it
is pointed the wrong way.

And the ceiling Propp himself puts on it, quoted because it is the honest limit of
everything below (p. 21): *"identical acts can have different meanings, and vice
versa. Function is understood as an act of a character, defined from the point of
view of its significance for the course of the action."* A single sentence scored as
a bag of words has no course of action in it. So nothing here can recover a function
in Propp's sense. At best it recovers an **act** — and the adjudication is where one
finds out whether that is enough.

## What is measured

Four measures over the same 521 `decisive_move` fields and the same tokenisation as
session 1 (imported from `nn.py`, so the comparison is like for like). Two factors,
two levels each:

    vocabulary   ALL  — every token that survives the stopword list (session 1)
                 ACT  — only tokens whose stem shows verbal inflection somewhere in
                        this corpus (the rule is in `act_vocabulary`, below)
    weighting    IDF  — tf · ln(N/df): rarity decides           (session 1)
                 TF   — tf alone: recurrence decides            (the Propp inversion)

    A = ALL × IDF   session 1's measure, reproduced
    B = ALL × TF    the inversion, on the whole vocabulary
    C = ACT × IDF   Propp's vocabulary, session 1's weighting
    D = ACT × TF    both

Each cell is calibrated against its own surrogate null, by the same route session 1
used: for every work, M surrogate texts of that work's exact token count *in that
cell's vocabulary*, drawn from that cell's own token-frequency pool, scored against
the same 520 others. Seeded, so a re-run is identical. A cut is measured, never
assumed — that was cycle 001's finding and it is not spent.

The two mechanical artefact strata are carried over from session 1 unchanged, so the
pair sets are comparable: **same artist** on both sides, and **catalogue residue** on
both sides (eight fixed markers). They are applied by rule, before any reading.

The feed is read, never mirrored. What is committed is derived.

    python3 tools/neighbour/propp.py --fetch --out window/cycle-002-session-2/data.json
    python3 tools/neighbour/propp.py --atlas /path/werke.json --out ... --m 200

Author: the Atelier. Licence: Apache-2.0 with the repository.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import pathlib
import random
import re
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nn  # noqa: E402  — the tokeniser, stopword list, feed URL and quantiles of session 1

FEED = nn.FEED
TOP_N = 40      # ranked pairs named per cell; their union is what gets adjudicated
                # 40 because that is the depth session 1 read, so cell A's survivors
                # are the very pairs already published with verdicts
QUOTE = 260     # characters of the decisive-move field quoted per named pair

RESIDUE = [
    "description edit", "outside link", "inception:", "attributed to:",
    "access url:", "variant edit", "static files", "&quot;",
]

CELLS = [
    ("A", "ALL", "IDF", "session 1's measure: every token, rarity decides"),
    ("B", "ALL", "TF", "the Propp inversion: every token, recurrence decides"),
    ("C", "ACT", "IDF", "Propp's vocabulary, session 1's weighting"),
    ("D", "ACT", "TF", "both: act vocabulary, recurrence decides"),
]


# ------------------------------------------------------- the act vocabulary
#
# Propp's functions are named by "a noun expressing an action" (p. 21). The problem
# is to decide, mechanically and without a hand-written word list, which of this
# corpus's 5,060 token types name an action.
#
# The rule below uses one kind of evidence and only one: **verbal inflection inside
# this corpus itself.** A stem counts as verbal when the corpus somewhere contains it
# in an -ing or -ed form AND somewhere contains it bare or with -s/-es. Then any token
# that can be built from a verbal stem by a stated English suffix rule is an act
# token. Nothing is judged; everything is derived from the corpus and can be listed.
#
# It is not a good part-of-speech tagger and is not offered as one. It is a rule a
# reader can hold in their head and overturn, and the derived lexicon is published
# in full beside the artifact so that overturning it costs nothing. Its errors are
# visible in both directions and are reported: `image` and `model` are admitted
# because English lets those nouns verb; `extraction` and `surveillance` are refused
# because no inflected form of their verbs happens to occur here.

def _stems(w: str) -> set[str]:
    """Every stem `w` could have been built from, under stated English suffix rules."""
    out: set[str] = set()

    def add(s: str) -> None:
        if len(s) >= 3:
            out.add(s)

    if w.endswith("ing") and len(w) >= 6:
        s = w[:-3]
        add(s)
        add(s + "e")
        if len(s) >= 3 and s[-1] == s[-2]:
            add(s[:-1])
    if w.endswith("ed") and len(w) >= 5:
        s = w[:-2]
        add(s)
        add(s + "e")
        add(w[:-1])
        if len(s) >= 3 and s[-1] == s[-2]:
            add(s[:-1])
    if w.endswith("es") and len(w) >= 5:
        add(w[:-2])
        add(w[:-1])
    elif w.endswith("s") and not w.endswith("ss") and len(w) >= 4:
        add(w[:-1])
    # action nominals resolved back to a verb stem — Propp's own examples
    # (interdiction, interrogation) are of exactly this shape
    if w.endswith("ation") and len(w) >= 8:
        add(w[:-5] + "ate")
        add(w[:-5])
        add(w[:-3])
    if w.endswith("ition") and len(w) >= 8:
        add(w[:-5] + "ite")
        add(w[:-5])
    if w.endswith("tion") and len(w) >= 7:
        add(w[:-4] + "te")
        add(w[:-4] + "t")
        add(w[:-3] + "e")
    if w.endswith("sion") and len(w) >= 7:
        add(w[:-4] + "se")
        add(w[:-4] + "d")
        add(w[:-4] + "t")
    for suf in ("ment", "ance", "ence"):
        if w.endswith(suf) and len(w) >= 7:
            add(w[:-4])
            add(w[:-4] + "e")
    if w.endswith("ure") and len(w) >= 6:
        add(w[:-3])
        add(w[:-3] + "e")
    add(w)
    return out


def act_vocabulary(vocab: set[str]) -> tuple[set[str], set[str]]:
    """(act tokens, verbal stems) derived from the corpus's own inflectional evidence."""
    verbal: set[str] = set()
    for w in vocab:
        if (w.endswith("ing") and len(w) >= 6) or (w.endswith("ed") and len(w) >= 5):
            verbal |= _stems(w)
    verbal = {
        s for s in verbal
        if s in vocab or s + "s" in vocab or s + "es" in vocab
        or (s.endswith("e") and s[:-1] + "es" in vocab)
    }
    act = {w for w in vocab if _stems(w) & verbal}
    return act, verbal


# --------------------------------------------------------------- the corpus


class Cell:
    """One measure: a vocabulary restriction and a weighting, with its own null pool."""

    def __init__(self, docs: list[list[str]], vocab: set[str] | None, weighting: str):
        self.weighting = weighting
        self.docs = [[w for w in d if vocab is None or w in vocab] for d in docs]
        self.n = len(self.docs)
        df: dict[str, int] = {}
        for d in self.docs:
            for w in set(d):
                df[w] = df.get(w, 0) + 1
        self.df = df
        self.idf = (
            {w: math.log(self.n / c) for w, c in df.items()} if weighting == "IDF"
            else {w: 1.0 for w in df}
        )
        pool: dict[str, int] = {}
        for d in self.docs:
            for w in d:
                pool[w] = pool.get(w, 0) + 1
        self.pool_words = sorted(pool)
        self.pool_weights = [pool[w] for w in self.pool_words]
        self.n_tokens = sum(self.pool_weights)
        self.vecs = [self._vec(d) for d in self.docs]
        inv: dict[str, list[tuple[int, float]]] = {}
        for i, v in enumerate(self.vecs):
            for w, x in v.items():
                inv.setdefault(w, []).append((i, x))
        self.inv = inv

    def _vec(self, toks: list[str]) -> dict[str, float]:
        tf: dict[str, int] = {}
        for w in toks:
            if w in self.idf:
                tf[w] = tf.get(w, 0) + 1
        v = {w: c * self.idf[w] for w, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / norm for w, x in v.items()}

    def scores(self, vec: dict[str, float], skip: int | None = None) -> dict[int, float]:
        acc: dict[int, float] = {}
        for w, x in vec.items():
            for j, y in self.inv.get(w, ()):
                if j == skip:
                    continue
                acc[j] = acc.get(j, 0.0) + x * y
        return acc

    def best(self, vec: dict[str, float], skip: int | None = None) -> float:
        acc = self.scores(vec, skip)
        return max(acc.values()) if acc else 0.0


def run_cell(cell: Cell, entries: list[dict], m_per_work: int, seed: int) -> dict:
    observed = [cell.best(v, skip=i) for i, v in enumerate(cell.vecs)]

    rng = random.Random(seed)
    null_all: list[float] = []
    for i, d in enumerate(cell.docs):
        L = len(d)
        for _ in range(m_per_work):
            draw = rng.choices(cell.pool_words, weights=cell.pool_weights, k=L) if L else []
            null_all.append(cell.best(cell._vec(draw), skip=i))

    obs_sorted = sorted(observed)
    null_sorted = sorted(null_all)
    t99 = nn.quantile(null_sorted, 0.99)

    seen: dict[tuple[int, int], float] = {}
    for i, v in enumerate(cell.vecs):
        for j, s in cell.scores(v, skip=i).items():
            key = (i, j) if i < j else (j, i)
            if s > seen.get(key, -1.0):
                seen[key] = s
    ranked = sorted(seen.items(), key=lambda kv: -kv[1])

    return {
        "observed_median": round(nn.quantile(obs_sorted, 0.5), 6),
        "observed_mean": round(sum(observed) / len(observed), 6),
        "null_median": round(nn.quantile(null_sorted, 0.5), 6),
        "null_t99": round(t99, 6),
        "null_max": round(null_sorted[-1], 6),
        "n_surrogates": len(null_all),
        "n_pairs_scored": len(seen),
        "n_works_above_t99": sum(1 for v in observed if v > t99),
        "n_pairs_above_t99": sum(1 for _k, v in seen.items() if v > t99),
        "obs_hist": nn.histogram(observed, 0.0, 1.0, 50),
        "null_hist": nn.histogram(null_all, 0.0, 1.0, 50),
        "vocab_types": len(cell.df),
        "vocab_tokens": cell.n_tokens,
        "empty_docs": sum(1 for d in cell.docs if not d),
        "_ranked": ranked,
        "_observed": observed,
    }


# ----------------------------------------------------- the grammatical census
#
# Before any similarity: how many of these fields are written as an act at all? The
# rule is the field's first word, and nothing else — a cheap test, stated so it can
# be re-run. It is not a claim about the whole sentence; it is a claim about what the
# writer put in the subject position of it.

DETERMINERS = {"a", "an", "the", "this", "that", "these", "those", "one", "two",
               "three", "four", "five", "six", "seven", "eight", "nine", "ten",
               "its", "his", "her", "their", "each", "every", "another", "both",
               "some", "any", "all", "no"}
RESIDUE_HEADS = {"description", "inception", "edit", "artist", "attributed",
                 "access", "outside", "variant", "static", "previousnext", "quot"}


def head_class(field: str, verbal_heads: set[str]) -> str:
    m = re.match(r"[A-Za-z]+", field.strip())
    if not m:
        return "no word"
    w = m.group(0).lower()
    if w in RESIDUE_HEADS:
        return "residue"
    if w in verbal_heads:
        return "finite verb"
    if w.endswith("ing") and len(w) >= 6:
        return "participle"
    if w in DETERMINERS:
        return "determiner"
    return "other"


# --------------------------------------------------------------------- feed


def load_feed(path: str | None) -> tuple[dict, dict]:
    if path:
        raw = pathlib.Path(path).read_bytes()
        origin = f"file:{path}"
    else:
        req = urllib.request.Request(
            FEED, headers={"User-Agent": "ulysses-atelier-propp/1.0 (artistic research)"}
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
        origin = FEED
    payload = json.loads(raw.decode("utf-8"))
    manifest = {
        "origin": origin,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "count_declared": payload.get("count"),
        "licence": payload.get("licence"),
        "read_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    return payload, manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--atlas", help="local werke.json (default: fetch the feed)")
    ap.add_argument("--fetch", action="store_true", help="explicitly fetch the feed")
    ap.add_argument("--out", required=True)
    ap.add_argument("--m", type=int, default=200, help="surrogates per work per cell")
    ap.add_argument("--seed", type=int, default=20260904)
    args = ap.parse_args()

    payload, manifest = load_feed(None if args.fetch else args.atlas)
    entries = payload["entries"]
    docs = [nn.tokens(e.get("decisive_move") or "") for e in entries]
    raw_fields = [(e.get("decisive_move") or "") for e in entries]
    vocab = {w for d in docs for w in d}
    act, verbal = act_vocabulary(vocab)

    # the grammatical census
    verbal_heads = {
        w for w in vocab
        if w.endswith("s") and not w.endswith("ss") and len(w) >= 4
        and ({w[:-1], w[:-1] + "e"} & verbal)
    }
    census: dict[str, int] = {}
    head_of = []
    for f in raw_fields:
        c = head_class(f, verbal_heads)
        head_of.append(c)
        census[c] = census.get(c, 0) + 1

    # the four cells
    cells: dict[str, dict] = {}
    cell_objects: dict[str, Cell] = {}
    for key, voc, weight, note in CELLS:
        cell = Cell(docs, act if voc == "ACT" else None, weight)
        cell_objects[key] = cell
        res = run_cell(cell, entries, args.m, args.seed)
        res.update({"vocabulary": voc, "weighting": weight, "note": note})
        lens = sorted(len(d) for d in cell.docs)
        res["doc_length"] = {
            "min": lens[0],
            "q25": lens[len(lens) // 4],
            "median": lens[len(lens) // 2],
            "q75": lens[3 * len(lens) // 4],
            "max": lens[-1],
        }
        cells[key] = res
        print(
            f"cell {key} ({voc}×{weight}): obs med {res['observed_median']:.4f} "
            f"null med {res['null_median']:.4f} t99 {res['null_t99']:.4f} "
            f"pairs>t99 {res['n_pairs_above_t99']}",
            file=sys.stderr,
        )

    # artefact strata, carried over from session 1 unchanged
    artists = [(e.get("artist") or "").strip().lower() for e in entries]
    low = [f.lower() for f in raw_fields]
    residue_set = {i for i, r in enumerate(low) if any(m in r for m in RESIDUE)}

    def stratum(i: int, j: int) -> str | None:
        if artists[i] and artists[i] == artists[j]:
            return "same artist"
        if i in residue_set and j in residue_set:
            return "residue both sides"
        return None

    def label(i: int) -> dict:
        e = entries[i]
        return {
            "i": i,
            "title": e.get("title"),
            "artist": e.get("artist"),
            "year": e.get("year"),
            "field": raw_fields[i][:QUOTE],
            "truncated": len(raw_fields[i]) > QUOTE,
            "residue": i in residue_set,
            "head": head_of[i],
        }

    # why a pair scored: the tokens carrying the cosine, largest contribution first.
    # This is what turns "linked by one verb" from a claim into a number.
    def contributions(cell_key: str, i: int, j: int, k: int = 6) -> list[list]:
        vi, vj = cell_objects[cell_key].vecs[i], cell_objects[cell_key].vecs[j]
        terms = [(w, vi[w] * vj[w]) for w in vi.keys() & vj.keys()]
        terms.sort(key=lambda t: -t[1])
        return [[w, round(x, 6)] for w, x in terms[:k]]

    # top-N per cell, and the union that goes to adjudication
    union: dict[tuple[int, int], dict] = {}
    for key in cells:
        top = []
        for rank, ((i, j), s) in enumerate(cells[key]["_ranked"][:TOP_N], start=1):
            st = stratum(i, j)
            top.append({"rank": rank, "score": round(s, 6), "i": i, "j": j, "stratum": st})
            if st is None:
                u = union.setdefault((i, j), {"cells": {}, "a": label(i), "b": label(j)})
                shared = contributions(key, i, j)
                u["cells"][key] = {
                    "rank": rank,
                    "score": round(s, 6),
                    "carried_by": shared,
                    # how much of the cosine the single largest shared token carries
                    "top_share": round(shared[0][1] / s, 4) if shared and s else None,
                    "n_shared": len(cell_objects[key].vecs[i].keys() & cell_objects[key].vecs[j].keys()),
                }
        cells[key]["top"] = top
        cells[key]["top_strata"] = {
            "same artist": sum(1 for t in top if t["stratum"] == "same artist"),
            "residue both sides": sum(1 for t in top if t["stratum"] == "residue both sides"),
            "survives": sum(1 for t in top if t["stratum"] is None),
        }
        del cells[key]["_ranked"]
        del cells[key]["_observed"]

    # a stable, provenance-free id for each adjudicable pair, and a shuffled reading
    # order — so that the reading cannot be steered by which cell produced the pair
    pairs = []
    for (i, j), u in union.items():
        pid = hashlib.sha1(f"{i}|{j}".encode()).hexdigest()[:8]
        pairs.append({"id": pid, "i": i, "j": j, "a": u["a"], "b": u["b"], "cells": u["cells"]})
    pairs.sort(key=lambda p: p["id"])
    order = [p["id"] for p in pairs]
    random.Random(args.seed).shuffle(order)

    # how far apart the four rankings are: overlap of the top-N sets
    tops = {k: {(t["i"], t["j"]) for t in cells[k]["top"]} for k in cells}
    overlap = {
        f"{a}|{b}": len(tops[a] & tops[b])
        for x, a in enumerate(sorted(tops)) for b in sorted(tops) if b > a
    }

    out = {
        "_note": (
            "Derived record of the Propp reduction — cycle 002, session 2 of the Atelier. "
            "Every number here is recomputed by tools/neighbour/propp.py from the feed "
            "pinned in `manifest`; nothing is copied by hand. The feed is read, never "
            "mirrored. Verdicts on the pairs live in verdicts.json, kept separate on "
            "purpose: this file is what the instrument computed, that file is what a "
            "reader decided."
        ),
        "session": "cycle-002-session-2",
        "date": dt.date.today().isoformat(),
        "manifest": manifest,
        "n_works": len(entries),
        "reach_outside": {
            "text": "Vladimir Propp, Morphology of the Folktale, 2nd ed., trans. Laurence "
                    "Scott, rev. Louis A. Wagner (Austin: University of Texas Press, 1968), "
                    "ch. II 'The Method and Material', pp. 19-24",
            "field": "structural folkloristics",
            "used_for": "the claim that moves are few and subjects many, and its consequence "
                        "that a move-word recurs across a corpus while a subject-word does not",
        },
        "tokenisation": {
            "source": "tools/neighbour/nn.py (session 1) — imported, not reimplemented",
            "types": len(vocab),
            "tokens": sum(len(d) for d in docs),
            "min_length": 3,
            "stopwords": len(nn.STOP),
        },
        "act_lexicon": {
            "rule": "a token is an act token iff one of its stems (stated English suffix "
                    "rules) appears in this corpus with verbal inflection (-ing or -ed) and "
                    "also bare or with -s/-es",
            "verbal_stems": len(verbal),
            "act_types": len(act),
            "act_types_share": round(len(act) / len(vocab), 4),
            "act_token_share": round(
                sum(1 for d in docs for w in d if w in act) / sum(len(d) for d in docs), 4
            ),
            "lexicon": sorted(act),
        },
        "census": {
            "rule": "class of the field's first word only",
            "counts": census,
            "n": len(entries),
        },
        "cells": cells,
        "top_overlap": overlap,
        "adjudication": {
            "strata_rule": "carried over from session 1 unchanged: a pair is set aside "
                           "before reading if both sides are by the same artist, or if both "
                           "sides carry one of eight fixed harvesting markers",
            "residue_markers": RESIDUE,
            "n_pairs": len(pairs),
            "reading_order": order,
            "pairs": pairs,
        },
    }

    path = pathlib.Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path} ({path.stat().st_size} bytes); {len(pairs)} pairs to adjudicate",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
