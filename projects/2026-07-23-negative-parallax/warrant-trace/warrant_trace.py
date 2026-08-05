#!/usr/bin/env python3
"""warrant-trace — does a threshold arrive with the document that produced it?

Generalisation of `circulation-measure-ruwe.py` (tick 21 of the work-line
`2026-07-23-negative-parallax`, 2026-08-01) into an instrument that can be pointed
at a threshold other than RUWE < 1.4, by anyone, without editing Python.

What it measures, over a stated frame of papers: how often a numeric threshold on a
named statistic is used at all, how many distinct values are in use, and how often
the use site carries the document the number was derived in — as against a proxy
document, a hedge word ("commonly used"), or nothing.

What it is not: a resolver. Every classifier here is a sieve whose load-bearing hits
must be read by hand; tick 21 found four false positives among eleven flagged sites,
all from one accident of sentence spacing. The sieve's job is to make hand-reading
finite, not to replace it.

Three subcommands:

    fetch    ids.txt -> src/*.txt      arXiv e-print sources, one request per 3 s
    measure  profile + src/ -> csv     the per-paper table and the summary
    verify   profile + src/ + csv      compare against an earlier run's table

`normalise()` and `body_of()` are copied verbatim from `circulation-measure-ruwe.py`,
which took them unchanged from tick 19, so that numbers produced here are comparable
with the two landed measurements. Everything that was hardcoded to RUWE — the term,
the relation vocabulary, the deriving document, the proxy documents, the provenance
and hedge vocabularies, the window — moves into a JSON profile.

Usage:
    python3 warrant_trace.py fetch   --ids ids.txt --out corpus/src [--limit N]
    python3 warrant_trace.py measure --profile profiles/ruwe-1.4.json --src corpus/src \\
                                     --out corpus/measure [--meta frame.csv] [--nocomments]
    python3 warrant_trace.py verify  --profile profiles/ruwe-1.4.json --src corpus/src \\
                                     --against ../circulation-measure-ruwe.csv --map ruwe

No paid service, no API key, no source text redistributed: the fetcher writes into a
working directory the caller chooses and the landed artefacts are the derived table
and this script.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import time
import urllib.request

VERSION = "warrant-trace 0.1 (2026-08-05)"
UA = "ulysses-warrant-trace/0.1 (artistic research; one request per 3 s)"
EPRINT = "https://arxiv.org/e-print/{}"

# ------------------------------------------------------------------ tick 19/21, verbatim
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
    """Keep .tex members, drop .bbl members and bibliography environments."""
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


# ------------------------------------------------------------------ the profile
class Profile:
    """A threshold, the document that produced it, and the vocabulary around both.

    Fields (see profiles/ruwe-1.4.json for the worked example):

      id, statistic, deriving_document   — prose, for the record and the report header
      term                               — regex matching the statistic's name
      rel                                — regex matching a comparison word or sign
      site_patterns                      — list of regexes; {TERM} and {REL} expand;
                                           the first non-empty group is the value
      window                             — characters either side of a site
      flags                              — name -> {pattern, scope: window|cites|both}
      targets                            — ordered [name, pattern]; first match wins,
                                           classifying WHICH document stands at the site
      deriving_flag                      — which flag name means "the deriving document
                                           itself is named here"
    """

    def __init__(self, d, path):
        self.path = path
        self.raw = d
        self.id = d["id"]
        self.statistic = d["statistic"]
        self.deriving_document = d["deriving_document"]
        self.window = int(d.get("window", 420))
        term, rel = d["term"], d.get("rel", "")
        self.term_re = re.compile(term)
        self.site_res = [re.compile(p.replace("{TERM}", term).replace("{REL}", rel))
                         for p in d["site_patterns"]]
        self.flags = {}
        for name, spec in d.get("flags", {}).items():
            self.flags[name] = (re.compile(spec["pattern"], re.I),
                                spec.get("scope", "window"))
        self.targets = [(t["name"], re.compile(t["pattern"], re.I))
                        for t in d.get("targets", [])]
        self.deriving_flag = d.get("deriving_flag")

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as fh:
            return cls(json.load(fh), path)

    def sha256(self):
        with open(self.path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()


def sites(text, prof):
    """Every use site of the statistic, with its window classified by the profile."""
    out, seen = [], set()
    for pat in prof.site_res:
        for m in pat.finditer(text):
            key = m.start() // 40
            if key in seen:
                continue
            seen.add(key)
            s, e = max(0, m.start() - prof.window), min(len(text), m.end() + prof.window)
            win = re.sub(r"\s+", " ", text[s:e])
            cites = " ".join(re.findall(r"<<CITE:([^>]*)>>", win))
            val = next((g for g in m.groups() if g), None)
            rec = {"match": re.sub(r"\s+", " ", m.group(0))[:110], "value": val,
                   "cite_keys": cites[:240], "window": win, "flags": {}}
            for name, (pat_f, scope) in prof.flags.items():
                hay = {"window": win, "cites": cites, "both": cites + " " + win}[scope]
                rec["flags"][name] = bool(pat_f.search(hay))
            hay = cites + " " + win
            hits = [k for k, p in prof.targets if p.search(hay)]
            rec["targets"] = hits
            rec["target"] = hits[0] if hits else ("other" if cites.strip() else "none")
            out.append(rec)
    return out


def pct(a, b):
    return f"{a}/{b} = {100.0*a/b:.1f}%" if b else f"{a}/0 = n/a"


# ------------------------------------------------------------------ fetch
def read_ids(path):
    ids = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#")[0].strip()
            if line:
                ids.append(line)
    return ids


def fetch(args):
    """arXiv e-print sources -> one flat .txt per id, in the tick-19 %%%FILE format.

    The tick-19/21 fetcher was never landed: the two measurements are re-runnable
    only by someone who rebuilds this step. That is the gap this subcommand closes,
    and the format is therefore a reconstruction, stated as one — .tex and .bbl
    members concatenated in archive order, each preceded by `%%%FILE <name>`.
    """
    os.makedirs(args.out, exist_ok=True)
    ids = read_ids(args.ids)
    if args.limit:
        ids = ids[:args.limit]
    manifest_path = os.path.join(args.out, "..", "fetch-manifest.jsonl")
    done = set()
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            done = {json.loads(l)["arxiv"] for l in fh if l.strip()}
    with open(manifest_path, "a", encoding="utf-8") as man:
        for i, aid in enumerate(ids, 1):
            if aid in done:
                continue
            safe = aid.replace("/", "_")
            url = EPRINT.format(aid)
            rec = {"arxiv": aid, "url": url, "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                         time.gmtime())}
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=120) as fh:
                    blob = fh.read()
                rec["bytes"] = len(blob)
                rec["sha256"] = hashlib.sha256(blob).hexdigest()
                parts, members = [], 0
                try:
                    tf = tarfile.open(fileobj=io.BytesIO(blob), mode="r:*")
                    for m in tf.getmembers():
                        if not m.isfile():
                            continue
                        low = m.name.lower()
                        if not (low.endswith(".tex") or low.endswith(".bbl")):
                            continue
                        data = tf.extractfile(m).read().decode("utf-8", errors="replace")
                        parts.append("%%%FILE " + m.name + "\n" + data)
                        members += 1
                except tarfile.ReadError:
                    # a single-file submission: gzipped .tex, not a tar archive
                    import gzip
                    data = gzip.decompress(blob).decode("utf-8", errors="replace")
                    parts.append("%%%FILE main.tex\n" + data)
                    members = 1
                rec["members"] = members
                rec["ok"] = members > 0
                if members:
                    with open(os.path.join(args.out, safe + ".txt"), "w",
                              encoding="utf-8") as out:
                        out.write("\n".join(parts))
            except Exception as exc:                      # recorded, never silent
                rec["ok"] = False
                rec["error"] = f"{type(exc).__name__}: {exc}"
            man.write(json.dumps(rec) + "\n")
            man.flush()
            print(f"[{i}/{len(ids)}] {aid} {'ok' if rec.get('ok') else 'FAILED'} "
                  f"{rec.get('members', 0)} members", file=sys.stderr)
            time.sleep(3)


# ------------------------------------------------------------------ measure
def measure_rows(prof, srcdir, nocomments=False):
    rows = []
    for fn in sorted(os.listdir(srcdir)):
        if not fn.endswith(".txt"):
            continue
        aid = fn[:-4]
        with open(os.path.join(srcdir, fn), encoding="utf-8", errors="replace") as fh:
            t = normalise(body_of(fh.read(), nocomments))
        S = sites(t, prof)
        rows.append({"arxiv": aid, "mentioned": bool(prof.term_re.search(t)),
                     "chars": len(t), "sites": S})
    return rows


def row_summary(prof, r):
    S = r["sites"]
    out = {"arxiv": r["arxiv"], "mentioned": int(r["mentioned"]), "sites": len(S),
           "values": "|".join(sorted({str(s["value"]) for s in S})),
           "targets": "|".join(sorted({s["target"] for s in S}))}
    for name in prof.flags:
        out["flag_" + name] = int(any(s["flags"][name] for s in S))
    return out


def measure(args):
    prof = Profile.load(args.profile)
    rows = measure_rows(prof, args.src, args.nocomments)
    summaries = [row_summary(prof, r) for r in rows]
    cols = list(summaries[0].keys()) if summaries else []
    with open(args.out + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for s in summaries:
            w.writerow(s)
    allsites = [s for r in rows for s in r["sites"]]
    report = {
        "instrument": VERSION,
        "profile": {"id": prof.id, "path": os.path.basename(prof.path),
                    "sha256": prof.sha256(), "statistic": prof.statistic,
                    "deriving_document": prof.deriving_document},
        "comments_stripped": bool(args.nocomments),
        "papers": len(rows),
        "papers_mentioning": sum(r["mentioned"] for r in rows),
        "papers_with_site": sum(1 for r in rows if r["sites"]),
        "sites": len(allsites),
        "distinct_values": len({s["value"] for s in allsites}),
        "value_counts": {},
        "flag_site_counts": {},
        "target_site_counts": {},
    }
    for s in allsites:
        report["value_counts"][str(s["value"])] = report["value_counts"].get(str(s["value"]), 0) + 1
        report["target_site_counts"][s["target"]] = report["target_site_counts"].get(s["target"], 0) + 1
        for name, v in s["flags"].items():
            if v:
                report["flag_site_counts"][name] = report["flag_site_counts"].get(name, 0) + 1
    with open(args.out + ".json", "w", encoding="utf-8") as fh:
        json.dump({"report": report, "rows": rows}, fh, indent=1)

    print(VERSION)
    print(f"profile      : {prof.id}  (sha256 {prof.sha256()[:12]}…)")
    print(f"statistic    : {prof.statistic}")
    print(f"deriving doc : {prof.deriving_document}")
    print(f"\ncorpus       : {report['papers']} papers; "
          f"{report['papers_mentioning']} mention the statistic; "
          f"{report['papers_with_site']} carry at least one use site")
    print(f"use sites    : {report['sites']}   distinct values in use: "
          f"{report['distinct_values']}")
    top = sorted(report["value_counts"].items(), key=lambda kv: -kv[1])[:12]
    print("  values     : " + ", ".join(f"{k}×{v}" for k, v in top))
    print("\nflags (share of use sites):")
    for name in prof.flags:
        print(f"  {name:16s} {pct(report['flag_site_counts'].get(name, 0), report['sites'])}")
    if prof.deriving_flag:
        n = report["flag_site_counts"].get(prof.deriving_flag, 0)
        print(f"\nthe deriving document is named at {pct(n, report['sites'])} of use sites "
              f"— a sieve count, to be hand-read before it is quoted")
    print("\nwhich document stands at the site (first match, profile order):")
    for k, v in sorted(report["target_site_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:16s} {pct(v, report['sites'])}")


# ------------------------------------------------------------------ verify
def verify(args):
    """Compare this instrument's per-paper classification against an earlier table.

    `--map` names the column prefix used by the earlier run (tick 21 wrote `ruwe_`).
    Only papers present in BOTH tables are compared; the earlier table's other rows
    are reported as not covered, never as agreement.
    """
    prof = Profile.load(args.profile)
    rows = measure_rows(prof, args.src, args.nocomments)
    mine = {r["arxiv"]: row_summary(prof, r) for r in rows}
    with open(args.against, encoding="utf-8", newline="") as fh:
        theirs = {r["arxiv"].replace("/", "_"): r for r in csv.DictReader(fh)}
    pre = args.map + "_" if args.map else ""
    pairs = [(pre + "mentioned", "mentioned"), (pre + "sites", "sites"),
             (pre + "values", "values"), (pre + "cite_targets", "targets")]
    for name in prof.flags:
        if pre + name in next(iter(theirs.values()), {}):
            pairs.append((pre + name, "flag_" + name))
    common = [a for a in sorted(mine) if a in theirs]
    print(VERSION)
    print(f"compared: {len(common)} papers present in both tables "
          f"({len(mine)} measured here, {len(theirs)} in {os.path.basename(args.against)})")
    disagreements = []
    for aid in common:
        for their_col, my_col in pairs:
            tv, mv = theirs[aid].get(their_col), str(mine[aid][my_col])
            if tv is None:
                continue
            if str(tv) != mv:
                disagreements.append({"arxiv": aid, "field": their_col,
                                      "earlier": tv, "now": mv})
    for f in {d["field"] for d in disagreements}:
        n = len([d for d in disagreements if d["field"] == f])
        print(f"  {f:24s} differs on {n} of {len(common)} papers")
    if not disagreements:
        print("  no disagreement on any compared field")
    for d in disagreements:
        print(f"    {d['arxiv']:16s} {d['field']:22s} earlier={d['earlier']!r} now={d['now']!r}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"instrument": VERSION, "profile": prof.id,
                       "compared": common, "disagreements": disagreements}, fh, indent=1)
    return 0 if not disagreements else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="arXiv e-print sources into a flat corpus")
    f.add_argument("--ids", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--limit", type=int, default=0)
    f.set_defaults(fn=fetch)

    m = sub.add_parser("measure", help="run a profile over a corpus")
    m.add_argument("--profile", required=True)
    m.add_argument("--src", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--nocomments", action="store_true")
    m.set_defaults(fn=measure)

    v = sub.add_parser("verify", help="compare against an earlier run's table")
    v.add_argument("--profile", required=True)
    v.add_argument("--src", required=True)
    v.add_argument("--against", required=True)
    v.add_argument("--map", default="")
    v.add_argument("--out", default="")
    v.add_argument("--nocomments", action="store_true")
    v.set_defaults(fn=verify)

    args = ap.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == "__main__":
    main()
