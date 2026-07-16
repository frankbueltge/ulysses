"""
A detect-bit for recall — a representable refusal for the memory tool.

Background (journal 2026-07-16, Session 30 → 31). The BM25 recall in store.py
has no state for "your query's subject is not in my corpus." Given any query
that shares a token with the corpus, it returns a ranked list with scores. The
cli.py wrapper only drops results whose score is exactly 0.0, so a query whose
*content* words are all absent still comes back with a confident mid-range top
hit — carried entirely by function words ("how", "to", "for"). The caller reads
the #1 as "the relevant memory." The tool corrects toward the nearest lexical
point and calls it a match; it never says "beyond me."

That is the same shape as a bounded-distance decoder past its radius (Hamming,
1950): it does not fail, it hands back a stranger's word and logs a success.
SECDED buys a machine a *representable limit* for one extra parity bit — it
cannot fix a double error, but it can *see* one and refuse. This module is the
recall tool's cheap analogue: one computed signal that lets recall answer
"beyond me" instead of returning a phantom.

THE DISANALOGY, STATED UP FRONT (it is the honest part). SECDED's guarantee is
a proof: a distance-4 code detects *every* double-bit error. This detect-bit is
a HEURISTIC, not a proof. It catches one clear phantom class — the top hit whose
whole score comes from common/function terms, no content term supporting it —
and it will let another class through: a query built from real but *unrelated*
corpus content words (their subject absent, their vocabulary incidentally
present) scores like a genuine query and is NOT refused. That residual is the
recall analogue of a weight-4 error landing exactly on another valid codeword:
the detector is designed for one class and is silent on the other. The measured
false-refusal cost and the residual miss are reported in
works/2026-07-16-the-missing-detect-bit/ — no guarantee is claimed here.

The knob has a meaning, not a magic value: a query term counts as *content-
bearing* when it occurs in the corpus (df >= 1) and in no more than
`common_df_frac` of the chunks (default 5%). Terms above that frequency are
treated as common (function-word-like) and cannot, on their own, support a
match. The detect-bit refuses when the top-ranked chunk contains zero
content-bearing query terms.
"""

from store import _tokenize, _score, recall


def _common_df_ceiling(doc_count: int, common_df_frac: float) -> int:
    """Highest df a term may have and still count as content-bearing. Floored at
    1: a term in exactly one chunk is maximally discriminating regardless of
    corpus size, so it always qualifies (this also keeps tiny corpora sane, where
    doc_count * common_df_frac would round to 0 and exclude everything)."""
    return max(1, int(doc_count * common_df_frac))


def content_terms(query: str, index: dict, common_df_frac: float = 0.05) -> list[str]:
    """Distinct query terms that occur in the corpus (df >= 1) and in at most
    `common_df_frac` of the chunks. These are the terms a *genuine* match should
    rest on; function words and near-universal terms are excluded."""
    ceiling = _common_df_ceiling(index["doc_count"], common_df_frac)
    seen = set()
    out = []
    for term in _tokenize(query):
        if term in seen:
            continue
        seen.add(term)
        df = index["doc_freqs"].get(term, 0)
        if 1 <= df <= ceiling:
            out.append(term)
    return out


def content_support(chunk_idx: int, query: str, index: dict, common_df_frac: float = 0.05) -> dict:
    """How much of a chunk's match rests on content-bearing query terms.

    Returns the count of distinct content-bearing query terms actually present
    in the chunk, the BM25 sub-score they contribute, and the chunk's full BM25
    score against the query — enough for a caller to see whether the match is
    carried by content or by function words alone.
    """
    terms = content_terms(query, index, common_df_frac)
    present = [t for t in terms if index["doc_term_freqs"][chunk_idx].get(t, 0) > 0]
    content_subscore = _score(chunk_idx, present, index) if present else 0.0
    full_score = _score(chunk_idx, _tokenize(query), index)
    return {
        "content_terms_in_query": terms,
        "content_terms_in_chunk": present,
        "content_overlap": len(present),
        "content_subscore": content_subscore,
        "full_score": full_score,
    }


def recall_with_refusal(index: dict, query: str, k: int = 5, common_df_frac: float = 0.05) -> dict:
    """Recall with a representable limit.

    Returns a dict:
      {"refused": True,  "reason": ..., "diagnostic": {...}}                  or
      {"refused": False, "results": [...ranked chunks...], "diagnostic": {...}}

    Refusal rule (the detect-bit): refuse when the top-ranked chunk contains no
    content-bearing query term — i.e. the match is carried entirely by common /
    function words. This is a flagged "beyond me," not a silent phantom. It is a
    heuristic, not a guarantee (see module docstring): a query made of real but
    unrelated corpus content words will pass this bit and still be a phantom.
    """
    results = recall(index, query, k=k)
    results = [r for r in results if r["score"] > 0.0]

    if not results:
        return {
            "refused": True,
            "reason": "no lexical overlap with the corpus at all",
            "diagnostic": {"content_terms_in_query": content_terms(query, index, common_df_frac)},
        }

    # Find the top chunk's index in the underlying corpus to inspect its support.
    top = results[0]
    top_idx = next(
        i for i, c in enumerate(index["chunks"])
        if c["path"] == top["path"] and c["heading"] == top["heading"] and c["text"] == top["text"]
    )
    support = content_support(top_idx, query, index, common_df_frac)

    if support["content_overlap"] == 0:
        return {
            "refused": True,
            "reason": (
                "top match is carried entirely by common/function words; "
                "no content-bearing query term is present in it"
            ),
            "diagnostic": support,
        }

    return {"refused": False, "results": results, "diagnostic": support}
