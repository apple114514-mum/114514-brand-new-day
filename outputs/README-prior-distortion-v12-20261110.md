# v12 交接：WorkBuddy v11 误差界反例与功率方向探针

先读 `v12_WorkBuddy误差界反例与功率中心化探针_20261110.md`。

## 要点

- WorkBuddy v11 的四核统一相对误差界 `288u/a²` 在其声明域内有实际反例：`mean_ratio_der` 的 Decimal 工作误差是该界的 **83.30 倍**。这一点不推翻其打印数值，也不影响独立 MPFR 全窗证书。
- 该核可按实际计算图逐式建立更合适的 `160u/a³` 保守界；其余三个核仍需逐式审计，不能继续引用统一 `288u/a²` 的证明。
- 在 6 kW 的一个共享参数子箱上，事后把浮升/阻力归一化，区间反而更宽。要收紧功率导数，须在温度递推内部符号化提出公共项。
- 连续 3–6 kW 的 `D_j<−3%` **仍未证明**。已有宽但严格的条件外包由独立 MPFR 计算给出，继续有效。

## 运行

需要 Python、`numpy`、`gmpy2`。解压后在包根目录运行：

```
python audit_v11_decimal_bound_v12_20261110.py
python probe_power_centering_v12_20261110.py
```

第二项依赖包内的冻结 `core_v2.py` 和 v7/v8/v9 MPFR 脚本。`workbuddy_received/` 保存本次用户上传的报告与修复件供对照；v12 脚本不导入其 `ivcore.py`。
