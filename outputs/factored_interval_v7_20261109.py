"""Exploratory outward interval residual with factored LBE buoyancy.

Arithmetic is widened two ulps, exp/log/pow eight ulps.  This is an explicit
libm-error assumption, not a machine-independent transcendental certificate.
The goal is to learn whether algebraic factorization makes root signs usable.
"""

import math

import core_v2 as C


def down(x,n=2):
    for _ in range(n):x=math.nextafter(x,-math.inf)
    return x


def up(x,n=2):
    for _ in range(n):x=math.nextafter(x,math.inf)
    return x


class I:
    __slots__=('lo','hi')
    def __init__(self,lo,hi=None):
        self.lo=float(lo);self.hi=float(lo if hi is None else hi)
        assert math.isfinite(self.lo) and math.isfinite(self.hi) and self.lo<=self.hi,(lo,hi)
    def __repr__(self):return f'[{self.lo:.8g},{self.hi:.8g}]'
    @staticmethod
    def co(x):return x if isinstance(x,I) else I(x)
    def __add__(self,b):
        b=I.co(b);return I(down(self.lo+b.lo),up(self.hi+b.hi))
    __radd__=__add__
    def __neg__(self):return I(-self.hi,-self.lo)
    def __sub__(self,b):return self+(-I.co(b))
    def __rsub__(self,b):return I.co(b)+(-self)
    def __mul__(self,b):
        b=I.co(b)
        c=(self.lo*b.lo,self.lo*b.hi,self.hi*b.lo,self.hi*b.hi)
        return I(down(min(c)),up(max(c)))
    __rmul__=__mul__
    def reciprocal(self):
        assert self.lo>0 or self.hi<0,self
        return I(down(1/self.hi),up(1/self.lo))
    def __truediv__(self,b):return self*I.co(b).reciprocal()
    def __rtruediv__(self,b):return I.co(b)*self.reciprocal()
    def __pow__(self,a):
        assert self.lo>0,self
        if a<0:return (self**(-a)).reciprocal()
        return I(down(math.pow(self.lo,a),8),up(math.pow(self.hi,a),8))


def exp_iv(x):
    return I(down(math.exp(x.lo),8),up(math.exp(x.hi),8))


def log_iv(x):
    assert x.lo>0,x
    return I(down(math.log(x.lo),8),up(math.log(x.hi),8))


def scalar_phi(a):
    return -math.expm1(-a)/a


def scalar_psi(a):
    # ψ(a)=∫₀¹(1-t)exp(-at)dt; alternating series, a<0.1 here.
    assert 0<a<0.1,a
    return math.fsum((-a)**k/(math.factorial(k)*(k+1)*(k+2)) for k in range(13))


def phi_iv(a):
    assert a.lo>0,a
    return I(down(scalar_phi(a.hi),8),up(scalar_phi(a.lo),8))


def psi_iv(a):
    assert a.lo>0 and a.hi<0.1,a
    # Series remainder after k=12 is <a^13/(13!*14*15)<1e-27.
    return I(down(scalar_psi(a.hi),8),up(scalar_psi(a.lo),8))


def phi_neg_iv(a):
    assert a.lo>0,a
    return I(down(math.expm1(a.lo)/a.lo,8),up(math.expm1(a.hi)/a.hi,8))


def cp_iv(t,fac):
    assert 400<t.lo<=t.hi<1100,t
    # NEA cp(T) is decreasing over this temperature domain.
    return I(down(C.cp_of(t.hi),8),up(C.cp_of(t.lo),8))*fac


def rho_iv(t,fac):
    return I(down(C.rho_of(t.hi),8),up(C.rho_of(t.lo),8))*fac


def mu_iv(t,fac):
    assert t.lo>0,t
    return I(down(C.mu_of(t.hi),8),up(C.mu_of(t.lo),8))*fac


def churchill_iv(re,rr):
    inner=(I(7)/re)**0.9 + I(.27)*rr
    assert inner.lo>0 and inner.hi<1,inner
    a=(I(2.457)*log_iv(I(1)/inner))**16
    b=(I(37530)/re)**16
    return I(8)*((I(8)/re)**12+(a+b)**(-1.5))**(1/12)


def elbow_iv(re):
    return I(427.5)*re**(-.77)+I(.9)


def table2_total_iv(re):
    def t(v):return sum(C.table2_k(v,clamp=True))
    return I(down(t(re.hi),8),up(t(re.lo),8))


def orifice_iv(dmain,d):
    return I(down(C.orifice_nea3(dmain,d.hi,.002),8),
             up(C.orifice_nea3(dmain,d.lo,.002),8))


def box_inputs(nominal=False):
    if nominal:return {name:I(v) for name,v in zip(C.NAMES,C.X0)}
    return {name:I(*bounds) for name,bounds in zip(C.NAMES,C.BOUNDS)}


