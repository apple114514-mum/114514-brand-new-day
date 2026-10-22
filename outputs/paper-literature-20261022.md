# “失真度先验性分析”与相关文献线索

## 先澄清术语

Carnevali 等（2025）原文没有将 “a-priori distortion analysis” 作为一个被明确定义并已验证的独立方法。至少有三个不同问题：

1. **实验设计前的失真识别/预估**：给定原型与缩比方案，用相似准则、无量纲群或守恒方程预判哪些过程难以相似。这类设计阶段分析已有大量方法，不是空白。
2. **实验或计算之后的失真确认**：用 IET 结果和成熟系统代码逐项比较过程贡献。本文第 2、9 页明确称这类工作为 a-posteriori scaling analysis。
3. **把失真映射到安全评价量并设容许界限**：不只说“某个无量纲比值偏离”，而要说明偏离使 PCT、压力交叉时间等 FoM 改变多少、何时不可接受。本文第 2、9–10 页把这部分描述为仍需更客观、可验证判据及更多混合计算支持的研究方向。

另一个容易混淆的“先验”是 GSA 在开始时**由专家预选模型和参数范围**（第 3–5、9–10 页）。这是输入设定方式，既不表示先验失真量已被准确预测，也不代表贝叶斯意义上的先验概率分布。

因此，较准确的判断是：**失真识别和设计前尺度预判并非空缺；FoM 导向的失真影响量化、容许阈值、跨工况验证与时间依赖分析在这篇文章中仍不充分。** 这说的是本文证据范围，不能据此断言整个领域从未做过。

## 文献线索

以下题录均从 Carnevali 等（2025）PDF 第 10–11 页参考文献核对。当前云环境无法访问出版商、DOI 和文献检索网站，所以这些是**原文所引的定向阅读清单**；除 Carnevali 等（2025）外，我尚未取得并核对各文献全文，不能替它们宣称具体数值结果或“首次提出”。

| 优先 | 文献（按原文参考文献著录） | 与问题的关系 | 建议核查 |
|---|---|---|---|
| 1 | OECD/NEA (2017), *A state-of-the-art report on scaling in system thermal-hydraulics applications to nuclear reactor safety and design*, NEA/CSNI/R(2016)14 | 缩比分析方法与应用的综述入口 | 区分设计前、试验后及代码辅助评估章节 |
| 2 | Zuber, Rohatgi, Wulff & Catton (2007), *Application of fractional scaling analysis (FSA) to loss of coolant accident (LOCA): methodology development*, Nuclear Engineering and Design 237 | FSA/效应度量与失真判据的早期方法基础；本论文第 2、9 页引用 | 检查实际容许界限的定义和是否依赖 FoM |
| 3 | Catton, Zuber, Wulff & Rohatgi (2009), *Application of fractional scaling analysis (FSA) to loss of coolant accidents (LOCA); component level scaling for peak clad temperature*, Journal of Fluids Engineering | 把部件尺度与 PCT 联系起来，是用户所问 FoM 导向分析的优先候选 | 看是否给出可检验的 FoM 误差/容许准则，而非仅过程排序 |
| 4 | Ishii et al. (1998), *The three-level scaling approach with application to the Purdue University Multi-Dimensional Integral Test Assembly (PUMA)*, Nuclear Engineering and Design 186, 177–211 | 设计阶段多层尺度分析的经典案例；证明“先验分析完全空白”不成立 | 比较系统、部件和局部层级如何安排 |
| 5 | Ciechocki, Carnevali, Bestion & Rossi (2022), *Scaling analyses of a SB-LOCA counterpart test between BETHSY and LSTF facilities and a three loops PWR*, NED 400 | 本文采用的前期三尺度对照基础；可能最直接讨论哪些过程已经失真 | 核对其过程项数值、实验/模拟差异、是否实施逐项校正 |
| 6 | Ciechocki, Carnevali, Bestion & Rossi (2022), *Scaling analysis of the loop seal plugging and clearing phenomena in a SB-LOCA transient on the BETHSY facility*, Nuclear Engineering and Design 400 | 水封堵塞/清除及阶段时间对后续干涸、PCT 的影响 | 看实测约束与 CATHARE 预测偏差 |
| 7 | Ciechocki, Carnevali, Bestion & Rossi (2024), *Scaling analyses of a SB-LOCA counterpart test between BETHSY and LSTF and a three loop PWR*, Nuclear Engineering and Design 422 | 与第 5 条题名非常接近；本论文同时列出 2022 与 2024 项 | 先核对是否为不同版本、扩展论文或参考文献重复/误记 |
| 8 | Bestion, Carnevali & Ciechocki (2023), *The use of System Codes for Scaling Analysis and the use of Scaling tools for the Analysis of Code Predictions*, NURETH-20 | 双向结合系统代码与尺度工具，贴近失真校正策略 | 查找代码适用性与验证矩阵的限定 |
| 9 | Joon Yoon, Alyammahi, Al-Yahia & Leung (2022), *The scaling effect analysis of counterpart test between LSTF and ATLAS IET facilities on 1% top head break LOCA*, NED 397 | 另一种跨设施 LOCA 对照，可用来检验方法能否迁移 | 看被定义的失真量、评价量和工况差别 |
| 10 | Larget & Gautier (2020), *Increasing conservatism in BEPU IB LOCA safety studies using complementary and industrially cost effective statistical tools*, BEPU 2020；Da Veiga (2015), *Global sensitivity analysis with dependence measures*, Journal of Statistical Computation and Simulation 85(7), 1283–1305 | GSA 和统计依赖量的依据，不等于直接的尺度失真判据 | 分辨“参数敏感性”与“尺度失真幅度” |

**优先阅读顺序：** 先看 OECD/NEA 综述和 Zuber 2007，建立“先验识别/判据”的术语；再看 Catton 2009 与 Ciechocki 2022/2024，判断 FoM 导向量化到底做到什么程度；最后用 Bestion 2023 和 Carnevali 2025 对照代码与 GSA 的新用途。

## 可落地的检索问题

待可访问文献全文时，可逐篇记录四项：① 在装置设计前还是实验后分析？② 失真量如何定义和估计？③ 是否实际计算对 PCT 等 FoM 的影响？④ 判据是否经过不同工况/设施验证？只有后两项均有实证，才足以说解决了本文提出的 FoM 导向可接受性问题。

**来源界限：** 本文件直接核查了 Carnevali 等（2025）的正文及参考文献；对其他条目的具体结论尚未作全文核验。
