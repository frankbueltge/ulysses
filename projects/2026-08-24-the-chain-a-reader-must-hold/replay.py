#!/usr/bin/env python3
"""Replay the amendment chains of the 2026-08-21 corpus and ask, for every deleted row,
whether a reader holding only that corpus can find out what the row named.

Every rule here is the one fixed in PREREGISTRATION.md before this file was written.
The parser's vocabulary was built by reading DEVELOPMENT chains only (split.json).
Standard library only. Nothing is fetched: the corpus is read out of the tarball of
2026-08-21 and every act is verified against its recorded sha256 first.

Writes replay.json. Prints nothing that is not in it.
"""

import hashlib
import json
import pathlib
import re
import statistics
import sys
import tarfile
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "2026-08-21-the-citation-that-stopped"
PAIRING = HERE.parent / "2026-08-23-the-row-that-was-deleted" / "pairing.json"

# ————————————————————————————————————————————————————————— the reference form —
# Imported unchanged from 2026-08-21/census.py, not re-typed by hand.
ORIGIN = r"(?:ISO/IEC|ISO/ASTM|ISO|IEC)\s+"
NUMBER = r"\d{2,6}(?:\s\d{3})?(?:-\d+)*"
EDITION = r"(?::\d{4}(?:\+A\d+(?::\d{4})?)*|\s+V\d+\.\d+\.\d+)"
REF_RE = re.compile(rf"EN\s+(?:{ORIGIN})?{NUMBER}{EDITION}")
# the base number of a reference: the standard, stripped of edition and amendment suffix
BASE_NUM_RE = re.compile(rf"EN\s+(?:{ORIGIN})?({NUMBER})")

ANNEX_HEAD_RE = re.compile(r"(?i)>\s*ANNEX\s+([IVX]+[A-C]?)\s*<")
# annex-level operations, from PREREGISTRATION.md §1
MAP_AMEND_RE = re.compile(
    r"Annex\s+([IVX]+[A-C]?)\s+is amended in accordance with Annex\s+([IVX]+[A-C]?)\s+to this Decision")
MAP_INSERT_RE = re.compile(
    r"Annex\s+([IVX]+[A-C]?)\s*,\s*as set out in Annex\s+([IVX]+[A-C]?)\s+to this Decision\s*,\s*is inserted")
ANNEX_REPLACED_RE = re.compile(
    r"Annex\s+([IVX]+[A-C]?)\s+is replaced by the following")

# row-level deletions, from PREREGISTRATION.md §1
DELETE_RE = re.compile(
    r"(?:rows?|entr(?:y|ies))\s+(?:No\s+)?((?:\d+[a-z]?)(?:\s*,\s*(?:and\s+)?\d+[a-z]?)*(?:\s+and\s+\d+[a-z]?)?)\s+(?:is|are)\s+deleted",
    re.I)
ROWNUM_RE = re.compile(r"\d+[a-z]?")
CELL_ROW_RE = re.compile(r"^(\d{1,4}[a-z]?)\.?$")

# H4's independent ground truth: the pairing expression of 2026-08-23/pairing.py
# (`[‘'"]?(\d+[a-z])\.\s+EN\s`), extended only to capture the reference it already matched.
PAIRED_INSERT_RE = re.compile(
    rf"[‘'\"]?(\d+[a-z])\.\s+(EN\s+(?:{ORIGIN})?{NUMBER}{EDITION})")


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    txt = re.sub(r"<[^>]+>", " ", html).replace("\xa0", " ").replace("‑", "-")
    return re.sub(r"\s+", " ", txt)


def tables(html: str):
    """Yield (start_offset, rows) for every <table>; rows are lists of cell texts."""
    for m in re.finditer(r"(?is)<table\b.*?</table>", html):
        block = m.group(0)
        rows = []
        for tr in re.findall(r"(?is)<tr\b.*?</tr>", block):
            cells = [strip_tags(td).strip() for td in re.findall(r"(?is)<td\b.*?</td>", tr)]
            if cells:
                rows.append(cells)
        if rows:
            yield m.start(), rows


def annex_segments(html: str):
    """[(annex_label, start, end)] for the act's own annexes, in document order."""
    heads = [(m.group(1).upper(), m.start()) for m in ANNEX_HEAD_RE.finditer(html)]
    # a heading repeated (table of contents, running head) keeps its first occurrence
    seen, uniq = set(), []
    for label, pos in heads:
        if label not in seen:
            seen.add(label)
            uniq.append((label, pos))
    out = []
    for i, (label, pos) in enumerate(uniq):
        end = uniq[i + 1][1] if i + 1 < len(uniq) else len(html)
        out.append((label, pos, end))
    return out


