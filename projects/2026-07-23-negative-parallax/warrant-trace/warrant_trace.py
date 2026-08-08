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
                                     --out corpus/measure [--frame ids.txt] [--nocomments]
    python3 warrant_trace.py verify  --profile profiles/ruwe-1.4.json --src corpus/src \\
                                     --against ../circulation-measure-ruwe.csv --map ruwe

No paid service, no API key, no source text redistributed: the fetcher writes into a
working directory the caller chooses and the landed artefacts are the derived table
and this script.

0.2 (tick 35, same day) repairs the defect 0.1 was built to find. `measure --frame`
gives a paper the fetcher could not read an explicit `no_source` state instead of an
absence that downstream joins turn into zeros, and every denominator in the report
excludes it. `match_flags` classifies the matched site string rather than its window,
so a profile can record *which* of several terms carried the number — needed when a
threshold is recommended on one statistic and applied to another.
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

VERSION = "warrant-trace 0.4 (2026-08-08)"


def as_number(v):
    """The number a written form denotes, or None if it is not one.

    0.3, and it is a repair of a fault this instrument was found to have twice. A
    literature writes one threshold in more than one way — `1.1` and `1.10`, `1.2`
    and `1.20` — and 0.2 compared the focus value as a *string*, so tick 36's
    machine report said "10 sites in 6 papers" where the hand count was 12 in 7.
    The same string identity sits under `distinct_values`, which is reported as
    "distinct published values in use": read as written forms the RUWE frame has
    121 and the R-hat frame 22; read as numbers, 115 and 20.

    Both readings are kept and both are reported. The written-form count is what
    the two landed measurements published and is not silently replaced.
    """
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def same_value(a, b):
    """Two written forms of one threshold, compared as numbers where they are numbers."""
    if str(a) == str(b):
        return True
    na, nb = as_number(a), as_number(b)
    return na is not None and nb is not None and na == nb
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
        # 0.2: flags tested against the matched site string itself, not its window.
        # A window flag cannot say WHICH of several alternative terms stood at the
        # site — needed when a threshold is recommended on one statistic and applied
        # to another.
        self.match_flags = {}
        for name, spec in d.get("match_flags", {}).items():
            self.match_flags[name] = re.compile(spec["pattern"], re.I)
        self.flag_names = list(self.flags) + list(self.match_flags)
        # 0.2: the value this profile is actually about. A profile names a threshold;
        # the corpus-wide counts answer "how many values are in use", and this answers
        # "and at the sites carrying THIS one, what stands there".
        self.focus_value = d.get("focus_value")
        # 0.4: one threshold written in two UNITS. 0.3 unified `1.1` and `1.10` —
        # two written forms of one number — but computer vision writes the same
        # overlap criterion as `0.5` and as `50%`, which are two different numbers
        # denoting one threshold, and no numeric comparison can see that. The
        # equivalences are declared in the profile, by a human who read the
        # literature, never inferred: `focus_equivalents: ["50"]`. Absent, 0.4
        # behaves exactly as 0.3, and the strict count is reported beside the
        # unioned one either way, so the repair is visible rather than assumed.
        self.focus_equivalents = [str(v) for v in d.get("focus_equivalents", [])]

    def is_focus(self, value):
        """Does this site carry the profile's threshold, in any declared unit?"""
        if self.focus_value is None:
            return False
        if same_value(value, str(self.focus_value)):
            return True
        return any(same_value(value, e) for e in self.focus_equivalents)

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
            for name, pat_m in prof.match_flags.items():
                rec["flags"][name] = bool(pat_m.search(rec["match"]))
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
                if blob[:4] == b"%PDF":
                    # 0.2: arXiv serves the PDF when a submission has no source. 0.1
                    # reached this through gzip and recorded "Not a gzipped file",
                    # which names the symptom and hides the fact. This is the silent
                    # zero at its origin and it gets its own word.
                    rec["ok"] = False
                    rec["members"] = 0
                    rec["error"] = "no_latex_source: arXiv served a PDF"
                    man.write(json.dumps(rec) + "\n")
                    man.flush()
                    print(f"[{i}/{len(ids)}] {aid} NO_LATEX_SOURCE", file=sys.stderr)
                    time.sleep(3)
                    continue
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
def measure_rows(prof, srcdir, nocomments=False, frame=None):
    """One row per source file — or, with `frame`, one row per paper in the frame.

    0.2, the silent-zero repair. Until now this walked the corpus directory, so a
    paper whose source could not be fetched produced *no row*, and whatever joined
    the result back to the frame filled it with zeros. Those zeros are
    indistinguishable from a paper that was read and does not mention the statistic
    — the defect found at tick 34 (`arXiv:2403.15513`, no LaTeX at arXiv). With
    `frame` the absence is a state of its own, `no_source`, and it never enters a
    denominator by accident.
    """
    ids = None
    if frame:
        ids = [i.replace("/", "_") for i in read_ids(frame)]
    else:
        ids = [fn[:-4] for fn in sorted(os.listdir(srcdir)) if fn.endswith(".txt")]
    rows = []
    for aid in ids:
        path = os.path.join(srcdir, aid + ".txt")
        if not os.path.exists(path):
            rows.append({"arxiv": aid, "state": "no_source", "mentioned": None,
                         "chars": 0, "sites": []})
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            t = normalise(body_of(fh.read(), nocomments))
        S = sites(t, prof)
        rows.append({"arxiv": aid, "state": "measured",
                     "mentioned": bool(prof.term_re.search(t)),
                     "chars": len(t), "sites": S})
    return rows


