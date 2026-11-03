#!/usr/bin/env python3
"""Independent arithmetic for uploaded component-Re claims and Yue Table 2.

The Yue numbers are an author's theoretical calculation, not measured losses.
The mitre correlation is specific to a sharp 90-degree circular mitre elbow.
"""

import csv
import math
from pathlib import Path


def mitre_k(re):
    assert 500 <= re <= 60000
    return 427.5 * re ** (-0.77) + 0.9


def mitre_m(re):
    a = 427.5 * re ** (-0.77)
    return 0.77 * a / (a + 0.9)  # minus d ln K / d ln Re


re_cross = (427.5 / (0.9 * 0.2 / (0.77 - 0.2))) ** (1 / 0.77)
actual = mitre_k(500) / mitre_k(60000)
claimed_bound = (500 / 60000) ** (-0.2)
print(f"mitre m=0.2 crossing Re={re_cross:.3f}")
print(f"mitre m(500)={mitre_m(500):.6f}, m(20000)={mitre_m(20000):.6f}")
print(f"K(500)/K(60000)={actual:.6f}, claimed universal bound={claimed_bound:.6f}, "
      f"excess factor={actual/claimed_bound:.6f}")
assert abs(re_cross - 11666.2983153) < 1e-5
assert actual > claimed_bound

# Yue et al., NST 28:39 (2017), PDF page 4, Table 2, theoretical results.
rows = [
    (0.25, 5.56, 1.90, 2.9, 2.5, 19.1, 24.5, 261.9),
    (0.50, 11.10, 3.81, 2.8, 2.5, 18.9, 24.2, 1034.8),
    (0.75, 16.70, 5.71, 2.8, 2.5, 18.5, 23.8, 2289.9),
    (1.00, 22.30, 7.62, 2.7, 2.5, 18.1, 23.3, 3985.4),
    (1.25, 27.80, 9.52, 2.6, 2.5, 17.7, 22.8, 6093.6),
]
out = Path(__file__).with_name("yue-2017-table2-resistance-20261103.csv")
with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(["source", "status", "mass_kg_s", "Re_tube_1000", "Re_HS_1000",
                     "K_HS", "K_EV", "K_pipe", "K_total", "dp_Pa", "pipe_friction_K",
                     "pipe_friction_fraction_of_total", "f_implied_11m_26mm", "f_smooth_Blasius"])
    for mass, re_tube, re_hs, khs, kev, kpipe, ktotal, dp in rows:
        assert abs(khs + kev + kpipe - ktotal) < 1e-10
        k_pipe_friction = kpipe - 1  # Yue Eq. (9): K_pipe=f L_pipe/D+1
        frac = k_pipe_friction / ktotal
        f_at_row = k_pipe_friction * 0.026 / 11
        f_smooth = 0.3164 / ((re_tube * 1000) ** 0.25)
        writer.writerow(["Yue2017_PDFp4_Table2", "theoretical", mass, re_tube,
                         re_hs, khs, kev, kpipe, ktotal, dp, round(k_pipe_friction, 4),
                         round(frac, 9), round(f_at_row, 9), round(f_smooth, 9)])
        print(f"Yue m={mass:.2f} kg/s: Ktotal={ktotal:.1f}, "
              f"pipe distributed fraction={frac:.6f}")

low, high = rows[0], rows[-1]
avg_m_total = math.log(low[6] / high[6]) / math.log(high[1] / low[1])
print(f"Yue model Ktotal mean Re exponent across table={avg_m_total:.6f}")
f_implied = (rows[-1][5] - 1) * 0.026 / 11  # Yue Eq. (9), assumed 11 m
f_blasius = 0.3164 / (27800 ** 0.25)
print(f"Yue table at Re_tube=27800 implies Darcy f={f_implied:.6f}; "
      f"smooth Blasius={f_blasius:.6f}; ratio={f_implied/f_blasius:.3f}")

# Yue PDF p2/Table 1 and accompanying text: 26-mm main pipe, 54-mm HS ID,
# one concentric electrical rod of 22-mm OD. Nominal fluid area excludes
# unreported supports, clearances, and blockage.
pipe_area = math.pi * 0.026 ** 2 / 4
hs_annulus_area = math.pi * (0.054 ** 2 - 0.022 ** 2) / 4
hs_hydraulic_diameter = 0.054 - 0.022
print(f"KYLIN nominal main pipe area={pipe_area:.9f} m2, "
      f"HS annulus area={hs_annulus_area:.9f} m2, "
      f"HS/main area ratio={hs_annulus_area/pipe_area:.6f}, "
      f"HS hydraulic diameter={hs_hydraulic_diameter:.3f} m")
print(f"Yue HS reference-velocity multiplier (A_pipe/A_HS)^2="
      f"{(pipe_area/hs_annulus_area)**2:.9f}")

# Zhao target-point values belong to the *declared* scalar model.
k_plus, f_plus = 1.092755604047, 1.305130341205
for label, w in (("E=1 fit", 0.291472160), ("enthalpy-proxy fit", 0.368691380)):
    delta_allow = (k_plus - w * f_plus) / (1 - w) - 1
    print(f"Zhao {label}: fitted w={w:.9f}, delta allowance={100*delta_allow:+.6f}%")

print(f"w=.291472, m=.2 hypothetical Re ratio gate="
      f"{((k_plus-.291472160*f_plus)/(1-.291472160))**(-5):.6f}")

for re_m, re_p in ((500, 60000), (4000, 12000)):
    ratio = mitre_k(re_m) / mitre_k(re_p)
    env = (re_m / re_p) ** (-0.2)
    print(f"mitre Re_M={re_m}, Re_P={re_p}: actual ratio={ratio:.6f}, "
          f"r^-0.2={env:.6f}, exceedance factor={ratio/env:.6f}")
