"""Directed-rounding MPFR interval pass for the factored residual.

Requires gmpy2/MPFR.  All constants already derived by core_v2.py (segment
areas, insulation U, main areas, pi*diameter) are treated as exact binary64
inputs.  Operations here are outward-rounded at 128-bit MPFR precision.
This certifies the stated frozen-number mathematical model, conditional on
the verified monotonicity identities for cp, phi, psi, Table 2 and orifice.
"""

import math

import gmpy2 as g

import core_v2 as C
import factored_interval_v7_20261109 as V

PREC=128
g.get_context().precision=PREC
g.get_context().round=g.RoundToNearest
CTX_DOWN=g.context(g.get_context(),precision=PREC,round=g.RoundDown)
CTX_UP=g.context(g.get_context(),precision=PREC,round=g.RoundUp)


def mp(x):
    return x if isinstance(x,g.mpfr) else g.mpfr(x,PREC)


class J:
    __slots__=('lo','hi')
    def __init__(self,lo,hi=None):
        self.lo=mp(lo);self.hi=mp(lo if hi is None else hi)
        assert g.is_finite(self.lo) and g.is_finite(self.hi) and self.lo<=self.hi,(lo,hi)
    @staticmethod
    def co(x):return x if isinstance(x,J) else J(x)
    def __repr__(self):return f'[{float(self.lo):.9g},{float(self.hi):.9g}]'
    def __add__(self,b):
        b=J.co(b)
        with CTX_DOWN:lo=self.lo+b.lo
        with CTX_UP:hi=self.hi+b.hi
        return J(lo,hi)
    __radd__=__add__
    def __neg__(self):return J(-self.hi,-self.lo)
    def __sub__(self,b):return self+(-J.co(b))
    def __rsub__(self,b):return J.co(b)+(-self)
    def __mul__(self,b):
        b=J.co(b)
        with CTX_DOWN:
            low=min(a*c for a in (self.lo,self.hi) for c in (b.lo,b.hi))
        with CTX_UP:
            high=max(a*c for a in (self.lo,self.hi) for c in (b.lo,b.hi))
        return J(low,high)
    __rmul__=__mul__
    def reciprocal(self):
        assert self.lo>0 or self.hi<0,self
        with CTX_DOWN:lo=g.mpfr(1)/self.hi
        with CTX_UP:hi=g.mpfr(1)/self.lo
        return J(lo,hi)
    def __truediv__(self,b):return self*J.co(b).reciprocal()
    def __rtruediv__(self,b):return J.co(b)*self.reciprocal()
    def __pow__(self,a):
        assert self.lo>0,self
        if a<0:return (self**(-a)).reciprocal()
        exponent=mp(a)
        with CTX_DOWN:lo=self.lo**exponent
        with CTX_UP:hi=self.hi**exponent
        return J(lo,hi)


def exp_iv(x):
    with CTX_DOWN:lo=g.exp(x.lo)
    with CTX_UP:hi=g.exp(x.hi)
    return J(lo,hi)


def expm1_iv(x):
    with CTX_DOWN:lo=g.expm1(x.lo)
    with CTX_UP:hi=g.expm1(x.hi)
    return J(lo,hi)


def log_iv(x):
    assert x.lo>0,x
    with CTX_DOWN:lo=g.log(x.lo)
    with CTX_UP:hi=g.log(x.hi)
    return J(lo,hi)


def phi_scalar(a):return (-expm1_iv(-J(a)))/J(a)
def psi_scalar(a):return (J(1)-phi_scalar(a))/J(a)
def phi_neg_scalar(a):return expm1_iv(J(a))/J(a)


def phi_iv(a):
    assert a.lo>0,a
    return J(phi_scalar(a.hi).lo,phi_scalar(a.lo).hi)


def psi_iv(a):
    assert a.lo>0,a
    return J(psi_scalar(a.hi).lo,psi_scalar(a.lo).hi)


def phi_neg_iv(a):
    assert a.lo>0,a
    return J(phi_neg_scalar(a.lo).lo,phi_neg_scalar(a.hi).hi)


def cp_scalar(t):
    t=J(t)
    return J(164.8)-J(3.94e-2)*t+J(1.25e-5)*t*t-J(4.56e5)/(t*t)


