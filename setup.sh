#!/usr/bin/env bash
# ============================================================
# Codex 云环境初始化脚本
# 用法：Codex 网页端 → 编辑环境 → Setup script 填 `bash setup.sh`
#       保存并发布后，新开任务即生效（旧任务不会自动重建）
# ============================================================
set -uo pipefail

echo "==> [1/4] 系统依赖（poppler 用于 PDF，Noto CJK 用于中文渲染）"
if command -v apt-get >/dev/null 2>&1; then
  SUDO=""
  [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"
  $SUDO apt-get update -qq || echo "  (apt update 跳过)"
  $SUDO apt-get install -y -qq poppler-utils fonts-noto-cjk 2>/dev/null || echo "  (部分系统包安装失败，继续)"
else
  echo "  非 apt 系统，跳过"
fi

echo "==> [2/4] Python 依赖"
python3 -m pip install --quiet --upgrade pip 2>/dev/null || true
python3 -m pip install --quiet pymupdf python-pptx pillow requests \
  || python3 -m pip install --quiet --break-system-packages pymupdf python-pptx pillow requests \
  || echo "  (pip 安装失败，任务中可重试)"

echo "==> [3/4] 可选：LibreOffice 渲染（体积大 ~400MB，按需取消注释）"
# $SUDO apt-get install -y -qq libreoffice-impress fonts-noto-cjk 2>/dev/null || true

echo "==> [4/4] 校验"
python3 - <<'PY'
mods = {}
try:
    import fitz; mods["pymupdf"] = getattr(fitz, "__version__", "ok")
except Exception as e:
    mods["pymupdf"] = f"FAIL: {e}"
try:
    import pptx; mods["python-pptx"] = pptx.__version__
except Exception as e:
    mods["python-pptx"] = f"FAIL: {e}"
try:
    import PIL; mods["pillow"] = PIL.__version__
except Exception as e:
    mods["pillow"] = f"FAIL: {e}"
for k, v in mods.items():
    print(f"  {k}: {v}")
PY
command -v pdftotext >/dev/null 2>&1 && echo "  pdftotext: ok" || echo "  pdftotext: 缺失"
command -v soffice >/dev/null 2>&1 && echo "  libreoffice: ok" || echo "  libreoffice: 未安装（PPT 预览将跳过）"

echo "==> 环境就绪"
