"""Explore implicit derivatives of the frozen v3 forward model.

Finite differences here are DISCOVERY data, not a continuous-domain proof.
They identify which parameter signs may admit an analytic proof and which
require a branch split.  The three M-only hydraulic axes also have a simple
symbolic ordering, documented in the accompanying report.
"""

import csv
import itertools
import math
from pathlib import Path

import core_v2 as C

ROOT = Path(__file__).resolve().parent
POWERS = (3000., 6000.)


def residual(side, m, power, x):
    kp, km = C.kw_from_vec(x)
    if side == "P":
        kw = kp
        loop = C.P
    else:
        kw = km
        loop = C.M
    tin = C.T_IN_REF + kw.pop("dtin")
    kw["k_clamp"] = False
    state = C.march(loop, m, power, tin, **kw)
    return state["dp_buoy"] - state["dp_fric"]


def param_diff(side, m, power, x, i, fraction):
    lo, hi = C.BOUNDS[i]
    h = (hi-lo)*fraction
    xx = list(x)
    if x[i] <= lo+h:
        f0 = residual(side,m,power,xx)
        xx[i] += h
        return (residual(side,m,power,xx)-f0)/h
    if x[i] >= hi-h:
        f0 = residual(side,m,power,xx)
        xx[i] -= h
        return (f0-residual(side,m,power,xx))/h
    xx[i] += h
    fp = residual(side,m,power,xx)
    xx[i] -= 2*h
    fm = residual(side,m,power,xx)
    return (fp-fm)/(2*h)


def main():
    rows=[]
    for power in POWERS:
        for bits in itertools.product((0,1), repeat=len(C.NAMES)):
            x=[C.BOUNDS[i][bit] for i,bit in enumerate(bits)]
            roots=C.fom(x,power)
            if roots is None:
                raise RuntimeError((power,bits))
            mp=roots["rp"]["m"]
            mm=roots["rm"]["m"]
            h_p=mp*1e-4
            h_m=mm*1e-4
            fm_p=(residual("P",mp+h_p,power,x)-residual("P",mp-h_p,power,x))/(2*h_p)
            fm_m=(residual("M",mm+h_m,power,x)-residual("M",mm-h_m,power,x))/(2*h_m)
            if min(abs(fm_p),abs(fm_m)) == 0:
                raise RuntimeError('zero sampled residual slope')
            for i,name in enumerate(C.NAMES):
                px=param_diff("P",mp,power,x,i,1e-3)
                mx=param_diff("M",mm,power,x,i,1e-3)
                deriv=-mx/(mm*fm_m)+px/(mp*fm_p)
                rows.append(dict(power_kW=power/1000,axis=name,
                                 corner_bits=''.join(map(str,bits)),
                                 dlog_massflux_daxis=deriv,
                                 Fm_P=fm_p,Fm_M=fm_m,
                                 Re_P=roots["rp"]["re"],
                                 Re_M=roots["rm"]["re"]))
    with (ROOT/'proof_scout_v5_20261109.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
    print('Residual root slope P:',min(r['Fm_P'] for r in rows),max(r['Fm_P'] for r in rows))
    print('Residual root slope M:',min(r['Fm_M'] for r in rows),max(r['Fm_M'] for r in rows))
    print('Re P:',min(r['Re_P'] for r in rows),max(r['Re_P'] for r in rows))
    print('Re M:',min(r['Re_M'] for r in rows),max(r['Re_M'] for r in rows))
    for name in C.NAMES:
        s=[r['dlog_massflux_daxis'] for r in rows if r['axis']==name]
        sign='MIXED' if min(s)<0<max(s) else ('positive' if min(s)>0 else 'negative')
        print(f'{name:12s} {min(s):+.7g} .. {max(s):+.7g} {sign}')


if __name__=='__main__':
    main()
