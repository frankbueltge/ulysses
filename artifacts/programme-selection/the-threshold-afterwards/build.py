"""The Threshold Afterwards — build and check.

Reads the RAPID 26.5N overturning record (moc_transports.nc, v2024.1a; not committed:
fetch it from the address in meta.json and pass its path), writes the monthly means the
page reads (data.js), recomputes every figure the page and the bulletin state with the
page's own two readings, and asserts them. Run: python3 build.py moc_transports.nc
"""
import datetime as dt
import hashlib
import json
import sys
from collections import defaultdict

import h5py
import numpy as np

SHA = "ba135d9447a87c2bf5dcc8870e2cb73ff348c412fa1bc3501145e01c79788eed"
W = 60          # the early-warning window, in months (the page's default)
TAU = 0.3       # the declared rule: tau above +0.3 reads "slowing", below -0.3 "not slowing"
FIRST = W + 24   # reading B speaks once its run of window values is two years long

path = sys.argv[1]
assert hashlib.sha256(open(path, "rb").read()).hexdigest() == SHA, "not the file this was built on"
f = h5py.File(path, "r")
t = f["time"][:]
m = f["moc_mar_hc10"][:].astype(float)
m[m < -9000] = np.nan
base = dt.date(2004, 4, 1)
acc = defaultdict(list)
for x, v in zip(t, m):
    if not np.isnan(v):
        d = base + dt.timedelta(days=float(x))
        acc[(d.year, d.month)].append(v)
keys = sorted(acc)
mm = np.array([np.mean(acc[k]) for k in keys])
N = len(keys)
assert keys[0] == (2004, 4) and keys[-1] == (2024, 3) and N == 240


def trend(s):
    """Reading A: least-squares slope (Sv per decade) of every month up to s, and the year
    that slope reaches zero from the fitted value at s (None if it never does)."""
    x = np.arange(s + 1) / 120.0
    b, a = np.polyfit(x, mm[: s + 1], 1)
    here = a + b * x[-1]
    zero = None if b >= 0 else keys[s][0] + (keys[s][1] - 0.5) / 12 + 10 * here / -b
    return b, zero


def ar1(seg):
    xx = np.arange(len(seg))
    r = seg - np.polyval(np.polyfit(xx, seg, 1), xx)
    return float(np.corrcoef(r[:-1], r[1:])[0, 1])


def kendall(a):
    n = len(a)
    s = sum(np.sign(a[j] - a[i]) for i in range(n) for j in range(i + 1, n))
    return s / (n * (n - 1) / 2)


def warning(s):
    """Reading B: seasonal cycle removed with a climatology of the months up to s only,
    lag-1 autocorrelation in each trailing W-month window, Kendall tau of that run."""
    clim = [np.mean([mm[j] for j in range(s + 1) if keys[j][1] == mo]) for mo in range(1, 13)]
    an = np.array([mm[j] - clim[keys[j][1] - 1] for j in range(s + 1)])
    run = [ar1(an[e - W + 1: e + 1]) for e in range(W - 1, s + 1)]
    tau = kendall(run)
    verdict = "slowing" if tau > TAU else "not slowing" if tau < -TAU else "undecided"
    return run[-1], tau, verdict


rows = []
for s in range(FIRST - 1, N):
    b, zero = trend(s)
    r, tau, v = warning(s)
    rows.append({"ym": "%d-%02d" % keys[s], "slope": round(b, 3),
                 "zero": None if zero is None else round(zero, 1),
                 "ar1": round(r, 3), "tau": round(tau, 3), "verdict": v})

by = {r["ym"]: r for r in rows}
count = defaultdict(int)
for r in rows:
    count[r["verdict"]] += 1
zeros = [r["zero"] for r in rows if r["zero"] is not None]
first_slow = next(r["ym"] for r in rows if r["verdict"] == "slowing")
last_slow = [r["ym"] for r in rows if r["verdict"] == "slowing"][-1]
first_not = next(r["ym"] for r in rows if r["verdict"] == "not slowing")

# The figures the page and the bulletin state.
assert len(rows) == N - FIRST + 1
assert round(by["2014-03"]["slope"], 1) == -3.2 and round(by["2024-03"]["slope"], 1) == -0.9
assert by["2011-03"]["zero"] == 2034.1 and by["2014-03"]["zero"] == 2062.6 and by["2024-03"]["zero"] == 2197.9
assert round(by["2011-03"]["slope"], 1) == -6.6
assert dict(count) == {"slowing": 42, "undecided": 30, "not slowing": 85}
assert (min(zeros), max(zeros)) == (2034.1, 2351.6)
assert round(float(mm.min()), 1) == 6.6 and keys[int(mm.argmin())] == (2013, 3)
assert round(float(mm.mean()), 1) == 17.0
print("standing months:", len(rows), dict(count))
print("first slowing", first_slow, "last slowing", last_slow, "first not slowing", first_not)
print("zero-year range", min(zeros), max(zeros))
print("2014-03", by["2014-03"], "\n2024-03", by["2024-03"])

with open("data.js", "w") as out:
    out.write("// Monthly means of RAPID 26.5N overturning transport (moc_mar_hc10, Sv), v2024.1a;\n")
    out.write("// built by build.py from moc_transports.nc sha256 %s\n" % SHA)
    out.write("window.RAPID = %s;\n" % json.dumps({"start": "2004-04", "sv": [round(float(v), 3) for v in mm]}))
json.dump({"window_months": W, "tau_rule": TAU, "counts": count, "first_slowing": first_slow,
           "last_slowing": last_slow, "first_not_slowing": first_not,
           "zero_year_min": min(zeros), "zero_year_max": max(zeros), "rows": rows},
          open("results.json", "w"), indent=1)
