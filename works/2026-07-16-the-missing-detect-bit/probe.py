#!/usr/bin/env python3
"""
The missing detect-bit — measurement.

Runs two query batteries against the project's own recall index (the memory
tool, tools/memory) and records, for each query: what plain BM25 recall returns
as its top "memory," and what the detect-bit (tools/memory/refusal.py) does —
answer or refuse.

  GENUINE : subjects the corpus genuinely covers.
  DECOY   : subjects the corpus does NOT cover (other domains, everyday life).

The point is not that BM25 is bad — it ranks lexical overlap, exactly as
designed. The point is that plain recall has no *representable limit*: for a
DECOY it still returns a confident, mid-range top hit (cli.py only drops an
exact 0.0), and a caller reading the #1 as "the relevant memory" is handed a
stranger's chunk. The detect-bit converts the clearest phantom class into a
flagged refusal — and, measured honestly here, lets a residual class slip: a
decoy carried by a real but unrelated corpus word.

Deterministic: the query lists are fixed, BM25 is deterministic, no RNG. Same
corpus + same queries -> same data.json. Run from the repo root:
    python3 works/2026-07-16-the-missing-detect-bit/probe.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "memory"))

from store import build_index  # noqa: E402
from refusal import recall_with_refusal, content_terms  # noqa: E402

COMMON_DF_FRAC = 0.05  # a term in >5% of chunks counts as common (see refusal.py)

GENUINE = [
    "model collapse recursive training",
    "hamming distance error correction",
    "negative knowledge honest refusal",
    "parry eliza conversation transcript",
    "benford law digit anomaly",
    "clinamen swerve outside element",
    "differential reproduction quasispecies error threshold",
    "generation loss repeated compression",
    "order from noise von foerster",
    "silent miscorrection undetected error rate",
]

DECOY = [
    "how to cook rice for dinner",
    "what is the best programming language",
    "please tell me tomorrow's weather forecast",
    "how do i change a car tyre",
    "recipe for chocolate birthday cake",
    "entropy black hole thermodynamics",   # incidental corpus words: entropy/black/hole
    "glacier ice sheet melt rate",         # incidental corpus word: sheet
    "football league match final score",
    "mortgage interest rate calculation",
    "train timetable platform departure",
]


def run_battery(index, queries):
    rows = []
    for q in queries:
        out = recall_with_refusal(index, q, k=3, common_df_frac=COMMON_DF_FRAC)
        diag = out.get("diagnostic", {})
        # Plain recall's top hit (what a caller sees today, refusal aside).
        if out["refused"]:
            top = None
            # recall_with_refusal already computed the ranked list internally only
            # when overlap existed; for the display we re-derive the top if any.
            from store import recall as _recall
            plain = [r for r in _recall(index, q, k=1) if r["score"] > 0.0]
            top = plain[0] if plain else None
        else:
            top = out["results"][0]
        rows.append({
            "query": q,
            "refused": out["refused"],
            "reason": out.get("reason"),
            "content_terms_in_query": diag.get("content_terms_in_query", content_terms(q, index, COMMON_DF_FRAC)),
            "content_overlap": diag.get("content_overlap"),
            "content_subscore": round(diag.get("content_subscore", 0.0), 3),
            "full_score": round(diag.get("full_score", 0.0), 3),
            "top_path": top["path"] if top else None,
            "top_heading": top["heading"] if top else None,
            "top_score": round(top["score"], 3) if top else None,
        })
    return rows


def main():
    index_path = REPO / "memory" / "index.jsonl"
    if not index_path.exists():
        sys.stderr.write("index missing; run: python3 tools/memory/cli.py index .\n")
        sys.exit(1)
    chunks = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    index = build_index(chunks)

    genuine_rows = run_battery(index, GENUINE)
    decoy_rows = run_battery(index, DECOY)

    genuine_refused = [r for r in genuine_rows if r["refused"]]
    decoy_refused = [r for r in decoy_rows if r["refused"]]
    decoy_slipped = [r for r in decoy_rows if not r["refused"]]

    data = {
        "generated_from": "works/2026-07-16-the-missing-detect-bit/probe.py",
        "corpus_chunks": len(chunks),
        "common_df_frac": COMMON_DF_FRAC,
        "note": (
            "Deterministic measurement over the project's own recall index. BM25 is "
            "not faulty; it has no representable 'beyond me'. The detect-bit adds one."
        ),
        "summary": {
            "genuine_total": len(genuine_rows),
            "genuine_falsely_refused": len(genuine_refused),
            "decoy_total": len(decoy_rows),
            "decoy_caught": len(decoy_refused),
            "decoy_slipped": len(decoy_slipped),
        },
        "genuine": genuine_rows,
        "decoy": decoy_rows,
        "slipped_detail": [
            {"query": r["query"], "carried_by": r["content_terms_in_query"],
             "top_heading": r["top_heading"], "top_path": r["top_path"], "top_score": r["top_score"]}
            for r in decoy_slipped
        ],
    }

    out_path = Path(__file__).resolve().parent / "data.json"
    out_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    s = data["summary"]
    print(f"genuine: {s['genuine_falsely_refused']}/{s['genuine_total']} falsely refused")
    print(f"decoy:   {s['decoy_caught']}/{s['decoy_total']} caught, {s['decoy_slipped']} slipped")
    for r in decoy_slipped:
        print(f"  SLIP: {r['query']!r} carried by {r['content_terms_in_query']} -> {r['top_heading']!r} ({r['top_score']})")
    print(f"wrote {out_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
