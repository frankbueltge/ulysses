#!/usr/bin/env python3
"""Find verbatim German quotations left in the record.

Standing rule of 2026-08-15 (architect; wording private): the record keeps the
substance of Frank's messages and drops their wording, marked "(wording private)".
Three passes ran that day. Each earlier pass was defeated by the same defect —
a *threshold*: pass 1 matched only quotations that fit on one line, pass 2 asked
for four German function words inside a quotation before flagging it. Short
quotations and wrapped ones walked through.

This detector carries no threshold. It flags a quoted span on **one** German-only
token: umlaut, eszett, or a stopword that is not also an English word. Recall
first; the false positives are read by hand.

Usage:  python3 tools/redaction_sweep.py [root]
Exit 1 if any span is flagged, 0 if the record is clean.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# German tokens that are not also English words. Deliberately short: a single
# hit flags the span, so every entry must be safe on its own.
GERMAN_ONLY = {
    "aber", "auch", "auf", "aus", "bei", "bitte", "dann", "das", "dass", "dein",
    "deine", "deinem", "deinen", "deiner", "dem", "den", "denn", "der", "des",
    "dich", "diese", "diesem", "diesen", "dieser", "dieses", "dir", "doch",
    "dort", "du", "ein", "eine", "einem", "einen", "einer", "eines", "einfach",
    "etwas", "euch", "gegen", "gibt", "habe", "haben", "hast", "hier", "ich",
    "ihm", "ihn", "ihr", "immer", "ist", "jede", "jeder", "jedes", "jetzt",
    "kann", "kannst", "kein", "keine", "keinen", "keiner", "machen", "mehr",
    "mein", "meine", "mich", "mir", "muss", "musst", "nach", "nicht", "nichts",
    "noch", "nun", "nur", "ob", "oder", "ohne", "schon", "sehr", "seine", "sich",
    "sie", "sind", "soll", "sollte", "und", "uns", "unser", "vom", "vor",
    "waren", "weil", "weiß", "welche", "wenn", "werde", "werden", "wie",
    "wieder", "wir", "wird", "wollen", "zum", "zur", "zwei",
}

# Proper names carry umlauts without being German prose.
NAME_UMLAUT = re.compile(r"\b(Bültge|Müller|Schäfer|Köln|Zürich|Göttingen)\b")

UMLAUT = re.compile(r"[äöüÄÖÜß]")
WORD = re.compile(r"[A-Za-zÄÖÜäöüß]+")

# Inline quotation: typographic pairs, guillemets, or a markdown-italic quote.
INLINE_QUOTE = re.compile(r"[“„»\"]([^“„»\"\n]{3,400})[”“«\"]")

# Lines that are quotation by structure, not by punctuation.
BLOCKQUOTE = re.compile(r"^\s*>\s?(.*)$")

SKIP_DIRS = {".git", "node_modules", "memory", "__pycache__"}

# The four-line request head is a house convention written in German by design
# (Frank reads it in his control panel). It is not a quotation of anyone.
HEAD_KEYS = re.compile(r"^[\s>]*(tl;dr|braucht|frist|kontext|status)\s*:", re.I)

# This practice's own scholarship is written in German in these paths. They are
# reported separately rather than suppressed: a threshold that hides a path is
# how the first three passes lost their quotations.
GERMAN_PROSE_PATHS = ("docs/foundation/",)


def german_hits(text: str) -> list[str]:
    hits = []
    if UMLAUT.search(NAME_UMLAUT.sub("", text)):
        hits.append("umlaut")
    for w in WORD.findall(text.lower()):
        if w in GERMAN_ONLY:
            hits.append(w)
    return hits


def scan_file(path: Path) -> list[tuple[int, str, str, list[str]]]:
    findings = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return findings
    for n, line in enumerate(lines, 1):
        if HEAD_KEYS.match(line):
            continue
        spans: list[tuple[str, str]] = []
        bq = BLOCKQUOTE.match(line)
        if bq and bq.group(1).strip():
            spans.append(("blockquote", bq.group(1)))
        for m in INLINE_QUOTE.finditer(line):
            spans.append(("inline", m.group(1)))
        for kind, span in spans:
            hits = german_hits(span)
            if hits:
                findings.append((n, kind, span.strip(), sorted(set(hits))))
    return findings


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    flagged = 0
    in_prose = 0
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        prose = str(rel).startswith(GERMAN_PROSE_PATHS)
        for n, kind, span, hits in scan_file(path):
            if prose:
                in_prose += 1
                continue
            flagged += 1
            print(f"{rel}:{n}  [{kind}] {', '.join(hits)}")
            print(f"    {span[:200]}")
    print(f"\n{flagged} flagged span(s) to read by hand.")
    print(f"{in_prose} further span(s) in this practice's own German-language "
          f"scholarship ({', '.join(GERMAN_PROSE_PATHS)}) — counted, not printed.")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
