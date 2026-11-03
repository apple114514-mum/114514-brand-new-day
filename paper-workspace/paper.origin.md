# 缩比失真研究状态包

## meta

- 创建：2026-11-02
- 题目（暂定）：铅铋自然循环缩比失真的设计阶段条件界
- 目标期刊：未定
- 最近事务：TX-004
- 参数原始表：[outputs/parameter-provenance-20261102.md](../outputs/parameter-provenance-20261102.md)

## source

| ID | 文件 | 已核范围 | SHA-256 |
|---|---|---|---|
| Z20 | [赵鹏程等 2020 PDF](../outputs/zhao-2020-original-20261102.pdf) | PDF 1、3–6 页，尤其表 2–5 与式(13) | `8e9a3c20d1e6a876ad357e0907f41c6e51fbdd2fdc0b6add06f4ec027337e951` |
| X26 | [Xu FR26-170 PDF](../outputs/xu-fr26-170-original-20261102.pdf) | PDF 2–5 页，尤其表 1–2 与式(7)、(15)–(18) | `713645a3c621ae097b175bc716eb4a0f9bf7d78c9f8070161f4d2b6e69d9a3c5` |
| I21 | [IAEA LFR-21 PDF](../outputs/lfr-21-kylin-ii-nc-original-20261102.pdf) | PDF 1–3 页，设施概况与参数表 | `4f75474bffb9c1650513909ef78043a352016e3e27a6650b8c9d6a0991043e25` |
| L15 | [Li 等 2015 PDF](../outputs/li-2015-kylin-original-20261103.pdf) | PDF 1–5 页，尤其 §2、§3.3、Fig. 7；全文已取得 | `ec9af10604503a3bdb0d3fa2707f6727949d7017eb7baf5af309412b9033882b` |
| Y17 | [Yue 等 2017 PDF](../outputs/yue-2017-kylin-original-20261103.pdf) | PDF 1–6 页，尤其 Table 1–3、式(3)/(6)–(9)、§4–5；全文已取得 | `fd75d3e78b3f43138af30dee01c6f52cf6ae2a46c1a24282668ccb768bd59a3a` |
| AR | [Al‑Tameemi–Ricco 锐角斜接弯头上传原稿](../outputs/altameemi-ricco-mitre-original-20261103.pdf) | PDF 1、5、16 页，式(4)与 Fig. 6；正式卷页/DOI 未核 | `8bc43ac9e50ac87dcbd6d85029e5c636966a17793b42121cb3bf8a5bc6b69649` |

## objects

### Q 研究问题

- Q-01：在明确原型—台架设计映射、模型闭合和有来源参数域后，能否在建台架前给出 FoM 失真的条件包含界？
- Q-02：哪些几何、阻力和物性输入已有一手出处，哪些仍只能做情景？

### C 论点与 E 证据

见 [claim-matrix.md](claim-matrix.md)。本轮只建立输入事实与缺口，不凭空生成物理 `δ` 域。

## relations

`C-01 supported_by E-01`；`C-02 supported_by E-02`；`C-03 supported_by E-03`；`C-04 supported_by E-04`；`C-05 supported_by E-05`；`C-06 supported_by E-06`；`C-07 supported_by E-07`。`C-08` 待补。

`C-09` 是 U-P1/A1–A2 的待验证假设；`C-10` 被独立算式核查反例推翻；`C-11` 被 Z20-P5/表3 与 X26-P4/表1 的来源核读否定。详见 [参数闭合 v1 复核](../outputs/parameter-closure-v1-review-20261102.md)。

`C-12` 由 Z20-P5/表3支持；`C-13/C-17` 是 U8-S 及独立算式支撑的条件归约；`C-14/C-15/C-16` 被目标门槛、面积假设或原文坐标核读否定。详见[第八轮复核](../outputs/provenance-v8-review-20261102.md)。

`C-18/C-19/C-21/C-22/C-23` 由 Y17/L15 全文定位；`C-20` 由 AR-P5/式(4)与 P16/Fig. 6 支撑，仅限锐角斜接弯头；`C-24/C-25` 的实物化或通式化表述撤回。详见[第九轮复核](../outputs/component-re-v2-review-20261103.md)。

## constraints

- 表中“直径”必须保留原文修饰语；不能把未说明的几何直径改写为流通内径。
- 表中数值须标为设计输入、作者理论计算、CFD 输出、设施档案或实测；Li/Yue 实验流量按热平衡反算，不能写成独立直读量。
- Xu 式(9) 的 `δ` 是壁厚，与本研究 `k_M/k_P−1` 的局阻失配参数同字母不同义。
- 参数域和 GSA 分布不能由技能模板、常见公差或 CFD 失真百分点臆定。
- 局阻的 Re 指数上界须有逐构件适用证据；`Re_R≥0.6418` 仅是 Zhao 声明模型 `w=0` 时的条件门槛，不得作为所有 `w` 或 KYLIN 案例的实物保证。
- Map I 的流量比来自 CFD 输出，只能作归约和输入分辨率分析；设计阶段先验预测仍需 Map II 的闭合及有来源的输入域。焓代理功率比与表 3 设计功率比必须分别命名。
- Yue Table 2 只给 KYLIN 单侧理论阻力，不给成对 `δ`。Al‑Tameemi–Ricco 式(4)只支持对应锐角斜接弯头、500≤Re≤60000 的关联式；平均拟合误差不是严格误差包络。

## metrics

- 当前 C-01–C-25 共 25 条；逐条状态和原文坐标见矩阵。L15/Y17 全文已补，原先“全文未取得”的门禁已解除；成对局阻与实际阀位仍缺。
- 目标期刊格式门禁：未启动；当前不判投稿合格。

## transactions

`TX-001 | 2026-11-02 | 原文取象 | Z20/X26/I21 页表核读，建立参数表与 claim-matrix；Li/Yue 全文缺席标空 | type=source-audit`

`TX-002 | 2026-11-02 | 参数闭合复核 | U-P1/U-S 的 131 行日志复现；Z20/X26 原文重核；独立脚本证明 0.6418 只适用于 w=0，局阻指数 .2 暂无出处；C-09 待补，C-10/C-11 撤回 | type=model-and-source-audit`

`TX-003 | 2026-11-02 | 输入分辨率复核 | U8-S 前 248 行复现；独立 Map I 算式给 3% 门槛余量 0.1232 pp、面积单项临界 0.1796%；区分设计功率与表5焓代理；Z20/X26 表号重核，C-12–C-17 更新 | type=model-and-source-audit`

`TX-004 | 2026-11-03 | 逐构件关联式及 KYLIN 原文复核 | U9-S 的 262 行日志复现；AR-P5/式(4)证通用 m≤.2 有反例，交点 Re≈11666；Y17 Table1/2 定名义环隙与单侧理论阻力，L15/Y17 核实验流量口径；C-18–C-25 更新 | type=model-and-source-audit`

分析采用 norman-paper-reading 技能｜作者：N同学｜小红书：N同学｜B站/抖音：耐心的N同学

Analysis performed using the norman-paper-reading skill | Author: N同学 | Xiaohongshu: N同学 | Bilibili/Douyin: 耐心的N同学
