#!/usr/bin/env python3
"""Read a paper's full text without the hosted converter.

The attached academic-paper connector's PDF-to-Markdown route has been failing
since 2026-07-24 with `libxcb.so.1: cannot open shared object file` — a library
missing from the converter's own image, which runs as a hosted service and is
not ours to repair (REQUESTS.md, 2026-08-03). Search and abstract retrieval on
the same connector are unaffected; only the conversion step is.

This is the fallback made explicit. The practice was already extracting text
locally and disclosing it per record, which works — but it depended on a tool
being present, unchecked, and would have failed silently and differently on the
day it was not. So the dependency is named here, checked before use, and the
tool refuses rather than half-works.

What it prints to stderr, and what belongs in the record beside any quotation
taken this way:

    source, retrieval date, sha256 of the bytes read, extractor and its version

The hash is the point. Two readings of "the same paper" are only the same
reading if the bytes were the same, and a text extracted from a PDF is a
derivative — it can lose a column, a ligature, a footnote marker. Quote from it
the way the practice quotes anything else: with the path it was read from.

    tools/paper_text.py 2101.11641v3
    tools/paper_text.py paper.pdf -o paper.txt
    tools/paper_text.py https://arxiv.org/pdf/2101.11641v3

Exit codes: 0 read, 2 dependency missing, 3 source unreachable, 4 unreadable.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

# arXiv ids in both schemes: 2101.11641v3 (since 2007) and math/0111153 (before).
ARXIV_ID = re.compile(r"\A(?:\d{4}\.\d{4,5}(?:v\d+)?|[a-z-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)\Z")


def fail(code: int, message: str, *hint: str) -> None:
    print(f"paper_text: {message}", file=sys.stderr)
    for line in hint:
        print(f"            {line}", file=sys.stderr)
    raise SystemExit(code)


def extractor() -> tuple[str, str]:
    """pdftotext and its version, or a refusal naming how to get it.

    Checked before anything is downloaded: a missing extractor should cost
    nothing and say so, not surface three steps later as an empty file.
    """
    path = shutil.which("pdftotext")
    if not path:
        fail(
            2,
            "pdftotext is not installed — no text can be extracted.",
            "It comes with poppler:  apt-get install poppler-utils  |  brew install poppler",
            "Until then the paper is unread. Record it as unread; do not paraphrase an abstract.",
        )
    out = subprocess.run([path, "-v"], capture_output=True, text=True)
    version = (out.stderr or out.stdout).strip().splitlines()[0] if (out.stderr or out.stdout) else "pdftotext (version unknown)"
    return path, version


def resolve(target: str) -> tuple[str, bool]:
    """Return (source, is_url). An arXiv id becomes that paper's PDF URL."""
    if ARXIV_ID.match(target):
        return f"https://arxiv.org/pdf/{target}", True
    if target.startswith(("http://", "https://")):
        return target, True
    return target, False


def fetch(url: str, into: Path) -> None:
    """Download, or say plainly that the sandbox blocked it.

    Ulysses' execution environment has blocked direct outbound fetches before
    (REQUESTS.md, 2026-06-29: 403 on every external URL). If that is the case
    again, this must not read as "the paper does not exist".
    """
    request = urllib.request.Request(url, headers={"User-Agent": "ulysses-paper-text/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            into.write_bytes(response.read())
    except urllib.error.HTTPError as error:
        fail(
            3,
            f"{url} answered HTTP {error.code}.",
            "403 here has meant the sandbox proxy, not the publisher — the same block",
            "recorded on 2026-06-29. Fetch the PDF by another route and pass the file:",
            "    tools/paper_text.py <downloaded>.pdf",
        )
    except (urllib.error.URLError, TimeoutError) as error:
        fail(3, f"{url} is unreachable: {error}", "Pass a local PDF instead if you already have one.")


def extract(pdf: Path, binary: str) -> str:
    # -layout keeps columns apart; without it a two-column paper interleaves its
    # halves line by line and every quotation taken from it is a fabrication.
    result = subprocess.run([binary, "-layout", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True)
    if result.returncode != 0:
        fail(4, f"pdftotext could not read {pdf}: {result.stderr.strip() or 'no reason given'}")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a paper's full text, with provenance.")
    parser.add_argument("target", help="arXiv id, PDF url, or path to a local PDF")
    parser.add_argument("-o", "--out", type=Path, help="write text here instead of stdout")
    args = parser.parse_args()

    binary, version = extractor()
    source, is_url = resolve(args.target)

    with tempfile.TemporaryDirectory() as tmp:
        if is_url:
            pdf = Path(tmp) / "paper.pdf"
            fetch(source, pdf)
        else:
            pdf = Path(source)
            if not pdf.is_file():
                fail(3, f"{pdf} is not a file.")

        data = pdf.read_bytes()
        if not data.startswith(b"%PDF"):
            fail(
                4,
                f"{source} did not return a PDF.",
                "The first bytes are not %PDF. A landing page or an error body, most likely —",
                "the failure mode that once returned raw compressed stream data instead of text.",
            )
        digest = hashlib.sha256(data).hexdigest()
        text = extract(pdf, binary)

    if not text.strip():
        fail(4, f"{source} yielded no text.", "A scanned PDF without a text layer needs OCR, which this tool does not do.")

    # Provenance to stderr so it survives `-o` and never contaminates the text.
    print(
        "\n".join(
            (
                "— read —",
                f"source:    {source}",
                f"retrieved: {date.today().isoformat()}",
                f"sha256:    {digest}",
                f"extractor: {version} (-layout)",
                f"characters: {len(text)}",
                "Derivative text. Quote it with this line, and check any load-bearing",
                "quotation against the PDF itself.",
            )
        ),
        file=sys.stderr,
    )

    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"written:   {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
