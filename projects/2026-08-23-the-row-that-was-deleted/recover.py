"""The recovery probe — what it takes to find out which standard a row number un-named.

Not a clause. PREREGISTRATION.md §4 measures whether the pointer's target is in reach;
this asks what happens when you follow it, on a fixed sample chosen by document order, and
it is reported as a probe with n named, never as a rate.

For each sampled number-only deletion: open the base act as the Official Journal published
it, index its annex rows by number, look the deleted number up, and count how many other
amending acts in the corpus touched the same base act before the deletion — because a row
number resolves against the list as it stood that day, not as it was first printed.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "2026-08-21-the-citation-that-stopped"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))
from census import text_of  # noqa: E402
from split import load, split  # noqa: E402
from removals import read_act, BASE_RE, celex_of  # noqa: E402

SAMPLE_N = 6

# A row of a harmonised-standards annex: a number, a full stop, then a standard reference.
ROW_RE = re.compile(r"[‘'\"]?(\d+[a-z]?)\.\s+(EN\s+(?:ISO/IEC|ISO/ASTM|ISO|IEC)?\s*\d[^\n]{0,90})")


def row_index(text: str) -> dict:
    out = {}
    for m in ROW_RE.finditer(text):
        out.setdefault(m.group(1), re.sub(r"\s+", " ", m.group(2)).strip())
    return out


def numbers_of(instruction) -> list:
    return re.findall(r"\d+[a-z]?", instruction["numbers"])


def main() -> None:
    man = json.loads((SRC / "manifest.json").read_text())
    all_acts = man["acts"]
    corpus = SRC / "corpus"
    present = {a["celex"] for a in all_acts}
    by_celex = {a["celex"]: a for a in all_acts}

    _, held_meta = split(all_acts)
    held = [read_act(a, corpus) for a in held_meta]

    # Which amending acts in the corpus cite each base act — the intervening-amendment count.
    touches = {}
    for a in all_acts:
        t = text_of(corpus / f"{a['celex']}.html")
        for m in BASE_RE.finditer(t):
            c = celex_of(m.group(1), m.group(2))
            if c != a["celex"]:
                touches.setdefault(c, set()).add((a["date"], a["celex"]))

    picked, results = 0, []
    for act in held:
        for ins in act["instructions"]:
            if picked >= SAMPLE_N:
                break
            if ins["kind"] != "DELETION" or not ins["number_only"]:
                continue
            base = act["base"]
            if base not in present:
                continue
            picked += 1
            base_text = text_of(corpus / f"{base}.html")
            idx = row_index(base_text)
            nums = numbers_of(ins)
            between = sorted(
                c for d, c in touches.get(base, set())
                if by_celex[base]["date"] < d < act["date"] and c != act["celex"]
            )
            results.append({
                "deleting_act": act["celex"],
                "date": act["date"],
                "instruction": ins["span"][:120].strip(),
                "base_act": base,
                "base_published": by_celex[base]["date"],
                "rows_deleted": nums,
                "resolved_in_base_as_published": {
                    n: idx.get(n, "NOT FOUND") for n in nums
                },
                "found": sum(1 for n in nums if n in idx),
                "of": len(nums),
                "intervening_amending_acts_in_corpus": between,
                "intervening_count": len(between),
            })
        if picked >= SAMPLE_N:
            break

    total_rows = sum(r["of"] for r in results)
    found_rows = sum(r["found"] for r in results)
    out = {
        "probe": "recovery of a deleted row from the base act as published",
        "sample_rule": f"first {SAMPLE_N} number-only deletions in held-out document order "
                       "whose base act is present in the corpus",
        "n_instructions": len(results),
        "rows_looked_up": total_rows,
        "rows_found_in_base_as_published": found_rows,
        "results": results,
    }
    (HERE / "recovery.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print(f"probe: {len(results)} deletions, {total_rows} row numbers, "
          f"{found_rows} found in the base act as published")
    for r in results:
        print(f"\n{r['deleting_act']} ({r['date']}) → {r['base_act']} (published {r['base_published']})")
        print(f"  {r['instruction']}")
        print(f"  intervening amending acts in corpus: {r['intervening_count']}")
        for n, v in r["resolved_in_base_as_published"].items():
            print(f"   row {n}: {v[:88]}")


if __name__ == "__main__":
    main()


# ————————————————————————————————————————————————————————— POST-HOC, 2026-08-23 —
# Not pre-registered. The probe above found two of six deleted row numbers absent from the
# base act as published — because an intervening amendment created them. This measures how
# often that happens across the whole held-out set, conservatively: a deleted number counts
# as unresolvable only when it is LARGER than every row number the base act printed, which
# no reading of the base act alone can explain away.
def out_of_range_census() -> dict:
    man = json.loads((SRC / "manifest.json").read_text())
    all_acts = man["acts"]
    corpus = SRC / "corpus"
    present = {a["celex"] for a in all_acts}
    _, held_meta = split(all_acts)
    held = [read_act(a, corpus) for a in held_meta]

    max_row: dict = {}
    for c in present:
        idx = row_index(text_of(corpus / f"{c}.html"))
        nums = [int(re.sub(r"\D", "", n)) for n in idx if re.sub(r"\D", "", n)]
        max_row[c] = max(nums) if nums else 0

    rows_total = rows_beyond = 0
    ins_total = ins_with_beyond = 0
    cases = []
    for act in held:
        for ins in act["instructions"]:
            if ins["kind"] != "DELETION" or not ins["number_only"]:
                continue
            base = act["base"]
            if base not in present:
                continue
            ins_total += 1
            beyond = []
            for n in numbers_of(ins):
                rows_total += 1
                if int(re.sub(r"\D", "", n)) > max_row[base]:
                    rows_beyond += 1
                    beyond.append(n)
            if beyond:
                ins_with_beyond += 1
                cases.append({
                    "deleting_act": act["celex"], "date": act["date"], "base_act": base,
                    "base_max_row_as_published": max_row[base], "rows_beyond": beyond,
                })
    return {
        "note": "POST-HOC, not pre-registered. Conservative: counts only row numbers larger "
                "than every row the base act printed.",
        "deletion_instructions": ins_total,
        "instructions_with_an_unresolvable_row": ins_with_beyond,
        "row_numbers": rows_total,
        "row_numbers_beyond_the_base_act_as_published": rows_beyond,
        "share_of_rows_unresolvable": rows_beyond / rows_total if rows_total else None,
        "cases": cases,
    }


if __name__ == "__main__":
    extra = out_of_range_census()
    p = HERE / "recovery.json"
    d = json.loads(p.read_text())
    d["out_of_range_post_hoc"] = extra
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    print("\n--- POST-HOC: rows deleted that the base act as published never contained ---")
    print(f"deletion instructions {extra['deletion_instructions']}, "
          f"row numbers {extra['row_numbers']}")
    print(f"beyond the base act's last printed row: {extra['row_numbers_beyond_the_base_act_as_published']}"
          f"  ({extra['share_of_rows_unresolvable']:.3f})")
    print(f"instructions carrying at least one such row: {extra['instructions_with_an_unresolvable_row']}")
