#!/usr/bin/env python3
"""Dial invariance — which sentences about a catalogue survive their own rule.

A companion to `columns.py`. That instrument asks what a column holds using checks
with no free parameter. This one asks the question that opens the moment a check
*does* have a free parameter: **of the sentences you could publish off a dialled
rule, which ones are properties of the file and which are properties of the dial?**

The unit is a **statement**, and there are two kinds:

* a **level** — "more than half of group G satisfies P";
* a **comparison** — "group A satisfies P more often than group B".

Both are binary, so neither needs a tolerance to be called stable. A statement
**survives** its family of settings when its truth value is identical at every
setting in the grid. Nothing here is thresholded except by strict equality.

The instrument needs no model, no network beyond the caller's fetch and no external
lexicon: every predicate builds its vocabulary from the field it is applied to.

    from dials import analyse
    result = analyse(entries, feed_name="atlas")

Author: the Atelier. Licence: Apache-2.0 with the repository.
"""

from __future__ import annotations

import itertools
import re
from collections import Counter

# --------------------------------------------------------------------------------- #
# Text handling — deliberately small and stated, so a reader can re-derive it
# --------------------------------------------------------------------------------- #

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "for", "from", "had",
    "has", "have", "he", "her", "his", "in", "is", "it", "its", "of", "on", "or",
    "she", "that", "the", "their", "them", "there", "these", "they", "this", "to",
    "was", "were", "which", "who", "will", "with",
}

ACT_SUFFIXES = ("s", "es", "ed", "ing")

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


def words(text: str) -> list[str]:
    """The word tokens of a text, in order, case preserved."""
    return _WORD.findall(text or "")


def content_words(text: str) -> list[str]:
    return [w for w in (t.lower() for t in words(text)) if w not in STOPWORDS]


