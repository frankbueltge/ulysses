"""Only a Return — build the page's data from FEWS NET's data warehouse.

Source (public, no key): https://fdw.fews.net/api/marketpricefacts/?format=json&country_code=<CC>
&start_date=2024-01-01&end_date=2026-10-31 (Sudan: end_date=2026-10-28, the Studio's query of
2026-10-28, which this build re-fetched on 2026-11-01 with the same 10,039 rows). The raw files are
not committed (about 400 MB); their sha256 and row counts are written to data.json and asserted.

Kinds of row kept:
  price    a row with a value and status "Collected" (it has an id and a submission)
  absence  a row with no value and status "Not Collected", "Not Available" or
           "Missing Historic Data" (it has an id, a submission and a `created` day)
  nodata   a row with status "No Data" (no id, no submission, no `created` day). Since the second
           session of 2026-11-01 each is placed by its edges: the written rows of its own series
           before and after it, and drawn at the day the later one (the far edge) was written.
Rows with status "Aggregated" are derived from other series and are left out.

Usage: python3 -I build.py <dir with CC.json files>   (writes data.json beside this file)
"""
import collections, datetime as dt, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
T0 = dt.date(2024, 1, 1)
ABS = {"Not Collected", "Not Available", "Missing Historic Data"}
NAMES = {"AF": "Afghanistan", "CD": "DR Congo", "ET": "Ethiopia", "HT": "Haiti", "KE": "Kenya",
         "MG": "Madagascar", "MW": "Malawi", "MZ": "Mozambique", "NG": "Nigeria", "SD": "Sudan",
         "SO": "Somalia", "SS": "South Sudan", "TD": "Chad", "YE": "Yemen", "ZW": "Zimbabwe",
         "NE": "Niger", "ML": "Mali", "BF": "Burkina Faso", "UG": "Uganda"}


def day(s):
    return (dt.date.fromisoformat(s[:10]) - T0).days


def month(s):
    d = dt.date.fromisoformat(s[:10])
    return (d.year - 2024) * 12 + d.month - 1


files, countries = {}, []
T = collections.Counter()
alone = []           # dated absences written on a day their source wrote no price
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".json"):
        continue
    cc = fn[:-5]
    raw = open(os.path.join(SRC, fn), "rb").read()
    rows = json.loads(raw)
    files[cc] = {"sha256": hashlib.sha256(raw).hexdigest(), "rows": len(rows)}
    if not rows:
        continue
    sources = sorted({r["source_organization"] for r in rows if r["status"] != "Aggregated"})
    si = {s: i for i, s in enumerate(sources)}
    price_days = collections.defaultdict(collections.Counter)
    sub_has_price = collections.defaultdict(bool)
    for r in rows:
        if r["status"] == "Collected" and r["value"] is not None:
            assert r["id"] is not None and r["created"]
            price_days[r["source_organization"]][day(r["created"])] += 1
            sub_has_price[r["datacollection"]] = True
    # The edges of each No Data row (second session, 2026-11-01): the written rows of its own
    # series before and after it. "Written" = any row with a `created` day, Aggregated included.
    written = collections.defaultdict(list)    # dataseries -> [(period month, created day)]
    for r in rows:
        if r["status"] != "No Data" and r["created"]:
            written[r["dataseries"]].append((month(r["period_date"]), day(r["created"])))
    for v in written.values():
        v.sort()
    groups = collections.Counter()   # (source, kind, month, written day or -1[, far-edge month]) -> n
    for r in rows:
        st, s = r["status"], r["source_organization"]
        if st == "Aggregated":
            continue
        if st == "Collected" and r["value"] is not None:
            groups[(si[s], "price", month(r["period_date"]), day(r["created"]))] += 1
            T["price"] += 1
        elif st in ABS and r["value"] is None:
            assert r["id"] is not None and r["created"] and r["datacollection"] is not None
            w = day(r["created"])
            groups[(si[s], "absence", month(r["period_date"]), w)] += 1
            T["absence"] += 1
            T["absence:" + st] += 1
            lag = w - day(r["period_date"])
            T["absence_lag_over_180"] += lag > 180
            if price_days[s][w]:
                T["absence_same_day_as_price"] += 1
            else:
                near = min(abs(w - d) for d in price_days[s]) if price_days[s] else None
                T["absence_within_1_day_of_price"] += near is not None and near <= 1
                alone.append({"cc": cc, "source": s, "written": r["created"][:10],
                              "for": r["period_date"][:10], "nearest_price_day_off": near})
            T["absence_in_submission_with_price"] += sub_has_price[r["datacollection"]]
        elif st == "No Data":
            assert r["id"] is None and r["created"] is None and r["datacollection"] is None
            assert r["value"] is None
            m, w = month(r["period_date"]), written[r["dataseries"]]
            before = [e for e in w if e[0] < m]
            after = [e for e in w if e[0] > m]
            if before and after:
                T["nodata_between_two_written_rows"] += 1
                far = after[0]                    # the next written row: the gap's far edge
                groups[(si[s], "nodata", m, far[1], far[0])] += 1
                T["nodata_months_to_far_edge_sum"] += far[0] - m
            else:
                T["nodata_leading" if after else ("nodata_trailing" if before else "nodata_alone")] += 1
                groups[(si[s], "nodata", m, -1, -1)] += 1
            T["nodata"] += 1
        else:
            T["other:" + st] += 1
    pdays = {si[s]: sorted(c.items()) for s, c in price_days.items()}
    countries.append({"cc": cc, "name": NAMES.get(cc, cc), "sources": sources,
                      "groups": [[g[0], g[1], g[2], g[3], n] + list(g[4:])
                                 for g, n in sorted(groups.items())],
                      "price_days": pdays})

# the alone rows, folded
fold = collections.Counter((a["cc"], a["source"], a["written"], a["nearest_price_day_off"]) for a in alone)
T["absence_alone"] = len(alone)
# assertions: the numbers the page prints
assert files["SD"]["rows"] == 10039 and files["SD"]["sha256"].startswith("472b7805")
sd = next(c for c in countries if c["cc"] == "SD")
famis = sd["sources"].index("FAMIS, Sudan")
nc_feb = sum(g[4] for g in sd["groups"]
             if g[0] == famis and g[1] == "absence" and g[3] == day("2026-02-03"))
assert nc_feb == 3472, nc_feb          # the Studio's count (etudes/the-remainder, movement VII)
assert T["absence_same_day_as_price"] + T["absence_alone"] == T["absence"]
# second session: every No Data row lies between two written rows of its own series
assert T["nodata_between_two_written_rows"] == T["nodata"], dict(T)

out = {"built": dt.date.today().isoformat(), "t0": T0.isoformat(),
       "source": "https://fdw.fews.net/api/marketpricefacts/", "files": files,
       "totals": dict(T),
       "alone": [{"cc": a, "source": b, "written": c, "nearest_price_day_off": d, "rows": n}
                 for (a, b, c, d), n in sorted(fold.items())],
       "countries": countries}
json.dump(out, open(os.path.join(HERE, "data.json"), "w"), separators=(",", ":"))
print(json.dumps(out["totals"], indent=1)); print(out["alone"])
