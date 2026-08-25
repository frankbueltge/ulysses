#!/usr/bin/env python3
"""Score the four pre-registered clauses against measurement.json, and run the
known-answer test. Prints only; the verdicts are written into DECISION.md by hand."""

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
m = json.loads((HERE / "measurement.json").read_text(encoding="utf-8"))
rows = m["rows"]
N = len(rows)

FLOOR_N, FLOOR_M = 60, 40


def verdict(name: str, got: float, op: str, bound: float, void: bool) -> str:
    if void:
        return f"{name}  VOID   (floor not met)"
    held = got >= bound if op == ">=" else got < bound
    return f"{name}  {'HELD  ' if held else 'FAILED'} {got:6.1%}  {op} {bound:.0%}"


# ---- H1 ------------------------------------------------------------------------------
live = [r for r in rows if r["wrong_pointer_is_live"]]
h1 = len(live) / N

# ---- H2 ------------------------------------------------------------------------------
acts = [t for r in rows for t in r["corrected_act"] if t["readable"]]
M = len(acts)
still = [t for t in acts if t["still_names_wrong"]]
h2 = len(still) / M if M else 0.0

# ---- H3 ------------------------------------------------------------------------------
oper = [r for r in rows if r["in_enacting_terms"]]
h3 = len(oper) / N

# ---- H4 : live AND the act still names it --------------------------------------------
both = [
    r for r in rows
    if r["wrong_pointer_is_live"]
    and any(t["readable"] and t["still_names_wrong"] for t in r["corrected_act"])
]
h4 = len(both) / N

print(f"N (selected reference corrections) = {N}   floor {FLOOR_N}")
print(f"M (readable corrected acts)        = {M}   floor {FLOOR_M}\n")
print(verdict("H1  wrong pointer is live      ", h1, ">=", 0.60, N < FLOOR_N),
      f"   {len(live)}/{N}")
print(verdict("H2  the fix does not travel    ", h2, ">=", 0.90, M < FLOOR_M),
      f"   {len(still)}/{M}")
print(verdict("H3  error mostly not operative ", h3, "<", 0.25, N < FLOOR_N),
      f"   {len(oper)}/{N}")
print(verdict("H4  silent and live together   ", h4, ">=", 0.30, N < FLOOR_N),
      f"   {len(both)}/{N}")

# ---- known-answer test ---------------------------------------------------------------
print("\nknown-answer test — the case hand-verified 2026-08-24:")
hits = [r for r in rows if r["corrigendum"] == "32020D1146R(01)"]
if not hits:
    print("  NOT IN THE SELECTED SET — the pipeline disagrees with the hand reading")
for r in hits:
    ok = r["wrong_number"] == "2020/1956" and "32020B1956" in r["wrong_resolves_to"]
    print(f"  wrong={r['wrong_number']}  resolves_to={r['wrong_resolves_to']}  "
          f"enacting={r['in_enacting_terms']}  -> {'PASS' if ok else 'FAIL'}")
    for t in r["corrected_act"]:
        print(f"  corrected act {t['act']}: readable={t['readable']} "
              f"still_names_wrong={t.get('still_names_wrong')}")

# ---- what the dead ones are, for the record ------------------------------------------
dead = [r for r in rows if not r["wrong_pointer_is_live"]]
print(f"\ndead wrong pointers ({len(dead)}):")
for r in dead:
    print(f"  {r['corrigendum']:22s} {r['wrong_number']}")

# ---- the sharpest subset: live, uncorrected, and in the enacting terms ----------------
sharp = [r for r in both if r["in_enacting_terms"]]
print(f"\nlive + still uncorrected + in the enacting terms: {len(sharp)}/{N}")
for r in sharp[:40]:
    print(f"  {r['corrigendum']:22s} {r['date']}  {r['wrong_number']:>10s} "
          f"-> {','.join(r['wrong_resolves_to'][:3])}")