def as_text(value) -> str:
    """Flatten a cell to text. Lists join; anything else stringifies."""
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(as_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(as_text(v) for v in value.values())
    return str(value)


# --------------------------------------------------------------------------------- #
# The predicate families — each one carries its dial and builds its own vocabulary
# --------------------------------------------------------------------------------- #


def _act_lexicon(texts: list[str], inflections: int) -> set[str]:
    """Stems appearing in THIS field with at least `inflections` of -s/-es/-ed/-ing.

    The rule of `columns.py` check C, and the same one the house has been arguing
    about since 2026-09-04. It borrows no word list: a field's own morphology says
    which of its stems are used as acts.
    """
    tokens = Counter()
    for t in texts:
        for w in words(t):
            tokens[w.lower()] += 1
    stems: dict[str, set[str]] = {}
    for t in tokens:
        for suf in ACT_SUFFIXES:
            if t.endswith(suf) and len(t) - len(suf) >= 3:
                stems.setdefault(t[: -len(suf)], set()).add(suf)
    lex: set[str] = set()
    for stem, sufs in stems.items():
        if len(sufs) >= inflections:
            lex.add(stem)
            for suf in sufs:
                lex.add(stem + suf)
    return lex


def family_act(texts: list[str]) -> tuple[list[str], list[list[bool]]]:
    """"Written as an act" — is one of the first w words used as a verb here?

    Dial: w (opening window, 1..5) x k (inflections required, 1..3). Twelve settings.
    """
    lexicons = {k: _act_lexicon(texts, k) for k in (1, 2, 3)}
    toks = [[w.lower() for w in words(t)] for t in texts]
    names, rows = [], []
    for w in (1, 2, 3, 5):
        for k in (1, 2, 3):
            lex = lexicons[k]
            names.append(f"w={w},k={k}")
            rows.append([any(x in lex for x in tk[:w]) for tk in toks])
    return names, rows


def family_length(texts: list[str]) -> tuple[list[str], list[list[bool]]]:
    """"Long" — at least t content words. Dial: t. Six settings."""
    n = [len(content_words(t)) for t in texts]
    names, rows = [], []
    for t in (3, 5, 8, 12, 20, 30):
        names.append(f"t={t}")
        rows.append([c >= t for c in n])
    return names, rows


def family_rare(texts: list[str]) -> tuple[list[str], list[list[bool]]]:
    """"Specific" — contains a token this field uses in at most q entries.

    Dial: q (document frequency ceiling). Five settings. The vocabulary is the
    field's own; no corpus is borrowed.
    """
    docs = [set(w.lower() for w in words(t)) for t in texts]
    df = Counter()
    for d in docs:
        df.update(d)
    names, rows = [], []
    for q in (1, 2, 3, 5, 10):
        names.append(f"q={q}")
        rows.append([any(df[w] <= q for w in d) for d in docs])
    return names, rows


def family_named(texts: list[str]) -> tuple[list[str], list[list[bool]]]:
    """"Names something" — at least m capitalised tokens after the first word.

    Dial: m. Four settings.
    """
    caps = []
    for t in texts:
        ws = words(t)
        caps.append(sum(1 for w in ws[1:] if w[:1].isupper()))
    names, rows = [], []
    for m in (1, 2, 3, 4):
        names.append(f"m={m}")
        rows.append([c >= m for c in caps])
    return names, rows


FAMILIES = {
    "act": ("written as an act", family_act),
    "length": ("long", family_length),
    "rare": ("specific", family_rare),
    "named": ("names something", family_named),
}

LEVEL_CUTS = (0.25, 0.5, 0.75)


# --------------------------------------------------------------------------------- #
# Groupings — derived mechanically, so nobody chooses the flattering split
# --------------------------------------------------------------------------------- #

MAX_GROUP_VALUES = 12


def scalar(value) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def groupings(entries: list[dict], exclude: set[str], year_fields=("year", "jahr")) -> dict:
    """Every scalar column with at most MAX_GROUP_VALUES distinct values, plus a
    decade band derived from the feed's year column. No column is picked by hand."""
    out: dict[str, list[str]] = {}
    keys: set[str] = set()
    for r in entries:
        keys.update(r.keys())
    for k in sorted(keys):
        if k in exclude:
            continue
        vals = [r.get(k) for r in entries]
        if not all(scalar(v) for v in vals):
            continue
        norm = ["" if v is None or v == "" else str(v) for v in vals]
        distinct = {v for v in norm if v}
        if 2 <= len(distinct) <= MAX_GROUP_VALUES:
            out[k] = norm
    for yf in year_fields:
        if yf in keys:
            band = []
            for r in entries:
                m = re.search(r"(1[89]\d\d|20\d\d)", str(r.get(yf) or ""))
                band.append(f"{int(m.group(1)) // 10 * 10}s" if m else "")
            if len({b for b in band if b}) >= 2:
                out[f"{yf}:decade"] = band
            break
    return out


# --------------------------------------------------------------------------------- #
# The analysis
# --------------------------------------------------------------------------------- #


def _rates(rows: list[list[bool]], idx: list[int]) -> list[float]:
    n = len(idx)
    return [sum(1 for i in idx if row[i]) / n for row in rows]


def analyse(
    entries: list[dict],
    feed: str,
    text_fields: list[str],
    min_group: int = 20,
    families: dict | None = None,
) -> dict:
    """Every statement this feed supports, with its verdict at every setting."""
    families = families or FAMILIES
    groups = groupings(entries, exclude=set(text_fields))
    statements: list[dict] = []
    field_report: list[dict] = []

    for field in text_fields:
        texts = [as_text(r.get(field)) for r in entries]
        if not any(texts):
            continue
        for fam_key, (fam_label, fam_fn) in families.items():
            names, rows = fam_fn(texts)
            whole = _rates(rows, list(range(len(entries))))
            # A dial that moves nothing, or a predicate that is always true or always
            # false, makes "it survived" meaningless. Both tests are strict.
            live = len(set(whole)) > 1 and min(whole) > 0.0 and max(whole) < 1.0
            field_report.append(
                {
                    "feed": feed,
                    "field": field,
                    "family": fam_key,
                    "family_label": fam_label,
                    "settings": names,
                    "whole_rates": whole,
                    "live": live,
                }
            )
            if not live:
                continue

            # the whole catalogue, as a group of its own
            buckets: list[tuple[str, str, list[int]]] = [
                ("(whole feed)", "all entries", list(range(len(entries))))
            ]
            for gname, col in groups.items():
                by: dict[str, list[int]] = {}
                for i, v in enumerate(col):
                    if v:
                        by.setdefault(v, []).append(i)
                for gv, idx in sorted(by.items()):
                    if len(idx) >= min_group:
                        buckets.append((gname, gv, idx))

            cache: dict[tuple[str, str], list[float]] = {}
            for gname, gv, idx in buckets:
                cache[(gname, gv)] = _rates(rows, idx)
                sizes = len(idx)
                for cut in LEVEL_CUTS:
                    verdicts = [r > cut for r in cache[(gname, gv)]]
                    med = sorted(cache[(gname, gv)])[len(verdicts) // 2]
                    statements.append(
                        {
                            "kind": "level",
                            "feed": feed,
                            "field": field,
                            "family": fam_key,
                            "grouping": gname,
                            "group_a": gv,
                            "group_b": None,
                            "n_a": sizes,
                            "n_b": None,
                            "cut": cut,
                            "verdicts": [int(v) for v in verdicts],
                            "survives": len(set(verdicts)) == 1,
                            "margin": min(abs(r - cut) for r in cache[(gname, gv)]),
                            "median_margin": abs(med - cut),
                        }
                    )

            for gname in {b[0] for b in buckets if b[0] != "(whole feed)"}:
                members = [b for b in buckets if b[0] == gname]
                for (_, ga, ia), (_, gb, ib) in itertools.combinations(members, 2):
                    ra, rb = cache[(gname, ga)], cache[(gname, gb)]
                    diffs = [x - y for x, y in zip(ra, rb)]
                    verdicts = [1 if d > 0 else (-1 if d < 0 else 0) for d in diffs]
                    statements.append(
                        {
                            "kind": "comparison",
                            "feed": feed,
                            "field": field,
                            "family": fam_key,
                            "grouping": gname,
                            "group_a": ga,
                            "group_b": gb,
                            "n_a": len(ia),
                            "n_b": len(ib),
                            "cut": None,
                            "verdicts": verdicts,
                            "survives": len(set(verdicts)) == 1,
                            "margin": min(abs(d) for d in diffs),
                            "median_margin": abs(sorted(diffs)[len(diffs) // 2]),
                        }
                    )

    return {"feed": feed, "statements": statements, "fields": field_report,
            "groupings": sorted(groups)}


def standardise(statements: list[dict], bin_width: float = 0.02, key: str = "median_margin") -> dict:
    """Survival of levels and comparisons at matched margin.

    A statement whose margin is large survives for a reason that has nothing to do
    with its grammar: there is simply nothing near enough to flip. So the raw
    survival rates of the two kinds are not comparable until the margin is held
    fixed. This bins both kinds on the same margin scale and reweights the levels
    to the comparisons' margin distribution (direct standardisation).
    """
    def b(x: float) -> int:
        return int(x / bin_width)

    lev = [s for s in statements if s["kind"] == "level"]
    cmp_ = [s for s in statements if s["kind"] == "comparison"]
    bins: dict[int, dict] = {}
    for s in lev + cmp_:
        d = bins.setdefault(b(s[key]), {"level": [0, 0], "comparison": [0, 0]})
        d[s["kind"]][0] += int(s["survives"])
        d[s["kind"]][1] += 1
    num = den = 0.0
    covered = 0
    for i, d in bins.items():
        w = d["comparison"][1]
        if w and d["level"][1]:
            num += w * d["level"][0] / d["level"][1]
            den += w
            covered += w
    return {
        "bin_width": bin_width,
        "key": key,
        "raw_level": sum(s["survives"] for s in lev) / len(lev) if lev else None,
        "raw_comparison": sum(s["survives"] for s in cmp_) / len(cmp_) if cmp_ else None,
        "n_level": len(lev),
        "n_comparison": len(cmp_),
        "expected_level_at_comparison_margins": num / den if den else None,
        "comparison_survival_in_matched_bins": (
            sum(s["survives"] for s in cmp_ if bins[b(s[key])]["level"][1]) / covered
            if covered else None
        ),
        "matched_comparisons": covered,
        "bins": {
            str(i): {
                "lo": round(i * bin_width, 6),
                "level": d["level"],
                "comparison": d["comparison"],
            }
            for i, d in sorted(bins.items())
        },
    }
