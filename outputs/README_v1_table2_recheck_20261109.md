# 先验失真 v1：输入冻结与独立复算

先读 `inputs_v1_frozen_review_20261109.md`，再看对照图、CSV 和日志。`workbuddy_v1_recheck_handoff_20261109.md` 可直接转给 WorkBuddy。`source/` 内是用户上传的 v1 原件和 Yue 2017 Table 2 的原文页，供审计。

复算环境：Python 3，`numpy`、`scipy`、`matplotlib`、`SALib`。在解压目录运行 `python forward_v1_table2_recheck_20261109.py`；该脚本从同目录导入 `forward_v1_original_20261109.py`。运行会覆盖同目录的 corrected CSV、JSON 和日志。然后运行 `python plot_v1_table2_recheck_20261109.py` 重画 SVG/PNG。

主结论是**条件模型预测**：M 保持先前声明的 16 m / 3 m 设计，P 阻力改用 Yue Table 2 的五行 `K(Re)`。6 kW 名义质量通量偏差为 −7.1316%，十轴盒角点**搜索**到 −8.9087% 至 −5.1040%。连续域的严格极值证书和受控冷源的设备可行域尚未完成。报告不能把搜索端点称为已证明上界，也不能把 3 kW 称为 Yue 实测点。
