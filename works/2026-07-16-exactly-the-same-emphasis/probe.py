#!/usr/bin/env python3
"""Exactly the Same Emphasis — the measurement behind work 26.

Stein's claim ("Portraits and Repetition", Lectures in America, 1935):
there is no repetition, only INSISTENCE — a living process cannot use
"exactly the same emphasis" twice; only a dead one can. Session 31's
detect-bit judged repeated words by document frequency alone, i.e. it
counted tokens as identical. This probe measures what frequency cannot
see: whether each recurrence of a repeated word arrives with FRESH
surroundings (insistence) or COPIED surroundings (dead repetition).

Registers measured (all real, all committed):
  A. Stein, "Melanctha" (1909, public domain, texts/melanctha.txt)
       targets: always, certainly, melanctha
  B. This project's journal corpus (journal/*.md + pulse/vital-signs.json)
       targets: noise, error, swerve
  C. The project's ritual formulas — sentences repeated verbatim across
     sessions, measured as phrase-targets over register B's stream:
       "i am the observer measuring the system i am inside"
       "treat this number as fallible"
       "error is what method is made of"        (the thesis itself)

Metrics — fixed BEFORE anything was run (see journal 2026-07-16 s33);
the target words were fixed on occurrence COUNTS only, never on results:
  context(i)   = the 8 tokens either side of occurrence i (target excluded)
  novelty(i)   = |set(context(i)) − union of all earlier context sets| / |set(context(i))|
                 (first occurrence ≡ 1.0 by definition)
  sameness     = mean pairwise Jaccard similarity over all occurrence-context SETS
  verbatim     = fraction of occurrences (after the first) whose exact context token
                 SEQUENCE already occurred at an earlier occurrence
  controls     = for each single-word target, the 2 nearest-frequency tokens in the
                 same corpus (len ≥ 4, not a stopword, not itself a target), chosen
                 by |count difference| then alphabetically — a deterministic rule
The dead limit needs no fake text — exact copying gives novelty ≡ 0 (after the
first occurrence), sameness = 1.0, verbatim = 1.0, analytically.

Deterministic: no randomness, no timestamps read at run time. Re-running on the
same tree gives the same data.json; the committed data.json is a dated snapshot
of the tree as it stood on 2026-07-16 (before this session's own entry existed —
re-running after this session lands will fold tonight's text into register B,
so the committed numbers are the measurement, per the S32 precedent).

Run from the repository root:  python3 works/2026-07-16-exactly-the-same-emphasis/probe.py
"""

import glob
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

WINDOW = 8
SNAPSHOT_DATE = "2026-07-16"

STOP = set(
    """the a an and or but if then than that this these those there here of to in on
    at by for with from into over under about as is are was were be been being have
    has had do does did not no nor so such it its it's they them their she her hers
    he him his we us our you your i me my mine one ones what which who whom whose
    when where why how all any both each few more most other some only own same very
    can will just should now also because while after before between out up down off
    again once too""".split()
)

WORD_TARGETS = {
    "melanctha": ["always", "certainly", "melanctha"],
    "journal": ["noise", "error", "swerve"],
}

PHRASE_TARGETS = [
    "i am the observer measuring the system i am inside",
    "treat this number as fallible",
    "error is what method is made of",
]


def tokenize(text):
    return re.findall(r"[a-zäöüß']+", text.lower())


def load_corpora():
    mel = open(os.path.join(HERE, "texts", "melanctha.txt")).read()
    parts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "journal", "*.md"))):
        parts.append(open(f).read())
    parts.append(open(os.path.join(ROOT, "pulse", "vital-signs.json")).read())
    return {"melanctha": tokenize(mel), "journal": tokenize("\n".join(parts))}


def contexts_for_word(tokens, target):
    out = []
    for i, t in enumerate(tokens):
        if t == target:
            ctx = tokens[max(0, i - WINDOW) : i] + tokens[i + 1 : i + 1 + WINDOW]
            out.append(ctx)
    return out


def contexts_for_phrase(tokens, phrase_tokens):
    n = len(phrase_tokens)
    out = []
    for i in range(len(tokens) - n + 1):
        if tokens[i : i + n] == phrase_tokens:
            ctx = tokens[max(0, i - WINDOW) : i] + tokens[i + n : i + n + WINDOW]
            out.append(ctx)
    return out


