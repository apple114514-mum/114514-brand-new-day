"""Full-box interval certificate for the fourth M-only mass-flux axis.

Requires the already proved F_M,m<0 and root existence in [0.15,0.32].
The M heater length multiplier enters the thermal and friction modules,
so its sign is established with automatic differentiation, not by a
component-only monotonicity argument.
"""

import math

import factored_interval_v7_20261109 as V
import mpfr_derivative_v7_20261109 as D
import mpfr_interval_v7_20261109 as M


def main():
    D.activate()
    x=V.box_inputs(False)
    x['L_HS_M']=D.D(x['L_HS_M'].v,M.J(1))
    q=D.D(M.J(3000,6000))
    low=math.inf;high=-math.inf
    for j in range(8):
        m=D.D(M.J(.15+(.32-.15)*j/8,
                    .15+(.32-.15)*(j+1)/8))
        f,*_=V.interval_residual('M',m,q,x)
        low=min(low,float(f.d.lo));high=max(high,float(f.d.hi))
        print(f'mass box {j}: dF/dL_HS_M = '
              f'[{float(f.d.lo):.9f},{float(f.d.hi):.9f}] Pa/m')
        assert f.d.hi<0
    print(f'CERTIFIED whole-box dF/dL_HS_M in '
          f'[{low:.9f},{high:.9f}] Pa/m; '
          f'm_M and D_j strictly decrease as L_HS_M increases')


if __name__=='__main__':main()
