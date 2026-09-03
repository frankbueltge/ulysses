#!/usr/bin/env python3
"""The neighbour instrument — a calibrated "has the world already done this?" check.

The house keeps an atlas of neighbouring works (data art and adjacent practice), and
the duty that rests on it is a curatorial one: a new work must state its daylight from
the neighbours it is nearest to. The usual machine answer to "is this new?" is a
similarity ranking — nearest neighbour, with a score. A score is worthless without the
score you would have got by chance, and no such number exists for this apparatus.

This instrument supplies it. For every work in the atlas it measures

    s(w) = max over the other works of cosine similarity between decisive moves,

and then manufactures the negative case: surrogate texts of the same length, drawn
from the corpus's own word frequencies, measured against the same corpus by the same
route. The gap between the two distributions is the only thing that makes a
similarity score mean anything.

Method, stated so it can be argued with:

  * Text: the `decisive_move` field only — the sentence the atlas uses to say what a
    work actually does. Not the title, not the venue.
  * Tokens: lowercased runs of a-z of length >= 3, a fixed stopword list removed
    (below, in this file). No stemming, no lemmatisation, unigrams only. Unigrams are
    the honest baseline and also the weak point: they cannot tell a subject from a
    move, which is what the measurement below is really about.
  * Weights: tf-idf, tf = raw count, idf = ln(N / df), vectors L2-normalised.
  * Observed: leave-one-out — a work is never its own neighbour.
  * Null: for each work, M surrogate documents with that work's exact token count,
    tokens drawn i.i.d. from the corpus-wide token-frequency distribution, each
    surrogate scored against the same 520 other works. Seeded, so it re-runs identically.

The feed is read, never mirrored (SITE-API, "feeds, never copies"). What is committed
beside the artifact is derived: scores, distributions, and the handful of pairs the
session actually reads and names. Re-running against a later feed gives different
numbers because the atlas grows daily; the manifest pins which state was measured.

    python3 tools/neighbour/nn.py --fetch --out window/cycle-002-session-1/data.json
    python3 tools/neighbour/nn.py --atlas /path/werke.json --out ...

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

FEED = "https://frankbueltge.de/atlas/werke.json"

TOP_N = 40      # how many ranked pairs are named and quoted in the derived record
QUOTE = 240     # characters of the decisive-move field quoted per named pair

# A fixed, short stopword list. Deliberately not a library's: a list you can read is a
# list you can argue with, and every word here was in the corpus's top band.
STOP = {
    "the", "and", "for", "that", "with", "from", "into", "its", "his", "her", "their",
    "are", "was", "were", "has", "have", "had", "not", "but", "which", "who", "whom",
    "this", "these", "those", "then", "than", "them", "they", "you", "your", "our",
    "out", "over", "each", "into", "onto", "upon", "about", "also", "such", "been",
    "being", "both", "own", "same", "some", "any", "all", "one", "two", "can", "will",
    "would", "could", "may", "might", "must", "does", "did", "done", "how", "what",
    "when", "where", "while", "into", "per", "via", "off", "under", "between", "through",
    "against", "without", "within", "across", "after", "before", "during", "because",
    "itself", "himself", "herself", "themselves", "there", "here", "other", "another",
    "more", "most", "less", "least", "very", "only", "just", "into", "using", "used",
    "use", "uses", "make", "makes", "made", "making", "work", "works", "piece", "shows",
    "show", "showing", "shown",
}

WORD = re.compile(r"[a-z]+")


def tokens(text: str) -> list[str]:
    return [w for w in WORD.findall(text.lower()) if len(w) >= 3 and w not in STOP]


def work_id(entry: dict) -> str:
    key = f"{entry.get('title','')}|{entry.get('artist','')}|{entry.get('year','')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]


# ---------------------------------------------------------------- the corpus


class Corpus:
    """tf-idf over the decisive moves, with an inverted index for sparse scoring."""

    def __init__(self, docs: list[list[str]]):
        self.n = len(docs)
        self.docs = docs
        df: dict[str, int] = {}
        for d in docs:
            for w in set(d):
                df[w] = df.get(w, 0) + 1
        self.df = df
        self.idf = {w: math.log(self.n / c) for w, c in df.items()}
        # token-frequency pool for the null, and its cumulative weights
        pool: dict[str, int] = {}
        for d in docs:
            for w in d:
                pool[w] = pool.get(w, 0) + 1
        self.pool_words = sorted(pool)
        self.pool_weights = [pool[w] for w in self.pool_words]
        self.n_tokens = sum(self.pool_weights)
        # document vectors, L2-normalised
        self.vecs: list[dict[str, float]] = []
        for d in docs:
            tf: dict[str, int] = {}
            for w in d:
                tf[w] = tf.get(w, 0) + 1
            v = {w: c * self.idf[w] for w, c in tf.items()}
            norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
            self.vecs.append({w: x / norm for w, x in v.items()})
        # inverted index: word -> [(doc, weight), ...]
        inv: dict[str, list[tuple[int, float]]] = {}
        for i, v in enumerate(self.vecs):
            for w, x in v.items():
                inv.setdefault(w, []).append((i, x))
        self.inv = inv

    def vectorise(self, toks: list[str]) -> dict[str, float]:
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

    def best(self, vec: dict[str, float], skip: int | None = None) -> tuple[float, int]:
        acc = self.scores(vec, skip)
        if not acc:
            return 0.0, -1
        j = max(acc, key=lambda k: acc[k])
        return acc[j], j


# ---------------------------------------------------------------- statistics


def quantile(sorted_vals: list[float], q: float) -> float:
    """Linear-interpolated quantile of an already sorted list."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def histogram(vals: list[float], lo: float, hi: float, bins: int) -> list[int]:
    out = [0] * bins
    width = (hi - lo) / bins
    for v in vals:
        k = int((v - lo) / width)
        if k < 0:
            k = 0
        if k >= bins:
            k = bins - 1
        out[k] += 1
    return out


