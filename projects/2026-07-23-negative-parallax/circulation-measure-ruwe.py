#!/usr/bin/env python3
"""Circulation measurement — tick 21 of the work-line `2026-07-23-negative-parallax`.

Question (pre-registered in PREREGISTRATION-tick21.md, written before any count):
tick 19 measured a threshold nobody uses. This measures the criterion this same
corpus actually uses. When a paper applies a RUWE cut, does the number arrive with
its source, or with any mark of the sample and the reading it was derived from?

The number's index, from the primary read at source on 2026-08-01 — Lindegren 2018,
GAIA-C3-TN-LU-LL-124-01, §6, a section titled "An example using the RUWE": "for RUWE
there seems to be a clear breakpoint around RUWE = 1.4 ... Thus, looking at the
distribution of RUWE it is quite natural to adopt RUWE <= 1.4 as a criterion for
'good' solutions", read off a sample of 338 833 sources "nominally within 100 pc of
the Sun" further cut at parallax significance > 10. The note's Conclusions (§8) do
not contain the number.

Frame: the 599 papers of tick 19, reconstructed from circulation-measure.csv. No
citation index is re-queried; no paper is added or dropped. Normalisation, window
size and bibliography stripping are tick 19's, unchanged, so the two criteria are
measured by one instrument over one corpus.

Usage:  python3 circulation-measure-ruwe.py <workdir> [--dump RUWE|POS|NEG] [--sample N]
"""
import csv, json, os, re, sys, glob

# ---------------------------------------------------------------- tick 19, unchanged
CITE_RE = re.compile(r"\\[a-zA-Z]*cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\s*\{([^}]*)\}")


def normalise(t):
    """LaTeX -> flat text, with citation keys preserved as <<CITE:key>> markers."""
    t = CITE_RE.sub(lambda m: " <<CITE:" + m.group(1).replace(" ", "") + ">> ", t)
    t = t.replace("\\_", "_").replace("\\%", "%").replace("\\,", " ").replace("\\!", "")
    t = re.sub(r"\\(varpi|pi|sigma|cdot|times|mathrm|texttt|textit|textbf|rm|it|bf|left|right|,|;|:|&)",
               r" \1 ", t)
    t = re.sub(r"\\(geq|ge)\b", " > ", t)
    t = re.sub(r"\\(leq|le)\b", " < ", t)
    for ch in "${}~":
        t = t.replace(ch, " ")
    return re.sub(r"[ \t]+", " ", t)


def body_of(raw, drop_comments=False):
    """Keep .tex members, drop .bbl members and bibliography environments.

    `drop_comments` is NOT part of the pre-registered instrument. Tick 19's sieve
    reads LaTeX line comments as text, which was discovered while checking the two
    substitute documents on 2026-08-01: a commented-out table annotation repeated
    twenty-odd times inflated one count by an order of magnitude. The pre-registered
    run is reported as the primary result and this is reported beside it as a
    sensitivity check, because silently repairing the instrument would both hide the
    fault and break comparability with tick 19 — whose published counts carry the
    same inflation and are corrected in that record.
    """
    chunks = []
    for part in raw.split("%%%FILE "):
        name, _, content = part.partition("\n")
        if name.strip().lower().endswith(".bbl"):
            continue
        body = re.split(r"\\begin\{thebibliography\}", content)[0]
        if drop_comments:
            body = "\n".join(re.sub(r"(?<!\\)%.*$", "", ln) for ln in body.split("\n"))
        chunks.append(body)
    return "\n".join(chunks)


RATIO = (r"(?:parallax_over_error|parallax\s*/\s*parallax_error|parallax\s*/\s*sigma|"
         r"varpi\s*/\s*sigma(?:_?\s*varpi)?|plx\s*/\s*e_?plx|parallax\s+significance|"
         r"parallax\s+signal[-\s]to[-\s]noise(?:\s+ratio)?|parallax\s+S\s*/\s*N)")
