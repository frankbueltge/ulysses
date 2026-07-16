"""Tests for the recall detect-bit (refusal.py).

Run (no pytest needed):
    python3 -c "import test_refusal as m; [getattr(m,n)() for n in dir(m) if n.startswith('test_')]; print('ok')"
"""

from store import build_index
from refusal import content_terms, recall_with_refusal


# One content doc plus six filler docs that all share the same function words,
# so "the/for/how/to/work/day/session" saturate the corpus (df 6 of 7) and read
# as common under frac=0.3 (ceiling = int(7*0.3) = 2), while "benford" (df 1)
# stays content-bearing — mirroring how function words saturate the real corpus.
FRAC = 0.3


def _corpus():
    docs = [{"path": "a.md", "heading": "Benford", "text": "benford law digit distribution anomaly fraud"}]
    for i in range(6):
        docs.append({"path": f"f{i}.md", "heading": "Notes",
                     "text": "the work of the session for the day how to do it"})
    return build_index(docs)


def test_genuine_query_is_not_refused():
    idx = _corpus()
    out = recall_with_refusal(idx, "benford digit anomaly", k=1, common_df_frac=FRAC)
    assert out["refused"] is False
    assert out["results"][0]["path"] == "a.md"


def test_stopword_phantom_is_refused():
    # All content words absent; only function words ("how","to","for","the") hit.
    idx = _corpus()
    out = recall_with_refusal(idx, "how to cook rice for dinner", k=1, common_df_frac=FRAC)
    assert out["refused"] is True
    assert "function words" in out["reason"]


def test_no_overlap_at_all_is_refused():
    idx = _corpus()
    out = recall_with_refusal(idx, "xylophone zeppelin quokka", k=1, common_df_frac=FRAC)
    assert out["refused"] is True


def test_content_terms_excludes_common_and_absent():
    idx = _corpus()
    # "the" saturates the corpus (common); "cook" is absent (df 0); "benford" qualifies.
    terms = content_terms("benford the cook", idx, common_df_frac=FRAC)
    assert "benford" in terms
    assert "the" not in terms
    assert "cook" not in terms


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("test_")):
        globals()[name]()
    print("ok")
