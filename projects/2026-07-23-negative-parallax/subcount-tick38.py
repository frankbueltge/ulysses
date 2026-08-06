#!/usr/bin/env python3
"""Tick 38 — what the published sub-count 393 is, if it is anything reproducible.

Pre-registered in PREREGISTRATION-tick38.md, written before this ran.

`TRACE.md` tick 21 publishes "numeric sites (deduplicated) | 803" and "sites at the
value 1.4 | 393, in 187 papers". The landed table of that same tick,
`circulation-measure-ruwe.csv`, sums to 810 sites, and tick 35's independent re-run
found 397 at 1.4 while reproducing every per-paper field of the landed table. The
script that wrote that CSV prints its summary in the same run from the same list of
site records, so 803 and 810 cannot come from one run.

This asks whether the deduplication the tick-21 text mentions in one sentence —
"10 of 599 archives carry a same-named .tex in more than one path", removing 0.9 %
of sites — produces 803 and 393. The rule itself was never landed; three candidate
reconstructions are run and all three are reported.

Frame: the 259 papers carrying at least one RUWE site in the landed table. A paper
with no site cannot lose one to deduplication, so the restriction is exact for every
site count here. It is not exact for "papers mentioning RUWE", which is not tested.

Usage:  python3 subcount-tick38.py <srcdir> [--landed circulation-measure-ruwe.csv]
                                            [--manifest warrant-trace/fetch-manifest-tick35.jsonl]
                                            [--fetched <srcdir>/../fetch-manifest.jsonl]
"""
import argparse, csv, importlib.util, json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))


