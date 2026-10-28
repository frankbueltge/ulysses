# Section IV, "The hour you read it" (2026-10-28, nineteenth session).
# Reduces FEWS NET's warehouse prices for Sudan to: per source and measured month, the days on which
# rows were entered, with how many carried a price and how many were marked "Not Collected".
# Input (not committed; fetch with the URL below): python3 -I build_clock.py SD.json > price-clock.json
import collections, hashlib, json, sys

URL = "https://fdw.fews.net/api/marketpricefacts/?format=json&country_code=SD&start_date=2024-01-01&end_date=2026-10-28"
raw = open(sys.argv[1], "rb").read()
rows = json.loads(raw)
src = lambda r: "FAMIS" if "FAMIS" in r["source_organization"] else "WFP" if r["source_organization"].startswith("WFP") else "other"
cells = collections.defaultdict(lambda: collections.Counter())
undated = collections.Counter()
for r in rows:
    if r["status"] not in ("Collected", "Not Collected"):
        continue
    kind = "price" if r["value"] is not None else "nc"
    if not r["created"]:
        undated[kind] += 1
        continue
    cells[(src(r), r["period_date"][:7])][(r["created"][:10], kind)] += 1
out = {"_note": "Sudan, FEWS NET Data Warehouse market price facts, reduced by build_clock.py. For each source and measured month: [day entered, prices entered that day, 'Not Collected' marks entered that day]. Rows with status 'Not Available' (to Sep 2024) and 'No Data' (no entry date) are left out; their counts are under left_out.",
       "url": URL, "sha256": hashlib.sha256(raw).hexdigest(), "rows": len(rows), "fetched": "2026-10-28",
       "left_out": dict(collections.Counter(r["status"] for r in rows if r["status"] not in ("Collected", "Not Collected"))),
       "undated": dict(undated), "series": {}}
for (s, m), c in sorted(cells.items()):
    days = sorted({d for d, _ in c})
    out["series"].setdefault(s, {})[m] = [[d, c[(d, "price")], c[(d, "nc")]] for d in days]
json.dump(out, sys.stdout, separators=(",", ":"))
