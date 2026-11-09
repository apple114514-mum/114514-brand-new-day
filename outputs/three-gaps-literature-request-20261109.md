# 三项输入闭合的文献清单

2026-11-09。用途：供用户寻找原文，并在拿到后判断其能否形成**设计阶段的条件模型**。本项目主线是独立指定 P/M 物理输入、分别前向求解，再计算预先定义的 FoM；以下任何文献数值都不用于反调 M，使其满足 H2TS 或 `K_M=22.8`。

## 先读已经拥有的文献：无需重复寻找

| 对应问题 | 原文 | 直接核查的位置 | 能提供什么／不能提供什么 |
|---|---|---|---|
| ① P 侧基准 | **Yue et al. 2017**, *Flow characteristics of natural circulation in a lead–bismuth eutectic loop*, *Nuclear Science and Techniques* 28:39, DOI `10.1007/s41365-017-0187-x`。仓库 `outputs/yue-2017-kylin-original-20261103.pdf` | PDF p2 Table 1；p3 式(3)、(6)–(9)；p4 Table 2/3、§4.1；p5 §4.2；p6 §5.1–5.2 | p4 的 **P-CFD 分支**声明了 17.9 kW、油侧 `h=4.89 W/(cm²·K)` 与 `T∞=200 °C`；p5 声明绝热、阀门改直管。Table 2 的 `1.25 kg/s、K=22.8` 只是理论阻力取点，不是该 CFD 或实验的实测流量。可选一个同口径 P 分支，不可拼接。 |
| ① P 实验条件 | **Li et al. 2015**, *Experiments and analysis on LBE steady natural circulation in a rectangular shape loop*, *Progress in Nuclear Energy* 81:239–244, DOI `10.1016/j.pnucene.2014.12.009`。仓库 `outputs/li-2015-kylin-original-20261103.pdf` | PDF p2–5，特别是 §2、§3.2 与 24 kW 工况描述 | 给设施、油侧约 `1.0 kg/s`、24 kW 最大阀开度及 `ṁ≈1.21 kg/s` 等**随工况走的条件**；未给可直接复用的阀门 `K_v(Re,开度)`。实验流量由热平衡反算。 |
| ① 设施规格 | **IAEA LFR-21 KYLIN-II TH NC facility profile**。仓库 `outputs/lfr-21-kylin-ii-nc-original-20261102.pdf` | PDF p1–3 | 可复核 24 kW、2.6 cm 管、HS 1.8 m、HX 1.5 m；未给油侧 UA/阀位，流量计描述前后不一致。 |
| ② 冷却器 LBE 侧 | **OECD/NEA 2015**, *Handbook on Lead-bismuth Eutectic Alloy and Lead Properties, Materials Compatibility, Thermal-hydraulics and Technologies*, NEA No. 7268。用户已上传全书 `OECD_NEA_2015_LBE_Handbook.pdf`；仓库有阻力关键页 `outputs/fluid-component-nea-evidence-20261108.pdf` | **全书 PDF p684–697**，第 10 章 §10.4.1、Tables 10.4.3–10.4.4、§10.4.3；物性见 PDF p131 Table 2.19.3 | 圆管 LBE 均匀热流：Table 10.4.3 推荐 `Nu=5.9+0.015 Pe^0.8`，表中 RMS 8.7% 是样本拟合统计，**不是硬误差界**。均匀壁温另见 Table 10.4.4；真实冷却器若轴向热流变化，须分段并写边界选择。环隙不可仅把圆管式的直径换成水力直径。 |
| ② 净热与控制 | **Zhang et al. 2020**, *Experimental investigation on flow and heat transfer characteristics of lead–bismuth eutectic in circular tubes*, *Applied Thermal Engineering* 180:115820, DOI `10.1016/j.applthermaleng.2020.115820`。用户上传 `1-s2.0-S1359431120333020-main.pdf` | PDF p3–6，尤其 p4 的油回路与入口温度控制、p5 式(13)–(15) | 给出“电功率 `UI`、测试段热损、净加热量”分账与油侧稳温的实例；它的设备热损、管径和油侧能力不是拟建 M 的参数。 |
| ③ 阻力基础 | **OECD/NEA 2015** 同上 | 全书 PDF p931–940：式(15.1)–(15.2)，Tables 15.3.2–15.3.6、15.4.1，§15.5 | 圆管 Churchill、有限厚孔板、面积突变的分件式和 Re 条件；第 3 孔板式列 `Re>10³`，但 HELIOS 最佳实践总体推荐只限实验 `10⁴<Re<2×10⁵`，自然循环尚待验证。要分清“表列公式域”与“LBE 基准验证域”。 |
| ③ 弯头 | **Al-Tameemi & Ricco 2018**, *Pressure-loss coefficient of 90° sharp-angled mitre elbows*, *Journal of Fluids Engineering*。仓库 `outputs/altameemi-ricco-mitre-original-20261103.pdf` | PDF p3 实验直管布置；p5 式(4) `K=427.5 Re^-0.77+0.9`，`500≤Re≤60000` | 仅适用于指定锐角斜接几何；水/空气结果迁移至 LBE 是**模型选择**，不是已测 LBE 弯头误差。 |
| ③ LBE 对照 | **Shi et al. 2019**, *Experimental study on the natural circulation capability and heat transfer characteristic of liquid lead bismuth eutectic*, *Progress in Nuclear Energy* 115:99–106, DOI `10.1016/j.pnucene.2019.03.003`。用户上传 `1-s2.0-S0149197019300605-main.pdf`；以及上列 **Zhang 2020** | Shi PDF p2 实验环隙 26/20 mm、p6 式(7) 与 Fig.12；Zhang PDF p4–6，特别是 p6 式(24) | Shi 给 LBE 环隙 `5000<Re<35000` 的拟合；Zhang 给 LBE 圆管 `3.8×10⁴<Re<1.8×10⁵` 的拟合。可做**模型形式对照**；几何或 Re 与拟建 16 mm 管并不重合，不能直接充当其概率区间或保证上界。 |

