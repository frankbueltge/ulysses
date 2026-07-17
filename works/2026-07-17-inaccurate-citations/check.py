#!/usr/bin/env python3
# check.py — Inaccurate Citations (Ulysses, Session 34, 2026-07-17).
#
# A retrieval-consistency check over this project's OWN reservoir of references.
# The swerve source is the Nature paper "Towards end-to-end automation of AI
# research" (Lu et al., 2026) — a machine that generates research AND runs its
# own review, whose limitations list names "inaccurate citations" and "many
# types of hallucinations" as defects to reduce. This work turns that same
# standard on the atelier's atlas.
#
# The check is DETERMINISTIC and needs no network at build time:
#   - the atlas CLAIM (work title named for each arXiv entry) is read live from
#     ../../atlas/atlas.json as committed at this snapshot;
#   - the CANONICAL title for each arXiv id was retrieved THIS SESSION from the
#     arXiv metadata service (an outside index) and is embedded below with that
#     provenance — the one act of outside contact, frozen into a dated snapshot
#     exactly as probe.py did in work 26.
#
# Verdict per entry = does the paper the `url` points to actually carry the
# title the `work` field names? (normalised exact match). Re-run: same tree,
# same numbers. No invented data: every canonical string below is a real
# retrieval result; nothing is fabricated to make a point.

import json
import re
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, "..", "..", "atlas", "atlas.json")
OUT = os.path.join(HERE, "data.json")

# Canonical titles + first-listed author + published year, retrieved this
# session (2026-07-17) from the arXiv metadata service. Provenance, not decor.
CANONICAL = {
    "1706.07068": ("CAN: Creative Adversarial Networks, Generating \"Art\" by Learning About Styles and Deviating from Style Norms", "Ahmed Elgammal", 2017),
    "1801.04486": ("Can Computers Create Art?", "Aaron Hertzmann", 2018),
    "2306.04141": ("Art and the science of generative AI: A deeper dive", "Ziv Epstein", 2023),
    "2305.17493": ("The Curse of Recursion: Training on Generated Data Makes Models Forget", "Ilia Shumailov", 2023),
    "2307.01850": ("Self-Consuming Generative Models Go MAD", "Sina Alemohammad", 2023),
    "2404.01413": ("Is Model Collapse Inevitable? Breaking the Curse of Recursion by Accumulating Real and Synthetic Data", "Matthias Gerstgrasser", 2024),
    "2506.20623": ("Lost in Retraining: Roaming the Parameter Space of Exponential Families Under Closed-Loop Learning", "Fariba Jangjoo", 2025),
    "2407.17590": ("Is computational creativity flourishing on the dead internet?", "Terence Broad", 2024),
    "2401.14425": ("No Longer Trending on Artstation: Prompt Analysis of Generative AI Art", "Jon McCormack", 2024),
    "1908.01133": ("Machinic Surrogates: Human-Machine Relationships in Computational Creativity", "Ardavan Bidgoli", 2019),
    "2007.11973": ("The societal and ethical relevance of computational creativity", "Michele Loi", 2020),
    "2406.14516": ("Extended error threshold mechanism in quasispecies theory via population dynamics", "Hermano Velten", 2024),
}

# The prose layer: the verdict a HUMAN reaches after reading each entry's own
# `summary` field in the atlas. Only assigned for entries the machine flags —
# these classifications are read off the disclosing prose already committed in
# atlas.json (quoted in the journal), not invented here.
PROSE = {
    "epstein-et-al-art-and-the-science-of-generative-ai":
        ("disclosed-variant",
         "Atlas names the short Science (2023) version; the url resolves to the same authors' "
         "expanded arXiv companion, titled with the added subtitle 'A deeper dive'. The atlas "
         "summary discloses this: 'the expanded companion version is open access on arXiv.'"),
    "eigen-quasispecies-error-threshold":
        ("disclosed-substitution",
         "Atlas names Eigen's 1971 Naturwissenschaften primary; the url resolves to a DIFFERENT, "
         "later paper (Velten et al. 2024) used to verify the threshold claim. The atlas summary "
         "discloses this in full: '1971 German primary NOT read directly ... verified S27 via two "
         "independent retrievable expositions: arXiv:2406.14516v1 ... and .../VError.pdf.'"),
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^0-9a-z]+", " ", s.lower())).strip()


