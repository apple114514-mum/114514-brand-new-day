"""Certified, possibly conservative D_j range over the continuous design box.

Uses proven unique roots in I_P and I_M.  The three monotone M-only axes are
fixed at their signed endpoint combinations.  The remaining seven axes plus
the continuous power axis are divided into closed subboxes; interval residual
signs bound both roots in each subbox.  This avoids assuming an interior
extremum cannot occur.
"""

import itertools
import sys
import time

import core_v2 as C
import factored_interval_v7_20261109 as V
import mpfr_interval_v7_20261109 as M


AXES=[n for n in C.NAMES if n not in ('eps_M','d_hole','k_aux_M')]


def root_hull(side,x,q,steps=12):
    lo,hi=((M.mp(.4),M.mp(1.15)) if side=='P' else
           (M.mp(.15),M.mp(.32)))
    flo,*_=V.interval_residual(side,M.J(lo),q,x)
    fhi,*_=V.interval_residual(side,M.J(hi),q,x)
    assert flo.lo>0 and fhi.hi<0,(side,flo,fhi)
    a,b=lo,hi
    for _ in range(steps):
        mid=(a+b)/2
        f,*_=V.interval_residual(side,M.J(mid),q,x)
        if f.lo>0:a=mid
        else:b=mid
    lower=a
    a,b=lo,hi
    for _ in range(steps):
        mid=(a+b)/2
        f,*_=V.interval_residual(side,M.J(mid),q,x)
        if f.hi<0:b=mid
        else:a=mid
    assert lower<=b,(side,lower,b)
    return M.J(lower,b)


def split(iv):
    mid=(iv.lo+iv.hi)/2
    return (M.J(iv.lo,mid),M.J(mid,iv.hi))


def main():
    M.activate()
    levels=int(sys.argv[1]) if len(sys.argv)>1 else 1
    steps=int(sys.argv[2]) if len(sys.argv)>2 else 12
    if levels not in (0,1,2):raise ValueError('levels must be 0,1,2')
    assert len(AXES)==7 and len(C.NAMES)==10
    base=V.box_inputs(False)
    axis_intervals=[]
    for n in [*AXES,'Q']:
        orig=M.J(3000,6000) if n=='Q' else base[n]
        vals=[orig]
        for _ in range(levels):
            vals=[child for v in vals for child in split(v)]
        axis_intervals.append(vals)
    global_lower=M.mp(1e9);global_upper=M.mp(-1e9)
    count=0;start=time.monotonic()
    r=M.J(C.A_R)
    for cell in itertools.product(*axis_intervals):
        x=dict(base)
        for n,v in zip([*AXES,'Q'],cell):
            if n=='Q':q=v
            else:x[n]=v
        p=root_hull('P',x,q,steps)
        # D_j minimum: eps and auxiliary K high, hole diameter low.
        xmin=dict(x)
        xmin['eps_M']=M.J(C.BOUNDS[C.IDX['eps_M']][1])
        xmin['k_aux_M']=M.J(C.BOUNDS[C.IDX['k_aux_M']][1])
        xmin['d_hole']=M.J(C.BOUNDS[C.IDX['d_hole']][0])
        mmin=root_hull('M',xmin,q,steps)
        lower=((M.J(mmin.lo)/M.J(p.hi))/r-M.J(1)).lo
        global_lower=min(global_lower,lower)
        # D_j maximum: reverse the three monotone coordinates.
        xmax=dict(x)
        xmax['eps_M']=M.J(C.BOUNDS[C.IDX['eps_M']][0])
        xmax['k_aux_M']=M.J(C.BOUNDS[C.IDX['k_aux_M']][0])
        xmax['d_hole']=M.J(C.BOUNDS[C.IDX['d_hole']][1])
        mmax=root_hull('M',xmax,q,steps)
        upper=((M.J(mmax.hi)/M.J(p.lo))/r-M.J(1)).hi
        global_upper=max(global_upper,upper)
        count+=1
        if count%100==0:
            print(f'progress {count}/{2**(8*levels)}, '
                  f'bound=[{float(global_lower)*100:.4f},'
                  f'{float(global_upper)*100:.4f}] %, '
                  f'time={time.monotonic()-start:.1f}s',flush=True)
    print(f'CERTIFIED OUTER D_j, levels={levels}, boxes={count}, '
          f'root_bisection={steps}: '
          f'[{float(global_lower)*100:.8f}, '
          f'{float(global_upper)*100:.8f}] %, '
          f'seconds={time.monotonic()-start:.1f}')


if __name__=='__main__':main()
