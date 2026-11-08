#!/usr/bin/env python3
"""Reproduce the arithmetic in physical-domain-v15-review-20261108.md.

The paper-specific applicability ranges and geometric meanings must be
checked in the cited PDF pages; this script does not certify transfer.
"""

from math import exp, pi


def lbe_nea2015(temperature_k):
    density = 11065 - 1.293 * temperature_k
    heat_capacity = (
        164.8
        - 0.0394 * temperature_k
        + 1.25e-5 * temperature_k**2
        - 4.56e5 / temperature_k**2
    )
    viscosity = 4.94e-4 * exp(754.1 / temperature_k)
    conductivity = (
        3.284 + 0.01617 * temperature_k - 2.305e-6 * temperature_k**2
    )
    return density, heat_capacity, viscosity, conductivity


def circular_reynolds(mass_flow_kg_s, inner_diameter_m, viscosity_pa_s):
    return 4 * mass_flow_kg_s / (pi * inner_diameter_m * viscosity_pa_s)


def annular_reynolds(mass_flow_kg_s, outer_id_m, rod_od_m, viscosity_pa_s):
    return 4 * mass_flow_kg_s / (
        pi * (outer_id_m + rod_od_m) * viscosity_pa_s
    )


if __name__ == "__main__":
    pipe_id = 0.026
    hs_id = 0.054
    rod_od = 0.022
    mass_flow = 1.2  # Illustrative KYLIN literature point, not a domain bound.
    area_pipe = pi * pipe_id**2 / 4
    area_hs = pi * (hs_id**2 - rod_od**2) / 4
    print(f"A_pipe={area_pipe:.9f} m2; A_HS={area_hs:.9f} m2")
    print(f"Dh_HS={hs_id - rod_od:.3f} m")
    for t in (423.15, 533.15, 600.0, 673.15, 773.15):
        rho, cp, mu, conductivity = lbe_nea2015(t)
        rp = circular_reynolds(mass_flow, pipe_id, mu)
        ra = annular_reynolds(mass_flow, hs_id, rod_od, mu)
        print(
            f"T={t:.2f} K rho={rho:.4f} cp={cp:.4f} "
            f"mu={mu:.8f} lambda={conductivity:.4f} "
            f"Re_pipe={rp:.0f} Re_HS={ra:.0f}"
        )
    print("cp pointwise ratio extreme:", 1.07 / 0.93)
    print("rho pointwise ratio extreme:", 1.008 / 0.992)
    print("cp-only cubic response:", (1.07 / 0.93) ** (1 / 3) - 1)
