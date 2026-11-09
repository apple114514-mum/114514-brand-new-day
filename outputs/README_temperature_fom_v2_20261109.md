# v2 温度 FoM 补算与证书审查

先读 `temperature_fom_v2_review_20261109.md`；`temperature_fom_v2_20261109.png/.svg` 是论文候选结果图，CSV/JSON 保存全部数值。`source-v2/` 是用户本次上传的 WorkBuddy 材料。

复算：安装 `numpy scipy SALib matplotlib`，在解压目录运行 `python temperature_fom_v2_audit_20261109.py`，再运行 `python plot_temperature_fom_v2_20261109.py`。补算脚本使用同包中的 `forward_v1_original_20261109.py` 与 `forward_v1_table2_recheck_20261109.py`，不依赖未上传的 WorkBuddy `core_v2.py`。

温度 FoM 使用同一加热段流体进出口温升，名义值 3 kW 为 +10.3070%、6 kW 为 +7.8773%。区间端点是角点搜索结果，不是严格上界。WorkBuddy v2 的 `certify_v2.py` 有反向 K 区间、Taylor 余项缺失和浮点外舍入缺失三处问题；其区间数字只作探索性诊断。
