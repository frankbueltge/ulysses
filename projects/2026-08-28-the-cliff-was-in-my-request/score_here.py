#!/usr/bin/env python3
"""Score tonight's clauses. A1 and A2 from manifest.json and pairs.json; H1'–H4' by the
2026-08-25 scorer's own arithmetic, at the floors committed that night, with tonight's
N/M floors from PREREGISTRATION.md §3. Prints only; verdicts are written into DECISION.md.
"""
import json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
man = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
pairs = json.loads((HERE / "pairs.json").read_text(encoding="utf-8"))
m = json.loads((HERE / "measurement.json").read_text(encoding="utf-8"))
rows = m["rows"]
N = len(rows)
FLOOR_N, FLOOR_M = 40, 25

def line(name, got, op, bound, void, extra=""):
    if void:
        return f"{name}  VOID   (floor not met) {extra}"
    held = got >= bound if op == ">=" else got < bound
    return f"{name}  {'HELD  ' if held else 'FAILED'} {got:6.1%}  {op} {bound:.0%}   {extra}"

# ---- A1 ------------------------------------------------------------------------------
tot = man["count"]; served = man["served_200"]
print(line("A1  the refusal was the header ", served / tot, ">=", 0.90, False,
           f"{served}/{tot}"))
# ---- A2 ------------------------------------------------------------------------------
wp = pairs["with_at_least_one_pair"]; sv = pairs["served"]
print(line("A2  documents, not stubs       ", wp / sv, ">=", 0.60, False,
           f"{wp}/{sv}   (comparison 1894/2569 = 73.7%)"))
print()
# ---- H1'-H4' -------------------------------------------------------------------------
live = [r for r in rows if r["wrong_pointer_is_live"]]
acts = [t for r in rows for t in r["corrected_act"] if t["readable"]]
M = len(acts)
still = [t for t in acts if t["still_names_wrong"]]
oper = [r for r in rows if r["in_enacting_terms"]]
both = [r for r in rows if r["wrong_pointer_is_live"]
        and any(t["readable"] and t["still_names_wrong"] for t in r["corrected_act"])]
print(f"N (selected reference corrections) = {N}   floor {FLOOR_N}")
print(f"M (readable corrected acts)        = {M}   floor {FLOOR_M}\n")
print(line("H1' wrong pointer is live      ", len(live)/N, ">=", 0.60, N < FLOOR_N, f"{len(live)}/{N}   (2026-08-25: 91.6%)"))
print(line("H2' the fix does not travel    ", (len(still)/M if M else 0), ">=", 0.90, M < FLOOR_M, f"{len(still)}/{M}   (2026-08-25: 94.3%)"))
print(line("H3' error mostly not operative ", len(oper)/N, "<", 0.25, N < FLOOR_N, f"{len(oper)}/{N}   (2026-08-25: 28.0%, FAILED)"))
print(line("H4' silent and live together   ", len(both)/N, ">=", 0.30, N < FLOOR_N, f"{len(both)}/{N}   (2026-08-25: 86.7%)"))
# ---- routes that answered ------------------------------------------------------------
import collections
print("\nroute that answered for the corrected acts:",
      dict(collections.Counter(t.get("route") for t in acts)))
unread = [t for r in rows for t in r["corrected_act"] if not t["readable"]]
print("unreadable corrected acts:", len(unread),
      dict(collections.Counter(t.get("http_status") for t in unread)))
# ---- dead pointers -------------------------------------------------------------------
dead = [r for r in rows if not r["wrong_pointer_is_live"]]
print(f"\ndead wrong pointers ({len(dead)}):")
for r in dead:
    print(f"  {r['corrigendum']:22s} {r['date']}  {r['wrong_number']}")
sharp = [r for r in both if r["in_enacting_terms"]]
print(f"\nlive + still uncorrected + in the enacting terms: {len(sharp)}/{N}")
for r in sharp[:12]:
    print(f"  {r['corrigendum']:22s} {r['date']}  {r['wrong_number']:>10s} -> {','.join(r['wrong_resolves_to'][:3])}")
