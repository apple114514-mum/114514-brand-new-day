# v19 阀门可行域与曲线极值复核材料包

请先读 `design-v19-independent-review-20261108.md`，再将整包交给 WorkBuddy。报告中区分了可复算的设计点/角点、v19 GSA 的实现错误，以及尚未证明的连续上界。

## 复算

```bash
python design-v19-independent-audit-20261108.py
```

独立审计只用 Python 标准库。它调用包内的上一轮独立标量实现 `design-v18-independent-audit-20261108.py`；不执行上传的 v19 脚本。结果已保存为 `design-v19-independent-audit-log-20261108.txt`。

## 包内

- `design-v19-independent-review-20261108.md`：本轮复核与设计规格候选。
- `design-v19-independent-audit-20261108.py` / `design-v19-independent-audit-log-20261108.txt`：独立计算与输出。
- `design-v18-independent-audit-20261108.py`：供本轮独立计算复用的标量模型。
- `design-v19-upload-script-20261108.py` / `design-v19-upload-log-20261108.txt`：上传的原始脚本与日志。
- `design-v19-upload-points-20261108.csv`：上传的点值表。
- `design-v19-upload-report-20261108.html`：上传的 WorkBuddy 原报告。
- `parameter-provenance-v19-upload-20261108.md`：上传的参数溯源表（含 §17）。

原文件供追踪推导；引用本轮结论时以独立复核报告的条件和撤回项为准。
