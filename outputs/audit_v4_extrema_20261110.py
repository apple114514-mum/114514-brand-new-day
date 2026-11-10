"""Numerical challenge to v4's extrapolated claim about missed extrema.

This is a search, not a continuous-domain certificate.  It uses C.fom so
both inlet-temperature perturbations enter before C.solve is called.
"""

import itertools
import time

import numpy as np
from scipy.optimize import differential_evolution

import core_v2 as C


def main():
    bounds=C.BOUNDS
    for q in (3000.,4300.,6000.):
        start=time.monotonic()
        corners=[]
        for bits in itertools.product((0,1),repeat=len(bounds)):
            x=np.array([bounds[i][b] for i,b in enumerate(bits)])
            corners.append((C.fom(x,q)['d_j'],bits))
        mincorner=min(corners);maxcorner=max(corners)
        print('power',q,'corner min',mincorner,'corner max',maxcorner,
              'seconds',round(time.monotonic()-start,2),flush=True)
        for sign in (1,-1):
            def objective(x):return sign*C.fom(x,q)['d_j']
            res=differential_evolution(objective,bounds,seed=20261110,
                                       popsize=5,maxiter=100,tol=1e-10,
                                       polish=True,workers=1)
            print('power',q,'sign',sign,'DE D_j',sign*res.fun,
                  'evaluations',res.nfev,'x',res.x.tolist(),
                  'success',res.success,'seconds',round(time.monotonic()-start,2),
                  flush=True)


if __name__=='__main__':main()
