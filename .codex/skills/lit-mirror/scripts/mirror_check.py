#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mirror_check.py —— 文献镜像审计。退出码 0 才算过。

检查四件事：
  1. claims.csv 每行的 evidence 指针能否落到一个真实存在的 文献文本/<key>.txt
  2. 每个 文献原文/<key>.pdf 是否有同名 文献文本/<key>.txt
  3. 每个 .txt 是否有 [[pN]] 页码锚
  4. claims.csv 的 grade 是否只用 L1/L2/L3/L4

用法：
    python mirror_check.py <工作区根目录>

缺件清单会打印在最后 —— 那张清单就是下一张取件单。
"""
import csv
import re
import sys
from pathlib import Path

GRADES = {'L1', 'L2', 'L3', 'L4'}
KEY_RE = re.compile(r'[（(\s]*([A-Za-z][A-Za-z0-9_\-]{2,})')


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    pdfs = {p.stem: p for p in (root / '文献原文').glob('*.pdf')}
    txts = {p.stem: p for p in (root / '文献文本').glob('*.txt')}
    anchors = {}
    claims = root / 'claims.csv'

    problems = []

    # 2. pdf <-> txt 配对
    for k in sorted(pdfs):
        if k not in txts:
            problems.append('PDF 无文本：%s.pdf（未抽文本，读者看不到）' % k)
    for k in sorted(txts):
        if k not in pdfs:
            problems.append('文本无 PDF：%s.txt（来源不可核）' % k)

    # 3. 页码锚
    for k, p in sorted(txts.items()):
        t = p.read_text(encoding='utf-8', errors='replace')
        nums = [int(n) for n in re.findall(r'^\[\[p(\d+)\]\]$', t, re.M)]
        anchors[k] = set(nums)
        if not nums:
            problems.append('无页码锚：%s.txt（无法回溯，重跑 pdf2txt.py）' % k)
        elif nums != list(range(1, len(nums) + 1)):
            problems.append('页码锚不连续：%s.txt' % k)
        if k in pdfs:
            try:
                from pypdf import PdfReader
                actual_pages = len(PdfReader(str(pdfs[k])).pages)
                if len(nums) != actual_pages:
                    problems.append('PDF/文本页数不一致：%s（PDF %d，文本 %d）'
                                    % (k, actual_pages, len(nums)))
            except ImportError:
                problems.append('缺 pypdf：无法核对 %s 的 PDF 页数' % k)

    # 1 + 4. claims.csv
    rows = 0
    if not claims.exists():
        problems.append('缺 claims.csv（断言—证据表）')
    else:
        with claims.open(encoding='utf-8-sig', newline='') as f:
            rd = csv.DictReader(f)
            if not rd.fieldnames or not {'claim', 'evidence', 'grade'} <= set(rd.fieldnames):
                problems.append('claims.csv 表头须含 claim,evidence,grade,gap')
            else:
                for i, r in enumerate(rd, 2):
                    rows += 1
                    g = (r.get('grade') or '').strip()
                    if g and g not in GRADES:
                        problems.append('claims.csv 第 %d 行 grade=%r 不在 L1..L4' % (i, g))
                    if not g:
                        problems.append('claims.csv 第 %d 行 grade 为空（未定级即未核）' % i)
                    ev = (r.get('evidence') or '').strip()
                    if not ev or '未核' in ev or '未找到' in ev:
                        continue
                    m = KEY_RE.search(ev)
                    if m:
                        key = m.group(1)
                        if key not in txts or key not in pdfs:
                            problems.append('claims.csv 第 %d 行证据指针 %r 无成对 PDF/文本'
                                            % (i, key))
                        else:
                            refs = [int(n) for n in re.findall(r'\[\[p(\d+)\]\]', ev)]
                            if not refs:
                                problems.append('claims.csv 第 %d 行缺 [[pN]] 页码锚' % i)
                            for page in refs:
                                if page not in anchors.get(key, set()):
                                    problems.append('claims.csv 第 %d 行 %s 的 [[p%d]] 不在文本中'
                                                    % (i, key, page))
                    else:
                        problems.append('claims.csv 第 %d 行证据指针缺文献键' % i)
                    if not re.search(r'\[\[p\d+\]\]', ev):
                        problems.append('claims.csv 第 %d 行证据无页码/表号/式号' % i)

    print('工作区：%s' % root)
    print('  PDF %d 个，文本 %d 个，断言 %d 条' % (len(pdfs), len(txts), rows))
    if problems:
        print()
        print('缺件 / 问题（%d）：' % len(problems))
        for p in problems:
            print('  - ' + p)
        print()
        print('=> 这张清单就是下一张取件单。')
        return 1
    print()
    print('OK：镜像完整，页码可回溯，定级合法。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
