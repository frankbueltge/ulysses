#!/usr/bin/env python3
"""An excess-power blind search over a corpus of dated session records.

WHAT THIS IS. A transposition, made deliberately and reported as one, of the
excess power statistic for gravitational-wave burst detection:

    W. G. Anderson, P. R. Brady, J. D. E. Creighton and E. E. Flanagan,
    "An excess power statistic for detection of burst sources of gravitational
    radiation", Phys. Rev. D 63, 042003 (2001); arXiv:gr-qc/0008066.

That method exists for one reason: to find signals whose waveform is not known
in advance. Matched filtering needs a template; where no template can be
computed the paper's authors sum the data power inside a time-frequency window
and ask whether it exceeds what the detector's own noise would produce. "These
methods are often called 'blind search' methods" (§I A).

The transposition, term by term:

    detector strain h(t)      ->  a practice's session records, one per day
    sample                    ->  one active day of the record
    frequency channel         ->  one term of a shared vocabulary
    noise spectrum S(f)       ->  each term's own mean and variance in that
                                  practice's record (its baseline chatter)
    whitening                 ->  z = (rate - mean) / sd, per practice, per term
    excess power in a tile    ->  sum of z^2 over a block of days x a band
    chi-squared threshold     ->  the same, with the degrees of freedom changed
                                  (see DEGREES OF FREEDOM below)
    detector network          ->  three machine practices in one house, whose
                                  records are written independently and cover
                                  the same days

WHAT IS NOT FAITHFUL, stated up front because a transposition that hides its
seams is decoration:

1.  DEGREES OF FREEDOM. The paper's tile of duration dt and bandwidth df has
    2*dt*df degrees of freedom, because each Fourier bin carries a real and an
    imaginary part (§I B). A term-count pixel carries one real number. So the
    null here is chi-squared with V = (active pixels) degrees of freedom, not
    2V. Halving the paper's number is the whole of the change.

2.  THE FREQUENCY AXIS IS A CONVENTION, NOT A PHYSICS. In a detector, "band"
    means an interval of a real ordered quantity; adjacent channels are
    genuinely adjacent. Terms have no such order. This tool orders channels by
    document frequency across the union corpus (rare to common), so that a band
    is an interval of rarity -- and then runs the entire search again with the
    channels in alphabetical order, as a control. An event that survives both
    orderings is not an artefact of the ordering. An event that does not is
    reported as ordering-dependent and no more.

3.  NO GAUSSIANITY IS CLAIMED. The paper's chi-squared threshold assumes
    stationary Gaussian noise and says plainly that real noise is not
    ("Real detector noise will contain significant non-Gaussian components",
    §I A). Term rates are certainly not Gaussian. The chi-squared p-value here
    is therefore a RANKING STATISTIC, not a probability of anything, and it is
    labelled as such wherever it is printed. The paper's own remark is the one
    to keep: a blind search "will likely be a useful tool for characterizing and
    investigating the non-Gaussian components of the noise" -- that is, it finds
    the instrument before it finds the sky.

4.  THE SIGNAL IS ONE-SIDED. Strain is signed and symmetric about zero, so a
    trough carries as much power as a crest and summing z^2 is the right thing
    to do. A term rate is bounded below by zero: a word can be arbitrarily more
    frequent than usual and cannot be less than absent. Measured on this house's
    records, not one of the 1,664 pixels reaching two standard deviations was a
    deficit. The statistic is built to hear a silence as loudly as a shout, and
    here it never gets the chance.

WHAT REPLACES THE PAPER'S THRESHOLD. Because of (3), the chi-squared cut is
computed and reported but never believed. The cut that decides anything here is
measured: the order of a record's active days is shuffled, the entire search is
re-run, and the loudest tile is recorded; 200 times over, that gives the
distribution of the loudest-thing-you-find-by-chance in this particular record,
and its fifth percentile is the threshold. The shuffle keeps every day's
composition and every term's distribution across days, and destroys only
temporal contiguity -- which is what a burst is.

Its blind spot is exact and is reported with every run: shuffling day order
leaves every single-day tile untouched, so a one-day event is present unchanged
in every shuffled copy and can never be significant under this test. The
procedure preserves precisely what it cannot judge.

Usage:
    python3 tools/burst/burst.py --out run.json
    python3 tools/burst/burst.py --order alpha --out run-alpha.json
    python3 tools/burst/burst.py --baseline local --window 15 --out run-local.json
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# --- the three detectors ------------------------------------------------------
# One kind of unit in all three: the session record a machine practice writes
# when it closes a session. Not its works, not its protocol -- the log.
DETECTORS = [
    {"key": "atelier", "name": "The Atelier", "repo": "/home/user/ulysses", "dir": "journal"},
    {"key": "nightly", "name": "the nightly line", "repo": "/home/user/error-as-method", "dir": "journal"},
    {"key": "remainder", "name": "Remainder", "repo": "/home/user/n-1", "dir": "nights"},
]

# Durations, in ACTIVE days (a day on which that practice wrote). Gaps are
# closed up rather than filled with zeros: a detector that is off is not a
# detector reading zero. The paper's duty-cycle problem, handled the blunt way.
DURATIONS = [1, 2, 3, 5, 8, 13]
BANDWIDTHS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

MIN_DF = 8          # a term must appear in at least this many units to be a channel
MAX_CHANNELS = 512  # keep the tiling tractable and the plane readable
P_CUT = 0.01        # threshold on the trials-corrected ranking statistic
OVERLAP_CUT = 0.25  # cluster: reject a tile sharing more than this with a kept one

TOKEN = re.compile(r"[a-zà-öø-ÿ][a-zà-öø-ÿ'’-]{2,}", re.UNICODE)

# Function words in the three languages the house's records actually contain.
# Deliberately short: a stoplist that removes topic words removes the finding.
STOP = set("""
the and that with for this not are was were has have had but its it's from all any can
which what when where who whom whose why how than then there their they them these those
you your yours our ours his her hers him she out into over under about after before more
most other some such only own same too very just also because been being both each few
itself myself ourselves does did doing done else ever every here now once said
say says see seen shall should since still take taken tell
und der die das dass mit den dem des ein eine einer eines einem einen nicht auch noch
wird werden wurde wurden sein seine seiner ist sind war waren haben hat hatte hatten
aber oder wenn dann dort hier sich sie ihr ihre ihren ihrem als auf aus bei bis durch
für gegen ohne über unter vor zwischen zum zur vom beim ich wir man kann muss soll nur
schon sehr mehr wie was wer wo warum weil damit dazu dabei diese dieser dieses diesem
""".split())


# --- reading the corpora ------------------------------------------------------
ISO = re.compile(r"(20\d\d-[01]\d-[0-3]\d)")


def unit_date(rel: str, head: str, added: str | None) -> tuple[str, str] | None:
    """The day a record says of itself it was written, by a fixed precedence.

    1. the filename, where it opens with a date (the Atelier's and the nightly
       line's session logs);
    2. the first ISO date in the record's opening lines (Remainder numbers its
       nights and dates them in the heading);
    3. the commit that added the file.

    The first pass of this instrument used (3) alone, for uniformity, and it
    collapsed: 166 Atelier logs landed on 10 days, because a repository that has
    been forked adds its whole history in a handful of commits. A commit date is
    the date of a copy, not of a night. The precedence above is disclosed here
    and reported per detector in the run.
    """
    name = Path(rel).name
    m = ISO.match(name)
    if m:
        return m.group(1), "filename"
    m = ISO.search(head)
    if m:
        return m.group(1), "heading"
    if added:
        return added, "commit"
    return None


def git_add_dates(repo: str, subdir: str) -> dict[str, str]:
    """Date on which each file under subdir was first committed — the fallback."""
    out = subprocess.run(
        ["git", "-C", repo, "log", "--reverse", "--diff-filter=A",
         "--format=C%ad", "--date=short", "--name-only", "--", subdir],
        capture_output=True, text=True, check=True,
    ).stdout
    dates: dict[str, str] = {}
    cur = None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("C") and len(line) == 11 and line[1:5].isdigit():
            cur = line[1:]
        elif cur and line.startswith(subdir + "/"):
            dates.setdefault(line, cur)   # first add wins; a later rename does not move it
    return dates


def provenance(repo: str, subdir: str) -> dict:
    """Which state of the record was measured.

    A practice that searches its own log is inside its own data: the session
    that runs this instrument will, when it closes, add a record to the corpus
    the instrument just measured. That cannot be avoided, only pinned. Each run
    records the commit the repository stood at and whether the measured
    directory had uncommitted changes, so a reading can be repeated exactly.
    """
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                              text=True).stdout.strip()
    return {"head": git("rev-parse", "HEAD")[:12],
            "dirty": bool(git("status", "--porcelain", "--", subdir))}


def strip_markup(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)      # fenced code
    text = re.sub(r"`[^`]*`", " ", text)                     # inline code
    text = re.sub(r"https?://\S+", " ", text)                # bare URLs
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)     # links keep their words
    text = re.sub(r"[#*_>|\-]{1,}", " ", text)
    return text


def read_detector(det: dict) -> dict:
    repo, subdir = det["repo"], det["dir"]
    added = git_add_dates(repo, subdir)
    units, sources = [], Counter()
    for path in sorted((Path(repo) / subdir).rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".markdown"}:
            continue
        rel = str(path.relative_to(repo))
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        dated = unit_date(rel, "\n".join(raw.splitlines()[:6]), added.get(rel))
        if dated is None:
            continue
        date, how = dated
        toks = TOKEN.findall(strip_markup(raw).lower())
        toks = [t for t in toks if t not in STOP]
        if len(toks) < 40:      # a stub is not a session record
            continue
        sources[how] += 1
        units.append({"path": rel, "date": date, "tokens": toks})
    units.sort(key=lambda u: (u["date"], u["path"]))
    return {**det, "units": units, "date_sources": dict(sources),
            "provenance": provenance(repo, subdir)}


# --- the statistic ------------------------------------------------------------
def log_chi2_sf(x: float, k: int) -> float:
    """log10 of the upper tail of chi-squared(k) at x. Numerical Recipes §6.2.

    Returned in logs because the tiles are large and the tails are far out; a
    float underflows long before the ranking stops being informative.
    """
    if x <= 0:
        return 0.0
    a, xx = k / 2.0, x / 2.0
    if xx < a + 1.0:                      # series for the lower tail, then complement
        term = 1.0 / a
        total = term
        n = a
        for _ in range(10000):
            n += 1.0
            term *= xx / n
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
        log_p = math.log(total) - xx + a * math.log(xx) - math.lgamma(a)
        p = math.exp(log_p) if log_p > -700 else 0.0
        q = 1.0 - p
        return math.log10(q) if q > 0 else -300.0
    # continued fraction for the upper tail
    tiny = 1e-300
    b = xx + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    log_q = math.log(h) - xx + a * math.log(xx) - math.lgamma(a)
    return log_q / math.log(10.0)


def whiten(det: dict, channels: list[str], baseline: str = "global",
           window: int = 15) -> dict:
    """Bin units into active days, take term rates, and whiten per channel.

    The whitening is per detector: each practice's own baseline is its own noise
    spectrum. A term that one practice says every night is that practice's
    noise, however loud it would be in another.
    """
    by_day: dict[str, Counter] = defaultdict(Counter)
    totals: Counter = Counter()
    units_per_day: Counter = Counter()
    for u in det["units"]:
        by_day[u["date"]].update(u["tokens"])
        totals[u["date"]] += len(u["tokens"])
        units_per_day[u["date"]] += 1

    days = sorted(by_day)
    idx = {c: i for i, c in enumerate(channels)}
    rates = [[by_day[d][c] / totals[d] for c in channels] for d in days]

    n, m = len(days), len(channels)

    def moments(col: list[float]) -> tuple[float, float]:
        mean = sum(col) / len(col)
        var = sum((x - mean) ** 2 for x in col) / max(1, len(col) - 1)
        return mean, math.sqrt(var)

    cols = [[rates[j][k] for j in range(n)] for k in range(m)]
    glob = [moments(c) for c in cols]
    live = [k for k in range(m) if glob[k][1] > 0]

    if baseline == "global":
        z = [[(rates[j][k] - glob[k][0]) / glob[k][1] if glob[k][1] > 0 else 0.0
              for k in range(m)] for j in range(n)]
    else:
        # A running local baseline, the way a burst pipeline estimates its noise
        # spectrum from the data around the sample rather than from the whole
        # run. The day under test is left out of its own baseline. The cost is
        # named rather than hidden: a baseline of half-width W cannot tell a
        # burst longer than about W from a change of level. That is precisely
        # the ambiguity this control exists to expose.
        z = []
        for j in range(n):
            lo, hi = max(0, j - window), min(n, j + window + 1)
            row = []
            for k in range(m):
                near = cols[k][lo:j] + cols[k][j + 1:hi]
                if len(near) < 10:
                    mu_k, sd_k = glob[k]
                else:
                    mu_k, sd_k = moments(near)
                    if sd_k <= 0:
                        sd_k = glob[k][1]
                row.append((rates[j][k] - mu_k) / sd_k if sd_k > 0 else 0.0)
            z.append(row)
    return {"days": days, "z": z, "live": set(live), "idx": idx,
            "tokens_per_day": {d: totals[d] for d in days},
            "units_per_day": dict(units_per_day)}


def scan(z: list[list[float]], live: set[int], m: int, best_only: bool = False,
         keep_cut: float = 0.0):
    """Every concordant tile. The paper's step 7: repeat for all allowable
    choices of start time, duration, start frequency and bandwidth.

    With best_only, returns just the loudest tile's log10 p and the tile count —
    which is all a permutation of the day axis needs to contribute.
    """
    n = len(z)
    if n == 0:
        return ([], 0) if not best_only else (0.0, 0)

    # running sums of z^2 down the day axis, per channel: tile power in O(1)
    cum = [[0.0] * (m + 1)]
    for j in range(n):
        row = cum[-1]
        cum.append([row[k] + (z[j][k] ** 2 if k in live else 0.0) for k in range(m)] + [0.0])
    # prefix along the channel axis of each running row
    pre = []
    for j in range(n + 1):
        r, s = [0.0], 0.0
        for k in range(m):
            s += cum[j][k]
            r.append(s)
        pre.append(r)

    live_pre = [0]
    s = 0
    for k in range(m):
        s += 1 if k in live else 0
        live_pre.append(s)

    tiles = []
    trials = 0
    best = 0.0
    for dt in DURATIONS:
        if dt > n:
            continue
        for df in BANDWIDTHS:
            if df > m:
                continue
            step_t = max(1, dt // 2)
            step_f = max(1, df // 2)
            for j0 in range(0, n - dt + 1, step_t):
                for k0 in range(0, m - df + 1, step_f):
                    v = (live_pre[k0 + df] - live_pre[k0]) * dt
                    if v < 1:
                        continue
                    p = (pre[j0 + dt][k0 + df] - pre[j0 + dt][k0]
                         - pre[j0][k0 + df] + pre[j0][k0])
                    trials += 1
                    if p <= v:                     # no excess at all
                        continue
                    lp = log_chi2_sf(p, v)
                    if best_only:
                        if lp < best:
                            best = lp
                        continue
                    if lp < keep_cut:
                        tiles.append({"j0": j0, "dt": dt, "k0": k0, "df": df,
                                      "power": p, "dof": v, "log10p": lp})
    if best_only:
        return best, trials
    tiles.sort(key=lambda t: t["log10p"])
    return tiles, trials


def cluster(tiles: list[dict], cut: float, limit: int = 25) -> list[dict]:
    """Keep the loudest tile of each overlapping family above the cut.

    Not from the paper — clustering is what burst pipelines add around it, and
    it is named here as this instrument's own addition, not a borrowed step.
    """
    kept: list[dict] = []
    for t in tiles:
        if t["log10p"] >= cut:
            break
        ok = True
        for u in kept:
            ot = max(0, min(t["j0"] + t["dt"], u["j0"] + u["dt"]) - max(t["j0"], u["j0"]))
            of = max(0, min(t["k0"] + t["df"], u["k0"] + u["df"]) - max(t["k0"], u["k0"]))
            inter = ot * of
            union = t["dt"] * t["df"] + u["dt"] * u["df"] - inter
            if union and inter / union > OVERLAP_CUT:
                ok = False
                break
        if ok:
            kept.append(t)
        if len(kept) >= limit:
            break
    return kept


def permutation_null(plane: dict, m: int, n_perm: int, seed: int) -> dict:
    """The threshold the paper's chi-squared cannot supply here.

    The analytic cut assumes stationary Gaussian noise. Term rates are neither,
    and the first run of this instrument showed what that costs: with the
    chi-squared cut the search called a large fraction of the record
    significant. So the null is measured instead of assumed. Each trial shuffles
    the ORDER of a detector's active days and re-runs the whole search. That
    keeps every day's composition and every term's distribution across days
    intact and destroys only temporal contiguity -- which is precisely what a
    burst is. The loudest tile of each shuffled record gives a distribution of
    the loudest-thing-you-find-by-chance; the 5th percentile of it is the cut.
    """
    rng = random.Random(seed)
    rows = list(plane["z"])
    loudest = []
    for _ in range(n_perm):
        rng.shuffle(rows)
        best, _tr = scan(rows, plane["live"], m, best_only=True)
        loudest.append(best)
    loudest.sort()                      # most negative = loudest
    k = max(0, int(0.05 * n_perm) - 1)  # family-wise 0.05 over the whole search
    return {"n_perm": n_perm, "cut_log10p": loudest[k],
            "median_log10p": loudest[n_perm // 2],
            "loudest_log10p": loudest[0],
            "quietest_log10p": loudest[-1],
            "all_log10p": [round(v, 2) for v in loudest]}


def describe(event: dict, plane: dict, channels: list[str]) -> dict:
    """Name an event by the days it covers and the channels carrying its power."""
    days = plane["days"][event["j0"]:event["j0"] + event["dt"]]
    z = plane["z"]
    contrib = []
    for k in range(event["k0"], event["k0"] + event["df"]):
        if k not in plane["live"]:
            continue
        power = sum(z[j][k] ** 2 for j in range(event["j0"], event["j0"] + event["dt"]))
        signed = sum(z[j][k] for j in range(event["j0"], event["j0"] + event["dt"]))
        contrib.append((power, channels[k], 1 if signed >= 0 else -1))
    contrib.sort(reverse=True)
    share = sum(c[0] for c in contrib[:5]) / event["power"] if event["power"] else 0.0
    return {
        **event,
        "day_first": days[0], "day_last": days[-1],
        "top_terms": [{"term": t, "power": round(p, 1), "sign": s} for p, t, s in contrib[:8]],
        "top5_share": round(share, 4),
    }


# --- coincidence --------------------------------------------------------------
def coincidences(events: dict[str, list[dict]]) -> list[dict]:
    """Two detectors, one sky. The paper's reason for a network (§I A, §V).

    A single detector cannot tell a noise burst from a signal. Two records that
    burst on the same days, in the same band, are at least not each other's
    private artefact -- which is all a coincidence ever establishes.
    """
    out = []
    keys = sorted(events)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            for ea in events[a]:
                for eb in events[b]:
                    if ea["day_last"] < eb["day_first"] or eb["day_last"] < ea["day_first"]:
                        continue
                    band = max(0, min(ea["k0"] + ea["df"], eb["k0"] + eb["df"])
                               - max(ea["k0"], eb["k0"]))
                    shared = sorted({t["term"] for t in ea["top_terms"]}
                                    & {t["term"] for t in eb["top_terms"]})
                    out.append({
                        "a": a, "b": b,
                        "a_rank": events[a].index(ea) + 1, "b_rank": events[b].index(eb) + 1,
                        "days": [max(ea["day_first"], eb["day_first"]),
                                 min(ea["day_last"], eb["day_last"])],
                        "band_overlap": band, "shared_terms": shared,
                    })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", choices=["df", "alpha"], default="df",
                    help="channel ordering: by document frequency (default) or alphabetical")
    ap.add_argument("--baseline", choices=["global", "local"], default="global",
                    help="noise estimated over the whole record, or in a sliding window")
    ap.add_argument("--window", type=int, default=15,
                    help="half-width, in active days, of the local baseline")
    ap.add_argument("--perms", type=int, default=200,
                    help="permutations of the day order used to measure the null")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    dets = [read_detector(d) for d in DETECTORS]
    for d in dets:
        if not d["units"]:
            print(f"burst: {d['key']} has no readable units — refusing to run", file=sys.stderr)
            raise SystemExit(3)

    # one vocabulary for all three: coincidence is only meaningful in a shared band
    df_count: Counter = Counter()
    for d in dets:
        for u in d["units"]:
            df_count.update(set(u["tokens"]))
    vocab = [t for t, c in df_count.items() if c >= MIN_DF]
    vocab.sort(key=lambda t: (df_count[t], t))            # rare -> common
    channels = vocab[-MAX_CHANNELS:] if len(vocab) > MAX_CHANNELS else vocab
    if args.order == "alpha":
        channels = sorted(channels)

    planes, events, stats = {}, {}, {}
    m = len(channels)
    for d in dets:
        pl = whiten(d, channels, args.baseline, args.window)
        planes[d["key"]] = pl

        # 1. the paper's threshold, applied literally: chi-squared, Bonferroni
        #    over every tile the search visits.
        _b, trials = scan(pl["z"], pl["live"], m, best_only=True)
        analytic = math.log10(P_CUT) - math.log10(max(1, trials))
        tiles, _ = scan(pl["z"], pl["live"], m, keep_cut=analytic)

        # 2. the threshold this record's own noise actually asks for.
        null = permutation_null(pl, m, args.perms, seed=args.seed)
        cut = null["cut_log10p"]
        if cut > analytic:                       # empirical is the looser of the two
            tiles, _ = scan(pl["z"], pl["live"], m, keep_cut=cut)

        ev = cluster(tiles, cut)
        events[d["key"]] = [describe(e, pl, channels) for e in ev]
        stats[d["key"]] = {
            "tiles_searched": trials,
            "analytic_cut_log10p": round(analytic, 3),
            "tiles_over_analytic_cut": sum(1 for t in tiles if t["log10p"] < analytic),
            "events_over_analytic_cut": len(cluster(tiles, analytic, limit=10 ** 6)),
            "null": {k: (round(v, 3) if isinstance(v, float) else v)
                     for k, v in null.items() if k != "all_log10p"},
            "null_all_log10p": null["all_log10p"],
            "empirical_cut_log10p": round(cut, 3),
        }

    result = {
        "generated": subprocess.run(["date", "-u", "+%FT%TZ"], capture_output=True,
                                    text=True).stdout.strip(),
        "order": args.order,
        "baseline": args.baseline, "window": args.window,
        "params": {"perms": args.perms, "seed": args.seed, "min_df": MIN_DF, "max_channels": MAX_CHANNELS, "p_cut": P_CUT,
                   "durations": DURATIONS, "bandwidths": BANDWIDTHS,
                   "overlap_cut": OVERLAP_CUT},
        "vocab_size": len(vocab), "channels": channels,
        "detectors": [
            {"key": d["key"], "name": d["name"], "repo": Path(d["repo"]).name,
             "dir": d["dir"], "units": len(d["units"]),
             "active_days": len(planes[d["key"]]["days"]),
             "first_day": planes[d["key"]]["days"][0],
             "last_day": planes[d["key"]]["days"][-1],
             "date_sources": d["date_sources"], "provenance": d["provenance"],
             "live_channels": len(planes[d["key"]]["live"]),
             **stats[d["key"]],
             "events": events[d["key"]]}
            for d in dets
        ],
        "coincidences": coincidences(events),
        "planes": {k: {"days": p["days"],
                       "loud": [[j, kk, round(p["z"][j][kk], 2)]
                                for j in range(len(p["days"]))
                                for kk in range(len(channels))
                                if abs(p["z"][j][kk]) >= 2.0]}
                   for k, p in planes.items()},
    }
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    for d in result["detectors"]:
        print(f"{d['key']:10s} units={d['units']:4d} days={d['active_days']:3d} "
              f"tiles={d['tiles_searched']:8d} chi2-events={d['events_over_analytic_cut']:5d} events={len(d['events'])}")
    print(f"coincidences: {len(result['coincidences'])}  ->  {args.out}")


if __name__ == "__main__":
    main()
