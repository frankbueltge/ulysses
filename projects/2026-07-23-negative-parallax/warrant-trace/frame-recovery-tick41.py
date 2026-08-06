#!/usr/bin/env python3
"""Frame recovery — tick 41 of the work-line `2026-07-23-negative-parallax`.

Question (PREREGISTRATION-tick41.md, written before this ran): frames A and B of the
episode were built from a NAMED, re-derivable source (OpenCitations Index API v2, citations
of one DOI each) UNION an unnamed second index, with an unnamed DOI->arXiv resolver. How
much of the landed 599-member frame does the named source alone account for today — and do
the episode's own numbers survive on that part alone?

What this does NOT do: it does not re-derive frames A and B. The union partner and the
resolver stay unnamed and unreconstructed; a third party rebuilding the frame would still
need a resolver and would meet a drifted index. This script makes the *named* step
re-runnable code and measures the residue the named step leaves.

Steps:
  1. GET the OpenCitations Index API v2 citation list of each cited DOI; land every
     citing DOI with the retrieval record (url, utc, http status, sha256 of the body,
     record count). No source text is redistributed; OpenCitations data is CC0.
  2. Mark each landed frame member recovered / not-recovered against today's list for
     its own frame (DOIs compared lowercased).
  3. Recompute, over the recovered members only, what the exposition states: for RUWE
     1.4 the measured denominator, the papers carrying the focus value, and the papers
     naming the deriving technical note; the same shape for UWE 1.25; and the
     site-level hand-reading of case 2 restricted to recovered papers.

Usage:  python3 frame-recovery-tick41.py [--outdir DIR]
Outputs (in --outdir, default: this script's directory):
  oc-citations-tick41.jsonl        citing DOIs as retrieved today, one per line
  frame-recovery-tick41.csv        per landed member: frame, arxiv, doi, recovered
  frame-recovery-tick41.json       retrieval record, Q1/Q2/Q3 quantities, defeat verdicts
"""
import argparse, csv, hashlib, json, os, sys, time, urllib.request
from datetime import datetime, timezone

API = "https://api.opencitations.net/index/v2/citations/doi:{doi}"

# The two cited DOIs, as recorded in PREREGISTRATION-tick19.md and the docstring of
# circulation-measure.py. Frame letters are the ones the landed table uses.
CITED = {
    "A": "10.1051/0004-6361/202039834",   # Fabricius et al. 2021, A&A 649, A5
    "B": "10.1093/mnras/stab323",          # El-Badry, Rix & Heintz 2021, MNRAS 506, 2269
}

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)

