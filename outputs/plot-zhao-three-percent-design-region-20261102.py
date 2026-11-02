#!/usr/bin/env python3
"""Render the Zhao model's illustrative |D_m|<=3% design band.

Input: zhao-three-percent-design-region-20261102.csv (scenario values).
Output: PDF, SVG, and 600 DPI PNG in the same directory.
"""

import csv
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mpl-zhao-design-band"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "zhao-three-percent-design-region-20261102.csv"
BASE = HERE / "zhao-three-percent-design-region-20261102"

with SOURCE.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

delta = [100 * float(r["delta_scenario"]) for r in rows]
lower = [float(r["w_min_for_abs_D_le_3pct"]) for r in rows]
upper = [float(r["w_max_for_abs_D_le_3pct"]) for r in rows]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Noto Sans CJK SC", "DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 9,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.linewidth": .8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "legend.frameon": False,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": .04,
})

fig, ax = plt.subplots(figsize=(3.35, 2.55))
ax.fill_between(delta, lower, upper, color="#1f77b4", alpha=.16,
                label=r"Model feasible: $|D_m|\leq3\%$")
ax.plot(delta, lower, color="#1f77b4", lw=1.2, label="Lower w limit")
ax.plot(delta, upper, color="#d62728", lw=1.2, label="Upper w limit")
ax.axvline(0, color="#6b6b6b", lw=.7, ls=(0, (3, 2)))
ax.set_xlim(min(delta), max(delta))
ax.set_ylim(0, 1)
ax.set_xticks([-20, -15, -10, -5, 0, 5, 9.27556])
ax.set_xticklabels(["-20", "-15", "-10", "-5", "0", "5", "9.28"])
ax.set_xlabel(r"Assumed form-loss mismatch $\delta$ / %")
ax.set_ylabel(r"Friction share $w$ / 1")
ax.text(.03, .75, "Zhao idealized model\nδ uncalibrated",
        transform=ax.transAxes, ha="left", va="top", fontsize=7.0,
        color="#555555")
ax.legend(loc="upper right", handlelength=1.8, borderaxespad=.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.savefig(BASE.with_suffix(".pdf"))
fig.savefig(BASE.with_suffix(".svg"))
fig.savefig(BASE.with_suffix(".png"))
plt.close(fig)
print(BASE)
