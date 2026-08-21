#!/usr/bin/env python3
"""Count what the Official Journal printed, by the origin of the document it named.

Reads corpus/*.html and manifest.json; writes census.json and references.csv.
Every rule here is the one fixed in PREREGISTRATION.md before the run. Standard library only.
"""

import csv
import json
import pathlib
import re
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
CORPUS = HERE / "corpus"

# ————————————————————————————————————————————————————————— the reference form —
# Editions appear as ":YYYY" (CEN/CENELEC/ISO/IEC) or as " Vx.y.z" (ETSI), with optional
# "+Ann[:YYYY]" amendment suffixes. Both forms are part of the reference: a new edition of a
# standard is a new thing for the law to name.
ORIGIN = r"(?:ISO/IEC|ISO/ASTM|ISO|IEC)\s+"
NUMBER = r"\d{2,6}(?:\s\d{3})?(?:-\d+)*"
EDITION = r"(?::\d{4}(?:\+A\d+(?::\d{4})?)*|\s+V\d+\.\d+\.\d+)"
REF_RE = re.compile(rf"EN\s+(?:{ORIGIN})?{NUMBER}{EDITION}")

# Anything beginning "EN <digit>" that the pattern above did not take, so the misses are
# countable instead of invisible (adversarial read §5, and §8's "no silent caps").
LOOSE_RE = re.compile(r"EN\s+(?:ISO/IEC|ISO/ASTM|ISO|IEC)?\s*\d{2,6}[^\s,;.)]*")

WITHDRAWAL_MARKERS = (
    "withdrawn", "is deleted", "are deleted", "shall be deleted",
    "is removed", "are removed",
)
ADDITION_MARKERS = (
    "is added", "are added", "is inserted", "are inserted",
    "is replaced by", "are replaced by", "is amended as follows",
)
MARKERS = [(m, "withdrawal") for m in WITHDRAWAL_MARKERS] + \
          [(m, "addition") for m in ADDITION_MARKERS]


def text_of(path: pathlib.Path) -> str:
    html = path.read_text(encoding="utf-8", errors="replace")
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace(" ", " ").replace("‑", "-")
    return re.sub(r"\s+", " ", text)


def marker_positions(text: str) -> list[tuple[int, str]]:
    low = text.lower()
    out = []
    for phrase, kind in MARKERS:
        start = 0
        while True:
            idx = low.find(phrase, start)
            if idx < 0:
                break
            out.append((idx, kind))
            start = idx + 1
    return sorted(out)


def classify_origin(ref: str) -> tuple[str, str]:
    """Return (class, limb). Total and disjoint by construction — D-3."""
    body = ref[len("EN"):].strip()
    if body.startswith("ISO"):
        return "ISO", "explicit"
    if body.startswith("IEC"):
        return "IEC", "explicit"
    digits = re.match(r"(\d{2,6})(?:\s(\d{3}))?", body)
    if not digits:
        return "UNCLASSIFIED", "none"
    head = digits.group(1)
    if digits.group(2) and head in ("300", "301", "302", "303"):
        return "ETSI", "spaced"
    number = int(head)
    if 60000 <= number <= 69999:
        return "IEC", "inferred-60000"
    if 50000 <= number <= 59999:
        return "CENELEC", "number"
    return "CEN", "number"


INTL = {"ISO", "IEC"}


def act_kind(title: str) -> str:
    """Full-list acts republish a legislation's entire list; amending acts add to one.

    Not in the pre-registration, and added after the first run — see DECISION.md. The
    pre-registered measure counted a reference's first appearance in the corpus, which
    cannot tell a fresh citation from a whole list being re-printed: one act of 30 January
    2025 contributed 166 "new" references that way. This split is the correction, and it is
    named as post-hoc wherever its figures are used.
    """
    low = title.lower()
    if low.startswith("corrigendum"):
        return "CORRIGENDUM"
    if "amending" in low:
        return "AMENDING"
    if "correcting" in low:
        return "CORRECTING"
    return "FULL_LIST"


def fresh_by_month(fresh: list[dict]) -> dict:
    """First appearance within the amending-act subset, month by month, from 2024 on."""
    seen: set[str] = set()
    per_month: dict[str, Counter] = defaultdict(Counter)
    for row in fresh:                                          # already date-sorted
        if row["reference"] in seen:
            continue
        seen.add(row["reference"])
        if row["date"] >= "2024-01-01":
            per_month[row["date"][:7]][row["origin"]] += 1
    return {m: dict(sorted(c.items())) for m, c in sorted(per_month.items())}


