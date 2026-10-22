---
name: research-plot
description: 科研数据绘图与出图规范。当用户要求画图、出图、把数据做成图表、统一图表风格、生成论文级插图、画温度/流量/压力曲线、实验与计算对比图时使用。输出高 DPI 的 PNG/SVG/PDF，符合期刊投稿要求。
---

# 科研出图（research-plot）

把数据画成能直接放进论文或汇报的图。目标是**风格统一、单位齐全、可复现**，而不是好看。

## 一、先确认三件事

1. **图的用途**：论文插图（单栏 8.5 cm / 双栏 17 cm，300–600 DPI，矢量优先）／组会汇报（16:9，字号放大）／内部快速看（可以粗糙）
2. **数据类型**：x-y 两列？多工况对比？误差带？双 Y 轴？子图？
3. **单位与工况标注**：横纵轴单位、工况名（如 q=50 kW/m²、Tin=300 ℃）

用户没说就按「论文插图」处理，并在交付时说明假设。

## 二、统一样式（默认值，可被用户覆盖）

- 字体：英文 Arial / Times New Roman，中文 Noto Sans CJK SC 或 SimSun
- 字号：坐标轴标签 8–9 pt，刻度 7–8 pt，图例 7–8 pt，标题一般不加（论文图标题写在图注里）
- 线宽：数据线 1.0–1.5 pt，坐标轴 0.8 pt，误差棒 0.8 pt
- 坐标轴：只保留左、下边框，刻度朝内，刻度线长度 3 pt
- 图例：无边框、无背景填充，放在不遮挡数据的空白区
- 颜色：色盲友好（如 #1f77b4 / #d62728 / #2ca02c / #ff7f0e），不用彩虹色
- 网格：默认不加；需要时用浅灰虚线、线宽 0.4

## 三、Python 模板

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Noto Sans CJK SC", "SimHei", "Arial", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 8,
    "axes.labelsize": 9,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.linewidth": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "legend.frameon": False,
    "figure.dpi": 150,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

fig, ax = plt.subplots(figsize=(3.35, 2.6))   # 单栏 8.5 cm 宽
# ax.plot(...) / ax.errorbar(...)
ax.set_xlabel("时间 t / s")
ax.set_ylabel("质量流量 G / (kg·m⁻²·s⁻¹)")
fig.savefig("figures/fig-xxx.pdf")
fig.savefig("figures/fig-xxx.png")
```

中文显示方块 = 字体没设对，先查字体是否可用（`fc-list :lang=zh`），不要靠猜。

## 四、常见图的画法约定

- **实验 vs 计算对比**：实验点用 marker + 误差棒，计算用实线；同一工况同色，图例写清「EXP」「CFD」
- **多工况**：按物理量递增排序配色（浅→深），不要随机取色
- **双 Y 轴**：左右轴各标单位与颜色，轴标签颜色与对应曲线一致
- **子图**：(a)(b)(c) 标在左上角，字号与正文一致；共享 X 轴时只保留底部刻度标签
- **无量纲图**：明确写清 Nu、Re、Pr 的定义式与特征长度，否则图无意义

## 五、交付前自检

- [ ] 横纵轴都有标签且带单位
- [ ] 图例与正文称呼一致，没有互相遮挡
- [ ] 数据点/曲线没有被裁切，刻度范围合理
- [ ] 图上文字在缩放后仍可读（打印 A4 时不小于 7 pt）
- [ ] 文件名有含义（`fig-nu-vs-re.pdf`），不用 `图1.png`
- [ ] 给出生成脚本，保证可复现

## 六、不要做的事

- 不要为了「好看」改坐标轴范围或截断数据（会误导结论）
- 不要把不同量纲的数据硬画在同一根轴上
- 不要用 3D 柱状图、饼图表达科研数据
- 不要凭空补数据点拟合曲线
