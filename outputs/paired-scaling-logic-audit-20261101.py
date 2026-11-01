#!/usr/bin/env python3
"""Independent algebra audit of the uploaded paired-scaling claims.

Zhao et al. 2020 Tables 3-5 supply paired *CFD*, not measurements. Gross
diameters are used in the effective-K illustration only as a declared
scenario; they are not established net flow areas or hydraulic diameters.
The n/w/delta box below is an algebraic surrogate with a frozen Reynolds
ratio derived from the CFD outputs, not a prospective physical bound.

Run: python outputs/paired-scaling-logic-audit-20261101.py > results.csv
"""

import csv
import math
import sys


MP, MM = 540.0, 92.79
DTP, DTM = 130.0, 136.70
T_IN = 533.15
T_OUT_P, T_OUT_M = 663.16, 669.85
QP_DESIGN, QM_DESIGN = 10e6, 1.77e6
IDEAL_M, IDEAL_T = 2.0**2.5, 1.0
G, BETA_NUM = 9.81, 1.1944


def rho(t):
    return 11096.0 - BETA_NUM * t


def cp_primitive(t):
    return 159*t - 0.0272*t*t/2 + 7.12e-6*t**3/3


def enthalpy_power(m, t_out):
    return m * (cp_primitive(t_out) - cp_primitive(T_IN))


def emit(writer, label, value, status, note):
    writer.writerow((label, f"{value:.12g}", status, note))


def main():
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("quantity", "value", "evidence_status", "interpretation"))

    dm = (MP/MM)/IDEAL_M - 1
    dt = (DTP/DTM)/IDEAL_T - 1
    prod = (1+dm)*(1+dt)
    emit(writer, "observed_Dm_percent", 100*dm, "Zhao Table 5 CFD", "P/M normalized by Table 1 ideal ratio")
    emit(writer, "observed_DdeltaT_percent", 100*dt, "Zhao Table 5 CFD", "Cannot be replaced by a counterfactual")
    emit(writer, "mass_times_deltaT_factor", prod, "algebra on CFD outputs", "(1+Dm)(1+DdeltaT)")

    qhp = enthalpy_power(MP, T_OUT_P)
    qhm = enthalpy_power(MM, T_OUT_M)
    cpbarp = qhp/(MP*(T_OUT_P-T_IN))
    cpbarm = qhm/(MM*(T_OUT_M-T_IN))
    enthalpy_factor = (qhp/qhm)/(IDEAL_M*IDEAL_T)
    # The source table rounds prototype deltaT to 130.0 K, while its
    # printed inlet/outlet difference is 130.01 K.
    round_factor = DTP/(T_OUT_P-T_IN)
    assert math.isclose(prod, enthalpy_factor*(cpbarm/cpbarp)*round_factor, rel_tol=1e-12)
    emit(writer, "prototype_enthalpy_MW", qhp/1e6, "single-stream proxy", "Integral of Zhao Table 4 cp over printed temperatures")
    emit(writer, "facility_enthalpy_MW", qhm/1e6, "single-stream proxy", "Integral of Zhao Table 4 cp over printed temperatures")
    emit(writer, "enthalpy_ratio_factor", enthalpy_factor, "single-stream proxy", "Qh,P/Qh,M divided by ideal mass and temperature ratio")
    emit(writer, "cpbar_M_over_P", cpbarm/cpbarp, "single-stream proxy", "Required factor in the energy identity")
    emit(writer, "printed_deltaT_rounding_factor", round_factor, "Zhao Table 5", "130.0 K versus 663.16-533.15=130.01 K")
    emit(writer, "counterfactual_DdeltaT_percent", 100*(1/(1+dm)-1), "counterfactual only", "Requires mass-times-temperature factor exactly one")

    # Effective K is defined from the observed point and assumed *gross*
    # circular areas. Reusing it in the defining equation is tautological.
    tbp, tbm = T_IN+DTP/2, T_IN+DTM/2
    rp, rm = rho(tbp), rho(tbm)
    ap, am = math.pi/4, math.pi/16
    kp = 2*rp*ap**2*G*BETA_NUM*DTP*2/MP**2
    km = 2*rm*am**2*G*BETA_NUM*DTM*1/MM**2
    kr = km/kp
    density_ratio = rp/rm
    assert math.isclose((1+dm)**2, density_ratio*(1+dt)*kr, rel_tol=1e-12)
    assert math.isclose((1+dm)**3, density_ratio*kr*prod, rel_tol=1e-12)
    emit(writer, "effective_K_M_over_P", kr, "CFD-inverted scenario", "Uses assumed gross area; not an independently known loss ratio")
    emit(writer, "observed_cube_factor", (1+dm)**3, "algebra on CFD outputs", "Equals density ratio times effective K ratio times energy factor")
    emit(writer, "K_only_cube_prediction_Dm_percent", 100*(kr**(1/3)-1), "counterfactual only", "Drops density and energy factors; disagrees with observed Dm")

    # The Reynolds ratio 0.3461 and n/w/delta box are the uploaded script's
    # retrospective assumptions; they do not define a prospective input box.
    re_r = 0.3461
    n = 0.25
    f = re_r**(-n)
    delta = 0.05
    w0 = (kr-1)/(f-1)
    wdelta_correct = (kr-1-delta)/(f-1-delta)
    wdelta_uploaded = (kr-1-delta)/(f-1+delta)
    assert math.isclose(1+wdelta_correct*(f-1)+(1-wdelta_correct)*delta, kr, rel_tol=1e-12)
    assert not math.isclose(1+wdelta_uploaded*(f-1)+(1-wdelta_uploaded)*delta, kr, rel_tol=1e-3)
    emit(writer, "w_fit_delta_0", w0, "retrospective fit", "Assumes n=0.25 and delta=0")
    emit(writer, "w_fit_delta_0p05_correct", wdelta_correct, "retrospective fit", "Correct denominator f_R-1-delta")
    emit(writer, "w_fit_delta_0p05_uploaded", wdelta_uploaded, "uploaded-code error", "Incorrect denominator f_R-1+delta")

    # This corner result is exact for the *frozen-Re algebraic surrogate*.
    def surrogate_k(n_, w_, delta_):
        return 1+w_*(re_r**(-n_)-1)+(1-w_)*delta_

    klo = surrogate_k(0.18, 0.20, -0.05)
    khi = surrogate_k(0.30, 0.60, +0.05)
    emit(writer, "frozen_Re_surrogate_K_min", klo, "conditional surrogate", "n/w/delta low corner")
    emit(writer, "frozen_Re_surrogate_K_max", khi, "conditional surrogate", "n/w/delta high corner")
    emit(writer, "frozen_Re_surrogate_Dm_max_percent", 100*(khi**(1/3)-1), "conditional surrogate", "Not a prior bound for Zhao facility")
    target_k = 1.03**3
    w_limit_delta0 = (target_k-1)/(f-1)
    fmax = re_r**(-0.30)
    w_limit_robust = (target_k-1-0.05)/(fmax-1-0.05)
    emit(writer, "3pct_w_limit_n0p25_delta0", w_limit_delta0, "conditional surrogate", "Only for fixed n and delta")
    emit(writer, "3pct_w_limit_all_n_delta", w_limit_robust, "conditional surrogate", "All n in [0.18,0.30], delta in [-0.05,0.05]")
    emit(writer, "10pct_max_Dm_n0p25_delta0_percent", 100*(f**(1/3)-1), "conditional surrogate", "If w<=1, 10 percent target is automatically met")


if __name__ == "__main__":
    main()
