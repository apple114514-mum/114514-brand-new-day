#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf2txt.py —— 把 PDF 抽成带页码锚的纯文本，供不能联网的推理链阅读。

用法：
    python pdf2txt.py 文献原文/xxx.pdf [更多.pdf ...]
    python pdf2txt.py --dir 文献原文

输出：
    文献文本/<key>.txt，每页开头一行 [[pN]]，便于引用时锚定页码。
    同时打印每页字符数；某页 < 40 字符会标 EMPTY_PAGE（多为扫描件）。

只依赖 pypdf；没有 pypdf 时尝试 pdftotext。两者都没有就报错退出，不静默降级。
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

MIN_CHARS = 40


def extract_pypdf(path):
    try:
        import pypdf
    except ImportError:
        return None
    reader = pypdf.PdfReader(str(path))
    return [(p.extract_text() or '') for p in reader.pages]


def extract_pdftotext(path):
    if not shutil.which('pdftotext'):
        return None
    out = subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', str(path), '-'],
                         capture_output=True)
    if out.returncode != 0:
        return None
    return out.stdout.decode('utf-8', 'replace').split('\f')


def write_marked(pages, dst, src_name):
    lines = []
    bad = []
    for i, txt in enumerate(pages, 1):
        txt = (txt or '').replace('\r\n', '\n').strip('\n')
        lines.append('[[p%d]]' % i)
        lines.append(txt)
        lines.append('')
        if len(txt.strip()) < MIN_CHARS:
            bad.append(i)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text('\n'.join(lines), encoding='utf-8')
    total = sum(len(t or '') for t in pages)
    print('  %-44s %3d 页 %7d 字符 -> %s' % (src_name, len(pages), total, dst.name))
    if bad:
        print('    EMPTY_PAGE: %s（多为扫描件，需人工核图像页，不得凭印象补）'
              % ','.join('p%d' % b for b in bad))
    return len(pages), total, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdfs', nargs='*')
    ap.add_argument('--dir', default=None, help='批量处理该目录下所有 .pdf')
    ap.add_argument('--outdir', default='文献文本')
    ap.add_argument('--engine', choices=['auto', 'pypdf', 'pdftotext'], default='auto')
    a = ap.parse_args()

    targets = [Path(p) for p in a.pdfs]
    if a.dir:
        targets += sorted(Path(a.dir).glob('*.pdf'))
    if not targets:
        ap.error('没有输入文件')

    outdir = Path(a.outdir)
    if not outdir.is_absolute():
        # 以输入 PDF 的父目录的父目录为基准，保证 文献原文/ 与 文献文本/ 同级
        base = targets[0].resolve().parent
        if base.name in ('文献原文', 'pdfs', 'papers'):
            base = base.parent
        outdir = base / a.outdir

    engine = a.engine
    if engine == 'auto':
        try:
            import pypdf  # noqa: F401
            engine = 'pypdf'
        except ImportError:
            engine = 'pdftotext' if shutil.which('pdftotext') else ''

    rc = 0
    for pdf in targets:
        if not pdf.exists():
            print('  缺文件：%s' % pdf)
            rc = 2
            continue
        pages = extract_pypdf(pdf) if engine == 'pypdf' else None
        if pages is None and engine != 'pdftotext':
            pages = extract_pdftotext(pdf)
        if pages is None:
            print('  无法解析：%s（缺 pypdf 与 pdftotext）' % pdf)
            rc = 3
            continue
        _, _, bad = write_marked(pages, outdir / (pdf.stem + '.txt'), pdf.name)
        if bad:
            rc = max(rc, 1)

    print()
    print('引擎：%s；输出目录：%s' % (engine or '无', outdir))
    return rc


if __name__ == '__main__':
    sys.exit(main())