## 真正值得你再找的原文：按优先顺序

1. **Cho et al. 2011**, *Benchmarking of thermal hydraulic loop models for Lead-Alloy Cooled Advanced Nuclear Energy System (LACANES), Phase-I: isothermal steady state forced convection*, *Journal of Nuclear Materials* **415:404–414**, DOI **`10.1016/j.jnucmat.2011.04.043`**。Yue ref. 21、NEA 2015 第 15 章均引用。请重点看 HELIOS 的孔板几何、Re、压差测点、闸阀和局阻建模误差。它能加强构件模型的证据链，**无法替 KYLIN 阀位定值**。
2. **吴磊、贾海军、刘洋等，2016**，《自然循环系统流动—阻力特性理论和实验研究》，《核动力工程》**37(03):10–15**。赵鹏程 2020 的参考文献 [5]。请重点查：工质、回路拓扑、局阻清单、流动—阻力曲线、热边界是否同工况记录。若只是水回路，仍可用于**方法或模型形式**，不可当 LBE 数值。
3. **若有具体换热器设计资料，优先于再找泛泛的 LBE 论文**：拟建 M 的冷却器管径、有效换热长度、油种类和 `c_p/μ/k(T)`、油侧流量范围、入口温度或控制律、保温与热桥规格。以 NEA 第 10 章求 LBE 侧 `h`，配油侧关联式及壁热阻，才可前向计算 `UA(ṁ_LBE,ṁ_oil,T)` 和控制所需冷却量。单篇其他台架的 `UA` 无法移植为这台设备的验收值。

## 找回来之后如何判定“能填域”

每篇请保留**原文 PDF**，并指出表号/式号/页码、几何、参考动压、工质、Re/Pe 与温度范围、边界条件、误差是最大值还是拟合统计。满足**同几何且同流动范围**的数值才考虑直接输入；不满足时只能给独立的模型形式分支。设计尺寸、公差、控制目标与功能比较尺 `r_ref` 属于论文事先声明的工程条件，文献提供计算依据，不会替研究者决定它们。

分析采用 norman-paper-reading 技能｜作者：N同学｜小红书：N同学｜B站/抖音：耐心的N同学

Analysis performed using the norman-paper-reading skill | Author: N同学 | Xiaohongshu: N同学 | Bilibili/Douyin: 耐心的N同学
