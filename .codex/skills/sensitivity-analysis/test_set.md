---
skill: 敏感性分析
dept: 财务部
generated_by: G5-trigger-test-generator
trigger_sources: [metadata.triggers]
spec: G5 / §7.1 触发工程 / §12.1 评测双门制（确定性 lint 门）
---

# 敏感性分析 · 触发测试集（G5）

## 应触发（Positive · 需召回）

- 帮我做敏感性分析 （触发词：敏感性分析）
- 帮我做敏感度分析 （触发词：敏感度分析）
- 帮我做情景分析 （触发词：情景分析）
- 帮我做单因素变动测算 （触发词：单因素变动测算）
- 这个敏感性分析该怎么弄 （语义匹配：敏感性分析）

## 不应触发（Negative · near-miss 防误触发）

- 帮我看看这笔销售订单的毛利 （归属：销售部 - 应转product-margin）
- 整理本周的费用报销单据 （归属：行政部）
- 起草一份代理商的返点政策 （归属：销售部）
- 给客户发一封催款函 （归属：应转collection-followup-letter）
- 帮我做一份招聘预算 （归属：行政部 - 应转budget-compilation）
- 报税的事直接找代理记账公司做吧 （归属：外部服务 - 非本技能）

## 专属负例（技能边界 · 来自 SKILL.md 相邻技能边界 / manifest 消歧说明）

- 这个项目要不要投 （本技能不覆盖，应转 `investment-feasibility`）
- 重估全年预测 （本技能不覆盖，应转 `rolling-forecast`）
- 已发生差异的归因 （本技能不覆盖，应转 `budget-variance-analysis`）
