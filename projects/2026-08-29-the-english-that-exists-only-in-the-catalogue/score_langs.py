#!/usr/bin/env python3
"""Score L1–L5 of PREREGISTRATION.md against catalogue.json and probes.json.

Nothing here selects; the population was fixed by a committed file written the night before.
The collision rule of §4.3 runs before L2 and L4 and can void them.
"""

import collections
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DIGITAL = {"html", "xhtml", "pdf", "pdf1x", "pdfa1a", "pdfa1b", "pdfa2a", "pdfx",
           "fmx4", "xml", "doc", "docx", "epub"}

cat = json.loads((HERE / "catalogue.json").read_text())["listings"]
prb = json.loads((HERE / "probes.json").read_text())["probes"]


def served(p: dict) -> bool:
    return (p["http_status"] == 200 and p["bytes"] >= 500
            and (p.get("content_type") or "").startswith("text/html"))


def digital(types: list[str]) -> bool:
    return bool(set(types) & DIGITAL)


works = sorted(cat)
out: dict = {"population": len(works)}

# —— the types the register used, published whatever the outcome (§2 of the pre-registration)
types_seen = collections.Counter(t for v in cat.values() for ts in v.values() for t in ts)
out["manifestation_types_seen"] = dict(types_seen.most_common())
out["types_outside_declared_sets"] = sorted(set(types_seen) - DIGITAL - {"print"})

# —— selection cross-check: the catalogue must still list no digital English manifestation
out["cross_check_eng_digital_now"] = sorted(c for c in works if digital(cat[c].get("ENG", [])))
out["works_without_eng_expression"] = sorted(c for c in works if "ENG" not in cat[c])

# —— void guard
out["works_with_a_binding"] = sum(1 for c in works if cat[c])
void_all = out["works_with_a_binding"] < 150

# —— L1
l1_works = [c for c in works if any(l != "ENG" and digital(t) for l, t in cat[c].items())]
out["L1"] = {"floor": ">= 60 %", "n": len(l1_works), "of": len(works),
             "pct": round(100 * len(l1_works) / len(works), 1),
             "verdict": "VOID" if void_all else
                        ("HELD" if len(l1_works) / len(works) >= 0.60 else "FAILED")}

# —— §4.3 collision rule, before L2 and L4
coll_total = coll_hit = 0
for c in works:
    by_sha = collections.defaultdict(list)
    for lang, p in prb.get(c, {}).items():
        if served(p) and p["sha256"]:
            by_sha[p["sha256"]].append(lang)
    for sha, langs in by_sha.items():
        non_eng = [l for l in langs if l != "ENG"]
        coll_total += len(non_eng)
        if len(langs) > 1:
            coll_hit += len(non_eng)
out["collision"] = {"served_non_english_responses": coll_total,
                    "sharing_a_sha256_with_another_language": coll_hit,
                    "pct": round(100 * coll_hit / coll_total, 1) if coll_total else 0.0,
                    "voids_L2_L4_above": "20 %"}
collided = coll_total and (coll_hit / coll_total) > 0.20

# —— L2
l2_hits = [c for c in l1_works
           if any(l != "ENG" and digital(cat[c][l]) and served(prb.get(c, {}).get(l, {"http_status": 0, "bytes": 0}))
                  for l in cat[c])]
out["L2"] = {"floor": ">= 85 %", "n": len(l2_hits), "of": len(l1_works),
             "pct": round(100 * len(l2_hits) / len(l1_works), 1) if l1_works else 0.0,
             "verdict": "VOID (collision rule §4.3)" if collided else
                        ("HELD" if l1_works and len(l2_hits) / len(l1_works) >= 0.85 else "FAILED")}

# —— L3
l3_hits = [c for c in works if served(prb.get(c, {}).get("ENG", {"http_status": 0, "bytes": 0}))]
out["L3"] = {"floor": "<= 10 %", "n": len(l3_hits), "of": len(works),
             "pct": round(100 * len(l3_hits) / len(works), 1),
             "works": sorted(l3_hits),
             "verdict": "VOID" if void_all else
                        ("HELD" if len(l3_hits) / len(works) <= 0.10 else "FAILED")}

