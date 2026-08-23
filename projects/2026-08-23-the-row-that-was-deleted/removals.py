"""The numbered removal — census of how the Official Journal takes a standard off a list.

Executes PREREGISTRATION.md §4 on the 68 held-out amending acts. The 23 development acts are
counted separately and are not clause evidence.

No network call. The corpus is the one fetched and hashed on 2026-08-21; every file's sha256 is
verified before anything is counted (D-1). The standard-reference pattern is imported from that
night's census.py, never re-typed (D-3).
"""
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "2026-08-21-the-citation-that-stopped"
sys.path.insert(0, str(SRC))
from census import REF_RE, text_of  # noqa: E402  — D-3: imported, not re-typed

sys.path.insert(0, str(HERE))
from split import load, split, act_kind  # noqa: E402

# ————————————————————————————————————————————————————— the removal instruction —
# Defined by the operative verb and a NUMBERED object (§3). Never by the absence of a
# reference — that would make W2 true by construction (§5.1).
REMOVAL_RE = re.compile(
    r"\b(rows?|entry|entries)\s+"
    r"((?:\d+[a-z]?)(?:\s*(?:,|and)\s*\d+[a-z]?)*)\s+"
    r"(?:is|are)\s+"
    r"(deleted|removed|replaced by)",
    re.IGNORECASE,
)

# ——————————————————————————————————————————————————————————— POST-HOC, 2026-08-23 —
# Found by §7's no-silent-caps check AFTER the pre-registered run: the pattern above misses
# the form "entry No 18 is deleted" (an optional "No" between the noun and the number) and
# the separator ", and" in "rows 139, 198, 221, 299a, and 517 are deleted". 12 instructions
# in 8 held-out acts, all of them number-only. Every figure derived from this pattern is
# labelled `repaired_post_hoc` and is NOT the scored result — the pre-registered figures are.
# See DECISION.md; this is not retro-fitted into PREREGISTRATION.md.
REMOVAL_RE_REPAIRED = re.compile(
    r"\b(rows?|entry|entries)\s+(?:No\.?\s+)?"
    r"((?:\d+[a-z]?)(?:\s*(?:,\s*and|,|and)\s*\d+[a-z]?)*)\s+"
    r"(?:is|are)\s+"
    r"(deleted|removed|replaced by)",
    re.IGNORECASE,
)

# Where an instruction's span ends: the next list marker, or the next operative verb.
BOUNDARY_RE = re.compile(
    r"\(\s*(?:\d+|[a-z])\s*\)"
    r"|\b(?:is|are)\s+(?:added|inserted|deleted|removed|replaced by)\b",
    re.IGNORECASE,
)

# §5.3 — mechanism (A), the dated withdrawal list, which names what it ends.
DATED_LIST_RE = re.compile(r"Date\s+of\s+withdrawal", re.IGNORECASE)

# §8's "no silent caps": removal language the numbered-object rule does not catch.
LOOSE_REMOVAL_RE = re.compile(r"\b(?:is|are)\s+(?:deleted|removed)\b", re.IGNORECASE)

BASE_RE = re.compile(
    r"(?:Implementing\s+)?Decision\s+\(EU\)\s+(\d{4})/(\d{1,4})\b", re.IGNORECASE
)


def celex_of(year: str, number: str) -> str:
    return f"3{year}D{int(number):04d}"


def base_act(text: str, self_celex: str) -> str:
    """First Decision (EU) cited anywhere in the act that is not the act itself."""
    for m in BASE_RE.finditer(text):
        celex = celex_of(m.group(1), m.group(2))
        if celex != self_celex:
            return celex
    return "UNNAMED"


def spans(text: str, pattern=REMOVAL_RE):
    """Yield one record per removal instruction, span ending at the next boundary."""
    for m in pattern.finditer(text):
        nxt = BOUNDARY_RE.search(text, m.end())
        end = nxt.start() if nxt else len(text)
        span = text[m.start():end]
        verb = m.group(3).lower()
        yield {
            "object": m.group(1).lower(),
            "numbers": m.group(2),
            "verb": verb,
            "kind": "REPLACEMENT" if verb == "replaced by" else "DELETION",
            "span": span,
            "refs": REF_RE.findall(span),
            "number_only": not REF_RE.search(span),
            "at": m.start(),
        }


def read_act(a, corpus: pathlib.Path):
    path = corpus / f"{a['celex']}.html"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != a["sha256"]:
        raise SystemExit(f"D-1 violated: {a['celex']} does not match manifest.json")
    text = text_of(path)
    ins = list(spans(text))
    rep = list(spans(text, REMOVAL_RE_REPAIRED))
    for r in ins + rep:
        r["celex"] = a["celex"]
        r["date"] = a["date"]
    return {
        "celex": a["celex"],
        "date": a["date"],
        "year": a["date"][:4],
        "instructions": ins,
        "instructions_repaired": rep,
        "dated_list": bool(DATED_LIST_RE.search(text)),
        "base": base_act(text, a["celex"]),
        "loose_removal_hits": len(LOOSE_REMOVAL_RE.findall(text)),
    }


