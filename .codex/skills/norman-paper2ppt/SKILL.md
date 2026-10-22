---
name: norman-paper2ppt
description: Turn academic paper PDFs into Chinese research presentations. Confirm presentation mode, speaker notes, and editable output in sequence; plan all prompts together; prioritize original main-text figures, with two related figures per slide for shorter decks and one per slide for longer decks. Add no AI scientific illustrations; use only simple supporting flowcharts. Generate 16:9 layouts in batches, assemble locally, and optionally use bundled norman-fig2ppt for editable text and image objects.
---

# Norman Paper2PPT

Turn a paper into a presentation-ready PPTX grounded in its evidence. Original main-text figures are the primary visuals; AI assists with layout and simple flowcharts. Default to Simplified Chinese. Complete reading, structure, prompts, image production, speaker notes, assembly, and verification. The editable-output engine, runtimes, and licenses are bundled in `vendor/norman-fig2ppt`; no separate installation of that skill is needed.

## 云环境（Linux）适配说明

> 原发行版附带 Windows x64 / macOS 编译引擎（`bin/` 与 `vendor/norman-fig2ppt/bin/`），在 Codex 云端 Linux 容器中无法运行，本副本已按下列替代路线改造。deck.json 约定、页面结构、图覆盖规则、文本框设计标准、水印规则等全部方法论不变。

| 原引擎子命令 | Codex 云环境（Linux）替代 |
|---|---|
| `inspect-pdf` | `pip install pymupdf`，用 fitz 抽取全文并逐页渲染 PNG（做法同 norman-paper-reading 的适配段） |
| `prepare-image-batch` | 直接用 Python 脚本读 deck.json 生成 `prompts/NN.txt` 与 `image-batch.json`；无真实图像工具时跳过整页 AI 图，进入下一行路线 |
| 整页 AI 版图（imagegen） | 先检查环境中真实可用的图像生成工具并核实其参数；不可用时，直接用 python-pptx 按 `image_brief`/`art_direction` 搭建原生文本框 + 原图（等效可编辑版质量），图片版由渲染产出 |
| `powerpoint -Mode images`（组装图片版） | `pip install python-pptx`：960×540 pt（13.333×7.5 in）画布，每页嵌入一张完整 16:9 大图，讲稿写入 notes_slide |
| fig2ppt 引擎（可编辑版） | 用 python-pptx 直接创建原生文本框（`fill_color` 用文本框填充近似，`padding` 用内部边距近似）与普通图片对象；科学图内部文字保持位图，不矢量化 |
| `validate` / `audit` | 按 deck.json 字段写 Python 自检脚本（页数、16:9、每页一张图、备注存在性、封面恰好两行水印、正文无水印），并逐页目视核对 |
| 渲染预览 | 容器内有 LibreOffice（`soffice`）则转 PDF/PNG 预览；没有则如实披露未渲染，不谎称已预览 |

不得把原包的 Windows/Mac 命令伪称可在 Linux 执行；遇到真实能力阻塞时报告并完成可行部分。

## Original figures first; no added illustrations

These rules take precedence over other visual descriptions in this skill and its references.

- Do not add AI-created scientific illustrations, photographs, scenes, 3D diagrams, decorative icons, invented mechanism diagrams, or data charts. AI may organize layout and text and create paper-grounded simple flowcharts using text nodes, basic geometric shapes, and necessary connectors. A flowchart is optional, not a per-slide requirement.
- Inventory all main-text Figures and panels first and include as many as possible. Prioritize main-text figures over supplementary figures; do not select only attractive examples or replace result evidence with flowcharts. Overview and synthesis slides without relevant original figures may use concise text and simple flowcharts, without new filler illustrations.
- For shorter decks, prefer two logically related main-text Figures per slide, aligned horizontally or vertically with separate figure identifiers. For longer decks, prefer one enlarged Figure per slide. One Figure means one numbered paper Figure, possibly with several panels; two panels do not count as two Figures. Dense Figures may span slides by panel, preserving axes, legends, error bars, and necessary controls. Do not repeat figures to fill a slide quota.
- Plan figure coverage within the mode's slide budget before finalizing the results narrative. Two Figures on one slide must remain readable. Explain each omitted Figure or panel instead of shrinking text to force coverage. Record `figure_id`, `pdf_page`, `panels`, `asset_path`, `slide_numbers`, `omitted_panels`, and `omission_reason` in `figure_coverage`. QA must report the total main-text Figures and counts fully shown, partly shown, and omitted; never claim complete coverage without evidence.
- Extract original figures from the PDF or crop high-resolution page renders, preserving aspect ratio and scientific information. Do not ask the model to redraw figures, guess labels, or reconstruct curves. AI-generated full-slide layouts are drafts with clean empty regions for originals. Insert original files directly with local PowerPoint or a native PPTX backend, then render final slide images. Insert the real first PDF page on the cover in the same way. Editable output must reuse original image objects, not approximate scientific figures cropped from an AI draft.
- Faithful local insertion of original figures is explicitly authorized and requires no additional confirmation. This overrides reference language requiring exclusively AI-generated full pages or prohibiting local composition. Other AI-image edits must follow the actual image tool's rules. Apply these constraints to every `image_brief`, `style.md`, prompt, and QA record.

