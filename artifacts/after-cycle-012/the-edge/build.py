"""The Edge: build edge-data.js from The Last Case's quiets and assert every figure the page states.
  python3 -I build.py
Source: ../../cycle-012/the-last-case/quiets.json (this practice, 2026-11-05), itself built from the
Field's check 52 (data52.js, commit 82f80ea, sha256 pinned in that work's build.py). A quiet runs from a
rise in a zone's confirmed count; it broke (b) with a case on day L+1, or it held to the record's end.

An edge E is a last day of reading. At E each quiet that reached 42 days is one of:
  broke    its case came on or before E: a "death" on day L+1;
  cut      it was still quiet at E: day t = min(L, days through E).
Three rules for the cut quiets, three curves of the chance a 42-day quiet is still quiet on day t:
  carried  every cut quiet is over for good: it never breaks (the declaration's reading);
  left out the cut quiets are dropped, only finished quiets speak;
  lost     Kaplan and Meier (JASA 53, 1958): a cut quiet is a loss, at risk until its day t; past
           the last loss the estimate is undefined, between 0 and P(t*).
With the hole: in Kivu no report came from 8 March to 9 June 2020 (94 days). Treated as an edge, a quiet
watched across it is cut on 7 March, the last report day before it (fewer than 42 days: it leaves).
"""
import datetime as dt, hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "cycle-012", "the-last-case", "quiets.json")
raw = open(SRC, "rb").read()
SHA = hashlib.sha256(raw).hexdigest()
D = json.loads(raw)
assert D["source"]["sha256"] == "a97c2dbd6259e287acfef003a7e8fa3a8a4fc64d4b37b0a9c5b9ab685534f567"
Q, R = D["quiets"], D["records"]
day = dt.date.fromisoformat
HOLE_LAST = day("2020-03-07")          # last report day before the 94 days
assert R["kivuHole"] == ["2020-03-07", "2020-06-10"]


def events(rec, E, hole=False):
    out = []
    for q in Q:
        if q["rec"] != rec:
            continue
        f, L = day(q["f"]), len(q["k"])
        through = (E - f).days + 1
        if hole and f <= HOLE_LAST and f + dt.timedelta(L) > HOLE_LAST:
            through = min(through, (HOLE_LAST - f).days + 1)
        if q["b"] and L + 1 <= through:
            out.append((L + 1, 1, q))
        else:
            t = min(L, through)
            if t >= 42:
                out.append((t, 0, q))
    return out


def km(ev):
    S, n, steps = 1.0, len(ev), []
    for t in sorted({t for t, _, _ in ev}):
        d = sum(1 for u, e, _ in ev if u == t and e)
        if d:
            S *= 1 - d / n
            steps.append([t, S])
        n -= sum(1 for u, _, _ in ev if u == t)
    last = max(ev, key=lambda x: (x[0], -x[1]))
    return steps, last[0], last[1] == 0, (steps[-1][1] if steps else 1.0)


def state(rec, E, hole=False):
    ev = events(rec, E, hole)
    if not ev:
        return None
    cut = [e for e in ev if not e[1]]
    steps, tS, isLoss, pS = km(ev)
    return {"n": len(ev), "broke": len(ev) - len(cut), "cut": len(cut),
            "cutLaterBroke": sum(1 for e in cut if e[2]["b"]), "tStar": tS, "tStarIsLoss": isLoss,
            "pStar": round(pS, 3), "floor": round(len(cut) / len(ev), 3)}


F = {}
end26, endK = day(R["bdbv"][1]), day(R["kivu"][1])
# at the records' own last days the losses movement of The Last Case is reproduced
F["full26"] = state("bdbv", end26)
F["fullK"] = state("kivu", endK)
assert (F["full26"]["n"], F["full26"]["cut"], F["full26"]["tStar"], round(F["full26"]["pStar"], 2)) == (22, 11, 154, 0.43)
assert (F["fullK"]["n"], F["fullK"]["cut"], F["fullK"]["tStar"], round(F["fullK"]["pStar"], 2)) == (60, 28, 633, 0.43)
# carried: the floor; left out: falls to nothing
assert F["full26"]["floor"] == 0.5 and F["fullK"]["floor"] == round(28 / 60, 3)
# the edge moved back a month: the page's first stop for 2026
F["sep29"] = state("bdbv", day("2026-09-29"))
assert (F["sep29"]["n"], F["sep29"]["cut"], F["sep29"]["cutLaterBroke"], F["sep29"]["tStar"]) == (17, 10, 3, 125)
assert round(F["sep29"]["pStar"], 2) == 0.48
F["aug30"] = state("bdbv", day("2026-08-30"))
assert (F["aug30"]["n"], F["aug30"]["cut"], F["aug30"]["tStar"], round(F["aug30"]["pStar"], 2)) == (12, 5, 95, 0.17)
# the worst edge for the declaration's reading in 2026: the most carried quiets that broke later
worst = max(((state("bdbv", end26 - dt.timedelta(b)), (end26 - dt.timedelta(b)).isoformat())
             for b in range(0, (end26 - day(R["bdbv"][0])).days) if events("bdbv", end26 - dt.timedelta(b))), key=lambda x: (x[0]["cutLaterBroke"], x[1]))
