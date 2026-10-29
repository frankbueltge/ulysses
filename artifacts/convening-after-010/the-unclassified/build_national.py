# Section III, "The fourth way" (2026-10-29, twentieth session; the Field's case of session 238, re-counted here).
# For Sudan's analysis of Sep 2025, period by period: the national row of HDX's IPC table against the sum of
# its own area rows, and where El Fasher town and Kadugli town stand in each (in the population, in Phase 5).
# Inputs (not committed; HDX, CC0): python3 -I build_national.py ipc_global_area_long.csv ipc_global_national_long.csv > national-row.json
import collections, csv, hashlib, json, sys

AREA, NAT = sys.argv[1], sys.argv[2]
TOWNS = {"Al Fasher Urban": "El Fasher town", "Kadugli Urban": "Kadugli town"}
PERIODS = [("current", "cur"), ("first projection", "p1"), ("second projection", "p2")]
PH = ["1", "2", "3", "4", "5"]
near = lambda a, b: abs(a - b) <= 1000  # the national row rounds; 330,000 is far outside this
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()

nat = collections.defaultdict(dict)
for r in csv.DictReader(open(NAT, newline="")):
    if r["Country"] == "SDN" and r["Date of analysis"] == "Sep 2025":
        nat[r["Validity period"]][r["Phase"]] = int(float(r["Number"]))
area = collections.defaultdict(dict)  # duplicate rows keep the last value, as in the Field's script
for r in csv.DictReader(open(AREA, newline="")):
    if r["Country"] == "SDN" and r["Date of analysis"] == "Sep 2025":
        area[(r["Validity period"], r["Area"])][r["Phase"]] = int(float(r["Number"]))

out = {"_note": "Built by build_national.py from HDX's IPC tables (CC0). 'national' is the country row as written; 'areas' is the sum of the 215 area rows; 'towns' gives each town's own area row and whether the national row's population and Phase 5 hold it (tested by arithmetic within 1,000 people of rounding: national = areas, or national = areas minus the towns).",
       "source": {"cite": "HDX, Global: Acute Food Insecurity Country Data (CC0; source National IPC Technical Working Group)",
                  "url": "https://data.humdata.org/dataset/global-acute-food-insecurity-country-data",
                  "sha256": {"area": sha(AREA), "national": sha(NAT)}, "fetched": "2026-10-29"},
       "periods": {}}
for long, key in PERIODS:
    n = nat[long]
    rows = {a: v for (p, a), v in area.items() if p == long}
    asum = {ph: sum(v.get(ph, 0) for v in rows.values()) for ph in ["all"] + PH}
    towns = {}
    for t, name in TOWNS.items():
        v = rows.get(t, {})
        towns[name] = {"all": v.get("all", 0), "p5": v.get("5")}
    tall = sum(t["all"] for t in towns.values())
    tp5 = sum(t["p5"] or 0 for t in towns.values())
    nphases = sum(n.get(ph, 0) for ph in PH)
    out["periods"][key] = {
        "label": long,
        "national": {"all": n["all"], "phases": nphases, "p5": n["5"]},
        "areas": asum,
        "towns": towns,
        "towns_in_population": tall > 0 and near(n["all"], asum["all"]),
        "towns_left_out_of_population": tall > 0 and near(n["all"], asum["all"] - tall),
        "towns_in_phase5": tp5 > 0 and near(n["5"], asum["5"]),
        "towns_p5": tp5,
        "gap": nphases - n["all"],
    }
json.dump(out, sys.stdout, indent=1)
