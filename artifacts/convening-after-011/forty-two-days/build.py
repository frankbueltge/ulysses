"""Forty-Two Days — build the page's data from OCHA's consolidated DRC Ebola file on HDX.

Usage: python3 -I build.py <path to drc_ebola_cases_consolidated.csv>
Writes data.json beside this script and asserts every figure the page states in prose.
"""
import csv, collections, datetime as dt, hashlib, json, os, sys

SHA = "761e1ed4f11db45a28ff8338a22ae78d9d78fd942603177bb8cbc16fb8352dbf"
URL = ("https://data.humdata.org/dataset/e902b209-b7bc-42f9-893a-294276d7cc62/resource/"
       "f7c9b552-0d41-4559-9fae-c450175fc39c/download/drc_ebola_cases_consolidated.csv")
path = sys.argv[1]
raw = open(path, "rb").read()
assert hashlib.sha256(raw).hexdigest() == SHA, "file changed since 2026-11-01"
rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
D = dt.date.fromisoformat
sitreps = sorted({r["reference_date"] for r in rows})
first, last = D(sitreps[0]), D(sitreps[-1])
cal = [(first + dt.timedelta(i)).isoformat() for i in range((last - first).days + 1)]

conf = collections.defaultdict(dict)   # zone -> date -> cumulative confirmed cases
susp = collections.defaultdict(list)   # zone -> dates with a suspected-case row
any_ = collections.defaultdict(list)   # zone -> dates with any row
code = {}
for r in rows:
    if r["location_level"] != "3" or r["location_name"] == "NA":
        continue  # 'NA' rows are cases not attributed to a zone
    z = r["location_name"]; code[z] = r["location_code"]
    any_[z].append(r["reference_date"])
    if r["measure"] == "cases" and r["case_classification"] == "confirmed":
        conf[z][r["reference_date"]] = int(r["value"])
    if r["measure"] == "cases" and r["case_classification"] == "suspected":
        susp[z].append(r["reference_date"])

zones = []
for z in sorted(set(conf) | set(susp)):
    v = conf.get(z, {})
    vals = [v.get(d) for d in cal]            # None = no row that day
    m, rises, revisions = -1, [], 0
    for i, x in enumerate(vals):
        if x is None: continue
        if x > m:
            if m >= 0 or x > 0: rises.append(i)
            m = x
        elif x < m: revisions += 1
    zones.append({"name": z, "code": code.get(z, ""), "v": vals, "rises": rises,
                  "revisions": revisions,
                  "lastSusp": max(susp[z]) if susp.get(z) else None,
                  "firstAny": min(any_[z]), "lastAny": max(any_[z]),
                  "lastRow": max(v) if v else None})

# quiet runs: calendar days from one rise to the next (or to the last day, censored)
def runs():
    for z in zones:
        r = z["rises"]
        for a, b in zip(r, r[1:]): yield z["name"], a, b - a, True
        if r: yield z["name"], r[-1], len(cal) - 1 - r[-1], False

curve = []
for T in range(7, 121):
    broke = sum(1 for _, _, L, ended in runs() if ended and L > T)
    held = sum(1 for _, _, L, ended in runs() if not ended and L >= T)
    curve.append({"T": T, "broke": broke, "held": held})
c = {x["T"]: x for x in curve}

out = {"source": {"url": URL, "sha256": SHA, "file": "drc_ebola_cases_consolidated.csv",
                  "publisher": "OCHA DRC on HDX (CC BY), from INRB-UMIE", "fetched": "2026-11-01"},
       "days": cal, "sitreps": sitreps, "zones": zones, "curve": curve}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json"), "w"),
          separators=(",", ":"))

# figures stated in the page's prose
withconf = [z for z in zones if z["rises"]]
assert len(cal) == 169 and len(sitreps) == 143
assert len(zones) == 69 and len(withconf) == 67
assert [z["name"] for z in zones if not z["rises"]] == ["Jiba", "Karisimbi"]
assert c[42]["broke"] == 11 and len({n for n, _, L, e in runs() if e and L > 42}) == 10
assert c[42]["held"] == 11, c[42]["held"]
assert c[63]["broke"] == 3, c[63]["broke"]
mx = max(L for _, _, L, e in runs() if e)
assert mx == 86, mx
assert c[90]["broke"] == 0 and c[21]["broke"] == 34


print("ok", {T: c[T] for T in (21, 42, 63, 90)}, "longest broken quiet", mx)
mah = next(z for z in zones if z["name"] == "Mahagi")
assert any(cal[a] == "2026-07-27" and cal[b] == "2026-10-21" for a, b in zip(mah["rises"], mah["rises"][1:]))
assert (D("2026-10-29") - D("2026-05-30")).days == 152
never = [z for z in zones if not z["rises"]]
assert [(z["firstAny"], z["lastAny"]) for z in never] == [("2026-05-28", "2026-05-30"), ("2026-05-24", "2026-05-30")]
kar = never[1]["v"]; assert [x for x in kar if x is not None] == [0] * 5  # Karisimbi: five written zeros
assert all(x is None for x in never[0]["v"])  # Jiba: no confirmed-case row at all
assert sum(1 for r in rows) == 13363
assert c[42]["broke"] + c[42]["held"] == 22
assert c[63]["held"] == 10 and c[90]["held"] == 5
