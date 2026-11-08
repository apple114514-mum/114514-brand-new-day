# v18 缩比设计复核材料包

先读 `design-v18-independent-review-20261108.md`。它区分了可保留的 v18 数值、阶段Ⅰ A 支角点证明，以及阶段Ⅲ可行性/GSA/热路的待修正项。

## 复算

```bash
python design-v18-independent-audit-20261108.py
python design-v18-gsa-range-check-20261108.py
```

第一份独立脚本只用 Python 标准库；第二份范围复跑沿用上传 v18 模型，需要 `numpy`。两份脚本的输出已保存为同名前缀的 `...-log-20261108.txt`，可直接查看。

## 包内文件

- `design-v18-independent-review-20261108.md`：独立复核报告。
- `design-v18-independent-audit-20261108.py`：阶段Ⅰ、配平交互、负阀门阻力、可行角点和物性检查。
- `design-v18-independent-audit-log-20261108.txt`：独立审计运行结果。
- `design-v18-gsa-range-check-20261108.py`：把 Φ 声明宽度改为 ±1%，重算单点输出的探索性 ST。
- `design-v18-gsa-range-check-log-20261108.txt`：GSA 范围检查运行结果。
- `design-v18-upload-report-20261108.html`：上传的 WorkBuddy 原报告。
- `design-v18-upload-script-20261108.py`：上传的 WorkBuddy 原脚本。
- `design-v18-upload-log-20261108.txt`：上传的 WorkBuddy 原日志。
- `design-v18-upload-points-20261108.csv`：上传的点值表。
- `parameter-provenance-v18-upload-20261108.md`：上传的参数溯源表（含 §16）。

研究结论以独立复核报告中标明的条件和更正为准；包内原报告供核对历史推导。
