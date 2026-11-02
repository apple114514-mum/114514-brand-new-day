# WorkBuddy 技能本地导入记录（2026-11-02）

来源：用户上传的 `skills_added_2026-11-02.zip`；SHA-256：`f4b34a57b3056b76ac92ae34bdef3c441c347c00c46bca161c2b6abf1c588260`。此处采用压缩包本地安装，**没有通过 Codex 技能市场安装**。Codex 市场当前未配置可访问目录，WorkBuddy 的 `skillId` 只用于版本核对。

| 项目级目录 | 版本 | 原 WorkBuddy `skillId` | 本项目用途 |
|---|---|---|---|
| `.codex/skills/zvex-model-sensitivity/` | 1.0.2 | `skill_2107645256676827136` | GSA 选型、Morris/Sobol 等分析流程；运行前需明确输入域与分布 |
| `.codex/skills/origin-paper-workspace/` | 1.0.0 | `skill_2104450706215473152` | 论文论点—证据矩阵及出处审查 |
| `.codex/skills/sensitivity-analysis/` | 1.0.0 | `skill_2106758297841381376` | 财务情景分析备用；不承担本项目的 GSA |

安装检查：压缩包 `testzip` 无损坏；路径均位于上述三个目录，无绝对路径或目录穿越；`SKILL.md` 的 `name` 与目录匹配；三个 `_skillhub_meta.json` 的版本和 `skillId` 与用户给出的值一致；包内 Python 脚本通过语法解析。原始元数据已保留，后续可按 ID 核对市场更新。仓库的 `AGENTS.md` 已登记，**新会话重新加载技能目录后生效**。

配套依赖：此环境已有 `numpy/scipy/pandas`。初次按压缩包 README 指定的华为云镜像获取 `SALib` 时，云代理返回 `403 Forbidden`。用户随后明确授权直连 PyPI；已在独立环境 `/workspace/.venv-gsa` 安装 `SALib==1.6.0`、`multiprocess==0.70.19`、`dill==0.4.1`，并在 `setup.sh` 中记录重建步骤。使用 `/workspace/.venv-gsa/bin/python` 运行 GSA；系统默认 `python` 不保证能导入 SALib。最小 Morris 冒烟测试用 3 参数、32 条轨迹生成 128 行样本，恢复预设的 `2.0/0.5/0.0` 重要性顺序；`pip check` 通过。`SALib` 不是这三个技能目录的一部分。
