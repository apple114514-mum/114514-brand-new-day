# Norman 技能来源与云端安装

来源：`https://github.com/N-tongxue/norman-skill.git`，默认分支 `main`，核对提交 `1529ae4f2bcc7db2159710ed40d0e174c67a943b`（2026-10-31）。仅安装这个提交列出的五个现行技能；没有复制旧版目录或其他平台的程序。

| 技能 | 版本 | 云端运行方式 | Linux x64 程序 SHA-256 |
|---|---:|---|---|
| norman-fig2ppt | 1.3.1 | 上游 Linux x64 程序 | `af41db23f6307c6d27d91c01f8ea59b990a58beb38c2974f30e531cd89f2159f` |
| norman-paper-reading | 1.4.0 | 本仓库同版本 Python 适配；上游未提供 Linux 程序 | 不适用 |
| norman-research-idea | 2.0.0 | 上游 Linux x64 程序 | `3e2ec86872c9378314786142607fa344426b97fbee44a66c02324bed5232194c` |
| norman-paper2ppt | 1.1.0 | 上游 Linux x64 程序 | `48f54a8e2c4b70bcb92f91f4f7eccbb5e02aea0dced70206a19b15c196d4db29` |
| norman-humanize | 1.3.2 | 上游 Linux x64 程序 | `ed72311a25056f60ef0b8f8e23c70133b198b858f37ee890e786c30c633ddce0` |

每个上游 Linux 技能目录包含对应 `SKILL.md`、`README.md` 和 `*-linux-x64` 程序。完整工作流与参考资料由该程序的 `guide`、`list` 和 `read` 命令提供。Windows Workbuddy 安装与这个云端目录独立。

更新时先核对上游默认分支、版本和平台支持，再按程序实际运行结果更新本表。不要用上游 Windows/macOS 文件替换 `norman-paper-reading` 的 Linux 适配版。
