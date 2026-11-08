"""Independent audit of the uploaded v17 KYLIN-II conditional scaling example.

The data are Yue et al. (2017), Table 2 (theoretical values). The two
model-pipe closures and the unchanged model HS/EV losses are *scenarios*.
Run: python outputs/design-v17-independent-audit-20261108.py
"""

import csv
import math
from pathlib import Path


TABLE = [
    # prototype mass flow, HS, EV, pipe, total, pipe Re
    (0.25, 2.9, 2.5, 19.1, 24.5, 5560.0),
    (0.50, 2.8, 2.5, 18.9, 24.2, 11100.0),
    (0.75, 2.8, 2.5, 18.5, 23.8, 16700.0),
    (1.00, 2.7, 2.5, 18.1, 23.3, 22300.0),
    (1.25, 2.6, 2.5, 17.7, 22.8, 27800.0),
]

D_P = 0.026
D_M = D_P * 0.616
L_M = 11.0 * 0.5
MU = 2.2019e-3
MASS_RATIO = 0.2683
BASE = Path(__file__).resolve().parent


def re_pipe(m):
    return 4.0 * m / (math.pi * D_M * MU)


def f_yue_implied(re):
    """Log-linear interpolation/extrapolation of Yue Table 2, NOT measured f."""
    points = [(row[5], (row[3] - 1.0) * D_P / 11.0) for row in TABLE]
    k = next((i for i in range(4) if re <= points[i + 1][0]), 3)
    r0, f0 = points[k]
    r1, f1 = points[k + 1]
    t = math.log(re / r0) / math.log(r1 / r0)
    return f0 * (f1 / f0) ** t


def f_smooth(re):
    return 0.3164 * re ** (-0.25)


def model_k(m, hs, ev, valve, friction):
    return 1.0 + friction(re_pipe(m)) * L_M / D_M + hs + ev + valve


def solve_mass(ideal_mass, kp, hs, ev, valve, friction):
    """Solve x^3 K_M(x*m_ideal)/K_P = 1 by sign bisection."""
    def residual(x):
        return x ** 3 * model_k(x * ideal_mass, hs, ev, valve, friction) / kp - 1.0

    lo, hi = 0.2, 2.0
    assert residual(lo) < 0 < residual(hi)
    for _ in range(90):
        mid = (lo + hi) / 2.0
        if residual(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def main():
    design = TABLE[-1]
    ideal_design = MASS_RATIO * design[0]
    valves = {
        "A_Bla": design[4] - model_k(ideal_design, design[1], design[2], 0.0, f_smooth),
        "B_Yue": design[4] - model_k(ideal_design, design[1], design[2], 0.0, f_yue_implied),
    }
    frictions = {"A_Bla": f_smooth, "B_Yue": f_yue_implied}

    out = []
    for m_p, hs, ev, _pipe, kp, _re in TABLE:
        ideal = m_p * MASS_RATIO
        row = {"m_P_kg_s": m_p, "m_M_ideal_kg_s": ideal,
               "Re_M_ideal": re_pipe(ideal),
               "Re_HS_M_ideal": 4.0 * ideal / (math.pi * 0.076 * 0.616 * MU),
               "K_P_Yue": kp}
        for name, friction in frictions.items():
            valve = valves[name]
            k_at_ideal = model_k(ideal, hs, ev, valve, friction)
            x = solve_mass(ideal, kp, hs, ev, valve, friction)
            k_at_actual = model_k(x * ideal, hs, ev, valve, friction)
            row[f"K_M_ideal_{name}"] = k_at_ideal
            row[f"D_frozen_percent_{name}"] = 100 * ((k_at_ideal / kp) ** (-1 / 3) - 1)
            row[f"K_M_solved_{name}"] = k_at_actual
            row[f"D_forward_percent_{name}"] = 100 * (x - 1)
            row[f"Re_M_solved_{name}"] = re_pipe(x * ideal)
            row[f"residual_{name}"] = x ** 3 * k_at_actual / kp - 1
        out.append(row)

    output = BASE / "design-v17-independent-audit-20261108.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)

    print(f"valve K: {valves}")
    print("m_P  Re_M  D_frozen_A  D_forward_A  D_frozen_B  D_forward_B")
    for r in out:
        print(f"{r['m_P_kg_s']:.2f} {r['Re_M_ideal']:.0f} "
              f"{r['D_frozen_percent_A_Bla']:+.5f} {r['D_forward_percent_A_Bla']:+.5f} "
              f"{r['D_frozen_percent_B_Yue']:+.5f} {r['D_forward_percent_B_Yue']:+.5f}")
    print(f"3% K interval: [{1.03**-3:.9f}, {0.97**-3:.9f}]")
    b1 = 2.5 * 0.50 + 2.6 * 0.20 + f_smooth(re_pipe(ideal_design)) * L_M / D_M * 0.20 + 11.4 * 0.005
    print(f"v17 linear corner: {100*b1/22.8/3:.5f}%")
    print(f"same lumped K corner evaluated exactly: "
          f"{100*((1+b1/22.8)**(-1/3)-1):+.5f}%, "
          f"{100*((1-b1/22.8)**(-1/3)-1):+.5f}%")
    for name, friction in frictions.items():
        m0 = ideal_design
        h = 1e-5
        kp_plus = model_k(m0*math.exp(h), 2.6, 2.5, valves[name], friction)
        kp_minus = model_k(m0*math.exp(-h), 2.6, 2.5, valves[name], friction)
        slope = (math.log(kp_plus)-math.log(kp_minus))/(2*h)
        print(f"{name} model K flow slope at design: {slope:+.8f}; "
              f"implicit dln(m/m_ideal)/dln(K multiplier)={-1/(3+slope):+.8f}")
    beta = (D_P ** 2) / (0.054 ** 2 - 0.022 ** 2)
    re_hs = 4 * 1.25 / (math.pi * 0.076 * MU)
    f_hs = 0.685 * re_hs ** (-0.30)
    kfr = f_hs * 1.8 / (0.054 - 0.022) * beta ** 2
    total = 1.29 + 0.64 + kfr + 0.5 * (1 - beta)
    corrected = 1.29 + (1 - beta) ** 2 + kfr + 0.5 * (1 - beta)
    print(f"HS Re {re_hs:.2f}; beta {beta:.7f}; kfr {kfr:.6f}")
    print(f"HS original sum {total:.6f}, residual {2.6-total:.6f}")
    print(f"HS with Borda-Carnot {corrected:.6f}, residual {2.6-corrected:.6f}")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
