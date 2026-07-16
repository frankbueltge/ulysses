#!/usr/bin/env python3
"""
The Wrong Sphere — channel.py
Ulysses, Session 30, 2026-07-16.

A real Hamming(7,4) single-error-correcting decoder, and its extended
Hamming(8,4) SECDED cousin, run over a real binary symmetric channel. The work
is the decoder's own behaviour past its distance bound: at minimum distance 3
(Hamming 1950, Table V), one bit-flip is corrected and returns the exact word;
TWO bit-flips carry the received word out of the sent codeword's sphere and INTO
a neighbour's, so the decoder — applying the identical nearest-codeword rule —
hands back a clean, valid, WRONG codeword and reports success. It has no state in
which to say "I cannot fix this." Adding one parity bit (SECDED, distance 4) buys
exactly that state: the silent lie becomes an honest refusal.

Everything here is exact and reproducible. The census is exhaustive (no sampling);
the channel sweep is seeded (seed below -> same numbers). git is the archive.

Run: python3 channel.py  ->  writes data.json
"""

import json
import random

SEED = 20260716
N_TRIALS = 200_000                       # messages per crossover value
P_SWEEP = [0.0, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50]

# --- Hamming(7,4): positions 1..7 (0-based array index = position-1).
# Parity (check) bits at positions 1,2,4; data bits at 3,5,6,7.
DATA_POS = [3, 5, 6, 7]                   # Hamming positions carrying the 4 message bits
CHECK_POS = [1, 2, 4]

def encode74(m):
    """m: 4 bits (list). -> 7-bit codeword c[0..6] (index i = position i+1)."""
    a, b, c, d = m                        # a->pos3  b->pos5  c->pos6  d->pos7
    cw = [0] * 7
    cw[2] = a; cw[4] = b; cw[5] = c; cw[6] = d
    cw[0] = a ^ b ^ d                     # pos1 parity of {3,5,7}
    cw[1] = a ^ c ^ d                     # pos2 parity of {3,6,7}
    cw[3] = b ^ c ^ d                     # pos4 parity of {5,6,7}
    return cw

def syndrome(cw):
    """Return the 3-bit syndrome as an integer 0..7 = position of a single error."""
    s0 = cw[0] ^ cw[2] ^ cw[4] ^ cw[6]    # positions with bit0 set: 1,3,5,7
    s1 = cw[1] ^ cw[2] ^ cw[5] ^ cw[6]    # bit1 set: 2,3,6,7
    s2 = cw[3] ^ cw[4] ^ cw[5] ^ cw[6]    # bit2 set: 4,5,6,7
    return s0 + 2 * s1 + 4 * s2

def data_bits(cw):
    return [cw[p - 1] for p in DATA_POS]

def decode74(recv):
    """Single-error-correcting decode. Returns (message_out, report).
    report: 0 = 'no error (syndrome 0)', else k = 'corrected position k'.
    Note: the decoder NEVER refuses. That is the whole point."""
    s = syndrome(recv)
    cw = recv[:]
    if s != 0:
        cw[s - 1] ^= 1                    # flip the position the syndrome names
    return data_bits(cw), s

def decode_secded(recv8):
    """Extended Hamming(8,4): recv8[0..6] = the 7 code bits, recv8[7] = overall parity.
    Returns (message_out or None, status): status in {'ok','corrected','REFUSED','ok_parity'}.
    On a detected (but uncorrectable) double error it REFUSES instead of guessing."""
    cw = recv8[:7]
    s = syndrome(cw)
    overall = 0
    for b in recv8:
        overall ^= b                      # parity of all 8 received bits
    if s == 0 and overall == 0:
        return data_bits(cw), 'ok'
    if s != 0 and overall == 1:
        cw[s - 1] ^= 1
        return data_bits(cw), 'corrected'
    if s == 0 and overall == 1:
        return data_bits(cw), 'ok_parity'  # the error is in the overall parity bit itself
    # s != 0 and overall == 0  ->  even number of errors (>=2): detected, uncorrectable
    return None, 'REFUSED'

def encode_secded(m):
    cw = encode74(m)
    return cw + [sum(cw) % 2]             # append overall parity