def verbatim_examples(contexts, top=4):
    """The exact context sequences that occur more than once — the copied emphases."""
    dup = Counter(tuple(c) for c in contexts)
    ex = [(cnt, " ".join(k)) for k, cnt in dup.items() if cnt > 1]
    ex.sort(key=lambda t: (-t[0], t[1]))
    return [{"times": c, "context": s} for c, s in ex[:top]]


def measure(contexts):
    """novelty trace, mean pairwise Jaccard, verbatim-context rate."""
    if not contexts:
        return None
    sets = [set(c) for c in contexts]
    novelty, seen = [], set()
    for s in sets:
        novelty.append(round(len(s - seen) / len(s), 4) if s else 0.0)
        seen |= s
    pair_sum, pairs = 0.0, 0
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            inter = len(sets[i] & sets[j])
            union = len(sets[i] | sets[j])
            if union:
                pair_sum += inter / union
                pairs += 1
    sameness = round(pair_sum / pairs, 4) if pairs else None
    seqs_seen, verbatim = set(), 0
    for k, c in enumerate(contexts):
        key = tuple(c)
        if k > 0 and key in seqs_seen:
            verbatim += 1
        seqs_seen.add(key)
    verbatim_rate = round(verbatim / (len(contexts) - 1), 4) if len(contexts) > 1 else 0.0
    tail = novelty[len(novelty) // 2 :]
    return {
        "n": len(contexts),
        "novelty": novelty,
        "novelty_mean": round(sum(novelty) / len(novelty), 4),
        "novelty_tail_mean": round(sum(tail) / len(tail), 4) if tail else None,
        "sameness": sameness,
        "verbatim_rate": verbatim_rate,
    }


def pick_controls(counter, target, taken):
    """The 2 nearest-frequency tokens (len>=4, non-stopword, unused) — deterministic."""
    tc = counter[target]
    cands = [
        (abs(c - tc), w)
        for w, c in counter.items()
        if len(w) >= 4 and w not in STOP and w != target and w not in taken
    ]
    cands.sort()
    return [w for _, w in cands[:2]]


def main():
    corpora = load_corpora()
    result = {
        "snapshot_date": SNAPSHOT_DATE,
        "window": WINDOW,
        "corpus_stats": {k: {"tokens": len(v), "types": len(set(v))} for k, v in corpora.items()},
        "registers": {},
        "formulas": [],
        "dead_limit": {
            "note": "exact copying, analytically: novelty=0 after the first occurrence, sameness=1.0, verbatim=1.0",
            "novelty_tail_mean": 0.0,
            "sameness": 1.0,
            "verbatim_rate": 1.0,
        },
    }
    for corpus, targets in WORD_TARGETS.items():
        tokens = corpora[corpus]
        counter = Counter(tokens)
        reg = []
        taken = set(targets)
        for target in targets:
            ctxs = contexts_for_word(tokens, target)
            m = measure(ctxs)
            m["target"] = target
            m["count"] = counter[target]
            m["verbatim_examples"] = verbatim_examples(ctxs)
            ctrls = []
            for cw in pick_controls(counter, target, taken):
                taken.add(cw)
                cm = measure(contexts_for_word(tokens, cw))
                ctrls.append(
                    {
                        "word": cw,
                        "count": counter[cw],
                        "n": cm["n"],
                        "novelty_tail_mean": cm["novelty_tail_mean"],
                        "sameness": cm["sameness"],
                        "verbatim_rate": cm["verbatim_rate"],
                    }
                )
            m["controls"] = ctrls
            reg.append(m)
        result["registers"][corpus] = reg
    jt = corpora["journal"]
    for phrase in PHRASE_TARGETS:
        m = measure(contexts_for_phrase(jt, tokenize(phrase)))
        if m is None:
            m = {"n": 0}
        m["phrase"] = phrase
        result["formulas"].append(m)
    out = os.path.join(HERE, "data.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=1)
    print(f"wrote {out}")
    for corpus, reg in result["registers"].items():
        for m in reg:
            print(
                f"{corpus:10s} {m['target']:12s} n={m['n']:5d} "
                f"novelty_tail={m['novelty_tail_mean']:.3f} sameness={m['sameness']:.3f} "
                f"verbatim={m['verbatim_rate']:.3f}"
            )
    for m in result["formulas"]:
        print(
            f"formula    {m['phrase'][:40]:40s} n={m['n']:3d} "
            f"novelty_tail={m.get('novelty_tail_mean')} sameness={m.get('sameness')} "
            f"verbatim={m.get('verbatim_rate')}"
        )


if __name__ == "__main__":
    main()
