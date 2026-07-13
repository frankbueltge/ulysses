#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generative Unknowing — the measured core.
Ulysses, 2026-07-13, Session 24.  Research project: Error as Method.  Track B / B4 (Jones).

THE CLAIM BEING MEASURED (Jones 2022, primary; drawing on Marenko 2015, on Parisi 2013):
  A glitch is "a form of unknowing: a 'machine's own incomprehensible, non-human thought'
  manifests itself as a glitch because it reaches outside normalised determinations."
  And, load-bearing for this work: it is BOTH the algorithm's capacity to produce differentiating
  outputs AND the surprising event of the error that hold creative potential, and
  "*often it is impossible to distinguish between the two, primarily because algorithms currently
  operate with data and materials at vastly larger scales than we can ourselves*."
  (N. Jones, Glitch Poetics, Open Humanities Press 2022, ch. "Media Realism in Post-Digital Writing".)

THE INSTRUMENT (mine; the synthesis):
  Signal detection theory (Green & Swets 1966; born from radar/comms engineering — the same
  1948-era information-theory milieu as Wiener/Shannon). SDT gives an observer trying to tell a
  SIGNAL (here: a glitch) from NOISE (here: ordinary generation) two independent numbers:
    - sensitivity  d' = z(Hit) - z(FalseAlarm)  : how far apart signal and noise really are.
    - criterion    c                             : where the observer draws the line (their bias).
  This is the project's founding thesis in equation form (parry-problem.md): error is a RELATION
  between output and an observer's expectation, not a property of the output; d' is the world's
  part, c is the observer's part. Jones's "impossible to distinguish at scale" is the precise,
  measurable statement  d' -> 0 .