# —— L4
p193 = [c for c in works if int(c[1:5]) >= 1973]
l4_hits = [c for c in p193 if digital(cat[c].get("DAN", []))]
out["L4"] = {"floor": ">= 40 %", "n": len(l4_hits), "of": len(p193),
             "pct": round(100 * len(l4_hits) / len(p193), 1) if p193 else 0.0,
             "verdict": "VOID (collision rule §4.3)" if collided else
                        ("HELD" if p193 and len(l4_hits) / len(p193) >= 0.40 else "FAILED")}

# —— L5
n5 = h5 = 0
undeclared_served = []
for c in works:
    for lang, types in cat[c].items():
        if digital(types):
            continue
        p = prb.get(c, {}).get(lang)
        if p is None:
            continue
        n5 += 1
        if served(p):
            h5 += 1
            undeclared_served.append(f"{c}/{lang}")
out["L5"] = {"floor": "<= 5 %", "n": h5, "of": n5,
             "pct": round(100 * h5 / n5, 1) if n5 else 0.0,
             "examples": sorted(undeclared_served)[:20],
             "verdict": "VOID" if void_all else ("HELD" if n5 and h5 / n5 <= 0.05 else "FAILED")}

# —— descriptive, not scored
status = collections.Counter(p["http_status"] for v in prb.values() for p in v.values())
out["http_status_distribution"] = dict(status.most_common())
out["served_pairs"] = sum(1 for v in prb.values() for p in v.values() if served(p))
out["languages_served_per_work"] = {
    "median": sorted(sum(1 for p in prb.get(c, {}).values() if served(p))
                     for c in works)[len(works) // 2],
    "works_with_zero_served": sum(
        1 for c in works if not any(served(p) for p in prb.get(c, {}).values())),
}
lang_served = collections.Counter(
    l for c in works for l, p in prb.get(c, {}).items() if served(p))
out["served_by_language"] = dict(lang_served.most_common())
lang_declared_digital = collections.Counter(
    l for c in works for l, t in cat[c].items() if digital(t))
out["catalogue_digital_by_language"] = dict(lang_declared_digital.most_common())

# —— post-hoc, not pre-registered and not scored: what the two instruments agree on
HTMLISH = {"html", "xhtml"}
listed_html = {(c, l) for c in works for l, t in cat[c].items() if set(t) & HTMLISH}
served_pairs = {(c, l) for c in works for l, p in prb.get(c, {}).items() if served(p)}
out["post_hoc"] = {
    "note": "descriptive; not pre-registered, not scored",
    "pairs_listing_html_or_xhtml": len(listed_html),
    "pairs_served": len(served_pairs),
    "served_but_not_listed_html": sorted(f"{c}/{l}" for c, l in served_pairs - listed_html),
    "listed_html_but_not_served": sorted(f"{c}/{l}" for c, l in listed_html - served_pairs),
    "works_with_a_founding_four_digital": sum(
        1 for c in works if any(l in {"NLD", "FRA", "DEU", "ITA"} and digital(t)
                                for l, t in cat[c].items())),
    "works_with_a_post_english_accession_digital": sum(
        1 for c in works if any(l in {"ELL", "SPA", "POR", "FIN", "SWE"} and digital(t)
                                for l, t in cat[c].items())),
    "eng_listing_shapes": {
        "print_only": sum(1 for c in works if cat[c].get("ENG") == ["print"]),
        "empty": sum(1 for c in works if cat[c].get("ENG") == []),
    },
}

# —— known-answer test (§5)
ka = "31989R3540R(01)"
out["known_answer"] = {
    "celex": ka,
    "catalogue": cat.get(ka),
    "eng": prb.get(ka, {}).get("ENG"),
    "fra": prb.get(ka, {}).get("FRA"),
    "deu": prb.get(ka, {}).get("DEU"),
}

(HERE / "measurement.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
print(json.dumps(out, indent=1, ensure_ascii=False))
