#!/usr/bin/env python3
"""Circulation measurement — tick 19 of the work-line `2026-07-23-negative-parallax`.

Question: when a threshold its own author calls "an illustrative example and not a
recommendation" (Fabricius et al. 2021, A&A 649, A5, §3.2) is reused downstream, does its
warrant travel with it — and does the number computed from it travel with its index?

Method (see PREREGISTRATION-tick19.md, written before the counts):

  Frame A  works that OpenCitations records as citing 10.1051/0004-6361/202039834
           (Fabricius et al. 2021), union the same list from a second metadata index.
  Frame B  works that OpenCitations records as citing 10.1093/mnras/stab323
           (El-Badry, Rix & Heintz 2021) — the paper whose arithmetic on that limit
           produced "2,877,625 sources, implying that about 4.5% ... have spurious
           solutions".

  Citing DOIs are resolved to arXiv identifiers, the LaTeX source of each is fetched from
  arXiv (one request per 3 s), bibliographies are dropped, the remaining text is
  normalised, and every use site is located and classified. No source text is
  redistributed; only the derived table is kept.

This script expects, beside it, the working directory produced by the fetch step:
  frame_all.json   the citation frame (doi, arxiv, title, year, frame)
  src/<arxiv>.txt  the concatenated .tex bodies, one file per paper

Usage:  python3 circulation-measure.py <workdir> [--dump NEG|FRAC]
"""
import csv, json, os, re, sys, glob

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


RATIO = (r"(?:parallax_over_error|parallax\s*/\s*parallax_error|parallax\s*/\s*sigma|"
         r"varpi\s*/\s*sigma(?:_?\s*varpi)?|plx\s*/\s*e_?plx|parallax\s+significance|"
         r"parallax\s+signal[-\s]to[-\s]noise(?:\s+ratio)?|parallax\s+S\s*/\s*N)")
POS = re.compile(RATIO + r"\s*(?:>|>=)\s*\+?\s*(\d+(?:\.\d+)?)", re.I)
NEG_PATTERNS = [
    re.compile(RATIO + r"\s*(?:<|<=)\s*-\s*(\d+(?:\.\d+)?)", re.I),
    re.compile(r"negative\s+(?:parallax(?:es)?\s+)?(?:at|by|beyond|more\s+than)\s*[<>]?\s*"
               r"(\d+(?:\.\d+)?)\s*[-\s]*sigma", re.I),
    re.compile(r"parallax(?:es)?\s+(?:that\s+(?:are|is)\s+)?negative\s+at\s*[<>]?\s*(\d+(?:\.\d+)?)", re.I),
    # "varpi + N sigma_varpi < 0" — a negative parallax significant at N sigma. The trailing
    # "< 0" is required: without it the same string matches ordinary distance-range criteria
    # (verified by hand on two false positives, arXiv:2201.09097 and arXiv:2211.01449).
    re.compile(r"varpi\s*\+\s*(\d+(?:\.\d+)?)\s*(?:cdot|times|\*)?\s*sigma[^<>]{0,24}<\s*0", re.I),
    re.compile(r"parallax\s*<\s*-\s*(\d+(?:\.\d+)?)\s*(?:cdot|times|\*)?\s*(?:parallax_error|sigma)", re.I),
]
# A percentage on its own is not the figure in question: 4.5 appears in section numbers and
# error bars. A FRAC site counts only when a spurious/contamination context stands in the same
# window (checked in sites()), except for the seven-digit count, which is unambiguous.
FRAC = re.compile(r"2\s?877\s?625|2,877,625|(?<![-\d.^_])4\.5\s*%|(?<![-\d.^_])4\.5\s*per\s*cent|"
                  r"(?<![-\d.^_])4\.47\s*%|3\.04\s*million", re.I)
FRAC_CONTEXT = re.compile(r"spurious|contaminat|unreliable\s+astrometr|bad\s+astrometric", re.I)
# The general form of the same question: whenever this literature states ANY spurious-solution
# percentage, does the cut that the percentage is a percentage OF travel with it?
SPURFRAC = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|per\s*cent)[^.]{0,120}?spurious|"
                      r"spurious[^.]{0,120}?(\d+(?:\.\d+)?)\s*(?:%|per\s*cent)", re.I)