POS = re.compile(RATIO + r"\s*(?:>|>=)\s*\+?\s*(\d+(?:\.\d+)?)", re.I)
NEG_PATTERNS = [
    re.compile(RATIO + r"\s*(?:<|<=)\s*-\s*(\d+(?:\.\d+)?)", re.I),
    re.compile(r"negative\s+(?:parallax(?:es)?\s+)?(?:at|by|beyond|more\s+than)\s*[<>]?\s*"
               r"(\d+(?:\.\d+)?)\s*[-\s]*sigma", re.I),
    re.compile(r"parallax(?:es)?\s+(?:that\s+(?:are|is)\s+)?negative\s+at\s*[<>]?\s*(\d+(?:\.\d+)?)", re.I),
    re.compile(r"varpi\s*\+\s*(\d+(?:\.\d+)?)\s*(?:cdot|times|\*)?\s*sigma[^<>]{0,24}<\s*0", re.I),
    re.compile(r"parallax\s*<\s*-\s*(\d+(?:\.\d+)?)\s*(?:cdot|times|\*)?\s*(?:parallax_error|sigma)", re.I),
]
# tick 19's attribution vocabulary, for the side-by-side column of Q5
ORIGIN19 = re.compile(r"fabricius|rybizki|badry|lindegren\s*(?:et\s*al\.?)?\s*\(?2021|marrese", re.I)
INDEX19 = re.compile(r"parallax_over_error|varpi\s*/\s*sigma|parallax\s+significance|"
                     r"-\s*5\s*sigma|5\s*sigma|significan\w+\s+negative|negative\s+parallax", re.I)

# ---------------------------------------------------------------- tick 21, new
TERM = r"(?:\bRUWE\b|\bruwe\b|re-?normali[sz]ed\s+unit[- ]weight\s+error)"
REL = (r"(?:<|>|=|less\s+than|smaller\s+than|lower\s+than|greater\s+than|larger\s+than|"
       r"higher\s+than|below|above|exceed(?:ing|s)?|of|up\s+to|at\s+most|at\s+least|"
       r"under|over|worse\s+than|better\s+than)")
RUWE_PATTERNS = [
    # RUWE <rel> value  — the ordinary direction, with a short intervening clause allowed
    re.compile(TERM + r"[^.;:\n]{0,50}?" + REL + r"\s*(\d(?:\.\d+)?)\b"),
    # value <rel> RUWE — the reversed direction
    re.compile(r"(\d(?:\.\d+)?)\s*(?:<|>)\s*" + TERM),
]
# A citation to Lindegren et al. 2018 (A&A 616, A2 — the many-author DR2 astrometry
# paper) is NOT a citation to the single-author technical note LL-124. The two are one
# character apart in most bibliographies, so the sieve separates only what it can
# separate and marks the rest ambiguous for hand-reading (PREREGISTRATION §3).
LIND = re.compile(r"lindegren", re.I)
TN = re.compile(r"LL-?\s?124|GAIA-C3-TN|technical\s+note|DPAC\s+technical|"
                r"re-?normali[sz](?:ing|ation)\s+the\s+astrometric\s+chi", re.I)
# provenance of the number: the sample, the reading, the release it was derived on
PROV = re.compile(r"empirical|breakpoint|break[-\s]point|100\s*pc|nearby\s+star|"
                  r"well[-\s]behaved|example|derived\s+(?:for|from|on)|calibrat", re.I)
PROV_DR2 = re.compile(r"\bDR2\b|Data\s+Release\s+2", re.I)
# status marking without citation: the field saying "this is a convention"
HEDGE = re.compile(r"commonly\s+(?:used|adopted)|widely\s+(?:used|adopted)|standard\s+"
                   r"(?:cut|threshold|criteri|value|selection)|typical(?:ly)?\s*(?:used|adopted|"
                   r"applied)|conventional|arbitrar|recommend|customar|usual(?:ly)?\s*"
                   r"(?:used|adopted|applied)|often\s+(?:used|adopted)|frequently\s+(?:used|adopted)|"
                   r"de\s+facto|rule\s+of\s+thumb|common\s+(?:practice|choice)", re.I)
# Added mid-run (PREREGISTRATION-tick21.md §5a A2, written before the complete run and
# stating what had been seen). A RUWE cut standing beside a citation is not the same as a
# RUWE cut standing beside *its own source*: in the debug sample the keys named the DR3
# validation paper, the EDR3 astrometry paper and generic release papers, none of which is
# where 1.4 was derived. Classification is by key string and is a sieve, not a resolver;
# every load-bearing assignment is checked by hand.
TARGETS = [
    ("tn", re.compile(r"LL-?\s?124|GAIA-C3-TN|lindegren.{0,12}(?:tech|note)|"
                      r"re-?normali[sz](?:ing|ation).{0,20}chi", re.I)),
    ("lind_dr2", re.compile(r"lindegren[^,\s]*(?:2018|18)\b|2018A&A\.\.\.616A\.\.\.2L", re.I)),
    ("lind_edr3", re.compile(r"lindegren[^,\s]*(?:2021|21)\b|2021A&A\.\.\.649A\.\.\.2L", re.I)),
    ("fabricius", re.compile(r"fabricius", re.I)),
    ("gaia_generic", re.compile(r"gaia[-_]?(?:collab|edr3|dr3|dr2|mission|brown|vallenari|"
                               r"prusti)|edr3astrom|dr3astrom|_astrometry|astrometry_", re.I)),
]
WIN = 420


