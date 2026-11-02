#!/usr/bin/env python3
"""Independent arithmetic audit of the uploaded v8 input-resolution claims.

Values based on Zhao 2020 Tables 3–5. All results are conditional on the
chosen ideal ratio and on using table-5 mass flow as an output, not a prior.
"""

from math import sqrt


def cp_zhao(t):
    return 159.0 - 0.0272 * t + 7.12e-6 * t * t


def distortion(r_mass, area_ratio, height_ratio, power_ratio):
    return r_mass * area_ratio ** (2 / 3) / (height_ratio * power_ratio) ** (1 / 3) - 1


r_mass = 540.0 / 92.79
area_ratio = 0.25  # assumed net-flow area ratio; Table 3 does not give it
height_ratio = 2.0
q_analytic = 4 * sqrt(2)
q_table3 = 10.0 / 1.77
t_p = (533.15 + 663.16) / 2
t_m = (533.15 + 669.85) / 2
q_proxy_p = 540 * cp_zhao(t_p) * (663.16 - 533.15) / 1e6
q_proxy_m = 92.79 * cp_zhao(t_m) * (669.85 - 533.15) / 1e6
q_proxy = q_proxy_p / q_proxy_m

for name, q in (("analytic design", q_analytic), ("printed Table 3", q_table3),
                ("Table 5 enthalpy proxy", q_proxy)):
    print(f"{name}: Q_P/Q_M={q:.9f}, D_m={100*distortion(r_mass,area_ratio,height_ratio,q):+.6f}%")

x = 1 + distortion(r_mass, area_ratio, height_ratio, q_analytic)
print(f"threshold margin to +3%: {100*(1.03-x):.6f} percentage points")
t = 1.03 / x
for name, change in (("mass ratio", t-1), ("d (assuming A=d²)", t**(3/4)-1),
                     ("net area ratio", t**(3/2)-1), ("power ratio", t**(-3)-1),
                     ("height ratio", t**(-3)-1)):
    print(f"one-at-a-time input change to reach +3%: {name}: {100*change:+.6f}%")

print(f"power rounding ratio (10/1.77)/(4sqrt2): {q_table3/q_analytic:.10f}")
print(f"enthalpy-proxy/design power ratio: {q_proxy/q_analytic:.9f}")
k_model = 1.088839060800  # uploaded v8 model-fit result, not measured loop loss
f_model = 1.304794327  # uploaded v8 friction ratio, model dependent
for name, e in (("effective/design power = 1", 1.0),
                ("effective/design = enthalpy proxy", q_proxy/q_analytic)):
    k = k_model / e
    print(f"{name}: inferred K={k:.9f}, w(delta=0)={(k-1)/(f_model-1):.9f}")

k_core_assumed = 1.032945089
smaller_area = 0.239587
print(f"core K if its assumed area ratio changes .25 -> {smaller_area}: "
      f"{k_core_assumed*(smaller_area/.25)**2:.9f}")

assert abs(100*(x-1)-2.87683528417) < 1e-8
assert abs(100*distortion(r_mass,area_ratio,height_ratio,q_proxy)-3.61280803934) < 1e-8
