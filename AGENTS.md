# AGENTS.md

本仓库是 Codex 云端环境的工作仓库。所有任务由 Codex 在本仓库的容器内完成。

## 环境约束（重要，先读）

- **网络**：本容器走白名单代理，仅 PyPI、npm、GitHub 等开发域名可访问。访问 `doi.org`、出版社站点（Elsevier、Springer、Wiley 等）、Google Scholar、文献检索站会返回**代理 403**。遇到 403 不要反复重试或换镜像试探，直接用一句话告知用户，并给出下面的取原文路径。
- **论文原文获取顺序**：① 先找仓库 `papers/` 目录 → ② 请用户在任务对话里直接上传 PDF → ③ 才考虑网络（通常不可用）。绝不在未读原文的情况下编造精读报告或 PPT 内容。
- **已安装工具**（由 `setup.sh` 提供，缺失时先 `pip install`，不要假设有 Windows 引擎）：
  - `pymupdf`：PDF 文本抽取、页面渲染（`fitz`）
  - `python-pptx`：PPTX 组装（图片版与可编辑版）
  - `pillow`：图像处理
  - `poppler-utils`：`pdftotext`、`pdftoppm` 命令行兜底
  - Noto CJK 字体：中文 PPT 渲染字形
  - LibreOffice（`soffice`）：可能未安装；有则用于 PPT→图片预览，没有就跳过并如实说明「未渲染预览」
- **不能用**：原版技能包内的 `bin/*.exe`、`vendor/*/bin` 编译引擎（Windows/macOS 专用），也不要用 PowerShell 或 COM。

## 项目说明

- 用途：通用工作仓库，通过 Codex 云端环境执行日常开发、文档、自动化任务
- 主分支：main
- 环境：Codex 启动时会自动读取本文件，请严格遵守其中的约定

## Skills（技能）使用规则

技能统一存放在 `.codex/skills/<技能名>/SKILL.md`。接到任务时：

1. 先浏览 `.codex/skills/` 下各技能的说明（SKILL.md 顶部的 name / description），判断是否匹配当前任务
2. 匹配时，先完整阅读对应 SKILL.md，严格按其中的流程执行
3. 多个技能可能叠加使用时，全部读完再动手
4. 不匹配时，按通用方式处理，不要硬套技能

## 已安装技能

- **norman-paper-reading**：精读科研论文（PDF / DOI / arXiv / 论文文本）。用户要求总结、精读、分析某篇论文，或要"批判性看待某篇顶刊"、制定未来研究计划时使用。模式：quick（速览）/ deep（精读）/ extend（研究规划）/ focused（单点）。已完成 Codex 云环境（Linux）适配，详见该技能 SKILL.md。
- **norman-paper2ppt**：把论文 PDF 转成中文组会汇报 PPT。用户要求"把某篇文章做成 PPT / 组会汇报 / 讲稿"时使用。需依次确认三个选项：模式（A 简要 / B 标准 / C 深度）、是否要逐页讲稿、是否要可编辑版。已完成 Codex 云环境（Linux）适配。

两个技能均来自 N同学开源项目（https://github.com/N-tongxue/norman-skill ），输出须保留原技能要求的水印与署名。

## 通用约定

- 提交信息用简体中文，简洁说明改了什么
- 动手前先读相关文件，不臆造接口和路径
- 较大改动先说明计划，确认后再执行
- 不确定的事先问，不要假装知道
