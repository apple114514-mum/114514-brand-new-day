#!/usr/bin/env python3
"""Independent arithmetic audit of Workbuddy closure_v11 against Li/Yue/Xu.

All inferred quantities are conditional on the printed assumptions. This script
does not infer valve position, measurement uncertainty, or actual local losses.
"""

import math

PIPE_D = 0.026
PIPE_A = math.pi * PIPE_D**2 / 4
T2 = [(.25, 5.56, 2.9, 19.1, 24.5), (.50, 11.10, 2.8, 18.9, 24.2),
      (.75, 16.70, 2.8, 18.5, 23.8), (1.00, 22.30, 2.7, 18.1, 23.3),
      (1.25, 27.80, 2.6, 17.7, 22.8)]
T3 = [(4, .657, 41.4), (8, .834, 65.3), (12, .957, 85.3),
      (16, 1.058, 102.9), (20, 1.143, 119.1), (24, 1.215, 134.4)]

def interp_total(m):
    for (m0, *a), (m1, *b) in zip(T2[:-1], T2[1:]):
        if m <= m1:
            return a[3] + (b[3] - a[3]) * (m-m0)/(m1-m0)
    return T2[-1][4]

cp = sum(p*1000/(m*dt) for p,m,dt in T3)/len(T3)
rho = 10370.0  # inferred by v11 from rounded Yue Table 2, not measured
beta = 1.3235/rho  # Xu correlation imported into the Yue calculation
g = 9.81
h = []
for p,m,dt in T3:
    hi = m**3*cp*interp_total(m)/(2*beta*rho**2*g*PIPE_A**2*p*1000)
    h.append(hi)
print("Yue Table 3 with Yue Table 2 K and Xu beta: H_eff rows =", ", ".join(f"{v:.4f}" for v in h))
print(f"mean H_eff={sum(h)/len(h):.6f} m, half range={(max(h)-min(h))/2:.6f} m; Xu Table 1 height=3.35 m")

fs = [(kpipe-1)*PIPE_D/11 for _,re,khs,kpipe,ktotal in T2]
lx = [math.log(re*1000) for _,re,*_ in T2]
ly = [math.log(f) for f in fs]
mx,my = sum(lx)/5,sum(ly)/5
fit_slope = sum((x-mx)*(y-my) for x,y in zip(lx,ly))/sum((x-mx)**2 for x in lx)
print(f"conditional f_pipe=({fs[0]:.6f}..{fs[-1]:.6f}), fitted log slope={fit_slope:.6f}, positive exponent={-fit_slope:.6f}")
print("Yue Table 2 numbers are original reported theoretical results (L1), not L3 calibration")

# Li Fig. 4(b) explicitly labels its ordinate 'Between hot and cold leg'.
# Its 68/89/125 K are not HS inlet/outlet temperature differences.
for power,mass,dt_hotcold in [(5,.5,68),(10,.8,89),(20,1.1,125)]:
    enthalpy_proxy = mass*cp*dt_hotcold/1000
    print(f"Li Fig 4: plotted heater power about {power} kW; hot/cold-leg delta T={dt_hotcold} K; "
          f"m*cp*deltaT={enthalpy_proxy:.3f} kW is a different control-volume proxy")

M24 = 1.21  # Li p5, highest power with maximum valve opening
K24 = interp_total(M24)
K_base = 2.6 + 2.5 + 1.0  # scenario decomposition, not component measurement
K_dist = K24-K_base

def paired_root(power_kw, exponent):
    def K(m): return K_base+K_dist*(m/M24)**(-exponent)
    lo,hi=.01,2.0
    target=M24**3*K24*power_kw/24.0
    for _ in range(100):
        mid=(lo+hi)/2
        if mid**3*K(mid)<target:lo=mid
        else:hi=mid
    return (lo+hi)/2

for p in [17.9,12,8,5]:
    vals=[paired_root(p,n) for n in [0,.05,.25]]
    print(f"power={p:g} kW scenario: n=0/{0.05}/{0.25} -> ",
          "/".join(f"{v:.6f}" for v in vals),
          f"; n=.05 vs .25 gap={vals[1]-vals[2]:.6f} kg/s")

fix=paired_root(17.9,0)
obs=1.12  # Yue p6 experimental, itself estimated from heat balance
print(f"17.9 kW constant-K scenario vs Yue reported point: {fix:.6f} vs {obs:.2f} kg/s")
print(f"exact K factor required={((fix/obs)**3):.6f} ({((fix/obs)**3-1)*100:+.3f}%), "
      f"exact net-power or H factor={(obs/fix)**3:.6f} ({((obs/fix)**3-1)*100:+.3f}%)")

# v11 labels the fitted positive exponent as 'm=.05' but passes `fit_slope`
# (negative), giving an unphysical sign reversal for the intended law.
wrong = paired_root(17.9,fit_slope)
right = paired_root(17.9,-fit_slope)
print(f"v11 sign check: passed slope={fit_slope:+.6f} gives {wrong:.6f}; "
      f"correct positive exponent={-fit_slope:.6f} gives {right:.6f}")

# Replace the v11 out-of-range 300 K point with the facility's stated lower
# operating temperature 150 C. This remains a hypothetical two-condition
# discrimination calculation, not a validated measurement precision.
mu = lambda T: 4.94e-4*math.exp(754.1/T)
rm = 540/92.79
f_temp = lambda tm: (rm*0.5*mu(750)/mu(tm))**0.25
df_valid = abs(f_temp(423.15)-f_temp(500))
sigma_b_over_b = math.sqrt(2)*3*.005/df_valid/.291472160
print(f"hypothetical T_M=423.15 vs 500 K, T_P=750 K: delta_f={df_valid:.6f}, "
      f"sigma_B/B={100*sigma_b_over_b:.1f}% if sigma_D=.5 pp and all other inputs fixed")
