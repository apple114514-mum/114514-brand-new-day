#!/usr/bin/env python3
"""Audit the uploaded Zhao 2020 paired forward model with consistent FoMs.

This is a conditional, retrospective diagnostic. Prototype K is inverted
from Zhao Table 5 CFD, and gross diameters from Table 3 are assumed to be
flow diameters. Select the uploaded exponential viscosity (default) for a
direct comparison, or Zhao Table 4's polynomial with --viscosity zhao.
No physical bound is claimed.

The energy equation uses the *integral* of Zhao Table 4 cp(T). A bracketed
root solves facility mass flow, with Reynolds ratio evaluated at the trial
mass flow. One CFD pair can conditionally fit (effective heat, friction
share), but it is then fully spent on calibration and cannot validate the
model. Run: python outputs/paired-forward-consistency-20261101.py > result.csv
For the same-source property check, append --viscosity zhao.
"""

import csv
import math
import sys
import argparse


G = 9.80665
TIN = 533.15
MP, DTP, MM_OBS, DTM_OBS = 540.0, 130.0, 92.79, 136.70
QP_DESIGN, QM_DESIGN = 10e6, 1.77e6
DP, DM, HP, HM = 1.0, 0.5, 2.0, 1.0
AP, AM = math.pi*DP**2/4, math.pi*DM**2/4
IDEAL_M = 2**2.5
IDEAL_MM = MP/IDEAL_M
B = 1.1944


def rho(t):
    return 11096.0 - B*t


def mu_uploaded(t):
    return 4.94e-4 * math.exp(754.1/t)


def mu_zhao_table4(t):
    """Zhao 2020 Table 4, Pa s; T is kelvin."""
    return 4.56e-3 - 7.03e-6*t + 3.61e-9*t*t


mu = mu_uploaded


def enthalpy_primitive(t):
    return 159*t - 0.0272*t*t/2 + 7.12e-6*t**3/3


def bisect_increasing(fun, low, high):
    if not fun(low) < 0 < fun(high):
        raise ValueError(f"root not bracketed on [{low}, {high}]")
    for _ in range(90):
        mid = (low+high)/2
        if fun(mid) < 0:
            low = mid
        else:
            high = mid
    return (low+high)/2


def rise_from_heat(q_eff, mass):
    return bisect_increasing(
        lambda dt: mass*(enthalpy_primitive(TIN+dt)-enthalpy_primitive(TIN))-q_eff,
        0.0, 300.0)


TP = TIN + DTP/2
KP = 2*rho(TP)*AP**2*G*B*DTP*HP/MP**2
RE_P = 4*MP/(math.pi*DP*mu(TP))


def state(m, w, q_eff, n=0.25, delta=0.0):
    dt = rise_from_heat(q_eff, m)
    tm = TIN+dt/2
    re_ratio = (4*m/(math.pi*DM*mu(tm)))/RE_P
    f_ratio = re_ratio**(-n)
    k_ratio = 1+w*(f_ratio-1)+(1-w)*delta
    rhs_m2 = 2*rho(tm)*AM**2*G*B*dt*HM/(KP*k_ratio)
    return dict(m=m, dt=dt, tm=tm, re_ratio=re_ratio,
                k_ratio=k_ratio, residual_m2=m*m-rhs_m2,
                Dm=IDEAL_MM/m-1, DT=DTP/dt-1)


def forward(w, q_eff, n=0.25, delta=0.0):
    m = bisect_increasing(lambda x: state(x,w,q_eff,n,delta)["residual_m2"],
                          50.0, 150.0)
    return state(m,w,q_eff,n,delta)


def fit_w_for_mass(q_eff):
    # At these specific conditions, mass decreases with w.
    lo, hi = 0.0, 1.0
    if not forward(lo,q_eff)["m"] > MM_OBS > forward(hi,q_eff)["m"]:
        raise ValueError("target mass not bracketed by w in [0,1]")
    for _ in range(70):
        mid=(lo+hi)/2
        if forward(mid,q_eff)["m"] > MM_OBS:
            lo=mid
        else:
            hi=mid
    w=(lo+hi)/2
    return w,forward(w,q_eff)


