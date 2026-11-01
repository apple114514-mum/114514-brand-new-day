#!/usr/bin/env python3
"""Audit a finite-k sign crossing and the consistency of ideal scaling ratios.

Uses the already committed four-section conditional model, not a new data
source. It does not prove global monotonicity or validate the model against
an independent operating point. Run from the repository root:

  python outputs/kylin-denominator-crossing-20261101.py > outputs/kylin-denominator-crossing-20261101.csv
"""

import csv
import math
from pathlib import Path
import runpy
import sys


model = runpy.run_path(str(Path(__file__).with_name("loop-audit-repair-corrected-20261101.py")))
solve = model["solve"]
calibrate = model["calibrate"]
point = model["point"]
cal, _, _, _, k_cal = calibrate(3.35)
k_base = sum(section["k"] for section in model["SEC"].values())


def pair(k_tot, q_ratio=1.0, ua_ratio=1.0, us_ratio=0.5):
    p = dict(cal, kmult=k_tot / k_base)
    m_p, d_p = solve(p)
    m_params = dict(p, lR=0.5, Q=p["Q"]*q_ratio,
                    UA=p["UA"]*ua_ratio, US=p["US"]*us_ratio)
    m_m, d_m = solve(m_params)
    return m_p, m_m, d_p, d_m


def error(k_tot):
    m_p, m_m, _, _ = pair(k_tot)
    return m_m/m_p - 1


def find_crossing():
    low, high = 0.0, 1.0
    assert error(low)>0>error(high)
    for _ in range(70):
        mid = (low+high)/2
        if error(mid)>0:
            low=mid
        else:
            high=mid
    return (low+high)/2


def main():
    writer=csv.writer(sys.stdout,lineterminator="\n")
    writer.writerow(("case","k_total","Q_M_over_Q_P","UA_M_over_UA_P",
                     "US_M_over_US_P","ideal_mass_ratio","ideal_deltaT_ratio",
                     "mass_P_kg_s","mass_M_kg_s","observed_mass_ratio",
                     "mass_error_percent","deltaT_ratio","cold_M_K",
                     "note"))
    cross=find_crossing()
    for k in (0.0,0.1,0.3,0.4,cross,0.5,1.0,3.0,k_cal,36.0,40.0):
        mp,mm,dp,dm=pair(k)
        writer.writerow(("paired_k",f"{k:.9f}","1","1","0.5","1","1",
                         f"{mp:.9f}",f"{mm:.9f}",f"{mm/mp:.9f}",
                         f"{100*(mm/mp-1):.9f}",f"{dm['dT']/dp['dT']:.9f}",
                         f"{dm['Tc']:.6f}","A sign crossing exists between 0 and 1" if k==cross else "conditional model point"))
    k=k_cal
    targets=(("same_power_reference",1,1,0.5,1,1),
             ("borrowed_sqrt_mass_reference",1,1,0.5,math.sqrt(.5),1),
             ("power_consistent_sqrt_reference",math.sqrt(.5),math.sqrt(.5),math.sqrt(.5),math.sqrt(.5),1))
    for label,qr,uar,usr,mideal,dtideal in targets:
        mp,mm,dp,dm=pair(k,qr,uar,usr)
        writer.writerow((label,f"{k:.9f}",f"{qr:.9f}",f"{uar:.9f}",f"{usr:.9f}",
                         f"{mideal:.9f}",f"{dtideal:.9f}",f"{mp:.9f}",f"{mm:.9f}",
                         f"{mm/mp:.9f}",f"{100*(mm/(mp*mideal)-1):.9f}",
                         f"{dm['dT']/dp['dT']:.9f}",f"{dm['Tc']:.6f}",
                         "Reference only: Q target incompatible with m*DeltaT target" if label.startswith('borrowed') else "conditional model point"))
    nominal=point(1.2,cal)[1]
    low_flow=point(0.36,cal)[1]
    assert abs(nominal["fric_share"]-.486726)<1e-5
    assert low_flow["Tc"]<398.15
    print(f"crossing k={cross:.9f}; nominal w={nominal['fric_share']:.7f}; "
          f"low-flow cold temperature={low_flow['Tc']:.3f} K",file=sys.stderr)


if __name__=="__main__":
    main()