## Full compositions and designed text boxes

Use the effective canvas to form a finished composition, eliminating large unused areas while retaining safe margins and figure/text spacing. Original figures, titles, explanatory text boxes, and conclusion bands should occupy the main region. Background color, empty boxes, and decoration do not count as substantive coverage. Enlarge originals and improve layout first, then add evidence-grounded explanation, comparisons, method definitions, interpretation of numbers, and limitations. Do not copy speaker notes into slides or add unsupported material.

- Result slides usually contain 120–180 external Chinese characters; overview and synthesis slides usually contain 160–220; the cover about 60–100, excluding the English paper title, bibliographic details, and fixed watermark. These are density targets, not quotas; readability of complex figure labels takes priority. Explanations may use 3–5 short sections with small headings and usually 1–3 lines each.
- Default to designed native text boxes with light solid fills, dark text, clear small headings, and consistent padding. Use conclusion, metric explanation, comparison, and evidence-boundary boxes to support the figure. Use 2–4 text regions with clear hierarchy or a full-width bottom synthesis band; do not impose identical equal-width cards on every slide. Dark heading boxes with white text are allowed when contrast is sufficient. Explanations need not float without a background.
- Vary layouts: large figure with compact side notes; two figures above an explanatory band; vertically arranged evidence and conclusion; or a process alongside data interpretation. The title region is roughly 12%–16% of slide height, and the body extends toward the footer. Main content should occupy about 90%–96% of safe-area width and 85%–92% of its height. Treat these as composition guides, never reasons to crop scientific information. Avoid two-sentence sidebars, near-empty synthesis slides, and isolated islands of figure and text.
- On a 960×540 pt canvas, body text is usually 18–22 pt, small headings 22–28 pt, and main titles 30–36 pt. Adjust text-region dimensions and grouping, then remove repetition; do not shrink type to force content in. Keep paragraph spacing, line spacing, and padding consistent, align text-block bottoms, and place explanations near the figures they explain.
- Editable output must preserve text-box fills, padding, and type hierarchy. Do not replace the design with scattered text on a plain white slide. Use native text-box fill; do not add complex shapes, paths, illustration tracing, or vectorization inside scientific figures. Scope remains text and ordinary images.
- Specify each figure slot and text region's position, dimensions, fill, text color, type size, padding, and exact copy in `image_brief` / `art_direction`. Plan the finished appearance after original-figure insertion. QA must inspect composition density, hierarchy, style preservation, and large empty areas in both image and editable versions. Figure fidelity alone does not establish visual quality. Fix hollow layouts in the same correction round without seeking new approval.

## 1. Start with three sequential choices

After receiving the PDF, ask for the following choices in order, **one question at a time, waiting for each answer**. Reuse choices already stated by the user. If the PDF is missing, request it first. Ask in the user's language; the default presentation language is Simplified Chinese.

1. Choose a mode: A, brief overview (5 minutes, 5–7 slides); B, standard reading (10 minutes, 8–12 slides); or C, deep reading (15 minutes, 12–16 slides).
2. Ask whether to include slide-by-slide speaker notes, about 200 Chinese characters per minute: approximately 1,000 / 2,000 / 3,000 characters respectively, also written into presenter notes where possible.
3. Ask whether to also create an editable PPTX. Explain that the image version has one complete image per slide; editable output takes additional processing, while scientific charts and illustrations remain ordinary images.

Once these choices are complete, start production directly. **Do not ask again about slide count, style, audience, output directory, outline approval, Quick/Advanced mode, or other production preferences.** Choose a suitable count, usually 6 / 10 / 14, including the cover, combined research overview, core results, and final synthesis. Explicit custom user instructions take precedence. Ask only for missing choices. While waiting, inspect the PDF inventory and tools, but do not generate slides early.

A technical blocker is not a new preference questionnaire. Report missing tools or actual failures and continue feasible work. Do not substitute guesses for unread papers or ungenerated images. Do not silently activate paid APIs, change macro-security settings, or install software.

