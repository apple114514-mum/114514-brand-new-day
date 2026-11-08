"""Audit a proposed, independently specified LBE loop design.

This is a component/input audit, not a solution of the coupled loop or a
certified bound on a fabricated device. Sources and design status are in the
companion Markdown report. All losses use the 16 mm class pipe velocity head.
"""

import csv
import importlib.util
import math
from itertools import product
from pathlib import Path


HERE = Path(__file__).resolve().parent
COMPONENT = HERE / "fluid-component-prior-domain-20261108.py"
SPEC = importlib.util.spec_from_file_location("components", COMPONENT)
components = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(components)

# Proposed drawing / procurement acceptance values, not published plant data.
D_BORE = (0.01595, 0.01605)     # m; 16.00 +/- 0.05 mm
D_HOLE = (0.00998, 0.01002)    # m; 10.00 +/- 0.02 mm
T_PLATE = (0.00195, 0.00205)   # m; 2.00 +/- 0.05 mm
L_PIPE = (15.96, 16.04)        # m; four 3/5 m legs, each +/- 0.01 m
ROUGH = (0.0, 10e-6)           # m; equivalent sand roughness acceptance
K_AUX = (0.0, 0.5)             # acceptance for all active-path auxiliary ports
M_CHECK = (0.10, 0.20, 0.40)   # kg/s; admissibility check, NOT independent input
T_CHECK = (473.15, 573.15, 773.15)  # K; admissibility check


def elbow_k(re):
    """Al-Tameemi/Ricco, Eq. 4: 90-degree sharp mitre; 500 <= Re <= 60000."""
    return 427.5 * re ** (-0.77) + 0.9


def loop_k(mass, temp, bore, hole, thickness, length, roughness, auxiliary):
    re = components.reynolds(mass, bore, components.lbe_mu(temp))
    if not (1000 < re < 60000):
        raise ValueError("Re outside orifice/elbow overlap")
    pipe = components.churchill_darcy(re, roughness / bore) * length / bore
    elbow = 4 * elbow_k(re)
    orifice = components.orifice_idelchik_3(bore, hole, thickness)
    return re, pipe, elbow, orifice, auxiliary, pipe + elbow + orifice + auxiliary


def main():
    rows = []
    for m, temp in product(M_CHECK, T_CHECK):
        for bore, hole, thickness, length, rough, aux in product(
            D_BORE, D_HOLE, T_PLATE, L_PIPE, ROUGH, K_AUX
        ):
            re, kp, ke, ko, ka, kt = loop_k(
                m, temp, bore, hole, thickness, length, rough, aux
            )
            rows.append({
                "m_check_kg_s": m, "T_check_K": temp,
                "D_bore_m": bore, "d_hole_m": hole, "t_plate_m": thickness,
                "L_pipe_m": length, "roughness_m": rough, "K_aux": aux,
                "Re_main": re, "K_pipe": kp, "K_4_mitre": ke,
                "K_orifice": ko, "K_total": kt,
            })
    out = HERE / "lbe-forward-design-input-grid-20261108.csv"
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    nominal = loop_k(0.20, 573.15, .016, .010, .002, 16, 0, 0)
    # 16 m perimeter, 1 m cooler: all remaining 15 m has outer insulation.
    # Use outward extremes of the proposed geometry and thermal specifications.
    r_pipe_max = 0.0201 / 2
    t_ins_min = .050
    u_prime_max = 2 * math.pi * .050 / math.log(
        (r_pipe_max + t_ins_min) / r_pipe_max
    )
    q_loss_max = (u_prime_max * (16.04 - .99) + .5) * (773.15 - 293.15)
    print("MODEL DESIGN INPUT AUDIT; conditional correlation model, not full-loop FoM")
    print("source pages: NEA 2015 PDF 131/932/934; Al-Tameemi/Ricco PDF 5 Eq.(4)")
    print("nominal m=0.2 kg/s, T=573.15 K: Re, Kpipe, K4elbow, Korifice, Kaux, Ktotal")
    print(" ".join(f"{v:.6f}" for v in nominal))
    print("scenario-grid rows:", len(rows))
    print("Re min/max:", min(r["Re_main"] for r in rows), max(r["Re_main"] for r in rows))
    print("grid K min/max, not certified extrema:",
          min(r["K_total"] for r in rows), max(r["K_total"] for r in rows))
    print("insulation U' upper W/(m K):", u_prime_max)
    print("distributed+bridge ambient heat-loss upper W:", q_loss_max)
    print("3 kW electrical input minus this bound, W:", 3000-q_loss_max)
    print("CSV:", out.name)


if __name__ == "__main__":
    main()
