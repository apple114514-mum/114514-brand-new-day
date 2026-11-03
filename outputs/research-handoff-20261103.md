# 自然循环缩比研究：2026-11-03 当前交接

这份 Markdown 是给 Workbuddy 的**当前下载入口**。先读第十三轮复核，再看同篇五功率趋势检查与第十二轮复核；旧文件保留演变记录，不应直接引用已撤回说法。以下 GitHub 链接在本文件单独下载后仍可使用；本地仓库执行 `git pull`。

## 第十三轮新增：拟合 `L` 与物理热损分账

| 文件 | 下载链接 | 用法 |
|---|---|---|
| **v13 复核** | [PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v13-review-20261103.pdf) · [Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v13-review-20261103.md) | 修 `H` 的公式位置；保留 `L≈1.25 kW` 为相对拟合；审计绝对热量口径、局阻“上限”、温差图读及留一功率检验 |
| **独立复算** | [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v13-independent-audit-20261103.py) · [结果](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v13-independent-audit-20261103.txt) | 原 241 行日志隔离复现；绝对水平 `18.75 kW`、单点高度正确方向 `2.339 m`、留一最低功率预测 `0.654 kg/s` |
| **Workbuddy 上传原件** | [HTML](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v13-upload-report-20261103.html) · [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v13-upload-20261103.py) · [日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v13-upload-log-20261103.txt) · [参数表](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v13-upload-provenance-20261103.md) | 留存原命题；解释以复核报告为准 |

**给 Workbuddy 的修订重点：** 由动量与能量式得到 `ṁ³=H·P_net/(C·K)`，`H` 在分子；高度单独解释图读比值需低功率 `H≈2.339 m`，非 `4.69 m`。`0.77` 是特定水/空气弯头拟合项的指数，不能给 KYLIN 总局阻上界，所以“阻力至多 63% / 热账至少 37%”和 `0.66/1.38 kW` 三分支不能作为物理判据。`L≈1.25 kW` 是 17.9 kW 锚点归一化后的曲线偏移：选用的理论 K、H、C 绝对代回需约 `18.75 kW` 净热，高于 `17.9 kW` 输入；若 L 指加热段外漏，Yue 按输入功率反算的报告流量也必须同步重算。留下 4.3 kW 不参与拟合时 `L≈0.745 kW`、该点残差 `+0.034 kg/s`。下一步须测与原流量反算独立的入流体热量或主流量，并记录逐点阀位及压降；至少两功率点检验“恒定热损”。

## 新增：Yue 同篇五功率趋势检查

| 文件 | 下载链接 | 用法 |
|---|---|---|
| **趋势检查** | [PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-same-paper-trend-review-20261103.pdf) · [Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-same-paper-trend-review-20261103.md) | Yue §5.1 同一油侧设定，17.9 kW 作锚，四条实验曲线作图读条件对照；4.3 kW 低功率点偏离联合固定闭合 |
| **原图与复算** | [Yue Fig.4 原图](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-fig4-original-20261103.png) · [五点 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-same-paper-trend-20261103.csv) · [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-same-paper-trend-20261103.py) · [输出](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-same-paper-trend-20261103.txt) | 四个低功率流量为图读约值；`±0.03 kg/s` 是读图敏感性情景，不是仪表误差 |

**给 Workbuddy 的下一步：** 同篇 4.3/7.6/11.2/15.3/17.9 kW 序列比 Li↔Yue 跨论文点更适合先做趋势检查；Yue §5.1 明言油侧条件保持相同，仍未给逐点阀位。固定 `K、η、H、C` 的三次方律从 17.9 kW 预测 4.3 kW `ṁ≈0.696`，Fig.4(c) 平台约 `0.62 kg/s`。不要把残差归给单一机制，也不要用 `ṁc_pΔT_HS≈P` 作独立热账，因为文中流量正是这样反算。优先找二次油进出口焓差、加热器电功率/热损与阀位记录；否则把此结果写成“联合固定闭合的条件趋势诊断”，成对 `δ` 仍空。

## 第十二轮新增：口径分级和判别门槛

| 文件 | 下载链接 | 用法 |
|---|---|---|
| **v12 复核** | [PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-review-20261103.pdf) · [Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-review-20261103.md) | 保留五档溯源、正指数求根与控制体修正；收窄 `P/ṁ³`、热损百分数、留出点和统计判别门槛 |
| **独立复算** | [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-independent-audit-20261103.py) · [输出](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-independent-audit-20261103.txt) | 271 行原日志逐行复现；代理比 `2.662`、条件 `η₅/η₂₀=0.375657`、理想 95% 区分尺度及份额差 |
| **工况台账** | [修订 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-reviewed-condition-ledger-20261103.csv) · [Workbuddy 原 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-upload-ledger-20261103.csv) | 原 6 行保留，增加复核说明；将 `0.002826 kg/s` 从统一留出验收条件降为特定半差示例 |
| **Workbuddy 上传原件** | [HTML](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-upload-report-20261103.html) · [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-upload-20261103.py) · [日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-upload-log-20261103.txt) · [参数表](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-upload-provenance-20261103.md) · [可运行 ZIP](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v12-repro-20261103.zip) | 原样留存；ZIP 含 v5 依赖。解释以复核报告和证据矩阵为准 |

