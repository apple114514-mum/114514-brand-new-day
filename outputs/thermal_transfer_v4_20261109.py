"""Audit the exact heater energy transfer between the two v3 FoMs.

This evaluates sampled corners.  It does not certify the full ten-axis box.
The second result is an algebraic conditional enclosure for the heater factor
under the independently stated condition 471.15 <= T_HS(s) <= 800 K.
Printed floating-point endpoints are illustrative, not a roundoff certificate.
"""

import csv
import itertools
import math
from pathlib import Path

import core_v2 as C

ROOT = Path(__file__).resolve().parent
POWERS = (3000., 4300., 6000.)
CORNERS = itertools.product((0, 1), repeat=len(C.NAMES))


def heater_factor(r, x):
    """The exact factor for core_v2's constant-cp-on-each-segment march."""
    fcp = x[C.IDX["cp_fac"]]
    t_p = C.T_IN_REF + x[C.IDX["dTin_P"]]
    t_m = C.T_IN_REF + x[C.IDX["dTin_M"]]
    cp_p = C.cp_of(t_p, fcp)
    cp_m = C.cp_of(t_m, fcp)
    net_p = r["rp"]["m"] * cp_p * r["rp"]["d_t_hs"]
    net_m = r["rm"]["m"] * cp_m * r["rm"]["d_t_hs"]
    return net_m / net_p * cp_p / cp_m, net_m / net_p, cp_p / cp_m


def analytic_factor_enclosure(power):
    """Conditional algebraic bound assuming every heated bulk T is in [471.15,800].

    Heater temperature rises monotonically in the declared domain because
    Q_e/L exceeds the maximum U*(800-Tamb) by a large factor.  Thus its
    mean T lies between the inlet lower bound and 800 K.  Qnet=Qe-Qloss.
    These are positive interval operations; property factor cp_fac cancels.
    """
    u_p = C.P["segs"][0]["u"]
    u_m = C.M["segs"][0]["u"]
    l_p = C.P["segs"][0]["L"]
    l_m_lo, l_m_hi = C.BOUNDS[C.IDX["L_HS_M"]]
    u_fac_lo, u_fac_hi = C.BOUNDS[C.IDX["u_loss_fac"]]
    t_lo = C.T_IN_REF + C.BOUNDS[C.IDX["dTin_P"]][0]
    t_hi = 800.0
    cp_prime = lambda T: -3.94e-2 + 2*1.25e-5*T + 2*4.56e5/T**3
    assert cp_prime(C.T_IN_REF-2.) < 0 and cp_prime(C.T_IN_REF+2.) < 0
    assert power/l_p > u_p*u_fac_hi*(t_hi-C.T_AMB)
    assert power/l_m_hi > u_m*u_fac_hi*(t_hi-C.T_AMB)
    qloss_p_lo = u_p*u_fac_lo*l_p*(t_lo-C.T_AMB)
    qloss_p_hi = u_p*u_fac_hi*l_p*(t_hi-C.T_AMB)
    qloss_m_lo = u_m*u_fac_lo*l_m_lo*(t_lo-C.T_AMB)
    qloss_m_hi = u_m*u_fac_hi*l_m_hi*(t_hi-C.T_AMB)
    heat_lo = (power-qloss_m_hi)/(power-qloss_p_lo)
    heat_hi = (power-qloss_m_lo)/(power-qloss_p_hi)
    cp_lo = C.cp_of(C.T_IN_REF+2.)/C.cp_of(C.T_IN_REF-2.)
    cp_hi = 1./cp_lo
    return heat_lo*cp_lo, heat_hi*cp_hi, (qloss_p_lo, qloss_p_hi), (qloss_m_lo, qloss_m_hi)


def main():
    rows=[]
    for power in POWERS:
        vals=[]
        for bits in itertools.product((0,1), repeat=len(C.NAMES)):
            x=[C.BOUNDS[i][bit] for i,bit in enumerate(bits)]
            r=C.fom(x,power)
            if r is None:
                raise RuntimeError((power,bits))
            R,qratio,cpratio=heater_factor(r,x)
            dj=r["d_j"]/100.;dt=r["d_t"]/100.
            vals.append((dj,dt,R,qratio,cpratio,(1+dj)*(1+dt)-R,
                         r["rp"]["t_hs"],r["rm"]["t_hs"]))
        djs=[v[0] for v in vals]; dts=[v[1] for v in vals]
        rs=[v[2] for v in vals]; qs=[v[3] for v in vals]; cps=[v[4] for v in vals]
        r_lo,r_hi,p_loss,m_loss=analytic_factor_enclosure(power)
        row={"power_kW":power/1000,"corners":len(vals),
             "Dj_min_pct":100*min(djs),"Dj_max_pct":100*max(djs),
             "DT_min_pct":100*min(dts),"DT_max_pct":100*max(dts),
             "R_corner_min":min(rs),"R_corner_max":max(rs),
             "Qnet_ratio_corner_min":min(qs),"Qnet_ratio_corner_max":max(qs),
             "cp_ratio_corner_min":min(cps),"cp_ratio_corner_max":max(cps),
             "P_heater_out_corner_min_K":min(v[6] for v in vals),
             "P_heater_out_corner_max_K":max(v[6] for v in vals),
             "M_heater_out_corner_min_K":min(v[7] for v in vals),
             "M_heater_out_corner_max_K":max(v[7] for v in vals),
             "identity_max_abs_residual":max(abs(v[5]) for v in vals),
             "transfer_corner_lo_pct":100*(min(rs)/(1+max(djs))-1),
             "transfer_corner_hi_pct":100*(max(rs)/(1+min(djs))-1),
             "R_conditional_analytic_lo":r_lo,"R_conditional_analytic_hi":r_hi,
             "P_heater_loss_analytic_W_lo":p_loss[0],
             "P_heater_loss_analytic_W_hi":p_loss[1],
             "M_heater_loss_analytic_W_lo":m_loss[0],
             "M_heater_loss_analytic_W_hi":m_loss[1]}
        rows.append(row)
        print(f'{power/1000:g} kW: R corners [{min(rs):.8f},{max(rs):.8f}], '
              f'conditional analytic R [{r_lo:.6f},{r_hi:.6f}], '
              f'DT corners [{100*min(dts):+.4f},{100*max(dts):+.4f}]%, '
              f'transferred corner range '
              f'[{row["transfer_corner_lo_pct"]:+.4f},'
              f'{row["transfer_corner_hi_pct"]:+.4f}]%, '
              f'identity residual {row["identity_max_abs_residual"]:.2e}')
    with (ROOT/'thermal_transfer_v4_20261109.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)


if __name__=='__main__':
    main()
