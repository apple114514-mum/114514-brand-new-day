"""Continuous-power outer enclosure for the heater bulk-rise FoM.

This transfers the already certified v9 slabwise mass-flux bounds through
the exact heater-energy identity.  It uses directed MPFR intervals for the
heater losses and retains the common Q in the expression

    Qnet_M/Qnet_P = 1 + (loss_P-loss_M)/(Q-loss_P).

The printed v9 D_j endpoints are widened by 1e-6 percentage point before
use.  This is greater than their 8-decimal-place display rounding error.
"""

from __future__ import annotations

from pathlib import Path
import re

import mpfr_centered_bound_v8_20261110 as B
import mpfr_global_bound_v9_20261110 as G
import mpfr_interval_v7_20261109 as M
import core_v2 as C


HERE = Path(__file__).resolve().parent
DISPLAY_WIDEN_PP = M.mp('0.000001')


def heater(side, q, m, x):
    """Directed version of the v8 heater with interval common power."""
    seg = (C.P if side == 'P' else C.M)['segs'][0]
    length = M.J(seg['L']) * (x['L_HS_M'] if side == 'M' else M.J(1))
    inlet = M.J(C.T_IN_REF) + x['dTin_' + side]
    u = M.J(seg['u']) * x['u_loss_fac']
    cp = M.cp_iv(inlet, x['cp_fac'])
    a = u * length / (m * cp)
    mean = M.J(C.T_AMB) + (inlet - M.J(C.T_AMB)) * M.phi_iv(a) + (
        q / (m * cp)) * M.psi_iv(a)
    return u * length * (mean - M.J(C.T_AMB)), M.cp_iv(inlet, M.J(1))


def read_dj_slab_bounds():
    source = (HERE / 'mpfr_global_bound_v9_k4_20261110.log').read_text()
    result = {}
    pattern = r'SLAB_BOUND (\d+) (\d+) 4 12 \[([^,]+),([^\]]+)\]'
    for match in re.finditer(pattern, source):
        loq, hiq = int(match[1]), int(match[2])
        lo = (M.mp(match[3]) - DISPLAY_WIDEN_PP) / M.mp(100)
        hi = (M.mp(match[4]) + DISPLAY_WIDEN_PP) / M.mp(100)
        result[(loq, hiq)] = M.J(lo, hi)
    assert set(result) == set(G.SLABS), result
    return result


def continuous_temperature_bound():
    G.verify_power_sign()
    source = B.source_box()
    dj_bounds = read_dj_slab_bounds()
    glo, ghi = M.mp(100), M.mp(-100)
    for j, (qlo, qhi) in enumerate(G.SLABS):
        G.verify_slab(j)
        roots = {}
        for side in ('P', 'M'):
            window = G.WINDOWS[j][side]
            left = G.edge(side, qlo, source, -1, window, 18)
            right = G.edge(side, qhi, source, +1, window, 18)
            roots[side] = M.J(left, right)
        q = M.J(qlo, qhi)
        loss_p, cp_p = heater('P', q, roots['P'], source)
        loss_m, cp_m = heater('M', q, roots['M'], source)
        net_p = q - loss_p
        assert net_p.lo > 0, (j, net_p)
        rh = (M.J(1) + (loss_p - loss_m) / net_p) * (cp_p / cp_m)
        dj = dj_bounds[(qlo, qhi)]
        assert (M.J(1) + dj).lo > 0
        dt = rh / (M.J(1) + dj) - M.J(1)
        glo, ghi = min(glo, dt.lo), max(ghi, dt.hi)
        print('SLAB', qlo, qhi, 'root_P', roots['P'], 'root_M', roots['M'],
              'R_H', rh, 'D_j', dj, 'D_T_percent',
              f'[{float(dt.lo)*100:.8f},{float(dt.hi)*100:.8f}]', flush=True)
    print('CONTINUOUS_BULK_TEMPERATURE_OUTER',
          f'[{float(glo)*100:.8f},{float(ghi)*100:.8f}] percent',
          'Q=[3000,6000]W; all ten frozen input axes', flush=True)
    return glo, ghi


if __name__ == '__main__':
    continuous_temperature_bound()
