#!/usr/bin/env python3
"""identify.py — how wide the answer is, before anyone argues about the method.

A catalogue is asked how many of its entries are of some kind. Somebody screens the
entries, reads the ones the screen flagged, and reports a count. The count is a point.
This instrument says what interval that point is an end of.

The frame is the one econometrics has used for missing data since Manski (1989): an
entry either has a settled verdict (`z = 1`) or it does not (`z = 0`), the estimand is
the population mean of a binary outcome, and with no assumption at all about the
unsettled entries the estimand's **identification region** is the interval

    [ yes / N ,  (yes + free) / N ]

where `free` is the number of entries whose verdict could still go either way. Its
width is exactly `free / N` — the unsettled fraction — and none of that width is
sampling error: read the whole catalogue and the width does not move. An assumption
about the unsettled entries narrows the interval; the instrument's whole purpose is to
report which assumption bought which contraction, and to say when two of them together
admit no value at all.

Three assumption families are implemented, each of which a caller states explicitly:

  `recall`     — a screen sees everything of the kind it looks for, so every unscreened
                 entry is a `no`. Untestable from the screen alone.
  `floor`      — an independent estimate puts the total number of `yes` entries at or
                 above some value (two disjoint screens give one; see `capture()`).
  `monotone`   — the rate of `yes` among the entries no screen flagged is at most the
                 rate among the entries one did. Weak, and stateable in a sentence.

`region()` composes any subset of them and returns the interval, its width, and — the
point of the exercise — `feasible = False` where the composition is empty, which is a
proof that at least one of the assumptions held is false.

`capture()` is the second-detector arithmetic: two screens built from disjoint word
lists are two detectors of the same property, and the Lincoln–Petersen and Chapman
estimators say how many entries of the kind neither of them saw. The estimators assume
the detectors independent given the property. Two absence-vocabulary lists are not
independent — a work described in those words tends to trip both — and positive
dependence between detectors biases both estimators **downwards**, so their value is a
floor on the total rather than a guess at it. That direction is a property of the
estimator, not a hedge.

No model, no calibration, no random number. Usage as a library:

    import identify
    reg = identify.region(n=521, yes=22, borderline=4, unscreened=466,
                          assume={"recall"})
    cap = identify.capture(a1=20, a2=6, both=4)

Author: the Atelier. Licence: Apache-2.0 with the repository.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

ASSUMPTIONS = ("recall", "floor", "monotone")


@dataclass(frozen=True)
class Region:
    """An identification region for a fraction, plus why it is that wide."""

    n: int
    lo_count: float
    hi_count: float
    assume: frozenset[str]
    feasible: bool = True
    note: str = ""

    @property
    def lo(self) -> float:
        return self.lo_count / self.n

    @property
    def hi(self) -> float:
        return self.hi_count / self.n

    @property
    def width(self) -> float:
        return self.hi - self.lo

    @property
    def midpoint(self) -> float:
        """The assumption-free point estimate that minimises the largest squared bias
        the region admits — Manski (2022) §3.1.2. Reported, never used as the answer."""
        return (self.lo + self.hi) / 2

    def as_dict(self) -> dict:
        return {
            "assume": sorted(self.assume),
            "feasible": self.feasible,
            "lo_count": self.lo_count,
            "hi_count": self.hi_count,
            "lo": self.lo,
            "hi": self.hi,
            "width": self.width,
            "midpoint": self.midpoint,
            "note": self.note,
        }


@dataclass(frozen=True)
class Capture:
    """Two detectors, and what they say about what neither of them saw."""

    a1: int
    a2: int
    both: int
    seen: int
    lincoln_petersen: float
    chapman: float
    unseen_lp: float
    unseen_chapman: float
    bias_direction: str = field(
        default=(
            "downwards: the two word lists both name absence, so an entry of the kind "
            "trips both more often than independence allows, which inflates `both` and "
            "shrinks the estimate. Read the value as a floor on the total."
        )
    )

    def as_dict(self) -> dict:
        return {
            "a1": self.a1, "a2": self.a2, "both": self.both, "seen": self.seen,
            "lincoln_petersen": self.lincoln_petersen, "chapman": self.chapman,
            "unseen_lp": self.unseen_lp, "unseen_chapman": self.unseen_chapman,
            "bias_direction": self.bias_direction,
        }


def capture(a1: int, a2: int, both: int) -> Capture:
    """Lincoln–Petersen and Chapman totals from a two-detector overlap.

    `a1` and `a2` are the entries of the kind each detector caught (each counting the
    ones both caught), `both` the overlap. Lincoln–Petersen is `a1 * a2 / both` and is
    undefined at `both = 0`; Chapman's `(a1+1)(a2+1)/(both+1) − 1` is defined there and
    is the less biased of the two at small counts. Both assume the detectors independent
    given the property — see `Capture.bias_direction`."""
    if min(a1, a2, both) < 0 or both > min(a1, a2):
        raise ValueError("an overlap cannot exceed either detector's catch")
    seen = a1 + a2 - both
    lp = (a1 * a2 / both) if both else math.inf
    ch = (a1 + 1) * (a2 + 1) / (both + 1) - 1
    return Capture(a1, a2, both, seen, lp, ch, lp - seen, ch - seen)


def region(
    n: int,
    yes: int,
    borderline: int,
    unscreened: int,
    assume: set[str] | frozenset[str] = frozenset(),
    floor_count: float | None = None,
    screened_rate_max: float | None = None,
) -> Region:
    """The identification region for `yes / n` under the assumptions named in `assume`.

    `yes` are the entries settled as of the kind, `borderline` the ones read and not
    settled, `unscreened` the ones no screen flagged and nobody read. `floor_count` is
    required by `floor`, `screened_rate_max` by `monotone`; an assumption named without
    its number raises. An empty composition returns `feasible = False` rather than a
    reversed interval, because two assumptions that admit no value are a finding."""
    bad = set(assume) - set(ASSUMPTIONS)
    if bad:
        raise ValueError(f"unknown assumption(s): {sorted(bad)}")
    assume = frozenset(assume)
    lo, hi = float(yes), float(yes + borderline + unscreened)
    notes: list[str] = []

    if "recall" in assume:
        hi = float(yes + borderline)
        notes.append("unscreened entries are all `no`")
    if "monotone" in assume:
        if screened_rate_max is None:
            raise ValueError("`monotone` needs `screened_rate_max`")
        cap = yes + borderline + unscreened * screened_rate_max
        hi = min(hi, cap)
        notes.append("the unscreened rate is at most the screened rate")
    if "floor" in assume:
        if floor_count is None:
            raise ValueError("`floor` needs `floor_count`")
        lo = max(lo, float(floor_count))
        notes.append("an independent estimate puts the total at or above the floor")

    feasible = lo <= hi + 1e-12
    return Region(n, lo, hi, assume, feasible, "; ".join(notes))


def ladder(
    n: int,
    yes: int,
    borderline: int,
    unscreened: int,
    floor_count: float,
    screened_rate_max: float,
) -> list[Region]:
    """Every composition of the three assumptions, in order of how many are held.

    2**3 = 8 rows, which is why this figure is worth making interactive: a page can draw
    four bars honestly and a reader can hold any of the eight."""
    out: list[Region] = []
    for k in range(len(ASSUMPTIONS) + 1):
        for combo in _subsets(ASSUMPTIONS, k):
            out.append(region(n, yes, borderline, unscreened, frozenset(combo),
                              floor_count, screened_rate_max))
    return out


def _subsets(items: tuple[str, ...], k: int) -> list[tuple[str, ...]]:
    if k == 0:
        return [()]
    if k > len(items):
        return []
    head, *rest = items
    with_head = [(head, *s) for s in _subsets(tuple(rest), k - 1)]
    return with_head + _subsets(tuple(rest), k)


def hyper_ge(n: int, k_total: int, draws: int, k: int) -> float:
    """Exact P(X >= k) for X ~ Hypergeometric(n, k_total, draws). No simulation."""
    total = math.comb(n, draws)
    return sum(
        math.comb(k_total, x) * math.comb(n - k_total, draws - x)
        for x in range(k, min(k_total, draws) + 1)
    ) / total


def fisher_one_sided(a: int, b: int, c: int, d: int) -> float:
    """Fisher's exact test, one-sided towards a larger `a`, in exact integer combinatorics.

    The 2x2 is [[a, b], [c, d]]. Used here for one claim only, and reported beside the
    hypergeometric tail it corrects, because the two answer different questions."""
    n = a + b + c + d
    row1, col1 = a + b, a + c
    total = math.comb(n, col1)
    return sum(
        math.comb(row1, x) * math.comb(n - row1, col1 - x)
        for x in range(max(0, col1 - (n - row1)), min(row1, col1) + 1)
        if x >= a
    ) / total


if __name__ == "__main__":  # a worked example, so the module is checkable by running it
    cap = capture(a1=20, a2=6, both=4)
    print(f"two detectors: seen {cap.seen}, Lincoln–Petersen {cap.lincoln_petersen:.1f}, "
          f"Chapman {cap.chapman:.1f}")
    for r in ladder(521, 22, 4, 466, cap.lincoln_petersen, 26 / 55):
        held = "+".join(sorted(r.assume)) or "nothing"
        if r.feasible:
            print(f"{held:>28}  [{r.lo:.4f}, {r.hi:.4f}]  width {100 * r.width:6.2f} pts")
        else:
            print(f"{held:>28}  no value satisfies these together")
