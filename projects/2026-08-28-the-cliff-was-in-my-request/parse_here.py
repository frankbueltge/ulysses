#!/usr/bin/env python3
"""Parse tonight's corpus with the 2026-08-25 reader, unchanged, and run the hinge test
§5.1–5.4 of PREREGISTRATION.md demands *before* any clause is scored.

`triples`, `tokens` and `to_text` are imported from
`../2026-08-25-the-pointer-that-resolves/parse_pairs.py`. Nothing in that file is edited or
copied: the same reader runs on both serialisations, which is the only way the comparison
means anything.

The comparison corpus is a fixed stride sample of the works the first route served — sorted
by (date, celex), every 8th — chosen by that rule alone, before any parsing, and re-fetched
tonight under the original `Accept: application/xhtml+xml`. Its purpose is one thing: to say
whether the capture defects counted on the old serialisation are unusual.

Standard library only.
"""

import hashlib
import json
import pathlib
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
PRIOR_DIR = HERE.parent / "2026-08-25-the-pointer-that-resolves"
sys.path.insert(0, str(PRIOR_DIR))
from parse_pairs import to_text, triples, tokens  # noqa: E402  the same reader, both sides

CORPUS = HERE / "corpus"
SAMPLE = HERE / "sample_xhtml"
CELLAR = "http://publications.europa.eu/resource/celex/"
UA = "Ulysses research (artistic research on how warrants travel); contact via repository"
STRIDE = 8


def capture_stats(values: list[str]) -> dict:
    """§5.1–5.2: what the capture did, counted, not inspected."""
    n = len(values)
    return {
        "captures": n,
        "empty": sum(1 for v in values if not v.strip()),
        "contains_double_slash": sum(1 for v in values if "//" in v),
        "contains_entity": sum(1 for v in values if "&#" in v),
        "over_400_chars": sum(1 for v in values if len(v) > 400),
        "median_len": sorted(len(v) for v in values)[n // 2] if n else 0,
    }


def parse_dir(paths: list[tuple[str, pathlib.Path]]) -> tuple[list[dict], list[str]]:
    out, values = [], []
    for celex, path in paths:
        text = to_text(path.read_text(encoding="utf-8", errors="replace"))
        pairs = []
        for t in triples(text):
            f, r = t["for"], t["read"]
            values.extend([f, r])
            tf, tr = tokens(f), tokens(r)
            wrong = sorted(tf - tr)
            pairs.append({
                "locus": t["locus"], "for": f[:400], "read": r[:400],
                "for_len": len(f), "read_len": len(r),
                "for_tokens": sorted(tf), "read_tokens": sorted(tr),
                "reference_correction": bool(wrong), "erroneous_tokens": wrong,
            })
        out.append({"celex": celex, "pair_count": len(pairs), "pairs": pairs})
    return out, values


def fetch_sample(celexes: list[str]) -> None:
    SAMPLE.mkdir(exist_ok=True)
    for celex in celexes:
        dest = SAMPLE / (urllib.parse.quote(celex, safe="") + ".xhtml")
        if dest.exists():
            continue
        req = urllib.request.Request(
            CELLAR + urllib.parse.quote(celex, safe=""),
            headers={"Accept": "application/xhtml+xml", "Accept-Language": "eng",
                     "User-Agent": UA},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as fh:
                dest.write_bytes(fh.read())
        except Exception as exc:  # noqa: BLE001
            print(f"  sample {celex}: {type(exc).__name__}", flush=True)


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    served = [r for r in manifest["records"] if r["http_status"] == 200]

    # ——— the known-answer test for the route (§6.3) ———
    known = next(r for r in served if r["celex"] == "31989R3755R(01)")
    body = (CORPUS / (urllib.parse.quote(known["celex"], safe="") + ".html")).read_bytes()
    assert hashlib.sha256(body).hexdigest() == known["sha256"], "known-answer: hash moved"
    kpairs = triples(to_text(body.decode("utf-8", "replace")))
    assert len(kpairs) == 1 and kpairs[0]["for"] == "0502 21 00" \
        and kpairs[0]["read"] == "0802 21 00", f"known-answer: parse moved: {kpairs}"
    print("known-answer test (route + parse on 31989R3755R(01)): PASS")

    paths = [(r["celex"], CORPUS / (urllib.parse.quote(r["celex"], safe="") + ".html"))
             for r in served]
    records, values = parse_dir(paths)
    by_celex = {r["celex"]: r for r in records}
    for r in served:
        r.update({k: by_celex[r["celex"]][k] for k in ("pair_count", "pairs")})

    # ——— the comparison sample, by a rule fixed before parsing ———
    prior = json.loads((PRIOR_DIR / "manifest.json").read_text(encoding="utf-8"))
    prior_served = sorted((r for r in prior["corrigenda"] if r["http_status"] == 200),
                          key=lambda r: (r["date"], r["celex"]))
    sample_celex = [r["celex"] for r in prior_served[::STRIDE]]
    print(f"comparison sample: every {STRIDE}th of {len(prior_served)} = {len(sample_celex)}")
    fetch_sample(sample_celex)
    spaths = [(c, SAMPLE / (urllib.parse.quote(c, safe="") + ".xhtml")) for c in sample_celex]
    spaths = [(c, p) for c, p in spaths if p.exists()]
    _, svalues = parse_dir(spaths)

    # ——— §5.4: the two-digit year ———
    years = [int(y) for r in served for p in r["pairs"]
             for y, _ in (p["for_tokens"] + p["read_tokens"])]
    out_of_range = sum(1 for y in years if not 1950 <= y <= 2030)

    with_pair = sum(1 for r in served if r["pair_count"])
    result = {
        "served": len(served),
        "with_at_least_one_pair": with_pair,
        "A2_rate": round(100 * with_pair / len(served), 1),
        "pair_total": sum(r["pair_count"] for r in served),
        "reference_correction_pairs": sum(1 for r in served for p in r["pairs"]
                                          if p["reference_correction"]),
        "reference_correction_rows": sum(len(p["erroneous_tokens"]) for r in served
                                         for p in r["pairs"] if p["reference_correction"]),
        "reference_correction_corrigenda": sum(1 for r in served
                                               if any(p["reference_correction"] for p in r["pairs"])),
        "hinge_this_corpus": capture_stats(values),
        "hinge_comparison_sample": {"documents": len(spaths), **capture_stats(svalues)},
        "normalised_years_outside_1950_2030": out_of_range,
        "records": served,
    }
    (HERE / "pairs.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    for k, v in result.items():
        if k != "records":
            print(f"{k:38} {v}")


if __name__ == "__main__":
    main()
