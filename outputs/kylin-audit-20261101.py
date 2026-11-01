#!/usr/bin/env python3
"""Reproduce and challenge the uploaded KYLIN-II four-section model.

This is a conditional model audit, not a validated KYLIN-II prediction.
Values for geometry, thermophysical properties, heat transfer, and the
24 kW / 1.2 kg/s calibration target come from the user's uploaded HTML/code;
the cited original KYLIN-II papers were not supplied for primary checking.

Run: python outputs/kylin-audit-20261101.py > outputs/kylin-audit-20261101.csv
Uses only Python's standard library. CSV rows are scenarios, not measurements.
"""

import csv
import math
import sys


G, BETA_NUM, T_AMB = 9.80665, 1.3235, 298.15
DIAMETER, HEIGHT, CENTER_SEPARATION = 0.026, 5.0, 3.35
Q_P, TS, UA_P, US_P, M_CAL = 24000.0, 553.15, 915.0, 6.0, 1.2
SECTIONS = (
    ("core", 1.8, 1.5, "b"),
    ("hot", 3.2, 1.0, "h"),
    ("hx", 1.5, 2.5, "b"),
    ("cold", 5.5, 1.0, "c"),
)
C, N = 0.5, 0.25
D_R = C ** 0.7
M_R = C ** 1.9


def rho(t):
    return 11096.0 - BETA_NUM * t


def cp(t):
    return 164.8 - 0.0394 * t + 1.25e-5 * t * t - 4.56e5 / (t * t)


def mu(t):
    return 4.94e-4 * math.exp(754.1 / t)


def thermo(m, p):
    tb = (p["UA"] * TS + p["Q"] + p["US"] * T_AMB) / (p["UA"] + p["US"])
    qnet = p["Q"] - p["US"] * (tb - T_AMB)
    dt = qnet / (m * cp(tb))
    return tb, tb + dt / 2, tb - dt / 2, dt


def terms(m, p, effective_height):
    tb, th, tc, dt = thermo(m, p)
    temps = {"b": tb, "h": th, "c": tc}
    diameter = DIAMETER * p["dR"]
    area = math.pi * diameter**2 / 4
    local = friction = 0.0
    for _, length, k, tag in SECTIONS:
        t = temps[tag]
        reynolds = m * diameter / (area * mu(t))
        f = 0.3164 * reynolds ** (-N)
        weight = m * m / (2 * rho(t) * area * area)
        local += weight * k * p["kmult"]
        friction += weight * f * length * p["lR"] / diameter
    buoyancy = G * BETA_NUM * dt * effective_height * p["lR"]
    return buoyancy, local, friction, dt, tb, th, tc


def residual(m, p, effective_height):
    buoyancy, local, friction, *_ = terms(m, p, effective_height)
    return buoyancy - local - friction


def root(p, effective_height):
    low, high = 0.05, 5.0
    if residual(low, p, effective_height) <= 0 or residual(high, p, effective_height) >= 0:
        raise ValueError("root is not bracketed")
    for _ in range(90):
        mid = (low + high) / 2
        if residual(mid, p, effective_height) > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def prototype(effective_height):
    p = dict(Q=Q_P, UA=UA_P, US=US_P, dR=1.0, lR=1.0, kmult=0.0)
    buoyancy, _, friction, *_ = terms(M_CAL, p, effective_height)
    p["kmult"] = (buoyancy - friction) / terms(M_CAL, dict(p, kmult=1.0), effective_height)[1]
    if p["kmult"] < 0:
        raise ValueError("assumed heat/height model requires negative local loss")
    assert abs(root(p, effective_height) - M_CAL) < 1e-11
    return p


def standard(p, us_ratio=C * D_R):
    return dict(p, Q=Q_P * M_R, UA=UA_P * M_R,
                US=US_P * us_ratio, dR=D_R, lR=C)


def point(label, p, effective_height, expected_m, expected_dt, note):
    m = root(p, effective_height)
    buoy, local, friction, dt, tb, th, tc = terms(m, p, effective_height)
    return [label, effective_height, p["dR"], p["lR"], p["US"],
            6 * p["kmult"], m, dt, 100 * (m / expected_m - 1),
            100 * (dt / expected_dt - 1), local / (local + friction),
            buoy, tb, th, tc, note]


