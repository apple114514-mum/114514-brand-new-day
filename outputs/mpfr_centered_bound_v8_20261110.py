"""Independent fixed-power certificate using corner signs and centered T_in.

For each residual F_s, four shared-axis partial derivatives have fixed signs
on an independently certified broad root bracket.  Four M-only axes are
likewise signed (three analytically, heater length by MPFR AD).  The only
undetermined residual axis, heater inlet temperature, is enclosed by the
mean-value theorem around its midpoint.  Root signs then enclose each loop's
unique root.  Shared axes are kept in the SAME cell for both loops, reducing
the otherwise huge independent-quotient overestimation.

This does not assert the mass-flux ratio is monotone in the shared axes.
"""

import itertools
import sys
import time

import core_v2 as C
import factored_interval_v7_20261109 as V
import mpfr_derivative_v7_20261109 as D
import mpfr_interval_v7_20261109 as M


SHARED=('u_loss_fac','mu_fac','cp_fac','rho_fac')
MONO_M=('eps_M','d_hole','k_aux_M','L_HS_M')
SIGNS={'u_loss_fac':-1,'mu_fac':-1,'cp_fac':-1,'rho_fac':1,
       'eps_M':-1,'d_hole':1,'k_aux_M':-1,'L_HS_M':-1}
BRACKETS={3000:{'P':(.50,.70),'M':(.18,.25)},
          4300:{'P':(.60,.80),'M':(.21,.27)},
          6000:{'P':(.70,.90),'M':(.24,.31)}}


def source_box():
    return {n:M.J(*bounds) for n,bounds in zip(C.NAMES,C.BOUNDS)}


def verify_shared_signs(q):
    D.activate()
    for side,(mlo,mhi) in BRACKETS[q].items():
        for name in SHARED:
            rough_parts=2 if side=='M' and name=='u_loss_fac' and q>3000 else 1
            low=M.mp(1e99);high=M.mp(-1e99)
            for eidx in range(rough_parts):
                x=source_box()
                if rough_parts>1:
                    x['eps_M']=M.J(20*eidx/rough_parts,
                                   20*(eidx+1)/rough_parts)
                dx={n:D.D(v) for n,v in x.items()}
                dx[name]=D.D(x[name],M.J(1))
                for i in range(8):
                    m=D.D(M.J(mlo+(mhi-mlo)*i/8,
                                mlo+(mhi-mlo)*(i+1)/8))
                    f,*_=V.interval_residual(side,m,D.D(M.J(q)),dx)
                    low=min(low,f.d.lo);high=max(high,f.d.hi)
            print('F-axis',q,side,name,float(low),float(high),flush=True)
            assert (high<0 if SIGNS[name]<0 else low>0),(
                q,side,name,float(low),float(high))
    print('CERTIFIED all four shared F-axis signs at',q,'W',flush=True)


def verify_broad_brackets(q):
    M.activate()
    x=source_box()
    for side,(lo,hi) in BRACKETS[q].items():
        f1,*_=V.interval_residual(side,M.J(lo),M.J(q),x)
        f2,*_=V.interval_residual(side,M.J(hi),M.J(q),x)
        print('root bracket',q,side,float(f1.lo),float(f2.hi),flush=True)
        assert f1.lo>0 and f2.hi<0


def residual_extreme(side,m,q,x,which):
    """Rigorous F lower/upper with unknown inlet delta via MVT.

    which=-1 selects F minimum in the signed eight axes; +1 maximum.
    Derivative hull covers the active T_in interval, while all other axes
    are fixed at the selected F-extremizing corner of the current cell.
    """
    D.activate()
    active='dTin_P' if side=='P' else 'dTin_M'
    point={}
    for name,v in x.items():
        if name==active:continue
        if name in SIGNS and (side=='M' or name in SHARED):
            select_high=(SIGNS[name]*which>0)
            point[name]=M.J(v.hi if select_high else v.lo)
        else:point[name]=M.J(v.lo)
    ti=x[active]
    mid=(ti.lo+ti.hi)/2
    point[active]=M.J(mid)
    center={n:D.D(v) for n,v in point.items()}
    f0,*_=V.interval_residual(side,D.D(M.J(m)),D.D(M.J(q)),center)
    center[active]=D.D(ti,M.J(1))
    ft,*_=V.interval_residual(side,D.D(M.J(m)),D.D(M.J(q)),center)
    enclosure=f0.v+ft.d*M.J(ti.lo-mid,ti.hi-mid)
    return enclosure.lo if which<0 else enclosure.hi


def root_edge(side,q,x,which,steps):
    lo,hi=map(M.mp,BRACKETS[q][side])
    # For a lower root bound F_min>0 at lo; for an upper root bound
    # F_max<0 at hi.  The whole-box test above implies these signs.
    for _ in range(steps):
        mid=(lo+hi)/2
        f=residual_extreme(side,mid,q,x,which)
        if which<0:
            if f>0:lo=mid
            else:hi=mid
        else:
            if f<0:hi=mid
            else:lo=mid
    return lo if which<0 else hi


def main():
    q=int(sys.argv[1]) if len(sys.argv)>1 else 3000
    k=int(sys.argv[2]) if len(sys.argv)>2 else 2
    steps=int(sys.argv[3]) if len(sys.argv)>3 else 15
    if q not in BRACKETS:raise ValueError('q must be 3000, 4300, 6000')
    verify_broad_brackets(q)
    verify_shared_signs(q)
    base=source_box()
    cells=[]
    for name in SHARED:
        v=base[name]
        cuts=[v.lo]+[v.lo+(v.hi-v.lo)*i/k for i in range(1,k)]+[v.hi]
        cells.append([M.J(cuts[i],cuts[i+1]) for i in range(k)])
    global_low=M.mp(1e9);global_high=M.mp(-1e9)
    start=time.monotonic();n=0
    for joint in itertools.product(*cells):
        x=dict(base);x.update(dict(zip(SHARED,joint)))
        p_low=root_edge('P',q,x,-1,steps)
        p_high=root_edge('P',q,x,1,steps)
        xmin=dict(x);xmax=dict(x)
        for name in MONO_M:
            v=x[name]
            xmin[name]=M.J(v.hi if SIGNS[name]<0 else v.lo)
            xmax[name]=M.J(v.lo if SIGNS[name]<0 else v.hi)
        m_low=root_edge('M',q,xmin,-1,steps)
        m_high=root_edge('M',q,xmax,1,steps)
        low=((M.J(m_low)/M.J(p_high))/M.J(C.A_R)-M.J(1)).lo
        high=((M.J(m_high)/M.J(p_low))/M.J(C.A_R)-M.J(1)).hi
        global_low=min(global_low,low)
        global_high=max(global_high,high)
        n+=1
        if n%50==0:print('progress',q,k,n,'of',k**4,'sec',
                         round(time.monotonic()-start,1),flush=True)
    print('CERTIFIED D_j fixed-power outer',q,'W',k**4,'cells',
          f'[{float(global_low)*100:.8f},{float(global_high)*100:.8f}] %',
          'width_pp',float(global_high-global_low)*100,
          'seconds',round(time.monotonic()-start,1),flush=True)


if __name__=='__main__':main()
