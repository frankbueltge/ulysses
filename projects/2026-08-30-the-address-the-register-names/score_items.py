#!/usr/bin/env python3
"""Scoring — the five clauses of `PREREGISTRATION.md` §3, and nothing beyond them.

Reads `addresses.json` and `items.json`, writes `measurement.json`. Void rules are applied
before any clause is scored; a void clause is reported void, not discounted.
"""

import collections
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PDF_TYPES = {"pdf", "pdfa1b", "pdfa2a"}


def main() -> None:
    addr = json.loads((HERE / "addresses.json").read_text())
    items = json.loads((HERE / "items.json").read_text())["records"]
    shapes = addr["shape_from_committed_file"]
    mans = addr["manifestations"]

    group_a = sorted(c for c in mans if shapes[c] not in ("print", "(none)"))
    group_b = sorted(c for c in mans if shapes[c] in ("print", "(none)"))

    present = [r for r in items if r["present"]]
    pdfs = [r for r in present if r["type"] in PDF_TYPES]

    # --- void rules (§3) -------------------------------------------------------------
    hashes = collections.Counter(r["no_accept"]["sha256"] for r in present)
    top_share = (hashes.most_common(1)[0][1] / len(present)) if present else 0.0
    fallback_void = top_share >= 0.20
    bound_a = sum(1 for c in group_a if mans[c])
    binding_void = bound_a < 150
    c1_void = fallback_void or len(pdfs) < 50

    # --- C1 : machine-readable, not only fetchable -----------------------------------
    readable = [r for r in pdfs if r.get("readability", {}).get("readable")]
    c1 = len(readable) / len(pdfs) if pdfs else 0.0

    # --- C2 : the file is at the address ---------------------------------------------
    a_items = [r for r in items if shapes[r["celex"]] not in ("print", "(none)")]
    c2 = len([r for r in a_items if r["present"]]) / len(a_items) if a_items else 0.0

    # --- C3 : the refusal is structural ----------------------------------------------
    def refusal(mtype: str) -> tuple[int, int]:
        sel = [r for r in present if r["type"] == mtype]
        return sum(1 for r in sel if r["typed_accept"]["http_status"] != 200), len(sel)

    ref_a1b, n_a1b = refusal("pdfa1b")
    ref_pdf, n_pdf = refusal("pdf")
    c3_a1b = ref_a1b / n_a1b if n_a1b else 0.0
    c3_pdf = ref_pdf / n_pdf if n_pdf else 0.0

    # --- C4 : the control -------------------------------------------------------------
    b_with_item = [c for c in group_b
                   if any(r["items"] for r in mans[c].values())]
    c4 = len(b_with_item) / len(group_b) if group_b else 0.0

    # --- C5 : the corrected figure -----------------------------------------------------
    a_reached = sorted({r["celex"] for r in present})
    still_unreachable = len(group_a) + len(group_b) - len(a_reached)

    def verdict(ok: bool, void: bool) -> str:
        return "VOID" if void else ("HELD" if ok else "FAILED")

    out = {
        "measured_utc": items and json.loads((HERE / "items.json").read_text())["measured_utc"],
        "population": {"works": len(mans), "group_a": len(group_a), "group_b": len(group_b),
                       "item_uris": len(items)},
        "void_rules": {
            "largest_sha256_share_of_present": round(top_share, 4),
            "fallback_rule_fired": fallback_void,
            "group_a_works_with_binding": bound_a,
            "binding_rule_fired": binding_void,
            "present_pdfs": len(pdfs),
        },
        "clauses": {
            "C1_readable": {"floor": ">= 0.60", "measured": round(c1, 4),
                            "n": f"{len(readable)}/{len(pdfs)}",
                            "verdict": verdict(c1 >= 0.60, c1_void)},
            "C2_present": {"floor": ">= 0.85", "measured": round(c2, 4),
                           "n": f"{len([r for r in a_items if r['present']])}/{len(a_items)}",
                           "verdict": verdict(c2 >= 0.85, fallback_void or binding_void)},
            "C3_refusal": {"floor": "pdfa1b >= 0.80 and pdf <= 0.20",
                           "measured": {"pdfa1b": round(c3_a1b, 4), "pdf": round(c3_pdf, 4)},
                           "n": {"pdfa1b": f"{ref_a1b}/{n_a1b}", "pdf": f"{ref_pdf}/{n_pdf}"},
                           "verdict": verdict(c3_a1b >= 0.80 and c3_pdf <= 0.20,
                                              fallback_void or binding_void)},
            "C4_control": {"floor": "<= 0.05", "measured": round(c4, 4),
                           "n": f"{len(b_with_item)}/{len(group_b)}",
                           "verdict": verdict(c4 <= 0.05, False)},
            "C5_corrected_figure": {"floor": "in [196, 230]", "measured": still_unreachable,
                                    "published_2026_08_28": 372,
                                    "verdict": verdict(196 <= still_unreachable <= 230,
                                                       fallback_void or binding_void)},
        },
        "reproduction_check_not_a_clause": {
            "item_counts_in_committed_file": dict(collections.Counter(
                t.split(":")[0]
                for c in mans
                for t in json.loads((HERE.parent / "2026-08-28-the-cliff-was-in-my-request"
                                     / "unserved.json").read_text())["detail_unserved"][c]
                if int(t.split(":")[1]) > 0)),
            "item_uris_found_tonight": dict(collections.Counter(
                r["type"] for r in items)),
        },
        "descriptive_not_scored": {
            "typed_accept_status_by_type": {
                t: dict(collections.Counter(str(r["typed_accept"]["http_status"])
                                            for r in present if r["type"] == t))
                for t in sorted({r["type"] for r in present})},
            "content_type_by_type": {
                t: dict(collections.Counter(str(r["no_accept"]["content_type"])
                                            for r in present if r["type"] == t))
                for t in sorted({r["type"] for r in present})},
            "bytes_median_by_type": {
                t: sorted(r["no_accept"]["bytes"] for r in present if r["type"] == t)[
                    len([r for r in present if r["type"] == t]) // 2]
                for t in sorted({r["type"] for r in present})},
            "pdfs_with_font": sum(1 for r in pdfs if r["readability"]["has_font"]),
            "pdfs_with_image": sum(1 for r in pdfs if r["readability"]["has_image"]),
            "pdfs_chars_zero": sum(1 for r in pdfs if r["readability"]["chars"] == 0),
            "distinct_sha256_of_present": len(hashes),
        },
        "hand_check_sample": [r["celex"] for r in sorted(
            pdfs, key=lambda r: r["no_accept"]["sha256"])[:20]],
    }
    (HERE / "measurement.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(out["clauses"], indent=1, ensure_ascii=False))
    print(json.dumps(out["void_rules"], indent=1))
    print(json.dumps(out["descriptive_not_scored"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