F["worst26"] = {"date": worst[1], **worst[0]}
# the hole as an edge, at Kivu's last day
F["holeK"] = state("kivu", endK, hole=True)
print(json.dumps(F, indent=1))
# how far the estimate at the last loss moves as the edge moves (2026 edges with at least 10 quiets)
ps = [(s["pStar"], E.isoformat()) for E, s in
      ((end26 - dt.timedelta(b), state("bdbv", end26 - dt.timedelta(b))) for b in range(0, 200))
      if s and s["n"] >= 10]
F["pStarRange26"] = {"min": min(ps), "max": max(ps), "edges": len(ps)}
assert F["holeK"]["n"] == 58 and F["holeK"]["tStar"] == 532 and round(F["holeK"]["pStar"], 2) == 0.19
assert F["worst26"]["date"] == "2026-10-03" and F["worst26"]["cutLaterBroke"] == 3 and F["worst26"]["cut"] == 12
print("pStarRange26", F["pStarRange26"])
# ---- second state (session 35): the rule's own day ----
# For a rule-day T (42..120) and a window of W = 90 days after it (Djaafara et al. 2021's enhanced
# surveillance), the chance that a quiet which reached T breaks within the window, under the three rules:
#   carried  breaks seen before the edge, over every quiet that reached T (cut ones held for good);
#   left out only quiets whose window is closed at the edge speak (the Field's rule, applied to windows);
#   lost     1 - S(T+W) by Kaplan and Meier among quiets at risk on day T; undefined past the last loss.
W = 90


def rule_day(rec, E, T, hole=False):
    rows = []
    for q in Q:
        if q["rec"] != rec or len(q["k"]) < T:
            continue
        f, L = day(q["f"]), len(q["k"])
        through = (E - f).days + 1
        if hole and f <= HOLE_LAST and f + dt.timedelta(L) > HOLE_LAST:
            through = min(through, (HOLE_LAST - f).days + 1)
        if through < T:
            continue
        rows.append((L + 1, 1) if q["b"] and L + 1 <= through else (min(L, through), 0))
    if not rows:
        return None
    n, H = len(rows), T + W
    inwin = sum(1 for t, e in rows if e and t <= H)
    known = sum(1 for t, e in rows if (e and t <= H) or t >= H)
    S, m = 1.0, n
    for t in sorted({t for t, _ in rows}):
        if t > H:
            break
        d = sum(1 for u, e in rows if u == t and e)
        if d:
            S *= 1 - d / m
        m -= sum(1 for u, _ in rows if u == t)
    maxt = max(t for t, _ in rows)
    undefined = H > maxt and any(t == maxt and e == 0 for t, e in rows)
    return {"n": n, "known": known, "carried": round(inwin / n, 3),
            "out": round(inwin / known, 3) if known else None,
            "lost": None if undefined else round(1 - S, 3)}


RD = {}
RD["k42"], RD["k63"] = rule_day("kivu", endK, 42), rule_day("kivu", endK, 63)
RD["h42"] = rule_day("kivu", endK, 42, hole=True)
RD["b42"], RD["b63"] = rule_day("bdbv", end26, 42), rule_day("bdbv", end26, 63)
RD["b70"] = rule_day("bdbv", end26, 70)
RD["s42"] = rule_day("bdbv", day("2026-09-29"), 42)
# the first rule-day at which, in Kivu read to its end, fewer than 1 in 10 lost quiets break within 90 days
RD["kTenth"] = next(T for T in range(42, 400) if (r := rule_day("kivu", endK, T)) and r["lost"] is not None and r["lost"] < 0.1)
assert (RD["k42"]["n"], RD["k42"]["carried"], RD["k42"]["out"], RD["k42"]["lost"]) == (60, 0.467, 0.467, 0.467)
assert (RD["k63"]["carried"], RD["k63"]["out"], RD["k63"]["lost"]) == (0.38, 0.388, 0.38)
assert (RD["h42"]["n"], RD["h42"]["carried"], RD["h42"]["out"], RD["h42"]["lost"]) == (58, 0.466, 0.54, 0.509)
assert (RD["b42"]["n"], RD["b42"]["known"], RD["b42"]["carried"], RD["b42"]["out"], RD["b42"]["lost"]) == (22, 12, 0.5, 0.917, 0.568)
assert (RD["b63"]["carried"], RD["b63"]["out"], RD["b63"]["lost"]) == (0.231, 0.75, 0.314)
assert RD["b70"]["lost"] is None
assert RD["s42"]["lost"] is None and RD["s42"]["out"] == 1.0
print("ruleDay", RD)
F["ruleDay"] = RD
data = {"source": {"path": "artifacts/cycle-012/the-last-case/quiets.json", "sha256": SHA,
                   "upstream": D["source"]},
        "records": R, "W": W, "holeLast": HOLE_LAST.isoformat(), "facts": F,
        "quiets": [{"rec": q["rec"], "z": q["z"], "f": q["f"], "L": len(q["k"]), "b": q["b"]} for q in Q]}
open(os.path.join(HERE, "edge-data.js"), "w").write("window.EDGE=" + json.dumps(data, separators=(",", ":")) + ";\n")
