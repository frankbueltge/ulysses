#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
experiment.py  --  "Low-Background"  --  Ulysses, 2026-07-12 (Session 23)

A seeded, reproducible closed-loop (model-collapse) experiment on the project's
own bench (a character-level Markov model, as in works 12-14), extended with the
one variable the 2025-26 field says now matters: a CONTAMINATED COMMONS.

Question (Deepen of Track C / C5):
  The model-collapse literature agrees the disease is a closed self-training loop
  and the cure is "an outside" -- keep a channel to REAL data open. Gerstgrasser
  et al. (2024, arXiv:2404.01413) prove ACCUMULATING real data alongside synthetic
  gives a finite error bound; Jangjoo, Marsili & Roudi (2025, arXiv:2506.20623,
  Phys. Rev.) show even ONE ground-truth data point can prevent collapse.
  BUT every such remedy presupposes that the "real" data entering the loop is
  actually real. In 2025 the open web -- the reservoir every remedy draws on --
  is itself ~35% AI-generated (Dolezal, Alam, Graham & Bohacek 2026,
  arXiv:2604.26965) and, worse, that synthetic fraction is UNDETECTABLE at scale
  (Robyn Speer retired the wordfreq corpus in 2024 for exactly this reason).
  So: what happens to the accumulate-remedy when the "fresh real data" you add
  each generation is secretly a fraction c synthetic -- the loop's own past output,
  masquerading as real?

This script does NOT assert an answer. It measures one (protocol step: measure
before you assert). Same seed -> same numbers. Pure standard library.

Bench
-----
Ground truth G: a fixed, seeded order-2 character Markov process over a 27-symbol
alphabet (a-z + space) with deliberately SKEWED transition distributions, so the
true distribution has a real TAIL of rare-but-valid trigrams. "Collapse" = losing
that tail. (Using a defined ground-truth process, rather than a copyrighted human
text, follows the toy-model methodology of the collapse literature itself --
Shumailov 2024's Gaussian toy, Gerstgrasser 2024 -- and avoids any quotation /
transcription risk. The finding is a property of the loop, not of any one text.)

Model M_g at generation g: an order-3 (trigram) Markov model fit by counts on the
current TRAINING POOL, then sampled to produce that generation's corpus. Finite
sampling is what loses the tail -- a trigram whose probability is below ~1/L is
expected fewer than once in a corpus of length L and tends to vanish (this is the
Shumailov 2024 mechanism, stated for finite corpora).

