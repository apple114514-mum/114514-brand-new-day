# 自然循环缩比研究：2026-11-03 原文与逐构件复核交接

这份 Markdown 是给 Workbuddy 的**当前下载入口**。以本轮原文核读与[复核报告](component-re-v2-review-20261103.md)为准；此前文件保留演变记录，不应直接引用作废的来源归属或设计保证。以下 GitHub 链接在本文件单独下载后仍可使用；本地仓库执行 `git pull`。

## 先下载

| 文件 | 链接 | 内容 |
|---|---|---|
| **本轮复核** | [PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-review-20261103.pdf) · [Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-review-20261103.md) | 一手原文坐标、逐构件指数反例、KYLIN 名义环隙与理论阻力、有效结论和限制 |
| **复算** | [独立脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-independent-audit-20261103.py) · [Yue Table 2 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-table2-resistance-20261103.csv) · [证据矩阵](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/paper-workspace/claim-matrix.md) | `m=.2` 交点、反例、名义流道、理论摩擦份额与来源门禁 |
| **一手文献** | [Li 2015 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/li-2015-kylin-original-20261103.pdf) · [Yue 2017 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-kylin-original-20261103.pdf) · [Al‑Tameemi–Ricco 原稿](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/altameemi-ricco-mitre-original-20261103.pdf) | 全文已取得；弯头上传稿未核正式 DOI/卷页 |
| **原图** | [Yue Table 1](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-table1-original-20261103.png) · [Yue Table 2](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/yue-2017-table2-original-20261103.png) · [Li Fig. 7](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/li-2015-fig7-original-20261103.png) · [弯头 Fig. 6](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/mitre-elbow-fig6-original-20261103.png) | 从所附 PDF 原页裁取并目视核验，保留表头、坐标和图注 |
| **Workbuddy 本轮原件** | [HTML 报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-upload-report-20261103.html) · [脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-upload-script-20261103.py) · [262 行日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-upload-log-20261103.txt) · [参数表](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/component-re-v2-upload-table-20261103.md) | 上传计算可复现；解释以本轮复核修订 |
| **前轮交接** | [2026-11-02 总索引](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/research-handoff-20261102.md) · [第八轮输入分辨率复核](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/provenance-v8-review-20261102.md) | 原有计算、撤回记录、Zhao 原文和方法背景 |

## 本轮能守住的结论

1. **几何落地：** Yue PDF 第 2 页 Table 1 与正文给 KYLIN 主管内径 26 mm、加热段内径 54 mm、**一根同心棒直径 22 mm**。名义环隙面积为 `1.91009×10^-3 m²`，水力直径 `32 mm`；支撑件等未列，不能等同验收净面积。54/22 mm 不能再归给 Xu Table 1。
2. **单侧阻力有模型锚：** Yue PDF 第 4 页 Table 2 属**理论计算**，不是实测；按其式(9)，`K_pipe−1` 为管段沿程摩擦，在表内五点占 `K_total` 的 `73.25–73.97%`。此前四段模型反标定的 `48.67%` 与之不一致，应查摩擦关联式、管长和局阻闭合，不挑一个当真值。
3. **通用指数 A2 有反例：** Al‑Tameemi–Ricco 式(4)仅适用于水/空气、圆管 90° 锐角斜接弯头、`500≤Re≤60000`。其 `m=−dlnK/dlnRe` 于 **Re≈11666** 降至 `.2`；原文 ±3% 为**平均拟合误差**。`Re_M=4000,Re_P=12000` 的关联式比值 `1.340`，超过 `.2` 指数的 `1.246`，但不能移植为 KYLIN 的弯头系数。
4. **留出点口径已核：** Li 正文 24 kW、阀门最大开度给 `1.21 kg/s`（摘要圆整为 `1.2`）；Yue §5.2 给 17.9 kW 理论/实验/CFD `1.10/1.12/1.20 kg/s`。两文实验流量均按加热段能量平衡反算，流量与温升不独立；Yue CFD 又以直管替换阀门并设绝热。17.9 kW 只能在阀门、油侧与热量口径对齐后作候选留出点。

## 下一轮给 Workbuddy 的具体任务

> 先用 Yue 第 2–4 页的 `26/54/22 mm`、`L_pipe≈11 m`、式(3)/(6)–(9) 和 Table 2，逐项复算**单侧**五个阻力点；明确计算 `f` 时使用何种关联式，尤其解释 `Re_tube=27800` 行由 `K_pipe=17.7` 隐含的 Darcy `f≈0.03947` 与光滑管 Blasius `0.02450` 的差。把 Table 2 标为“作者理论结果”，不要标实测。固定 24 kW 参数后，用同一阀位、油侧和加热段热量口径预测 17.9 kW 流量，**不得重新标定**。逐构件 `κ_i=K_i(A_ref/A_i)^2` 要注明面积和开度；未知的 `α_i` 与成对 `δ` 保留为空。通用锐角斜接弯头关联式只作反例，不代入 KYLIN。完成上述单侧闭合后，再讨论成对缩比盒、摄动与 GSA。

分析采用 norman-paper-reading 技能｜作者：N同学｜小红书：N同学｜B站/抖音：耐心的N同学

Analysis performed using the norman-paper-reading skill | Author: N同学 | Xiaohongshu: N同学 | Bilibili/Douyin: 耐心的N同学
