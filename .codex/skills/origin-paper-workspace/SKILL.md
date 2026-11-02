---
name: origin-paper-workspace
description: "论文工作区与本象对象模型。用于把文献与投稿要求编译成持久化的论文状态包（paper.origin.md）与论点—证据—文献矩阵（claim-matrix.md），并按学术规范红线库做确定性门禁校验。当任务涉及选题拆解、文献综述、论证建模、论文成稿、投稿前学术规范审查时使用。"
description_zh: "论文工作区与本象对象模型。用于把文献与投稿要求编译成持久化的论文状态包（paper.origin.md）与论点—证据—文献矩阵（claim-matrix.md），并按学术规范红线库做确定性门禁校验。当任务涉及选题拆解、文献综述、论证建模、论文成稿、投稿前学术规范审查时使用。"
description_en: "Origin Paper Workspace: compile literature and submission requirements into a persistent paper state package and claim-evidence-reference matrix, with deterministic gate checks against academic-integrity redlines."
display_name: "论文写作与学术规范审查"
display_name_en: "Academic Paper Writing and Review"
version: "1.0.0"
---

# 本源论文工作区（Origin Paper Workspace）

本 Skill 是「本源论文攻坚团」的执行底座。它把本象协议的三个核心机制搬进学术写作场景：

- **Origin IR 对象模型** — 文献与论点不进聊天记录，编译成 `paper.origin.md` 里的对象 + 关系 + 约束 + 来源
- **语义事务** — 每次有结论就提交一条事务留痕，谁在哪一步依据哪条坐标改的，可回放可追责
- **确定性门禁** — 成稿必须过 A/B/C 三级校验才允许投稿

## 工作区结构

```
paper-workspace/
├── paper.origin.md        论文状态包（唯一真相源，换会话从这儿恢复）
├── claim-matrix.md        论点—证据—文献矩阵（全流程中枢产物）
├── assets/                研究资产库（学籍）
│   ├── literature.md         文献条目与引用键
│   ├── datasets.md           数据集与实验记录
│   ├── figures.md            图表资产与可复现脚本
│   └── modules/              可复用写作模块
├── draft/                 分节成稿（sec-01.md, sec-02.md …）
└── audit/                 审查报告
```

## 铁律

1. **先建模后动笔** — 没有 `claim-matrix.md` 不许开始写正文。
2. **无坐标不成条** — 任何论点必须有 provenance（`文献ID-页码` 或 `文件前缀-页码/条款号`），没有坐标的视为无效。
3. **缺口显式化** — 追溯不到的主张一律标 `【待补充:具体内容】` 并进缺口清单，不允许用漂亮话填充。
4. **不编造学术事实** — 作者、年份、页码、DOI、样本量、统计值、实验参数，只从 `assets/` 或用户材料取。
5. **不做查重规避** — 只做规范性与引用完整性检查，不提供降重洗稿、同义替换、AI 痕迹清除。
6. **不下能不能发的结论** — 只呈现事实、空白、要求与支撑率，决策权归用户。

## 执行顺序

| 步骤 | 动作 | 产物 |
|---|---|---|
| 1 | 取象：文献与要求坐标级拆解 | `paper.origin.md` 的 `source` 区 |
| 2 | 本象：建 Q/L/C/E/K/T 对象与关系 | `paper.origin.md` + `claim-matrix.md` |
| 3 | 学籍：研究资产匹配与缺口暴露 | `assets/` + 缺口清单 |
| 4 | 影核：分节成稿 | `draft/sec-xx.md` |
| 5 | 门禁：六项校验 | `audit/审查报告.md` |

对象定义、字段规范见 `references/paper-object-model.md`；学术红线库见 `references/academic-integrity-redlines.md`；矩阵模板见 `templates/claim-matrix-template.md`。

## References

- `references/paper-object-model.md` — Q/L/C/E/K/T 六类对象与事务日志的字段规范
- `references/academic-integrity-redlines.md` — 常见学术不端红线与规范扣分项清单（A/B/C 分级）
- `templates/claim-matrix-template.md` — 论点—证据—文献矩阵模板
