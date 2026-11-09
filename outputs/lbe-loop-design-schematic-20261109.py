"""Render the proposed LBE loop layout (schematic, not construction drawing).

Source: lbe-forward-design-input-spec-20261108.md. Dimensions are nominal.
The loop plan has a consistent 5 m : 3 m aspect ratio; pipe bore and orifice
details are drawn separately at arbitrary magnification.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle


OUT = Path(__file__).resolve().parent
font_manager.fontManager.addfont(
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
)
font_manager.fontManager.addfont(
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
)
plt.rcParams.update({
    "font.family": "sans-serif",
    # Matplotlib exposes the first face of the installed TTC as 'JP'; the
    # collection contains all CJK glyphs required by these Chinese labels.
    "font.sans-serif": ["Noto Sans CJK JP", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "path",
    "pdf.fonttype": 42,
    "savefig.facecolor": "white",
})

INK = "#25364A"
PIPE = "#435A71"
HOT = "#DC5538"
COLD = "#2477B7"
ORIFICE = "#8D4F9E"
SRC = "#1A6E60"      # original correlation or property source
SPEC = "#B07310"     # proposed engineering specification
MUTED = "#657583"
FAINT = "#D9E0E5"


def txt(ax, x, y, s, size=10, color=INK, ha="left", va="center", weight=None, **kw):
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
                   fontweight=weight, **kw)


def arrow(ax, xy1, xy2, color=INK, width=1.7, style="-|>", scale=14):
    ax.add_patch(FancyArrowPatch(xy1, xy2, arrowstyle=style,
                                 mutation_scale=scale, lw=width, color=color))


def dim(ax, xy1, xy2, label, label_xy, size=10):
    arrow(ax, xy1, xy2, MUTED, 1.0, "<->", 11)
    txt(ax, *label_xy, label, size=size, color=MUTED, ha="center")


fig, ax = plt.subplots(figsize=(15.8, 6.3), dpi=150)
ax.set_xlim(-1.45, 14.35)
ax.set_ylim(-1.25, 5.05)
ax.set_aspect("equal")
ax.axis("off")

# Header and two-panel divider.
txt(ax, -1.25, 4.77, "拟建 LBE 自然循环回路｜独立前向设计输入", 18, INK, weight="bold")
txt(ax, -1.25, 4.42, "方案示意；名义尺寸按比例画，管径与孔板局部放大；不是 KYLIN-II 实物或施工图", 10, MUTED)
ax.plot([7.95, 7.95], [-1.02, 4.16], color=FAINT, lw=1.2)

# Main loop centerline: hot leg is left, cold leg right.
xl, xr, yb, yt = 1.0, 6.0, .42, 3.42
ax.plot([xl, xl, xr, xr, xl], [yb, yt, yt, yb, yb], color=PIPE,
        lw=7, solid_capstyle="round", solid_joinstyle="miter", zorder=2)
ax.plot([xl, xl], [yb, yb+1.0], color=HOT, lw=10, solid_capstyle="butt", zorder=3)
ax.plot([xr, xr], [yt-1.0, yt], color=COLD, lw=10, solid_capstyle="butt", zorder=3)

# The four mitre elbows are explicit local losses.
for x in (xl, xr):
    for y in (yb, yt):
        ax.add_patch(Circle((x, y), .085, fc=SRC, ec="white", lw=1.2, zorder=5))

# Source and sink are distributed over one metre, not point sources.
ax.add_patch(Rectangle((.61, yb), .78, 1.0, fc=HOT, alpha=.10,
                       ec=HOT, lw=1.2, zorder=1))
ax.add_patch(Rectangle((xr-.39, yt-1), .78, 1.0, fc=COLD,
                       alpha=.10, ec=COLD, lw=1.2, zorder=1))

# Fixed finite-thickness orifice in bottom horizontal leg.
xo = 3.5
ax.add_patch(Rectangle((xo-.045, yb-.17), .09, .34,
                       fc=ORIFICE, ec="white", lw=.7, zorder=6))
txt(ax, xo, -.04, "固定孔板", 11, ORIFICE, ha="center", weight="bold")
txt(ax, xo, -.30, "孔 d=10.00±0.02 mm；板厚 2.00±0.05 mm",
    9.5, SPEC, ha="center")

# Closed vent / filling branch is off the active flow route.
ax.plot([3.5, 3.5], [yt, 4.01], color=PIPE, lw=3, zorder=3)
ax.add_patch(Polygon([[3.36, 3.77], [3.5, 3.86], [3.36, 3.95]],
                     closed=True, fc=SPEC, ec=SPEC, zorder=5))
ax.add_patch(Polygon([[3.64, 3.77], [3.5, 3.86], [3.64, 3.95]],
                     closed=True, fc=SPEC, ec=SPEC, zorder=5))
txt(ax, 3.75, 3.91, "关闭的排气/灌注支路阀", 10, SPEC)
txt(ax, 3.75, 3.65, "不在正常循环流路；接口计入 K_aux", 9, MUTED)

# Flow direction.
arrow(ax, (xl, 1.83), (xl, 2.13), HOT, 2.5, scale=17)
arrow(ax, (2.02, yt), (2.36, yt), PIPE, 2.5, scale=17)
arrow(ax, (xr, 2.04), (xr, 1.70), COLD, 2.5, scale=17)
arrow(ax, (4.8, yb), (4.45, yb), PIPE, 2.5, scale=17)
txt(ax, 2.58, 3.12, "流向", 9, MUTED)

# Dimension lines: centreline 5 m by 3 m, not to be confused with bore.
dim(ax, (.55, yb), (.55, yt), "3.00±0.01 m", (.16, 1.92), 10)
dim(ax, (xl, -.82), (xr, -.82), "5.00±0.01 m", (3.5, -1.06), 10)
ax.plot([xl, xl], [-.72, -.39], color=FAINT, lw=1)
ax.plot([xr, xr], [-.72, -.39], color=FAINT, lw=1)
dim(ax, (6.73, .92), (6.73, 2.92), "源—汇中心高差 2.00 m", (6.85, 1.92), 9.3)

# Function callouts.
arrow(ax, (-.58, .92), (.52, .92), HOT, 2.0, scale=15)
txt(ax, -.75, 1.28, "加热段", 11, HOT, weight="bold")
txt(ax, -.75, .37, "外加热圆管 1.00 m", 9.7, HOT)
txt(ax, -.75, .12, "Q_e=3–6 kW", 9.5, SPEC)
arrow(ax, (6.10, 2.90), (7.32, 2.90), COLD, 2.0, scale=15)
txt(ax, 6.29, 3.20, "冷却段", 11, COLD, weight="bold")
txt(ax, 6.30, 2.50, "外冷却圆管 1.00 m", 9.5, COLD)
txt(ax, 1.47, 2.09, "直管：D_i=16.00±0.05 mm", 10, PIPE)
txt(ax, 1.47, 1.79, "四边总长 16.00 m", 10, PIPE)
txt(ax, 1.47, 1.41, "四角：90° 锐角斜接弯头", 10, SRC)

# Magnified longitudinal section of the fixed orifice.
txt(ax, 8.33, 4.06, "局部构件（放大、非比例）", 12, INK, weight="bold")
ax.add_patch(Rectangle((8.72, 2.83), 5.03, .79, fc="#ECF2F5", ec=PIPE, lw=1.6))
ax.add_patch(Rectangle((11.13, 2.67), .20, .23, fc=ORIFICE, ec=ORIFICE))
ax.add_patch(Rectangle((11.13, 3.54), .20, .23, fc=ORIFICE, ec=ORIFICE))
arrow(ax, (9.10, 3.23), (10.30, 3.23), PIPE, 1.7, scale=15)
dim(ax, (8.50, 2.83), (8.50, 3.62), "", (8.5, 2.45))
txt(ax, 8.37, 2.50, "D_i=16 mm", 9.2, PIPE, ha="left")
dim(ax, (11.58, 2.90), (11.58, 3.54), "", (11.58, 2.43))
txt(ax, 11.46, 2.49, "d=10 mm", 9.2, ORIFICE)
txt(ax, 11.23, 3.95, "t=2 mm", 9.2, ORIFICE, ha="center")
txt(ax, 12.04, 3.23, "孔板整体损失", 10, ORIFICE)

# Named forward correlations (not a target loss).
txt(ax, 8.35, 2.03, "阻力的正向计算", 11, INK, weight="bold")
txt(ax, 8.35, 1.72, "圆管：Churchill f(Re, ε/D) · L/D", 10, SRC)
txt(ax, 8.35, 1.43, "弯头：K=427.5 Re^(-0.77)+0.9（每件）", 10, SRC)
txt(ax, 8.35, 1.14, "孔板：NEA 2015 表 15.3.3 第 3 式", 10, SRC)

# Controlled thermal and design specification status.
txt(ax, 8.35, .67, "热边界与验收条件", 11, INK, weight="bold")
txt(ax, 8.35, .37, "加热入口 473.15–483.15 K；冷源 ≤433.15 K", 9.4, SPEC)
txt(ax, 8.35, .08, "保温 ≥50 mm；k ≤0.05 W/(m·K)", 9.4, SPEC)
txt(ax, 8.35, -.21, "热桥 UA ≤0.5 W/K；冷却 UA ≥150 W/K", 9.4, SPEC)
txt(ax, 8.35, -.50, "粗糙度 ≤10 μm；辅助口合计 0≤K_aux≤0.5", 9.4, SPEC)
ax.plot([8.35, 13.88], [-.74, -.74], color=FAINT, lw=1)
txt(ax, 8.35, -.93, "绿色＝有原文关联式；棕色＝本研究拟定规格，尚须落实", 8.8, MUTED)

for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"lbe-loop-design-schematic-20261109.{ext}",
                dpi=300, bbox_inches="tight", pad_inches=.10)
plt.close(fig)
