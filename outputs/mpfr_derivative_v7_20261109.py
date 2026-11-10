"""Interval automatic differentiation of factored residual w.r.t. mass flow.

Uses MPFR directed intervals from mpfr_interval_v7_20261109.  Each input box
and the entire power interval stay free while m is split into subintervals.
"""

import math

import gmpy2 as g

import core_v2 as C
import factored_interval_v7_20261109 as V
import mpfr_interval_v7_20261109 as M

J=M.J


class D:
    __slots__=('v','d')
    def __init__(self,v,d=0):
        self.v=J.co(v);self.d=J.co(d)
    @staticmethod
    def co(x):return x if isinstance(x,D) else D(x)
    @property
    def lo(self):return self.v.lo
    @property
    def hi(self):return self.v.hi
    def __repr__(self):return f'D(v={self.v}, dm={self.d})'
    def __add__(self,b):
        b=D.co(b);return D(self.v+b.v,self.d+b.d)
    __radd__=__add__
    def __neg__(self):return D(-self.v,-self.d)
    def __sub__(self,b):return self+(-D.co(b))
    def __rsub__(self,b):return D.co(b)+(-self)
    def __mul__(self,b):
        b=D.co(b);return D(self.v*b.v,self.d*b.v+self.v*b.d)
    __rmul__=__mul__
    def reciprocal(self):
        vi=self.v.reciprocal()
        return D(vi,-self.d*vi*vi)
    def __truediv__(self,b):return self*D.co(b).reciprocal()
    def __rtruediv__(self,b):return D.co(b)*self.reciprocal()
    def __pow__(self,a):
        if a<0:return (self**(-a)).reciprocal()
        value=self.v**a
        # Subtract one at MPFR precision.  Python's binary64 (a-1) can
        # differ from the exact derivative exponent of the encoded a.
        exponent=M.mp(a)
        return D(value,J(exponent)*(self.v**(exponent-M.mp(1)))*self.d)


def exp_iv(x):
    v=M.exp_iv(x.v);return D(v,v*x.d)


def log_iv(x):return D(M.log_iv(x.v),x.d/x.v)


def phi_prime_point(a):
    a=J(a);e=M.exp_iv(-a)
    return (e*(a+J(1))-J(1))/(a*a)


def psi_prime_point(a):
    a=J(a);e=M.exp_iv(-a)
    return (J(2)-a-(a+J(2))*e)/(a*a*a)


def phi_neg_prime_point(a):
    a=J(a)
    return (a*M.exp_iv(a)-M.expm1_iv(a))/(a*a)


def increasing_derivative_hull(fn,a):
    left,right=fn(a.lo),fn(a.hi)
    if left.lo>right.hi:
        raise ValueError((fn.__name__,str(a.lo),str(a.hi),str(left),str(right)))
    return J(left.lo,right.hi)


def phi_iv(a):
    return D(M.phi_iv(a.v),increasing_derivative_hull(phi_prime_point,a.v)*a.d)


def psi_iv(a):
    return D(M.psi_iv(a.v),increasing_derivative_hull(psi_prime_point,a.v)*a.d)


def phi_neg_iv(a):
    return D(M.phi_neg_iv(a.v),increasing_derivative_hull(phi_neg_prime_point,a.v)*a.d)


def cp_prime(t):
    return -J(3.94e-2)+J(2)*J(1.25e-5)*t+J(2)*J(4.56e5)/(t*t*t)


def cp_iv(t,fac):
    v=M.cp_iv(t.v,fac.v)
    base=J(M.cp_scalar(t.v.hi).lo,M.cp_scalar(t.v.lo).hi)
    return D(v,cp_prime(t.v)*t.d*fac.v+base*fac.d)


def rho_iv(t,fac):
    v=M.rho_iv(t.v,fac.v)
    base=J(M.rho_scalar(t.v.hi).lo,M.rho_scalar(t.v.lo).hi)
    return D(v,-J(1.293)*t.d*fac.v+base*fac.d)


def mu_iv(t,fac):
    v=M.mu_iv(t.v,fac.v)
    base=J(M.mu_scalar(t.v.hi).lo,M.mu_scalar(t.v.lo).hi)
    slope=base*(-J(754.1))/(t.v*t.v)
    return D(v,slope*t.d*fac.v+base*fac.d)


def table2_slope_hull(re):
    slopes=[]
    for a,b in zip(C.TABLE2[:-1],C.TABLE2[1:]):
        if re.hi<a[0] or re.lo>b[0]:continue
        num=sum((J(b[k])-J(a[k]) for k in (1,2,3)),J(0))
        slopes.append(num/(J(b[0])-J(a[0])))
    if not slopes:raise ValueError(f'Table 2 Re outside range: {re}')
    return J(min(v.lo for v in slopes),max(v.hi for v in slopes))


def table2_total_iv(re):
    return D(M.table2_total_iv(re.v),table2_slope_hull(re.v)*re.d)


def orifice_iv(dmain,d):
    assert d.d.lo==0 and d.d.hi==0,d
    return D(M.orifice_iv(dmain,d.v))


def activate():
    V.I=D
    for name in ('exp_iv','log_iv','phi_iv','psi_iv','phi_neg_iv',
                 'cp_iv','rho_iv','mu_iv','table2_total_iv','orifice_iv'):
        setattr(V,name,globals()[name])
    V.box_inputs=lambda nominal=False: (
        {name:D(J(value)) for name,value in zip(C.NAMES,C.X0)}
        if nominal else
        {name:D(J(*bounds)) for name,bounds in zip(C.NAMES,C.BOUNDS)})


def main():
    activate()
    x=V.box_inputs(False)
    q=D(J(3000,6000))
    print(f'MPFR {g.mpfr_version()}, precision={M.PREC} bits, full ten-axis box')
    for side,mlo,mhi in (('P',.4,1.15),('M',.15,.4)):
        for n in (8,32,128):
            deriv_lo=math.inf;deriv_hi=-math.inf
            bad=0
            for j in range(n):
                m=D(J(mlo+(mhi-mlo)*j/n,mlo+(mhi-mlo)*(j+1)/n),J(1))
                f,*_=V.interval_residual(side,m,q,x)
                deriv_lo=min(deriv_lo,float(f.d.lo))
                deriv_hi=max(deriv_hi,float(f.d.hi))
                bad+=f.d.hi>=0
            print(f'{side}, {n} m boxes: F_m in '
                  f'[{deriv_lo:.4f},{deriv_hi:.4f}] Pa/(kg/s), '
                  f'boxes crossing 0: {bad}/{n}')


if __name__=='__main__':main()