def printed_rows(html: str, lo: int, hi: int):
    """Row numbers a content table in [lo,hi) sets out, with their references.

    A content table is one whose first column carries row numbers and whose second column
    carries at least one standard reference. Layout tables — the numbered instruction lists
    the Journal renders as tables — have '(1)' in the first cell and are skipped by this test.
    """
    found = {}
    for pos, rows in tables(html):
        if not (lo <= pos < hi):
            continue
        for cells in rows:
            if len(cells) < 2:
                continue
            m = CELL_ROW_RE.match(cells[0])
            if not m:
                continue
            body = " ".join(cells[1:])
            refs = REF_RE.findall(body)
            if not refs:
                continue
            found.setdefault(m.group(1).lower(), (pos, refs))
    return found


def deletions(html: str, lo: int, hi: int):
    """[(doc_pos, row_number)] for every deletion instruction in [lo,hi)."""
    seg = html[lo:hi]
    out = []
    for m in DELETE_RE.finditer(strip_tags(seg)):
        for num in ROWNUM_RE.findall(m.group(1)):
            out.append((lo + m.start(), num.lower()))
    return out


def base_number(ref: str) -> str:
    m = BASE_NUM_RE.match(ref)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ref


def main() -> None:
    man = json.loads((SRC / "manifest.json").read_text())
    acts = {a["celex"]: a for a in man["acts"]}
    split = json.loads((HERE / "split.json").read_text())
    chains = split["chains"]
    held_out = set(split["held_out"])

    html = {}
    bad = []
    with tarfile.open(SRC / "corpus.tar.gz") as tf:
        for celex, meta in acts.items():
            raw = tf.extractfile(f"corpus/{celex}.html").read()
            if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
                bad.append(celex)
            html[celex] = raw.decode("utf-8", errors="replace")
    if bad:
        sys.exit(f"corpus hash mismatch: {bad}")

    # ——————————————————————————————————————————— the printing index and the deletions —
    # printings[(base, annex, row)] -> [(date, celex, doc_pos, refs)]
    printings = defaultdict(list)
    dels = []            # (base, annex, row, date, celex, doc_pos)
    touches = defaultdict(set)   # (base, annex) -> {(date, celex)}
    unmapped, renumbered = [], []

    for base, amenders in chains.items():
        # the base act as published: its own annexes are the initial state
        h = html[base]
        for label, lo, hi in annex_segments(h):
            for row, (pos, refs) in printed_rows(h, lo, hi).items():
                printings[(base, label, row)].append((acts[base]["date"], base, pos, refs))

        for celex in amenders:
            h = html[celex]
            segs = annex_segments(h)
            article1 = h[: segs[0][1]] if segs else h
            a1 = strip_tags(article1)
            if ANNEX_REPLACED_RE.search(a1):
                renumbered.append({"base": base, "act": celex})
                continue
            own_to_base = {}
            for base_annex, own in MAP_AMEND_RE.findall(a1):
                own_to_base[own.upper()] = base_annex.upper()
            for base_annex, own in MAP_INSERT_RE.findall(a1):
                own_to_base[own.upper()] = base_annex.upper()
            if not own_to_base:
                # a single-annex amending act: its one annex acts on the base annex named
                # in Article 1, if Article 1 names exactly one
                named = {x.upper() for x in re.findall(r"Annex\s+([IVX]+[A-C]?)\b", a1)}
                if len(segs) == 1 and len(named) == 1:
                    own_to_base[segs[0][0]] = named.pop()
            for label, lo, hi in segs:
                target = own_to_base.get(label)
                if target is None:
                    if printed_rows(h, lo, hi) or deletions(h, lo, hi):
                        unmapped.append({"base": base, "act": celex, "own_annex": label})
                    continue
                touches[(base, target)].add((acts[celex]["date"], celex))
                for row, (pos, refs) in printed_rows(h, lo, hi).items():
                    printings[(base, target, row)].append(
                        (acts[celex]["date"], celex, pos, refs))
                for pos, row in deletions(h, lo, hi):
                    dels.append((base, target, row, acts[celex]["date"], celex, pos))

    # ————————————————————————————————————————————————————————————— resolve each row —
    resolved = []
    for base, annex, row, date, celex, pos in sorted(dels, key=lambda d: (d[3], d[4], d[5])):
        prior = [p for p in printings[(base, annex, row)]
                 if p[0] < date or (p[1] == celex and p[2] < pos)]
        prior.sort(key=lambda p: (p[0], p[2]))
        in_base = any(p[1] == base for p in prior)
        last = prior[-1] if prior else None
        depth = 1 + len({c for d, c in touches[(base, annex)] if d <= date})
        resolved.append({
            "base": base, "annex": annex, "row": row,
            "deleting_act": celex, "date": date,
            "printed_by_base_act": in_base,
            "resolves": last is not None,
            "last_printed_by": last[1] if last else None,
            "last_printed_date": last[0] if last else None,
            "reference": last[3][0] if last else None,
            "depth": depth,
            "held_out": base in held_out,
        })

    ho = [r for r in resolved if r["held_out"]]

    # ——————————————————————————————————————————————————————————————— the clauses —
    def clause(name, num, den, band):
        if den < 20:
            return {"clause": name, "band": band, "n": den, "verdict": "VOID (n < 20)"}
        share = num / den
        return {"clause": name, "band": band, "numerator": num, "denominator": den,
                "measured": round(share, 4),
                "verdict": "HELD" if share >= band else "FAILED"}

    not_in_base = [r for r in ho if not r["printed_by_base_act"]]
    h1 = clause("H1 the base act alone is not enough", len(not_in_base), len(ho), 0.15)
    h2 = clause("H2 the corpus closes the gap",
                sum(1 for r in not_in_base if r["resolves"]), len(not_in_base), 0.50)

    depths = [r["depth"] for r in ho]
    med = statistics.median(depths) if depths else None
    h3 = ({"clause": "H3 the burden is more than two documents", "band": ">= 3",
           "n": len(depths), "verdict": "VOID (n < 20)"} if len(depths) < 20 else
          {"clause": "H3 the burden is more than two documents", "band": ">= 3",
           "n": len(depths), "measured_median": med,
           "mean": round(sum(depths) / len(depths), 2), "max": max(depths),
           "verdict": "HELD" if med >= 3 else "FAILED"})

    # H4's ground truth is the PAIRING of 2026-08-23, detected by that night's own
    # expression on the FLAT TEXT of the deleting act. Tonight's index reads TABLES in
    # earlier acts. The two readings share the HTML and nothing else; PREREGISTRATION §5.4
    # states what that does and does not buy. `pairing.json` itself carries only a
    # twelve-row sample of the unpaired, so the expression is re-run rather than its
    # output re-used — the deviation is recorded in DECISION.md.
    agree = tot = 0
    disagreements = []
    for r in ho:
        if not r["resolves"]:
            continue
        flat = strip_tags(html[r["deleting_act"]])
        target = None
        for m in PAIRED_INSERT_RE.finditer(flat):
            if re.sub(r"\D", "", m.group(1)) == re.sub(r"\D", "", r["row"]):
                target = m.group(2)
                break
        if target is None:
            continue
        tot += 1
        if base_number(target) == base_number(r["reference"]):
            agree += 1
        else:
            disagreements.append({"row": r["row"], "act": r["deleting_act"],
                                  "resolved": r["reference"], "inserted": target})
    h4 = clause("H4 instrument validity against the 2026-08-23 pairing", agree, tot, 0.85)

    guard = [r for i, r in enumerate([x for x in ho if x["resolves"]]) if i % 10 == 0]

    out = {
        "corpus": {"source": "../2026-08-21-the-citation-that-stopped/corpus.tar.gz",
                   "acts": len(acts), "all_hashes_verified": True},
        "split": {"development_chains": len(split["development"]),
                  "held_out_chains": len(split["held_out"])},
        "coverage": {
            "deletion_instructions_attached_to_an_annex": len(dels),
            "held_out": len(ho),
            "development": len(resolved) - len(ho),
            "annex_segments_with_content_but_no_mapping": unmapped,
            "chains_dropped_for_wholesale_annex_replacement": renumbered,
        },
        "clauses": [h1, h2, h3, h4],
        "h4_disagreements": disagreements,
        "guard_sample_every_10th_resolved_held_out": guard,
        "held_out_rows": ho,
    }
    (HERE / "replay.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
