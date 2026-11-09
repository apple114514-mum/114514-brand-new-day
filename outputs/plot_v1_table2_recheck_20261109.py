"""Plot the preregistered v1 design and the source-corrected recheck."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "analysis_v1_table2_recheck.json").read_text())

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "svg.fonttype": "none",
    "savefig.bbox": "tight",
})

fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(7.25, 3.25), layout="constrained")

points = data["nominal"]
q = np.array([p["Q_W"] / 1000 for p in points])
y = np.array([p["D_massflux_pct"] for p in points])
y_old = np.array([data["frozen22_8_D_pt_pct"][str(int(p["Q_W"]))] for p in points])

ax0.plot(q, y, "o-", color="#176b87", ms=3.6, lw=1.5, label="Yue Table 2: $K(Re)$")
ax0.plot(q, y_old, "s--", color="#b55730", ms=3.3, lw=1.15, label="Frozen $K=22.8$ (v1)")
ax0.axvline(4.3, color="0.45", ls=":", lw=0.8)
ax0.text(4.34, -10.45, "lowest Yue measured power", fontsize=6.8, color="0.35", rotation=90, va="bottom")
ax0.set(xlabel="Common electric power (kW)", ylabel="Mass-flux deviation $D_j$ (%)", xlim=(2.9, 6.1), ylim=(-11.15, -6.45))
ax0.legend(loc="lower right", fontsize=7, frameon=False)
ax0.grid(alpha=0.16, lw=0.6)
ax0.text(0.02, 0.98, "(a)", transform=ax0.transAxes, va="top", fontweight="bold")

keys = ["eps_M", "k_aux_M", "mu_fac", "cp_fac", "d_hole"]
labels = ["M roughness", "M auxiliary $K$", "Viscosity", "$c_p$", "Orifice bore"]
st = np.array([data["sobol"][k]["ST"] for k in keys])
ci = np.array([data["sobol"][k]["ST_conf"] for k in keys])
order = np.arange(len(keys))[::-1]
ax1.barh(order, st, color="#176b87", height=0.56)
ax1.errorbar(st, order, xerr=ci, fmt="none", ecolor="#193e50", capsize=2, lw=0.9)
ax1.set_yticks(order, labels)
ax1.set(xlabel="Sobol total-order index $S_T$", xlim=(0, 0.82))
ax1.grid(axis="x", alpha=0.16, lw=0.6)
ax1.set_axisbelow(True)
ax1.text(0.02, 0.98, "(b)", transform=ax1.transAxes, va="top", fontweight="bold")
ax1.text(0.98, 0.02, "6 kW; 10-axis design box\n95% bootstrap half-width", transform=ax1.transAxes, ha="right", va="bottom", fontsize=6.8, color="0.3")

for suffix, dpi in (("svg", None), ("png", 600)):
    fig.savefig(ROOT / f"figure_v1_table2_recheck_20261109.{suffix}", dpi=dpi)
plt.close(fig)
