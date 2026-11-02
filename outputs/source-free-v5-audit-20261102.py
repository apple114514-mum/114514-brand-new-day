#!/usr/bin/env python3
"""Audit v5's delta-dependent bound and derive the two-sided 3% design band.

Standard library only. Run next to source-free-v5-upload-20261102.py.
Scalar roots below are diagnostics, not new interval certificates.
"""

import importlib.util
import csv
from pathlib import Path
import sys

sys.dont_write_bytecode = True
src = Path(__file__).with_name("source-free-v5-upload-20261102.py")
spec = importlib.util.spec_from_file_location("source_free_v5", src)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def model(delta=0):
    return v.Model(0.5, 0.5, 2.0, v.QR_ZHAO, 0.25, delta=delta)


def w_at_target(c, x, delta):
    """Invert F(x,w)=0 at a fixed target x; lambda/d=1 in this case."""
    A = 1 + delta
    K = x**3 / c.M_s(x)
    f = c.f_s(x)
    return (K-A)/(f-A)


def main():
    c = model()
    targets = (.97, 1.03)
    for x in targets:
        K = x**3 / c.M_s(x)
        print(f"target x={x}: K={K:.12f}, f={c.f_s(x):.12f},"
              f" exact delta at w=0={K-1:+.9f}")

    for delta in (-.20, -.10, -.09, 0, .07, .09274):
        m = model(delta)
        wl, wu = [w_at_target(m, x, delta) for x in targets]
        wl, wu = max(0, wl), min(1, wu)
        print(f"delta={delta:+.5f}: D(0)={100*m.D_s(0):+.6f}%,"
              f" w feasible in [{wl:.8f},{wu:.8f}]")
        assert wl <= wu
    assert model(.09274).D_s(0) < .03
    assert model(-.10).D_s(0) < -.03 < model(-.10).D_s(.10)

    x1 = c.solve_s(1)
    M1 = c.M_s(x1)
    xbar = (c.i_Rid.a * .5) ** (.25/(3-.25))
    ana = xbar**3 - 1
    num = x1**3/M1 - 1
    root_slack = xbar**3 - x1**3
    property_term = x1**3 * (1 - 1/M1)
    print(f"delta thresholds: analytic={ana:.9f}, endpoint={num:.9f},"
          f" difference={ana-num:.9f}")
    print(f"difference components: root slack={root_slack:.9f},"
          f" property correction={property_term:.9f}")

    # Tests the literal phrase "for every delta>-1" against the same
    # polynomial property functions continued beyond their useful range.
    x = 6.0
    M = c.M_s(x)
    delta = x**3/M - 1
    claimed = max((1+delta)**(1/3), xbar)
    print(f"large-delta algebraic counterexample: x={x},"
          f" T={c.T_s(x):.3f} K, M={M:.9f},"
          f" delta={delta:.6f}, claimed x upper={claimed:.9f}")
    assert M > 1 and x > claimed

    m = model(-.99)
    x = m.solve_s(0)
    print(f"delta=-.99: x(w=0)={x:.9f}, f(x)={m.f_s(x):.9f}"
          " (the premise f>=1 is not global)")
    assert m.f_s(x) < 1

    d = model(.1)
    a = d.F_iv(v.I(1), v.I(0))
    b = d.F_dep_iv(v.I(1), v.I(0))
    print("v5 F_dep_iv at delta=.1,w=0: actual F interval", a,
          "returned", b)
    assert a.b < b.a

    if len(sys.argv) == 3 and sys.argv[1] == "--csv":
        limit = 1.03**3 / c.M_s(1.03) - 1
        with Path(sys.argv[2]).open("w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out)
            writer.writerow(["delta_scenario", "w_min_for_abs_D_le_3pct",
                             "w_max_for_abs_D_le_3pct", "D_at_w0_percent"])
            for i in range(81):
                delta = -.20 + (limit + .20) * i / 80
                m = model(delta)
                wl, wu = [w_at_target(m, x, delta) for x in targets]
                writer.writerow([f"{delta:.12f}", f"{max(0,wl):.12f}",
                                 f"{min(1,wu):.12f}", f"{100*m.D_s(0):.9f}"])
        print("wrote numerical scenario grid:", sys.argv[2])


if __name__ == "__main__":
    main()
