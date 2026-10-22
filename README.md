# Codex Starter

给 OpenAI Codex 云端环境用的仓库初始化模板：**AGENTS.md + skills 目录**。

## 目录结构

```
.
├── AGENTS.md              # Codex 启动时自动读取的项目指令（核心）
└── .codex/
    └── skills/            # 技能目录，每个技能一个文件夹
        └── README.md      # 技能安装说明（可删除）
```

## 工作原理

1. Codex 云端环境每次从本仓库的 main 分支启动，**自动读取根目录的 `AGENTS.md`**
2. 每个「技能」是一个文件夹，里面放一个 `SKILL.md`（YAML 头 + Markdown 指令），可附带脚本和参考文件
3. `AGENTS.md` 里登记了每个技能的用途和触发场景，Codex 据此判断何时加载哪个技能

## 如何添加新技能

1. 在 `.codex/skills/` 下新建文件夹，命名用英文小写连字符，如 `weekly-report`
2. 文件夹内创建 `SKILL.md`，格式如下：

```markdown
---
name: weekly-report
description: 生成周报。当用户要求写周报、汇总本周工作时使用。
---

# 周报生成流程

1. 收集本周完成的事项……
2. 按「进展 / 数据 / 下周计划」三段输出……
3. 输出为 Markdown，保存到 reports/ 目录
```

3. 在 `AGENTS.md` 的「已安装技能」一节登记一行
4. 提交并推送到 main，Codex 下一个任务即可生效
