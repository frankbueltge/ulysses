#!/usr/bin/env python3
"""Parse every fetched corrigendum into its `for: … read: …` pairs, and select the ones
that change a document number.

The Journal's corrigenda use one formula: a locus ("On page 124, Articles 1 and 2:"),
then `for: '<wrong>', read: '<right>'`. This script does three things and no more:

1. strip the XHTML to text and extract every (locus, for, read) triple;
2. extract, from each side, the set of *document-number tokens* — the Journal's own forms
   for naming another act: `(EU) 2020/1956`, `(EU) No 1025/2012`, `(EC) No 765/2008`,
   `2014/23/EU`, `(EU, Euratom) 2018/1046`;
3. mark a pair a REFERENCE CORRECTION when those two sets differ.

Step 3 is the study's selection step and it is **blind to every outcome measured
downstream**: it sees only the two strings the Journal printed side by side, never whether
the wrong number resolves and never whether the act's own text still carries it.

Output: pairs.json. Nothing is fetched here.
"""

import html
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
CORPUS = HERE / "corpus"

# The Journal's ways of naming an act by number. Each yields (year, number).
NUM_PATTERNS = [
    # (EU) 2020/1956 · (EU, Euratom) 2018/1046 · (CFSP) 2019/797
    (re.compile(r"\((?:EU|EC|EEC|Euratom|CFSP|CE)(?:,\s*(?:EU|Euratom|EC))?\)\s*(\d{4})/(\d{1,4})\b"),
     "year_first"),
    # (EU) No 1025/2012 · (EC) No 765/2008 · (EEC) No 2913/92
    (re.compile(r"\((?:EU|EC|EEC|Euratom|CFSP|CE)(?:,\s*(?:EU|Euratom|EC))?\)\s*No\s*(\d{1,4})/(\d{2,4})\b"),
     "number_first"),
    # 2014/23/EU · 2019/1024/EU · 96/71/EC
    (re.compile(r"\b(\d{2,4})/(\d{1,4})/(?:EU|EC|EEC|Euratom|CFSP)\b"), "year_first"),
]

MARKER = re.compile(r"\b(for|read):\s*", re.IGNORECASE)
OPEN, CLOSE = "‘“\"'", "’”\"'"

# The instrument this replaced matched `for: ‘…’` with a lazy quote pair. Tested against
# the corpus before execution (journal 2026-08-25): 30 of 510 captures carry a typographic
# quote *inside* the quoted legal text — `‘T2L’` in 32016R0341R(05) is one — and a lazy
# pair closes on the first inner quote, truncating the very text being compared. Two
# captures swallowed a following marker outright. So the span is bounded by the Journal's
# own `for:`/`read:` markers, and the value inside it runs from the FIRST opening quote to
# the LAST closing one, which is what nesting requires.


def spans(text: str) -> list[tuple[str, str, int]]:
    """(kind, raw value, start offset) for every for:/read: marker, in document order."""
    marks = list(MARKER.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(1).lower(), text[m.end():end], m.start()))
    return out


def unquote(raw: str) -> str:
    """The quoted value inside a marker span: first opener to last closer."""
    raw = raw.strip()
    start = next((i for i, c in enumerate(raw) if c in OPEN), None)
    if start is None:
        return raw.rstrip(" ,.;").strip()
    stop = next((i for i in range(len(raw) - 1, start, -1) if raw[i] in CLOSE), None)
    if stop is None:
        return raw[start + 1:].rstrip(" ,.;").strip()
    return raw[start + 1:stop].strip()


def triples(text: str) -> list[dict]:
    """Every `for: … read: …` pair, with the sentence that located it."""
    out = []
    sp = spans(text)
    for i, (kind, raw, at) in enumerate(sp):
        if kind != "for" or i + 1 >= len(sp) or sp[i + 1][0] != "read":
            continue
        head = text[:at]
        locus = re.split(r"(?<=[.;])\s+", head)[-1] if head else ""
        out.append(
            {
                "locus": " ".join(locus.split())[-160:],
                "for": unquote(raw),
                "read": unquote(sp[i + 1][1]),
            }
        )
    return out


def norm_year(y: str) -> str:
    """Two-digit Journal years belong to the 20th century (Reg. (EEC) No 2913/92)."""
    if len(y) == 2:
        return "19" + y
    return y


def tokens(s: str) -> set[tuple[str, str]]:
    """Every (year, number) an act is named by in this string."""
    out = set()
    for pat, order in NUM_PATTERNS:
        for m in pat.finditer(s):
            a, b = m.group(1), m.group(2)
            year, number = (a, b) if order == "year_first" else (b, a)
            out.add((norm_year(year), str(int(number))))
    return out


def to_text(raw: str) -> str:
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    records, no_pair = [], []
    for it in manifest["corrigenda"]:
        path = CORPUS / (it["celex"].replace("/", "_") + ".html")
        if not path.exists():
            continue
        text = to_text(path.read_text(encoding="utf-8", errors="replace"))
        pairs = []
        for t in triples(text):
            f, r = t["for"], t["read"]
            tf, tr = tokens(f), tokens(r)
            wrong = sorted(tf - tr)          # named by the wrong text, not by the right one
            pairs.append(
                {
                    "locus": t["locus"],
                    "for": f[:400],
                    "read": r[:400],
                    "for_len": len(f),
                    "read_len": len(r),
                    "for_tokens": sorted(tf),
                    "read_tokens": sorted(tr),
                    # a *dropped* number, not merely a differing token set: a `read:` that
                    # only ADDS a reference corrects no pointer a reader could follow wrong
                    "reference_correction": bool(wrong),
                    "erroneous_tokens": wrong,
                }
            )
        if not pairs:
            no_pair.append(it["celex"])
        records.append(
            {
                "celex": it["celex"],
                "date": it["date"],
                "corrects": it["corrects"],
                "sha256": it["sha256"],
                "pair_count": len(pairs),
                "pairs": pairs,
            }
        )
    out = {
        "source_manifest_fetched_utc": manifest["fetched_utc"],
        "corrigenda_parsed": len(records),
        "corrigenda_with_no_for_read_pair": len(no_pair),
        "no_pair_celex": no_pair,
        "pair_total": sum(r["pair_count"] for r in records),
        "reference_correction_pairs": sum(
            1 for r in records for p in r["pairs"] if p["reference_correction"]
        ),
        "reference_correction_corrigenda": sum(
            1 for r in records if any(p["reference_correction"] for p in r["pairs"])
        ),
        "records": records,
    }
    (HERE / "pairs.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"corrigenda parsed            {out['corrigenda_parsed']}")
    print(f"  with no for/read pair      {out['corrigenda_with_no_for_read_pair']}")
    print(f"for/read pairs               {out['pair_total']}")
    print(f"  changing a document number {out['reference_correction_pairs']}")
    print(f"corrigenda with >=1 such     {out['reference_correction_corrigenda']}")


if __name__ == "__main__":
    main()
