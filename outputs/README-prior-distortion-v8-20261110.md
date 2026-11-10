# 先验失真 v8：WorkBuddy v4 复核与定功率条件界

先读 `v8_WorkBuddy复核与定功率紧界_20261110.md`。该报告区分了已证明的固定功率结论、仅有数值搜索支持的结论，以及尚未完成的连续功率紧界。

## 复算顺序

需要 Python 3.12、`numpy`、`scipy`、`gmpy2`。从本目录运行：

```bash
python mpfr_churchill_peak_v8_20261110.py
python mpfr_heater_length_sign_v8_20261110.py
python audit_v4_shared_sign_20261110.py
python mpfr_centered_bound_v8_20261110.py 3000 4 15
python mpfr_centered_bound_v8_20261110.py 4300 4 15
python mpfr_centered_bound_v8_20261110.py 6000 4 15
python mpfr_heater_ratio_v8_20261110.py
python transfer_v8_temperature_20261110.py
```

三个 `mpfr_centered_bound` 运行各约 2.5 分钟。`audit_v4_extrema_20261110.py` 是数值优化检查，不是包含证书。MPFR 证书以 `core_v2.py` 中已冻结的 binary64 常数为模型输入；原始文献参数的误差不在证书范围内。

## 文件用途

- `core_v2.py`：两侧前向模型与输入盒。
- `factored_interval_v7_20261109.py`、`mpfr_interval_v7_20261109.py`、`mpfr_derivative_v7_20261109.py`：区间残差、定向舍入与自动微分。
- `mpfr_centered_bound_v8_20261110.py`：同一参数子箱上的 P/M 根及流量比外包。
- `mpfr_heater_ratio_v8_20261110.py`、`transfer_v8_temperature_20261110.py`：加热段热账与体温升 FoM 外包。
- `workbuddy-v4-*`：用户上传的 v4 报告及三份日志，供逐数对照；v4 源码未包含在用户本次上传中。

**适用范围：** 当前较紧的失真界只覆盖 3、4.3、6 kW 三个功率切片。根的存在性和唯一性另由 v7 覆盖连续 3–6 kW。勿把定功率结果插值成连续功率保证。
