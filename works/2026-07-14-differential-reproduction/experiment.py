#!/usr/bin/env python3
# Differential Reproduction — the measured backbone
# works/2026-07-14-differential-reproduction/experiment.py   (Ulysses, Session 27, 2026-07-14)
#
# WHAT THIS RUNS (the error mechanism runs for real; nothing here is asserted).
# ---------------------------------------------------------------------------
# Session 26 read the philosophy of experimental science and subtracted a word: at the centre
# of this project sits not "error" but Rheinberger's EPISTEMIC THING -- the productive
# not-yet-known a repeating system throws off by DIFFERENTIAL REPRODUCTION, which he defines as
# the capacity to "produce differences without destroying its reproductive coherence"
# (Rheinberger, "Experimental Systems: Difference, Graphematicity, Conjuncture").
#
# Three earlier works of mine ran the LOSS side of a recursive loop (Generation Loss 07-03,
# The Closing Loop 07-11, Low-Background 07-12): finite-sampling error kills the tail; the cure
# is renewal/accumulation (Gerstgrasser et al. 2024, arXiv:2404.01413 -- REPLACE collapses,
# ACCUMULATE bounds the error). All three measured only how a system DIES.
#
# This one measures the BIRTH side, which needs a mechanism those three lacked: variation plus a
# viability filter (selection). That mechanism has a name in theoretical biology I had not worked
# -- Eigen's QUASISPECIES / ERROR THRESHOLD (Eigen 1971). In the classical lethal-error model "an
# imperfect copy leads to elimination of the offspring" (as restated in arXiv:2406.14516); genetic
# information is maintained only BELOW a critical per-site mutation rate of order ln(q)/L ~ 1/L, and
# above it the error catastrophe destroys it (the master is lost). So differential reproduction is
# an INVERTED-U in the mutation rate mu:
#   mu = 0             : perfect reproduction, NO difference           -> the frozen loop (dead one way)
#   0 < mu < mu_crit   : difference produced AND kept coherent         -> the LIVING BAND (epistemic things)
#   mu > mu_crit        : difference destroys coherence, extinction     -> the catastrophe (dead the other way)
#
# THE MODEL (a real artificial-life run, deterministic under the seed).
# A genome is a string of length L over an alphabet of size q. VIABILITY (the "reproductive
# coherence") is membership of a regular language: a well-formedness rule -- no symbol may equal
# either of its two predecessors (a no-echo / phonotactic constraint). The viable strings form a
# large NEUTRAL NETWORK: many different well-formed words, all equally allowed. A population of N
# genomes reproduces each generation; each offspring copies a random viable parent with per-site
# substitution probability mu; an offspring that falls OFF the language (breaks well-formedness) is
# non-viable and dies. What survives is copied-with-difference and still speakable.
#
# WHAT IS MEASURED, per mu, averaged over SEEDS independent runs:
#   coherence  C(mu) = mean fraction of offspring that are viable      (Rheinberger's "reproductive coherence")
#   novelty    E(mu) = rate of NEW motifs (k-mers absent from the founder) that reach population
#                      MAJORITY and are thus inherited                 (the epistemic thing: difference that is KEPT)
#   drift          = mean Hamming distance of the population from the founder (how far the line walked)
#   extinct        = whether the population failed to stay viable
#   DR(mu) = C(mu) * E(mu)  -- the DIFFERENTIAL-REPRODUCTION index; its peak mu* is the living band,
#                              and the theory predicts the band's upper edge near mu ~ ln(q)/L.
#
# The whole point of the project, enacted: a system that only reproduces (mu=0) is the closing loop;
# a system that only differs (mu large) dissolves; the health is the two-factor middle -- exactly
# what the atelier's own closure index measures, now shown to be the differential-reproduction gauge.

import json, math, os

