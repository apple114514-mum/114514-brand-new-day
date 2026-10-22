# papers/ —— 论文原文目录

Codex 云容器的网络是白名单代理，**访问 doi.org、出版社、文献检索站会返回 403**。所以论文原文走这个目录传进去。

## 用法

1. 把 PDF 放进本目录，命名建议 `第一作者-年份-短标题.pdf`，例如 `zhang-2025-nucengdes-114409.pdf`
2. 提交并推送：`git add . && git commit -m "add paper" && git push`
3. 在 Codex 任务里直接说：`读 papers/xxx.pdf，用 $norman-paper-reading 精读` 或 `用 $norman-paper2ppt 做成组会 PPT`

## 为什么不用链接

云环境只能访问白名单域名（PyPI、npm、GitHub 等），学术站点不在其中。即使能连通，多数顶刊也需要机构订阅。把 PDF 放进仓库是最稳的路径。

## 注意

- 版权允许的前提下再提交论文 PDF；私密论文可用私有仓库。
- 单个文件建议 < 50MB，仓库不宜长期堆积大文件。
