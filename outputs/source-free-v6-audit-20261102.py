#!/usr/bin/env python3
"""Audit v6's portable bound and connect its model to local perturbation.

Uses the archived v5 scalar model; numerical checks do not certify physical
parameter ranges. Run from any directory. Standard library only.
"""

import csv
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
src = HERE / "source-free-v5-upload-20261102.py"
spec = importlib.util.spec_from_file_location("v5", src)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def model(c=1, delta=0):
    return v.Model(.5, .5*c, 2, v.QR_ZHAO, .25, delta=delta)


def main():
    print("-- General c=lambda/d: v6 and corrected conditional bounds --")
    for c, delta in ((.5, 0), (.5, -.5), (1, 0), (2, 0)):
        m = model(c, delta)
        B = (m.i_Rid.a*.5)**.25
        A = 1+delta
        q = (c*B)**(1/(3-.25))
        D0, D1 = m.D_s(0), m.D_s(1)
        v6lo = min(0, A**(1/3)-1)
        v6hi = max(A**(1/3), q)-1
        safe_lo = min(1, A**(1/3), q)-1
        safe_hi = max(1, A**(1/3), q)-1
        print(f"c={c}, delta={delta}: D endpoints=({100*D0:+.6f}%,"
              f" {100*D1:+.6f}%), v6=[{100*v6lo:+.6f}%,"
              f" {100*v6hi:+.6f}%], corrected=[{100*safe_lo:+.6f}%,"
              f" {100*safe_hi:+.6f}%]")
        assert safe_lo-1e-12 <= min(D0,D1) <= max(D0,D1) <= safe_hi+1e-12
    m = model(.5, 0)
    assert m.D_s(1) < 0  # v6 lower says 0
    m = model(.5, -.5)
    q = (.5*(m.i_Rid.a*.5)**.25)**(1/(3-.25))
    assert m.D_s(1) > max(.5**(1/3),q)-1  # v6 upper says too low

    print("-- Perturbation is the local derivative of the same implicit model --")
    w, delta = .2, 0
    m = model(1, delta)
    x = m.solve_s(w)
    Ti = m.T_s(x)
    cpR = m._cp_s(Ti)/m._cp_s(m.T_P)
    Fx = m.Fx_iv(v.I(x), v.I(w))
    Fx_mid = (Fx.a+Fx.b)/2
    dD_dw = cpR*(m.f_s(x)-(1+delta))/Fx_mid
    dD_ddelta = cpR*(1-w)/Fx_mid
    h = 1e-4
    fdw = (m.D_s(w+h)-m.D_s(w-h))/(2*h)
    fdd = (model(1,delta+h).D_s(w)-model(1,delta-h).D_s(w))/(2*h)
    print(f"w={w},delta={delta}, D={100*(x-1):+.5f}%")
    print(f"dD/dw implicit={dD_dw:.9f}, finite difference={fdw:.9f}")
    print(f"dD/ddelta implicit={dD_ddelta:.9f}, finite difference={fdd:.9f}")
    assert abs(dD_dw-fdw)<1e-6 and abs(dD_ddelta-fdd)<1e-6

    with (HERE / "zhao-3pct-band-v6-upload-20261102.csv").open(newline="") as f:
        new = list(csv.DictReader(f))
    with (HERE / "zhao-three-percent-design-region-20261102.csv").open(newline="") as f:
        old = list(csv.DictReader(f))
    Klo=.97**3/m.M_s(.97);Khi=1.03**3/m.M_s(1.03)
    flo=m.f_s(.97);fhi=m.f_s(1.03)
    def band(d):
        A=1+d
        return (max(0,(Klo-A)/(flo-A)),min(1,(Khi-A)/(fhi-A)))
    e_low=max(abs(float(r["w_min_clipped"])-band(float(r["delta"]))[0])
              for r in new)
    e_up=max(abs(float(r["w_max_clipped"])-band(float(r["delta"]))[1])
             for r in new)
    print(f"uploaded v6 CSV {len(new)} data rows (prior grid {len(old)} rows);"
          f" max errors vs formula w_min={e_low:.3e}, w_max={e_up:.3e}")


if __name__ == "__main__":
    main()
