"""Forty-Two Days, second state — said or carried.

Joins the Field's day classes for the 22 long quiets (check 51, field-research, session 248) to this
page's record, and asserts every figure the new section states.

Usage: python3 -I said.py <path to the Field's data51.js>
Reads data.json (built by build.py), writes said.json beside this script.
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHA51 = "c5b3a8f77210741abcb42f89f9972535088dbbf23bf74a795c6761107859e08a"
URL51 = ("https://github.com/frankbueltge/field-research/blob/44a83458765a23cdaebba97cce52551740bc665f/"
         "artifacts/2026-11-02-the-carried-zero/data51.js")
raw = open(sys.argv[1], "rb").read()
assert hashlib.sha256(raw).hexdigest() == SHA51, "the Field's file changed since 2026-11-02"
s = raw.decode(); f = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
d = json.load(open(os.path.join(HERE, "data.json")))
days = d["days"]; N = len(days)
assert f["cal"] == days
Z = {z["name"]: z for z in d["zones"]}

# the Field's classes: w = the zone stands in that day's sitrep table; n = no report that day at all;
# u = a report is listed but its PDF could not be read; a = the report's table does not name the zone.
runs = []
for r in f["runs"]:
    z = Z[r["zone"]]; a = days.index(r["from"])
    assert a in z["rises"], r
    if r["broke"]:
        b = days.index(r["to"]); assert b == z["rises"][z["rises"].index(a) + 1]
        assert len(r["strip"]) == b - a - 1
    else:
        assert a == z["rises"][-1] and len(r["strip"]) == N - 1 - a
    for i, c in enumerate(r["strip"]):   # 'no report' in the Field's file = a date with no report in this page's file
        assert (c == "n") == (days[a + 1 + i] not in d["sitreps"]), (r["zone"], i, c)
    runs.append({"zone": r["zone"], "a": a, "broke": r["broke"], "k": "".join(r["strip"])})
assert len(runs) == 22

def reach(k, mode, T=42):
    c = 0
    for i, x in enumerate(k):
        if mode == "cal" or (mode == "rep" and x != "n") or (mode == "said" and x == "w"): c += 1
        if c >= T: return i + 1
    return None

out = {"source": {"file": "data51.js", "url": URL51, "sha256": SHA51,
                  "by": "The Field, check 51 (The Carried Zero), session 248, 2026-11-02"},
       "noReport": f["noReport"], "unread": f["unread"], "sitrepOf": f["sitrepOf"], "runs": runs}
json.dump(out, open(os.path.join(HERE, "said.json"), "w"), separators=(",", ":"))

# ---- figures stated on the page ----
br = [r for r in runs if r["broke"]]; ho = [r for r in runs if not r["broke"]]
assert len(br) == 11 and len(ho) == 11
cnt = lambda rs, m: sum(1 for r in rs if reach(r["k"], m))
assert (cnt(br, "rep"), cnt(ho, "rep")) == (7, 11)
assert (cnt(br, "said"), cnt(ho, "said")) == (6, 11)
spared = sorted((r["zone"], days[r["a"]]) for r in br if not reach(r["k"], "rep"))
assert spared == [("Aru", "2026-06-04"), ("Aru", "2026-08-28"), ("Boga", "2026-07-06"), ("Goma", "2026-05-18")], spared
assert [r["zone"] for r in br if reach(r["k"], "rep") and not reach(r["k"], "said")] == ["Vuhovi"]
# a plain calendar wait does the same: compare build.py's curve
c = {p["T"]: p for p in d["curve"]}
assert (c[49]["broke"], c[49]["held"]) == (7, 11) and (c[51]["broke"], c[51]["held"]) == (6, 11)
lng = {}
for z in d["zones"]:
    for a, b in zip(z["rises"], z["rises"][1:]):
        if b - a > 42: lng[(z["name"], days[a])] = b - a
assert sorted(k for k, L in lng.items() if L <= 49) == spared   # the same four
assert (c[48]["broke"]) == 8 and c[50]["broke"] == 7
# the day each clock says "over" for the 11 still running (calendar days after the last rise)
rep_days = sorted(reach(r["k"], "rep") for r in ho); said_days = sorted(reach(r["k"], "said") for r in ho)
assert min(rep_days) == 44 and max(rep_days) == 59 and round(sum(rep_days) / 11, 1) == 50.7, rep_days
assert min(said_days) == 45 and max(said_days) == 65 and round(sum(said_days) / 11, 1) == 55.1, said_days
# what the 42 calendar days that make the rule's "over" were, for the 11 still running
first42 = {r["zone"]: r["k"][:42] for r in ho}
said42 = {z: k.count("w") for z, k in first42.items()}
assert sum(said42.values()) == 11 * 42 - sum(42 - v for v in said42.values())
tot = {x: sum(k.count(x) for k in first42.values()) for x in "wnua"}
assert sum(tot.values()) == 462 and tot == {"w": 352, "n": 76, "u": 21, "a": 13}, tot
assert round(100 * 352 / 462, 1) == 76.2 and round(100 * 76 / 462, 1) == 16.5
assert min(said42.values()) == 22 and said42["Lubunga"] == 22 and said42["Ariwara"] == 23
print("ok", "spared", spared, "rep", rep_days, "said", said_days, "first 42 of the running:", tot, said42)
