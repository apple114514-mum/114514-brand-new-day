"""Plot the two bulk-flow outputs from the corrected conditional model."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
report = json.loads((ROOT / "temperature_fom_v2_analysis.json").read_text())
rows = report["nominal"]
q = [r["Q_W"] / 1000. for r in rows]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "svg.fonttype": "none"})
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), layout="constrained")
a.plot(q, [r["D_massflux_pct"] for r in rows], "o-", color="#176b87", label="Mass flux $D_j$")
a.plot(q, [r["D_temperature_pct"] for r in rows], "s-", color="#b55730", label="Heater rise $D_T$")
a.axhline(0, color="0.45", lw=0.7)
a.axvline(4.3, color="0.5", ls=":", lw=0.75)
a.set(xlabel="Common electric power (kW)", ylabel="Conditional deviation (%)", xlim=(2.9, 6.1))
a.legend(frameon=False, fontsize=7, loc="center right")
a.grid(alpha=0.17, lw=0.5)
a.text(0.02, 0.97, "(a)", transform=a.transAxes, va="top", fontweight="bold")

b.plot(q, [r["T_HS_out_P_K"] for r in rows], "o-", color="#176b87", label="Prototype P")
b.plot(q, [r["T_HS_out_M_K"] for r in rows], "s-", color="#b55730", label="Model M")
b.set(xlabel="Common electric power (kW)", ylabel="Heater-exit bulk temperature (K)", xlim=(2.9, 6.1))
b.legend(frameon=False, fontsize=7)
b.grid(alpha=0.17, lw=0.5)
b.text(0.02, 0.97, "(b)", transform=b.transAxes, va="top", fontweight="bold")

for ext, dpi in (("svg", None), ("png", 600)):
    fig.savefig(ROOT / f"temperature_fom_v2_20261109.{ext}", dpi=dpi, bbox_inches="tight")
plt.close(fig)