# ---------------------------------------------------------------------------
# 1) EXHAUSTIVE CENSUS — every error pattern of weight 0,1,2 on Hamming(7,4).
# By linearity the outcome depends only on the error pattern, not the message,
# so we may fix one message and enumerate all C(7,k) patterns.
# ---------------------------------------------------------------------------
def census():
    m = [1, 0, 1, 1]                      # any fixed message; result is message-independent
    cw = encode74(m)
    out = {"weight0": {"correct": 0, "miscorrected": 0, "patterns": 1},
           "weight1": {"correct": 0, "miscorrected": 0, "patterns": 7},
           "weight2": {"correct": 0, "miscorrected": 0, "patterns": 21}}
    # weight 0
    dec, _ = decode74(cw[:])
    out["weight0"]["correct" if dec == m else "miscorrected"] += 1
    # weight 1
    for i in range(7):
        r = cw[:]; r[i] ^= 1
        dec, _ = decode74(r)
        out["weight1"]["correct" if dec == m else "miscorrected"] += 1
    # weight 2
    for i in range(7):
        for j in range(i + 1, 7):
            r = cw[:]; r[i] ^= 1; r[j] ^= 1
            dec, _ = decode74(r)
            out["weight2"]["correct" if dec == m else "miscorrected"] += 1
    return out

# A few curated example rows: pairs whose decoder REPORT is identical in form
# (both "syndrome = k -> corrected position k") but one is a rescue, one a lie.
def examples():
    m = [1, 0, 1, 1]
    cw = encode74(m)
    rows = []
    # a single-error rescue at position 5
    r = cw[:]; r[4] ^= 1
    dec, s = decode74(r)
    rows.append({"kind": "one flip", "sent": cw[:], "recv": r[:], "syndrome": s,
                 "report": f"corrected position {s}", "out": dec, "truth": "RESCUE" if dec == m else "LIE",
                 "flips": [5]})
    # a double-error lie: flips at positions 1 and 4 -> syndrome points to position 5
    r = cw[:]; r[0] ^= 1; r[3] ^= 1
    dec, s = decode74(r)
    rows.append({"kind": "two flips", "sent": cw[:], "recv": r[:], "syndrome": s,
                 "report": f"corrected position {s}", "out": dec, "truth": "RESCUE" if dec == m else "LIE",
                 "flips": [1, 4]})
    return {"message": m, "codeword": cw, "rows": rows}


# ---------------------------------------------------------------------------
# 2) SEEDED CHANNEL SWEEP — real binary symmetric channel, SEC vs SECDED.
# For each crossover p, N random messages; each of 8 code bits flipped with
# prob p (SEC reads the first 7, SECDED all 8 — same noise on the shared bits).
# Classify by TRUTH (known only to us), not by the decoder's own report.
# ---------------------------------------------------------------------------
def channel_sweep():
    rng = random.Random(SEED)
    sweep = []
    for p in P_SWEEP:
        sec = {"correct": 0, "silent_error": 0}                 # SEC never refuses
        secded = {"correct": 0, "silent_error": 0, "refused": 0}
        for _ in range(N_TRIALS):
            m = [rng.randint(0, 1) for _ in range(4)]
            code8 = encode_secded(m)
            recv8 = [b ^ (1 if rng.random() < p else 0) for b in code8]
            # SEC on the first 7 bits
            dec, _ = decode74(recv8[:7])
            if dec == m:
                sec["correct"] += 1
            else:
                sec["silent_error"] += 1          # delivered a wrong message, flagged nothing
            # SECDED on all 8
            dec2, status = decode_secded(recv8)
            if status == 'REFUSED':
                secded["refused"] += 1
            elif dec2 == m:
                secded["correct"] += 1
            else:
                secded["silent_error"] += 1
        sweep.append({
            "p": p,
            "sec": {k: v / N_TRIALS for k, v in sec.items()},
            "secded": {k: v / N_TRIALS for k, v in secded.items()},
        })
    return sweep


def main():
    data = {
        "meta": {
            "code": "Hamming(7,4)",
            "extended": "Hamming(8,4) SECDED",
            "d_min_74": 3,
            "d_min_84": 4,
            "seed": SEED,
            "n_trials": N_TRIALS,
            "data_pos": DATA_POS,
            "check_pos": CHECK_POS,
            "note": "Census is exhaustive (message-independent by linearity). Channel sweep is seeded.",
        },
        "census": census(),
        "examples": examples(),
        "sweep": channel_sweep(),
    }
    with open("data.json", "w") as f:
        json.dump(data, f, indent=1)
    # console summary
    c = data["census"]
    print("CENSUS (Hamming 7,4), exhaustive over error patterns weight 0/1/2:")
    print(f"  weight 0: {c['weight0']['correct']}/1 correct")
    print(f"  weight 1: {c['weight1']['correct']}/7 correct (true rescues)")
    print(f"  weight 2: {c['weight2']['miscorrected']}/21 MISCORRECTED "
          f"(confident, silent, wrong)")
    print("CHANNEL sweep (seed %d, N=%d):" % (SEED, N_TRIALS))
    for row in data["sweep"]:
        print("  p=%.2f  SEC silent-error=%.4f   SECDED silent-error=%.4f  refused=%.4f"
              % (row["p"], row["sec"]["silent_error"],
                 row["secded"]["silent_error"], row["secded"]["refused"]))


if __name__ == "__main__":
    main()
