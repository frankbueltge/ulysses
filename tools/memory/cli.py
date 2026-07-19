#!/usr/bin/env python3
"""
Index/recall CLI for the semantic-memory tool.

Backend: BM25 only. An earlier feasibility probe found an embedding backend
impractical for this repo's scale, so there is no backend switch here — just
the plain lexical BM25 index from store.py.

JSONL layout: memory/index.jsonl holds one JSON record per chunk, with the
same {"path", "heading", "text"} shape that chunk_markdown() produces. No BM25
statistics (term frequencies, doc frequencies, etc.) are persisted. Instead,
`recall` reads the chunk records back and calls build_index() on them again
before scoring. This keeps the on-disk format trivial (plain chunk records,
easy to inspect or hand-edit) and costs nothing in practice because a BM25
rebuild over this repo's content is well under a second.

Usage:
    python tools/memory/cli.py index <repo_root>
    python tools/memory/cli.py recall "<query>" -k N
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chunking import chunk_markdown
from store import build_index, recall

# Repo-relative source globs to index.
SOURCE_GLOBS = [
    "journal/**/*.md",
    "works/**/*.md",
    "atelier-feedback/**/*.md",
    "drafts/**/*.md",
    "memory/dossiers/**/*.md",
    "docs/**/*.md",
]

INDEX_RELATIVE_PATH = Path("memory") / "index.jsonl"


def _collect_source_files(repo_root: Path) -> list[Path]:
    """Resolve all source globs against repo_root, de-duplicated and sorted."""
    files = set()
    for pattern in SOURCE_GLOBS:
        files.update(repo_root.glob(pattern))
    return sorted(files)


def _build_chunks(repo_root: Path) -> list[dict]:
    """Chunk every matched source file, using repo-relative paths for provenance."""
    chunks = []
    for file_path in _collect_source_files(repo_root):
        text = file_path.read_text(encoding="utf-8")
        rel_path = file_path.relative_to(repo_root).as_posix()
        chunks.extend(chunk_markdown(text, rel_path))
    return chunks


def _write_index_file(repo_root: Path, chunks: list[dict]) -> Path:
    """Write chunk records as JSONL to memory/index.jsonl, creating memory/ if needed."""
    index_path = repo_root / INDEX_RELATIVE_PATH
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")
    return index_path


def _load_chunks(index_path: Path) -> list[dict] | None:
    """Load chunk records back from the JSONL index file.

    Returns None if the index is corrupt (unparseable or missing required keys).
    """
    chunks = []
    try:
        with index_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    # Validate that record has expected keys.
                    if not isinstance(record, dict) or not all(k in record for k in ["path", "heading", "text"]):
                        return None
                    chunks.append(record)
    except (json.JSONDecodeError, OSError):
        return None
    return chunks


def _index_is_stale(repo_root: Path, index_path: Path) -> bool:
    """True if the index is missing, older than the newest matched source file,
    or if the set of indexed paths no longer matches the set of source files
    currently on disk (e.g. a previously-indexed file was deleted)."""
    if not index_path.exists():
        return True
    index_mtime = index_path.stat().st_mtime
    for file_path in _collect_source_files(repo_root):
        if file_path.stat().st_mtime > index_mtime:
            return True

    current_paths = {
        file_path.relative_to(repo_root).as_posix()
        for file_path in _collect_source_files(repo_root)
    }
    indexed_chunks = _load_chunks(index_path)
    if indexed_chunks is None:
        return True
    indexed_paths = {chunk["path"] for chunk in indexed_chunks}
    if indexed_paths != current_paths:
        return True

    return False


def cmd_index(repo_root_arg: str) -> None:
    repo_root = Path(repo_root_arg).resolve()
    if not repo_root.is_dir():
        sys.stderr.write(f"error: repo root does not exist: {repo_root}\n")
        sys.exit(1)
    chunks = _build_chunks(repo_root)
    if not chunks:
        sys.stderr.write("note: no source files matched\n")
    _write_index_file(repo_root, chunks)


def cmd_recall(query: str, k: int) -> None:
    repo_root = Path.cwd()
    index_path = repo_root / INDEX_RELATIVE_PATH

    if _index_is_stale(repo_root, index_path):
        chunks = _build_chunks(repo_root)
        _write_index_file(repo_root, chunks)
    else:
        chunks = _load_chunks(index_path)
        if chunks is None:
            # Index is corrupt; rebuild it.
            sys.stderr.write("index corrupt, rebuilding\n")
            chunks = _build_chunks(repo_root)
            _write_index_file(repo_root, chunks)

    if not chunks:
        sys.stderr.write("note: no source files matched\n")

    index = build_index(chunks)
    results = recall(index, query, k=k)

    # recall() returns ALL chunks at score 0.0 (insertion order) when no query
    # term matches anything. Filter those out here so "no relevant hits"
    # prints an empty JSON list instead of the whole corpus.
    results = [r for r in results if r["score"] > 0.0]

    print(json.dumps(results))


def main() -> None:
    parser = argparse.ArgumentParser(prog="cli.py", description="Index/recall CLI for the memory tool.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Build the memory index for a repo.")
    index_parser.add_argument("repo_root", help="Path to the repo root to index.")

    recall_parser = subparsers.add_parser("recall", help="Query the memory index.")
    recall_parser.add_argument("query", help="Free-text query.")
    recall_parser.add_argument("-k", type=int, default=5, help="Number of results to return (default: 5).")

    args = parser.parse_args()

    if args.command == "index":
        cmd_index(args.repo_root)
    elif args.command == "recall":
        cmd_recall(args.query, args.k)


if __name__ == "__main__":
    main()