# ---------------------------------------------------------------- the run


def run(entries: list[dict], manifest: dict, m_per_work: int, seed: int) -> dict:
    docs = [tokens(e.get("decisive_move") or "") for e in entries]
    corpus = Corpus(docs)
    ids = [work_id(e) for e in entries]

    # --- observed: leave-one-out nearest neighbour
    observed: list[float] = []
    partner: list[int] = []
    for i, v in enumerate(corpus.vecs):
        s, j = corpus.best(v, skip=i)
        observed.append(s)
        partner.append(j)

    # --- null: surrogate texts, same length, corpus word frequencies
    rng = random.Random(seed)
    null_all: list[float] = []
    null_per_work: list[float] = []          # the median surrogate score of each work
    for i, d in enumerate(docs):
        L = len(d)
        best_here: list[float] = []
        for _ in range(m_per_work):
            draw = rng.choices(corpus.pool_words, weights=corpus.pool_weights, k=L) if L else []
            s, _j = corpus.best(corpus.vectorise(draw), skip=i)
            best_here.append(s)
        null_all.extend(best_here)
        best_here.sort()
        null_per_work.append(quantile(best_here, 0.5))

    obs_sorted = sorted(observed)
    null_sorted = sorted(null_all)

    t = {
        "t50": quantile(null_sorted, 0.50),
        "t95": quantile(null_sorted, 0.95),
        "t99": quantile(null_sorted, 0.99),
        "t999": quantile(null_sorted, 0.999),
        "tmax": null_sorted[-1],
    }

    def count_above(vals: list[float], cut: float) -> int:
        return sum(1 for v in vals if v > cut)

    # --- distinct pairs, ranked. i<j, score = cosine
    seen: dict[tuple[int, int], float] = {}
    for i, v in enumerate(corpus.vecs):
        acc = corpus.scores(v, skip=i)
        for j, s in acc.items():
            key = (i, j) if i < j else (j, i)
            if s > seen.get(key, -1.0):
                seen[key] = s
    ranked = sorted(seen.items(), key=lambda kv: -kv[1])

    def cluster_overlap(a: int, b: int) -> int:
        ca = set(entries[a].get("clusters") or [])
        cb = set(entries[b].get("clusters") or [])
        return len(ca & cb)

    # --- does similarity track the atlas's own curatorial categories?
    #     Compared over the pairs above the calibrated cut against all pairs.
    all_pairs = list(seen.items())
    def share(pairs) -> dict:
        if not pairs:
            return {"n": 0, "cluster_share": None, "axis_share": None}
        n = len(pairs)
        c = sum(1 for (i, j), _ in pairs if cluster_overlap(i, j) > 0)
        a = sum(1 for (i, j), _ in pairs if entries[i].get("axis_pole") == entries[j].get("axis_pole"))
        return {"n": n, "cluster_share": round(c / n, 4), "axis_share": round(a / n, 4)}

    above99 = [p for p in all_pairs if p[1] > t["t99"]]

    # --- what is actually sitting at the top of the ranking
    # Two things a similarity score cannot tell apart from a neighbourhood, and one
    # this instrument would have reported as one if the null had not made us look.
    #
    # (a) the same artist twice: an artist statement repeated across that artist's
    #     entries is a high-similarity pair and is not evidence that anyone else has
    #     done the thing.
    # (b) catalogue residue: fragments of the harvesting apparatus that ended up in
    #     the field instead of a description of the move. The markers are fixed here,
    #     lowercase substring tests on the raw field, and each is counted separately.
    RESIDUE = [
        "description edit", "outside link", "inception:", "attributed to:",
        "access url:", "variant edit", "static files", "&quot;",
    ]
    raw = [(e.get("decisive_move") or "") for e in entries]
    low = [r.lower() for r in raw]
    residue_hits = {m: sum(1 for r in low if m in r) for m in RESIDUE}
    residue_any = [i for i, r in enumerate(low) if any(m in r for m in RESIDUE)]

    dup_groups: dict[str, list[int]] = {}
    for i, r in enumerate(raw):
        dup_groups.setdefault(r.strip(), []).append(i)
    dups = {k: v for k, v in dup_groups.items() if len(v) > 1}

    artists = [(e.get("artist") or "").strip().lower() for e in entries]
    residue_set = set(residue_any)

    def strata(pairs) -> dict:
        n = len(pairs)
        if not n:
            return {"n": 0}
        same_artist = {(i, j) for (i, j), _ in pairs if artists[i] and artists[i] == artists[j]}
        res = {(i, j) for (i, j), _ in pairs if i in residue_set and j in residue_set}
        any_res = {(i, j) for (i, j), _ in pairs if i in residue_set or j in residue_set}
        either = same_artist | res
        return {
            "n": n,
            "same_artist": len(same_artist),
            "both_residue": len(res),
            "any_residue": len(any_res),
            "either": len(either),
            "surviving": n - len(either),
            "same_artist_share": round(len(same_artist) / n, 4),
            "both_residue_share": round(len(res) / n, 4),
        }

    top_pairs = []
    for (i, j), s in ranked[:TOP_N]:
        same_artist = bool(artists[i]) and artists[i] == artists[j]
        both_res = i in residue_set and j in residue_set
        top_pairs.append({
            "rank": len(top_pairs) + 1,
            "score": round(s, 4),
            "a": {"id": ids[i], "title": entries[i]["title"], "artist": entries[i]["artist"],
                  "year": entries[i]["year"], "axis_pole": entries[i].get("axis_pole"),
                  "clusters": entries[i].get("clusters"),
                  "move": (entries[i].get("decisive_move") or "")[:QUOTE]},
            "b": {"id": ids[j], "title": entries[j]["title"], "artist": entries[j]["artist"],
                  "year": entries[j]["year"], "axis_pole": entries[j].get("axis_pole"),
                  "clusters": entries[j].get("clusters"),
                  "move": (entries[j].get("decisive_move") or "")[:QUOTE]},
            "cluster_overlap": cluster_overlap(i, j),
            "same_axis": entries[i].get("axis_pole") == entries[j].get("axis_pole"),
            "same_artist": same_artist,
            "both_residue": both_res,
            "identical_text": raw[i].strip() == raw[j].strip(),
            "survives": not (same_artist or both_res),
        })

    rows = [{"id": ids[i], "s": round(observed[i], 4), "nn": ids[partner[i]] if partner[i] >= 0 else None,
             "len": len(docs[i]), "null": round(null_per_work[i], 4)} for i in range(corpus.n)]

    return {
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": manifest,
        "method": {
            "field": "decisive_move",
            "tokens": "lowercase [a-z]{3,}, fixed stopword list, no stemming, unigrams",
            "weights": "tf-idf, idf = ln(N/df), L2-normalised",
            "observed": "leave-one-out maximum cosine",
            "null": f"{m_per_work} surrogates per work, same token count, i.i.d. draws "
                    f"from the corpus token-frequency pool, scored against the same 520 others",
            "seed": seed,
            "stopwords": sorted(STOP),
        },
        "corpus": {
            "n_works": corpus.n,
            "n_tokens": corpus.n_tokens,
            "vocab": len(corpus.df),
            "median_len": quantile(sorted(len(d) for d in docs), 0.5),
            "min_len": min(len(d) for d in docs),
            "max_len": max(len(d) for d in docs),
        },
        "observed": {
            "mean": round(sum(observed) / len(observed), 4),
            "median": round(quantile(obs_sorted, 0.5), 4),
            "q25": round(quantile(obs_sorted, 0.25), 4),
            "q75": round(quantile(obs_sorted, 0.75), 4),
            "min": round(obs_sorted[0], 4),
            "max": round(obs_sorted[-1], 4),
            "hist": histogram(observed, 0.0, 1.0, 50),
        },
        "null": {
            "m_per_work": m_per_work,
            "n_surrogates": len(null_all),
            "mean": round(sum(null_all) / len(null_all), 4),
            "median": round(quantile(null_sorted, 0.5), 4),
            "max": round(null_sorted[-1], 4),
            "hist": histogram(null_all, 0.0, 1.0, 50),
        },
        "thresholds": {k: round(v, 4) for k, v in t.items()},
        "flagged": {
            "calibrated_t95": count_above(observed, t["t95"]),
            "calibrated_t99": count_above(observed, t["t99"]),
            "calibrated_t999": count_above(observed, t["t999"]),
            "assumed_0_3": count_above(observed, 0.30),
            "assumed_0_5": count_above(observed, 0.50),
            "assumed_0_7": count_above(observed, 0.70),
        },
        "pairs_total": len(all_pairs),
        "pairs_above_t99": len(above99),
        # The whole finding is what happens as the line moves, so the line's consequences
        # are tabulated rather than asserted at one place: for each cut, how many works
        # are flagged and what the flagged pairs decompose into.
        "curve": [
            {
                "cut": round(cut, 3),
                "works": sum(1 for v in observed if v > cut),
                **{k: v for k, v in strata([p for p in all_pairs if p[1] > cut]).items()
                   if k in ("n", "same_artist", "both_residue", "any_residue", "either", "surviving")},
            }
            # the exact calibrated cut is a grid point, so the page's slider and its
            # prose cannot disagree by a few pairs at the one value that matters
            for cut in sorted([0.10 + 0.005 * k for k in range(101)] + [t["t99"]])
        ],
        "field_condition": {
            "residue_markers": residue_hits,
            "entries_with_any_residue": len(residue_any),
            "duplicate_texts": {
                "groups": len(dups),
                "entries": sum(len(v) for v in dups.values()),
            },
            "strata_above_t99": strata(above99),
            "strata_all_pairs": strata(all_pairs),
            "strata_top": strata(ranked[:TOP_N]),
        },
        "categories": {
            "all_pairs": share(all_pairs),
            "above_t99": share(above99),
            "top40": share(ranked[:40]),
        },
        "top_pairs": top_pairs,
        "rows": rows,
    }


def fetch(url: str) -> tuple[dict, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "atelier-neighbour-instrument/1 (research; one fetch)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    manifest = {
        "url": url,
        "fetched_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    return json.loads(raw), manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--atlas", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--m", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260903)
    a = ap.parse_args()

    if a.fetch:
        data, manifest = fetch(FEED)
    elif a.atlas:
        raw = a.atlas.read_bytes()
        data = json.loads(raw)
        manifest = {"url": FEED, "fetched_utc": "from local copy",
                    "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    else:
        print("give --fetch or --atlas PATH", file=sys.stderr)
        return 2

    manifest["count_declared"] = data.get("count")
    manifest["licence"] = data.get("licence")
    entries = [e for e in data["entries"] if (e.get("decisive_move") or "").strip()]
    manifest["count_used"] = len(entries)

    out = run(entries, manifest, a.m, a.seed)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(entries)} works · observed median {out['observed']['median']} · "
          f"null t99 {out['thresholds']['t99']} · flagged {out['flagged']['calibrated_t99']} "
          f"(t99) vs {out['flagged']['assumed_0_5']} (assumed 0.5) → {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
