"""Plot searched v3 FoMs and conditional cooler duty across the power window."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
rows = list(csv.DictReader((ROOT / "power_cooling_scan_v3_20261109.csv").open()))


def col(name):
    return [float(r[name]) for r in rows]


p = col("Q_kW")
plt.rcParams.update({"font.size": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "svg.fonttype": "none"})
fig, (a, b) = plt.subplots(1, 2, figsize=(8.0, 3.0), constrained_layout=True)

a.fill_between(p, col("corner_D_j_min_pct"), col("corner_D_j_max_pct"),
               color="#246b9a", alpha=.18, label="Mass flux: 1024 corners")
a.plot(p, col("nominal_D_j_pct"), color="#246b9a", lw=1.6,
       label="Mass flux: nominal")
a.fill_between(p, col("corner_D_T_min_pct"), col("corner_D_T_max_pct"),
               color="#bc5c39", alpha=.18, label="Heater rise: 1024 corners")
a.plot(p, col("nominal_D_T_pct"), color="#bc5c39", lw=1.6,
       label="Heater rise: nominal")
a.axhline(0, lw=.7, color="0.5")
a.set(xlabel="Electrical power (kW)", ylabel="Conditional FoM deviation (%)",
      title="A  |  Largest searched distortion at low power")
a.legend(frameon=False, fontsize=6.7, loc="center right")

b.fill_between(p, col("corner_UAreq_M_min_W_K"),
               col("corner_UAreq_M_max_W_K"), color="#246b9a", alpha=.18,
               label="Model: 1024 corners")
b.plot(p, col("nominal_UAreq_M_W_K"), color="#246b9a", lw=1.6,
       label="Model: nominal")
b.fill_between(p, col("corner_UAreq_P_min_W_K"),
               col("corner_UAreq_P_max_W_K"), color="#bc5c39", alpha=.18,
               label="Prototype: 1024 corners")
b.plot(p, col("nominal_UAreq_P_W_K"), color="#bc5c39", lw=1.6,
       label="Prototype: nominal")
b.axhline(45, lw=.9, ls="--", color="0.3", label="Illustrative UA = 45 W/K")
b.set(xlabel="Electrical power (kW)", ylabel="Required UA (W/K)",
      title="B  |  Cooling demand peaks at high power")
b.legend(frameon=False, fontsize=6.7, loc="upper left")

fig.text(.5, -.04, "UA assumes 433.15 K isothermal oil; actual oil warming raises the requirement. "
         "Bands show corner searches, not certified continuous bounds.",
         ha="center", fontsize=7)
fig.savefig(ROOT / "power_cooling_v3_20261109.svg", bbox_inches="tight")
fig.savefig(ROOT / "power_cooling_v3_20261109.png", dpi=300, bbox_inches="tight")
