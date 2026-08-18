#!/usr/bin/env python3
"""Step 3 — parse: the newest edition year each section binds, at both dates.

THE BLIND STEP (PREREGISTRATION-01.md, §4 condition 2). The extraction rule below —
`RE_YEAR4`, `W3A_MARKERS`, `edition_years()`, `flatten()` and the DIV8/CITA/EDNOTE
handling — is copied **unchanged** from
`projects/2026-08-17-the-warrant-under-the-section/parse_warrants.py`, which was written
on 2026-08-17 for a different question, before tonight's question existed. It is not
adjusted here for any reason. Its known defects travel with it and are declared as limits.

Nothing here reads a band or scores a clause; that is `score.py`.

Input:  data/xml/{before,after}/*.xml + data/snapshot-manifest.json + data/versions.json
Output: data/moves.json — one record per corpus section.

Usage: python3 parse_moves.py
"""

import json
import os
import re
import sys

BASE = "projects/2026-08-18-when-the-law-reopens-the-page"
PRIOR = "projects/2026-08-17-the-warrant-under-the-section/data/warrants.json"
OUT = f"{BASE}/data/moves.json"

# ---- copied unchanged from 2026-08-17 parse_warrants.py ----------------------
RE_YEAR4 = re.compile(r"(?<!\d)(19\d{2}|20[0-2]\d)(?!\d)")
W3A_MARKERS = ("FR ", "Federal Register", "Pub. L", "U.S.C", "Stat.", "CFR")
RE_CITA = re.compile(r"<CITA\b.*?</CITA>", re.S)
RE_EDNOTE = re.compile(r"<EDNOTE\b.*?</EDNOTE>", re.S)
RE_DIV8 = re.compile(r"<DIV8\b.*?</DIV8>", re.S)
RE_P = re.compile(r"<P\b[^>]*>(.*?)</P>", re.S)
RE_TAG = re.compile(r"<[^>]+>")
ENTITIES = {"&#xA7;": "§", "&amp;": "&", "&#x2014;": "—", "&quot;": '"',
            "&#x201C;": "“", "&#x201D;": "”", "&lt;": "<", "&gt;": ">"}


def flatten(s: str) -> str:
    s = RE_TAG.sub("", s)
    for k, v in ENTITIES.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip()


def edition_years(paragraphs: list[str]) -> list[int]:
    out = []
    for p in paragraphs:
        for m in RE_YEAR4.finditer(p):
            before = p[max(0, m.start() - 25):m.start()]
            if any(k in before for k in W3A_MARKERS):
                continue
            out.append(int(m.group(1)))
    return out
# ---- end of copied block ----------------------------------------------------


def newest_edition(path: str) -> tuple[int | None, int]:
    raw = open(path, encoding="utf-8", errors="replace").read()
    div = RE_DIV8.search(raw)
    body = div.group(0) if div else raw
    stripped = RE_EDNOTE.sub(" ", RE_CITA.sub(" ", body))
    paragraphs = [p for p in (flatten(x) for x in RE_P.findall(stripped)) if p]
    eys = edition_years(paragraphs)
    return (max(eys) if eys else None), len(eys)


def main() -> int:
    man = json.load(open(f"{BASE}/data/snapshot-manifest.json"))
    vers = {(r["title"], r["section"]): r for r in
            json.load(open(f"{BASE}/data/versions.json"))["records"]}
    prior = {(r.get("title"), r.get("section")): r for r in json.load(open(PRIOR))["records"]}

    got = {}
    for f in man["files"]:
        got[(f["which"], f["title"], f["section"])] = f

    records = []
    for (title, section), v in sorted(vers.items()):
        amd = sorted(x["date"] for x in v.get("versions", []) if x.get("date", "") >= "2017-01-02")
        rec = {
            "title": title, "section": section,
            "n_amendments_since_2017": len(amd),
            "reopened": bool(amd),
            "first_amendment": amd[0] if amd else None,
            "last_amendment": amd[-1] if amd else None,
            "last_version_date": max((x["date"] for x in v.get("versions", []) if x.get("date")),
                                     default=None),
            "printed_warrant_year": prior.get((title, section), {}).get("warrant_year"),
            "prior_newest_edition_year": prior.get((title, section), {}).get("newest_edition_year"),
        }
        for which in ("after", "before"):
            f = got.get((which, title, section))
            if f is None:
                rec[f"{which}_http"] = None
                rec[f"{which}_edition"] = None
                rec[f"{which}_sha256"] = None
                continue
            rec[f"{which}_http"] = f["http"]
            rec[f"{which}_sha256"] = f.get("sha256")
            path = f"{BASE}/data/xml/{which}/{f['file']}"
            if f["http"] == "200" and os.path.exists(path):
                ey, n = newest_edition(path)
                rec[f"{which}_edition"] = ey
                rec[f"{which}_n_years"] = n
            else:
                rec[f"{which}_edition"] = None
                rec[f"{which}_n_years"] = 0

        b, a = rec.get("before_edition"), rec.get("after_edition")
        if rec["reopened"] and b is not None and a is not None:
            rec["scorable_both_ends"] = True
            rec["delta"] = a - b
            rec["moved"] = a > b
            rec["retreat"] = a < b
        else:
            rec["scorable_both_ends"] = False
            rec["delta"] = None
            rec["moved"] = None
            rec["retreat"] = None
        rec["bytes_differ"] = (rec.get("before_sha256") is not None
                               and rec.get("after_sha256") is not None
                               and rec["before_sha256"] != rec["after_sha256"])
        records.append(rec)

    with open(OUT, "w") as fh:
        json.dump({"corpus": len(records), "before_date": man["before_date"],
                   "after_date": man["after_date"], "records": records}, fh, indent=1)
    print(f"{len(records)} sections -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
