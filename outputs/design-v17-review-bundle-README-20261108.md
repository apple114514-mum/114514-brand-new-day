# v17 缩比设计复核材料包

交给 WorkBuddy 时，请先读 `design-v17-independent-review-20261108.md`，再运行：

```bash
python design-v17-independent-audit-20261108.py
```

独立复算会生成 `design-v17-independent-audit-20261108.csv`。包内同时保留上传的 v17 报告、脚本、日志和参数溯源表，便于对照。上传文件中的旧结论以独立复核报告中的更正为准。

## 文件

- `design-v17-independent-review-20261108.md`：重点结论、证据边界与下一步。
- `design-v17-independent-audit-20261108.py`：纯标准库独立复算。
- `design-v17-independent-audit-20261108.csv`：五个工况的代入与联立结果。
- `design-v17-upload-report-20261108.html`：WorkBuddy 原报告。
- `design-v17-upload-script-20261108.py`：WorkBuddy 原脚本。
- `design-v17-upload-log-20261108.txt`：WorkBuddy 原运行日志。
- `parameter-provenance-v17-upload-20261108.md`：WorkBuddy 参数溯源表（含 §15）。
