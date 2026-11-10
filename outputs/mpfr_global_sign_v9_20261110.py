"""Certify D_j < 0 on every power 3000--6000 W and all ten input axes.

Uses twelve closed 250 W slabs and a 2^4 shared-input grid.  We need only
the upper bound: P's lower flow is at Q_low, M's upper flow is at Q_high.
Power monotonicity, root windows and residual-axis signs are rechecked on
the six parent 500 W slabs before any bound is reported.  The child slabs
are subsets, so those sign certificates apply unchanged.  The four M-only
axes are pinned to the D_j-maximising endpoints by v7/v8 certificates.
"""

from __future__ import annotations

import itertools
import sys
import time

import core_v2 as C
import mpfr_centered_bound_v8_20261110 as B
import mpfr_global_bound_v9_20261110 as G
import mpfr_interval_v7_20261109 as M


def upper_slab(qlo, qhi, parent, steps):
    base = B.source_box()
    cells = []
    for name in B.SHARED:
        v = base[name]
        mid = (v.lo + v.hi) / 2
        cells.append((M.J(v.lo, mid), M.J(mid, v.hi)))
    upper = M.mp(-1e99)
    for joint in itertools.product(*cells):
        x = dict(base)
        x.update(dict(zip(B.SHARED, joint)))
        xmax = dict(x)
        for name in B.MONO_M:
            v = xmax[name]
            xmax[name] = M.J(v.lo if B.SIGNS[name] < 0 else v.hi)
        p_lo = G.edge('P', qlo, x, -1, G.WINDOWS[parent]['P'], steps)
        m_hi = G.edge('M', qhi, xmax, +1, G.WINDOWS[parent]['M'], steps)
        bound = ((M.J(m_hi) / M.J(p_lo)) / M.J(C.A_R) - M.J(1)).hi
        upper = max(upper, bound)
    print('UPPER', qlo, qhi, f'{float(upper)*100:.9f}',
          'pct; width', qhi - qlo, 'W', flush=True)
    return upper


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    started = time.monotonic()
    G.verify_power_sign()
    for parent in range(6):
        G.verify_slab(parent)
    global_hi = M.mp(-1e99)
    for parent in range(6):
        a, b = G.SLABS[parent]
        mid = (a + b) // 2
        for qlo, qhi in ((a, mid), (mid, b)):
            global_hi = max(global_hi, upper_slab(qlo, qhi, parent, steps))
    # Rounded public threshold is deliberately looser than the MPFR bound.
    assert global_hi < M.mp(-0.00136), global_hi
    print('CERTIFIED_FULL_WINDOW_DJ_NEGATIVE',
          f'MPFR_display={float(global_hi)*100:.9f} %',
          'D_j < -0.136 % (outward public threshold)',
          'over Q in [3000,6000] W and all ten input axes;',
          'elapsed_s', round(time.monotonic() - started, 2), flush=True)


if __name__ == '__main__':
    main()