def raw_prefix_check(acts: list[dict], year: str) -> dict:
    """A cross-check that shares nothing with the parse above: count the bare prefixes."""
    out = {"acts": 0, "EN ISO": 0, "EN IEC": 0, "EN 6xxxx": 0}
    for act in acts:
        if not act["date"].startswith(year) or "amending" not in act["title"].lower():
            continue
        path = CORPUS / f"{act['celex']}.html"
        if not path.exists():
            continue
        text = text_of(path)
        out["acts"] += 1
        out["EN ISO"] += len(re.findall(r"EN ISO ", text))
        out["EN IEC"] += len(re.findall(r"EN IEC ", text))
        out["EN 6xxxx"] += len(re.findall(r"EN 6\d{4}", text))
    return out


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    acts = sorted(manifest["acts"], key=lambda a: (a["date"], a["celex"]))

    rows = []
    parse_failures = []
    loose_misses = Counter()
    for act in acts:
        path = CORPUS / f"{act['celex']}.html"
        if not path.exists():
            parse_failures.append(act["celex"])
            continue
        text = text_of(path)
        markers = marker_positions(text)
        found = list(REF_RE.finditer(text))
        if not found:
            parse_failures.append(act["celex"])
            continue
        taken = set()
        for match in found:
            taken.update(range(match.start(), match.end()))
            ref = re.sub(r"\s+", " ", match.group(0)).strip()
            klass, limb = classify_origin(ref)
            section, position = "none", None
            for idx, kind in markers:
                if idx < match.start():
                    section, position = kind, idx
                else:
                    break
            rows.append(
                {
                    "celex": act["celex"],
                    "date": act["date"],
                    "year": act["date"][:4],
                    "reference": ref,
                    "origin": klass,
                    "limb": limb,
                    "section": section,
                }
            )
        for match in LOOSE_RE.finditer(text):
            if match.start() not in taken:
                loose_misses[re.sub(r"\s+", " ", match.group(0))[:40]] += 1

    unclassified = [r for r in rows if r["origin"] == "UNCLASSIFIED"]
    if unclassified:                                            # D-3 voids the run
        raise SystemExit(f"D-3 fired: {len(unclassified)} unclassified references")

    # ————————————————————————————————————————————————— first appearance per year —
    def first_year_table(subset: list[dict]) -> dict:
        first: dict[str, dict] = {}
        for row in subset:                                      # acts already date-sorted
            if row["reference"] not in first:
                first[row["reference"]] = row
        per_year: dict[str, Counter] = defaultdict(Counter)
        for row in first.values():
            per_year[row["year"]][row["origin"]] += 1
        table = {}
        for year in sorted(per_year):
            counts = per_year[year]
            total = sum(counts.values())
            intl = sum(counts[k] for k in INTL)
            table[year] = {
                "new_references": total,
                "intl": intl,
                "euro": total - intl,
                "intl_share": round(intl / total, 4) if total else None,
                "by_origin": dict(sorted(counts.items())),
            }
        return {"distinct": len(first), "per_year": table}

    not_withdrawn = [r for r in rows if r["section"] != "withdrawal"]
    attributed = sum(1 for r in rows if r["section"] != "none")

    kinds = {a["celex"]: act_kind(a["title"]) for a in acts}
    for row in rows:
        row["act_kind"] = kinds.get(row["celex"], "UNKNOWN")
    # A fresh citation is a reference entering the corpus for the first time **through an
    # amending act** — an addition to an existing list. First appearance is computed over the
    # whole corpus and only then filtered: computing it inside the subset would let a reference
    # first printed in a 2021 full list count as new when a 2025 act touches it again.
    global_first: dict[str, dict] = {}
    for row in rows:                                           # acts already date-sorted
        global_first.setdefault(row["reference"], row)
    fresh = [
        r for r in global_first.values()
        if r["act_kind"] == "AMENDING" and r["section"] != "withdrawal"
    ]

    def clause_reading(table: dict) -> dict:
        per = table["per_year"]
        base = [per[y]["intl_share"] for y in ("2020", "2021", "2022", "2023") if y in per]
        mean = sum(base) / len(base)
        s25, s26 = per["2025"]["intl_share"], per["2026"]["intl_share"]
        return {
            "baseline_2020_2023_mean_intl_share": round(mean, 4),
            "quarter_of_baseline": round(mean / 4, 4),
            "share_2025": s25,
            "share_2026": s26,
            "K1_2025_below_quarter": "HELD" if s25 < mean / 4 else "REFUTED",
            "K2_2025_intl_not_zero": "HELD" if per["2025"]["intl"] > 0 else "REFUTED",
            "K3_2026_above_2025": "HELD" if s26 > s25 else "REFUTED",
        }

    census = {
        "acts": len(acts),
        "acts_parsed": len(acts) - len(parse_failures),
        "parse_failures": parse_failures,
        "reference_rows": len(rows),
        "rows_attributed_to_a_marker": attributed,
        "attribution_coverage": round(attributed / len(rows), 4) if rows else None,
        "rows_marked_withdrawal": sum(1 for r in rows if r["section"] == "withdrawal"),
        "iec_limb_split": dict(Counter(r["limb"] for r in rows if r["origin"] == "IEC")),
        "loose_misses_total": sum(loose_misses.values()),
        "loose_misses_top": loose_misses.most_common(12),
        "act_kinds": dict(Counter(kinds.values())),
        "all_rows": first_year_table(rows),
        "excluding_withdrawal_rows": first_year_table(not_withdrawn),
        "fresh_citations_amending_acts_only": first_year_table(fresh),
        "rows_per_year": dict(sorted(Counter(r["year"] for r in rows).items())),
        "clauses": {
            "guard": {
                "rule": "PREREGISTRATION §5.1 — clauses NOT SETTLED below 0.80 attribution coverage",
                "coverage": round(attributed / len(rows), 4),
                "fired": (attributed / len(rows)) < 0.80,
            },
            "as_preregistered_all_rows": clause_reading(first_year_table(rows)),
            "as_preregistered_excluding_withdrawal": clause_reading(first_year_table(not_withdrawn)),
            "post_hoc_amending_acts_only": clause_reading(first_year_table(fresh)),
        },
        "raw_prefix_cross_check_2025_amending": raw_prefix_check(acts, "2025"),
        "fresh_by_month_since_2024": fresh_by_month(fresh),
    }
    (HERE / "census.json").write_text(json.dumps(census, indent=1), encoding="utf-8")

    with (HERE / "references.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps({k: v for k, v in census.items() if k != "loose_misses_top"}, indent=1))


if __name__ == "__main__":
    main()
