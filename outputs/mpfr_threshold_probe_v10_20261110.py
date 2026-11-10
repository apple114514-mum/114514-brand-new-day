"""Direct 3%-threshold diagnostic for the worst 250 W slab.

For P root m_P and t=0.97*A_R*m_P, F_M(t)<0 is equivalent to
m_M<t, because F_M is strictly decreasing in m on the accepted root
interval.  The result is diagnostic: cells with an interval upper F_M>=0
are undecided, not counterexamples to the desired inequality.
"""

from __future__ import annotations

import itertools
import time

import core_v2 as C
import mpfr_centered_bound_v8_20261110 as B
import mpfr_global_bound_v9_20261110 as G
import mpfr_interval_v7_20261109 as M


def main():
    qlo, qhi, parent, k, steps = 5750, 6000, 5, 4, 14
    started = time.monotonic()
    G.verify_power_sign()
    G.verify_slab(parent)
    base = B.source_box()
    cut = []
    for name in B.SHARED:
        v = base[name]
        edges = [v.lo + (v.hi-v.lo)*i/k for i in range(k+1)]
        cut.append([M.J(edges[i], edges[i+1]) for i in range(k)])
    decided, undecided = 0, 0
    worst = M.mp(-1e99)
    for joint in itertools.product(*cut):
        x = dict(base)
        x.update(dict(zip(B.SHARED, joint)))
        xm = dict(x)
        for name in B.MONO_M:
            v = xm[name]
            xm[name] = M.J(v.lo if B.SIGNS[name]<0 else v.hi)
        p_lo = G.edge('P',qlo,x,-1,G.WINDOWS[parent]['P'],steps)
        t = (M.J('0.97')*M.J(C.A_R)*M.J(p_lo)).lo
        upper_f = B.residual_extreme('M',t,qhi,xm,+1)
        worst = max(worst, upper_f)
        decided += upper_f<0
        undecided += upper_f>=0
    print('DIRECT_THRESHOLD',qlo,qhi,'W',k**4,'cells',
          'certified_below_minus_3pct',decided,'undecided',undecided,
          'max_residual_upper_Pa',float(worst),
          'elapsed_s',round(time.monotonic()-started,2))
    assert decided == 16 and undecided == 240


if __name__=='__main__':
    main()
