# 论文对象模型（Benxiang Origin IR for Academic Writing）

本象协议在学术写作场景的落地：这项研究这座"世界"被编译成六类对象。AI 不直接重造文档，只提交对状态包的语义修改。

## 对象总览

| 前缀 | 对象 | 含义 | 来源 |
|---|---|---|---|
| `Q` | ResearchQuestion | 研究问题（这篇到底解决什么） | 取象报告 |
| `L` | LiteratureClaim | 文献主张（别人说了什么） | 取象报告 |
| `C` | Claim | 我方论点（立什么论） | 本象建模 |
| `E` | Evidence | 证据（实验/数据/推导/引文/案例） | 学籍资产 / 本象建模 |
| `K` | KillLine | 学术红线（会不会死） | 取象报告 |
| `T` | TimeNode | 时间节点 | 取象报告 |

> 论证关系由 `C supported_by E` 表达，不单独建 A 对象 —— 论文的核心资产是"论点被什么支撑"，不是"对要求的应答"。

## 字段规范

### Q 研究问题对象
```
id: Q-01
question: 该机制在低资源场景下是否仍然稳定
type: 主问题 | 子问题
provenance: [L04-P12/Limitation]
status: 已定 | 待定 | 已废弃
```

### L 文献主张对象
```
id: L-01
ref_key: authorA2023
claim_raw: "…（原文摘录）"
provenance: [L01-P7/表2]
evidence_type: 实验 | 综述 | 案例 | 推论 | 仿真
relation: 支撑 | 对立 | 背景 | 方法借鉴
limitation: 单中心样本
```

### C 论点对象
```
id: C-01
claim: 该机制在低资源场景下稳定性显著下降
type: 事实性 | 方法性 | 因果性 | 价值性
strength: 强 | 中 | 弱        # 依现有证据如实标注
chapter: 4.2
status: 待写 | 已写 | 待补充 | 已核
provenance: [L04-P12]
```

### E 证据对象
```
id: E-01
content: 实验B组 n=240，均值差 3.2，p<0.01
type: 自有实验 | 公开数据集 | 引文 | 推导 | 调研
source: DS-02（assets/datasets.md）
reproducible: 是 | 否        # 是否有脚本与随机种子
availability: 已有 | 待补 | 不可得
```

### K 学术红线对象
```
id: K-01
content: 一稿多投一经发现直接退稿
provenance: [J01-P2/1.4]
level: A        # A=退稿/不端级 B=规范扣分 C=优化
block_condition: 同稿另投或实质重复发表
check_method: 核对已投期刊与在审稿状态
```

### T 时间节点对象
```
id: T-01
event: 截稿
time: 2026-xx-xx 23:59
provenance: [J01-P1]
owner: 用户
alert: 提前 14 天提醒
```

## 关系

| 关系 | 含义 |
|---|---|
| `C supported_by E` | 论点由某证据支撑 |
| `C cites L` | 论点引用/对话某文献主张 |
| `C contrasts L` | 论点与某文献主张对立 |
| `E derived_from 数据集ID` | 证据来自哪个数据集或实验 |
| `K blocks 整篇论文` | 红线对整篇的拦截 |
| `T precedes T` | 时间先后依赖 |
| `资产 supports C` | 资产支撑某论点 |

## 约束（constraints）

从投稿须知/学校规范抽取的硬性限制，独立于对象存在：
- 字数/页数上限、章节结构与层级、摘要类型与字数、关键词数量
- 引用格式（APA / MLA / GB/T 7714 / IEEE …）与参考文献条目数下限
- 图表数量上限、分辨率与格式、图表标题规范
- 必备声明：利益冲突、数据可用性、伦理审批、基金标注、作者贡献

## 事务日志（transactions）

每次对状态包的修改留一条记录，确保"每个字段都能回答凭什么是这个值"：

```
TX-001 | 2026-09-22 | 项立论 | 依据 [L04-P12] 新建 C-01 | type=因果性 strength=中
TX-002 | 2026-09-22 | 任积学 | C-01 关联证据 E-01(DS-02) | 强度 92
TX-003 | 2026-09-23 | 严必核 | C-07 判为断链，退回影核 | 缺跨场景验证数据
```

## 指标（metrics）

状态包必须实时给出：
- 论点总数 / 有可追溯证据的论点数 / **论点支撑率**
- **引用覆盖率** = 已挂文献的论点 / 全部论点
- A 类红线数 / B 类规范项数
- 缺证据论点数
- 最需补强论点 Top5（论点重要性 × 证据缺口）

## 状态包骨架

```markdown
# 论文状态包 paper.origin.md

## meta
题目（暂定）/ 目标期刊或学校 / 作者 / 创建时间 / 最近事务

## source
（取象报告摘要与坐标体系）

## objects
### Q 研究问题 / ### L 文献主张 / ### C 论点 / ### E 证据 / ### K 红线 / ### T 节点

## relations
C-01 supported_by E-01 …

## constraints
字数、结构、引用格式、声明要求 …

## metrics
支撑率、引用覆盖率、红线数、缺口数、Top5 …

## transactions
TX-001 …
```