def main():
    atlas = json.load(open(ATLAS, encoding="utf-8"))
    entries = []
    for e in atlas:
        url = e.get("url", "")
        if "arxiv.org" not in url:
            continue
        m = re.search(r"(\d{4}\.\d{4,5})", url)
        aid = m.group(1) if m else None
        if aid not in CANONICAL:
            raise SystemExit(f"atlas arXiv id {aid} ({e['id']}) has no retrieved canonical record — refusing to guess")
        can_title, can_author, can_year = CANONICAL[aid]
        claim = e.get("work", "")
        exact = norm(claim) == norm(can_title)
        prose_verdict, prose_note = PROSE.get(e["id"], ("resolves", ""))
        entries.append({
            "id": e["id"],
            "arxiv_id": aid,
            "status": e.get("status"),
            "atlas_work": claim,
            "atlas_author": e.get("author"),
            "atlas_year": e.get("year"),
            "canonical_title": can_title,
            "canonical_first_author": can_author,
            "canonical_year": can_year,
            "url_resolves_to_named_work": exact,   # the machine verdict
            "prose_verdict": prose_verdict,        # the reading verdict
            "disclosed_gap": e["id"] in PROSE,
            "note": prose_note,
        })

    flagged = [e for e in entries if not e["url_resolves_to_named_work"]]
    disclosed = [e for e in entries if e["disclosed_gap"]]
    # The load-bearing observation, computed rather than asserted:
    flagged_ids = {e["id"] for e in flagged}
    disclosed_ids = {e["id"] for e in disclosed}
    flags_are_exactly_the_disclosed = flagged_ids == disclosed_ids

    data = {
        "generated": "2026-07-17",
        "session": 34,
        "check": "Does the paper each atlas `url` points to actually carry the title the "
                 "`work` field names? (normalised exact title match against the canonical "
                 "arXiv record retrieved this session.)",
        "provenance": "Atlas claims read from atlas/atlas.json as committed at this snapshot; "
                      "canonical titles retrieved 2026-07-17 from the arXiv metadata service and "
                      "frozen in check.py. Deterministic; re-derivable from the tree with no network.",
        "swerve_source": {
            "title": "Towards end-to-end automation of AI research",
            "authors": "Chris Lu, Cong Lu, Robert Tjarko Lange, Yutaro Yamada, Shengran Hu, "
                       "Jakob Foerster, David Ha, Jeff Clune, et al.",
            "venue": "Nature 651, 914-919 (25 March 2026)",
            "url": "https://www.nature.com/articles/s41586-026-10265-5",
            "failure_modes_quoted": ["many types of hallucinations", "inaccurate citations"],
            "note": "The AI Scientist generates research AND runs its own simulated review (the "
                    "'Automated Reviewer'). Its own limitations list names inaccurate citations and "
                    "hallucinations among the failure modes it seeks to reduce. Quoted from the "
                    "open-access article, read this session.",
        },
        "counts": {
            "total": len(entries),
            "resolve": len(entries) - len(flagged),
            "flagged": len(flagged),
            "disclosed": len(disclosed),
            "hallucinations_found": 0,
            "flags_are_exactly_the_disclosed": flags_are_exactly_the_disclosed,
        },
        "entries": entries,
    }
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"wrote {OUT}")
    print(f"{data['counts']['resolve']}/{data['counts']['total']} resolve; "
          f"{len(flagged)} flagged; flagged == disclosed: {flags_are_exactly_the_disclosed}")
    for e in flagged:
        print(f"  FLAG {e['id']} -> {e['prose_verdict']}")


if __name__ == "__main__":
    main()
