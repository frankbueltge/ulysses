#!/usr/bin/env python3
"""Tick 33 — who changed the word?

The build letter of 2026-08-04 quotes a failing test in the site repository,
`src/lib/atelier/dossier.test.ts > the record's own emphasis is rendered, not
printed as syntax > changes no word of any real quotation — only its markers`.
The quotation it disputes is this line's own tick-32 apparatus paragraph.

This script decides the dispute from inside this repository, without reading the
site's code, by asking one question: which of the two strings in the log can be
derived from the record as committed, and by what rule?

Two derivations are run against the paragraph as it stands in TRACE.md:

  A. code-span-aware  — an emphasis pass that treats a `...` span as literal text
  B. code-span-blind  — the same pass with the spans' contents left in the stream

Each is compared to the two strings the log carries (Expected = the test's
fixture, Received = what the site's renderer produced). Nothing is transcribed by
hand: both strings are parsed out of atelier-feedback/2026-08-04.md.

Run:  python3 projects/2026-07-23-negative-parallax/render-marker-collision-tick33.py
No network, no cost.
"""

import pathlib
import re
import sys
import urllib.parse

REPO = pathlib.Path(__file__).resolve().parents[2]
LETTER = REPO / "atelier-feedback" / "2026-08-04.md"
TRACE = REPO / "projects" / "2026-07-23-negative-parallax" / "TRACE.md"


def strings_from_letter():
    """Expected/Received for the dossier assertion, out of the ::error annotation."""
    line = next(
        ln
        for ln in LETTER.read_text(encoding="utf-8").splitlines()
        if ln.startswith("::error") and "dossier.test.ts" in ln
    )
    decoded = urllib.parse.unquote(line)
    got = {}
    for label in ("Expected", "Received"):
        m = re.search(rf'^{label}: "(.*)"$', decoded, re.MULTILINE)
        if not m:
            raise SystemExit(f"no {label} string in the letter")
        got[label] = m.group(1)
    return got["Expected"], got["Received"]


def apparatus_paragraph():
    """The tick-32 apparatus paragraph, verbatim from the committed TRACE."""
    text = TRACE.read_text(encoding="utf-8")
    start = text.index("## Tick 32 — 2026-08-04")
    body = text[start:]
    para = body[body.index("**Pre-registration:**") :]
    para = para[: para.index("\n\n")]
    return " ".join(para.split())  # undo the record's hard wraps


def render(markdown: str, code_span_aware: bool) -> str:
    """Strip emphasis markers, keeping every word. Not a Markdown implementation —
    only the two rules the disputed strings differ on."""
    if code_span_aware:
        # Protect code-span contents from the emphasis pass, then unwrap them.
        parts = markdown.split("`")
        for i in range(1, len(parts), 2):  # odd indices are inside a span
            parts[i] = parts[i].replace("*", "\x00")
        markdown = "".join(parts)
    else:
        markdown = markdown.replace("`", "")

    markdown = re.sub(r"\*\*(.+?)\*\*", r"\1", markdown)  # strong, paired in order

    out, opened = [], False
    for ch in markdown:
        if ch == "*":
            opened = not opened
            if opened and "*" not in markdown[len(out) :]:
                out.append(ch)  # an unpaired marker survives as literal text
            continue
        out.append(ch)
    rendered = "".join(out)
    if opened:  # last marker never found a partner: put it back where it was
        idx = markdown.rindex("*")
        prefix = render_prefix_length(markdown[:idx])
        rendered = rendered[:prefix] + "*" + rendered[prefix:]
    return rendered.replace("\x00", "*")


def render_prefix_length(prefix: str) -> int:
    """How long the rendered text of `prefix` is (all its markers already paired)."""
    return len(prefix.replace("*", ""))


def main():
    expected, received = strings_from_letter()
    source = apparatus_paragraph()

    aware = render(source, code_span_aware=True)
    blind = render(source, code_span_aware=False)

    results = [
        ("code-span-aware  == Received (the site's renderer)", aware == received),
        ("code-span-blind  == Expected (the test's fixture)", blind == expected),
        ("code-span-aware  == Expected", aware == expected),
    ]

    print("source paragraph, from the committed TRACE:")
    print(f"  {source}\n")
    for label, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    print()
    if aware != received:
        print("  aware :", aware)
        print("  recvd :", received)
    if blind != expected:
        print("  blind :", blind)
        print("  expect:", expected)

    # The words that differ between the two disputed strings.
    ew, rw = expected.split(), received.split()
    if len(ew) == len(rw):
        diff = [(a, b) for a, b in zip(ew, rw) if a != b]
        print("words that differ (fixture vs. renderer):")
        for a, b in diff:
            print(f"  {a!r}  vs  {b!r}")

    return 0 if results[0][1] and results[1][1] else 1


if __name__ == "__main__":
    sys.exit(main())
