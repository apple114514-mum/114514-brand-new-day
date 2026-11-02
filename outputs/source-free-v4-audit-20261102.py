#!/usr/bin/env python3
"""Audit v4's claimed w bounds, derivative, and KYLIN root behavior.

Run next to source-free-v4-upload-20261102.py. Standard library only.
This reuses its interval kernel to test a narrower root tube; it does not
independently certify libm's assumed ulp errors.
"""

import importlib.util
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
src = Path(__file__).with_name("source-free-v4-upload-20261102.py")
spec = importlib.util.spec_from_file_location("uploaded_v4", src)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def dependent_F(c, x, w):
    """Equivalent F with the shared w kept as 1+w(Af-1)."""
    xi = v.I(x)
    Ti = c.T_iv(xi)
    rhoR = c.props.rho(Ti) / c.props.rho(c.T_P_iv)
    cpR = c.props.cp(Ti) / c.props.cp(c.T_P_iv)
    mismatch = v.I(c.lam / c.d) * c.f_iv(xi, Ti) - v.I(1)
    return xi**3 * rhoR - cpR * (v.I(1) + w * mismatch)


def main():
    qr = 4 * math.sqrt(2)
    zhao = v.Model(.5, .5, 2, qr, .25,
                   Q_R_iv=v.I(4) * v.i_sqrt(v.I(2)))
    root = zhao.root_iv(v.I(1), .98, 1.16)
    print("Zhao w=1 root interval:", root, "width", root.w)

    x = 1.1
    T = zhao.T_s(x)
    cpR = zhao._cp_s(T) / zhao._cp_s(zhao.T_P)
    rhoR = zhao._rho_s(T) / zhao._rho_s(zhao.T_P)
    loss_mismatch = zhao.lam/zhao.d * zhao.f_s(x) - 1
    actual_Fw = -cpR * loss_mismatch
    reported_Fw = zhao.Fw_iv(v.I(x), v.I(1))
    print("F_w at x=1.1, true formula:", f"{actual_Fw:.12f}")
    print("v4 Fw_iv:", reported_Fw)
    print("true derivative in interval:", reported_Fw.has(actual_Fw))
    print("rho ratio:", f"{rhoR:.12f}")

    for delta in (0, .07, .35, .4):
        c = v.Model(.5, .5, 2, qr, .25, delta=delta,
                    Q_R_iv=v.I(4) * v.i_sqrt(v.I(2)))
        print(f"delta={delta:.2f}: D(w=0)={100*c.D_s(0):+.6f}%,"
              f" D(w=1)={100*c.D_s(1):+.6f}%")
    x1 = zhao.solve_s(1)
    threshold = x1**3/zhao.M_s(x1) - 1
    print("delta where w=0 and w=1 give equal D:", f"{threshold:.9f}")

    for props in (v.P_ZHAO, v.P_XU):
        c = v.Model(.5**.7, .5, 2, 1/.268, .25, props=props)
        a, b = .99998, 1.00001
        w = v.I(0, 1)
        Fa, Fb = dependent_F(c, a, w), dependent_F(c, b, w)
        tube = v.I(a, b)
        mismatch = v.I(c.lam/c.d) * c.f_iv(tube, c.T_iv(tube)) - v.I(1)
        Fx = c.Fx_iv(tube, w)
        print(props.name, "F(a)", Fa, "F(b)", Fb,
              "(lambda/d)f-1", mismatch, "F_x", Fx)
        assert Fa.b < 0 < Fb.a
        assert mismatch.b < 0 and Fx.a > 0
        print("=> for every w in [0,1], root stays in the tube; D decreases with w")

    rounded = v.Model(.5**.7, .5, 2, 1/.268, .25)
    exact_scaling = v.Model(.5**.7, .5, 2, 1/(.5**1.9), .25)
    print("rounded m_R=.268, w=1 D (%):", f"{100*rounded.D_s(1):+.8f}")
    print("analytic m_R=c^1.9, w=1 D (%):", f"{100*exact_scaling.D_s(1):+.8f}")


if __name__ == "__main__":
    main()
