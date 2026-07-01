import math
import re


def _tokenize(text: str) -> list[str]:
    """Lowercase and extract Unicode-aware word tokens (letters/digits, no underscore)."""
    return re.findall(r"[^\W_]+", text.lower())


def build_index(chunks: list[dict]) -> dict:
    """
    Build a BM25 index over a list of chunk records.

    Each chunk is expected to have "path", "heading", and "text" keys.
    The returned index is a plain-JSON-serializable dict containing everything
    recall() needs: per-chunk term frequencies, document frequencies, and the
    original chunk records.

    Args:
        chunks: list of dicts with keys: path, heading, text

    Returns:
        dict index usable by recall()
    """
    doc_term_freqs = []  # list[dict[str, int]], one per chunk
    doc_lengths = []  # list[int], token count per chunk

    for chunk in chunks:
        # Heading tokens are folded into the indexed text so a query matching
        # only the heading (e.g. "Benford") can still surface the chunk.
        combined_text = chunk["heading"] + " " + chunk["text"]
        tokens = _tokenize(combined_text)
        term_freqs = {}
        for token in tokens:
            term_freqs[token] = term_freqs.get(token, 0) + 1
        doc_term_freqs.append(term_freqs)
        doc_lengths.append(len(tokens))

    doc_count = len(chunks)

    doc_freqs = {}  # term -> number of chunks containing it
    for term_freqs in doc_term_freqs:
        for term in term_freqs:
            doc_freqs[term] = doc_freqs.get(term, 0) + 1

    avg_doc_length = (sum(doc_lengths) / doc_count) if doc_count else 0.0

    return {
        "doc_count": doc_count,
        "avg_doc_length": avg_doc_length,
        "doc_lengths": doc_lengths,
        "doc_term_freqs": doc_term_freqs,
        "doc_freqs": doc_freqs,
        "chunks": chunks,
    }


def _idf(term: str, index: dict) -> float:
    """
    BM25 idf for a term, using the "+1" variant:
    log((N - df + 0.5) / (df + 0.5) + 1)
    This keeps idf non-negative even for terms that appear in most/all documents,
    unlike the classic Robertson-Sparck-Jones formula which can go negative.
    """
    doc_count = index["doc_count"]
    doc_freq = index["doc_freqs"].get(term, 0)
    return math.log((doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)


def _score(chunk_idx: int, query_terms: list[str], index: dict, k1: float = 1.5, b: float = 0.75) -> float:
    """BM25 score of one chunk against the tokenized query."""
    term_freqs = index["doc_term_freqs"][chunk_idx]
    doc_length = index["doc_lengths"][chunk_idx]
    avg_doc_length = index["avg_doc_length"]

    score = 0.0
    for term in query_terms:
        tf = term_freqs.get(term, 0)
        if tf == 0:
            continue
        idf = _idf(term, index)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length if avg_doc_length else 0))
        score += idf * (numerator / denominator)
    return score


def recall(index: dict, query: str, k: int = 5) -> list[dict]:
    """
    Return the top-k chunks ranked by BM25 score against the query.

    Args:
        index: dict returned by build_index()
        query: free-text query string
        k: maximum number of results to return

    Returns:
        list of dicts with keys: path, heading, text, score (highest score first)

    Zero-match contract: if the query's terms match nothing in the index, this
    returns ALL chunks at score 0.0 (in existing/insertion order), not an empty
    list. Callers that want "no relevant hits" to mean an empty result must
    filter on score > 0.0 themselves (see cli.py's cmd_recall, which does
    exactly this). An empty query string or an empty index still returns [].
    """
    doc_count = index["doc_count"]
    query_terms = _tokenize(query)

    if doc_count == 0 or not query_terms:
        return []

    if k <= 0:
        return []

    scored = []
    for chunk_idx, chunk in enumerate(index["chunks"]):
        score = _score(chunk_idx, query_terms, index)
        scored.append((score, chunk_idx))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    results = []
    for score, chunk_idx in scored[:k]:
        chunk = index["chunks"][chunk_idx]
        results.append({
            "path": chunk["path"],
            "heading": chunk["heading"],
            "text": chunk["text"],
            "score": float(score),
        })
    return results
