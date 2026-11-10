"""Exploratory power trend at all ten-axis corners; NOT a certificate."""

import itertools
import time

import numpy as np

import core_v2 as C


def main():
    started = time.monotonic()
    bounds = np.asarray(C.BOUNDS, dtype=float)
    low = (float('inf'), None)
    high = (-float('inf'), None)
    reversals = 0
    for index, bits in enumerate(itertools.product((0, 1), repeat=len(C.NAMES))):
        x = bounds[np.arange(len(bits)), bits]
        values = [C.d_j_of(x, q) for q in (3000, 4300, 6000)]
        if not (values[0] < values[1] < values[2]):
            reversals += 1
        delta = values[-1] - values[0]
        if delta < low[0]:
            low = (delta, index, bits, values)
        if delta > high[0]:
            high = (delta, index, bits, values)
    print('CORNER_POWER_TREND 1024 corners, Q=3000/4300/6000 W')
    print('three-point reversals', reversals)
    print('minimum D_j(6000)-D_j(3000) in percentage points:', low)
    print('maximum D_j(6000)-D_j(3000) in percentage points:', high)
    print('elapsed_s', round(time.monotonic() - started, 2))
    print('SEARCH ONLY: three Q values and corners do not prove monotonicity.')


if __name__ == '__main__':
    main()
