#!/usr/bin/env python3
"""I4 — is the file readable by a machine, or only fetchable?

Two tests on the bytes, both fixed in `PREREGISTRATION.md` §2 before any file was fetched:

1. **structure** — does the PDF's object dictionary contain a `/Font` resource? A page that is a
   scanned image carries `/Image` XObjects and no font.
2. **text** — how many characters does a FlateDecode-only extractor recover from the content
   streams, reading literal strings between `BT` and `ET`?

`READABLE` ≡ `/Font` present **and** ≥ 200 characters recovered.

The extractor is a derivative and is named as one. It decodes `FlateDecode` and nothing else;
a stream under any other filter contributes **zero** characters. That biases the result downwards
— against the clause its author expects to hold, which is the direction an instrument should err
in. No third-party library is used, and none is installed in this runtime.
"""

import re
import zlib

STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
TEXT_BLOCK = re.compile(rb"BT(.*?)ET", re.S)
LITERAL = re.compile(rb"\((?:\\.|[^\\()])*\)", re.S)
HEXSTR = re.compile(rb"<([0-9A-Fa-f\s]+)>\s*Tj", re.S)


def _decode_literal(raw: bytes) -> str:
    body = raw[1:-1]
    body = re.sub(rb"\\([nrtbf()\\])", lambda m: {
        b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b",
        b"f": b"\f", b"(": b"(", b")": b")", b"\\": b"\\"}[m.group(1)], body)
    body = re.sub(rb"\\([0-7]{1,3})", lambda m: bytes([int(m.group(1), 8) & 0xFF]), body)
    return body.decode("latin-1", "replace")


def extract_text(data: bytes) -> str:
    chunks: list[str] = []
    for raw in STREAM.findall(data):
        try:
            content = zlib.decompress(raw)
        except zlib.error:
            continue                        # not Flate, or damaged — counts as zero characters
        for block in TEXT_BLOCK.findall(content):
            for lit in LITERAL.findall(block):
                chunks.append(_decode_literal(lit))
            for hx in HEXSTR.findall(block):
                digits = re.sub(rb"\s", b"", hx)
                if len(digits) % 2 == 0:
                    chunks.append(bytes.fromhex(digits.decode()).decode("latin-1", "replace"))
    return "".join(chunks)


def classify(data: bytes) -> dict:
    text = extract_text(data)
    printable = "".join(ch for ch in text if ch.isprintable() or ch in " \n\t")
    has_font = b"/Font" in data
    return {
        "has_font": has_font,
        "has_image": b"/Image" in data,
        "chars": len(printable.strip()),
        "readable": bool(has_font and len(printable.strip()) >= 200),
        "sample": printable.strip()[:300],
    }
