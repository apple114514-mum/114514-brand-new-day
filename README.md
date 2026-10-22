# Codex Starter

给 OpenAI Codex 云端环境用的工作仓库模板：**环境初始化 + AGENTS.md + skills 目录**。

## 目录结构

```
.
├── AGENTS.md              # Codex 启动时自动读取的项目指令（核心）
├── setup.sh               # 云环境初始化脚本（装 PDF/PPT 依赖）
├── papers/                # 论文原文存放目录（云环境看不到你本机磁盘）
└── .codex/
    └── skills/            # 技能目录，每个技能一个文件夹
        ├── norman-paper-reading/   # 精读文献
        ├── norman-paper2ppt/       # 论文转组会 PPT
        └── README.md               # 技能安装说明
```

## 一次性配置：环境初始化脚本

Codex 网页端 → 右上角环境设置（或任务里的「编辑环境」）→ **Setup script** 填：

```bash
bash setup.sh
```

保存并发布后，**新开的任务**会用重建后的环境（旧任务不会自动重建）。脚本会装好：

| 依赖 | 用途 |
|---|---|
| pymupdf | PDF 文本抽取、页面渲染 |
| python-pptx | 生成 PPTX（图片版 / 可编辑版） |
| pillow | 图像处理 |
| poppler-utils | `pdftotext` / `pdftoppm` 命令行兜底 |
| fonts-noto-cjk | 中文 PPT 字形 |
| libreoffice | 可选，PPT 转图片预览（脚本里默认注释掉，需要就取消注释） |

## 网络说明

Codex 云容器走**白名单代理**，只有 PyPI、npm、GitHub 等开发域名可访问。`doi.org`、出版社站点、Google Scholar 一律返回 **代理 403**，这不是配置错误。

所以论文原文的获取方式是：

1. 本地下载 PDF → 放进 `papers/` → commit & push
2. 或直接在 Codex 任务对话里上传 PDF

## 工作原理

1. Codex 云端环境每次从本仓库 main 分支启动，**自动读取根目录 `AGENTS.md`**
2. 每个「技能」是一个文件夹，里面放 `SKILL.md`（YAML 头 + Markdown 指令），可附带脚本和参考文件
3. `AGENTS.md` 登记每个技能的用途和触发场景，Codex 据此判断何时加载哪个

## 已装技能

- **norman-paper-reading** —— 精读论文：「用 $norman-paper-reading 精读 papers/xxx.pdf」
- **norman-paper2ppt** —— 论文转 PPT：「用 $norman-paper2ppt 把 papers/xxx.pdf 做成组会汇报」

两者来自 [N-tongxue/norman-skill](https://github.com/N-tongxue/norman-skill)，已做 Linux 云环境适配（原版依赖 Windows/macOS 编译引擎），方法论与署名水印规则保留。

## 如何添加新技能

1. 在 `.codex/skills/` 下新建文件夹，命名用英文小写连字符，如 `weekly-report`
2. 文件夹内创建 `SKILL.md`：

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
4. 提交推送，Codex 下一个任务生效