def fit_w_for_rise(q_eff):
    lo,hi=0.0,1.0
    if not forward(lo,q_eff)["dt"] < DTM_OBS < forward(hi,q_eff)["dt"]:
        raise ValueError("target rise not bracketed by w in [0,1]")
    for _ in range(70):
        mid=(lo+hi)/2
        if forward(mid,q_eff)["dt"] < DTM_OBS:
            lo=mid
        else:
            hi=mid
    w=(lo+hi)/2
    return w,forward(w,q_eff)


def w_at_3pct(q_eff):
    target=0.03
    lo,hi=0.0,1.0
    if not forward(lo,q_eff)["Dm"] < target < forward(hi,q_eff)["Dm"]:
        raise ValueError("3 percent crossing not bracketed")
    for _ in range(70):
        mid=(lo+hi)/2
        if forward(mid,q_eff)["Dm"] < target:lo=mid
        else:hi=mid
    return (lo+hi)/2


def main():
    writer=csv.writer(sys.stdout,lineterminator="\n")
    writer.writerow(("case","effective_heat_MW","w","mass_kg_s","deltaT_K",
                     "Re_M_over_P","K_M_over_P","Dm_percent_P_over_M",
                     "DdeltaT_percent_P_over_M","mass_residual_m2","note"))
    q_from_pair=MM_OBS*(enthalpy_primitive(TIN+DTM_OBS)-enthalpy_primitive(TIN))
    cases=[]
    cases.append(("design_heat_fit_mass",QM_DESIGN,*fit_w_for_mass(QM_DESIGN),
                  "Matches mass only; temperature remains an unfitted check"))
    cases.append(("design_heat_fit_rise",QM_DESIGN,*fit_w_for_rise(QM_DESIGN),
                  "Matches temperature only; mass remains an unfitted check"))
    cases.append(("paired_fit_heat_and_w",q_from_pair,*fit_w_for_mass(q_from_pair),
                  "Both FoMs used for fit; neither is independent validation"))
    for name,q,w,r,note in cases:
        assert abs(r["residual_m2"])<1e-8
        assert abs(r["m"]*(enthalpy_primitive(TIN+r["dt"])-enthalpy_primitive(TIN))-q)<1e-6
        writer.writerow((name,f"{q/1e6:.9f}",f"{w:.9f}",f"{r['m']:.9f}",
                         f"{r['dt']:.9f}",f"{r['re_ratio']:.9f}",f"{r['k_ratio']:.9f}",
                         f"{100*r['Dm']:.9f}",f"{100*r['DT']:.9f}",
                         f"{r['residual_m2']:.6g}",note))
    for name,q in (("design_heat_3pct_threshold",QM_DESIGN),
                   ("fitted_heat_3pct_threshold",q_from_pair)):
        w=w_at_3pct(q)
        r=forward(w,q)
        writer.writerow((name,f"{q/1e6:.9f}",f"{w:.9f}",f"{r['m']:.9f}",
                         f"{r['dt']:.9f}",f"{r['re_ratio']:.9f}",f"{r['k_ratio']:.9f}",
                         f"{100*r['Dm']:.9f}",f"{100*r['DT']:.9f}",
                         f"{r['residual_m2']:.6g}","Conditional one-sided 3% crossing; not a physical acceptance limit"))
    print(f"Kp={KP:.8f} (CFD-inverted with gross area), inferred heat={q_from_pair/1e6:.8f} MW",file=sys.stderr)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--viscosity',choices=('uploaded','zhao'),default='uploaded')
    args=parser.parse_args()
    mu = mu_uploaded if args.viscosity=='uploaded' else mu_zhao_table4
    RE_P = 4*MP/(math.pi*DP*mu(TP))
    print(f'viscosity={args.viscosity}; mu_P={mu(TP):.9g} Pa s',file=sys.stderr)
    main()
