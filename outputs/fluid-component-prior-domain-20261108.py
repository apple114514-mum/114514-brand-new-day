"""Independent, forward component-loss examples from OECD/NEA 2015.

The geometry and operating window below are illustrative design declarations.
No resistance is inferred from a scaling target or observed FoM.
All K values refer to the dynamic head in the 16 mm main pipe.
"""

import csv
import math
from pathlib import Path


MAIN_D = 0.016  # m, declared candidate main-pipe bore
PIPE_L = 2.0  # m, declared extra straight horizontal pipe
ORIFICE_D = 0.010  # m, declared hole bore
ORIFICE_T = 0.002  # m, declared plate thickness
MASS_FLOW = (0.10, 0.13, 0.25, 0.40)  # kg/s, declared operating examples
TEMPERATURE = (423.15, 573.15, 773.15)  # K; KYLIN published temperature span


def lbe_mu(temp_k):
    # OECD/NEA 2015 Table 2.19.3, 400-1200 K.
    return 4.94e-4 * math.exp(754.1 / temp_k)


def lbe_rho(temp_k):
    # OECD/NEA 2015 Table 2.19.3, 400-1300 K.
    return 11065.0 - 1.293 * temp_k


def reynolds(mass_flow, diameter, mu):
    return 4.0 * mass_flow / (math.pi * diameter * mu)


def churchill_darcy(reynolds_number, relative_roughness=0.0):
    """OECD/NEA 2015 Table 15.3.2, correlation 6: circular pipe, all Re."""
    re = reynolds_number
    inner = (7.0 / re) ** 0.9 + 0.27 * relative_roughness
    a = (2.457 * math.log(1.0 / inner)) ** 16
    b = (37530.0 / re) ** 16
    return 8.0 * ((8.0 / re) ** 12 + (a + b) ** -1.5) ** (1.0 / 12.0)


def orifice_idelchik_3(main_d, hole_d, thickness):
    """NEA Table 15.3.3 correlation 3, Re_D > 1000; main-pipe head."""
    beta = (hole_d / main_d) ** 2
    complement = 1.0 - beta
    ell = thickness / main_d
    inv_power = ell ** -8
    phi = 0.25 + 0.535 * inv_power / (0.05 + inv_power)
    tau = (2.4 - ell) * 10.0 ** (-phi)
    return (
        0.5 * complement
        + complement**2
        + tau * math.sqrt(complement) * complement
    ) / beta**2


def orifice_idelchik_2(main_d, hole_d, thickness):
    """NEA Table 15.3.3 correlation 2, Re_D > 10000; check only."""
    beta = (hole_d / main_d) ** 2
    ell = thickness / main_d
    xi = 0.13 + 0.34 * 10.0 ** (-(3.4 * ell + 88.4 * ell**2.3))
    return (1.0 - beta + math.sqrt(xi) * (1.0 - beta) ** 0.375) ** 2 / beta**2


def annulus_laminar_fre(outer_d, inner_d):
    """Exact fully developed concentric-annulus laminar Darcy f*Re."""
    alpha = inner_d / outer_d
    return 64.0 * (1.0 - alpha) ** 2 / (
        1.0 + alpha**2 - (1.0 - alpha**2) / math.log(1.0 / alpha)
    )


def annulus_re(mass_flow, outer_d, inner_d, mu):
    # Re = 4*m/(wetted perimeter*mu), not 4*m/(pi*Dh*mu).
    return 4.0 * mass_flow / (math.pi * (outer_d + inner_d) * mu)


def main():
    area = math.pi * MAIN_D**2 / 4.0
    k_orifice = orifice_idelchik_3(MAIN_D, ORIFICE_D, ORIFICE_T)
    print("Independent geometry: main 16 mm; orifice 10 mm x 2 mm; straight pipe 2 m")
    print("NEA orifice #3 K:", f"{k_orifice:.9f}")
    print("NEA orifice #2 K (only Re_D>10000):", f"{orifice_idelchik_2(MAIN_D, ORIFICE_D, ORIFICE_T):.9f}")
    print("Orifice hole +/-0.02 mm declared tolerance:",
          f"{orifice_idelchik_3(MAIN_D, ORIFICE_D-0.00002, ORIFICE_T):.9f}",
          f"{orifice_idelchik_3(MAIN_D, ORIFICE_D+0.00002, ORIFICE_T):.9f}")
    print("Circular-pipe Churchill low-Re limit, Re=100:", f"{churchill_darcy(100):.7f}", "vs 64/Re=0.6400000")
    print("Annulus 34/14 mm laminar f*Re:", f"{annulus_laminar_fre(.034,.014):.6f}")
    rows = []
    for temp in TEMPERATURE:
        mu, rho = lbe_mu(temp), lbe_rho(temp)
        for mass in MASS_FLOW:
            re_main = reynolds(mass, MAIN_D, mu)
            re_hole = reynolds(mass, ORIFICE_D, mu)
            f_pipe = churchill_darcy(re_main)
            k_pipe = f_pipe * PIPE_L / MAIN_D
            dp_orifice = k_orifice * mass**2 / (2.0 * rho * area**2)
            re_annulus = annulus_re(mass, .034, .014, mu)
            rows.append({
                "T_K": f"{temp:.2f}", "mass_kg_s": f"{mass:.3f}",
                "Re_main": f"{re_main:.2f}", "Re_hole": f"{re_hole:.2f}",
                "Re_annulus_34_14": f"{re_annulus:.2f}",
                "pipe_branch": "Blasius_available" if re_main > 4000 else "Churchill_transition",
                "orifice_3_valid": str(re_main > 1000),
                "orifice_2_valid": str(re_main > 10000),
                "f_pipe_Churchill_smooth": f"{f_pipe:.8f}",
                "K_pipe_2m": f"{k_pipe:.8f}",
                "K_orifice_10mm_2mm": f"{k_orifice:.8f}",
                "dp_orifice_Pa": f"{dp_orifice:.4f}",
            })
    out = Path(__file__).with_name("fluid-component-prior-domain-points-20261108.csv")
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("Re_main range:", f"{min(float(r['Re_main']) for r in rows):.0f}",
          f"{max(float(r['Re_main']) for r in rows):.0f}")
    print("Re_hole range:", f"{min(float(r['Re_hole']) for r in rows):.0f}",
          f"{max(float(r['Re_hole']) for r in rows):.0f}")
    print("Re_annulus range:", f"{min(float(r['Re_annulus_34_14']) for r in rows):.0f}",
          f"{max(float(r['Re_annulus_34_14']) for r in rows):.0f}")
    print("K_pipe at listed points:", f"{min(float(r['K_pipe_2m']) for r in rows):.6f}",
          f"{max(float(r['K_pipe_2m']) for r in rows):.6f}")
    # Exploratory 1-D scan only; the extrema are not interval-certified.
    re_low = reynolds(MASS_FLOW[0], MAIN_D, lbe_mu(TEMPERATURE[0]))
    re_high = reynolds(MASS_FLOW[-1], MAIN_D, lbe_mu(TEMPERATURE[-1]))
    curve = [(churchill_darcy(re_low + (re_high-re_low)*i/20000)*PIPE_L/MAIN_D,
              re_low + (re_high-re_low)*i/20000) for i in range(20001)]
    print("K_pipe scan candidates (not certified):", min(curve), max(curve))
    print("Rows:", len(rows), "CSV:", out.name)


if __name__ == "__main__":
    main()