SPUR = re.compile(r"spurious\s+(?:astrometric\s+)?(?:solution|source|parallax|astrometry)", re.I)
# If the ±5 limit is not what travels out of that paper, something else does. These are the
# criteria the same literature actually applies when it wants to exclude bad astrometry.
SUCCESSORS = {
    "ruwe": re.compile(r"\bRUWE\b|renormalised\s+unit\s+weight", re.I),
    "fidelity": re.compile(r"fidelity_v\d|astrometric_fidelity|\bfidelity\b.{0,40}Rybizki|Rybizki.{0,60}fidelity", re.I),
    "excess_noise": re.compile(r"astrometric_excess_noise", re.I),
    "sigma5d": re.compile(r"astrometric_sigma5d_max", re.I),
    "ipd_gof": re.compile(r"ipd_gof_harmonic_amplitude|ipd_frac_multi_peak", re.I),
    "visibility": re.compile(r"visibility_periods_used", re.I),
    "gof_al": re.compile(r"astrometric_gof_al", re.I),
}
ORIGIN = re.compile(r"fabricius|rybizki|badry|lindegren\s*(?:et\s*al\.?)?\s*\(?2021|marrese", re.I)
INDEX = re.compile(r"parallax_over_error|varpi\s*/\s*sigma|parallax\s+significance|"
                   r"-\s*5\s*sigma|5\s*sigma|significan\w+\s+negative|negative\s+parallax", re.I)
WIN = 420


def sites(text, pat, kind):
    out = []
    for m in pat.finditer(text):
        s, e = max(0, m.start() - WIN), min(len(text), m.end() + WIN)
        win = re.sub(r"\s+", " ", text[s:e])
        if kind == "FRAC" and not re.search(r"2\s?877\s?625|2,877,625", m.group(0)) \
                and not FRAC_CONTEXT.search(win):
            continue
        cites = " ".join(re.findall(r"<<CITE:([^>]*)>>", win))
        out.append({"kind": kind,
                    "match": re.sub(r"\s+", " ", m.group(0))[:100],
                    "value": next((g for g in m.groups() if g), None),
                    "attributed": bool(ORIGIN.search(cites) or ORIGIN.search(win)),
                    "indexed": bool(INDEX.search(win)),
                    "cite_keys": cites[:200],
                    "window": win})
    return out


def body_of(raw):
    """Keep .tex members, drop .bbl members and bibliography environments."""
    chunks = []
    for part in raw.split("%%%FILE "):
        name, _, content = part.partition("\n")
        if name.strip().lower().endswith(".bbl"):
            continue
        chunks.append(re.split(r"\\begin\{thebibliography\}", content)[0])
    return "\n".join(chunks)