def tally(acts, present: set, key: str = "instructions"):
    deletions = [r for a in acts for r in a[key] if r["kind"] == "DELETION"]
    replacements = [r for a in acts for r in a[key] if r["kind"] == "REPLACEMENT"]
    number_only_acts = [
        a for a in acts if any(r["number_only"] for r in a[key])
    ]
    named = [a for a in number_only_acts if a["base"] != "UNNAMED"]
    reachable = [a for a in named if a["base"] in present]
    del_no = [r for r in deletions if r["number_only"]]
    return {
        "acts": len(acts),
        "acts_with_any_instruction": sum(1 for a in acts if a["instructions"]),
        "acts_with_number_only_removal": len(number_only_acts),
        "deletions": len(deletions),
        "deletions_number_only": len(del_no),
        "replacements": len(replacements),
        "replacements_number_only": sum(1 for r in replacements if r["number_only"]),
        "acts_dated_withdrawal_list": sum(1 for a in acts if a["dated_list"]),
        "base_named": len(named),
        "base_unnamed": len(number_only_acts) - len(named),
        "base_present_in_corpus": len(reachable),
        "W1": len(number_only_acts) / len(acts) if acts else None,
        "W2": len(del_no) / len(deletions) if deletions else None,
        "W3": len(named) / len(number_only_acts) if number_only_acts else None,
        "W4": len(reachable) / len(named) if named else None,
    }


def main() -> None:
    man = json.loads((SRC / "manifest.json").read_text())
    all_acts = man["acts"]
    corpus = SRC / "corpus"
    present = {a["celex"] for a in all_acts}

    dev_meta, held_meta = split(all_acts)
    dev = [read_act(a, corpus) for a in dev_meta]
    held = [read_act(a, corpus) for a in held_meta]

    # §5.1 — is W2 disarmed? A removal instruction in dev that DOES carry a reference.
    dev_del_with_ref = [
        {"celex": r["celex"], "numbers": r["numbers"], "refs": r["refs"][:4]}
        for a in dev for r in a["instructions"]
        if r["kind"] == "DELETION" and not r["number_only"]
    ]

    held_instructions = [r for a in held for r in a["instructions"]]
    sample = [
        {
            "i": i,
            "celex": r["celex"],
            "object": r["object"],
            "numbers": r["numbers"],
            "verb": r["verb"],
            "number_only": r["number_only"],
            "span": r["span"][:300],
        }
        for i, r in enumerate(held_instructions)
        if i % 5 == 0
    ]

    out = {
        "corpus": {
            "manifest": str(SRC / "manifest.json"),
            "acts_total": len(all_acts),
            "sha256_verified": len(all_acts),
            "fetched_utc": man.get("fetched_utc"),
            "act_kinds": {
                k: sum(1 for a in all_acts if act_kind(a["title"]) == k)
                for k in ("FULL_LIST", "AMENDING", "CORRIGENDUM", "CORRECTING")
            },
        },
        "split": {"development": len(dev), "held_out": len(held), "rule": "sorted CELEX, i%4==0"},
        "held_out": tally(held, present),
        "development": tally(dev, present),
        "held_out_repaired_post_hoc": tally(held, present, "instructions_repaired"),
        "development_repaired_post_hoc": tally(dev, present, "instructions_repaired"),
        "adversarial_5_1_dev_deletions_carrying_a_reference": dev_del_with_ref,
        "held_out_by_year": {},
        "loose_removal_uncaught": {},
        "hand_verification_sample": sample,
        "unreachable_bases": sorted(
            {a["base"] for a in held
             if any(r["number_only"] for r in a["instructions"])
             and a["base"] != "UNNAMED" and a["base"] not in present}
        ),
    }

    for year in sorted({a["year"] for a in held}):
        ya = [a for a in held if a["year"] == year]
        out["held_out_by_year"][year] = tally(ya, present)

    # every "is/are deleted|removed" the numbered-object rule did not turn into an instruction
    caught = sum(1 for a in held for r in a["instructions"] if r["kind"] == "DELETION")
    loose = sum(a["loose_removal_hits"] for a in held)
    out["loose_removal_uncaught"] = {
        "loose_hits_held_out": loose,
        "instructions_caught": caught,
        "difference": loose - caught,
    }

    (HERE / "removals.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))

    t = out["held_out"]
    print(f"held-out acts {t['acts']}  with a number-only removal {t['acts_with_number_only_removal']}")
    print(f"deletions {t['deletions']}  of them number-only {t['deletions_number_only']}")
    print(f"replacements {t['replacements']}  (excluded from W2 per §5.2)")
    print(f"dated withdrawal lists (mechanism A) {t['acts_dated_withdrawal_list']}")
    print(f"base named {t['base_named']}  unnamed {t['base_unnamed']}  present in corpus {t['base_present_in_corpus']}")
    for k in ("W1", "W2", "W3", "W4"):
        v = t[k]
        print(f"{k} = {v:.4f}" if v is not None else f"{k} = void")
    print("uncaught loose removal language:", out["loose_removal_uncaught"])
    print("dev deletions carrying a reference (§5.1):", len(dev_del_with_ref))
    print("hand-verification sample size:", len(sample))
    r = out["held_out_repaired_post_hoc"]
    print("--- repaired, POST-HOC, not the scored result ---")
    print(f"deletions {r['deletions']} of them number-only {r['deletions_number_only']}"
          f"  acts with a number-only removal {r['acts_with_number_only_removal']}")
    for k in ("W1", "W2", "W3", "W4"):
        v = r[k]
        print(f"{k} = {v:.4f}" if v is not None else f"{k} = void")


if __name__ == "__main__":
    main()
