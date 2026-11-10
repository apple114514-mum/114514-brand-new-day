"""Reproduce the active v5 interval-kernel truncation counterexample.

The input is the user-supplied v5_all_code_2026-11-10.zip in this directory.
It is treated as data; the original files are extracted only to a temporary
directory, with no changes to the user's archive.  MPFR 256-bit arithmetic
is used to evaluate the exact transcendental definitions at an endpoint
that the original v5 slab_window() actually passes to di_mean_ratio().
"""

from __future__ import annotations

import importlib
import math
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import gmpy2 as g


HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / 'v5_all_code_2026-11-10.zip'
PREFIX = 'v5_all_code_2026-11-10/'
NEEDED = ('v4_bound/core_v2.py', 'v4_bound/ivcore.py',
          'v4_bound/bound.py', 'v5_global/gbound.py')


def exact(a):
    with g.context(g.get_context(), precision=256):
        aa = g.mpfr(a)  # exact binary64 input used by the v5 kernel
        ee = g.exp(-aa)
        ww = -g.expm1(-aa)
        value = 1 / ww - 1 / aa
        derivative = 1 / (aa * aa) - ee / (ww * ww)
    return value, derivative


def main():
    with TemporaryDirectory() as tmp:
        p = Path(tmp)
        with ZipFile(ARCHIVE) as z:
            assert z.testzip() is None
            for name in NEEDED:
                data = z.read(PREFIX + name)
                dst = p / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(data)
        sys.path[:0] = [str(p / 'v5_global'), str(p / 'v4_bound')]
        I = importlib.import_module('ivcore')
        G = importlib.import_module('gbound')
        old = I.di_mean_ratio
        endpoints = []

        def record(arg):
            endpoints.extend((arg.v.lo, arg.v.hi))
            return old(arg)

        I.di_mean_ratio = record
        for qlo, qhi in G.SLABS:
            G.slab_window(qlo, qhi)
        a = max(endpoints)
        iv = I.di_mean_ratio(I.DI.seed(I.Iv(a)))
        true_value, true_derivative = exact(a)
        v_miss = float(g.mpfr(iv.v.lo) - true_value)
        d_miss = float(g.mpfr(iv.d.lo) - true_derivative)
        print('active_endpoint_a', repr(a), 'calls', len(endpoints))
        print('value_lower_minus_true', v_miss,
              'true_inside', iv.v.lo <= true_value <= iv.v.hi)
        print('derivative_lower_minus_true', d_miss,
              'true_inside', iv.d.lo <= true_derivative <= iv.d.hi,
              'error_ulps', d_miss / math.ulp(iv.d.lo))
        assert v_miss > 0 and d_miss > 0
        print('COUNTEREXAMPLE: both original v5 intervals miss exact values')


if __name__ == '__main__':
    main()