THE MECHANISM (real, seeded, no simulation of the appearance of an error):
  An order-1 Markov process over an alphabet of V symbols. From each state a it emits a successor
  b ~ P(.|a).  A GLITCH is a real out-of-distribution jump: b drawn UNIFORMLY at random, ignoring
  the learned transition. The only evidence any observer has about a single transition (a->b) is
  how the model rates it: the log-probability  x = log P(b|a)  (its surprisal, negated). The
  Bayes-optimal (ideal) observer thresholds the likelihood ratio, which here is monotone in x:
        p_glitch(b) / p_ordinary(b) = (1/V) / P(b|a)     -> call "glitch" when P(b|a) is too small.
  So the ideal observer simply says "error" when the model finds the successor too improbable.

  SCALE (Jones's "vastly larger scales") is operationalised as the process's branching entropy H:
  a low-entropy process affords few, predictable continuations (a glitch is glaring); a high-entropy
  process affords a vast, flat field of near-equiprobable continuations ("outside normalised
  determinations") in which an out-of-distribution jump is statistically indistinguishable from an
  ordinary rare-but-legal one. We sweep H (via a temperature on fixed seeded affinities) and, as a
  second axis, the alphabet size V, and MEASURE the ideal observer's discriminability at each scale.

WHAT IS COMPUTED (exactly, from the transition distributions — no Monte-Carlo needed for the core):
  For each state a, the evidence x = log P(b|a) has:
    - a "generation" distribution  (b ~ P(.|a))   — this is the NOISE (ordinary output),
    - a "glitch" distribution      (b ~ Uniform)  — this is the SIGNAL (the error).
  AUC = P(x_gen > x_glitch): the probability the ideal observer ranks a genuine (ordinary) symbol
  as more model-probable than a glitch — the assumption-free discriminability (area under the ROC).
  AUC = 0.5 is chance (the observer cannot tell them apart); AUC = 1.0 is perfect. We convert to the
  SDT scale via  d' = sqrt(2) * Phi^{-1}(AUC)  (the standard Az<->da relation). Averaged over states.

  We ALSO run a seeded fixed-criterion observer (a fixed "normality model") across scales, to show
  the second half of the thesis: as scale rises, its hits collapse toward its false alarms (d' -> 0)
  while it keeps saying "error" at nearly the same rate — the SENSITIVITY dies but the CRITERION
  survives. What it then calls "error" is no longer the error; it is the observer's own line.

OUTPUT: data.json  (consumed by work.astro).  Same seed -> same numbers.  Pure standard library.
"""

import json
import math
import os
import random

SEED = 20260713
ALPHABET_V = 48          # fixed alphabet for the entropy sweep ("scale as flatness")
STATES = 48              # number of Markov states (= symbols)
# 48 legible glyphs (letters); index i -> GLYPHS[i]. No emoji, no slop.
GLYPHS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUV")
assert len(GLYPHS) >= ALPHABET_V


# ----------------------------------------------------------------------------- SDT helpers
def norm_cdf(x):
    """Phi(x) via erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p):
    """Inverse standard-normal CDF (Acklam's rational approximation). Accurate to ~1e-9."""
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


# ----------------------------------------------------------------------------- the generator
def build_affinities(rng, n_states, v):
    """Seeded base affinities score(a,b); the transition matrix is softmax(score/tau)."""
    return [[rng.gauss(0.0, 1.0) for _ in range(v)] for _ in range(n_states)]


def row_probs(scores_a, tau):
    """P(.|a) = softmax(score(a,.)/tau).  tau small -> peaked (low H); tau large -> flat (high H)."""
    m = max(scores_a)
    exps = [math.exp((s - m) / tau) for s in scores_a]
    z = sum(exps)
    return [e / z for e in exps]


def entropy_nats(p):
    return -sum(pi * math.log(pi) for pi in p if pi > 0.0)


def auc_glitch_vs_gen(p):
    """
    Exact AUC = P(x_gen > x_glitch) + 0.5 P(x_gen = x_glitch),
    where x = log P(b|a); gen draws b ~ P, glitch draws b ~ Uniform(1/V).
    Because x is monotone in P(b|a), ranking by x == ranking by P(b|a).
      AUC = sum_{b,b'} P(b) * (1/V) * [ 1{P(b) > P(b')} + 0.5 * 1{P(b) == P(b')} ]
    Higher AUC -> ordinary symbols are reliably more model-probable than glitches
    -> the ideal observer can separate error from generation.
    """
    v = len(p)
    inv = 1.0 / v
    auc = 0.0
    for b in range(v):
        pb = p[b]
        acc = 0.0
        for bp in range(v):
            if pb > p[bp]:
                acc += 1.0
            elif pb == p[bp]:
                acc += 0.5
        auc += pb * inv * acc
    return auc


def dprime_from_auc(auc):
    auc = min(max(auc, 1e-6), 1 - 1e-6)
    return math.sqrt(2.0) * norm_ppf(auc)


# ----------------------------------------------------------------------------- sweeps
def entropy_sweep(scores, taus, v):
    """Scale axis = branching entropy H (nats), varied via temperature tau on a FIXED alphabet."""
    out = []
    for tau in taus:
        aucs, Hs = [], []
        for a in range(len(scores)):
            p = row_probs(scores[a][:v], tau)
            aucs.append(auc_glitch_vs_gen(p))
            Hs.append(entropy_nats(p))
        auc = sum(aucs) / len(aucs)
        H = sum(Hs) / len(Hs)
        out.append({
            "tau": round(tau, 4),
            "H_nats": round(H, 4),
            "H_bits": round(H / math.log(2), 4),
            "branching": round(math.exp(H), 3),       # effective # of equiprobable continuations
            "auc": round(auc, 5),
            "dprime": round(dprime_from_auc(auc), 4),
        })
    return out


def size_sweep(rng, sizes, tau):
    """Scale axis = alphabet size V (the 'vastly larger scale'), at a fixed moderate temperature."""
    out = []
    for v in sizes:
        sc = build_affinities(rng, v, v)
        aucs, Hs = [], []
        for a in range(v):
            p = row_probs(sc[a], tau)
            aucs.append(auc_glitch_vs_gen(p))
            Hs.append(entropy_nats(p))
        auc = sum(aucs) / len(aucs)
        H = sum(Hs) / len(Hs)
        out.append({
            "V": v,
            "H_bits": round(H / math.log(2), 4),
            "auc": round(auc, 5),
            "dprime": round(dprime_from_auc(auc), 4),
        })
    return out


# ----------------------------------------------------------------------------- fixed-criterion observer
def fixed_criterion_observer(rng, scores, taus, v, n_trials, crit_quantile):
    """
    A single observer carrying one FIXED normality model across scales. The criterion is a fixed
    log-prob threshold: 'error' if log P(b|a) < theta. theta is chosen ONCE, at the lowest-entropy
    (sharpest) scale, at a given quantile of that scale's ordinary-evidence — a reasonable line that
    catches most glitches there. We then carry the SAME theta to every higher scale and measure
    hit rate, false-alarm rate, empirical d', and 'yes'(=error) rate. The point: hits collapse
    toward false alarms (d' -> 0) as scale rises, while the observer keeps flagging 'error' at a
    similar rate. Sensitivity dies; the criterion survives.
    """
    # calibrate theta at the sharpest scale
    tau0 = taus[0]
    ord_lp = []
    for a in range(len(scores)):
        p = row_probs(scores[a][:v], tau0)
        lp = [math.log(pi) for pi in p]
        for b in range(v):
            # weight by how often ordinary generation produces b -> sample it
            pass
        # collect a sample of ordinary log-probs from this row
        for _ in range(200):
            b = _sample(rng, p)
            ord_lp.append(lp[b])
    ord_lp.sort()
    theta = ord_lp[int(crit_quantile * (len(ord_lp) - 1))]

    points = []
    for tau in taus:
        hits = misses = fa = cr = 0
        for _ in range(n_trials):
            a = rng.randrange(len(scores))
            p = row_probs(scores[a][:v], tau)
            lp = [math.log(pi) for pi in p]
            is_glitch = rng.random() < 0.5
            b = rng.randrange(v) if is_glitch else _sample(rng, p)
            says_glitch = lp[b] < theta
            if is_glitch and says_glitch:
                hits += 1
            elif is_glitch and not says_glitch:
                misses += 1
            elif (not is_glitch) and says_glitch:
                fa += 1
            else:
                cr += 1
        H_rate = hits / max(1, hits + misses)
        F_rate = fa / max(1, fa + cr)
        # clamp for z-transform
        Hc = min(max(H_rate, 0.5 / n_trials), 1 - 0.5 / n_trials)
        Fc = min(max(F_rate, 0.5 / n_trials), 1 - 0.5 / n_trials)
        dprime = norm_ppf(Hc) - norm_ppf(Fc)
        crit = -0.5 * (norm_ppf(Hc) + norm_ppf(Fc))
        yes_rate = (hits + fa) / n_trials
        H = sum(entropy_nats(row_probs(scores[a][:v], tau)) for a in range(len(scores))) / len(scores)
        points.append({
            "H_bits": round(H / math.log(2), 4),
            "hit": round(H_rate, 4),
            "fa": round(F_rate, 4),
            "yes_rate": round(yes_rate, 4),
            "dprime_emp": round(dprime, 4),
            "criterion": round(crit, 4),
        })
    return {"theta_logp": round(theta, 4), "crit_quantile": crit_quantile, "points": points}


def _sample(rng, p):
    r = rng.random()
    acc = 0.0
    for i, pi in enumerate(p):
        acc += pi
        if r <= acc:
            return i
    return len(p) - 1


# ----------------------------------------------------------------------------- example streams
def make_stream(rng, scores, tau, v, length, n_glitch):
    """
    A real Markov walk of `length` symbols with `n_glitch` genuine out-of-distribution jumps at
    seeded positions. Records per-symbol glitch flag and log-prob so the reader can hunt, then reveal.
    """
    positions = set()
    while len(positions) < n_glitch:
        positions.add(rng.randrange(2, length))  # not the first two
    glyphs = []
    state = rng.randrange(v)
    for i in range(length):
        p = row_probs(scores[state][:v], tau)
        lp = [math.log(pi) for pi in p]
        is_glitch = i in positions
        if is_glitch:
            b = rng.randrange(v)                  # ignore the model — a real stray
        else:
            b = _sample(rng, p)
        glyphs.append({
            "ch": GLYPHS[b],
            "glitch": is_glitch,
            "logp": round(lp[b], 3),              # the model's own rating of this successor
        })
        state = b
    H = sum(entropy_nats(row_probs(scores[a][:v], tau)) for a in range(len(scores))) / len(scores)
    return {
        "H_bits": round(H / math.log(2), 4),
        "auc": round(sum(auc_glitch_vs_gen(row_probs(scores[a][:v], tau)) for a in range(len(scores))) / len(scores), 4),
        "n_glitch": n_glitch,
        "glyphs": glyphs,
    }


# ----------------------------------------------------------------------------- main
def main():
    rng = random.Random(SEED)
    scores = build_affinities(rng, STATES, ALPHABET_V)

    # entropy sweep: many taus spanning peaked -> flat
    taus = [0.25, 0.35, 0.5, 0.7, 0.9, 1.15, 1.5, 2.0, 2.75, 4.0, 6.0, 9.0, 14.0, 22.0, 40.0]
    ent = entropy_sweep(scores, taus, ALPHABET_V)

    # size sweep: alphabet grows, fixed temperature
    rng2 = random.Random(SEED + 1)
    sizes = [4, 6, 9, 13, 18, 24, 32, 42, 56, 74, 96]
    siz = size_sweep(rng2, sizes, tau=1.0)

    # fixed-criterion observer across the entropy sweep
    rng3 = random.Random(SEED + 2)
    fixed = fixed_criterion_observer(rng3, scores, taus, ALPHABET_V,
                                     n_trials=8000, crit_quantile=0.20)

    # three example streams: low / mid / high entropy (glitch obvious -> invisible)
    rng4 = random.Random(SEED + 3)
    streams = {
        "low":  make_stream(rng4, scores, tau=0.35, v=ALPHABET_V, length=120, n_glitch=8),
        "mid":  make_stream(rng4, scores, tau=1.5,  v=ALPHABET_V, length=120, n_glitch=8),
        "high": make_stream(rng4, scores, tau=9.0,  v=ALPHABET_V, length=120, n_glitch=8),
    }

    data = {
        "seed": SEED,
        "alphabet_size": ALPHABET_V,
        "states": STATES,
        "entropy_sweep": ent,
        "size_sweep": siz,
        "fixed_criterion": fixed,
        "streams": streams,
    }

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "data.json"), "w") as f:
        json.dump(data, f, indent=1)

    # console summary (for the journal)
    print("Generative Unknowing — measured. seed =", SEED)
    print("\nENTROPY SWEEP (scale = branching entropy; fixed alphabet V=%d):" % ALPHABET_V)
    print("  H(bits)  branching   AUC     d'")
    for r in ent:
        print("  %6.2f   %7.2f   %.3f   %.3f" % (r["H_bits"], r["branching"], r["auc"], r["dprime"]))
    print("\nSIZE SWEEP (scale = alphabet size V; tau=1.0):")
    print("  V     H(bits)   AUC     d'")
    for r in siz:
        print("  %-4d  %6.2f   %.3f   %.3f" % (r["V"], r["H_bits"], r["auc"], r["dprime"]))
    print("\nFIXED-CRITERION OBSERVER (theta=%.3f at q=%.2f of the sharpest scale):"
          % (fixed["theta_logp"], fixed["crit_quantile"]))
    print("  H(bits)   hit     fa    yes-rate   d'_emp   criterion")
    for r in fixed["points"]:
        print("  %6.2f   %.3f  %.3f    %.3f     %.3f    %.3f"
              % (r["H_bits"], r["hit"], r["fa"], r["yes_rate"], r["dprime_emp"], r["criterion"]))
    print("\nSTREAMS (glitch detectability by scale):")
    for k in ("low", "mid", "high"):
        s = streams[k]
        gl = [g["logp"] for g in s["glyphs"] if g["glitch"]]
        no = [g["logp"] for g in s["glyphs"] if not g["glitch"]]
        print("  %-4s  H=%.2f bits  AUC=%.3f  mean logp: glitch=%.2f  ordinary=%.2f  gap=%.2f"
              % (k, s["H_bits"], s["auc"], sum(gl)/len(gl), sum(no)/len(no),
                 sum(no)/len(no) - sum(gl)/len(gl)))


if __name__ == "__main__":
    main()
