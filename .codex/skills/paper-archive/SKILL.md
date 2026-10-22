---
name: paper-archive
description: 文献归档与整理。当用户要把论文 PDF 归档、按规范重命名、去重、生成文献清单、整理参考文献目录、建立文献笔记时使用。适用于 papers/ 目录及本地文献库的规范化管理。
---

# 文献归档（paper-archive）

把散落的 PDF 变成可检索、可引用、不重复的文献库。

## 一、命名规范

| 场景 | 命名格式 | 示例 |
|---|---|---|
| 云仓库 `papers/` | `作者-年份-期刊缩写-页码或DOI尾号.pdf` | `carnevali-2025-nucengdes-114409.pdf` |
| 本地 Zotero 库 | `第一作者 等 - 年份 - 完整标题.pdf` | `Carnevali 等 - 2025 - Combining sensitivity analysis...pdf` |

规则：全小写英文 + 连字符（云仓库）；作者只取第一作者姓；标题截断时保留语义，不要留半个单词。

## 二、归档流程

1. **识别**：用 pymupdf 读首页文本与元数据，提取标题、作者、年份、期刊、DOI
2. **核对**：文件名/元数据与实际首页是否一致；不一致以 PDF 正文为准
3. **查重**：先比对文件大小，再比对正文文本（抽取全文求哈希），不要只看文件名
4. **落位**：按上表命名，放入目标目录
5. **登记**：更新 `papers/INDEX.md` 清单（见下）
6. **报告**：说明本次新增/跳过（重复）/待确认的条目

## 三、查重规则

```python
import pymupdf, hashlib
def fingerprint(path):
    doc = pymupdf.open(path)
    text = "".join(p.get_text() for p in doc).strip()
    return doc.page_count, hashlib.sha256(text.encode()).hexdigest()
```

页数与正文哈希都相同 → 同一篇，跳过并告知用户。仅元数据/字节不同但正文相同 → 也视为重复。

## 四、INDEX.md 格式

```markdown
| 文件 | 题名 | 作者 | 年份 | 期刊 | DOI | 主题 | 一句话结论 |
|---|---|---|---|---|---|---|---|
| carnevali-2025-nucengdes-114409.pdf | Combining sensitivity and scaling analysis | Carnevali 等 | 2025 | Nucl. Eng. Des. | 10.1016/j.nucengdes.2025.114409 | 失真/敏感性 | 把 GSA 与比例分析结合，给出台架失真评估路径 |
```

一句话结论没读过就不要编，写「未精读」。

## 五、环境限制

- 云容器网络是白名单代理，**访问 doi.org、出版社、CrossRef 会 403**。缺 DOI 或元数据时：从 PDF 首页与嵌入元数据抽取，标注「来源：PDF 内文」，不要编造。
- 需要联网补全信息时，明确告诉用户「本环境无法联网核对，请人工确认」。
- 本地 WorkBuddy 环境可用 Crossref / OpenAlex 接口补全（`api.crossref.org/works/<doi>`）。

## 六、不要做的事

- 不覆盖同名文件：冲突时另存 `-v2` 并报告，由用户决定保留哪份
- 不删除任何原始文件
- 不把预印本与正式版当同一篇（版本不同要分别标注 `preprint` / `published`）
- 不臆造 DOI、卷期、页码
