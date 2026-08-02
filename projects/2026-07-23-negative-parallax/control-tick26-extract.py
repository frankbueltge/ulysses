#!/usr/bin/env python3
"""Mechanical parameter extraction for the tick-26 control.

Implements PREREGISTRATION-tick26.md §3 exactly: the qualification of a numeric value
as a "parameter the document sets and could have set otherwise" is made by this script,
before any warrant is read, so that the choice of what counts is not made with the
answer in view. The script is frozen before the first item of the population is opened
and is debugged against RFC 2119 only (§2, debugging exclusion).

Usage:
    python3 control-tick26-extract.py 10004 10003 ...     # emits JSON to stdout

Output per document: every qualifying parameter with its section, paragraph and the
sentence it stands in. Warrants are NOT looked at here; that is the reader's pass.
"""

import json
import re
import sys
import urllib.request

TXT = "https://www.rfc-editor.org/rfc/rfc{}.txt"

# --- §3.4 normativity gate -------------------------------------------------
NORMATIVE = re.compile(
    r"\b(MUST|SHOULD|RECOMMENDED|REQUIRED|SHALL|default|at least|at most|"
    r"no more than|no less than|maximum|minimum|limit|limits|timeout|retry|retries|"
    r"interval|rate|threshold)\b",
    re.IGNORECASE,
)

# --- §3.5 attribution gate -------------------------------------------------
REPORTING_VERB = re.compile(
    r"\b(specif(?:y|ies|ied)|defin(?:e|es|ed)|recommend(?:s|ed)?|"
    r"requir(?:e|es|ed)|describ(?:e|es|ed))\b",
    re.IGNORECASE,
)
BRACKET_REF = re.compile(r"\[[A-Za-z][A-Za-z0-9._-]*\]")
SECTION_OF = re.compile(r"\bSection\s+\d[\d.]*\s+of\b", re.IGNORECASE)

# --- §3.2 numeric tokens ---------------------------------------------------
NUMBER_WORDS = ("two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve")
# The trailing lookahead is (?!\.?\w) and not (?![\w.]): the latter keeps "3.1.1" out of
# the token stream but also drops every number that ends a sentence ("the limit is 100."),
# which is not a neutral loss. Fixed on the synthetic fixture before any item was opened.
TOKEN = re.compile(
    r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*%?(?:/\d+)?(?!\.?\w)"
    r"|\b(?:" + "|".join(NUMBER_WORDS) + r")\b",
    re.IGNORECASE,
)

# --- §3.3 exclusions -------------------------------------------------------
PRECEDED_BY = re.compile(
    r"\b(RFC|RFCs|Section|Sections|Appendix|Appendices|Figure|Table|STD|BCP|"
    r"version|Version|IPv|TLS|DTLS|SHA|MD|Errata|errata|draft)\s*$"
)
MONTHS = ("january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december")
BIT_WIDTH = re.compile(r"^\s*-?\s*(bit|bits)\b", re.IGNORECASE)
LIST_MARKER = re.compile(r"^\s*\(?\d+[.)]\s")
IANA_SECTION = re.compile(r"IANA Considerations", re.IGNORECASE)
SENTINEL = {"0", "1", "zero", "one"}

SECTION_HEAD = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")


def fetch(num):
    req = urllib.request.Request(TXT.format(num), headers={"User-Agent": "ulysses-control/1"})
    with urllib.request.urlopen(req, timeout=60) as fh:
        return fh.read().decode("utf-8", errors="replace")


def strip_furniture(text):
    """Remove form feeds and the running headers/footers of the plain-text series."""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if "\f" in line:
            continue
        s = line.strip()
        # footer: "Mandel & Turner            Standards Track            [Page 3]"
        if s.endswith("]") and re.search(r"\[Page\s+\d+\]$", s):
            continue
        # header: "RFC 10004        CMC Compliance Requirements        July 2026"
        if re.match(r"^RFC\s+\d+\s{2,}\S", s) and re.search(
                r"(" + "|".join(MONTHS) + r")\s+\d{4}$", s, re.IGNORECASE):
            continue
        out.append(line)
    return "\n".join(out)


def paragraphs(text):
    """Yield (section_number, section_title, paragraph_text)."""
    sec_no, sec_title = "", "(front matter)"
    buf = []
    for line in text.split("\n"):
        if not line.strip():
            if buf:
                yield sec_no, sec_title, " ".join(x.strip() for x in buf)
                buf = []
            continue
        # an unindented line that looks like a numbered heading
        if not line.startswith(" "):
            m = SECTION_HEAD.match(line.strip())
            if m and len(line.strip()) < 90:
                if buf:
                    yield sec_no, sec_title, " ".join(x.strip() for x in buf)
                    buf = []
                sec_no, sec_title = m.group(1), m.group(2).strip()
                continue
        buf.append(line)
    if buf:
        yield sec_no, sec_title, " ".join(x.strip() for x in buf)


def sentences(par):
    parts = re.split(r"(?<=[.;:])\s+(?=[A-Z(\[]|\d)", par)
    return [p for p in parts if p.strip()]


def sentence_of(par, start):
    pos = 0
    for s in sentences(par):
        idx = par.find(s, pos)
        if idx <= start < idx + len(s):
            return s
        pos = idx + len(s)
    return par


def excluded(par, m):
    tok = m.group(0).strip()
    low = tok.lower().rstrip("%")
    before = par[max(0, m.start() - 24):m.start()]
    after = par[m.end():m.end() + 12]

    if low in SENTINEL:                                    # §3.3 sentinels/cardinalities
        return "sentinel-or-cardinality"
    if before.rstrip().endswith("[") or after.lstrip().startswith("]"):
        return "inside-bracketed-reference"
    if PRECEDED_BY.search(before):
        return "reference-version-or-algorithm-size"
    if BIT_WIDTH.match(after):
        return "bit-width"
    if re.fullmatch(r"(19|20)\d\d", low):
        return "year"
    if re.search(r"(" + "|".join(MONTHS) + r")\s*$", before, re.IGNORECASE):
        return "date"
    if LIST_MARKER.match(par[max(0, m.start() - 4):m.end() + 3]) and m.start() < 6:
        return "list-numbering"
    return None


def extract(num):
    raw = fetch(num)
    text = strip_furniture(raw)
    hits, dropped = [], []
    truncated = False
    for sec_no, sec_title, par in paragraphs(text):
        if IANA_SECTION.search(sec_title):
            continue
        if not NORMATIVE.search(par):
            continue
        for m in TOKEN.finditer(par):
            why = excluded(par, m)
            if why:
                continue
            sent = sentence_of(par, m.start())
            if (BRACKET_REF.search(sent) or SECTION_OF.search(sent)) and REPORTING_VERB.search(sent):
                dropped.append({"section": sec_no or "-", "title": sec_title,
                                "token": m.group(0).strip(), "sentence": sent,
                                "reason": "attribution-gate (§3.5)"})
                continue
            hits.append({"section": sec_no or "-", "title": sec_title,
                         "token": m.group(0).strip(), "sentence": sent,
                         "paragraph": par})
    if len(hits) > 20:                                      # §3.6 declared cap
        truncated = len(hits)
        hits = hits[:20]
    return {"rfc": num, "parameters": hits, "dropped_by_attribution_gate": dropped,
            "truncated_from": truncated}


if __name__ == "__main__":
    print(json.dumps([extract(int(n)) for n in sys.argv[1:]], indent=1))
