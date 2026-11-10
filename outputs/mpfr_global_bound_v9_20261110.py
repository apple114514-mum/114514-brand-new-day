"""MPFR outer bound for D_j on all ten axes and continuous 3--6 kW.

The six candidate mass windows are independently checked by directed
residual signs.  Residual partial-derivative signs are checked on a finite
no-gap cover of every window and power slab.  Four shared axes are gridded
together for P and M; four M-only axes use proved endpoint signs.  Each slab
uses Q_lo for the lower flow and Q_hi for the upper flow.  The pairing loses
same-Q correlation, so the result is an outer bound, never a found extremum.
All original Python binary64 constants remain the frozen source model.
"""

from __future__ import annotations

import itertools
import sys
import time

import core_v2 as C
import factored_interval_v7_20261109 as V
import mpfr_centered_bound_v8_20261110 as B
import mpfr_derivative_v7_20261109 as D
import mpfr_interval_v7_20261109 as M


SLABS = [(3000 + j * 500, 3500 + j * 500) for j in range(6)]
# These are merely candidates. verify_slab() proves every endpoint sign.
WINDOWS = [
    {'P': (.550, .700), 'M': (.180, .252)},
    {'P': (.585, .735), 'M': (.195, .266)},
    {'P': (.615, .765), 'M': (.205, .278)},
    {'P': (.640, .795), 'M': (.215, .289)},
    {'P': (.665, .825), 'M': (.225, .300)},
    {'P': (.690, .850), 'M': (.233, .310)},
]


def verify_power_sign():
    D.activate()
    x = {n: D.D(M.J(*iv)) for n, iv in zip(C.NAMES, C.BOUNDS)}
    for side, win in (('P', (.55, .85)), ('M', (.18, .31))):
        lo, hi = M.mp(1e99), M.mp(-1e99)
        for j in range(12):
            a = win[0] + (win[1] - win[0]) * j / 12
            b = win[0] + (win[1] - win[0]) * (j + 1) / 12
            f, *_ = V.interval_residual(
                side, D.D(M.J(a, b)), D.D(M.J(3000, 6000), M.J(1)), x)
            lo, hi = min(lo, f.d.lo), max(hi, f.d.hi)
        assert lo > 0, (side, lo, hi)
        print('POWER_SIGN', side, float(lo), float(hi), flush=True)


def verify_slab(j):
    qlo, qhi = SLABS[j]
    x = B.source_box()
    for side, (mlo, mhi) in WINDOWS[j].items():
        flo = B.residual_extreme(side, M.mp(mlo), qlo, x, -1)
        fhi = B.residual_extreme(side, M.mp(mhi), qhi, x, 1)
        assert flo > 0 and fhi < 0, (j, side, flo, fhi)
        print('ROOT_WINDOW', j, side, mlo, mhi,
              float(flo), float(fhi), flush=True)

        for name in B.SHARED:
            parts = 2 if side == 'M' and name == 'u_loss_fac' else 1
            low, high = M.mp(1e99), M.mp(-1e99)
            for eidx in range(parts):
                y = B.source_box()
                if parts > 1:
                    y['eps_M'] = M.J(10 * eidx, 10 * (eidx + 1))
                dy = {n: D.D(v) for n, v in y.items()}
                dy[name] = D.D(y[name], M.J(1))
                for k in range(8):
                    a = mlo + (mhi - mlo) * k / 8
                    b = mlo + (mhi - mlo) * (k + 1) / 8
                    f, *_ = V.interval_residual(
                        side, D.D(M.J(a, b)),
                        D.D(M.J(qlo, qhi)), dy)
                    low, high = min(low, f.d.lo), max(high, f.d.hi)
            assert high < 0 if B.SIGNS[name] < 0 else low > 0, (
                j, side, name, low, high)
            print('PARAM_SIGN', j, side, name,
                  float(low), float(high), flush=True)


def edge(side, q, x, want, win, steps):
    lo, hi = map(M.mp, win)
    for _ in range(steps):
        mid = (lo + hi) / 2
        f = B.residual_extreme(side, mid, q, x, want)
        if want < 0:
            if f > 0:
                lo = mid
            else:
                hi = mid
        elif f < 0:
            hi = mid
        else:
            lo = mid
    return lo if want < 0 else hi


def run_slab(j, k, steps):
    qlo, qhi = SLABS[j]
    base = B.source_box()
    cuts = {}
    for name in B.SHARED:
        v = base[name]
        ends = [v.lo] + [v.lo + (v.hi - v.lo) * z / k
                             for z in range(1, k)] + [v.hi]
        cuts[name] = [M.J(ends[z], ends[z + 1]) for z in range(k)]

    glo, ghi = M.mp(1e9), M.mp(-1e9)
    started = time.monotonic()
    for n, joint in enumerate(itertools.product(
            *(cuts[name] for name in B.SHARED)), 1):
        x = dict(base)
        x.update(dict(zip(B.SHARED, joint)))
        plo = edge('P', qlo, x, -1, WINDOWS[j]['P'], steps)
        phi = edge('P', qhi, x, +1, WINDOWS[j]['P'], steps)
        xmin, xmax = dict(x), dict(x)
        for name in B.MONO_M:
            v = x[name]
            xmin[name] = M.J(v.hi if B.SIGNS[name] < 0 else v.lo)
            xmax[name] = M.J(v.lo if B.SIGNS[name] < 0 else v.hi)
        mlo = edge('M', qlo, xmin, -1, WINDOWS[j]['M'], steps)
        mhi = edge('M', qhi, xmax, +1, WINDOWS[j]['M'], steps)
        dlo = ((M.J(mlo) / M.J(phi)) / M.J(C.A_R) - M.J(1)).lo
        dhi = ((M.J(mhi) / M.J(plo)) / M.J(C.A_R) - M.J(1)).hi
        glo, ghi = min(glo, dlo), max(ghi, dhi)
        if n % 64 == 0:
            print('PROGRESS', j, n, 'of', k**4,
                  round(time.monotonic() - started, 1), flush=True)
    print('SLAB_BOUND', qlo, qhi, k, steps,
          f'[{float(glo)*100:.8f},{float(ghi)*100:.8f}]',
          'width_pp', float(ghi - glo)*100,
          'seconds', round(time.monotonic() - started, 1), flush=True)
    return glo, ghi


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    verify_power_sign()
    for j in range(6):
        verify_slab(j)
    total_lo, total_hi = M.mp(1e9), M.mp(-1e9)
    for j in range(6):
        lo, hi = run_slab(j, k, steps)
        total_lo, total_hi = min(total_lo, lo), max(total_hi, hi)
    print('GLOBAL_BOUND 3000 6000', k, steps,
          f'[{float(total_lo)*100:.8f},{float(total_hi)*100:.8f}]',
          'width_pp', float(total_hi - total_lo)*100, flush=True)


if __name__ == '__main__':
    main()
