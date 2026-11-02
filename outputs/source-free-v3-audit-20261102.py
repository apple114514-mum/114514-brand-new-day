#!/usr/bin/env python3
"""Focused reproducibility checks for the uploaded source_free_bound_v3.py.

Place the archived v3 source in the same directory.  Uses only the standard
library and deliberately does not claim certified floating point bounds.
"""

import importlib.util
from pathlib import Path


SOURCE = Path(__file__).with_name("source-free-v3-upload-20261102.py")
spec = importlib.util.spec_from_file_location("source_free_v3", SOURCE)
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)


def exact_fx_formula(c, x, w):
    """Analytic F_x, including viscosity's temperature derivative."""
    t = c.T_in + c.prop(x)[3] / 2
    cp = v3.cp_z(t)
    dcp = -0.0272 + 2 * 7.12e-6 * t
    dt = 2 * (t - c.T_in)
    tp = cp * dt / (x * (dcp * dt + 2 * cp))
    m = (cp / v3.cp_z(c.T_P)) / (v3.rho_z(t) / v3.rho_z(c.T_P))
    mp = m * tp * (dcp / cp + 1.1944 / v3.rho_z(t))
    friction = (c.R_id * x * c.d * v3.mu_up(t) / v3.mu_up(c.T_P)) ** c.n
    g = (1 - w) * (1 + c.delta) + w * (c.lam / c.d) * friction
    dlog_mu_dx = (-754.1 / t**2) * tp
    gp = w * c.lam / c.d * c.n * friction * (1 / x + dlog_mu_dx)
    return 3 * x*x - mp * g - m * gp


def main():
    c = v3.Model(0.5, 0.5, 2.0, v3.QR_IDEAL, 0.25)
    x = 1.0
    claimed = c.Fx_iv(v3.I(x), v3.I(1.0))
    actual = exact_fx_formula(c, x, 1.0)
    print("F_x at x=1,w=1, full analytic formula:", f"{actual:.12f}")
    print("v3 Fx_iv returned:", claimed)
    print("True derivative lies in returned interval:", claimed.a <= actual <= claimed.b)

    for a, b in ((0.98, 1.16), (0.55, 1.05)):
        h = (b - a) / 12
        gaps = []
        for i in range(11):
            right = (a + h*i) + h
            left = a + h*(i+1)
            if right < left:
                gaps.append((i, left-right))
        print(f"x-box grid [{a},{b}]:", len(gaps), "uncovered gaps", gaps)

    d = -0.07
    cdelta = v3.Model(0.5, 0.5, 2.0, v3.QR_IDEAL, 0.25, delta=d)
    numeric = cdelta.D(0.0)
    proposed_closed = (1+d)**(1/3)-1
    print("delta=-0.07,w=0 true model D (%):", f"{100*numeric:.7f}")
    print("proposed closed form D (%):", f"{100*proposed_closed:.7f}")
    print("difference (percentage points):", f"{100*(numeric-proposed_closed):.7f}")
    print("K mismatch for +7.3% mass-flow deviation:", f"{1.073**3-1:.9f}")
    print("if delta alone caused it, delta at w=0/0.5:",
          f"{1.073**3-1:.6f}", f"{2*(1.073**3-1):.6f}")


if __name__ == "__main__":
    main()