def interval_residual(side,m,q,x):
    loop=C.P if side=='P' else C.M
    mi=I.co(m);qi=I.co(q)
    segs=loop['segs'];ic=next(j for j,s in enumerate(segs) if s['cool'])
    ti=I(C.T_IN_REF)+x['dTin_P' if side=='P' else 'dTin_M']
    t=ti;means=[None]*len(segs)
    for j in range(ic):
        s=segs[j]
        L=I(s['L'])*(x['L_HS_M'] if side=='M' and j==0 else I(1))
        heat=qi*I(s['qfrac'])
        u=I(s['u'])*x['u_loss_fac']
        cp=cp_iv(t,x['cp_fac'])
        a=u*L/(mi*cp)
        e=exp_iv(-a)
        means[j]=I(C.T_AMB)+(t-I(C.T_AMB))*phi_iv(a)+(heat/(mi*cp))*psi_iv(a)
        t=I(C.T_AMB)+(t-I(C.T_AMB))*e+(heat/(mi*cp))*phi_iv(a)
    tci=t;t=ti
    for j in range(len(segs)-1,ic,-1):
        s=segs[j]
        u=I(s['u'])*x['u_loss_fac']
        cp=cp_iv(t,x['cp_fac'])
        a=u*I(s['L'])/(mi*cp)
        means[j]=I(C.T_AMB)+(t-I(C.T_AMB))*phi_neg_iv(a)
        t=I(C.T_AMB)+(t-I(C.T_AMB))*exp_iv(a)
    tco=t
    means[ic]=(tci+tco)/I(2)
    z=I(0)
    for tm,s in zip(means,segs):z=z+tm*I(s['dz'])
    # In decimal geometry sum(dz)=0.  The *encoded binary64* P-side 0.8
    # and 3.2 leave a 2.22e-16 m remainder when interpreted as exact reals.
    # Retain its tiny intercept contribution so this encloses precisely the
    # frozen source-constant model, not only the ideal decimal geometry.
    dzsum=sum((I(s['dz']) for s in segs),I(0))
    buoy=I(C.G)*x['rho_fac']*(I(1.293)*z-I(11065)*dzsum)

    tmean=sum(means,I(0))/I(len(means))
    rmean=rho_iv(tmean,x['rho_fac'])
    re_main=I(4)*mi/(I(math.pi)*I(loop['D_main'])*mu_iv(tmean,x['mu_fac']))
    qmain=mi*mi/(I(2)*rmean*I(loop['A_main'])*I(loop['A_main']))
    diagnostic=dict(temperature_min=min(v.lo for v in [ti,tci,tco,*means]),
                    temperature_max=max(v.hi for v in [ti,tci,tco,*means]),
                    cooler_bulk_delta=tci-tco,
                    segment_re_min=math.inf,segment_re_max=0.)
    if side=='P':
        friction=table2_total_iv(re_main)*qmain
    else:
        friction=I(0)
        eps=x['eps_M']*I(1e-6)
        for tm,s in zip(means,segs):
            if s['cool']:continue
            L=I(s['L'])*(x['L_HS_M'] if s is segs[0] else I(1))
            rho=rho_iv(tm,x['rho_fac'])
            re=I(4)*mi/(I(s['per'])*mu_iv(tm,x['mu_fac']))
            diagnostic['segment_re_min']=min(diagnostic['segment_re_min'],re.lo)
            diagnostic['segment_re_max']=max(diagnostic['segment_re_max'],re.hi)
            f=churchill_iv(re,eps/I(s['Dh']))
            qdyn=mi*mi/(I(2)*rho*I(s['A'])*I(s['A']))
            friction=friction+f*L/I(s['Dh'])*qdyn
        d=x['d_hole']/I(1000)
        ko=orifice_iv(loop['D_main'],d)
        friction=friction+(I(4)*elbow_iv(re_main)+ko+x['k_aux_M'])*qmain
    return buoy-friction,buoy,friction,re_main,diagnostic


def main():
    for q in (3000.,6000.):
        roots=C.fom(C.X0,q)
        for side in ('P','M'):
            m=roots['rp' if side=='P' else 'rm']['m']
            x=box_inputs(True)
            val,*_=interval_residual(side,m,q,x)
            point=roots['rp' if side=='P' else 'rm']['resid']
            print(f'{q/1000:g} kW {side} point: model F={point:.9g}, '
                  f'interval F={val}, included={val.lo<=point<=val.hi}')
            for mt in ((.4,1.15) if side=='P' else (.15,.4)):
                fb,bu,fr,re,diag=interval_residual(side,mt,q,box_inputs(False))
                print(f'  full box m={mt:g}: F={fb} Pa, '
                      f'buoy={bu}, friction={fr}, Re={re}, '
                      f'T=[{diag["temperature_min"]:.2f},'
                      f'{diag["temperature_max"]:.2f}] K')


if __name__=='__main__':main()
