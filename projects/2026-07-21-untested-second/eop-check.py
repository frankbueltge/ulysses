#!/usr/bin/env python3
"""Test the score's sign-reading conjecture against the primary data (T-002).

Inputs (public, fetched 2026-07-21, not committed — see SCORE §7 trace policy):
  eopc04.txt        IERS EOP 20 C04 series, daily UT1-UTC since 1962
                    https://datacenter.iers.org/data/latestVersion/EOP_20_C04_one_file_1962-now.txt
  leap-seconds.list IERS/Paris Obs. canonical leap-second table (NTP epoch)
                    https://hpiers.obspm.fr/iers/bul/bulc/ntp/leap-seconds.list
  finals.all.txt    IERS Bulletin A combined series (closes the C04 latency gap;
                    measured values flagged 'I' only, predictions excluded)
                    https://datacenter.iers.org/data/latestVersion/finals.all.iau2000.txt

Questions (SCORE §2, "not yet determined"):
  1. Do positive leap seconds historically fire near the NEGATIVE excursions of
     UT1-UTC (so that Bulletin A's predicted downward drift moves AWAY from the
     never-executed negative leap second, which would fire near the positive bound)?
  2. What is the closest approach UT1-UTC has ever made to the positive side
     (the untested trigger) since 1972 — and when?
  3. Post-2020 "fast Earth" era: has UT1-UTC peaked, and where does it stand now?
     (C04 alone answers this wrongly — it ends months before the present; the
     finals.all gap check is load-bearing.)

Usage: python3 eop-check.py <eopc04.txt> <leap-seconds.list> <finals.all.txt>
"""
import sys
from datetime import date, timedelta

NTP_EPOCH = date(1900, 1, 1)

def load_eop(path):
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            p = line.split()
            y, m, d = int(p[0]), int(p[1]), int(p[2])
            rows.append((date(y, m, d), float(p[7])))  # UT1-UTC(s) is column 8
    return rows

def load_leaps(path):
    steps = []  # (effective date, new TAI-UTC)
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            p = line.split()
            steps.append((NTP_EPOCH + timedelta(seconds=int(p[0]) // 86400 * 86400), int(p[1])))
    return steps

def main():
    eop = load_eop(sys.argv[1])
    leaps = load_leaps(sys.argv[2])
    by_date = dict(eop)

    print("Q1  Each leap-second event: UT1-UTC on the eve vs. the day it takes effect")
    print(f"    table: initial TAI-UTC = {leaps[0][1]} s at {leaps[0][0]}; "
          f"{len(leaps) - 1} steps, all +1: {all(b[1] - a[1] == 1 for a, b in zip(leaps, leaps[1:]))}")
    eves = []
    for eff, _ in leaps[1:]:
        eve, day = by_date.get(eff - timedelta(days=1)), by_date.get(eff)
        eves.append(eve)
        print(f"    {eff}  eve {eve:+.4f}  day {day:+.4f}  jump {day - eve:+.4f}")
    print(f"    all 27 eves negative: {all(v < 0 for v in eves)}; "
          f"eve range [{min(eves):+.4f}, {max(eves):+.4f}]")

    since72 = [(d, v) for d, v in eop if d >= date(1972, 1, 1)]
    dmax, vmax = max(since72, key=lambda r: r[1])
    dmin, vmin = min(since72, key=lambda r: r[1])
    print(f"\nQ2  Since 1972: max UT1-UTC {vmax:+.6f} s on {dmax} (closest-ever approach to the")
    print(f"    untested positive trigger); min {vmin:+.6f} s on {dmin}")

    recent = [(d, v) for d, v in since72 if d >= date(2020, 1, 1)]
    rdmax, rvmax = max(recent, key=lambda r: r[1])
    print(f"\nQ3  Post-2020 (C04, series ends {recent[-1][0]}): "
          f"max UT1-UTC {rvmax:+.6f} s on {rdmax}")

    gap = load_finals(sys.argv[3], since=recent[-1][0])
    gdmax, gvmax = max(gap, key=lambda r: r[1])
    print(f"    finals.all gap check ({recent[-1][0]}..{gap[-1][0]}, measured only): "
          f"max {gvmax:+.6f} s on {gdmax}")
    print(f"    last measured value {gap[-1][1]:+.6f} s on {gap[-1][0]}")
    overall = max(rvmax, gvmax)
    od = rdmax if rvmax >= gvmax else gdmax
    print(f"    => fast-Earth-era closest free-drift approach to the untested trigger: "
          f"{overall:+.6f} s on {od}")

def load_finals(path, since):
    # finals.all fixed width: cols 1-6 YYMMDD; col 58 I/P flag for UT1-UTC; cols 59-68 value
    rows = []
    with open(path) as f:
        for line in f:
            if len(line) < 68:
                continue
            try:
                yy, mm, dd = int(line[0:2]), int(line[2:4]), int(line[4:6])
            except ValueError:
                continue
            year = 2000 + yy if yy < 73 else 1900 + yy
            s = line[58:68].strip()
            if not s or line[57] != "I":
                continue
            d = date(year, mm, dd)
            if d >= since:
                rows.append((d, float(s)))
    return rows

if __name__ == "__main__":
    main()
