#!/usr/bin/env python3
"""Independent audit of Yue five-power v13 closure and identifiability.

Yue 2017 p.4 Table 2 supplies theoretical K values; p.5 Fig.4 supplies
graph-read flows/temperature differences; p.6 Sec.5.2 states 1.12 kg/s.
Graph readings and +/-0.03 kg/s are analyst scenarios, not instrument errors.
"""

import math

P0, M0 = 17.9, 1.12
P_M = [(4.3, .62), (7.6, .82), (11.2, .94), (15.3, 1.06)]
K_TAB = [(.25, 24.5), (.50, 24.2), (.75, 23.8), (1.00, 23.3), (1.25, 22.8)]


def k_tab(m):
    for (a, ka), (b, kb) in zip(K_TAB, K_TAB[1:]):
        if m <= b:
            return ka + (m - a) * (kb - ka) / (b - a)
    return K_TAB[-1][1]


def flow(p, loss):
    target = M0**3 * k_tab(M0) * (p - loss) / (P0 - loss)
    lo, hi = 0.0, 2.0
    for _ in range(75):
        mid = (lo + hi) / 2
        if mid**3 * k_tab(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def fit_loss(points):
    # Golden-section minimization for a 1D in-sample least-squares fit.
    lo, hi = 0.0, 3.0
    phi = (math.sqrt(5) - 1) / 2
    def score(loss):
        return sum((flow(p, loss) - m)**2 for p, m in points)
    for _ in range(80):
        a = hi - phi * (hi - lo)
        b = lo + phi * (hi - lo)
        if score(a) < score(b):
            hi = b
        else:
            lo = a
    return (lo + hi) / 2


def cp(T):
    return 164.8 - .0394 * T + 1.25e-5 * T**2 - 4.56e5 / T**2


def rho(T):
    return 11096.0 - 1.3235 * T


def C(T):
    # rho*beta=1.3235; area and g cancel in ratios.
    return cp(T) / (1.3235 * rho(T))


ratio = (4.3 / .62**3) / (P0 / M0**3)
H_theory = 3.3119
print(f"P/m^3 ratio low/high: {ratio:.9f}")
print("correct momentum+energy elimination: m^3 = H*P_net/(C*K)")
print(f"if H alone varies, H_low = H_high/ratio = {H_theory/ratio:.6f} m")
print(f"if K alone varies, K_low = K_high*ratio = {k_tab(M0)*ratio:.6f}")
print(f"v13's 4.689 m uses the wrong H direction; its fitted L ratios cancel H")

temps = [423.15 + .35*i for i in range(1001)]
cv = [C(T) for T in temps]
print(f"X26-property C(483)/C(633): {C(483)/C(633):.9f}")
print(f"X26-property C max/min on 423.15-773.15 K scan: {max(cv)/min(cv):.9f}")
print("483 K and 633 K are heater temperatures in the 17.9 kW figure, not low/high power means")

# Absolute-closure check.  The relative fit normalizes away C*H at 17.9 kW.
area = math.pi * .026**2 / 4
c_absolute = cp(500) / (2 * 1.3235 * rho(500) * 9.81 * area**2)
required_net_kW = M0**3 * k_tab(M0) * c_absolute / H_theory / 1000
print(f"absolute model at 500 K, H=3.3119 m: Q_net required for 1.12 kg/s = {required_net_kW:.6f} kW")
print(f"relative to 17.9 kW electric input, L_equiv = {P0-required_net_kW:+.6f} kW")
print("Therefore the +1.25 kW relative-fit offset is not an independently calibrated absolute heat loss")
L_fit = 1.25
true_low = .62 * (4.3 - L_fit) / 4.3
true_high = M0 * (P0 - L_fit) / P0
print(f"IF reported m=P_electric/(cp*dT_HS) and L is HS external loss: true m_low/high = {true_low:.6f}/{true_high:.6f} kg/s")
print("For fixed K,C,H: m_reported is proportional to P^(1/3)*eta^(-2/3); lower eta raises the low-power reported-flow ratio")

print(f"v13 Table-2 interpolation K(.62), K(1.12): {k_tab(.62):.6f}, {k_tab(M0):.6f}")
print(f"in-sample loss fit on four graph points plus anchor: {fit_loss(P_M):.6f} kW")
for i, (p, m) in enumerate(P_M):
    train = P_M[:i] + P_M[i+1:]
    loss = fit_loss(train)
    pred = flow(p, loss)
    print(f"leave out {p:4.1f} kW: L(train)={loss:.6f} kW; predicted={pred:.6f}; graph~{m:.2f}; residual={pred-m:+.6f} kg/s")

print("Fig.4(b) plateau reread: analyst approximate values, not experimental errors")
for p, m, dt in [(4.3,.62,46),(7.6,.82,63),(11.2,.94,80),(15.3,1.06,97),(17.9,1.12,108.6)]:
    closure = m * cp(500) * dt / (p*1000)
    print(f"{p:4.1f} kW: dT~{dt:5.1f} K; m*cp*dT/P~{closure:.4f}")
print("This closure is not independent: the published m is computed by heater energy balance")
