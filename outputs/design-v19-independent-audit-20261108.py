"""Independent checks of v19's feasibility, slope sign, and temperature case.

Uses the previous, independently written v18 scalar implementation. The
uploaded v19 script is read only to report its GSA implementation mismatch.
Run from this directory or anywhere with the neighboring scripts present.
"""

import math
import itertools
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parent
s = runpy.run_path(str(ROOT / "design-v18-independent-audit-20261108.py"))
model = s["model"]
solve = s["solve"]
f_a, f_b = s["f_smooth"], s["f_yue"]
length, diameter, mass_d = s["L_M"], s["D_M"], s["M_DESIGN"]


def valve_design(friction, kev, pipe_length, pipe_diameter, band):
    return model(mass_d, friction, kev=kev, length=pipe_length,
                 diameter=pipe_diameter, band=band)[1]


worst_l = length * 1.0909
worst_d = diameter * .995
band = 1.3
for kev in (3.75, 3.50, 3.43091):
    print(f"B design valve at L={worst_l:.5f} m, K_EV={kev}: "
          f"{valve_design(f_b,kev,worst_l,worst_d,band):+.8f}")
kv_at_375 = valve_design(f_b,3.75,worst_l,worst_d,band)
kev_max = 3.75+kv_at_375
f_design = f_b(s["re_pipe"](mass_d,worst_d))
l_max = (22.8-1-s["k_hs"](mass_d,band)-3.75)*worst_d/f_design
print(f"B maximum K_EV at 6 m nominal corner: {kev_max:.8f}")
print(f"B maximum pipe length at K_EV=3.75: {l_max:.8f} m")
print("Correct feasibility form: 1 + K_pipe,fr + K_HS + K_EV <= 22.8")
print("Equivalently: K_pipe,fr + K_HS + K_EV <= 21.8")

for mv in (0,.05,.10):
    d = solve(.5,f_a,kev=1.25,length=worst_l,diameter=worst_d,
              band=1.3,valve_exp=mv,phi=.99)
    print(f"A selected adverse corner, Phi=.99 and m_v={mv:.2f}: "
          f"D={100*d:+.8f}%")

for closure, friction in (("A",f_a),("B",f_b)):
    for heat_half, valve_cap in ((.05,.10),(.01,.10),(.01,.05)):
        candidates=[]
        feasible_count=0
        for signs in itertools.product((-1,1),repeat=6):
            kev=2.5*(1+.5*signs[0])
            phi=1+heat_half*signs[1]
            lm=length*(1+.0909*signs[2])
            dm=diameter*(1+.005*signs[3])
            b=1+.3*signs[4]
            mv=.5*valve_cap*(signs[5]+1)
            kv=valve_design(friction,kev,lm,dm,b)
            if kv<0: continue
            feasible_count+=1
            d=solve(.5,friction,kev=kev,length=lm,diameter=dm,
                    band=b,valve_exp=mv,phi=phi)
            candidates.append((abs(d),d,signs))
        worst=max(candidates)
        print(f"{closure} Phi +/-{100*heat_half:.0f}%, m_v<= {valve_cap:.2f}: "
              f"feasible corners {feasible_count}/64, max sampled-corner "
              f"abs(D(.5))={100*worst[0]:.6f}%, signed={100*worst[1]:+.6f}%")


def prototype_k(q):
    table=((.5,24.2),(.75,23.8),(1.0,23.3),(1.25,22.8))
    for j in range(3):
        q0,k0=table[j]
        q1,k1=table[j+1]
        if q<=q1:
            t=math.log(q/q0)/math.log(q1/q0)
            return k0*(k1/k0)**t
    return table[-1][1]


def solve_general(q, kev, phi, lm, dm, band, mv):
    lo,hi=.2,2.
    ideal=s["MASS_RATIO"]*q
    for _ in range(55):
        x=(lo+hi)/2
        k=model(x*ideal,f_a,kev=kev,length=lm,diameter=dm,
                band=band,valve_exp=mv)[0]
        if x**3*k/(phi*prototype_k(q))<1:lo=x
        else:hi=x
    return (lo+hi)/2-1


best=(0,None,None)
for signs in itertools.product((-1,1),repeat=6):
    kev=2.5*(1+.5*signs[0])
    phi=1+.01*signs[1]
    lm=length*(1+.0909*signs[2])
    dm=diameter*(1+.005*signs[3])
    b=1+.3*signs[4]
    mv=.025*(signs[5]+1)
    for j in range(61):
        q=.5+.75*j/60
        d=solve_general(q,kev,phi,lm,dm,b,mv)
        if abs(d)>best[0]:best=(abs(d),q,signs)
print(f"A Phi +/-1%, m_v<=0.05: 64 corners x 61 flow nodes, "
      f"largest sampled abs(D)={100*best[0]:.6f}% at q={best[1]:.3f}, "
      f"signs={best[2]}; sampling is not a continuous certificate")

s_p = math.log(22.8/23.3)/math.log(1.25/1.0)
for mv in (0,.05,.085,.10):
    h=1e-6
    kp = model(mass_d*math.exp(h),f_a,valve_exp=mv)[0]
    km = model(mass_d*math.exp(-h),f_a,valve_exp=mv)[0]
    s_m = (math.log(kp)-math.log(km))/(2*h)
    print(f"A at design, m_v={mv:.3f}: s_P-s_M={s_p-s_m:+.8f}; "
          "valve slope contributes -m_v*K_v/K_M to s_M")

h_friction_d = s["k_hs"](mass_d)-s["K_FORM_HS"]
print(f"Heating friction at design={h_friction_d:.8f}; with band=1.3, "
      f"v19 GSA trim misses {(1.3-1)*h_friction_d:.8f} in K_M(d)")
true_b_valve = valve_design(f_b,3.75,5.89,worst_d,1.3)
bug_b_valve = true_b_valve+.3*h_friction_d
print(f"B sample L=5.89: correct valve K={true_b_valve:+.8f}, "
      f"v19 GSA feasibility formula gives {bug_b_valve:+.8f}")

source = (ROOT / "design-v19-upload-script-20261108.py").read_text(encoding="utf-8")
gsa_body = source.split("def gsa(",1)[1].split("for phi_half, tag",1)[0]
print("v19 gsa() evaluates model_vec(a), model_vec(b), model_vec(ab) "
      f"without applying ok_a/ok_b: {'model_vec(a, closure' in gsa_body and 'ok_a' in gsa_body}")
print("v19 model_vec()/feasible() use khs(m_d) instead of khs(m_d, band): "
      f"{source.count('khs(m_d) + kev') >= 2}")

mu_573 = 4.94e-4*math.exp(754.1/573)
mu_473 = 4.94e-4*math.exp(754.1/473)
rho = lambda t: 11065-1.293*t
cp = lambda t: 164.8-.0394*t+1.25e-5*t*t-4.56e5/t**2
phi = (rho(573)/rho(473))/((rho(473)/rho(573))*(cp(473)/cp(573)))
global_vars = solve.__globals__
for label, mu, heat_factor in (("same NEA 573 K",mu_573,1),
                               ("same NEA 473 K",mu_473,phi),
                               ("v19 nominal MU",.0022019,1),
                               ("v19 MU times ratio",.0022019*mu_473/mu_573,phi)):
    global_vars["MU"] = mu
    print(f"{label}: mu={mu:.9f} Pa s, A D(0.50)="
          f"{100*solve(.5,f_a,phi=heat_factor):+.6f}%")
global_vars["MU"] = .0022019
print(f"NEA phi 473/573={phi:.8f}; v19's 'nominal 573 K' uses a viscosity "
      "equivalent to about 504.6 K")
