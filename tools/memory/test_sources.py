#!/usr/bin/env python3
"""The index must see everywhere the practice writes.

This test exists because of a failure with a date. `SOURCE_GLOBS` was written on 2026-07-02.
On 2026-07-18 the unit of work changed from the night to the work-line and the practice began
writing its records into `projects/`. The constitution was rewritten three times in the weeks
that followed (v4, v5, v6); the source list was not touched once.

The consequence was not a broken tool — `recall` kept working perfectly on a corpus that no
longer contained the work. The only way to know where a line stood was to read it end to end,
and by 2026-08-12 one line's record had reached 196,000 words.

So the check is not "does the index work". It is: **does the index still point at the places
this repository actually keeps its records.** A directory that holds markdown records and is
not covered by a glob fails here, which is the check that did not exist for six weeks.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli import SOURCE_GLOBS, _collect_source_files

REPO_ROOT = Path(__file__).resolve().parents[2]

# Directories that hold the practice's records. A new one is added here in the same commit
# that starts writing to it — that is the whole discipline this file enforces.
RECORD_DIRS = ["journal", "works", "projects", "atelier-feedback", "drafts", "window"]

# Everything else at the repo root, with the reason it is not indexed. Listing the exclusions
# explicitly means a new top-level directory cannot be silently forgotten: it is either a
# record directory (indexed) or it is named here.
NOT_RECORDS = {
    "archive": "superseded texts, kept unchanged; recall should return the live text",
    "deliveries": "prepared post-office packets. The letter in one is a verbatim copy of a "
                  "record that lives in projects/ and is indexed there, so indexing the copy "
                  "too would return the same text twice and let the two drift — the packet's "
                  "own README refuses to duplicate its instrument for that reason. Same "
                  "ground as archive/: recall should return the canonical text",
    "atlas": "reference collection, not this practice's own record",
    "docs": "indexed already",
    "encounters": "contact-zone records held by the ecology, not by this practice",
    "governance": "delegation documents, read directly and rarely",
    "memory": "the index itself, plus dossiers which are indexed",
    "pulse": "derived activity data, not prose",
    "seeds": "material offered to the practice from outside, not a record it wrote; each seed's "
             "README says the directory may be deleted freely, and REQUESTS.md holds the durable "
             "note that it was offered",
    "tools": "code",
}


def _covered(rel_dir: str) -> bool:
    return any(glob.startswith(f"{rel_dir}/") for glob in SOURCE_GLOBS)


def test_every_record_directory_is_indexed() -> None:
    missing = [d for d in RECORD_DIRS if (REPO_ROOT / d).is_dir() and not _covered(d)]
    assert not missing, (
        f"these directories hold records but no SOURCE_GLOBS entry reaches them: {missing}. "
        "A session cannot recall what is not indexed, so it will read the whole record instead "
        "— the failure of 2026-07-18. Add the glob in the commit that starts writing there."
    )


def test_no_top_level_directory_is_silently_unindexed() -> None:
    """A new directory is either a record directory or an explicitly named exclusion."""
    unaccounted = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if entry.name in RECORD_DIRS or entry.name in NOT_RECORDS:
            continue
        if not any(entry.rglob("*.md")):
            continue
        unaccounted.append(entry.name)
    assert not unaccounted, (
        f"top-level directories holding markdown are neither indexed nor declared non-records: "
        f"{unaccounted}. Add each to RECORD_DIRS (and to SOURCE_GLOBS) or to NOT_RECORDS with "
        "the reason it is not a record."
    )


def test_the_foundation_synthesis_exists_and_is_indexed() -> None:
    """The two files §8 names as the practice's standing basis must be there and reachable.

    The Foundation is ~57,000 words across five tranches and cannot be read at session start.
    §8 therefore names a synthesis as the text that is actually carried. If either file is
    renamed or moved, the protocol would be pointing a session at nothing — silently, because
    a missing file simply returns no recall hits rather than an error.
    """
    named = [
        "docs/foundation/tranche-5-final/11-FINAL-RESEARCH-FOUNDATION-SYNTHESIS.md",
        "docs/foundation/tranche-5-final/12-FOUNDATION-REQUIREMENTS-FINAL.md",
    ]
    missing = [rel for rel in named if not (REPO_ROOT / rel).is_file()]
    assert not missing, (
        f"PROTOCOL.md §8 names these as the Foundation's standing text and they are gone: "
        f"{missing}. Either restore them or amend §8 — a protocol pointing at a missing file "
        "sends the session back to reading 57,000 words."
    )
    indexed = {p.resolve() for p in _collect_source_files(REPO_ROOT)}
    unreachable = [rel for rel in named if (REPO_ROOT / rel).resolve() not in indexed]
    assert not unreachable, (
        f"the Foundation's standing text is not covered by SOURCE_GLOBS: {unreachable}"
    )


def test_the_work_line_record_is_actually_reachable() -> None:
    """The regression itself: a real project's SCORE must be among the indexed files."""
    projects = REPO_ROOT / "projects"
    if not projects.is_dir():
        return
    scores = {p.resolve() for p in projects.glob("*/SCORE.md")}
    if not scores:
        return
    indexed = {p.resolve() for p in _collect_source_files(REPO_ROOT)}
    assert scores & indexed, (
        "no work-line SCORE.md is indexed. This is the exact state the repository was in "
        "between 2026-07-18 and 2026-08-12."
    )