def row_summary(prof, r):
    S = r["sites"]
    no = r.get("state") == "no_source"
    out = {"arxiv": r["arxiv"], "state": r.get("state", "measured"),
           "mentioned": "" if no else int(r["mentioned"]),
           "sites": "" if no else len(S),
           "values": "|".join(sorted({str(s["value"]) for s in S})),
           "targets": "|".join(sorted({s["target"] for s in S}))}
    for name in prof.flag_names:
        out["flag_" + name] = "" if no else int(any(s["flags"][name] for s in S))
    return out


def measure(args):
    prof = Profile.load(args.profile)
    rows = measure_rows(prof, args.src, args.nocomments, getattr(args, "frame", None))
    summaries = [row_summary(prof, r) for r in rows]
    cols = list(summaries[0].keys()) if summaries else []
    with open(args.out + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for s in summaries:
            w.writerow(s)
    allsites = [s for r in rows for s in r["sites"]]
    measured = [r for r in rows if r.get("state") != "no_source"]
    nosource = [r["arxiv"] for r in rows if r.get("state") == "no_source"]
    report = {
        "instrument": VERSION,
        "profile": {"id": prof.id, "path": os.path.basename(prof.path),
                    "sha256": prof.sha256(), "statistic": prof.statistic,
                    "deriving_document": prof.deriving_document},
        "comments_stripped": bool(args.nocomments),
        "frame": len(rows),
        "papers": len(measured),
        "papers_no_source": len(nosource),
        "no_source_ids": nosource,
        "papers_mentioning": sum(r["mentioned"] for r in measured),
        "papers_with_site": sum(1 for r in measured if r["sites"]),
        "sites": len(allsites),
        # 0.3: the written-form count is the one tick 21 and tick 35 published and
        # keeps its name; the numeric one is added beside it, never in its place.
        "distinct_values": len({s["value"] for s in allsites}),
        "distinct_values_numeric": len({as_number(s["value"]) if as_number(s["value"])
                                        is not None else s["value"]
                                        for s in allsites}),
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
    if prof.focus_value is not None:
        # 0.3: matched as a number where both sides are numbers (see `as_number`).
        # 0.2's string match is kept beside it, so that a re-run of an 0.2 report can
        # be compared field by field and the repair is visible rather than assumed.
        fv = str(prof.focus_value)
        # 0.4: `fs` is the unioned set (every declared unit of the one threshold);
        # `fs_strict` is 0.3's numeric-only set and `fs_str` 0.2's string-only one.
        # All three are reported, so a re-run of an earlier report can be compared
        # field by field and each repair is visible rather than assumed.
        fs = [s for s in allsites if prof.is_focus(s["value"])]
        fs_strict = [s for s in allsites if same_value(s["value"], fv)]
        fs_str = [s for s in allsites if str(s["value"]) == fv]
        fpapers = sorted({r["arxiv"] for r in measured
                          if any(prof.is_focus(s["value"]) for s in r["sites"])})
        forms = sorted({str(s["value"]) for s in fs})
        focus = {"value": fv, "equivalents": prof.focus_equivalents,
                 "sites": len(fs), "papers": len(fpapers),
                 "written_forms": forms,
                 "sites_numeric_match_0_3": len(fs_strict),
                 "sites_string_match_0_2": len(fs_str),
                 "paper_ids": fpapers, "flag_site_counts": {}, "target_site_counts": {}}
        for s in fs:
            focus["target_site_counts"][s["target"]] = \
                focus["target_site_counts"].get(s["target"], 0) + 1
            for name, v in s["flags"].items():
                if v:
                    focus["flag_site_counts"][name] = \
                        focus["flag_site_counts"].get(name, 0) + 1
        report["focus"] = focus
    with open(args.out + ".json", "w", encoding="utf-8") as fh:
        json.dump({"report": report, "rows": rows}, fh, indent=1)

    print(VERSION)
    print(f"profile      : {prof.id}  (sha256 {prof.sha256()[:12]}…)")
    print(f"statistic    : {prof.statistic}")
    print(f"deriving doc : {prof.deriving_document}")
    print(f"\nframe        : {report['frame']} papers; "
          f"{report['papers_no_source']} with no readable source (excluded from every "
          f"denominator below)")
    print(f"corpus       : {report['papers']} papers read; "
          f"{report['papers_mentioning']} mention the statistic; "
          f"{report['papers_with_site']} carry at least one use site")
    print(f"use sites    : {report['sites']}   distinct values in use: "
          f"{report['distinct_values']} written forms, "
          f"{report['distinct_values_numeric']} as numbers")
    top = sorted(report["value_counts"].items(), key=lambda kv: -kv[1])[:12]
    print("  values     : " + ", ".join(f"{k}×{v}" for k, v in top))
    print("\nflags (share of use sites):")
    for name in prof.flag_names:
        print(f"  {name:16s} {pct(report['flag_site_counts'].get(name, 0), report['sites'])}")
    if prof.deriving_flag:
        n = report["flag_site_counts"].get(prof.deriving_flag, 0)
        print(f"\nthe deriving document is named at {pct(n, report['sites'])} of use sites "
              f"— a sieve count, to be hand-read before it is quoted")
    print("\nwhich document stands at the site (first match, profile order):")
    for k, v in sorted(report["target_site_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:16s} {pct(v, report['sites'])}")
    if "focus" in report:
        f = report["focus"]
        print(f"\nthe threshold this profile is about — value {f['value']}: "
              f"{f['sites']} sites in {f['papers']} papers "
              f"(written {', '.join(f['written_forms'])}; "
              f"0.3's numeric match found {f['sites_numeric_match_0_3']}, "
              f"0.2's string match {f['sites_string_match_0_2']}"
              + (f"; units unified: {', '.join(f['equivalents'])}" if f['equivalents'] else "")
              + ")")
        for name in prof.flag_names:
            print(f"  {name:16s} {pct(f['flag_site_counts'].get(name, 0), f['sites'])}")
        print("  document at the site:")
        for k, v in sorted(f["target_site_counts"].items(), key=lambda kv: -kv[1]):
            print(f"    {k:14s} {pct(v, f['sites'])}")


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
    for name in prof.flag_names:
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
    m.add_argument("--frame", default=None,
                   help="ids file: one row per paper in the frame, with an explicit "
                        "no_source state for papers the fetcher could not read")
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
