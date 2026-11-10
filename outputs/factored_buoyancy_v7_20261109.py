"""Verify exact cancellation of the common density intercept in buoyancy."""

import itertools
import math

import core_v2 as C


def means_of(loop,m,q,ti,kw,state):
    segs=loop['segs']
    ic=next(i for i,s in enumerate(segs) if s['cool'])
    means=[0.]*len(segs)
    t=ti
    for i in range(ic):
        s=segs[i];L=s['L']*(kw.get('lhs_scale',1.) if i==0 else 1.)
        heat=q*s['qfrac']/L if s['qfrac'] else 0.
        u=s['u']*kw['u_fac'];cp=C.cp_of(t,kw['fcp']);a=u*L/(m*cp)
        if a>1e-12:
            teq=C.T_AMB+heat/u
            e=math.exp(-a)
            tnew=teq+(t-teq)*e
            means[i]=teq+(t-teq)*(-math.expm1(-a))/a
        else:
            tnew=t+heat*L/(m*cp);means[i]=(t+tnew)/2
        t=tnew
    t=ti
    for i in range(len(segs)-1,ic,-1):
        s=segs[i];u=s['u']*kw['u_fac'];cp=C.cp_of(t,kw['fcp'])
        a=u*s['L']/(m*cp)
        if a>1e-12:
            means[i]=C.T_AMB+(t-C.T_AMB)*math.expm1(a)/a
            t=C.T_AMB+(t-C.T_AMB)*math.exp(a)
        else:means[i]=t
    means[ic]=0.5*(state['t_ci']+state['t_co'])
    return means


def main():
    for q in (3000.,6000.):
        for side in ('P','M'):
            max_diff=0.;ratio_lo=math.inf;ratio_hi=0.
            for bits in itertools.product((0,1),repeat=len(C.NAMES)):
                x=[C.BOUNDS[i][bit] for i,bit in enumerate(bits)]
                roots=C.fom(x,q)
                state=roots['rp' if side=='P' else 'rm']
                kwp,kwm=C.kw_from_vec(x)
                kw=kwp if side=='P' else kwm
                ti=C.T_IN_REF+kw.pop('dtin')
                loop=C.P if side=='P' else C.M
                means=means_of(loop,state['m'],q,ti,kw,state)
                # The cooler has zero dz; only heated/passive means matter.
                z=sum(t*s['dz'] for t,s in zip(means,loop['segs']))
                new=C.G*1.293*kw['frho']*z
                old=state['dp_buoy']
                max_diff=max(max_diff,abs(new-old))
                base=[C.rho_of(t) for t in means]
                naive=(1.008-.992)*C.G*sum(abs(r*s['dz']) for r,s in zip(base,loop['segs']))
                factored=(1.008-.992)*C.G*1.293*abs(z)
                ratio=naive/factored
                ratio_lo=min(ratio_lo,ratio);ratio_hi=max(ratio_hi,ratio)
            print(f'{q/1000:g} kW {side}: max exact-form disagreement '
                  f'{max_diff:.4g} Pa; naive/factored density-axis '
                  f'interval-width ratio {ratio_lo:.1f}..{ratio_hi:.1f}')


if __name__=='__main__':main()
