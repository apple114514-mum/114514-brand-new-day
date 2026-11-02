#!/usr/bin/env python3
"""Check conservative inequalities for Zhao's one-parameter idealized model.

The mathematics behind each conservative constant is stated in the review.
This script is a reproducible diagnostic, not a machine-directed rounding
certificate for the last digits of the numerical endpoint.
"""

import math


TIN=533.15
MP=540.0
QP=10e6
R=2**2.5
D=.5
N=.25
B=1.1944
S=(QP/R)*R/MP


def cp(t): return 159.0-.0272*t+7.12e-6*t*t
def cp_t(t): return -.0272+1.424e-5*t
def rho(t): return 11096.0-B*t
def mu(t): return 4.94e-4*math.exp(754.1/t)


def bisect(fun,lo,hi):
    assert fun(lo)<0<fun(hi)
    for _ in range(90):
        mid=(lo+hi)/2
        if fun(mid)<0:lo=mid
        else:hi=mid
    return (lo+hi)/2


def temp(x):
    return bisect(lambda t:2*(t-TIN)*cp(t)-S*x,TIN,900)


TP=temp(1.0)


def mterm(x):
    t=temp(x)
    return cp(t)/cp(TP)*rho(TP)/rho(t)


def mprime(x):
    t=temp(x)
    tx=S/(2*(cp(t)+(t-TIN)*cp_t(t)))
    return mterm(x)*tx*(cp_t(t)/cp(t)+B/rho(t))


def friction_ratio(x):
    return (R*D*x*mu(temp(x))/mu(TP))**N


def f(x,w):
    return x**3-mterm(x)*(1+w*(friction_ratio(x)-1))


def main():
    avg=abs(mterm(1.2)-mterm(.9))/.3
    endpoint_derivative=abs(mprime(.9))
    assert endpoint_derivative>avg

    # From monotonic 2(T-TIN)cp(T)=S*x on x in [.9,1.2]:
    assert 2*(590-TIN)*cp(590)<S*.9
    assert 2*(610-TIN)*cp(610)>S*1.2
    assert cp(590)>cp(610)>0 and rho(590)>rho(610)>0
    assert cp_t(590)<cp_t(610)<0
    # Conservative constants on T in [590,610], justified in the report.
    assert cp(610)/cp(TP)*rho(TP)/rho(590)>.997
    assert cp(590)/cp(TP)*rho(TP)/rho(610)<1.003
    assert S/(2*(cp(610)+(610-TIN)*cp_t(590)))<65
    logder_min=cp_t(590)/cp(610)+B/rho(590)
    logder_max=cp_t(610)/cp(590)+B/rho(610)
    assert -.000015<logder_min<logder_max<0
    assert mu(590)/mu(TP)<1.02
    assert mu(610)/mu(TP)>.97
    # Thus M<1.003, |M_x|<0.001, f<1.37, 0<f_x<0.39.
    fx_lower=3*.9**2-.001*1.37-1.003*.39
    assert fx_lower>2.03
    assert .9**3-.997<0
    assert 1.2**3-1.003*1.37>0
    x_bar=(R*D)**(N/(3-N))
    root=bisect(lambda x:f(x,1.0),1.0,1.2)
    assert 1.0<root<x_bar<1.2

    print('Claimed |M_x| bound from mean secant:',f'{avg:.9f}')
    print('Exact |M_x| at x=0.9:',f'{endpoint_derivative:.9f}')
    print('Secant is NOT an upper derivative bound:',endpoint_derivative>avg)
    print('Conservative F_x lower bound on [0.9,1.2]:',f'{fx_lower:.6f}')
    print('Numerical w=1 endpoint, NOT certified last digits:',f'{root:.12f}')
    print('Analytic upper x_bar:',f'{x_bar:.12f}')
    print('Analytic conditional D range: [0,',f'{100*(x_bar-1):.6f}%',']')


if __name__=='__main__':
    main()
