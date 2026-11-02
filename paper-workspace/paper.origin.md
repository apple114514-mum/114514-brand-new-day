# 缩比失真研究状态包

## meta

- 创建：2026-11-02
- 题目（暂定）：铅铋自然循环缩比失真的设计阶段条件界
- 目标期刊：未定
- 最近事务：TX-002
- 参数原始表：[outputs/parameter-provenance-20261102.md](../outputs/parameter-provenance-20261102.md)

## source

| ID | 文件 | 已核范围 | SHA-256 |
|---|---|---|---|
| Z20 | [赵鹏程等 2020 PDF](../outputs/zhao-2020-original-20261102.pdf) | PDF 1、3–6 页，尤其表 2–5 与式(13) | `8e9a3c20d1e6a876ad357e0907f41c6e51fbdd2fdc0b6add06f4ec027337e951` |
| X26 | [Xu FR26-170 PDF](../outputs/xu-fr26-170-original-20261102.pdf) | PDF 2–5 页，尤其表 1–2 与式(7)、(15)–(18) | `713645a3c621ae097b175bc716eb4a0f9bf7d78c9f8070161f4d2b6e69d9a3c5` |
| I21 | [IAEA LFR-21 PDF](../outputs/lfr-21-kylin-ii-nc-original-20261102.pdf) | PDF 1–3 页，设施概况与参数表 | `4f75474bffb9c1650513909ef78043a352016e3e27a6650b8c9d6a0991043e25` |
| L15 | Li 等 2015 | 全文未取得；仅 X26 与 I21 的参考文献条目 | 未取得 |
| Y17 | Yue 等 2017 | 全文未取得；仅 I21 的参考文献条目 | 未取得 |

## objects

### Q 研究问题

- Q-01：在明确原型—台架设计映射、模型闭合和有来源参数域后，能否在建台架前给出 FoM 失真的条件包含界？
- Q-02：哪些几何、阻力和物性输入已有一手出处，哪些仍只能做情景？

### C 论点与 E 证据

见 [claim-matrix.md](claim-matrix.md)。本轮只建立输入事实与缺口，不凭空生成物理 `δ` 域。

## relations

`C-01 supported_by E-01`；`C-02 supported_by E-02`；`C-03 supported_by E-03`；`C-04 supported_by E-04`；`C-05 supported_by E-05`；`C-06 supported_by E-06`；`C-07 supported_by E-07`。`C-08` 待补。

`C-09` 是 U-P1/A1–A2 的待验证假设；`C-10` 被独立算式核查反例推翻；`C-11` 被 Z20-P5/表3 与 X26-P4/表1 的来源核读否定。详见 [参数闭合 v1 复核](../outputs/parameter-closure-v1-review-20261102.md)。

## constraints

- 表中“直径”必须保留原文修饰语；不能把未说明的几何直径改写为流通内径。
- 表中数值须标为设计输入、CFD 输出、设施档案或实测；当前未见 Li/Yue 全文，不引用其表内值。
- Xu 式(9) 的 `δ` 是壁厚，与本研究 `k_M/k_P−1` 的局阻失配参数同字母不同义。
- 参数域和 GSA 分布不能由技能模板、常见公差或 CFD 失真百分点臆定。
- 局阻的 Re 指数上界须有逐构件适用证据；`Re_R≥0.6418` 仅是 Zhao 声明模型 `w=0` 时的条件门槛，不得作为所有 `w` 或 KYLIN 案例的实物保证。

## metrics

- 当前 11 条论点：7 条由已读文献定位或明确检索范围支撑，2 条待补（物性有效域、局阻指数），2 条已撤回（通用 Re 门槛、误归来源）。
- 目标期刊格式门禁：未启动；当前不判投稿合格。

## transactions

`TX-001 | 2026-11-02 | 原文取象 | Z20/X26/I21 页表核读，建立参数表与 claim-matrix；Li/Yue 全文缺席标空 | type=source-audit`

`TX-002 | 2026-11-02 | 参数闭合复核 | U-P1/U-S 的 131 行日志复现；Z20/X26 原文重核；独立脚本证明 0.6418 只适用于 w=0，局阻指数 .2 暂无出处；C-09 待补，C-10/C-11 撤回 | type=model-and-source-audit`

分析采用 norman-paper-reading 技能｜作者：N同学｜小红书：N同学｜B站/抖音：耐心的N同学

Analysis performed using the norman-paper-reading skill | Author: N同学 | Xiaohongshu: N同学 | Bilibili/Douyin: 耐心的N同学
