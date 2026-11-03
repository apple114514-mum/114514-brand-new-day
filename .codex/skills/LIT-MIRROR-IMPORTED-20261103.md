# lit-mirror 本地导入与修补（2026-11-03）

来源：用户上传 `lit-mirror_skillpack_2026-11-03.zip`，SHA-256 `8d3c8ce9a67bd6b5c4feb92d13c7fc385dc3f30a71d2de892d119435f4bf59de`；`testzip` 通过。仅导入包内新的 `lit-mirror/` 六个文件至 `.codex/skills/lit-mirror/`。包内 `origin-paper-workspace`、`zvex-model-sensitivity`、`sensitivity-analysis` 与 `norman-paper-reading` 副本未覆盖仓库已安装版本。此处是上传包本地安装，不表示两个客户端的技能市场互通。

本地适配：`mirror_check.py` 原版会把只含 `[[p1]]` 的伪文本与声称 `[[p999]]` 的断言判为通过。现增加证据页码是否确在文本、页码是否连续、PDF 与文本页数是否相同的检查；相同反例退出码从 0 改为 1。检查依赖 `pypdf`。脚本通过语法检查，三篇真实文献镜像（3 PDF、3 逐页文本、5 条断言）审计退出码 0，打包在 `outputs/literature-mirror-20261103.zip`。

适用边界：审计通过只说明**文件与页码结构**一致，不能证明断言语义被原文支持。重要图表仍应打开 PDF 核对。本云环境已能读、渲染 PDF，因此新技能原文“只给模型 TXT、不要给 PDF”的客户端假设不适用于本仓库。L1/L2/L3/L4 是来源类型，不应按字符串“grade ≥ L2”筛选。