**给 Workbuddy 的修订重点：** `P/ṁ³≈2.66` 是图读电功率与热平衡反算流量组成的代理；跨工况比例还含物性因子 `C=c_p/(2βρ²gA²)`。只有令 `K、H、C` 均不变，才有 `η₅/η₂₀≈0.376`；不能宣称实物 5 kW 热效率恰为 38%。两斜率情景差 `0.005652 kg/s`，半差 `0.002826` 只是理想化规则，且两个预测都比 17.9 kW 观测低 `0.024–0.030 kg/s`。先对齐阀位、油侧、净热与误差链，再称留出检验；若设定不同但有记录并纳入模型，也可检验。Yue 理论份额与四段反标定份额名义差约 25 个百分点、倍率 1.5，属于口径诊断。

## 第十一轮新增：KYLIN 单侧闭合

| 文件 | 下载链接 | 用法 |
|---|---|---|
| **单侧闭合复核** | [PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-review-20261103.pdf) · [Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-review-20261103.md) | 六行有效高度复算、Yue 表2分级、Li Fig.4 控制体、17.9 kW 斜率符号修正及下一步 |
| **独立算术** | [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-independent-audit-20261103.py) · [输出](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-independent-audit-20261103.txt) · [v11 原脚本复现 ZIP](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-repro-20261103.zip) | 原 379 行已复现；正确正指数自洽求根 `1.095991/1.090333 kg/s`，差 `0.005658 kg/s` |
| **工况缺口台账** | [CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-condition-ledger-20261103.csv) | 把 Li 实验、Yue 实验与 Yue 理论行分开；阀位、净热、HS 温升及不确定度缺项明留空 |
| **原文页图** | [Yue Table 3](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-table3-original-20261103.png) · [Li Fig. 4](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/li-2015-fig4-original-20261103.png) | 表明六功率矩阵为理论结果；Li Fig.4(b) 是冷热腿温差，不能当加热段温升 |
| **Workbuddy 上传原件** | [HTML 报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-upload-report-20261103.html) · [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-upload-20261103.py) · [日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-upload-log-20261103.txt) · [参数溯源表](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-v11-upload-provenance-20261103.md) | 供保留演变记录；解释以本轮复核和[证据矩阵](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/paper-workspace/claim-matrix.md)为准 |

**给 Workbuddy 的修订重点：** `H_eff≈3.312 m` 与 Xu 3.35 m 是同一 KYLIN 几何的跨文献一致性检查，不是独立实验验证；Yue Table 2 原始理论值是 L1，反解 `f` 的形式未定。v11 的“`m=.05`”分支实际用了负斜率，修正后的 17.9 kW 两情景差约 `0.0057 kg/s`。Li Fig.4 的冷热腿温差不能作为加热段焓温升，“K 降 2.95 倍最可能因阀位”撤回；固定并记录阀位仍是必要的实验条件。300 K 的温度设计与该设施最低 150°C 运行范围不符，`σ_D=2%` 没有量测来源。下一步先补阀位、净热、热损与误差链，再做 17.9 kW 验证及物理 GSA。

## 第十轮新增：先看这里

| 文件 | 下载链接 | 用法 |
|---|---|---|
| **可辨识性复核** | [PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/identifiability-v10-review-20261103.pdf) · [Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/identifiability-v10-review-20261103.md) | 保留单点 `A+Bf=K` 退化；修正 δ 的物理含义、两点识别、误差表与双侧 3% 带 |
| **独立数值** | [复算脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/identifiability-v10-independent-audit-20261103.py) · [输出](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/identifiability-v10-independent-audit-20261103.txt) · [原脚本可运行 ZIP](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/identifiability-v10-repro-20261103.zip) | v10 248 行原日志已复现；独立脚本显示假设十倍功率跨度的 `σ_B/B≈32%`，不是 9.3% |
| **Workbuddy 上传原件** | [HTML](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/identifiability-v10-upload-report-20261103.html) · [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/identifiability-v10-upload-20261103.py) · [日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/identifiability-v10-upload-log-20261103.txt) · [README](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/lit-mirror-upload-readme-20261103.txt) | 用于追踪原命题与数值；解释以复核报告为准 |
| **文献镜像与新技能** | [三篇原文＋逐页文本＋证据卡 ZIP](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/literature-mirror-20261103.zip) · [上传技能包](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/lit-mirror-upload-skillpack-20261103.zip) · [本地适配说明](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/.codex/skills/LIT-MIRROR-IMPORTED-20261103.md) | 新装 `lit-mirror`；未覆盖旧技能；镜像 3 PDF/3 TXT/5 断言，审计通过但仍需核 PDF 内容 |

**第十轮结论边界：** 单个成对流量 FoM 只识别一条 `A,B` 等值线；`δ` 可由同口径成对局阻独立约束，不能说“永不可观测”。Li/Yue 是 KYLIN 单侧资料，不是两套装置的两条方程。Zhao 的条件点值 `+2.876835%` 距 +3% 为 `0.123165 pp`；`B±10%` 固定 `A` 的带是无来源情景，不是该点的测量不确定度。下一轮请先执行下文的 KYLIN 单侧闭合与 17.9 kW 留出核验，再讨论成对参数域和 GSA。

