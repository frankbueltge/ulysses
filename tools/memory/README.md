# Memory Tool

A semantic-memory retrieval layer that extends recall beyond a single session's context. This tool indexes an engine's markdown archive and retrieves relevant chunks via lexical search.

## Overview

The memory tool processes markdown files from designated directories (journal, works, drafts, dossiers) into a searchable index. It supports two operations:

- **`index`**: scan the repo's markdown sources and build a BM25 index
- **`recall`**: query the index and return ranked results

The index is stored as plain JSONL (one chunk record per line) and is derived data — the source markdown is the canonical archive. The index is gitignored and rebuilt on demand if missing, stale, or corrupt.

### How It Works

The tool splits each markdown file into chunks at heading boundaries (`#`, `##`, `###`). Each chunk records its source path, the nearest preceding heading, and the text under that heading. Chunks are then indexed using BM25, a lexical ranking algorithm that balances term frequency, document frequency, and document length.

When you query, the tool:
1. Loads or rebuilds the index if needed
2. Tokenizes your query (lowercase alphanumeric tokens)
3. Scores each chunk using BM25
4. Returns the top-k chunks with scores > 0 (filters out zero-score "no match" results)

**Backend**: BM25 only. An earlier feasibility probe found embeddings impractical for this repository's scale. Embeddings may be revisited if a server-side embedding connector becomes available.

## Usage

### Indexing

Index a repo root (builds `memory/index.jsonl`):

```bash
python tools/memory/cli.py index /path/to/repo_root
```

Example:

```bash
python tools/memory/cli.py index .
```

This scans `journal/**/*.md`, `works/**/*.md`, `atelier-feedback/**/*.md`, `drafts/**/*.md`, and `memory/dossiers/**/*.md` (repo-relative), chunks each file, and writes the chunks to `memory/index.jsonl`.

### Recall (Query)

Query the index from the repo root:

```bash
python tools/memory/cli.py recall "<query>" -k N
```

The query is a free-text string. Results are JSON on stdout, highest score first.

**Example**:

```bash
cd /path/to/repo_root
python tools/memory/cli.py recall "benford anomaly" -k 10
```

**Example output** (JSON array of chunk records):

```json
[
  {
    "path": "journal/2026-06-15.md",
    "heading": "Forensic Audit",
    "text": "Benford's law anomalies in transaction patterns...",
    "score": 3.742
  },
  {
    "path": "works/counter-measurement.md",
    "heading": "Validation",
    "text": "We tested the signal against Benford distributions...",
    "score": 2.104
  }
]
```

If no chunks match the query, the output is an empty list: `[]`

**Flags**:
- `-k N`: number of results (default: 5)

### Auto-Rebuild Behavior

The `recall` command automatically rebuilds the index when:
- The index file is missing
- The index is older than the newest source file
- The index file is corrupt (unparseable JSON or missing required keys)
- A previously-indexed source file has been deleted

Rebuilds complete in under a second. If the index is corrupt, a diagnostic message is printed to stderr: `index corrupt, rebuilding`

## Index Format

**File**: `memory/index.jsonl` (gitignored)

**Format**: One JSON record per line. Each record is a chunk with these keys:

```json
{
  "path": "journal/2026-06-15.md",
  "heading": "Forensic Audit",
  "text": "Benford's law anomalies in transaction patterns..."
}
```

- `path`: repo-relative path to the source file (using forward slashes)
- `heading`: the nearest preceding heading (level 1-3) or empty string if before any heading
- `text`: the text content under that heading, trimmed of whitespace

**Storage philosophy**: The JSONL file holds only the chunk records themselves — no BM25 statistics (term frequencies, document frequencies, etc.) are persisted. The `recall` command loads the chunks back and calls `build_index()` again. This keeps the on-disk format trivial (easy to inspect, hand-edit, or version-control a snapshot if needed) and costs nothing in practice because rebuilding the BM25 index is fast.

## Reuse

To reuse this tool in another engine repo:

1. Copy the entire `tools/memory/` directory into the target repo
2. Adjust the source globs in `tools/memory/cli.py` (the `SOURCE_GLOBS` list) to match the target repo's structure
3. Run `python tools/memory/cli.py index <repo_root>` to build the index
4. Query via `python tools/memory/cli.py recall "<query>" -k N` from the repo root

**Future**: Extracting this tool to a shared repo (to avoid duplication across engines) is a possible next step but requires coordination on glob patterns and shared dependencies.

## Tests

Run the full test suite:

```bash
python3 -m pytest tools/memory/ -v
```

This runs 19 tests covering chunking, indexing, recall scoring, auto-rebuild behavior, and edge cases (empty index, corrupt files, deleted source files, nonexistent repo root, zero source files, non-positive k, Unicode tokens, etc.).

## Indexed Source Globs

The tool indexes markdown files matching these patterns (repo-relative):

- `journal/**/*.md` — journaled observations or records
- `works/**/*.md` — finished or in-progress works
- `atelier-feedback/**/*.md` — feedback channel
- `drafts/**/*.md` — draft explorations
- `memory/dossiers/**/*.md` — dossier files in the memory directory

To add or remove sources, edit `SOURCE_GLOBS` in `tools/memory/cli.py`.