def main(workdir, dump=None):
    meta = {}
    for p in json.load(open(os.path.join(workdir, "frame_all.json"))):
        if p.get("arxiv"):
            meta.setdefault(p["arxiv"].replace("/", "_"), p)
    rows = []
    for f in sorted(glob.glob(os.path.join(workdir, "src", "*.txt"))):
        aid = os.path.basename(f)[:-4]
        t = normalise(body_of(open(f, encoding="utf-8", errors="replace").read()))
        S = []
        for pat in NEG_PATTERNS:
            S += sites(t, pat, "NEG")
        S += sites(t, POS, "POS")
        S += sites(t, FRAC, "FRAC")
        S += sites(t, SPURFRAC, "SPURFRAC")
        m = meta.get(aid, {})
        rows.append({"frame": m.get("frame", "?"), "arxiv": m.get("arxiv", aid),
                     "doi": m.get("doi"), "year": m.get("year"),
                     "title": m.get("title"), "sites": S,
                     "spurious_terms": len(SPUR.findall(t)),
                     "successors": sorted(k for k, pat in SUCCESSORS.items() if pat.search(t)),
                     "chars": len(t)})
    json.dump(rows, open(os.path.join(workdir, "analysis.json"), "w"), indent=1)

    def has(r, k): return [s for s in r["sites"] if s["kind"] == k]

    with open(os.path.join(workdir, "circulation-measure.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["frame", "arxiv", "doi", "year", "neg_sites", "neg_values", "neg_attributed",
                    "pos_sites", "pos_values", "pos_attributed", "frac_sites", "frac_attributed",
                    "frac_indexed", "spurfrac_sites", "spurfrac_attributed", "spurfrac_indexed",
                    "spurious_terms", "successor_criteria"])
        for r in rows:
            n, p, fr = has(r, "NEG"), has(r, "POS"), has(r, "FRAC")
            sf = has(r, "SPURFRAC")
            w.writerow([r["frame"], r["arxiv"], r["doi"], r["year"],
                        len(n), "|".join(sorted({str(x["value"]) for x in n})),
                        int(any(x["attributed"] for x in n)),
                        len(p), "|".join(sorted({str(x["value"]) for x in p})),
                        int(any(x["attributed"] for x in p)),
                        len(fr), int(any(x["attributed"] for x in fr)),
                        int(any(x["indexed"] for x in fr)),
                        len(sf), int(any(x["attributed"] for x in sf)),
                        int(any(x["indexed"] for x in sf)), r["spurious_terms"],
                        "|".join(r["successors"])])

    for fname in ("A", "B", None):
        sel = [r for r in rows if fname is None or r["frame"] == fname]
        if not sel:
            continue
        neg = [r for r in sel if has(r, "NEG")]
        pos = [r for r in sel if has(r, "POS")]
        fr = [r for r in sel if has(r, "FRAC")]
        sfr = [r for r in sel if has(r, "SPURFRAC")]
        print(f"\n=== frame {fname or 'ALL'} — {len(sel)} papers with retrievable source ===")
        print(f"  negative-side significance cut applied: {len(neg)}"
              f"  (origin named in the neighbourhood: {sum(any(x['attributed'] for x in has(r,'NEG')) for r in neg)})")
        print(f"  positive-side significance cut applied: {len(pos)}"
              f"  (origin named in the neighbourhood: {sum(any(x['attributed'] for x in has(r,'POS')) for r in pos)})")
        print(f"  spurious/contamination fraction quoted: {len(fr)}"
              f"  (origin named: {sum(any(x['attributed'] for x in has(r,'FRAC')) for r in fr)};"
              f" threshold named: {sum(any(x['indexed'] for x in has(r,'FRAC')) for r in fr)})")
        print(f"  any spurious-solution percentage stated: {len(sfr)}"
              f"  (origin named: {sum(any(x['attributed'] for x in has(r,'SPURFRAC')) for r in sfr)};"
              f" threshold named in the same window: {sum(any(x['indexed'] for x in has(r,'SPURFRAC')) for r in sfr)})")
        spur_papers = [r for r in sel if r["spurious_terms"]]
        print(f"  papers discussing spurious astrometric solutions at all: {len(spur_papers)}")
        tally = {}
        for r in spur_papers:
            for k in r["successors"]:
                tally[k] = tally.get(k, 0) + 1
        print("  what those papers actually apply: " +
              ", ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda kv: -kv[1])))

    if dump:
        for r in rows:
            for s in r["sites"]:
                if s["kind"] == dump:
                    print(f"\n--- {r['frame']} {r['arxiv']} ({r['year']}) {s['kind']} "
                          f"value={s['value']} attributed={s['attributed']} indexed={s['indexed']}")
                    print("   keys:", s["cite_keys"][:120])
                    print("   ...", s["window"][WIN - 200:WIN + 260], "...")


if __name__ == "__main__":
    wd = sys.argv[1] if len(sys.argv) > 1 else "."
    dmp = sys.argv[sys.argv.index("--dump") + 1] if "--dump" in sys.argv else None
    main(wd, dmp)
