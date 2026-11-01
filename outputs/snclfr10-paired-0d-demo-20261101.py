#!/usr/bin/env python3
"""A conditional paired-loop diagnostic for Zhao et al. (2020), Tables 3--5.

Prototype CFD mass flow is the *only fitted output*. The facility CFD flow
and temperatures are held out. Gross geometric area scaling A_P/A_M=4,
an effective friction exponent n=0.25 and friction share w are scenarios,
not measured channel geometry or validated wire-wrap correlations.

Run: python outputs/snclfr10-paired-0d-demo-20261101.py > scenarios.csv
"""

import csv
import math
import sys


G = 9.81
TIN = 533.15
Q_P, Q_M = 10e6, 1.77e6  # Table 3 design powers, W
H_P, H_M = 2.0, 1.0  # Table 3 circulation heights, m
M_P_CFD, M_M_CFD = 540.0, 92.79  # Table 5 CFD outputs, kg/s
DT_P_CFD, DT_M_CFD = 130.0, 136.70  # Table 5 CFD outputs, K
DIAMETER_RATIO = 2.0  # Table 3 gross geometric ratio, conditional use below


def rho(t):
    return 11096.0 - 1.1944 * t  # Zhao Table 4


def mu(t):
    return 4.56e-3 - 7.03e-6 * t + 3.61e-9 * t * t  # Zhao Table 4


def cp(t):
    return 159.0 - 0.0272 * t + 7.12e-6 * t * t  # Zhao Table 4


def enthalpy_rise(t):
    return (
        159.0 * (t - TIN)
        - 0.0272 * (t * t - TIN * TIN) / 2.0
        + 7.12e-6 * (t**3 - TIN**3) / 3.0
    )


def bisect_increasing(fun, low, high):
    if not fun(low) < 0 < fun(high):
        raise ValueError(f"root not bracketed on [{low}, {high}]")
    for _ in range(80):
        mid = (low + high) / 2.0
        if fun(mid) < 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def outlet_temperature(q, mass_flow):
    if mass_flow <= 0:
        raise ValueError("positive mass flow required")
    t = bisect_increasing(lambda x: mass_flow * enthalpy_rise(x) - q, TIN, TIN + 250)
    if min(cp(TIN), cp(t), rho(TIN), rho(t), mu(TIN), mu(t)) <= 0:
        raise ValueError("invalid thermophysical state")
    return t


T_P_MODEL = outlet_temperature(Q_P, M_P_CFD)
T_BAR_P = (TIN + T_P_MODEL) / 2.0
BUOY_P = G * H_P * (rho(TIN) - rho(T_P_MODEL))
# Only K_P/A_P^2 is identifiable from the prototype flow point.
KAPPA_P = 2.0 * rho(T_BAR_P) * BUOY_P / M_P_CFD**2


def predict_facility(area_ratio, friction_share, exponent=0.25):
    """Predict held-out facility m and rise under declared scaling scenarios.

    A_P/A_M=area_ratio is a scenario; Table 3 gross diameter alone does not
    determine true net flow area. The same effective loss structure is
    assumed on both sides, with a Re-dependent friction fraction.
    """
    if area_ratio <= 0 or not 0 <= friction_share <= 1 or not 0 <= exponent < 2:
        raise ValueError("invalid scenario")

    def residual(m):
        t = outlet_temperature(Q_M, m)
        tbar = (TIN + t) / 2.0
        re_ratio = (
            (m / M_P_CFD)
            * (area_ratio / DIAMETER_RATIO)
            * (mu(T_BAR_P) / mu(tbar))
        )
        k_ratio = (1.0 - friction_share) + friction_share * re_ratio ** (-exponent)
        loss = KAPPA_P * area_ratio**2 * k_ratio * m**2 / (2.0 * rho(tbar))
        buoy = G * H_M * (rho(TIN) - rho(t))
        return loss - buoy

    m = bisect_increasing(residual, 70.0, 130.0)
    t = outlet_temperature(Q_M, m)
    return m, t - TIN


def fit_decreasing(fun, low, high):
    if not fun(low) > 0 > fun(high):
        raise ValueError("decreasing root not bracketed")
    for _ in range(70):
        mid = (low + high) / 2.0
        if fun(mid) > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def rows():
    for w in (0.0, 0.25, 0.5, 1.0):
        yield f"area4_w{w:g}", 4.0, w
    w_fit = fit_decreasing(lambda w: predict_facility(4.0, w)[0] - M_M_CFD, 0.0, 1.0)
    yield "mass_fit_at_area4", 4.0, w_fit
    for w in (0.0, 1.0):
        area_fit = fit_decreasing(
            lambda area: predict_facility(area, w)[0] - M_M_CFD, 3.0, 5.0
        )
        yield f"mass_fit_at_w{w:g}", area_fit, w


def main():
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(
        ["scenario", "assumed_A_P_over_A_M", "assumed_friction_share_w", "effective_exponent_n",
         "facility_m_pred_kg_s", "facility_deltaT_pred_K", "facility_m_CFD_kg_s",
         "facility_deltaT_CFD_K", "m_pred_minus_CFD_percent", "deltaT_pred_minus_CFD_percent"]
    )
    for name, area, w in rows():
        m, dt = predict_facility(area, w)
        writer.writerow(
            [name, f"{area:.6f}", f"{w:.6f}", "0.25", f"{m:.6f}", f"{dt:.6f}",
             M_M_CFD, DT_M_CFD, f"{100*(m/M_M_CFD-1):.6f}",
             f"{100*(dt/DT_M_CFD-1):.6f}"]
        )
    print(
        f"Prototype-only calibration: K_P/A_P^2={KAPPA_P:.6f}; "
        f"prototype energy-model deltaT={T_P_MODEL-TIN:.6f} K vs CFD {DT_P_CFD:.2f} K. "
        "The pressure model is a total-loop equivalent; Table 5 core drop is not its validation target.",
        file=sys.stderr,
    )
    assert math.isclose(predict_facility(4.0, 0.25)[0], 93.1984, abs_tol=0.001)


if __name__ == "__main__":
    main()
