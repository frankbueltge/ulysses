#!/usr/bin/env python3
# resonance.py — Exclude the Third (work 28, Session 35, 2026-07-17)
#
# Runs, for real, a threshold detector on a SUBTHRESHOLD periodic signal buried
# in seeded Gaussian noise, and measures how well the detector's output tracks
# the signal as a function of the noise level D. This is the classical
# level-crossing model of STOCHASTIC RESONANCE (Gammaitoni, Haenggi, Jung &
# Marchesoni, Rev. Mod. Phys. 70, 223 (1998), DOI 10.1103/RevModPhys.70.223):
# a weak signal, undetectable on its own, is carried across the threshold ONLY
# with the assistance of noise — and the transmission peaks at an intermediate
# noise level (an inverted-U), collapsing again when noise is too strong.
#
# The point is not the physics. It is Serres' excluded third made to run: the
# noise is the parasite the channel is built to expel, and here expelling it to
# zero SILENCES the message. The committed data.json is the record of a real
# seeded run; the work.astro viewer only displays it (no re-computation, no
# second RNG). Same seed -> same run. No external dependencies (stdlib only) so
# anyone can reproduce every number by running: python3 resonance.py
#
# Signed: Ulysses.

import json
import math
import os

# ---- fixed parameters (subthreshold by construction: A < THETA) -------------
SEED        = 351720          # session 35, 2026-07-17
FS          = 1000.0          # sample rate (Hz)
F_SIG       = 5.0             # signal frequency (Hz)
DURATION    = 40.0            # seconds  -> 200 signal periods
A           = 0.30           # signal amplitude
THETA       = 0.50           # detector threshold  (A < THETA => never crosses without noise)
REFRACTORY  = 0.05           # dead time after a spike (s); a threshold element cannot
                             # re-fire instantly, so each excursion counts once, not
                             # once per fast noise wiggle. (0.05 s = 1/4 of a period.)
D_MIN       = 0.0
D_MAX       = 0.60           # noise standard deviation, swept
D_STEPS     = 31             # number of noise levels on the curve
HIST_BINS   = 24             # phase-histogram resolution
WIN_PERIODS = 3              # signal periods shown in the live channel window
WIN_STRIDE  = 2              # downsample the window trace by this factor for display

N        = int(FS * DURATION)
PERIODS  = F_SIG * DURATION
TWO_PI   = 2.0 * math.pi


# ---- explicit, portable PRNG (so reproducibility does not depend on any
#      library's RNG internals): SplitMix64 -> uniform -> Box-Muller gaussian --
class RNG:
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFFFFFFFFFF
        self._spare = None

    def _next_u64(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def uniform(self):
        # 53-bit uniform in (0,1)
        return ((self._next_u64() >> 11) + 0.5) / (1 << 53)

    def gauss(self):
        if self._spare is not None:
            g, self._spare = self._spare, None
            return g
        u1 = self.uniform()
        u2 = self.uniform()
        r = math.sqrt(-2.0 * math.log(u1))
        self._spare = r * math.sin(TWO_PI * u2)
        return r * math.cos(TWO_PI * u2)


def signal_at(i):
    return A * math.sin(TWO_PI * F_SIG * (i / FS))


def run():
    # One fixed unit-variance noise trace, drawn once from the seed and REUSED
    # (scaled by D) across every noise level. This is what lets the viewer show a
    # consistent live window: the same seeded third, admitted in varying amounts.
    rng = RNG(SEED)
    noise_unit = [rng.gauss() for _ in range(N)]
    sig = [signal_at(i) for i in range(N)]

    # sanity: the clean signal is genuinely subthreshold
    assert max(sig) < THETA, "signal is not subthreshold"

    curve = []
    hists = []
    for s in range(D_STEPS):
        D = D_MIN + (D_MAX - D_MIN) * s / (D_STEPS - 1)

        # detector: upward crossings of THETA on x = signal + D*noise, with a
        # refractory dead time so each excursion fires once.
        refr = int(REFRACTORY * FS)
        prev = sig[0] + D * noise_unit[0]
        last_spike = -refr - 1
        spike_times = []          # in seconds
        # accumulate the periodogram phasor of the spike train at F_SIG
        re = 0.0
        im = 0.0
        # phase histogram over [0,1)
        hist = [0] * HIST_BINS
        for i in range(1, N):
            x = sig[i] + D * noise_unit[i]
            if prev < THETA <= x and i - last_spike > refr:   # crossing, not refractory
                last_spike = i
                t = i / FS
                spike_times.append(t)
                phase = (F_SIG * t) % 1.0
                re += math.cos(TWO_PI * phase)
                im += math.sin(TWO_PI * phase)
                hist[int(phase * HIST_BINS) % HIST_BINS] += 1
            prev = x

        n = len(spike_times)
        rate = n / PERIODS                                   # spikes per signal period
        R = (math.hypot(re, im) / n) if n else 0.0           # vector strength in [0,1]
        # output power of the spike train at the signal frequency, per period:
        # |sum exp(-i 2pi phase)|^2 / PERIODS  -- the SR transmission measure.
        Q = (re * re + im * im) / PERIODS
        curve.append({
            "D": round(D, 4),
            "spikes": n,
            "rate": round(rate, 4),
            "R": round(R, 4),
            "Q": round(Q, 4),
        })
        hists.append(hist)

    # optimal noise level (argmax of transmitted power)
    q_opt = max(range(D_STEPS), key=lambda k: curve[k]["Q"])

    # short window for the live channel view: signal + unit noise, downsampled
    win_n = int(WIN_PERIODS * FS / F_SIG)
    idx = list(range(0, win_n, WIN_STRIDE))
    window = {
        "t":     [round(i / FS, 4) for i in idx],
        "signal":[round(sig[i], 4) for i in idx],
        "noise": [round(noise_unit[i], 4) for i in idx],
    }

    return {
        "params": {
            "seed": SEED, "fs": FS, "f_sig": F_SIG, "duration": DURATION,
            "N": N, "periods": PERIODS, "A": A, "theta": THETA,
            "refractory": REFRACTORY,
            "d_min": D_MIN, "d_max": D_MAX, "d_steps": D_STEPS,
            "hist_bins": HIST_BINS, "win_periods": WIN_PERIODS,
        },
        "curve": curve,
        "hists": hists,
        "window": window,
        "q_opt_index": q_opt,
        "q_opt_D": curve[q_opt]["D"],
        "q_max": curve[q_opt]["Q"],
    }


if __name__ == "__main__":
    out = run()
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "data.json"), "w") as f:
        json.dump(out, f, indent=1)
    c = out["curve"]
    print("stochastic-resonance run complete (seed %d)" % SEED)
    print("  D=0.0   : spikes=%d  Q=%.3f  (subthreshold: silent)"
          % (c[0]["spikes"], c[0]["Q"]))
    print("  optimal : D=%.3f  spikes=%d  R=%.3f  Q=%.3f  (index %d)"
          % (out["q_opt_D"], c[out["q_opt_index"]]["spikes"],
             c[out["q_opt_index"]]["R"], out["q_max"], out["q_opt_index"]))
    print("  D=%.2f  : spikes=%d  Q=%.3f  (swamped)"
          % (c[-1]["D"], c[-1]["spikes"], c[-1]["Q"]))
