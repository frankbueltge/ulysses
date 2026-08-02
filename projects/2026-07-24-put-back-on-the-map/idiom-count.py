#!/usr/bin/env python3
"""Frequency of the five terms named in the toolkit seed of 2026-08-02 (T3, the
pragmatics audit) across this practice's own record.

What this does: counts term families in `journal/*.md` and `projects/*/TRACE.md`,
reports rate per 10 000 words, and dates every occurrence of the two rarest.

What this does NOT do, and the reason it is written this narrowly: a count
establishes that a term is frequent. It cannot establish the seed's actual claim —
that the term *functions* as an order-word, performing an incorporeal
transformation. That separation is the same wall that retired the tick-26 control
in the work-line (a value cannot be individuated as a parameter without knowing
what licenses it). Nothing here may be read as evidence for the pragmatic claim.

Run from the repository root:  python3 projects/2026-07-24-put-back-on-the-map/idiom-count.py
"""

import collections
import glob
import re

# The five terms as the seed names them, plus the families they paraphrase.
FAMILIES = {
    "earn* (seed: 'earned')": r"\bearn(ed|s|ing)?\b",
    "honest* (seed: 'the honest close')": r"\bhonest(ly|y)?\b",
    "  of which 'the honest <X>'": r"\bthe honest (close|outcome|reading|form|thing|answer)\b",
    "defeat* (seed: 'defeated')": r"\bdefeat(ed|s|ing|able)?\b",
    "'flagged against myself' verbatim": r"\bflagged against myself\b",
    "flag* … against me/myself": r"\bflag\w*\b[^.]{0,60}\bagainst (me|myself|my own)\b",
    "'runs in my favour' verbatim": r"\bruns in my favou?r\b",
    "in my favour/favor (any)": r"\bin my favou?r\b",
}

RARE = ["in my favour/favor (any)", "flag* … against me/myself"]


def corpus():
    return sorted(glob.glob("journal/*.md")) + sorted(glob.glob("projects/*/TRACE.md"))


def main():
    files = corpus()
    totals = collections.Counter()
    words = 0
    hits = collections.defaultdict(list)
    for path in files:
        text = open(path, encoding="utf-8").read()
        words += len(text.split())
        for name, pattern in FAMILIES.items():
            found = list(re.finditer(pattern, text, re.I))
            totals[name] += len(found)
            if name in RARE:
                for m in found:
                    line = text.count("\n", 0, m.start()) + 1
                    hits[name].append((path, line, m.group(0)))

    print(f"corpus: {len(files)} files, {words} words "
          f"(journal entries and project TRACEs)\n")
    for name in FAMILIES:
        n = totals[name]
        print(f"{name:38} {n:5}   {n / words * 10000:5.1f} per 10k words")

    for name in RARE:
        print(f"\n-- every occurrence of: {name}")
        for path, line, text in hits[name]:
            print(f"   {path}:{line}  {text!r}")

    print("\n-- density over time: journal entries, by calendar week")
    weeks = collections.defaultdict(lambda: collections.Counter())
    for path in sorted(glob.glob("journal/*.md")):
        stamp = path.split("/")[-1][:10]
        if not re.match(r"\d{4}-\d{2}-\d{2}$", stamp):
            continue
        text = open(path, encoding="utf-8").read()
        key = f"{stamp[:7]}-w{(int(stamp[8:10]) - 1) // 7 + 1}"
        weeks[key]["words"] += len(text.split())
        weeks[key]["earn"] += len(re.findall(FAMILIES["earn* (seed: 'earned')"], text, re.I))
        weeks[key]["honest"] += len(
            re.findall(FAMILIES["honest* (seed: 'the honest close')"], text, re.I))
    for key in sorted(weeks):
        w = weeks[key]
        print(f"   {key}  words {w['words']:6}   "
              f"earn* {w['earn']:3} ({w['earn'] / w['words'] * 10000:5.1f}/10k)   "
              f"honest* {w['honest']:3} ({w['honest'] / w['words'] * 10000:5.1f}/10k)")


if __name__ == "__main__":
    main()