SEED = 20260714          # same seed -> same run; git is the archive
Q    = 6                 # alphabet size
L    = 24                # genome length
N    = 120               # population size
G    = 140               # generations per run
SEEDS = 12               # independent runs averaged per mu
KMER = 4                 # motif length for the novelty measure
MAJORITY = 0.5           # a motif is "inherited" once it is in > this fraction of the population

# mu grid: dense near the interesting region (~1/L ~ 0.042), out to catastrophe.
MU_GRID = [0.0, 0.002, 0.004, 0.007, 0.010, 0.014, 0.018, 0.024, 0.030,
           0.038, 0.048, 0.060, 0.075, 0.092, 0.110, 0.135, 0.165, 0.200, 0.250, 0.320]

# --- a small deterministic PRNG (LCG, Numerical Recipes constants) so the run is reproducible ---
class RNG:
    __slots__ = ("s",)
    def __init__(self, seed): self.s = seed & 0xFFFFFFFF
    def next_u32(self):
        self.s = (1664525 * self.s + 1013904223) & 0xFFFFFFFF
        return self.s
    def rand(self):                      # uniform [0,1)
        return self.next_u32() / 4294967296.0
    def randint(self, n):                # 0..n-1
        return self.next_u32() % n

def viable(g):
    # no-echo well-formedness: no symbol equals either of its two predecessors
    for i in range(len(g)):
        if i >= 1 and g[i] == g[i-1]: return False
        if i >= 2 and g[i] == g[i-2]: return False
    return True

def make_founder(rng):
    g = []
    for i in range(L):
        while True:
            c = rng.randint(Q)
            if (i < 1 or c != g[i-1]) and (i < 2 or c != g[i-2]):
                g.append(c); break
    return tuple(g)

def mutate(g, mu, rng):
    out = list(g)
    for i in range(L):
        if rng.rand() < mu:
            c = rng.randint(Q - 1)       # substitute to a DIFFERENT symbol
            if c >= out[i]: c += 1
            out[i] = c
    return tuple(out)

def kmers(g):
    return {g[i:i+KMER] for i in range(len(g) - KMER + 1)}

def run(mu, seed):
    rng = RNG(seed)
    founder = make_founder(rng)
    founder_motifs = kmers(founder)
    pop = [founder] * N

    accept_num = 0        # viable offspring produced
    accept_den = 0        # offspring attempted
    inherited_new = set() # new-to-lineage motifs that have reached majority
    novelty_events = 0    # count of such fixations (the epistemic things)
    drift_acc = 0.0
    extinct = False
    # trajectories (for the three illustrative regimes)
    traj_rich, traj_cov, traj_nov = [], [], []

    for gen in range(G):
        if not pop:
            extinct = True
            traj_rich.append(0); traj_cov.append(0.0); traj_nov.append(novelty_events)
            continue
        newpop = []
        attempts = 0
        cap = N * 40      # generous ceiling; if we cannot fill N viable, the line is failing
        while len(newpop) < N and attempts < cap:
            parent = pop[rng.randint(len(pop))]
            child = mutate(parent, mu, rng)
            attempts += 1
            accept_den += 1
            if viable(child):
                accept_num += 1
                newpop.append(child)
        pop = newpop
        if len(pop) < N:                 # could not sustain a full viable population
            extinct = True

        # ---- measure this generation ----
        # motif -> count across population
        counts = {}
        for g in pop:
            for m in kmers(g):
                counts[m] = counts.get(m, 0) + 1
        popn = max(1, len(pop))
        # motifs at majority
        majority = {m for m, c in counts.items() if c > MAJORITY * popn}
        for m in majority:
            if m not in founder_motifs and m not in inherited_new:
                inherited_new.add(m)
                novelty_events += 1      # a NEW motif got inherited: an epistemic thing, kept
        # richness: distinct viable words; coverage: distinct motifs / possible; drift
        rich = len(set(pop))
        if pop:
            dh = 0
            for g in pop:
                dh += sum(1 for a, b in zip(g, founder) if a != b)
            drift_acc += dh / (len(pop) * L)
        traj_rich.append(rich)
        traj_cov.append(len(counts))
        traj_nov.append(novelty_events)

    C = accept_num / accept_den if accept_den else 0.0
    E = novelty_events / G
    drift = drift_acc / G
    return {
        "coherence": C,
        "novelty_rate": E,
        "novelty_total": novelty_events,
        "drift": drift,
        "extinct": extinct,
        "traj_rich": traj_rich,
        "traj_cov": traj_cov,
        "traj_nov": traj_nov,
    }

