---
name: fluent-post
description: Fluent/CFD 计算结果后处理。当用户提供 Fluent 导出的监测数据（monitor .out）、Reports 积分结果（体积/面积分）、XY 数据（.xy/.csv）、残差记录，需要批量出图、判断收敛、提取特征量（ΔT、Q、Re、Nu、阻力系数）、生成工况对比表时使用。
---

# Fluent 后处理（fluent-post）

把 Fluent 吐出来的乱格式文本，变成**能判断物理正确性**的图和表。核心不是画图，是别把没收敛的结果当结论。

## 一、先认清输入是哪一类

| 文件来源 | 典型特征 | 包含内容 |
|---|---|---|
| Solver → Monitors → 导出 `.out` | 头部 `Iteration  Time Step  Continuity  ...`，可能多段拼接 | 残差、监测量随迭代/时间变化 |
| Reports → Volume/Surface Integrals `.out` | 头部 `Surface Integral` / `Volume Integral`，含 `(m)`、`(m2)` 单位与 `Net` 行 | 面积平均温度、质量流量、换热量 |
| XY Plot 导出 `.xy` / `.csv` | 两列或多列纯数字，首行可能是变量名 | 沿程分布（轴向温度、速度剖面） |
| TUI transcript / 日志 | 文本混排，含 `iter continuity x-velocity ...` | 残差历史 |

拿到文件先**打开看前 20 行**，判断属于哪类，再决定解析策略。不要盲写正则。

## 二、解析要点（Fluent 的坑）

- `.out` 报告文件有**多行表头**和单位行，数据行以空格分隔，列可能不对齐
- Monitor 文件可能把多个监测量**分段拼接**，每段重复一次表头
- `Net` 行是汇总不是数据点，必须排除
- 时间、迭代步可能同时存在两列，别混用
- 单位默认 SI；若模型用的是 mm、L/min 等，**先换算再画图**，并在图上注明

```python
import re
def parse_out(path):
    rows, cols = [], None
    for line in open(path, encoding="utf-8", errors="ignore"):
        if "Iteration" in line or "Time Step" in line:
            cols = line.split()
            continue
        parts = line.split()
        if not parts or not re.match(r"^[-+0-9.]", parts[0]):
            continue
        if parts[0].lower() == "net":
            continue
        try:
            rows.append([float(x) for x in parts])
        except ValueError:
            continue
    return cols, rows
```

## 三、收敛判断（必须给结论）

- 残差：连续相、动量、湍流 < 1e-4；能量 < 1e-6（视松弛因子与问题而定）
- 监测量：最后 20% 迭代内波动 < 1–2%，且无单调漂移
- 守恒性：进出口质量流量偏差 < 0.1%，能量不平衡 < 0.5%
- 结论三选一：**已收敛 / 勉强可接受（说明依据）/ 未收敛（不要出结论）**

未收敛时空有漂亮曲线也不能当结果，必须明说。

## 四、常用处理

- **稳态取值**：默认取最后 20–30% 迭代的平均值，同时给标准差；瞬时值另给
- **瞬态**：完整时间序列出图；有周期性振荡时给周期与幅值（可做 FFT）
- **派生量**（写清公式与特征长度）：
  - 温升 `ΔT = T_out − T_in`
  - 换热量 `Q = m·c_p·ΔT`
  - 雷诺数 `Re = ρ·u·D_h/μ`
  - 努塞尔数 `Nu = h·D_h/λ`，`h = q''/(T_w − T_b)`
  - 阻力系数 `f = 2Δp·D_h/(ρ·u²·L)`
- **工况对比表**：工况名 / 边界条件（热流、入口温度、压力）/ 质量流量 / ΔT / Q / Re / Nu / 备注

## 五、输出

```
post/
├── tables/   cleaned-<工况>.csv、summary.csv
├── figures/  fig-<内容>.pdf（PNG 备用）
└── report.md 处理说明 + 收敛判断 + 关键数值 + 结论
```

作图遵循 `research-plot` 技能（若已安装）；未安装则用其默认样式：中文 Noto Sans CJK、8 pt、单栏 8.5 cm、600 DPI。

## 六、不要做的事

- 不猜列的含义和单位：不确定就问，或标注「列 3 含义待确认」
- 不用未收敛的数据下结论
- 不把不同工况的曲线画在同一根轴上却不标工况
- 不修改原始导出文件，清洗结果另存
- 不假设 Fluent 版本差异不影响格式（19R3 / 2021R1 / 2023R1 的表头略有不同）
