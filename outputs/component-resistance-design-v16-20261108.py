#!/usr/bin/env python3
"""One-point resistance-design illustration from Yue 2017 and Xu FR26.

This is a conditional design calculation. It does not certify physical
component loss coefficients, valve opening, or across-power similarity.
"""

from math import pi, sqrt

YUE_THEORETICAL_ROWS = (
    # m_P kg/s, Re_pipe_P, Re_HS_P, K_HS_P, K_EV_P, K_pipe_P, K_total_P
    (0.25, 5560, 1900, 2.9, 2.5, 19.1, 24.5),
    (0.50, 11100, 3810, 2.8, 2.5, 18.9, 24.2),
    (0.75, 16700, 5710, 2.8, 2.5, 18.5, 23.8),
    (1.00, 22300, 7620, 2.7, 2.5, 18.1, 23.3),
    (1.25, 27800, 9520, 2.6, 2.5, 17.7, 22.8),
)

RE_PIPE_P = 27800.0  # Yue 2017 Table 2, theoretical m=1.25 kg/s row
RE_HS_P = 9520.0
K_PIPE_P = 17.7
K_HS_P = 2.6
K_EV_P = 2.5
K_TOTAL_P = K_PIPE_P + K_HS_P + K_EV_P

LENGTH_RATIO = 0.5  # Xu FR26 Table 2 standard model
DIAMETER_RATIO = 0.616
MASS_FLOW_RATIO = 0.268
PIPE_LENGTH_P = 11.0  # Yue 2017 conservatively assumed, not measured
PIPE_DIAMETER_P = 0.026


def blasius_darcy(reynolds):
    return 0.3164 / reynolds**0.25


def interpolate_yue_implied_pipe_f(reynolds):
    """Linear interpolation of Yue's *theoretical* K_pipe-derived f.

    The 11 m assumed length is held fixed. No extrapolation is allowed.
    """
    pairs = [
        (re, (k_pipe - 1) * PIPE_DIAMETER_P / PIPE_LENGTH_P)
        for _, re, _, _, _, k_pipe, _ in YUE_THEORETICAL_ROWS
    ]
    if not pairs[0][0] <= reynolds <= pairs[-1][0]:
        return None
    for (r0, f0), (r1, f1) in zip(pairs, pairs[1:]):
        if r0 <= reynolds <= r1:
            return f0 + (f1 - f0) * (reynolds - r0) / (r1 - r0)
    return pairs[-1][1]


def separated_step_loss_on_pipe_reference(area_ratio):
    """NEA Ch.15.3.5 idealized contraction + separated expansion.

    area_ratio = A_throat/A_pipe. Assumes an idealized long enough throat
    for the two losses to be treated separately; throat friction is omitted.
    """
    beta = area_ratio
    return (0.5 * (1 - beta) + (1 - beta) ** 2) / beta**2


def area_ratio_for_step_loss(target_k):
    low, high = 1e-6, 1.0
    for _ in range(100):
        mid = (low + high) / 2
        if separated_step_loss_on_pipe_reference(mid) > target_k:
            low = mid
        else:
            high = mid
    return (low + high) / 2


if __name__ == "__main__":
    re_ratio = MASS_FLOW_RATIO / DIAMETER_RATIO
    re_pipe_m = RE_PIPE_P * re_ratio
    re_hs_m = RE_HS_P * re_ratio
    f_pipe_m = blasius_darcy(re_pipe_m)
    k_pipe_m = 1 + f_pipe_m * PIPE_LENGTH_P * LENGTH_RATIO / (
        PIPE_DIAMETER_P * DIAMETER_RATIO
    )
    k_base_m = k_pipe_m + K_HS_P + K_EV_P
    k_valve_ref_needed = K_TOTAL_P - k_base_m
    f_pipe_implied_p = (K_PIPE_P - 1) * PIPE_DIAMETER_P / PIPE_LENGTH_P
    f_pipe_smooth_p = blasius_darcy(RE_PIPE_P)
    a_pipe = pi * PIPE_DIAMETER_P**2 / 4
    a_hs = pi * (0.054**2 - 0.022**2) / 4
    k_hs_friction_if_smooth = (
        blasius_darcy(RE_HS_P)
        * 1.8 / (0.054 - 0.022)
        * (a_pipe / a_hs) ** 2
    )

    for name, value in (
        ("K_total_P_theoretical", K_TOTAL_P),
        ("f_pipe_P_implied_by_Yue_table", f_pipe_implied_p),
        ("f_pipe_P_smooth_Blasius", f_pipe_smooth_p),
        ("Re_pipe_M", re_pipe_m),
        ("Re_HS_M", re_hs_m),
        ("f_pipe_M_smooth_Blasius", f_pipe_m),
        ("K_pipe_M", k_pipe_m),
        ("K_base_M", k_base_m),
        ("K_valve_ref_needed", k_valve_ref_needed),
        ("K_HS_friction_if_smooth_at_prototype_point", k_hs_friction_if_smooth),
        ("K_HS_outlet_residual_if_smooth", 2.6 - 1.29 - 0.64 - k_hs_friction_if_smooth),
    ):
        print(f"{name}={value:.9f}")

    f_yue_model = interpolate_yue_implied_pipe_f(re_pipe_m)
    path_ratio = PIPE_LENGTH_P * LENGTH_RATIO / (
        PIPE_DIAMETER_P * DIAMETER_RATIO
    )
    k_yue_model = 1 + f_yue_model * path_ratio
    k_valve_yue_model = K_TOTAL_P - k_yue_model - K_HS_P - K_EV_P
    model_pipe_id = PIPE_DIAMETER_P * DIAMETER_RATIO
    for name, target in (
        ("smooth_pipe_closure", k_valve_ref_needed),
        ("Yue_interpolated_pipe_closure", k_valve_yue_model),
    ):
        beta = area_ratio_for_step_loss(target)
        throat_id = model_pipe_id * sqrt(beta)
        throat_re = re_pipe_m / sqrt(beta)
        print(
            f"idealized_step_{name}: K={target:.6f}, "
            f"A_throat/A_pipe={beta:.6f}, "
            f"D_throat_mm={throat_id*1000:.3f}, "
            f"Re_throat={throat_re:.0f}"
        )

    print("\nMulti-point model friction closures (conditional):")
    print("mP,Re_pipe_M,Re_HS_M,K_valve_if_smooth,K_valve_if_Yue_interpolated")
    for m_p, re_p, re_hs_p, k_hs_p, k_ev_p, _, k_target in YUE_THEORETICAL_ROWS:
        re_m = re_p * re_ratio
        re_hs_m = re_hs_p * re_ratio
        base_constant = k_hs_p + k_ev_p + 1
        path_ratio = PIPE_LENGTH_P * LENGTH_RATIO / (
            PIPE_DIAMETER_P * DIAMETER_RATIO
        )
        # Blasius at low Re is deliberately not used below the nominal
        # turbulent gate Re=4000. This gate is a design screen, not a paper fit.
        smooth_needed = (
            k_target - base_constant - blasius_darcy(re_m) * path_ratio
            if re_m >= 4000
            else None
        )
        f_yue = interpolate_yue_implied_pipe_f(re_m)
        yue_needed = (
            k_target - base_constant - f_yue * path_ratio
            if f_yue is not None
            else None
        )
        fmt = lambda x: "OUT_OF_DOMAIN" if x is None else f"{x:.6f}"
        print(f"{m_p:.2f},{re_m:.0f},{re_hs_m:.0f},{fmt(smooth_needed)},{fmt(yue_needed)}")
