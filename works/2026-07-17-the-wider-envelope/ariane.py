#!/usr/bin/env python3
# The Wider Envelope — works/2026-07-17-the-wider-envelope/ariane.py
#
# The error mechanism, run for real (stdlib only, deterministic).
#
# Subject: the loss of Ariane 5 Flight 501, 4 June 1996. The maiden flight of
# the launcher veered off its path at about H0 + 37 s, at an altitude of about
# 3700 m, broke up and exploded. The trigger was a single arithmetic operation:
# the conversion of a 64-bit floating-point value (the internal alignment result
# BH, "Horizontal Bias") to a 16-bit signed integer. The value was larger than a
# 16-bit signed integer can hold, which raised an "Operand Error"; that
# conversion was not protected; the Inertial Reference System stopped.
# (ESA/CNES Inquiry Board, chaired by Prof. J.-L. Lions, Paris, 19 July 1996.)
#
# The point of this file is that the conversion below is the REAL operation, not
# a picture of it. A 16-bit signed integer holds [-32768, 32767]. Feed the same
# routine BH values from two trajectories and it returns a clean integer for one
# and raises for the other. The code does not change between the two runs. The
# world it runs in does.
#
# What is real here and what is schematic (stated plainly, no invention):
#   REAL, from the Inquiry Board report:
#     - 64-bit float -> 16-bit signed integer conversion; the Operand Error.
#     - the overflowing variable is BH, Horizontal Bias.
#     - "Ariane 5 has a high initial acceleration and a trajectory which leads to
#       a build-up of horizontal velocity which is five times more rapid than for
#       Ariane 4." -> the 5x ratio between the two envelopes.
#     - the back-up SRI became inoperative at 36.7 s after H0; the active SRI,
#       "identical ... in hardware and software, failed for the same reason"
#       about 0.05 s later.
#     - the alignment function that computed BH runs on ~40 s into flight and
#       "serves no purpose" after lift-off.
#     - four of seven internal variables were protected; three, including BH,
#       were left unprotected because "further reasoning indicated that they were
#       either physically limited or that there was a large margin of safety, a
#       reasoning which in the case of the variable BH turned out to be faulty."
#       "There is no evidence that any trajectory data were used" in that analysis.
#   REAL, arithmetic: the 16-bit signed range and the overflow point (32767).
#   SCHEMATIC, mine, and marked as such in the work: the ABSOLUTE size and shape
#     of the BH ramp. The report gives the RATIO (5x) and the timing (36.7 s),
#     not the raw telemetry. So the ramp is calibrated to one real datum only --
#     the Ariane-5 envelope is scaled so its conversion overflows at t = 36.7 s --
#     and everything vertical is in schematic units. No absolute BH number here is
#     claimed to be the flight's actual value.

INT16_MAX = 32767            # 2**15 - 1
INT16_MIN = -32768           # -2**15
T = 40.0                     # flight seconds over which the alignment code keeps running
BACKUP_FAIL_T = 36.7         # s after H0, back-up SRI inoperative (report)
ACTIVE_FAIL_OFFSET = 0.05    # s later, active SRI fails for the same reason (report)
RATIO_A4 = 0.2               # Ariane 4 builds horizontal velocity 1/5 as fast (report: 5x)
RATIO_A5 = 1.0               # Ariane 5, the reference envelope


class OperandError(Exception):
    """Raised when a value will not fit the target integer type -- the SRI's fault."""
    def __init__(self, value):
        self.value = value
        super().__init__("Operand Error: %r exceeds 16-bit signed integer range" % value)


def to_int16_signed(x):
    """The real conversion. 64-bit float in; 16-bit signed integer out, or raise.

    Ada's checked conversion raises on a value outside the target's range; the SRI
    left this particular conversion unchecked, so the raise propagated to a halt.
    """
    n = int(x)  # truncate toward zero; the rounding mode is not what breaks
    if n < INT16_MIN or n > INT16_MAX:
        raise OperandError(n)
    return n


# --- the schematic BH ramp, calibrated to the one real timing datum -------------
# BH accumulates while horizontal velocity builds. Ariane 5 accelerates hard off
# the pad, so treat the build-up as accelerating (quadratic in flight time). Scale
# the Ariane-5 ramp so it reaches INT16_MAX exactly at t = 36.7 s (the moment the
# report records the back-up SRI failing). Everything else follows from the 5x
# ratio. A is a schematic constant; it is NOT a claimed BH value.
A = INT16_MAX / (BACKUP_FAIL_T / T) ** 2   # ~= 38924 schematic units