def sites(text, pats, kind):
    out, seen = [], set()
    pats = pats if isinstance(pats, list) else [pats]
    for pat in pats:
        for m in pat.finditer(text):
            key = (m.start() // 40, kind)
            if key in seen:
                continue
            seen.add(key)
            s, e = max(0, m.start() - WIN), min(len(text), m.end() + WIN)
            win = re.sub(r"\s+", " ", text[s:e])
            cites = " ".join(re.findall(r"<<CITE:([^>]*)>>", win))
            val = next((g for g in m.groups() if g), None)
            rec = {"kind": kind, "match": re.sub(r"\s+", " ", m.group(0))[:110],
                   "value": val, "cite_keys": cites[:240], "window": win}
            if kind == "RUWE":
                rec["cite_lindegren"] = bool(LIND.search(cites) or LIND.search(win))
                rec["cite_tn"] = bool(TN.search(cites) or TN.search(win))
                rec["prov"] = bool(PROV.search(win))
                rec["prov_dr2"] = bool(PROV_DR2.search(win))
                rec["hedge"] = bool(HEDGE.search(win))
                rec["indexed"] = rec["prov"] or rec["prov_dr2"] or rec["hedge"]
                hay = cites + " " + win
                rec["targets"] = [k for k, p in TARGETS if p.search(hay)]
                rec["cite_target"] = rec["targets"][0] if rec["targets"] else (
                    "other" if cites.strip() else "none")
            else:
                rec["attributed"] = bool(ORIGIN19.search(cites) or ORIGIN19.search(win))
                rec["indexed"] = bool(INDEX19.search(win))
            out.append(rec)
    return out


def pct(a, b):
    return f"{a}/{b} = {100.0*a/b:.1f}%" if b else f"{a}/0 = n/a"


def main(workdir, dump=None, sample=0, nocomments=False):
    meta = {}
    for p in json.load(open(os.path.join(workdir, "frame_all.json"))):
        if p.get("arxiv"):
            meta.setdefault(p["arxiv"].replace("/", "_"), p)
    rows = []
    for f in sorted(glob.glob(os.path.join(workdir, "src", "*.txt"))):
        aid = os.path.basename(f)[:-4]
        t = normalise(body_of(open(f, encoding="utf-8", errors="replace").read(), nocomments))
        S = sites(t, RUWE_PATTERNS, "RUWE") + sites(t, POS, "POS") + sites(t, NEG_PATTERNS, "NEG")
        m = meta.get(aid, {})
        rows.append({"frame": m.get("frame", "?"), "arxiv": m.get("arxiv", aid),
                     "doi": m.get("doi"), "year": m.get("year"), "sites": S,
                     "ruwe_mentioned": bool(re.search(TERM, t)), "chars": len(t)})
    tag = "-nocomments" if nocomments else ""
    json.dump(rows, open(os.path.join(workdir, "analysis-ruwe%s.json" % tag), "w"), indent=1)

    def has(r, k):
        return [s for s in r["sites"] if s["kind"] == k]

    with open(os.path.join(workdir, "circulation-measure-ruwe%s.csv" % tag), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["frame", "arxiv", "doi", "year", "ruwe_mentioned", "ruwe_sites",
                    "ruwe_values", "ruwe_cite_lindegren", "ruwe_cite_tn", "ruwe_prov",
                    "ruwe_prov_dr2", "ruwe_hedge", "ruwe_cite_targets", "pos_sites", "pos_values",
                    "pos_attributed", "neg_sites", "neg_values", "neg_attributed"])
        for r in rows:
            u, p, n = has(r, "RUWE"), has(r, "POS"), has(r, "NEG")
            w.writerow([r["frame"], r["arxiv"], r["doi"], r["year"], int(r["ruwe_mentioned"]),
                        len(u), "|".join(sorted({str(x["value"]) for x in u})),
                        int(any(x["cite_lindegren"] for x in u)),
                        int(any(x["cite_tn"] for x in u)),
                        int(any(x["prov"] for x in u)),
                        int(any(x["prov_dr2"] for x in u)),
                        int(any(x["hedge"] for x in u)),
                        "|".join(sorted({x["cite_target"] for x in u})),
                        len(p), "|".join(sorted({str(x["value"]) for x in p})),
                        int(any(x["attributed"] for x in p)),
                        len(n), "|".join(sorted({str(x["value"]) for x in n})),
                        int(any(x["attributed"] for x in n))])

    allsites = [s for r in rows for s in r["sites"]]
    U = [s for s in allsites if s["kind"] == "RUWE"]
    P = [s for s in allsites if s["kind"] == "POS"]
    N = [s for s in allsites if s["kind"] == "NEG"]
    print(f"\n[LaTeX line comments {'STRIPPED (sensitivity check)' if nocomments else 'included (pre-registered instrument, tick 19 behaviour)'}]")
    print(f"\ncorpus: {len(rows)} papers with retrievable source; "
          f"{sum(r['ruwe_mentioned'] for r in rows)} mention RUWE at all")
    print(f"\n=== Q1  RUWE threshold sites: {len(U)} in "
          f"{len({r['arxiv'] for r in rows if has(r,'RUWE')})} papers")
    vals = {}
    for s in U:
        vals[s["value"]] = vals.get(s["value"], 0) + 1
    print("  values: " + ", ".join(f"{k}×{v}" for k, v in
                                   sorted(vals.items(), key=lambda kv: -kv[1])[:14]))
    print(f"\n=== Q2  any Lindegren citation in the window : {pct(sum(s['cite_lindegren'] for s in U), len(U))}")
    print(f"=== Q3  technical note identified as such    : {pct(sum(s['cite_tn'] for s in U), len(U))}")
    print(f"=== Q4  any index/hedge mark in the window   : {pct(sum(s['indexed'] for s in U), len(U))}")
    print(f"      of which provenance words (non-DR2)   : {pct(sum(s['prov'] for s in U), len(U))}")
    print(f"      of which the DR2 token alone (weak)   : {pct(sum(s['prov_dr2'] for s in U), len(U))}")
    print(f"      of which a convention hedge           : {pct(sum(s['hedge'] for s in U), len(U))}")
    print(f"\n=== Q3b which document stands beside the cut (first match, priority order)")
    tt = {}
    for s in U:
        tt[s["cite_target"]] = tt.get(s["cite_target"], 0) + 1
    for k, v in sorted(tt.items(), key=lambda kv: -kv[1]):
        print(f"      {k:14s} {pct(v, len(U))}")
    print(f"      (any mention of the technical note anywhere in the window: "
          f"{pct(sum('tn' in s['targets'] for s in U), len(U))})")

    print(f"\n=== Q5  side by side, one instrument, one corpus")
    print(f"  RUWE threshold sites            {len(U):5d}   source cited in window: "
          f"{pct(sum(s['cite_lindegren'] for s in U), len(U))}")
    print(f"  positive parallax-significance  {len(P):5d}   source cited in window: "
          f"{pct(sum(s['attributed'] for s in P), len(P))}")
    print(f"  negative parallax-significance  {len(N):5d}   source cited in window: "
          f"{pct(sum(s['attributed'] for s in N), len(N))}")

    if dump:
        sel = [ (r,s) for r in rows for s in r["sites"] if s["kind"] == dump ]
        if sample:
            step = max(1, len(sel) // sample)
            sel = sel[::step][:sample]
            print(f"\n--- fixed-rule sample: every {step}th site in arXiv order, {len(sel)} shown")
        for r, s in sel:
            flags = " ".join(k for k in ("cite_lindegren", "cite_tn", "prov", "prov_dr2",
                                         "hedge", "attributed", "indexed") if s.get(k))
            print(f"\n--- {r['frame']} {r['arxiv']} ({r['year']}) value={s['value']} [{flags}]")
            print("    match:", s["match"])
            print("    keys :", s["cite_keys"][:150])
            print("    win  :", s["window"][WIN - 240:WIN + 300])


if __name__ == "__main__":
    a = sys.argv
    wd = a[1] if len(a) > 1 else "."
    d = a[a.index("--dump") + 1] if "--dump" in a else None
    n = int(a[a.index("--sample") + 1]) if "--sample" in a else 0
    main(wd, d, n, "--nocomments" in a)
