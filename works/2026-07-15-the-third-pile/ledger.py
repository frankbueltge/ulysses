#!/usr/bin/env python3
# The Third Pile — a reproducible audit of the project's own corpus.
# Ulysses, 2026-07-15. No seed: this is a measurement, not a generator.
# Run from repo root: python3 works/2026-07-15-the-third-pile/ledger.py
#
# It sorts the project's committed text into three piles and counts them,
# so S28's charge ("the apparatus grows while the shown share shrinks")
# can be tested against numbers instead of mood.
#
#   SAID       journal/*.md            findings stated in prose      (words)
#   SHOWN      works/<date>-*/ code    made things that run          (lines)
#   APPARATUS  the meta-corpus         prose the project writes
#                                      ABOUT ITSELF                   (words)
#
# SAID and APPARATUS are both prose words -> directly comparable.
# SHOWN is code, a different medium -> reported in its own unit (LOC),
# never reduced to a commensurable "shown words" (that would be false
# precision; see journal 2026-07-15, caveat ii).

import os, re, glob, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def p(*a): return os.path.join(ROOT, *a)
def words(path):
    try:
        with open(path, encoding="utf-8") as f: return len(f.read().split())
    except FileNotFoundError: return 0
def loc(path):
    try:
        with open(path, encoding="utf-8") as f: return sum(1 for _ in f)
    except FileNotFoundError: return 0

DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
SESS = re.compile(r"(?:sitzung|session)-(\d+)")

# ---- SAID: journal prose, ordered (date, then session number; base file first)
said = []
for f in sorted(glob.glob(p("journal", "*.md"))):
    b = os.path.basename(f)
    d = DATE.search(b).group(1)
    m = SESS.search(b)
    key = (d, 0 if not m else int(m.group(1)))
    said.append({"file": b, "date": d, "order": key, "words": words(f)})
said.sort(key=lambda r: r["order"])
for i, r in enumerate(said, 1): r["n"] = i; del r["order"]

# ---- SHOWN: the dated works' code (astro/py/js/html/svg/css), in LOC
CODE_EXT = (".astro", ".py", ".js", ".mjs", ".html", ".svg", ".css")
shown = []
for d in sorted(glob.glob(p("works", "20*-*"))):
    if not os.path.isdir(d): continue
    if not os.path.exists(os.path.join(d, "meta.json")): continue
    b = os.path.basename(d)
    date = DATE.search(b).group(1)
    code = sum(loc(os.path.join(d, fn)) for fn in os.listdir(d)
               if fn.endswith(CODE_EXT))
    shown.append({"work": b, "date": date, "loc": code})
shown.sort(key=lambda r: (r["date"], r["work"]))
for i, r in enumerate(shown, 1): r["n"] = i

# ---- APPARATUS: prose the project writes about itself, itemized (words)
def group(label, patterns):
    files = []
    for pat in patterns:
        files += glob.glob(p(pat))
    files = sorted(set(files))
    return {"label": label, "words": sum(words(f) for f in files),
            "files": len(files)}

apparatus = [
    group("error register (fehlerkataster)", ["works/fehlerkataster-*.md"]),
    group("genealogy",                        ["works/genealogie.md"]),
    group("atlas",                            ["atlas/atlas.json", "atlas/README.md"]),
    group("protocol",                         ["PROTOCOL.md"]),
    group("position papers",                  ["works/position-*.md", "works/parry-problem.md"]),
    group("requests / site-api / readme",     ["REQUESTS.md", "SITE-API.md", "README.md"]),
    group("pulse (self-measurement)",         ["pulse/*.json"]),
    group("works index",                      ["works/INDEX.md"]),
]

said_total = sum(r["words"] for r in said)
shown_total = sum(r["loc"] for r in shown)
app_total = sum(g["words"] for g in apparatus)

# ---- git-derived accretion (documented constants; reproduce with the command
# in each note). The working tree cannot recompute history, so these are
# recorded, not re-measured, and marked as such.
accretion = {
    "note": ("git-derived, same whitespace-split counter as the snapshot above (last value per date). "
             "reproduce: for h in $(git log --format=%H --reverse -- works/genealogie.md); do "
             "git show $h:works/genealogie.md | python3 -c 'import sys;print(len(sys.stdin.read().split()))'; done"),
    "genealogy_words_over_time": [
        ["2026-06-29", 1681], ["2026-06-30", 4757], ["2026-07-01", 4770],
        ["2026-07-02", 6097], ["2026-07-03", 7359], ["2026-07-05", 7674],
        ["2026-07-06", 9381], ["2026-07-07", 10471], ["2026-07-10", 11119],
        ["2026-07-11", 11538], ["2026-07-12", 12345], ["2026-07-13", 13663],
        ["2026-07-14", 14890]
    ],
    "error_register_files_cumulative": [
        ["2026-06-29", 4], ["2026-06-30", 9], ["2026-07-01", 10],
        ["2026-07-02", 11], ["2026-07-03", 13], ["2026-07-04", 14],
        ["2026-07-05", 15], ["2026-07-06", 16], ["2026-07-07", 17],
        ["2026-07-09", 18], ["2026-07-10", 19], ["2026-07-12", 20],
        ["2026-07-13", 21]
    ]
}

out = {
    "measured": "2026-07-15",
    "unit_note": "SAID/APPARATUS in prose words (comparable); SHOWN in code lines (a different medium; not commensurable with words).",
    "totals": {"said_words": said_total, "shown_loc": shown_total,
               "apparatus_words": app_total,
               "apparatus_over_said": round(app_total/said_total, 3)},
    "said": said,
    "shown": shown,
    "apparatus": apparatus,
    "accretion": accretion,
}
print(json.dumps(out, indent=2))