## 2. Prepare actual tools and the working directory

Read [Local execution and file conventions](references/local-execution.md). In the Codex cloud (Linux) environment, follow the adaptation table at the top of this file instead of any Windows/Mac engine commands.

- Check what is actually available in this environment before relying on it: Python 3 and pip (install `pymupdf` and `python-pptx` as needed), any real image-generation tool (verify its actual arguments; do not invent model, resolution, or save-path parameters), and whether LibreOffice (`soffice`) exists for rendering. Do not assume tools from the author's original environment exist.
- If a real image-generation tool is available, use it for full-page layout drafts as described in section 4. If not, skip the AI full-page image and build slides directly with python-pptx (native text boxes + original figures), which is the authorized local-composition path.
- Do not look for `bin/` or `vendor/norman-fig2ppt/bin/` compiled engines; they cannot run on Linux. The editable-output route is python-pptx native objects, per the adaptation table.
- Use the user's specified output directory; otherwise create a new `paper2ppt-<paper-short-name>-<timestamp>` directory in the workspace. Do not overwrite previous deliverables. Record paths to the source PDF, originals, raw generated images, and corrected versions.

## 3. Read the paper and plan the narrative

Read [Scientific evidence and visual production](references/evidence-and-design.md) once, then reuse saved evidence locations rather than repeatedly rereading everything. **Actually read the entire PDF**, including original figures, captions, tables, and important equations. Text extraction does not replace image inspection. For scanned pages, use available OCR or read page images; empty extraction does not mean absent results.

Extract research background, scientific question, data and methods, main results, mechanism interpretation, innovation, limitations, conclusions, and research implications. Record sample sizes, comparators, effect direction, numbers, units, statistical definitions, causal boundaries, PDF page numbers, and figure/panel sources. Mark information absent from the paper as not reported. Distinguish authors' conclusions, evidence-supported scope, and your own implications.

Create an evidence table and figure inventory. **Use exactly four structural parts:** one cover; one combined background / technical approach / data and methods slide; multiple core-results slides based on the evidence and selected duration; and one final combined innovation / conclusions / research implications slide. Each combined slide must contain its three topics rather than splitting them into separate sections. For `N` total slides, use `N−3` core-results slides: 2–4 for brief, 5–9 for standard, and 9–13 for deep.

Develop results along the evidence chain, placing mechanism, controls, and robustness on relevant results slides. Put limitations beside their relevant results or in the final synthesis. Do not add separate agenda, transition, or closing slides. Each slide has one governing point; the combined slide's three topics support it coherently. Prefer evidence-supported conclusion titles for results. Do not split a single conclusion to fill a quota or shrink type to force all figures in. Record important omitted evidence in the coverage table.

Use `deck.json` and `evidence.json` as the content sources without requesting approval. Save the nine reading categories together in `deck.json.analysis`, figure coverage in `figure_coverage`, and each slide's evidence, copy, layout, and timing on the slide itself. Do not create duplicate `analysis.md` or `storyboard.md` by default; export detailed research records only when requested.

Keep machine-validated Chinese schema values unchanged, even though these instructions are English:

- `section` sequence: `封面` → `研究背景、技术路线与数据方法` → one or more `核心结果` → `研究创新、研究结论与研究启示`.
- Overview `topics`: `["研究背景", "技术路线", "数据方法"]`.
- Final synthesis `topics`: `["研究创新", "研究结论", "研究启示"]`.

For the cover, record the real file path, PDF page 1 source, and right-side position in `cover_paper_image`. Timing must total exactly 300 / 600 / 900 seconds, with slide count inside the chosen range. Once close reading is complete, briefly report the findings in chat, append the two exact watermark lines from section 5, and continue without waiting for confirmation.

## 4. Prepare all prompts, then generate layouts in a batch

Use one actual image-tool call per slide to create a 16:9 layout draft containing layout, approved copy, and any necessary simple flowchart. Leave original-figure regions clean and empty. Insert the paper's originals locally and render complete final slide images. Never crop a multipage collage into purported independently generated slides.

**Default fast production sequence:** read once and settle the full deck's content → establish one shared visual style → write all slide copy, compositions, and reference lists → compile all prompts and the job queue together → generate the entire first draft continuously → inspect the complete set → correct only affected slides. Read and follow [Fast batch production](references/batch-production.md). Do not finish generation, aesthetic refinement, speaker notes, and reconstruction of one slide before starting the next. Do not require repeated cover/sample approval.

