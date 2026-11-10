"""Outward transfer from fixed-power D_j and R_H logs to bulk D_T.

Displayed log endpoints are rounded.  We expand them by 1e-6 percentage
point for D_j and 1e-6 dimensionless for R_H before Decimal arithmetic,
then round the answer outward to 0.01 percentage point.
"""

from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, getcontext
from pathlib import Path
import re

getcontext().prec=50
HERE=Path(__file__).resolve().parent


def read_bounds(q):
    f=(HERE/f'mpfr_centered_bound_v8_{q}k4.log').read_text()
    m=re.search(r'CERTIFIED D_j fixed-power outer .*?\[([^,]+),([^\]]+)\] %',f)
    assert m
    dj=(D(m.group(1))-D('.000001'),D(m.group(2))+D('.000001'))
    r=(HERE/'mpfr_heater_ratio_v8_20261110.log').read_text()
    m=re.search(rf'CERTIFIED R_H, Q={q} W: .*?R_H=\[([^,]+),([^\]]+)\]',r)
    assert m
    rh=(D(m.group(1))-D('.000001'),D(m.group(2))+D('.000001'))
    return dj,rh


def main():
    cent=D('.01')
    for q in (3000,4300,6000):
        (dl,dh),(rl,rh)=read_bounds(q)
        lower=(rl/(D(1)+dh/D(100))-D(1))*D(100)
        upper=(rh/(D(1)+dl/D(100))-D(1))*D(100)
        outward=(lower.quantize(cent,rounding=ROUND_FLOOR),
                 upper.quantize(cent,rounding=ROUND_CEILING))
        print(q,'D_j printed widened',dl,dh,'R_H printed widened',rl,rh,
              'CERTIFIED D_T bulk pct',outward)


if __name__=='__main__':main()
