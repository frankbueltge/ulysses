from chunking import chunk_markdown


def test_splits_by_heading_and_keeps_path():
    md = "# A\nalpha text\n\n## B\nbeta text"
    out = chunk_markdown(md, "journal/x.md")
    assert len(out) == 2
    assert out[0]["heading"] == "A" and "alpha" in out[0]["text"]
    assert out[1]["heading"] == "B" and out[1]["path"] == "journal/x.md"
