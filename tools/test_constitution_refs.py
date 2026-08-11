#!/usr/bin/env python3
"""Every path the constitution names must exist.

Written 2026-08-12, after the third instance of one failure in six weeks:

  · 2026-07-18  the unit of work moved to `projects/`; the memory tool's source list did not
                follow, so a line's whole record became unreachable by recall
  · 2026-08-08  v6 folded v5 and dropped the Research Foundation to a single appendix path,
                with no part of its ~57,000 words named as the text a session carries
  · 2026-08-12  §8 was amended and named `12-FOUNDATION-REQUIREMENTS-FINAL.md` by bare
                filename rather than by path — caught by this test on its first run

Each time the constitution was edited as prose and the thing it pointed at was left behind.
Nothing failed loudly, because a dead pointer in a protocol produces no error: the session
simply does not find what it was told to use, and reads everything instead.

This test makes that class loud. A path named in `PROTOCOL.md` either resolves in this
repository, or is declared below as living elsewhere — with the repository it lives in. There
is no third option, and "it is obvious from context" is not one.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = REPO_ROOT / "PROTOCOL.md"

# Paths that legitimately live outside this repository. Each names where, so a reader can go
# and look, and so that "missing" and "elsewhere" never get confused again.
ELSEWHERE = {
    "docs/design/2026-08-08-research-ecology-v2.md": "site repo (frankbueltge.de)",
    "docs/design/2026-08-12-the-floors-that-were-never-run.md": "site repo (frankbueltge.de)",
    "docs/post-office/packet-convention.md": "site repo (frankbueltge.de)",
}

# Names that are per-record files, not repo paths: they exist inside a project or a work
# directory, and checking them at the repo root would be a category error.
PER_RECORD = {
    "PUBLICATION.json", "DECISION.md", "SCORE.md", "TRACE.md", "APPARATUS.md",
    "EXPOSITION.md", "meta.json", "packet.json", "data.json", "work.md",
}


def named_paths(text: str) -> set[str]:
    """Every backticked token that looks like a path or a file this repo should hold."""
    found = set()
    for token in re.findall(r"`([^`\s]+)`", text):
        token = token.rstrip(".,;:)")
        if token in PER_RECORD:
            continue
        # a directory (`works/`) or a file with a known extension
        if token.endswith("/") or re.search(r"\.(md|py|json|yml|yaml|jsonl)$", token):
            # skip shell fragments and globs — those are checked by test_sources.py
            if any(ch in token for ch in "*<>|") or token.startswith("-"):
                continue
            found.add(token)
    return found


def test_every_named_path_resolves_or_is_declared_elsewhere() -> None:
    text = CONSTITUTION.read_text(encoding="utf-8")
    dead = []
    for token in sorted(named_paths(text)):
        if token in ELSEWHERE:
            continue
        if (REPO_ROOT / token).exists():
            continue
        dead.append(token)
    assert not dead, (
        "PROTOCOL.md names paths that do not exist here and are not declared as living "
        f"elsewhere: {dead}.\n"
        "A dead pointer in a constitution fails silently — the session does not find what it "
        "was told to use and reads everything instead. Fix the path, or add it to ELSEWHERE "
        "with the repository that holds it."
    )


def test_declared_elsewhere_entries_are_still_needed() -> None:
    """An ELSEWHERE entry that the constitution no longer mentions is stale bookkeeping."""
    text = CONSTITUTION.read_text(encoding="utf-8")
    unused = [path for path in ELSEWHERE if path not in text]
    assert not unused, (
        f"these are declared as living elsewhere but the constitution no longer names them: "
        f"{unused}. Remove them from ELSEWHERE."
    )
