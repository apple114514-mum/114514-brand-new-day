"""Certified local sign counterexample for a universal shared-axis lemma.

The old core is used only to select two candidate corners.  Each root is
independently bracketed using 128-bit directed MPFR intervals.  Interval AD
and the implicit function theorem then enclose the exact derivative of the
mass-flux FoM at each corner.
"""

import itertools
import sys

import numpy as np

import core_v2 as C
import factored_interval_v7_20261109 as V
import mpfr_interval_v7_20261109 as M
import mpfr_derivative_v7_20261109 as D


def root_box(side,values,q):
    M.activate()
    x={n:M.J(v) for n,v in zip(C.NAMES,values)}
    lo,hi=((M.mp(.4),M.mp(1.15)) if side=='P' else
           (M.mp(.15),M.mp(.32)))
    fl,*_=V.interval_residual(side,M.J(lo),M.J(q),x)
    fh,*_=V.interval_residual(side,M.J(hi),M.J(q),x)
    assert fl.lo>0 and fh.hi<0,(side,fl,fh)
    for _ in range(46):
        mid=(lo+hi)/2
        f,*_=V.interval_residual(side,M.J(mid),M.J(q),x)
        if f.lo>0:lo=mid
        elif f.hi<0:hi=mid
        else:break
    return M.J(lo,hi)


def log_root_sensitivity(side,values,q,name,m):
    D.activate()
    x={n:D.D(M.J(v)) for n,v in zip(C.NAMES,values)}
    qd=D.D(M.J(q))
    fm,*_=V.interval_residual(side,D.D(m,M.J(1)),qd,x)
    x[name]=D.D(x[name].v,M.J(1))
    fx,*_=V.interval_residual(side,D.D(m),qd,x)
    assert fm.d.hi<0,(side,fm.d)
    return -fx.d/(m*fm.d)


def main():
    q=6000.
    i=C.IDX['u_loss_fac']
    found={1:None,-1:None}
    for bits9 in itertools.product((0,1),repeat=9):
        bits=list(bits9);bits.insert(i,0)
        xlo=[C.BOUNDS[k][b] for k,b in enumerate(bits)]
        bits[i]=1
        xhi=[C.BOUNDS[k][b] for k,b in enumerate(bits)]
        diff=C.fom(np.array(xhi),q)['d_j']-C.fom(np.array(xlo),q)['d_j']
        direction=1 if diff>0 else -1
        if (found[direction] is None or
            (direction>0 and diff>found[direction][2]) or
            (direction<0 and diff<found[direction][2])):
            found[direction]=(xlo,tuple(bits9),diff)
    for direction,(values,bits9,diff) in found.items():
        p=root_box('P',values,q)
        m=root_box('M',values,q)
        sp=log_root_sensitivity('P',values,q,'u_loss_fac',p)
        sm=log_root_sensitivity('M',values,q,'u_loss_fac',m)
        dln=sm-sp
        print('direction',direction,'other_bits',bits9,
              'finite_corner_difference_pp',diff)
        print('P root',p,'M root',m)
        print('dln(mP)/du',sp,'dln(mM)/du',sm,
              'dln(mM/mP)/du',dln)
        print('signed derivative interval',float(dln.lo),float(dln.hi))
        assert (dln.lo>0 if direction>0 else dln.hi<0)
    print('CERTIFIED: the shared heat-loss axis has both local derivative signs.')


if __name__=='__main__':main()
