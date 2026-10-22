# 技能（Skills）目录说明

每个技能 = 一个文件夹 + 一个 `SKILL.md`。

## SKILL.md 格式

```markdown
---
name: skill-name
description: 一句话说明这个技能做什么、什么时候用。Codex 靠这段文字决定是否加载。
---

# 技能标题

## 何时使用
……

## 执行流程
1. ……
2. ……

## 注意事项
……
```

## 可附带的文件

- `scripts/` —— 可执行脚本（Python、Shell 等）
- `references/` —— 参考文档、模板、示例
- `assets/` —— 模板文件等静态资源

## 安装后必须做

在仓库根目录的 `AGENTS.md` 的「已安装技能」一节登记：

```
- weekly-report：生成周报。用户说"写周报/汇总工作"时使用。
```

然后提交推送，Codex 的下一次任务就会生效。