Improve image quality through the current environment's imagegen tool and specific art direction. Do not promise the same model, sampling, or results as another chat client. Default to a full-canvas scientific information composition guided by the slide's actual argument: background extends to the edges, major figures and explanations occupy most of the canvas, and titles, nearby annotations, and conclusions form one reading path. Follow the full-canvas and logical-composition standards in the design reference. Avoid small centered figures, large idle areas, floating short sentences, and unrelated blocks. Prefer light solid text boxes and conclusion bands with substantive explanations.

Choose the argument structure first—process, comparison, or evidence convergence—without decorative arrows implying unsupported causation. Preserve safe text margins and complete scientific figures. Write the shared palette, fonts, title hierarchy, margins, chart language, header, page numbers, and watermark placement in `style.md`. Default to modern academic editorial design: restrained colors, clear hierarchy, precise alignment, a strong visual focus, and enlarged original figures. Translate the reference's slide-type layouts and acceptance criteria into specific compositions; words such as beautiful or professional alone are insufficient. Use coordinated but varied cover, overview, results, and synthesis layouts. The combined slides must integrate images and text with hierarchy, avoiding three long paragraphs or mechanical three-card grids. Decoration must not displace evidence.

**Required cover layout:** approved paper title, research positioning, and essential bibliographic details on the left; a high-resolution screenshot of the paper's **actual PDF page 1** on the right. Preserve its paper aspect ratio and page edges. It should occupy approximately 35%–42% of effective cover width and must not move to the left. Render and inspect the real page in advance for layout reference and direct final insertion. Do not substitute a fabricated paper or journal cover, another PDF page, or a generic illustration. Keep it separate from the bottom watermark; key bibliographic details should be recognizable, while small page text is contextual rather than mandatory audience reading. The final rendered cover must contain the directly inserted real page; editable output keeps it as an ordinary image.

Write every slide's `image_brief`—governing point, exact copy and numbers, dedicated layout, and image-input roles—and `reference_images` together in `deck.json`. Describe visual logic and reading direction in `image_brief` or optional `visual_logic`. Finalize `style.md` once, then run `prepare-image-batch` to produce all `prompts/NN.txt` files and `image-batch.json` together. Reuse shared specifications instead of reinventing prompts or revisiting settled paper content per slide.

Target native 1920×1080 or higher output. If the tool lacks a size parameter, state the target in the prompt and inspect actual pixels; never claim unverified HD. If native resolution falls short but scientific content and projection readability are acceptable, record and disclose it rather than repeatedly regenerating against the same limitation. Upscaling is not native HD.

Inspect reference images together before submission and identify their roles. Each slide depends on its own paper originals and the common style, not on the previous generated slide. Use bounded concurrency only when actually supported, with at most three slide calls and a rolling queue. If the interface is serial, submit continuously in sequence without extra performance experiments. Between serial submissions, save outputs and state; defer aesthetic discussion, rewriting, and reconstruction until the complete draft exists. A batch is orchestration of independent calls, not an invented tool batch endpoint, a multipage collage, or an unauthorized switch to another API or CLI.

Original figures and high-resolution panels are layout references only; their regions remain empty until original files are inserted directly. Generation can alter curves, numbers, and captions, so **compare result figures item by item with the originals**. Supplying a reference does not prove fidelity. Before using local images, inspect them with `view_image`, then supply reference paths or recent images according to the actual tool API. Preserve aspect ratios, axes, legends, statistical information, and necessary source labels.

After all first drafts return, inspect them together for copy, statistics, figures, layout, the cover watermark, and absence of skill watermarks on body slides. Make one list of affected slides; lock acceptable slides immediately rather than regenerating for minor aesthetic preferences. Normally perform one targeted correction round and recheck it. Mandatory fixes include text or scientific errors, missing cover watermarks, accidental body watermarks, wrong figures, cropping, overflow, and clear unreadability. Edit AI layouts using the same image tool under its actual editing rules; for scientific figure errors, reinsert the original file rather than asking the model to redraw it. The need for correction does not authorize changing image-editing tools. Direct insertion of original figures and the real cover page is already authorized. If necessary errors persist, simplify and regenerate the affected slide; disclose unresolved blockers instead of delivering known erroneous images.

After all slide images pass review, assemble the image version immediately, then perform the optional editable branch. While image calls are pending, prepare requested speaker notes, asset records, and assembly manifests without delaying available submission slots. Save raw outputs in `generated/` and final slide images as `slides/01.png`, etc. Require consistent dimensions, exact 16:9, complete scientific content, and no stretched figures or interpolation presented as native HD. Replan and regenerate unreadable pages.

