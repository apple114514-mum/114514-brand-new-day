# WorkBuddy 交接包说明（2026-11-09）

## 目标

按用户重新确认的导师主线，对**铅基快堆自然循环**做设计阶段的**先验、条件性失真预测**：事先声明 P（原型）与 M（候选模型）各自的几何、热边界、阻力及物性；两侧分别前向求解；预先定义 FoM；再做摄动、GSA 和求界。缩放准则或 `K=22.8` 仅作讨论对照，**不能反向配平主线输入**。方法论文首版无须完整实物模型、厂家验收单或实验验证。

本包中的 `WORKBUDDY_PROMPT.md` 可直接复制给 WorkBuddy。**优先读 `docs/01_scope_v1.md` 和本说明**，再看论文与脚本。用户所提“老师截图”的原图未包含在本包；此处按用户刚确认的目标表述，不冒称核过截图原字句。

## 文件结构

| 路径 | 身份与用途 |
|---|---|
| `docs/01_scope_v1.md` | **本轮主协议**：最低物理输入域与三项缺口的条件处理。 |
| `docs/02_v29_literature_audit.md` + `assets/cho_table1.png` | 新增 Cho、吴磊文献及 v29 油侧说法的逐项复核。 |
| `docs/03_v28_temperature_audit.md` | 温度受控边界的早期复核；已被 v29 部分更新。 |
| `docs/04_v24_independent_review.md` | 旧 16 m + 孔板方案数值审计；其中“必须去孔板”依赖旧配平目标，**不进入新主线**。 |
| `docs/05_component_formula_review.md` | NEA 构件式与适用域核对。 |
| `docs/06_three_gap_sources.md` | 三项问题的原文导航；其中“尚须完整油侧”的旧措辞以 `01_scope_v1.md` 为准。 |
| `docs/07_claim_matrix_snapshot.md` | 旧结论及更正的索引，不是当前输入表。 |
| `docs/08_v29_workbuddy_report.md` | WorkBuddy v29 原稿，供复算；其中“`h_o` 是测量”“只有两条路线”“8.7% 是油侧误差”等已在 `02` 更正。 |
| `scripts/` | 旧脚本和日志，只用于重现实例数；**本包不包含新的双侧 GSA 代码**。运行会生成本地日志。 |
| `papers/` | 用户已提供的 NEA、Yue、Li、Xu、Cho、吴磊和弯头实验原文。 |

## 复算基线（Python 3）

在解压目录中运行：

```bash
python3 scripts/fluid_component_prior_domain.py
python3 scripts/design_v24_historical.py
python3 scripts/probe_v29_oil_historical.py
```

这三条只验证各轮**原脚本在其原声明下**的数值，不能自动得到“新主线”的先验失真、GSA 或全域上界。`design_v24_historical.py` 在当前工作目录写 `design_v24_log.txt`；`probe_v29_oil_historical.py` 在脚本同目录写日志。建议先复制解压包到可写的独立工作目录再运行。

## 必须维持的边界

- 原文给出的几何、实验、CFD、理论表、拟合和我们声明的设计参数分别标身份；Cho 的 HELIOS 系数不能搬给本装置，吴磊 2016 不是 LBE 构件实验。
- P 与 M 的热量、阻力和物性分别前向算；不为了对齐文献流量、目标 `K` 或漂亮的 `D` 回填输入。
- 冷腿温度可以是**预先声明的受控热边界**。v29 的 0.50 kg/s 混温油路只作实现可能性的**条件示例**；不要求把整台油冷机纳入首版主模型。
- 固定一个 FoM 后再计算。`(K_M/K_P)^(-1/3)-1` 不是通用失真公式，除非其他几何和热量因子确实消去。
- 摄动解释局部机制，GSA 给指定域/分布下排序；样本最大值不是确定性上界，求界需要另行说明方法。
- 本包中的**设计域协议已经可用**；要得到首次数值论文结果，下一步是冻结一张 P/M 数值输入表并运行，而不是继续等更多实物文献。

## 文件校验

压缩包根目录的 `SHA256SUMS.txt` 给出各文件 SHA-256。解压后可运行 `sha256sum -c SHA256SUMS.txt`。核对后从 `WORKBUDDY_PROMPT.md` 开始执行新任务。