def cp_iv(t,fac):
    assert 400<t.lo<=t.hi<1100,t
    return J(cp_scalar(t.hi).lo,cp_scalar(t.lo).hi)*fac


def rho_scalar(t):return J(11065)-J(1.293)*J(t)
def rho_iv(t,fac):return J(rho_scalar(t.hi).lo,rho_scalar(t.lo).hi)*fac


def mu_scalar(t):return J(4.94e-4)*exp_iv(J(754.1)/J(t))
def mu_iv(t,fac):
    assert t.lo>0,t
    return J(mu_scalar(t.hi).lo,mu_scalar(t.lo).hi)*fac


def table2_scalar(re):
    re=mp(re)
    data=C.TABLE2
    if re<=data[0][0]:return J(sum(data[0][1:4]))
    if re>=data[-1][0]:return J(sum(data[-1][1:4]))
    for a,b in zip(data[:-1],data[1:]):
        if a[0]<=re<=b[0]:
            t=(J(re)-J(a[0]))/(J(b[0])-J(a[0]))
            out=J(0)
            for k in (1,2,3):out=out+J(a[k])+t*(J(b[k])-J(a[k]))
            return out
    raise AssertionError(re)


def table2_total_iv(re):
    # The total of the five printed rows decreases monotonically with Re.
    return J(table2_scalar(re.hi).lo,table2_scalar(re.lo).hi)


def orifice_scalar(dmain,d):
    beta=(J(d)/J(dmain))**2
    c=J(1)-beta
    ell=J(.002)/J(dmain)
    inv=ell**(-8)
    phi=J(.25)+J(.535)*inv/(J(.05)+inv)
    tau=(J(2.4)-ell)*exp_iv(-phi*log_iv(J(10)))
    return (J(.5)*c+c*c+tau*c**1.5)/(beta*beta)


def orifice_iv(dmain,d):
    # Analytically decreasing in the positive hole diameter.
    return J(orifice_scalar(dmain,d.hi).lo,orifice_scalar(dmain,d.lo).hi)


def activate():
    V.I=J
    for name in ('exp_iv','log_iv','phi_iv','psi_iv','phi_neg_iv',
                 'cp_iv','rho_iv','mu_iv','table2_total_iv','orifice_iv'):
        setattr(V,name,globals()[name])


def main():
    activate()
    x=V.box_inputs(False)
    q=J(3000,6000)
    print(f'MPFR {g.mpfr_version()}, precision={PREC} bits, binary64 source constants')
    for side,mlo,mhi in (('P',.4,1.15),('M',.15,.4)):
        for m in (mlo,mhi):
            f,bu,fr,re,diag=V.interval_residual(side,m,q,x)
            print(f'{side} m={m:g}: F={f}, buoy={bu}, friction={fr}, Re={re}, '
                  f'T=[{float(diag["temperature_min"]):.2f},'
                  f'{float(diag["temperature_max"]):.2f}]')
        # Only the source Table 2/association validity is checked here, not
        # F_m.  Divide m to preserve its correlation with the thermal field.
        rlo=math.inf;rhi=0.;tlo=math.inf;thi=0.;seglo=math.inf;seghi=0.
        cool_lo=math.inf;cool_hi=-math.inf
        for j in range(8):
            mi=J(mlo+(mhi-mlo)*j/8,mlo+(mhi-mlo)*(j+1)/8)
            _,_,_,re,d=V.interval_residual(side,mi,q,x)
            rlo=min(rlo,float(re.lo));rhi=max(rhi,float(re.hi))
            tlo=min(tlo,float(d['temperature_min']));thi=max(thi,float(d['temperature_max']))
            seglo=min(seglo,float(d['segment_re_min']))
            seghi=max(seghi,float(d['segment_re_max']))
            cool_lo=min(cool_lo,float(d['cooler_bulk_delta'].lo))
            cool_hi=max(cool_hi,float(d['cooler_bulk_delta'].hi))
        print(f'{side} eight m boxes: Re_main [{rlo:.3f},{rhi:.3f}], '
              f'T [{tlo:.3f},{thi:.3f}] K, '
              f'Re_segments [{seglo:.3f},{seghi:.3f}], '
              f'T_cool,in-T_cool,out [{cool_lo:.3f},{cool_hi:.3f}] K')


if __name__=='__main__':main()