## 5. Exact watermark on the cover only

Only the first PPT slide—the cover—must contain these two lines exactly. Do not change wording, capitalization, or punctuation. From slide 2 onward, including the final synthesis, add no skill watermark:

```text
分析采用 Norman Paper2ppt / norman-paper2ppt 技能
技能作者：小红书：N同学，抖音/B站：耐心的N同学。
```

Place both fully readable lines in the cover's bottom safe area, separate from source footnotes and page numbers. Embed them in the final complete cover image, not only as a PPT overlay or presenter notes. Editable output retains the same cover content, preferably as native text boxes. Reserve no watermark placeholder on body slides and do not repeat author promotion there; retain ordinary scholarly sources and page numbers.

**The chat watermark is also required:** after the paper-analysis update and after the final delivery response, append the exact two lines as ordinary visible text following prose and file links. Interpret references to the AI input box as the AI reply area; do not operate, write into, or claim to modify the user's input field. File content, screenshots, code blocks, and notes do not replace the visible chat text. Replies discussing skill installation or modification without paper analysis do not trigger this rule.

## 6. Speaker notes, image output, and optional editable output

If requested, write natural, spoken, scientifically accurate notes for each slide, including transitions and figure interpretation rather than reading bullets aloud. Target approximately 1,000 / 2,000 / 3,000 Chinese characters for the selected mode, allowing about ±10%. Match slide timings and final content. Save UTF-8 `speaker-notes.txt` and write notes into corresponding presenter-note fields in both versions. Count Chinese characters in narration only, excluding slide titles and other metadata. Character counts do not prove actual speaking duration.

Without narration, create no speaker-note file and do not insert production logs into notes.

**Always deliver the image version.** Assemble with python-pptx (Codex cloud adaptation; the compiled helper's `powerpoint` mode is Windows-only and unavailable here). Embed, rather than link, exactly one complete image per slide, filling the 960×540 pt 16:9 canvas without overlays obscuring science. Add notes if requested. Save `paper-image.pptx`, render it (via LibreOffice if available; otherwise disclose that rendering was not performed), and inspect the output.

**Deliver editable output only when selected.** Read [Fig2PPT handoff and actual invocation](references/fig2ppt-handoff.md) for the object-separation rules and text-box style requirements, but note that its engine commands are Windows/Mac-only: in this environment, build the editable deck directly with python-pptx from the measured objects list in `deck.json` (native text boxes with fills/padding/hierarchy + ordinary images). Limit scope to native editable text boxes and ordinary images, preserving fills, padding, hierarchy, and layout. Keep charts, illustrations, flowcharts, arrows, and similar visuals as image regions. Do not use path tracing, curve reconstruction, or vectorization of internal figure labels. External titles, body copy, conclusions, page numbers, and the cover watermark must be editable. Do not overlay editable text on a full-slide background that still contains the same text, hide OCR text, or present rasterized text as editable.

If the macro runner fails but ordinary object interfaces work, complete the editable version and record the actual backend, explicitly noting that macros were not run. If both assembly routes fail, retain the image version and disclose that editable output remains incomplete. Never rename an image-only deck to suggest editability.

## 7. Verify slides and deliver directly

The compiled `validate` / `audit` helpers are unavailable in this environment; implement the same checks with python-pptx and file inspection: slide count and order per deck.json, exact 16:9 dimensions, exactly one full-bleed image per slide (image version), embedded (not linked) media, presenter notes present when requested, the cover containing exactly the two watermark lines and no watermark on body slides, and narration length per mode. Machine checks do not establish watermark pixels or scientific accuracy; visual inspection of the rendered pages remains mandatory.

Perform and save one scientific/visual review of generated images in `qa.json`; use brief actual observations for the reference's six dimensions rather than long evaluations of normal items. After rendering the PPTX, inspect the complete thumbnail set and full-size views of the cover, densest results slide, and final slide, focusing on aspect ratios, cropping, order, and notes. If image-version `audit` proves media-hash equality and correct full-slide placement, reuse the original image review rather than rereading all text and figures. Expand review only for slides with rendering anomalies. Editable output requires full-size inspection of every slide because layout was reconstructed; check text, image position, and duplicate text. Record the actual inspection scope and unresolved items. Disclose if rendering was not performed. Do not regenerate acceptable slides for minor preferences.

Deliver clickable links to the image PPTX, final slide-image folder or ZIP, and any selected editable PPTX and notes. Retain prompts, evidence records, originals, and QA for traceability without asking for another confirmation. Explain actual limitations affecting use. Do not invent tool calls, generation, rendering, or installation status.
