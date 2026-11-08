"""Check three coupled claims in uploaded v18 without importing its code.

This reproduces the stated, deliberately conditional, scalar flow model.
Run: python outputs/design-v18-independent-audit-20261108.py
"""

import itertools
import math


MASS_RATIO = 0.2683
MU = 2.2019e-3
D_M = 0.026 * 0.616
L_M = 11.0 * 0.5
M_DESIGN = 1.25 * MASS_RATIO
PERIM_HS = math.pi * (0.054 + 0.022) * 0.616
BETA_HS = 0.026**2 / (0.054**2 - 0.022**2)
K_FORM_HS = 1.29 + 0.64 + 0.5 * (1 - BETA_HS)
LD_HS = 1.8 * 0.5 / ((0.054 - 0.022) * 0.616)
RATIO2 = BETA_HS**2
ALPHA = 0.022 / 0.054
FRE_LAM = 64 * (1-ALPHA)**2 / (1+ALPHA**2-(1-ALPHA**2)/math.log(1/ALPHA))
YUE = [(5560, 19.1), (11100, 18.9), (16700, 18.5), (22300, 18.1), (27800, 17.7)]
K_P_05 = 24.2


def re_pipe(m, d=D_M):
    return 4*m/(math.pi*d*MU)


def f_smooth(re):
    return 0.3164*re**(-0.25)


def f_yue(re):
    """Table-implied f, logarithmically interpolated as in uploaded v18."""
    points = [(rv, (kp-1)*0.026/11.0) for rv, kp in YUE]
    if re <= points[0][0]:
        a, b = points[0], points[1]
    elif re >= points[-1][0]:
        return points[-1][1]
    else:
        a, b = next((points[i], points[i+1]) for i in range(4)
                    if points[i][0] <= re <= points[i+1][0])
    t = math.log(re/a[0])/math.log(b[0]/a[0])
    return a[1]*(b[1]/a[1])**t


def f_hs(re):
    if re <= 2300:
        return FRE_LAM/re
    hi = 0.685*5000**(-0.30)
    if re >= 5000:
        return 0.685*re**(-0.30)
    lo = FRE_LAM/2300
    t = math.log(re/2300)/math.log(5000/2300)
    return lo*(hi/lo)**t


def k_hs(m, band=1):
    return K_FORM_HS + band*f_hs(4*m/(PERIM_HS*MU))*LD_HS*RATIO2


def model(m, friction, kev=2.5, length=L_M, diameter=D_M,
          band=1, valve_exp=0, phi=1):
    re_d = re_pipe(M_DESIGN, diameter)
    f_d = friction(re_d)*length/diameter
    valve = 22.8 - (1 + f_d + k_hs(M_DESIGN, band) + kev)
    re = re_pipe(m, diameter)
    k = 1 + friction(re)*length/diameter + k_hs(m, band) + kev
    k += valve*(re/re_d)**(-valve_exp)
    return k, valve


def solve(m_p, friction, kev=2.5, length=L_M, diameter=D_M,
          band=1, valve_exp=0, phi=1):
    ideal = MASS_RATIO*m_p
    kp = 24.2 if m_p == .5 else 22.8
    lo, hi = .2, 2
    def residual(x):
        k, _ = model(x*ideal, friction, kev, length, diameter, band, valve_exp)
        return x**3*k/(phi*kp)-1
    assert residual(lo)<0<residual(hi)
    for _ in range(90):
        mid = (lo+hi)/2
        if residual(mid)<0:
            lo=mid
        else:
            hi=mid
    return (lo+hi)/2-1


def check():
    design_pipe = f_smooth(re_pipe(M_DESIGN))*L_M/D_M
    design_valve_a = 22.8-(1+design_pipe+k_hs(M_DESIGN)+2.5)
    stage_i = []
    for signs in itertools.product((-1,1),repeat=4):
        kev = 2.5*(1+.5*signs[0])
        khs = k_hs(M_DESIGN)+.06*signs[1]
        length = L_M*(1+.0909*signs[2])
        diameter = D_M*(1+.005*signs[3])
        lo,hi=.2,2.
        for _ in range(90):
            x=(lo+hi)/2
            k=1+f_smooth(re_pipe(x*M_DESIGN,diameter))*length/diameter
            k+=khs+kev+design_valve_a
            if x**3*k/22.8<1: lo=x
            else: hi=x
        stage_i.append(((lo+hi)/2-1,signs))
    print(f"stage I 16 A corners: D in "
          f"[{100*min(stage_i)[0]:+.6f}%, {100*max(stage_i)[0]:+.6f}%]")
    print("stage I uniqueness and corner extremum: "
          "x^3 K(x)=C*x^3+B*L*d^(-0.75)*x^(2.75), "
          "increasing x; K increasing in K_EV,K_HS,L and decreasing in d")
    for label, f in (("A",f_smooth),("B",f_yue)):
        print(f"closure {label}")
        for exponent in (0,.1):
            vals = [100*solve(.5,f,kev=k,valve_exp=exponent)
                    for k in (1.25,2.5,3.75)]
            print(f"  valve exponent {exponent:.2f}, D at K_EV 1.25/2.5/3.75: "
                  + ", ".join(f"{v:+.6f}%" for v in vals))

        lower_valve = (float("inf"),None)
        upper_valve = (-float("inf"),None)
        corners = []
        negative_count = 0
        for signs in itertools.product((-1,1),repeat=6):
            kev = 2.5*(1+.5*signs[0])
            phi = 1+.01*signs[1]
            length = L_M*(1+.0909*signs[2])
            diameter = D_M*(1+.005*signs[3])
            band = 1+.30*signs[4]
            exponent = .05*(signs[5]+1)
            _, valve = model(M_DESIGN,f,kev,length,diameter,band,exponent)
            lower_valve = min(lower_valve,(valve,signs))
            upper_valve = max(upper_valve,(valve,signs))
            negative_count += valve < 0
            if valve >= 0:
                d = solve(.5,f,kev,length,diameter,band,exponent,phi)
                corners.append((abs(d), d, signs))
        print(f"  valve K over 64 corners: [{lower_valve[0]:+.6f}, "
              f"{upper_valve[0]:+.6f}], negative-K corners "
              f"{negative_count}")
        worst = max(corners)
        print(f"  largest feasible |D| among corners with phi +/-1%: "
              f"{100*worst[0]:.6f}%, signed {100*worst[1]:+.6f}%, "
              f"signs {worst[2]} (K_EV,Phi,L,d,HS,m_v)")

        h = 1e-5
        slope = (math.log(model(M_DESIGN*math.exp(h),f)[0])
                 -math.log(model(M_DESIGN*math.exp(-h),f)[0]))/(2*h)
        sensitivity = 1/(3+slope)
        phi_low_temp = .96225
        d_100k = 100*solve(1.25,f,phi=phi_low_temp)
        print(f"  K flow slope at design {slope:+.8f}; "
              f"dlnx/dlnPhi {sensitivity:.8f}; "
              f"100K Phi-only design-point shift {d_100k:+.5f}%")
    mu_ratio = math.exp(754.1*(1/473-1/573))
    print(f"NEA viscosity mu(473K)/mu(573K)={mu_ratio:.6f}; "
          "v18's 100K Phi scenario held mu fixed")


if __name__ == '__main__':
    check()