# Pre-registered defeat conditions. Not editable after the fact without the record showing it.
D1_MIN_RECOVERY = 0.90          # r_union below this -> D1 fires
D2_MAX_NAMING_RATE = 0.05       # naming rate among focus-carrying papers above this -> D2 fires
D2_MAX_USE_RATE_SHIFT = 0.10    # use-rate shift in absolute percentage points -> D2 fires


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(doi):
    """Return (records, retrieval_record). Raises on anything that is not a clean 200."""
    url = API.format(doi=doi)
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "warrant-trace/frame-recovery-tick41"})
    started = utcnow()
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        status = r.status
        final_url = r.url
    rec = {
        "cited_doi": doi,
        "requested_url": url,
        "final_url": final_url,
        "http_status": status,
        "fetched_utc": started,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    data = json.loads(body.decode("utf-8"))
    rec["records"] = len(data)
    return data, rec


def citing_doi(entry):
    """Pull the doi: token out of an OpenCitations v2 'citing' identifier string."""
    for tok in entry.get("citing", "").split():
        if tok.startswith("doi:"):
            return tok[4:].strip().lower()
    return None


def load_landed():
    """The landed frame: frame letter, arXiv id, DOI (circulation-measure.csv, tick 19)."""
    rows = []
    with open(os.path.join(PROJ, "circulation-measure.csv")) as fh:
        for r in csv.DictReader(fh):
            rows.append({"frame": r["frame"], "arxiv": r["arxiv"],
                         "doi": (r["doi"] or "").strip().lower(), "year": r["year"]})
    return rows


def read_measure(fname, focus, naming_flag):
    """Landed per-paper table -> {arxiv: {carries_focus, names_deriving, measured}}."""
    out = {}
    with open(os.path.join(HERE, fname)) as fh:
        for r in csv.DictReader(fh):
            measured = r["state"] == "measured"
            values = (r.get("values") or "").split("|")
            out[r["arxiv"]] = {
                "measured": measured,
                "carries_focus": measured and focus in values,
                "names_deriving": r.get(naming_flag) == "1",
            }
    return out


def tally(measure, keep=None):
    """Counts over the whole table, or over `keep` (a set of arXiv ids)."""
    ids = [a for a in measure if keep is None or a in keep]
    measured = [a for a in ids if measure[a]["measured"]]
    focus = [a for a in measured if measure[a]["carries_focus"]]
    naming = [a for a in focus if measure[a]["names_deriving"]]
    return {
        "in_frame": len(ids),
        "measured": len(measured),
        "carrying_focus": len(focus),
        "naming_deriving_document": len(naming),
        "use_rate": (len(focus) / len(measured)) if measured else None,
        "naming_rate": (len(naming) / len(focus)) if focus else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=HERE)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # 1. the named step, as code
    retrieval, citing = [], {}
    for frame, doi in CITED.items():
        data, rec = fetch(doi)
        rec["frame"] = frame
        retrieval.append(rec)
        citing[frame] = data
        print(f"frame {frame}: {rec['records']} citation records for {doi}", file=sys.stderr)
        time.sleep(2)

    jl = os.path.join(args.outdir, "oc-citations-tick41.jsonl")
    sets = {}
    with open(jl, "w") as fh:
        for frame, data in citing.items():
            s = set()
            for e in data:
                d = citing_doi(e)
                if d:
                    s.add(d)
                fh.write(json.dumps({"frame": frame, "cited_doi": CITED[frame],
                                     "citing_doi": d, "oci": e.get("oci"),
                                     "creation": e.get("creation")}) + "\n")
            sets[frame] = s

    # 2. recovery of the landed membership
    landed = load_landed()
    recovered_ids, per_frame = set(), {}
    with open(os.path.join(args.outdir, "frame-recovery-tick41.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["frame", "arxiv", "doi", "year", "recovered_in_own_frame", "recovered_in_either"])
        for row in landed:
            own = bool(row["doi"]) and row["doi"] in sets.get(row["frame"], set())
            either = bool(row["doi"]) and any(row["doi"] in s for s in sets.values())
            if own:
                recovered_ids.add(row["arxiv"])
            per_frame.setdefault(row["frame"], {"landed": 0, "with_doi": 0, "recovered": 0})
            per_frame[row["frame"]]["landed"] += 1
            per_frame[row["frame"]]["with_doi"] += 1 if row["doi"] else 0
            per_frame[row["frame"]]["recovered"] += 1 if own else 0
            w.writerow([row["frame"], row["arxiv"], row["doi"], row["year"],
                        int(own), int(either)])

    landed_dois = {r["doi"] for r in landed if r["doi"]}
    not_in_landed = {f: sorted(s - landed_dois) for f, s in sets.items()}

    # the residue itself, member by member: what the named source does not return today.
    residue = [{"frame": r["frame"], "arxiv": r["arxiv"], "doi": r["doi"] or None,
                "year": r["year"]}
               for r in landed
               if not (r["doi"] and r["doi"] in sets.get(r["frame"], set()))]
    residue_years = {}
    for m in residue:
        residue_years[m["year"]] = residue_years.get(m["year"], 0) + 1
    # citations returned today but absent from the landed frame, by publication year of the
    # citing work (OpenCitations 'creation'). This mixes index growth with works the unnamed
    # resolver could not map to arXiv; nothing here separates the two.
    drift_years = {}
    for frame, dois in not_in_landed.items():
        for e in citing[frame]:
            d = citing_doi(e)
            if d in set(dois):
                y = (e.get("creation") or "?")[:4]
                drift_years.setdefault(frame, {})
                drift_years[frame][y] = drift_years[frame].get(y, 0) + 1

    n_landed = len(landed)
    n_recovered_unique = len({r["arxiv"] for r in landed
                              if r["doi"] and r["doi"] in sets.get(r["frame"], set())})
    r_union = n_recovered_unique / n_landed

    # 3. the episode's own numbers, whole frame and recovered sub-frame
    ruwe = read_measure("measure-ruwe-1.4-tick35.csv", "1.4", "flag_cite_tn")
    uwe = read_measure("measure-uwe-1.25-tick35.csv", "1.25", "flag_cite_paper_i_id")
    q2 = {"whole_frame": tally(ruwe), "recovered_sub_frame": tally(ruwe, recovered_ids)}
    q3 = {"whole_frame": tally(uwe), "recovered_sub_frame": tally(uwe, recovered_ids)}

    # case 2 hand-reading, restricted
    hand_path = os.path.join(HERE, "handread-uwe-1.25-tick35.csv")
    hand = {"whole_frame": {"sites": 0, "papers": set()},
            "recovered_sub_frame": {"sites": 0, "papers": set()}}
    hand_docs = {"whole_frame": {}, "recovered_sub_frame": {}}
    with open(hand_path) as fh:
        for r in csv.DictReader(fh):
            doc = (r.get("hand_document") or "").split("—")[0].strip() or "(blank)"
            for key in ("whole_frame", "recovered_sub_frame"):
                if key == "recovered_sub_frame" and r["arxiv"] not in recovered_ids:
                    continue
                hand[key]["sites"] += 1
                hand[key]["papers"].add(r["arxiv"])
                hand_docs[key][doc] = hand_docs[key].get(doc, 0) + 1
    for key in hand:
        hand[key]["papers"] = len(hand[key]["papers"])
        hand[key]["by_document"] = hand_docs[key]

    # defeat conditions, evaluated exactly as pre-registered
    sub = q2["recovered_sub_frame"]
    whole = q2["whole_frame"]
    d2_naming = (sub["naming_rate"] is not None and sub["naming_rate"] > D2_MAX_NAMING_RATE)
    d2_use = (sub["use_rate"] is not None and whole["use_rate"] is not None
              and abs(sub["use_rate"] - whole["use_rate"]) > D2_MAX_USE_RATE_SHIFT)

    result = {
        "tick": 41,
        "written_utc": utcnow(),
        "preregistration": "PREREGISTRATION-tick41.md",
        "retrieval": retrieval,
        "q1_recovery": {
            "landed_members": n_landed,
            "recovered_in_own_frame": n_recovered_unique,
            "r_union": round(r_union, 4),
            "per_frame": {f: dict(v, rate=round(v["recovered"] / v["landed"], 4))
                          for f, v in per_frame.items()},
            "returned_today_not_in_landed_frame": {f: len(v) for f, v in not_in_landed.items()},
            "returned_today_not_in_landed_frame_by_citing_year": drift_years,
            "residue_members": residue,
            "residue_by_arxiv_year": residue_years,
        },
        "q2_ruwe_1_4": q2,
        "q3_uwe_1_25": dict(q3, hand_reading=hand),
        "defeat": {
            "D1_recovery_below_0.90": r_union < D1_MIN_RECOVERY,
            "D2_naming_rate_above_0.05": d2_naming,
            "D2_use_rate_shift_above_0.10": d2_use,
        },
    }
    out = os.path.join(args.outdir, "frame-recovery-tick41.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=False)
    print(json.dumps(result["q1_recovery"], indent=2))
    print(json.dumps(result["q2_ruwe_1_4"], indent=2))
    print(json.dumps(result["defeat"], indent=2))


if __name__ == "__main__":
    main()
