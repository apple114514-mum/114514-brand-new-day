# AGENTS.md

本仓库是 Codex 云端环境的工作仓库。所有任务由 Codex 在本仓库的容器内完成。

## 交付物输出约定（重要）

用户在 Codex 网页端**无法直接打开容器内的文件路径**，只能靠仓库传递。

- 所有最终交付物（PPTX、PDF、图片、CSV）生成后，**复制到 `outputs/` 目录并 commit push**，然后在回复里给出仓库内的相对路径
- 文件名带版本或日期：`paper-editable-20261022.pptx`
- 单文件控制在 **90 MB 以内**（GitHub 上限 100 MB）；超过 **40 MB** 的 PPT/PDF 网页预览会失败，交付时主动说明「请用 git pull 获取」
- 超过 90 MB 时先压缩：PPTX 图片重采样到 1280×720/质量 85，或 zip 分包
- 不要把 `generated/`、`previews/`、`source-pages/` 等中间产物提交进仓库
- 交付话术示例：「已输出 `outputs/paper-editable-20261022.pptx`（62 MB），请在本地执行 git pull 获取」

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
- **技能运行平台**：本仓库的 `norman-fig2ppt`、`norman-paper2ppt`、`norman-research-idea` 和 `norman-humanize` 只安装了上游对应版本的 Linux x64 可执行文件；按各自 `SKILL.md` 调用。`norman-paper-reading` 上游 v1.4.0 没有 Linux 可执行文件，继续使用本仓库的 Python 适配版。不要在云端运行 Windows/macOS 可执行文件、PowerShell 或 COM。

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

- **norman-paper-reading v1.4.0**：精读科研论文（PDF / DOI / arXiv / 论文文本），包括证据审查与研究规划；使用现有 Linux/Python 适配版。
- **norman-paper2ppt v1.1.0**：把论文 PDF 转成中文组会汇报 PPT；使用上游 Linux x64 版，按技能要求依次确认汇报模式、讲稿和可编辑版。
- **norman-fig2ppt v1.3.1**：把论文图片、流程图等重建为可编辑 PowerPoint 对象；使用上游 Linux x64 版。
- **norman-research-idea v2.0.0**：从研究方向或论文出发，核查文献、比较创新点并设计可执行研究方案；使用上游 Linux x64 版。
- **norman-humanize v1.3.2**：按用户选择的文体、修改程度和范围润色中英文文字或 Word 文档；使用上游 Linux x64 版。
- **research-plot**：科研数据绘图与出图规范。要画图、出图、统一图表风格、出论文级插图（温度/流量/压力曲线、实验 vs 计算对比）时使用。默认论文插图规格：单栏 8.5 cm、600 DPI、矢量优先、单位齐全。
- **fluent-post**：Fluent/CFD 结果后处理。给了 monitor `.out`、Reports 积分结果、`.xy`/`.csv` 数据，要判断收敛、提特征量（ΔT、Q、Re、Nu、f）、出工况对比表时使用。**未收敛不出结论**。
- **paper-archive**：文献归档与整理。要归档 PDF、按规范重命名、查重、生成 `papers/INDEX.md` 清单时使用。
- **thesis-writing**：中文学术写作与排版。写开题报告、学位论文章节、期刊投稿、研究进展报告时使用；含结构模板、图表公式编号、GB/T 7714 引用规范。
- **weekly-report**：生成周报与研究进展。用户说"写周报""汇报本周工作""准备组会进展"时使用。结构：本周完成 / 遇到的问题 / 下周计划 / 需要支持。

上述五个 Norman 技能来自 N同学项目（https://github.com/N-tongxue/norman-skill ），版本与来源提交见 `.codex/skills/NORMAN-UPSTREAM.md`，输出须遵守各技能的署名要求；其余五个为本仓库自建，按本组习惯持续修订。

## 通用约定

- 提交信息用简体中文，简洁说明改了什么
- 动手前先读相关文件，不臆造接口和路径
- 较大改动先说明计划，确认后再执行
- 不确定的事先问，不要假装知道
