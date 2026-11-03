lit-mirror skillpack · 2026-11-03
================================================================

先说一句要紧的：**没有任何技能能给 Codex 装上网络。**
技能只是文本 + 脚本；它不能让一个不能联网的链路看到网页。
所以「Codex 看不到额外文献」这件事，靠装技能解决不了，得靠**换角色**：

    联网侧（我）= 取件 + 抽文本 + 定级
    推理侧（Codex）= 只读工作区里的 .txt，按页码引

这个包里唯一真正解决你那个问题的，是 lit-mirror。其余是配套。


目录
----------------------------------------------------------------
lit-mirror/                  ← 新写的。让不能联网的链路也能读文献且引用可回溯
    SKILL.md                 铁律 / 目录约定 / 五步流程 / 定级 L1-L4 / 反模式
    scripts/pdf2txt.py        PDF → 带 [[pN]] 页码锚的 txt（pypdf，离线）
    scripts/mirror_check.py   审计：缺件清单 → 下一张取件单（退出码 0 才算过）
    templates/证据卡.md       一篇一张，每条数字必须跟 [[pN]] 表M
    templates/取件单.md       给联网侧的具体取件要求（不是「找一下 XX 文献」）
    templates/claims.csv      断言｜证据指针｜定级｜缺口

pdf/                         PDF 读写操作手册（pypdf / pdfplumber / OCR），纯 Python，可移植
research-literature-manager/ 文献精读 11 板块 + 本地文献库（scripts/litlib.py 全文检索）
norman-paper-reading/        只保留了 SKILL.md 与 README.md（见下方「剔除了什么」）
_上一批/                     11-02 给过的三个：origin-paper-workspace / sensitivity-analysis / zvex-model-sensitivity


怎么用（三步）
----------------------------------------------------------------
1) 我这边取件，原样丢进  文献原文/<key>.pdf
2) python scripts/pdf2txt.py --dir 文献原文
   → 文献文本/<key>.txt（每页开头 [[p1]]、[[p2]]…）
3) python scripts/mirror_check.py .
   → 退出码 0 才把 文献文本/ + claims.csv 交给 Codex；否则缺件清单就是下一张取件单

给 Codex 的话只需要一句：
「你只能引用 claims.csv 里 grade ≥ L2 的条目，每条要给 [[pN]] 表M；其余写未核。」


剔除了什么，为什么
----------------------------------------------------------------
norman-paper-reading 自带的 norman-paper-reading.exe 是 30 MB 的 Windows 二进制，
另有 macos-arm64 / macos-x64 两个 39 MB 版本。Codex 用不上，也不该塞进压缩包。
它的**工作流文本**（SKILL.md，13 KB）留下了，那部分是可移植的。

同理：kling-ai、weixinpay、patsnap-search 这几个是连接器（MCP），不是技能，
压缩包带不走；其中 patsnap-search 在本次会话里是 unavailable（授权失效）。


这个包的边界
----------------------------------------------------------------
能解决：文献看不到、看到了核不回去、缺件越积越多没人分工。
不能解决：付费墙（Li 2015 / Yue 2017）、原文本身没写的东西（KYLIN 的段长分配）、
          以及任何需要仪器或图纸才能得到的量。

最后一条正好是本轮分析的结论：
delta 不是一个可以被「查」到的量，它是 B 与 c 的函数。
详见 比例失真_计算/identifiability_v10.py 与
    docs/可辨识性与参数域_2026-11-03.html
