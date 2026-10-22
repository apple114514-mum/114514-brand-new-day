# outputs/ —— 交付物目录

Codex 云容器里生成的文件（PPTX / PDF / 图片 / 表格）**必须复制到本目录再 commit push**，
用户才能在本地 `git pull` 下来直接打开。容器里的临时路径用户是访问不到的。

## 规则

- 命名带版本或日期：`paper-editable-20261022.pptx`、`fig-nu-vs-re.pdf`
- **单文件 < 90 MB**（GitHub 单文件硬上限 100 MB）
- **超过 40 MB 的 PPT/PDF 预览会失败**（前端预览器的限制），但下载仍可用；能压就压：
  - PPTX 内的图片重采样到 1280×720、JPEG 质量 85
  - 或打成 zip 分包
- 只放**最终交付物**，不要把 `generated/`、`previews/`、`source-pages/` 这类中间产物放进来
- 提交信息写清楚：`输出：论文组会 PPT（图片版+可编辑版）`

## 交付后

用户本地执行 `git pull` 即可拿到文件；不需要在任务里反复找「下载按钮」。