Metric (the project's established tail metric since work 12): DISTINCT trigrams in
a generation's output, and -- the sharper one -- COVERAGE: the fraction of the
ground truth's "significant" trigrams (prob >= tau) still present. Coverage -> 0
is collapse; coverage holding is a live tail.

Regimes
-------
  REPLACE            : train gen g only on gen g-1's output. (the disease.)
  ACCUMULATE+ANCHOR  : train on a permanent clean anchor (samples from G) UNION all
                       synthetic so far. ("low-background steel" kept: Gerstgrasser.)
  COMMONS(c)         : NO permanent anchor. Each generation adds a fresh batch drawn
                       from the "commons": a fraction (1-c) genuine G-samples and a
                       fraction c the loop's own recent output, ingested as if real
                       (undetectable). Data still ACCUMULATES -- only its realness
                       is adulterated. Sweep c in [0,1].
                       c is anchored to the real trajectory: ~0 pre-2022 -> ~0.35 by
                       2025 (Dolezal et al. 2026); we sweep past it to find the shape.

Sign the work: Ulysses.
"""

import json
import os
from collections import defaultdict, Counter

# --------------------------------------------------------------------------
# Deterministic PRNG (seeded LCG -- no Math.random / no os randomness, so the
# whole experiment is reproducible from the seed alone: git is the archive.)
# --------------------------------------------------------------------------
class LCG:
    """Numerical Recipes LCG. Deterministic, portable, seed -> stream."""
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF
    def next_u32(self):
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state
    def random(self):
        return self.next_u32() / 4294967296.0
    def choice_weighted(self, symbols, weights, wsum):
        r = self.random() * wsum
        acc = 0.0
        for sym, w in zip(symbols, weights):
            acc += w
            if r <= acc:
                return sym
        return symbols[-1]

ALPHABET = "abcdefghijklmnopqrstuvwxyz "
SEED = 20260712  # the date. same seed -> same work.

# --------------------------------------------------------------------------
# Ground truth G: fixed order-2 Markov with skewed (tailed) transitions.
# --------------------------------------------------------------------------
def build_ground_truth(seed):
    """For each 2-char context, a skewed distribution over next chars.
    Skew (a few likely, many rare) is what creates a real tail to lose."""
    rng = LCG(seed)
    gt = {}
    contexts = [a + b for a in ALPHABET for b in ALPHABET]
    for ctx in contexts:
        # Draw raw weights, then cube them to sharpen into a heavy head + long tail.
        raw = [rng.random() for _ in ALPHABET]
        weights = [x ** 3 + 1e-4 for x in raw]  # +eps keeps every transition possible
        s = sum(weights)
        weights = [w / s for w in weights]
        gt[ctx] = weights
    return gt

def gt_sample(gt, rng, length):
    """Sample a length-`length` string from the ground-truth order-2 process."""
    out = ["t", "h"]  # fixed start context
    syms = list(ALPHABET)
    for _ in range(length - 2):
        ctx = out[-2] + out[-1]
        weights = gt[ctx]
        out.append(rng.choice_weighted(syms, weights, 1.0))
    return "".join(out)

def significant_trigrams(gt, rng, tau_count, sample_len, n_samples):
    """The ground truth's 'real' trigram support: trigrams that occur with
    frequency >= tau in a large fair sample from G. This is the tail we ask the
    loop to preserve."""
    counts = Counter()
    total = 0
    for i in range(n_samples):
        s = gt_sample(gt, LCG(SEED * 7 + i * 101 + 3), sample_len)
        for j in range(len(s) - 2):
            counts[s[j:j+3]] += 1
            total += 1
    tau = tau_count / total
    sig = {tg for tg, c in counts.items() if (c / total) >= tau}
    return sig

# --------------------------------------------------------------------------
# The learner: order-3 Markov fit by counts, then sampled.
# --------------------------------------------------------------------------
def fit_order3(corpus):
    model = defaultdict(Counter)
    for i in range(len(corpus) - 3):
        model[corpus[i:i+2]][corpus[i+2:i+3]] += 1  # ctx=2 chars -> next char; trigram support
    return model

def sample_order3(model, rng, length):
    # Start from a context that exists; fall back to "th".
    ctxs = list(model.keys())
    if not ctxs:
        return ""
    ctx = "th" if "th" in model else ctxs[rng.next_u32() % len(ctxs)]
    out = list(ctx)
    for _ in range(length - 2):
        nxt = model.get(out[-2] + out[-1])
        if not nxt:
            # dead end: restart from a random known context (a real collapse symptom)
            ctx = ctxs[rng.next_u32() % len(ctxs)]
            out.append(ctx[0]); out.append(ctx[1])
            continue
        syms = list(nxt.keys())
        weights = list(nxt.values())
        wsum = sum(weights)
        out.append(rng.choice_weighted(syms, weights, wsum))
    return "".join(out)

def distinct_trigrams(s):
    return {s[i:i+3] for i in range(len(s) - 2)}

# --------------------------------------------------------------------------
# The closed loop.
# --------------------------------------------------------------------------
def run_loop(gt, sig, regime, generations, L, anchor_len, contamination, seed, capture_at=None):
    """Returns per-generation lists: distinct-trigram count and coverage of `sig`.
    If capture_at is a set of generation indices, also returns short text samples."""
    rng = LCG(seed)
    sig_set = sig
    nsig = len(sig_set)
    capture_at = capture_at or set()
    samples = {}

    # Generation 0: a clean corpus drawn straight from the ground truth ("pre-AI").
    gen0 = gt_sample(gt, LCG(seed + 1), L)
    corpus_prev = gen0

    anchor = gt_sample(gt, LCG(seed + 2), anchor_len) if regime == "accumulate_anchor" else ""
    accumulated = []  # all synthetic corpora so far (for accumulate regimes)

    distinct_series, coverage_series = [], []

    # record gen 0
    d0 = distinct_trigrams(gen0)
    distinct_series.append(len(d0))
    coverage_series.append(len(d0 & sig_set) / nsig)
    if 0 in capture_at:
        samples["0"] = gen0[100:340]

    for g in range(1, generations + 1):
        # Build the training pool for THIS generation, per regime.
        if regime == "replace":
            pool = corpus_prev

        elif regime == "accumulate_anchor":
            # permanent clean anchor + everything the loop has produced
            pool = anchor + "".join(accumulated + [corpus_prev])

        elif regime == "commons":
            # The commons is a growing pool that PERMANENTLY retains its old (clean)
            # data -- gen0 is the pre-2022 bedrock, never discarded (this is what
            # "accumulate" means). Each period a fresh batch is added: (1-c) genuine
            # G-samples + c the loop's own last output, ingested as if real
            # (undetectable). Train on the whole commons.
            fresh_real_len = int(round(L * (1.0 - contamination)))
            fresh_syn_len = L - fresh_real_len
            fresh_real = gt_sample(gt, LCG(seed + 1000 + g), fresh_real_len) if fresh_real_len > 0 else ""
            fresh_syn = corpus_prev[:fresh_syn_len]  # loop's own recent output, masked as real
            fresh_batch = fresh_real + fresh_syn
            pool = gen0 + "".join(accumulated + [fresh_batch])
            accumulated.append(fresh_batch)
        else:
            raise ValueError(regime)

        if regime == "accumulate_anchor":
            accumulated.append(corpus_prev)

        model = fit_order3(pool)
        gen = sample_order3(model, rng, L)
        corpus_prev = gen

        dg = distinct_trigrams(gen)
        distinct_series.append(len(dg))
        coverage_series.append(len(dg & sig_set) / nsig)
        if g in capture_at:
            samples[str(g)] = gen[100:340]

    return distinct_series, coverage_series, samples


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    gt = build_ground_truth(SEED)

    L = 8000            # corpus length per generation
    ANCHOR = 8000       # size of the permanent clean anchor (accumulate_anchor)
    GENERATIONS = 24
    TAU_COUNT = 6       # a trigram is "significant" if expected >= ~6 times in a fair sample

    sig = significant_trigrams(gt, None, TAU_COUNT, sample_len=20000, n_samples=8)
    print(f"ground-truth significant trigrams (the tail to keep): {len(sig)}")

    results = {"meta": {
        "seed": SEED, "alphabet_size": len(ALPHABET), "corpus_len": L,
        "anchor_len": ANCHOR, "generations": GENERATIONS,
        "ground_truth_order": 2, "model_order": 3,
        "n_significant_trigrams": len(sig), "tau_count": TAU_COUNT,
    }, "regimes": {}}

    CAP = {0, 8, 16, 24}  # generations at which to capture a text sample

    # 1) the disease and the two clean references
    for regime, label in [("replace", "REPLACE (self-training only)"),
                          ("accumulate_anchor", "ACCUMULATE + clean anchor (low-background steel kept)")]:
        d, c, samp = run_loop(gt, sig, regime, GENERATIONS, L, ANCHOR, 0.0, SEED, capture_at=CAP)
        results["regimes"][regime] = {"label": label, "distinct": d, "coverage": c, "samples": samp}
        print(f"{label:52s}  final coverage={c[-1]:.3f}  distinct {d[0]}->{d[-1]}")

    # 2) the contaminated commons: sweep c
    commons = {}
    for c_rate in [0.0, 0.10, 0.20, 0.35, 0.50, 0.70, 0.90, 1.0]:
        cap = CAP if c_rate in (0.35, 1.0) else None
        d, cov, samp = run_loop(gt, sig, "commons", GENERATIONS, L, ANCHOR, c_rate, SEED, capture_at=cap)
        commons[f"{c_rate:.2f}"] = {"contamination": c_rate, "distinct": d, "coverage": cov, "samples": samp}
        print(f"COMMONS c={c_rate:.2f} (fresh inflow {int((1-c_rate)*100)}% real)         "
              f"final coverage={cov[-1]:.3f}  distinct {d[0]}->{d[-1]}")
    results["commons_sweep"] = commons

    # 3) time-driven contamination: c follows the REAL measured web trajectory.
    #    Anchor points (sourced): ~0 before ChatGPT (late 2022); ~0.35 of new
    #    websites AI by mid-2025 (Dolezal et al. 2026). Linear interpolation
    #    between, extrapolated flat after -- an illustrative schedule, not a forecast.
    def c_of_year(y):
        if y <= 2022.85:
            return 0.0
        if y >= 2025.5:
            return 0.35
        return 0.35 * (y - 2022.85) / (2025.5 - 2022.85)
    years = [2020 + (2027 - 2020) * g / GENERATIONS for g in range(GENERATIONS + 1)]
    # run a schedule where each generation uses c_of_year(that generation's year)
    rng = LCG(SEED + 55)
    gen0_td = gt_sample(gt, LCG(SEED + 1), L)  # the pre-2022 bedrock, retained
    gen_prev = gen0_td
    accumulated = []
    d_series, cov_series, c_series = [], [], []
    d0 = distinct_trigrams(gen_prev)
    d_series.append(len(d0)); cov_series.append(len(d0 & sig) / len(sig)); c_series.append(0.0)
    for g in range(1, GENERATIONS + 1):
        c_rate = c_of_year(years[g])
        fr = int(round(L * (1 - c_rate))); fs = L - fr
        fresh = (gt_sample(gt, LCG(SEED + 2000 + g), fr) if fr > 0 else "") + gen_prev[:fs]
        pool = gen0_td + "".join(accumulated + [fresh]); accumulated.append(fresh)
        model = fit_order3(pool); gen = sample_order3(model, rng, L); gen_prev = gen
        dg = distinct_trigrams(gen)
        d_series.append(len(dg)); cov_series.append(len(dg & sig) / len(sig)); c_series.append(c_rate)
    results["time_driven"] = {"years": years, "contamination": c_series,
                              "distinct": d_series, "coverage": cov_series,
                              "note": "c(year): 0 until late-2022, linear to 0.35 by mid-2025 (Dolezal et al. 2026), flat after."}
    print(f"TIME-DRIVEN (real web trajectory)                    final coverage={cov_series[-1]:.3f}")

    with open(os.path.join(here, "data.json"), "w") as f:
        json.dump(results, f, indent=1)
    print("wrote data.json")


if __name__ == "__main__":
    main()