def main():
    sweep = []
    for mu in MU_GRID:
        Cs, Es, Ds, exts = [], [], [], 0
        for s in range(SEEDS):
            r = run(mu, SEED + 1009 * s + int(round(mu * 100000)))
            Cs.append(r["coherence"]); Es.append(r["novelty_rate"])
            Ds.append(r["drift"]);     exts += 1 if r["extinct"] else 0
        C = sum(Cs) / len(Cs); E = sum(Es) / len(Es); D = sum(Ds) / len(Ds)
        sweep.append({
            "mu": mu,
            "coherence": round(C, 4),
            "novelty_rate": round(E, 4),
            "dr": round(C * E, 5),
            "drift": round(D, 4),
            "extinct_frac": round(exts / SEEDS, 3),
        })

    # normalise DR to its peak for display; find mu*
    max_dr = max(x["dr"] for x in sweep) or 1.0
    for x in sweep:
        x["dr_norm"] = round(x["dr"] / max_dr, 4)
    mu_star = max(sweep, key=lambda x: x["dr"])["mu"]

    # theory: single-master lethal threshold ~ ln(Q)/L ; also the per-site "1/L" order
    mu_crit_eigen = math.log(Q) / L
    mu_crit_1overL = 1.0 / L

    # three illustrative single-seed trajectories: frozen / living / catastrophe
    def near(target):
        return min(MU_GRID, key=lambda m: abs(m - target))
    regimes = {
        "frozen":       0.0,
        "living":       mu_star,
        "catastrophe":  near(0.25),
    }
    traj = {}
    for name, mu in regimes.items():
        r = run(mu, SEED)   # the canonical seed, single run, for the animation reference
        traj[name] = {
            "mu": mu,
            "rich": r["traj_rich"],
            "nov": r["traj_nov"],
            "extinct": r["extinct"],
            "novelty_total": r["novelty_total"],
            "drift": round(r["drift"], 4),
        }

    out = {
        "meta": {
            "title": "Differential Reproduction",
            "seed": SEED, "q": Q, "L": L, "N": N, "G": G, "seeds": SEEDS,
            "kmer": KMER, "majority": MAJORITY,
            "rule": "viable iff no symbol equals either of its two predecessors (no-echo well-formedness)",
            "generated_note": "All numbers below are measured by this script; same seed -> same numbers.",
        },
        "sweep": sweep,
        "mu_star": mu_star,
        "mu_crit_eigen_lnq_over_L": round(mu_crit_eigen, 4),
        "mu_crit_1_over_L": round(mu_crit_1overL, 4),
        "regimes": traj,
    }
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "data.json"), "w") as f:
        json.dump(out, f, indent=1)

    # console summary
    print(f"mu*  (peak differential reproduction) = {mu_star}")
    print(f"theory: ln(q)/L = {mu_crit_eigen:.4f} ; 1/L = {mu_crit_1overL:.4f}")
    print(" mu     coher  novelty   DR_norm  drift  ext")
    for x in sweep:
        print(f"{x['mu']:.3f}  {x['coherence']:.3f}  {x['novelty_rate']:.4f}   "
              f"{x['dr_norm']:.3f}   {x['drift']:.3f}  {x['extinct_frac']:.2f}")

if __name__ == "__main__":
    main()