def main():
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("scenario", "effective_height_m", "diameter_ratio", "length_ratio",
                     "US_W_per_K", "fitted_k_sum", "mass_kg_per_s", "deltaT_K",
                     "mass_deviation_percent", "deltaT_deviation_percent",
                     "local_loss_share", "buoyancy_Pa", "Tb_K", "Th_K", "Tc_K", "note"))
    for h in (HEIGHT, CENTER_SEPARATION):
        p = prototype(h)
        _, _, _, dtp, *_ = terms(M_CAL, p, h)
        writer.writerow(point("prototype_calibration", p, h, M_CAL, dtp,
                              "24 kW/1.2 kg/s is a calibration target, not a validation point"))
        for label, usratio in (("standard_uploaded_US", C * D_R),
                               ("standard_US_matched_to_Q_UA", M_R)):
            writer.writerow(point(label, standard(p, usratio), h, M_CAL * M_R, dtp,
                                  "Second US scaling is an algebraic diagnostic"))
        height_case = dict(p, lR=C, US=US_P * C)
        writer.writerow(point("height_only_scenario", height_case, h, M_CAL, dtp,
                              "Not a replication of Cheng et al. apparatus"))
        if h == HEIGHT:
            base = standard(p)
            bm = root(base, h)
            bdt = terms(bm, base, h)[3]
            for tolerance in (0.01, 0.03):
                for side in (-1, 1):
                    bore = dict(base, dR=D_R * (1 + side * tolerance))
                    writer.writerow(point(f"bore_{side*tolerance:+.0%}", bore, h, bm, bdt,
                                          "Corner value; exact extremum only under proved one-parameter monotonicity"))
    for k_sum in (3.0, 6.0, 12.0, 22.7184408636, 36.0, 60.0):
        p = dict(Q=Q_P, UA=UA_P, US=US_P, dR=1.0, lR=1.0, kmult=k_sum/6)
        mp = root(p, HEIGHT)
        dtp = terms(mp, p, HEIGHT)[3]
        height_case = dict(p, lR=C, US=US_P*C)
        writer.writerow(point("height_loss_sensitivity", height_case, HEIGHT, mp, dtp,
                              "Same assumed Q, UA, US scaling; k is varied, not refitted"))
    # Sanity checks against the uploaded program, which uses H=5 m.
    original = prototype(HEIGHT)
    assert abs(6 * original["kmult"] - 22.71844086) < 1e-6
    assert abs(root(standard(original), HEIGHT) - 0.32030354) < 1e-7
    # For fixed Q, UA and US, T(m) does not depend on D. Each positive local
    # loss term is proportional to D^-4 and each Blasius term to D^(N-5).
    # On the bracket below, the bounds on d(log loss)/d(log m) are positive.
    # Thus g_m<0 and g_D>0; each bore has one root and it grows with D.
    base = standard(original)
    dmin, dmax = D_R * 0.97, D_R * 1.03
    low_mass, high_mass = 0.25, 0.4
    g_low = residual(low_mass, dict(base, dR=dmin), HEIGHT)
    g_high = residual(high_mass, dict(base, dR=dmax), HEIGHT)
    _, _, tcl, _ = thermo(low_mass, base)
    _, thh, _, _ = thermo(low_mass, base)
    assert 450 < tcl < thh < 700 and g_low > 0 > g_high
    rho_min = rho(700)
    local_slope_lower = 2 - BETA_NUM * 150 / rho_min
    friction_slope_lower = 2 - N - 150 * (N * 754.1 / 450**2 + BETA_NUM / rho_min)
    assert local_slope_lower > 0 and friction_slope_lower > 0
    print(f"One-parameter bore bracket: g(0.25,Dmin)={g_low:.1f} Pa, "
          f"g(0.40,Dmax)={g_high:.1f} Pa; "
          f"lower logarithmic loss slopes {local_slope_lower:.3f}, "
          f"{friction_slope_lower:.3f}.", file=sys.stderr)
    print("Reproduced original H=5 m branch; H=3.35 m is an alternative interpretation, not a validated correction.", file=sys.stderr)


if __name__ == "__main__":
    main()
