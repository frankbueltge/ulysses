#!/usr/bin/env python3
"""columns.py — does a catalogue column hold what its name says?

A field name is a claim about every row. `verify_status` claims each entry has been
checked or not; `aufnahmegrund` claims each entry has its own reason for being in the
register; `year` claims a year. Reading a catalogue never tests such a claim, because
reading is per-row and every row looks fine. Testing it is a whole-column act, and it
is cheap.

This instrument runs four checks over every field of a catalogue. Each is one rule,
each is re-derivable from the committed record, and none of them needs a model:

  A. FILL         — is there anything in the column at all?
  B. VARIATION    — does it vary? A column with one value cannot be about an entry;
                    whatever it says, it is a fact about the catalogue's boundary.
  C. KIND         — where the *name* claims a kind (a year, an address, a boolean, an
                    HTTP status, an act), do the values have it? Names that claim no
                    kind get no kind check, and that is reported rather than hidden.
  D. REDUNDANCY   — is the column a function of another column? Then it is perfectly
                    filled, perfectly typed and adds nothing. This is the failure a
                    reader cannot see at all: it requires holding two columns across
                    every row at once.

And one summary number, chosen because a visitor can read it without a definition:

  RESIDUAL — pick an entry at random and read this field. How many entries share that
             value? Averaged over the catalogue. A key gives 1; a constant column
             gives n; everything real is in between. Its analytic floor for a column
             with k distinct values is n/k (even spread), so the ratio residual/(n/k)
             separates "few values" from "badly balanced values".

  The floor is *analytic*, and that is on purpose. This practice found in cycle 001
  that where a threshold is analytic, automation adds nothing and will supply a
  confident wrong answer if asked to simulate one; where it must be measured against
  re-runs of the same material, automation is the only thing that can supply it. This
  measure is the first kind. No surrogates are manufactured here, and none are needed.

Usage:
    python3 tools/census/columns.py URL_OR_PATH [URL_OR_PATH ...] --out data.json

Feeds are read live and pinned by sha256. Nothing is mirrored into this repository:
what is committed is the derived record, never the source catalogue.

Author: the Atelier. Licence: Apache-2.0 with the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
import sys
import urllib.request
from collections import Counter
from typing import Any

# --------------------------------------------------------------------------------- #
# Check C — the name → kind table.
#
# Every rule is a substring of the field name and a predicate on the value. The table
# is deliberately short: only kinds a name states plainly enough that a disagreement
# is a defect rather than an interpretation. A field whose name claims no kind is
# reported as `no claim`, which is itself a finding — most names claim none, so the
# structural checks A, B and D are the only ones available for most of a catalogue.
# --------------------------------------------------------------------------------- #

YEAR_RE = re.compile(r"^-?\d{1,4}$")
URL_RE = re.compile(r"^https?://\S+$", re.I)

# Check C, the act rule, reused verbatim from cycle 002 session 2 (Propp): a field
# named for a move should open with an act. The lexicon is derived from the corpus's
# own inflectional evidence, not written by hand — see `_act_lexicon`.
ACT_SUFFIXES = ("s", "es", "ed", "ing")


def _is_year(v: str) -> bool:
    if not YEAR_RE.match(v):
        return False
    n = int(v)
    return 1400 <= n <= 2100


def _is_url(v: str) -> bool:
    return bool(URL_RE.match(v))


def _is_bool(v: str) -> bool:
    return v in ("True", "False", "true", "false")


def _is_http_status(v: str) -> bool:
    return bool(re.fullmatch(r"\d{3}", v)) and 100 <= int(v) <= 599


KIND_RULES: list[tuple[str, str, str, Any]] = [
    # (name substring, kind label, one-line rule as a reader checks it, predicate)
    ("pruef_status", "an HTTP status", "three digits, 100–599", _is_http_status),
    ("year", "a year", "digits only, 1400–2100", _is_year),
    ("jahr", "a year", "digits only, 1400–2100", _is_year),
    ("url", "an address", "starts http:// or https://", _is_url),
    ("adressen", "an address", "starts http:// or https://", _is_url),
    ("zugriff", "an address", "starts http:// or https://", _is_url),
    ("geprueft", "a boolean", "true or false", _is_bool),
    ("frei_zugaenglich", "a boolean", "true or false", _is_bool),
    ("gesperrt", "a boolean", "true or false", _is_bool),
    ("renderable", "a boolean", "true or false", _is_bool),
    ("nur_vorlage", "a boolean", "true or false", _is_bool),
    ("move", "an act", "first word inflects as a verb in this corpus", None),
]


def _act_lexicon(values: list[str]) -> set[str]:
    """The act vocabulary, derived from the corpus's own inflectional evidence.

    A token counts as an act word when the corpus itself shows it inflecting: the
    stem appears with at least two of the endings -s/-es/-ed/-ing somewhere in the
    column. No hand-written verb list, so the rule can be re-derived by anyone with
    the same column and no outside resource.
    """
    tokens: Counter[str] = Counter()
    for v in values:
        for t in re.findall(r"[a-z]+", v.lower()):
            tokens[t] += 1
    stems: dict[str, set[str]] = {}
    for t in tokens:
        for suf in ACT_SUFFIXES:
            if t.endswith(suf) and len(t) - len(suf) >= 3:
                stems.setdefault(t[: -len(suf)], set()).add(suf)
    lexicon: set[str] = set()
    for stem, sufs in stems.items():
        if len(sufs) >= 2:
            for suf in sufs:
                lexicon.add(stem + suf)
            lexicon.add(stem)
    return lexicon


def _first_word(v: str) -> str:
    m = re.match(r"[A-Za-z]+", v.strip())
    return m.group(0).lower() if m else ""


# --------------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------------- #


def cell_parts(v: Any) -> list[str]:
    """The values a kind check should look at inside one cell.

    A list-valued cell holds several values of the claimed kind, not one string that
    happens to look like JSON. `adressen` holds addresses; checking the rendered list
    against an address rule fails all 82 rows and reports an instrument artefact as a
    catalogue defect. Found the same way everything here is found — by reading the
    column the instrument had just condemned.
    """
    if isinstance(v, list):
        return [norm(x) for x in v if norm(x)]
    s = norm(v)
    return [s] if s else []


def norm(v: Any) -> str:
    """One string per cell, so every check reads the same thing.

    A missing key, None, an empty string, an empty list and an empty object are all
    the same fact — the catalogue does not say — and are normalised to "". Lists and
    objects are rendered as canonical JSON so that two rows agree exactly when they
    hold the same value.
    """
    if v is None:
        return ""
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, (list, dict)):
        return json.dumps(v, sort_keys=True, ensure_ascii=False) if v else ""
    return str(v).strip()


# --------------------------------------------------------------------------------- #
# The four checks over one catalogue
# --------------------------------------------------------------------------------- #


def census(entries: list[dict], name: str) -> dict:
    n = len(entries)
    fields: list[str] = []
    for row in entries:
        for k in row:
            if k not in fields:
                fields.append(k)

    cols: dict[str, list[str]] = {f: [norm(r.get(f)) for r in entries] for f in fields}
    # the same cells, opened up, so a kind check reads the values and not their
    # rendering — a list cell holds several values of the claimed kind
    parts: dict[str, list[list[str]]] = {
        f: [cell_parts(r.get(f)) for r in entries] for f in fields
    }
    counts: dict[str, Counter[str]] = {f: Counter(cols[f]) for f in fields}

    out_fields = []
    for f in fields:
        col = cols[f]
        c = counts[f]
        filled = [x for x in col if x]
        cf = Counter(filled)
        distinct = len(cf)
        modal_value, modal_count = cf.most_common(1)[0] if cf else ("", 0)

        # RESIDUAL — expected number of entries sharing a random entry's value,
        # counting the empty cell as a value of its own (not saying is a state).
        residual = sum(k * k for k in c.values()) / n
        # analytic floor: the same number of distinct values, evenly spread
        k_all = len(c)
        floor = n / k_all
        concentration = residual / floor if floor else float("nan")

        # normalised entropy, for readers who want the conventional number
        ent = -sum((v / n) * math.log2(v / n) for v in c.values())
        ent_norm = ent / math.log2(n) if n > 1 else 0.0

        # ---- Check C: kind
        # A cell conforms when every value inside it conforms; an empty cell is not
        # checked (that is check A's business, not this one).
        cells = [p for p in parts[f] if p]
        kind = None
        for sub, label, rule, pred in KIND_RULES:
            if sub in f:
                if pred is None:  # the act rule
                    lex = _act_lexicon([v for p in cells for v in p])
                    test = lambda p: all(_first_word(v) in lex for v in p)  # noqa: E731
                else:
                    test = lambda p: all(pred(v) for v in p)  # noqa: E731
                ok = sum(1 for p in cells if test(p))
                examples = [" | ".join(p) for p in cells if not test(p)][:3]
                kind = {
                    "claim": label,
                    "rule": rule,
                    "checked": len(cells),
                    "conforming": ok,
                    "failing": len(cells) - ok,
                    "failing_examples": [e[:120] for e in examples],
                }
                break

        out_fields.append(
            {
                "field": f,
                "n": n,
                "filled": len(filled),
                "empty": n - len(filled),
                "distinct": distinct,
                "modal_value": modal_value[:160],
                "modal_count": modal_count,
                "modal_share": modal_count / len(filled) if filled else 0.0,
                "residual": residual,
                "residual_floor": floor,
                "concentration": concentration,
                "entropy_norm": ent_norm,
                "constant": distinct == 1 and len(filled) == n,
                "kind": kind,
                "determined_by": [],  # filled in below
            }
        )

    # ---- Check D: redundancy (functional dependency X -> Y)
    #
    # Y is redundant when some other column X fixes it: every distinct value of X
    # occurs with exactly one value of Y.
    #
    # Two exclusions, and the first one cost a draft. A column that singles out
    # entries determines every other column trivially — `decisive_move` has 519
    # distinct values over 521 rows, so the first run of this check reported that it
    # "determines" the artist, the year, the venue and nine more, which is true and
    # worthless. The rule is therefore not "not a key" but **not near-key**: a
    # determinant must leave at least two entries standing on average
    # (residual >= 2), so it is genuinely coarser than the catalogue. A constant
    # column is excluded from the other side: it explains nothing by determining
    # nothing.
    #
    # An empty cell counts as a value here, deliberately — "the catalogue does not
    # say" is a state a column can be in, and a remark that appears exactly where a
    # status is not 200 is determined by that status whether or not the other rows
    # are blank.
    by_name = {d["field"]: d for d in out_fields}
    for y in fields:
        ydat = by_name[y]
        if ydat["constant"] or ydat["distinct"] <= 1:
            continue
        dets = []
        for x in fields:
            if x == y:
                continue
            xdat = by_name[x]
            if xdat["residual"] < 2:  # a key, or near enough, explains everything
                continue
            if xdat["distinct"] <= 1:  # a constant explains nothing
                continue
            mapping: dict[str, str] = {}
            ok = True
            for xv, yv in zip(cols[x], cols[y]):
                if xv in mapping:
                    if mapping[xv] != yv:
                        ok = False
                        break
                else:
                    mapping[xv] = yv
            if ok:
                dets.append(
                    {
                        "field": x,
                        "distinct": xdat["distinct"],
                        "mutual": bool(xdat["distinct"] == ydat["distinct"]),
                    }
                )
        dets.sort(key=lambda d: (not d["mutual"], d["distinct"]))
        ydat["determined_by"] = dets

    return {
        "catalogue": name,
        "entries": n,
        "field_count": len(fields),
        "fields": out_fields,
    }


# --------------------------------------------------------------------------------- #
# Reading a feed: live, pinned, never mirrored
# --------------------------------------------------------------------------------- #


def read_source(src: str) -> tuple[bytes, str]:
    if src.startswith("http://") or src.startswith("https://"):
        req = urllib.request.Request(
            src,
            headers={
                # An honestly identified research instrument — the doorkeeper finding
                # of cycle 001 session 4 is why this header says what it says.
                "User-Agent": "atelier-column-census/1.0 (artistic research; frankbueltge.de)"
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
    else:
        raw = pathlib.Path(src).read_bytes()
    return raw, hashlib.sha256(raw).hexdigest()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sources", nargs="+", help="feed URL or local path")
    ap.add_argument("--name", action="append", default=[], help="short name per source")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    catalogues = []
    for i, src in enumerate(args.sources):
        try:
            raw, sha = read_source(src)
        except Exception as exc:  # an unreachable feed is a fact about the session
            catalogues.append({"catalogue": src, "unreachable": str(exc)})
            print(f"UNREACHABLE {src}: {exc}", file=sys.stderr)
            continue
        doc = json.loads(raw.decode("utf-8"))
        entries = doc["entries"] if isinstance(doc, dict) and "entries" in doc else doc
        name = args.name[i] if i < len(args.name) else src.rsplit("/", 2)[-1]
        c = census(entries, name)
        c["source"] = src
        c["sha256"] = sha
        c["bytes"] = len(raw)
        catalogues.append(c)

    pathlib.Path(args.out).write_text(
        json.dumps({"catalogues": catalogues}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