def load_tick21():
    """Import the tick-21 script by path — its filename is not an identifier."""
    path = os.path.join(HERE, "circulation-measure-ruwe.py")
    spec = importlib.util.spec_from_file_location("tick21", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tick21"] = mod
    spec.loader.exec_module(mod)
    return mod


def members(raw):
    """The %%%FILE members of a fetched source, in archive order: (name, content)."""
    out = []
    for part in raw.split("%%%FILE ")[1:]:
        name, _, content = part.partition("\n")
        out.append((name.strip(), content))
    return out


def rebuild(ms):
    return "\n".join("%%%FILE " + n + "\n" + c for n, c in ms)


def rule_none(ms):
    return ms


def rule_2a(ms):
    """Same basename, keep the first."""
    seen, out = set(), []
    for n, c in ms:
        b = os.path.basename(n).lower()
        if b in seen:
            continue
        seen.add(b)
        out.append((n, c))
    return out


def rule_2b(ms):
    """Same basename AND identical content."""
    seen, out = set(), []
    for n, c in ms:
        key = (os.path.basename(n).lower(), hash(c))
        if key in seen:
            continue
        seen.add(key)
        out.append((n, c))
    return out


def rule_2c(ms):
    """Identical content, any name."""
    seen, out = set(), []
    for n, c in ms:
        if hash(c) in seen:
            continue
        seen.add(hash(c))
        out.append((n, c))
    return out


RULES = [("1  no deduplication", rule_none),
         ("2a same basename", rule_2a),
         ("2b same basename + identical content", rule_2b),
         ("2c identical content, any name", rule_2c)]


def run(mod, corpus, rule):
    """Per-paper RUWE site records under one deduplication rule."""
    per = {}
    for aid, raw in corpus.items():
        text = mod.normalise(mod.body_of(rebuild(rule(members(raw)))))
        per[aid] = mod.sites(text, mod.RUWE_PATTERNS, "RUWE")
    return per


def report(name, per, focus="1.4"):
    allsites = [s for v in per.values() for s in v]
    papers = sum(1 for v in per.values() if v)
    vals = {s["value"] for s in allsites}
    fs = [s for s in allsites if s["value"] == focus]
    fp = sum(1 for v in per.values() if any(s["value"] == focus for s in v))
    print(f"  {name:38s} sites {len(allsites):5d}  papers {papers:4d}  "
          f"values {len(vals):4d}  at {focus}: {len(fs):4d} in {fp:4d} papers")
    return {"rule": name, "sites": len(allsites), "papers_with_site": papers,
            "distinct_values": len(vals), "focus_value": focus,
            "focus_sites": len(fs), "focus_papers": fp}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("srcdir")
    ap.add_argument("--landed", default=os.path.join(HERE, "circulation-measure-ruwe.csv"))
    ap.add_argument("--manifest", default=os.path.join(HERE, "warrant-trace",
                                                       "fetch-manifest-tick35.jsonl"))
    ap.add_argument("--fetched", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    landed = {}
    with open(args.landed, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            landed[r["arxiv"]] = r
    frame = [a for a, r in landed.items() if int(r["ruwe_sites"] or 0) > 0]

    # --- the corpus, and whether it is the same bytes as tick 35 fetched
    # Both manifests are deduplicated by identifier, last record wins — this run, like
    # tick 35's, briefly had two fetchers appending to one file, and the surplus rows
    # would otherwise be counted as extra agreements.
    fetched_path = args.fetched or os.path.join(args.srcdir, "..", "fetch-manifest.jsonl")
    drift = {"compared": 0, "same_sha": 0, "differs": [], "missing": [],
             "duplicate_rows": 0}
    if os.path.exists(fetched_path) and os.path.exists(args.manifest):
        old = {}
        with open(args.manifest, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    d = json.loads(line)
                    old[d["arxiv"]] = d.get("sha256")
        rows, new = 0, {}
        with open(fetched_path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                rows += 1
                new[d["arxiv"]] = d.get("sha256")
        drift["duplicate_rows"] = rows - len(new)
        for aid, sha in new.items():
            if aid not in old:
                continue
            drift["compared"] += 1
            if old[aid] == sha:
                drift["same_sha"] += 1
            else:
                drift["differs"].append(aid)

    corpus = {}
    for aid in frame:
        p = os.path.join(args.srcdir, aid.replace("/", "_") + ".txt")
        if not os.path.exists(p):
            drift["missing"].append(aid)
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            corpus[aid] = fh.read()

    print(f"frame (papers with >=1 RUWE site in the landed table): {len(frame)}")
    print(f"corpus read: {len(corpus)}   missing: {len(drift['missing'])}")
    print(f"sha256 compared against the tick-35 manifest: {drift['compared']}, "
          f"identical {drift['same_sha']}, differing {len(drift['differs'])}"
          + (f" {drift['differs']}" if drift["differs"] else "")
          + f"   (surplus manifest rows discarded: {drift['duplicate_rows']})")
    print(f"landed table, these papers: sites "
          f"{sum(int(landed[a]['ruwe_sites']) for a in frame)}  "
          f"papers listing 1.4 "
          f"{sum(1 for a in frame if '1.4' in landed[a]['ruwe_values'].split('|'))}")
    print("\npublished at tick 21: sites 803, at 1.4: 393 in 187 papers")
    print("landed CSV / tick-35 re-run: sites 810, at 1.4: 397 in 187 papers\n")

    mod = load_tick21()
    results = []
    per_none = None
    for name, fn in RULES:
        per = run(mod, corpus, fn)
        if fn is rule_none:
            per_none = per
        results.append(report(name, per))

    # --- D1: does run 1 reproduce the landed table paper by paper?
    disagree = [a for a in corpus
                if len(per_none[a]) != int(landed[a]["ruwe_sites"])]
    print(f"\nD1 per-paper site counts against the landed table: "
          f"{len(disagree)} disagreements" + (f" {disagree[:12]}" if disagree else ""))

    # --- which sites a rule removes, when one does
    for name, fn in RULES[1:]:
        per = run(mod, corpus, fn)
        lost = {a: len(per_none[a]) - len(per[a]) for a in corpus
                if len(per[a]) != len(per_none[a])}
        lost14 = {a: (sum(1 for s in per_none[a] if s["value"] == "1.4")
                      - sum(1 for s in per[a] if s["value"] == "1.4"))
                  for a in corpus}
        lost14 = {a: v for a, v in lost14.items() if v}
        print(f"\n{name}: papers losing sites {len(lost)} -> {lost}")
        print(f"{' ' * len(name)}  of them at 1.4: {sum(lost14.values())} -> {lost14}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"frame": len(frame), "corpus": len(corpus), "drift": drift,
                       "published_tick21": {"sites": 803, "focus_sites": 393,
                                            "focus_papers": 187},
                       "landed_csv": {"sites": 810, "focus_sites": 397,
                                      "focus_papers": 187},
                       "runs": results, "d1_disagreements": disagree}, fh, indent=1)
        print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    main()