## 先下载

| 文件 | 链接 | 内容 |
|---|---|---|
| **本轮复核** | [PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-review-20261103.pdf) · [Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-review-20261103.md) | 一手原文坐标、逐构件指数反例、KYLIN 名义环隙与理论阻力、有效结论和限制 |
| **复算** | [独立脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-independent-audit-20261103.py) · [Yue Table 2 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-table2-resistance-20261103.csv) · [证据矩阵](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/paper-workspace/claim-matrix.md) | `m=.2` 交点、反例、名义流道、理论摩擦份额与来源门禁 |
| **一手文献** | [Li 2015 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/li-2015-kylin-original-20261103.pdf) · [Yue 2017 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-kylin-original-20261103.pdf) · [Al‑Tameemi–Ricco 原稿](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/altameemi-ricco-mitre-original-20261103.pdf) | 全文已取得；弯头上传稿未核正式 DOI/卷页 |
| **原图** | [Yue Table 1](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-table1-original-20261103.png) · [Yue Table 2](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-table2-original-20261103.png) · [Li Fig. 7](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/li-2015-fig7-original-20261103.png) · [弯头 Fig. 6](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/mitre-elbow-fig6-original-20261103.png) | 从所附 PDF 原页裁取并目视核验，保留表头、坐标和图注 |
| **Workbuddy 本轮原件** | [HTML 报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-upload-report-20261103.html) · [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-upload-script-20261103.py) · [262 行日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-upload-log-20261103.txt) · [参数表](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-upload-table-20261103.md) | 上传计算可复现；解释以本轮复核修订 |
| **前轮交接** | [2026-11-02 总索引](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/research-handoff-20261102.md) · [第八轮输入分辨率复核](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/provenance-v8-review-20261102.md) | 原有计算、撤回记录、Zhao 原文和方法背景 |

## 本轮能守住的结论

1. **几何落地：** Yue PDF 第 2 页 Table 1 与正文给 KYLIN 主管内径 26 mm、加热段内径 54 mm、**一根同心棒直径 22 mm**。名义环隙面积为 `1.91009×10^-3 m²`，水力直径 `32 mm`；支撑件等未列，不能等同验收净面积。54/22 mm 不能再归给 Xu Table 1。
2. **单侧阻力有模型锚：** Yue PDF 第 4 页 Table 2 属**理论计算**，不是实测；按其式(9)，`K_pipe−1` 为管段沿程摩擦，在表内五点占 `K_total` 的 `73.25–73.97%`。此前四段模型反标定的 `48.67%` 与之不一致，应查摩擦关联式、管长和局阻闭合，不挑一个当真值。
3. **通用指数 A2 有反例：** Al‑Tameemi–Ricco 式(4)仅适用于水/空气、圆管 90° 锐角斜接弯头、`500≤Re≤60000`。其 `m=−dlnK/dlnRe` 于 **Re≈11666** 降至 `.2`；原文 ±3% 为**平均拟合误差**。`Re_M=4000,Re_P=12000` 的关联式比值 `1.340`，超过 `.2` 指数的 `1.246`，但不能移植为 KYLIN 的弯头系数。
4. **留出点口径已核：** Li 正文 24 kW、阀门最大开度给 `1.21 kg/s`（摘要圆整为 `1.2`）；Yue §5.2 给 17.9 kW 理论/实验/CFD `1.10/1.12/1.20 kg/s`。两文实验流量均按加热段能量平衡反算，流量与温升不独立；Yue CFD 又以直管替换阀门并设绝热。17.9 kW 只能在阀门、油侧与热量口径对齐后作候选留出点。

## 下一轮给 Workbuddy 的具体任务

> 先用 Yue 第 2–4 页的 `26/54/22 mm`、`L_pipe≈11 m`、式(3)/(6)–(9) 和 Table 2，逐项复算**单侧**五个阻力点；明确计算 `f` 时使用何种关联式，尤其解释 `Re_tube=27800` 行由 `K_pipe=17.7` 隐含的 Darcy `f≈0.03947` 与光滑管 Blasius `0.02450` 的差。把 Table 2 标为“作者理论结果”，不要标实测。固定 24 kW 参数后，用同一阀位、油侧和加热段热量口径预测 17.9 kW 流量，**不得重新标定**。逐构件 `κ_i=K_i(A_ref/A_i)^2` 要注明面积和开度；未知的 `α_i` 与成对 `δ` 保留为空。通用锐角斜接弯头关联式只作反例，不代入 KYLIN。完成上述单侧闭合后，再讨论成对缩比盒、摄动与 GSA。

分析采用 norman-paper-reading 技能｜作者：N同学｜小红书：N同学｜B站/抖音：耐心的N同学

Analysis performed using the norman-paper-reading skill | Author: N同学 | Xiaohongshu: N同学 | Bilibili/Douyin: 耐心的N同学