def bh(t, ratio):
    """Horizontal Bias at flight time t (s) for a trajectory of the given steepness."""
    return A * ratio * (t / T) ** 2


def crossing_time(ratio):
    """First flight time at which BH exceeds INT16_MAX, or None within [0, T]."""
    # A * ratio * (t/T)**2 = INT16_MAX  ->  t = T * sqrt(INT16_MAX / (A*ratio))
    peak = bh(T, ratio)
    if peak <= INT16_MAX:
        return None
    return T * (INT16_MAX / (A * ratio)) ** 0.5


def fly(ratio, protected, dt=0.1):
    """Run the alignment conversion every dt seconds of flight. Return the outcome."""
    t = 0.0
    while t <= T + 1e-9:
        raw = bh(t, ratio)
        try:
            to_int16_signed(raw)
        except OperandError as e:
            if protected:
                # a guarded conversion: catch, substitute a safe default, fly on
                pass
            else:
                # the SRI's real choice for BH: the exception halts the unit
                return {"failed": True, "t": round(t, 2), "raw": round(raw, 1),
                        "int": e.value}
        t += dt
    return {"failed": False, "t": None, "raw": round(bh(T, ratio), 1)}


def sample(ratio, n=161):
    """BH ramp sampled for display (n points over [0, T])."""
    pts = []
    for i in range(n):
        t = T * i / (n - 1)
        pts.append([round(t, 3), round(bh(t, ratio), 2)])
    return pts


def build():
    return {
        "subject": "Ariane 5 Flight 501, 4 June 1996 — loss traced to a 64-bit "
                   "float to 16-bit signed integer conversion (variable BH, "
                   "Horizontal Bias). ESA/CNES Inquiry Board (Lions), 19 July 1996.",
        "constants": {
            "int16_max": INT16_MAX,
            "int16_min": INT16_MIN,
            "flight_window_s": T,
            "backup_fail_t": BACKUP_FAIL_T,
            "active_fail_offset": ACTIVE_FAIL_OFFSET,
            "ratio_a4": RATIO_A4,
            "ratio_a5": RATIO_A5,
            "bh_scale_A": round(A, 3),
            "note": "vertical units are SCHEMATIC; only the 5x ratio and the "
                    "t=36.7s crossing are anchored to the report.",
        },
        "envelopes": {
            "ariane4": {"ratio": RATIO_A4, "crossing": crossing_time(RATIO_A4),
                        "outcome_unprotected": fly(RATIO_A4, False)},
            "ariane5": {"ratio": RATIO_A5, "crossing": crossing_time(RATIO_A5),
                        "outcome_unprotected": fly(RATIO_A5, False)},
        },
        # the steepness at which the crossing first enters the flight window:
        "critical_ratio": round(INT16_MAX / A, 4),   # BH(T)=MAX  -> (36.7/40)^2
        "ramp_a4": sample(RATIO_A4),
        "ramp_a5": sample(RATIO_A5),
    }


if __name__ == "__main__":
    import json
    import os

    data = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2)

    a4 = data["envelopes"]["ariane4"]
    a5 = data["envelopes"]["ariane5"]
    print("16-bit signed range: [%d, %d]" % (INT16_MIN, INT16_MAX))
    print("critical steepness (crossing enters the 40 s window): %.4f of Ariane 5"
          % data["critical_ratio"])
    print("Ariane 4 (0.2x): crossing =", a4["crossing"],
          "| unprotected outcome:", a4["outcome_unprotected"])
    print("Ariane 5 (1.0x): crossing = %.3f s | unprotected outcome: %s"
          % (a5["crossing"], a5["outcome_unprotected"]))
    # the one real check: the reference envelope must overflow at 36.7 s
    assert abs(a5["crossing"] - BACKUP_FAIL_T) < 1e-6, "Ariane 5 must cross at 36.7 s"
    assert a4["crossing"] is None, "Ariane 4 must never cross in the flight window"
    print("checks passed — same conversion, two envelopes, one Operand Error.")
