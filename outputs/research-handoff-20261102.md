# 自然循环缩比失真研究：文件索引与 Workbuddy 交接

更新日期：2026-11-02。**本文件是下载入口和下一轮工作素材**。请先读下表最上方的**v6 最新复核**：Zhao 模型的双侧 3% 可行带成立，但 v6 声称适用于任意 `λ/d` 的双侧界有反例，已给出有条件的修正式。下方旧报告保留审计轨迹；如有冲突，以最新复核为准。链接使用完整仓库地址，单独下载这份 Markdown 后仍可点击；本地使用前执行 `git pull`。

## 文件下载

| 主题 | 文件 | 用途 |
|---|---|---|
| **v6 最新复核（先读）** | [复核报告 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v6-review-20261102.pdf) · [可编辑 Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v6-review-20261102.md) · [独立复核脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v6-audit-20261102.py) | 一般 `λ/d` 的反例与修正条件界；Zhao 3% 双侧带可保留；摄动在整条方法链中的具体位置 |
| v6 上传原件 | [v6 原脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v6-upload-20261102.py) · [原日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v6-upload-log-20261102.txt) · [原 HTML 报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v6-upload-report-20261102.html) · [本轮 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/zhao-3pct-band-v6-upload-20261102.csv) | Workbuddy 原始计算；新 CSV 有 61 数据行，脚本核对的 81 行是前轮 CSV |
| v5 前轮复核 | [复核报告 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v5-review-20261102.pdf) · [可编辑 Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v5-review-20261102.md) · [复核脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v5-audit-20261102.py) · [3% 可行域 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/zhao-three-percent-design-region-20261102.csv) | `δ` 解析界适用域、负向 3% 分支、精确两侧 `w(δ)` 边界和 81 点情景曲线数据 |
| Zhao 3% 可行域论文单栏图 | [矢量 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/zhao-three-percent-design-region-20261102.pdf) · [SVG](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/zhao-three-percent-design-region-20261102.svg) · [600 DPI PNG](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/zhao-three-percent-design-region-20261102.png) · [绘图脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/plot-zhao-three-percent-design-region-20261102.py) | 阴影为未标定 `δ` 情景下满足双侧 `|D_m|≤3%` 的 `w`；仅作模型条件图，不是实测台架认证。 |
| v5 上传原件归档（待审计） | [v5 原脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v5-upload-20261102.py) · [原日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v5-upload-log-20261102.txt) · [原 HTML 报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v5-upload-report-20261102.html) | 保留 Workbuddy 本轮原始计算；完整运行需要下方四段修订依赖脚本。 |
| v4 前轮复核 | [复核报告 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v4-review-20261102.pdf) · [可编辑 Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v4-review-20261102.md) · [复核脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v4-audit-20261102.py) · [IAEA LFR-21 原文](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/lfr-21-kylin-ii-nc-original-20261102.pdf) | Zhao 条件证书评估、`δ=.35` 反例、KYLIN 根区域的单调证明、`.268` 舍入来源、档案仪表矛盾 |
| v4 上传原件归档（待审计） | [v4 原脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v4-upload-20261102.py) · [原日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v4-upload-log-20261102.txt) · [原 HTML 报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v4-upload-report-20261102.html) | 保留 Workbuddy 本轮原始计算；完整运行仍需下方四段修订依赖脚本。 |
| v3 前轮复核 | [复核报告 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v3-review-20261102.pdf) · [可编辑 Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v3-review-20261102.md) · [复核脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v3-audit-20261102.py) | v3 数值复现；`F_x` 漏项、箱覆盖空隙、派生常数无包络；Xu `<7.3%` 无法约束 `δ`；`w=0` 闭式反例 |
| v3 上传原件归档（待审计） | [v3 原脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v3-upload-20261102.py) · [原日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v3-upload-log-20261102.txt) · [原 HTML 报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v3-upload-report-20261102.html) | 保留本轮 Workbuddy 原始计算与解释。完整复跑时将下方修订依赖脚本复制到同目录并命名为 `loop_audit_repair.py`。 |
| v2 前轮复核 | [复核报告 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v2-review-20261102.pdf) · [可编辑 Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v2-review-20261102.md) · [Xu FR26 原文](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/xu-fr26-170-original-20261102.pdf) · [解析界核查脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/zhao-analytic-envelope-check-20261102.py) | Xu 表 1/2 与 Fig. 3 核读；v2 单参数证书的导数与舍入问题；较宽但可论证的解析条件界 |
| 本轮上传原件归档（待审计） | [v2 原脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v2-upload-20261102.py) · [原运行日志](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v2-upload-log-20261102.txt) · [原 HTML 报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-v2-upload-report-20261102.html) · [所需依赖脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/loop-audit-repair-corrected-20261101.py) | 保留 Workbuddy 本轮输入原貌；其中“末位认证”和“独立验证”说法需以最新复核为准。运行原脚本时，将所需依赖复制到同目录并命名为 `loop_audit_repair.py`。 |
| 上一轮复核 | [源无关条件界复核 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-bound-review-20261102.pdf) · [可编辑 Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-bound-review-20261102.md) · [复算脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-bound-audit-20261102.py) · [结果 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/source-free-bound-audit-20261102.csv) | 检查通用 `K_R` 的长度因子、比热比方向和 KYLIN 热损反例；分清候选留出点与已验证工况 |
| Zhao 成对前向模型 | [复核报告 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/paired-forward-review-20261101.pdf) · [可编辑 Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/paired-forward-review-20261101.md) | 流量/温升口径、精确关系、Re 内生求解及“认证上界”审查 |
| Zhao 成对前向模型 | [复算脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/paired-forward-consistency-20261101.py) · [原上传黏度结果 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/paired-forward-consistency-20261101.csv) · [赵文同版黏度结果 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/paired-forward-zhao-property-20261101.csv) | 用两种黏度式复算同一条件模型；CSV 可由脚本重新生成 |
| KYLIN-II 四段模型 | [第二轮复核报告 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-second-review-audit-20261101.pdf) · [可编辑 Markdown](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-second-review-audit-20261101.md) | 名义摩擦份额、共同阻力成对扫描、缩比参照口径及跨案例判据审查 |
| KYLIN-II 四段模型 | [过零及口径复算脚本](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-denominator-crossing-20261101.py) · [结果 CSV](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/kylin-denominator-crossing-20261101.csv) | 复算有限正阻力过零点，以及只换参考比与同时换功率设计的差别 |
| 共同背景 | [Carnevali 等（2025）原文 PDF](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/papers/carnevali-2025-nucengdes-114409.pdf) · [此前的方法定位报告](https://github.com/apple114514-mum/114514-brand-new-day/blob/main/outputs/paired-scaling-method-position-20261101.md) | 失真对 FoM 的影响、可接受性问题与本研究的贡献边界 |

## 给 Workbuddy 的已核结论

### 本轮 v6 更新

- v6 脚本复跑 205 行；上传日志 202 行完全一致，另三行仅区间末位约 `10^-16` 有平台差异。新上传 CSV 为 **61** 个数据行，逐行与闭式相符；v6 脚本 `[D]` 使用硬编码路径核的 **81** 行是上一轮 CSV。两份文件不能混称。
- Zhao `c=λ/d=1` 的双侧 `|D_m|≤3%` 带与 `δ_crit≈0.092755604047` 可保留；在临界值处 `w=0` **恰好可行**。`δ→−1` 仍有数学可行带，但实际局阻范围未建立。
- v6 的**通用双侧界不成立**：同一声明模型改 `c=.5,δ=0,w=1`，实际 `D_m=−14.416496%`，v6 下界却为 `0%`；改 `δ=−.5`，实际 `−14.416496%` 又高于其上界 `−14.575176%`。在根处物性方向成立时，可用 `q=[(λ/d)(R_id d)^n]^{1/(3−n)}` 及 `min{1,(1+δ)^{1/3},q}−1 ≤ D_m ≤ max{1,(1+δ)^{1/3},q}−1`。这是保守模型界，不是物理认证。
- 摄动已经可具体落实为隐式导数：Zhao `w=.2,δ=0` 点的 `∂D_m/∂w≈0.098616705`、`∂D_m/∂δ≈0.260956027`，与有限差分相符。它给设计点的局部方向；3% 带给条件可行域；GSA 需有来源的联合参数域或明确声明的概率分布，尚未完成。

### 本轮 v5 更新

- v5 日志 **204 行逐行复现**。其上界 `D_m≤max{(1+δ)^(1/3),(R_id d)^(n/(3−n))}−1` 需连同 `M(x)≤1`、`μ_R≤1` 和物性有效域一起报告；**不能无条件写“所有 `δ>−1`”**。下界可用 `x<1` 时 `f(x)>x³` 直接证明，无需全域 `f≥1`。
- Zhao 声明模型的 `|D_m|≤3%` 设计域是**双侧** `max(0,w_−(δ))≤w≤min(1,w_+(δ))`。`δ=−.10` 时为 `[0.03257,0.47579]`；`δ=+.07` 时为 `[0,0.09678]`。正向 `w=0` 变物性阈值是 `δ≈0.092755604`，不是 v5 称为“硬上限”的 `0.092727`。上方 CSV 提供 81 个未标定情景点。
- 两个 δ 阈值 `0.327848828−0.323077721≈0.004771107` 的主因是**解析根包络与实际根的间隙** `+0.004882331`，物性项为 `−0.000111224`；不能称“恰好是物性比偏离 1 的三倍”。`F_dep_iv()` 的 `G=1+w[...]` 写法只在 `δ=0` 等价；非零 δ 时须改为 `G=(1+δ)+w[...]`。
- “K_EV/K_HS/K_pipe 在 Yue 2017 表 2”仍是**未见全文的转述**；即使该表有单台架阻力，也只能帮助阻力份额 `w`，成对局阻失配 `δ` 仍需原型和台架两侧数据。

### 本轮 v4 更新

- v4 日志 **212 行逐行复现**。Zhao `d=λ=.5,n=.25,δ=0,w∈[0,1]` 声明模型的 `w=1` 根区间 `[1.09778244634013289,1.09778244634013911]` 可作为依赖程序所述浮点函数误差界的**条件证书**；解析宽界 `[0,+9.914%]` 仍适合作主要解释。
- `w=1` 的端点对 `δ` 不敏感，**整个 w 域的上界并非如此**：同一模型取 `δ=.35`，`w=0` 偏差 `+10.5176%`，超过 `w=1` 的 `+9.7782%`；阈值约 `δ=.323078`。`δ` 尚无文献/实测域，不能把 `+9.7782%` 写成任意局阻条件的上界。
- v4 所用 KYLIN 近似输入 `d=.5**.7,Q_R=1/.268` 的根均位于 `x∈[.99998,1.00001]`，沿根管 `(λ/d)f−1<0`、`F_x>0`，故偏差随 `w` **单调下降**；宽箱 `F_w` 跨零只表示判号不充分。其约 `−0.00081%` 来自 `m_R=.268` 三位舍入；用解析 `c^1.9` 则零偏差。
- IAEA LFR-21 一手档案列 KYLIN-II 的 `24 kW`、`2.6 cm` 管径、HS/HX 长 `1.8/1.5 m`、二次侧油，但**没有逐段阻力**；“电磁流量计下次安装”和仪表栏“Induction flow meter”相互矛盾。Xu 表 2 只有缩比比值，**没有** `K_EV/K_HS/K_pipe` 那组三个阻力数；来源仍待查。

### 本轮 v3 更新

- v3 日志 190 行逐行复现；高精度根落在其打印的窄区间内，但当前程序**尚未证明**原十进制模型的 `1×10^-14` 包含宽度。`Fx_iv` 漏黏度温度导数，箱边界出现 3–4 处极小空隙，派生常数先做普通浮点运算。详见上方 v3 复核和脚本。
- Xu §4 的标准缩比 CFD 流量偏差 `<7.3%` 与温差 `<7.5%` 有原文依据；它们不是 Zhao 的局阻参数 `δ`。`δ∈[-.07,.07]` 只能作人为情景，不能称有文献约束。`w=0` 时精确关系是 `x³=M(x)(1+δ)`，立方根闭式要附恒物性条件。
- Xu §2 式(6)–(9)给出多项准则；摩擦数是关键约束之一，不能写成唯一要求。解析条件界 `[0,+9.914%]` 在声明的一维模型内仍成立。

### 1. 研究目标

拟研究的问题是：**指定原型—候选台架的几何、功率和工况映射，在明确的模型闭合与有来源的参数域内，能否于建台架前计算流量、温升等 FoM 的比例偏差包含界，并反解设计可行域？** 缩比比值或全套设计映射是定义“失真”的必要比较基准；FoM 单独不足以给出失真。摄动和 GSA 用于局部方向、参数排序及分盒，不能代替非线性最坏界证明。简化模型可每侧消元到一维求根，因而不需要 CFD/系统程序逐次重算，但**仍需要数值求根**。

### 2. Zhao 2020 成对 CFD 案例

- 原文表 5 的原型/台架比例偏差：流量 **`+2.876835%`**，温升 **`−4.901244%`**；温升不能改写为 `−2.80%`。表 3 的 `1/0.5 m` 是外形直径，不能直接认定为真实净流面积或水力直径。
- 在所用集总动量式和给定几何理想比下，精确代数关系是 `(1+D_m)^3 = E K_R/ρ_R`，其中 `E=(1+D_m)(1+D_T)=0.978345910`。上传模型用设计功率比构造的 `1+ε_Q=0.979160292` **不等于 E**，因此代入后仍差约 `0.029` 个百分点；该差额不能直接证明两次 CFD 使用了不同的施加功率比。
- 将台架雷诺数随未知流量内生求解是有效改进，但上传的 `[-1.219%,+7.035%]` 来自角点和随机点，**不是已证明的全盒上界**。新旧温升范围的 `M/P` 与 `P/M` 方向也不一致，须先统一定义。
- 一个成对工况的两个 FoM 可以在**固定其他假设时**拟合“有效入热量 + 摩擦份额”两个参数；拟合后两个 FoM 都已用尽，仍须独立工况验证。取设计功率 `1.77 MW`、只拟合流量时预测温升约 `131.304 K`，而表 5 为 `136.700 K`；把有效入热量也作为拟合量时可同时命中两者，但该值约 `1.842108 MW` 只是单流道焓代理，不能直接称真实施加热功率。改回赵文表 4 黏度式，主要判断不变。

### 3. KYLIN-II 四段条件模型

- 在所选集总温度形状下，等效浮升高度 **`3.35 m`**；`k_total=11.593` 是在给定 `UA/US` 下由单点反标定的**局部阻力系数和**，不是独立测得的总阻力。
- `1.2 kg/s` 名义点的摩擦份额是 **`48.6726%`**。旧 `57.5287%` 来自 `0.36 kg/s` 点；该点冷段约 `363.49 K`，还低于用户物性台账所列 `398.15 K` 的适用下限，不应作为液态 LBE 的物理份额。
- 对公共 `k` 同时重解两侧并保持相同热损规则后，`k=3,6,11.593,36` 的流量偏差为 **`−5.610%,−8.962%,−12.151%,−16.253%`**。旧 `+10%→−35%` 翻转是固定分母、热损规则及共享状态污染造成的伪像。
- 但“**只有 k 趋近零才可能转正**”仍错：同一条件模型在**有限正 `k≈0.403218`** 数值过零。`k=0.1,0.3,0.4` 的偏差仍为正。`k≥1` 已计算点为负，但全区间方向和单调性尚未完成认证。
- 同功率候选设计的实际流量比 `0.878491`，若理想比分别取 `1` 与 `√0.5`，偏差分别为 `−12.151%` 与 `+24.237%`；后者只是**更换参考尺**。若声称同时保持 `m_R=√0.5` 和 `ΔT_R=1`，能量目标要求净入热量比约 `√0.5`，不能保留同一功率方案的 `Q_R=1`。一个同步调整 `Q/UA/US` 的反事实设计给 `+8.973%`，说明它是**另一设计**。
- Zhao 情景中的 `|D_m|≤3% ⇔ K_R≤1.0923 ⇔ w≤0.302` **不能跨案移植**。KYLIN 名义 `w≈0.487>0.302`，标准缩比流量偏差仍仅 `−0.388%`；两案模型、热损和参数口径不同。

## 已撤回或不得继续引用的说法

1. “Carnevali 明确说设计前失真先验分析为空白”——原文并未这样说。较准确的是：其讨论失真对 FoM 的影响与可接受性如何量化；本研究的设计阶段条件界是**待验证的切入点**。
2. “失真由一个 `K_R` 唯一决定”以及“零次求解”——热量、物性、几何和理想比分母都要明确；当前四段程序实际上两侧各求一个标量根。
3. “`−0.39%` 已证明真实表面体积比失真”——目前仅证明在所选 `US` 缩放规则下的模型内干预结果；`US=6 W/K` 未独立校核。
4. “`k∈[3,36]` 给受实测约束的不确定度范围”——它只是情景扫描；不能当认证最大失真或文献互证。
5. 任何没有同时列出 `Q_R`、`ΔT_R`、`m_R`、实际设计输入及理想分母的单一偏差百分数。

## 下一轮给 Workbuddy 的任务说明

> 请先读本文件所链接的**v6 最新复核**，再读 v5、Xu、LFR-21 与此前报告，**先核来源，再建界**。Zhao `λ/d=1` 的 3% 双侧 `w(δ)` 可行带保留，但 v6 把双侧解析界推广至任意 `λ/d` 的式子已有上下界反例；先按 v6 复核中的 `min/max{1,(1+δ)^(1/3),[(λ/d)(R_id d)^n]^(1/(3−n))}` 条件界改写并检验物性域。`δ_crit≈0.092755604` 的**等号可行**；`δ→−1` 仅是数学极限。修正 `F_dep_iv()`：非零 δ 时应取 `G=(1+δ)+w[(λ/d)f−(1+δ)]`。本轮上传 CSV 有 61 行，脚本硬编码读取的前轮 CSV 才有 81 行，请分清。继续建 `δ`、`w`、净流道尺寸的来源台账，优先核原型与台架两侧压降及 Li/Yue 全文；一侧阻力不能定成对 `δ`。摄动用隐式导数做局部排序和线性余项检查，GSA 需明示联合参数域/分布；它们不能替代最坏界。留出点只预测、不重新拟合。输出按“选用什么—依据是什么—可复核结果—局限—下一步”组织，不需要 PPT。

## 来源边界

Carnevali 等（2025）原文在仓库 `papers/`，已用于 FoM 问题定位。赵鹏程等（2020）中文 PDF 与 Xu/KYLIN、Li 2015 的一手材料并未全部作为本仓库文件交付；目前 Zhao 表 3–5 的数值来自此前上传 PDF 的核读，Xu/Li 具体几何和单点条件仍须重核原文。上述模型复算**不是台架实测性能预报**，也未完成最新文献的系统查新。

分析采用 norman-paper-reading 技能｜作者：N同学｜小红书：N同学｜B站/抖音：耐心的N同学

Analysis performed using the norman-paper-reading skill | Author: N同学 | Xiaohongshu: N同学 | Bilibili/Douyin: 耐心的N同学
