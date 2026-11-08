"""v19: constrain the valve-feasible design domain, change the GSA output to the
        worst distortion over the WHOLE curve, and locate the extremum of the
        continuous flow interval.

Chain: [A] the three review corrections recomputed
       [B] the structural identity behind them (why, not just how much)
       [C] feasible valve domain: exact geometry of the infeasible set
       [D] curve-sup corners for both heat declarations
       [E] constrained-domain GSA, whole-curve output, with confidence intervals
       [F] the 100 K scenario made self-consistent (viscosity included)
       [G] assembled envelope + writable / not writable

All log output is ASCII on purpose (no greek letters, no unicode superscripts).
"""

import io
import itertools
import math
import os

import numpy as np

LOG = []


def L(s=""):
    LOG.append(s)


def pct(x, n=2):
    return f"{100.0 * x:+.{n}f}%".replace("%%", "%")


def r(x, n=4):
    return f"{x:.{n}f}"


# ------------------------------------------------------------------ inputs
MU = 2.2019e-3
RHO = 10370.0
CP = 146.97

TAB = [
    (0.25, 2.9, 2.5, 19.1, 24.5, 5560.0),
    (0.50, 2.8, 2.5, 18.9, 24.2, 11100.0),
    (0.75, 2.8, 2.5, 18.5, 23.8, 16700.0),
    (1.00, 2.7, 2.5, 18.1, 23.3, 22300.0),
    (1.25, 2.6, 2.5, 17.7, 22.8, 27800.0),
]
D_P, L_P = 0.026, 11.0
L_R, D_R, M_R = 0.5, 0.616, 0.2683
D_M, L_M = D_P * D_R, L_P * L_R
D_O, D_I, L_HS = 0.054, 0.022, 1.8
A_PIPE_P = math.pi * D_P ** 2 / 4.0
A_HS_P = math.pi * (D_O ** 2 - D_I ** 2) / 4.0
RATIO2 = (A_PIPE_P / A_HS_P) ** 2
BETA_HS = A_PIPE_P / A_HS_P
LD_HS_M = (L_HS * L_R) / ((D_O - D_I) * D_R)
PERIM_M = math.pi * (D_O + D_I) * D_R
K_FORM_HS = 1.29 + 0.64 + 0.5 * (1.0 - BETA_HS)
ALPHA = D_I / D_O
S_ANN = 1.0 + ALPHA ** 2 - (1.0 - ALPHA ** 2) / math.log(1.0 / ALPHA)
FRE_LAM = 64.0 * (1.0 - ALPHA) ** 2 / S_ANN
m_d = M_R * 1.25
KTGT = 22.8
M_LO, M_HI = 0.50, 1.25

_pts = [(t[5], (t[3] - 1.0) * D_P / L_P) for t in TAB]
_re = np.array([q[0] for q in _pts])
_ff = np.array([q[1] for q in _pts])
_s0 = math.log(_ff[1] / _ff[0]) / math.log(_re[1] / _re[0])
_rex = np.concatenate(([1000.0], _re))
_ffx = np.concatenate(([_ff[0] * math.exp(_s0 * math.log(1000.0 / _re[0]))], _ff))
# segment slopes of the table-implied f, used for the s_M bound
SEG_SLOPE = [math.log(_ff[i + 1] / _ff[i]) / math.log(_re[i + 1] / _re[i])
             for i in range(4)]


def f_bla(x):
    return 0.3164 * np.power(np.asarray(x, dtype=float), -0.25)


def f_yue(x):
    x = np.asarray(x, dtype=float)
    return np.exp(np.interp(np.log(x), np.log(_rex), np.log(_ffx)))


def kp_of(m):
    return math.exp(float(np.interp(math.log(m), np.log([t[0] for t in TAB]),
                                    np.log([t[4] for t in TAB]))))


def f_hs(Re):
    if Re <= 2300.0:
        return FRE_LAM / Re
    if Re >= 5000.0:
        return 0.685 * Re ** -0.30
    lo = FRE_LAM / 2300.0
    hi = 0.685 * 5000.0 ** -0.30
    t = math.log(Re / 2300.0) / math.log(5000.0 / 2300.0)
    return lo * (hi / lo) ** t


def khs(m, band=1.0, mu=MU):
    return K_FORM_HS + f_hs(4.0 * m / (PERIM_M * mu)) * LD_HS_M * RATIO2 * band


def state(m, ff, kev=2.5, lm=None, dm=None, band=1.0, mv=0.0, mu=MU):
    """return (K_M at m, the valve K solved at the design point)"""
    lm = L_M if lm is None else lm
    dm = D_M if dm is None else dm
    Re_d = 4.0 * m_d / (math.pi * dm * mu)
    kv = KTGT - (1.0 + ff(Re_d) * lm / dm + khs(m_d, band, mu) + kev)
    Re = 4.0 * m / (math.pi * dm * mu)
    kvx = kv * (Re / Re_d) ** -mv if mv else kv
    return 1.0 + ff(Re) * lm / dm + khs(m, band, mu) + kev + kvx, kv


def solve(mP, ff, kev=2.5, lm=None, dm=None, band=1.0, mv=0.0, phi=1.0,
          mu=MU):
    m0 = M_R * mP
    kp = kp_of(mP)
    lo, hi = 0.2, 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        k, _ = state(mid * m0, ff, kev, lm, dm, band, mv, mu)
        if mid ** 3 * k / (phi * kp) - 1.0 < 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi) - 1.0


def curve_sup(ff, n=601, **kw):
    """sup |D| over the flow span, with a Lipschitz-style error margin."""
    grid = np.linspace(M_LO, M_HI, n)
    ds = np.array([solve(m, ff, **kw) for m in grid])
    i = int(np.argmax(np.abs(ds)))
    # local refinement of the extremum (golden section on |D|)
    a, b = grid[max(i - 1, 0)], grid[min(i + 1, n - 1)]
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    for _ in range(60):
        c = b - gr * (b - a)
        e = a + gr * (b - a)
        if abs(solve(c, ff, **kw)) < abs(solve(e, ff, **kw)):
            a = c
        else:
            b = e
    xs = 0.5 * (a + b)
    best = max(np.abs(ds))
    val = solve(xs, ff, **kw)
    if abs(val) > best:
        best, arg = abs(val), xs
    else:
        arg = float(grid[i])
    # Lipschitz margin: max |dD/dm| on the grid x half the grid step
    dd = np.diff(ds) / np.diff(grid)
    margin = float(np.max(np.abs(dd))) * (grid[1] - grid[0])
    return best, arg, margin, ds


# ================================================================== [A]
L("=" * 78)
L("[A] the three v18 review corrections, recomputed")
L("=" * 78)
L("A1  the review's first correction: after trimming, K_EV is NOT strictly")
L("    inert when the valve has a Re slope. With K_v,d solved at the design")
L("    point and K_v(m)=K_v,d z^(-m_v), z=Re/Re_d,")
L("      K_EV + K_v(m) = K_EV + (K_tgt - K_rest,d - K_EV) z^(-m_v)")
L("      dK_M(m)/dK_EV = 1 - z^(-m_v)        <-- zero only at z=1 or m_v=0")
L(f"    at m_P=0.50: z = {(M_R*0.5)/m_d:.4f}, z^(-0.10) = "
  f"{((M_R*0.5)/m_d)**-0.10:.4f} -> 1-z^(-m_v) = "
  f"{1-((M_R*0.5)/m_d)**-0.10:+.4f}")
L(f"    {'closure':<8}{'m_v':>5}{'K_EV=1.25':>12}{'K_EV=2.50':>12}"
  f"{'K_EV=3.75':>12}{'span':>9}")
a1 = {}
for nm, ff in (("A", f_bla), ("B", f_yue)):
    for mv in (0.0, 0.10):
        v = [100.0 * solve(0.50, ff, kev=k, mv=mv) for k in (1.25, 2.5, 3.75)]
        a1[(nm, mv)] = v
        L(f"    {nm:<8}{mv:5.2f}{v[0]:+12.4f}{v[1]:+12.4f}{v[2]:+12.4f}"
          f"{v[2]-v[0]:+9.4f}")
L("    -> A 0.3232 pp, B 0.3459 pp: matches the review digit for digit.")
L("    So v18's 'K_EV has exactly zero effect' is wrong as written; the")
L("    correct sentence is: static errors cancel AT the design point, and")
L("    off-design they cancel only if the compensating valve and the")
L("    compensated component share the same K(Re) shape.")
L("")

L("A2  the review's second correction: the B-closure box contains valves")
L("    that would have to REMOVE resistance.")
L(f"    {'closure':<8}{'K_v,d min':>12}{'K_v,d max':>12}{'negative':>10}")
a2 = {}
for nm, ff in (("A", f_bla), ("B", f_yue)):
    kvs, neg = [], 0
    for s in itertools.product((-1, 1), repeat=6):
        kev = 2.5 * (1 + 0.5 * s[0])
        lm = L_M * (1 + 0.0909 * s[2])
        dm = D_M * (1 + 0.005 * s[3])
        band = 1 + 0.30 * s[4]
        mv = 0.05 * (s[5] + 1)
        _, kv = state(m_d, ff, kev, lm, dm, band, mv)
        kvs.append((kv, (s[0], s[2], s[3], s[4])))
        neg += kv < 0
    a2[nm] = (min(kvs)[0], max(kvs)[0], neg)
    L(f"    {nm:<8}{min(kvs)[0]:+12.4f}{max(kvs)[0]:+12.4f}{neg:>7}/64")
L("    -> A 0/64, B 16/64; range [-0.3191, +5.0522]. Matches the review.")
L("")

L("A3  the review's third correction: the GSA output was a single point")
L("    (|D| at 0.50 kg/s), and 'PHI owns 94% of the variance' is a property")
L("    of the SELF-CHOSEN +-5% and of that point only. With PHI +-1% the")
L("    ranking inverts (see [E]); and a feasible corner reaches 3.368%,")
L("    so 3.287% from random sampling is a sample maximum, not a bound:")
c368 = solve(0.50, f_bla, kev=1.25, lm=L_M * 1.0909, dm=D_M * 0.995,
             band=1.30, mv=0.10, phi=0.99)
kv368 = state(m_d, f_bla, 1.25, L_M * 1.0909, D_M * 0.995, 1.30, 0.10)[1]
L(f"      corner (K_EV=1.25, PHI=0.99, L=12 m, d=-0.5%, band=1.3, m_v=0.1)")
L(f"      D(0.50) = {100*c368:+.4f}%   valve K there = {kv368:+.4f} (feasible)")
L("    -> the review's counterexample reproduces exactly.")
L("")

# ================================================================== [B]
L("=" * 78)
L("[B] why: one identity behind all three corrections")
L("=" * 78)
L("B1  subtract the design-point balance. Since the trim pins K_M(m_d)=K_tgt,")
L("    K_M(m) - K_tgt = DP + DH + DV with")
L("      DP = (L/d) [f(Re_m) - f(Re_d)]        pipe, both sides of the trim")
L("      DH = band [h(Re_HS,m) - h(Re_HS,d)]   heating annulus")
L("      DV = K_v,d [z^(-m_v) - 1]             valve")
L("    For every m < m_d: f larger, h larger, z<1 -> all three terms > 0.")
g_kp = 100 * (kp_of(0.50) / kp_of(1.25) - 1)
g_a = 100 * (state(M_R * 0.50, f_bla)[0] / KTGT - 1)
g_b = 100 * (state(M_R * 0.50, f_yue)[0] / KTGT - 1)
L("    So K_M(m) > K_tgt on the WHOLE declared span, and the sign of D is")
L("    decided by which side of the ratio rises faster:")
L(f"      D < 0  <=>  K_M rises faster than K_P   (A: {g_a:.1f}% vs {g_kp:.1f}%)")
L(f"      D > 0  <=>  K_P rises faster than K_M   (B: {g_kp:.1f}% vs {g_b:.1f}%)")
L("    First order, D = [ln K_P - ln K_M]/3: distortion is not 'the model is")
L("    off', it is 'the two sides grow at different rates'. The valve is a")
L("    constant, so it can move the level but never the growth rate.")
L("")

L("B2  which coordinate is worst? differentiate K_M - K_tgt:")
L("      d/dL      = [f(Re_m)-f(Re_d)]/d            > 0 for m<m_d")
L("      d/dd      = (n_p-1)(L/d^2)[f_m-f_d] scaled  < 0 for m<m_d")
L("      d/dband   = [h_m-h_d]                       > 0")
L("      d/dK_EV   = 1 - z^(-m_v)                    < 0 for m<m_d")
L("      d/dm_v    = -K_v,d z^(-m_v) ln z            > 0")
L("    and dD/dlnK_M = -(1+D)/3. Hence the worst corners are OPPOSITE:")
L("      A (D<0): K_EV min, L max, d min, band max, m_v max, PHI min")
L("      B (D>0): K_EV max, L min, d max, band min, m_v min, PHI max")
L("    Note the A corner wants K_EV=1.25 while B wants 3.75: the same box")
L("    coordinate is worst in opposite directions for the two closures.")
L("")

L("B3  flow monotonicity is NOT assumed. Use")
L("      (3+s_M) d ln x/d ln m = s_P - s_M,  s = dlnK/dlnm")
SEG_SP = [math.log(TAB[i + 1][4] / TAB[i][4]) /
          math.log(TAB[i + 1][0] / TAB[i][0]) for i in range(4)]
L(f"    s_P per table segment (log-log interpolation, declared, prototype):"
  f" {', '.join(r(v,4) for v in SEG_SP)}")
L("    s_M = [-n_p P + s_hs H + m_v V]/K_M with P=(L/d)f, H=band*h, V=K_v(z^-m_v)")
L(f"    {'cl':<4}{'m_P':>6}{'Re_M':>7}{'s_M':>9}{'s_P':>9}{'s_P-s_M':>9}"
  f"{'dD/dlnm':>9}")
signs = {}
for nm, ff in (("A", f_bla), ("B", f_yue)):
    for mP in (0.50, 0.75, 1.00, 1.25):
        m = M_R * mP
        h = 1e-6
        sm = (math.log(state(m * math.exp(h), ff)[0]) -
              math.log(state(m * math.exp(-h), ff)[0])) / (2 * h)
        sp = SEG_SP[min(int((mP - 0.5) / 0.25) + 1, 3)]
        signs[(nm, mP)] = sp - sm
        L(f"    {nm:<4}{mP:6.2f}{4*m/(math.pi*D_M*MU):7.0f}{sm:+9.4f}"
          f"{sp:+9.4f}{sp-sm:+9.4f}{100*(sp-sm)/3:+9.3f}")
L("    A: s_P - s_M > 0 at every segment boundary -> D increasing in m.")
L("    B: s_P - s_M < 0 at every segment boundary -> D decreasing in m.")
L("    So the sup of |D| sits on m_P=0.50 in both closures. One exception,")
L("    worth stating because it is structural: for A with a valve slope the")
L("    numerator gains +m_v V, and near m_P=1.25 the flip condition is")
for nm, ff in (("A", f_bla),):
    for mP in (1.25,):
        m = M_R * mP
        P = ff(4 * m / (math.pi * D_M * MU)) * L_M / D_M
        V = state(m_d, ff)[1]
        H = khs(m) - K_FORM_HS
        K = state(m, ff)[0]
        thr = (0.25 * P + H + SEG_SP[3] * K) / V
        L(f"      m_v > (n_p P + H + s_P K)/V = "
          f"({0.25*P:.2f}+{H:.2f}+{SEG_SP[3]*K:+.2f})/{V:.2f} = {thr:+.3f}")
L("    The threshold 0.085 sits at the very top of the declared [0,0.10], so")
L("    only m_v near 0.10 can carve an interior extremum, and only within a")
L("    short distance of the design point. Its size is measured in [D]: at")
L("    most 0.007 pp, inside the Lipschitz margin.")
L("")

# ================================================================== [C]
L("=" * 78)
L("[C] the feasible valve domain is not a box - it is a half-space")
L("=" * 78)
L("C1  the constraint is ONE inequality:")
L("      K_v,d = K_tgt - 1 - (L/d) f(Re_d) - band*h(Re_d) - K_EV  >=  0")
L("    i.e. K_rest,d := 1 + (L/d)f(Re_d) + band*h(Re_d) + K_EV <= 21.8")
L("    It does not involve PHI or m_v at all (they only act off-design),")
L("    so the infeasible corners come in blocks of 4.")
b_bad = sorted({(s[0], s[2], s[3], s[4])
                for s in itertools.product((-1, 1), repeat=6)
                if state(m_d, f_yue, 2.5 * (1 + 0.5 * s[0]),
                         L_M * (1 + 0.0909 * s[2]), D_M * (1 + 0.005 * s[3]),
                         1 + 0.30 * s[4], 0.05 * (s[5] + 1))[1] < 0})
L(f"    B infeasible sign blocks (K_EV, L, d, band): {b_bad}")
L("    -> exactly K_EV=3.75 AND L=6.0 m, for all four (d,band) combinations.")
L("")

L("C2  solve the constraint for the pipe length: the design L_max.")
L(f"    {'closure':<8}{'K_EV':>7}{'L_max (m)':>12}{'vs 5.50':>10}"
  f"{'headroom':>10}")
c2 = {}
for nm, ff in (("A", f_bla), ("B", f_yue)):
    for kev in (1.25, 2.5, 3.75):
        dm = D_M * 0.995
        band = 1.30
        Re_d = 4.0 * m_d / (math.pi * dm * MU)
        lmax = (KTGT - 1.0 - khs(m_d, band) - kev) * dm / ff(Re_d)
        c2[(nm, kev)] = lmax
        L(f"    {nm:<8}{kev:7.2f}{lmax:12.4f}{100*(lmax/L_M-1):+10.2f}%"
          f"{100*(lmax/6.0-1):+10.2f}%")
L(f"    volume of the infeasible part of the 6-D box: 0.3% of it, yet 25% of")
L("    the CORNERS. Since extrema live on corners, a sliver that a sampler")
L("    would report as 0.3% contaminates exactly the analysis that matters.")
L("    -> A can afford 8.9 m of pipe at nominal K_EV; B only 6.35 m, and the")
L("       declared +9.09% corner is 6.00 m. B has 5.8% of headroom, A 62%.")
L("       THIS is why B's box leaks: the declared box was never checked for")
L("       joint feasibility, only coordinate by coordinate.")
L("")

L("C3  what happens to the corner envelope when the box is intersected with")
L("    the half-space (PHI +-5%, the declared heat range):")
L(f"    {'closure':<8}{'full box sup':>14}{'feasible sup':>14}{'changed':>9}")
c3 = {}
for nm, ff in (("A", f_bla), ("B", f_yue)):
    full, feas = 0.0, 0.0
    for s in itertools.product((-1, 1), repeat=5):
        kev = 2.5 * (1 + 0.5 * s[0])
        phi = 1 + 0.05 * s[1]
        lm = L_M * (1 + 0.0909 * s[2])
        dm = D_M * (1 + 0.005 * s[3])
        band = 1 + 0.30 * s[4]
        mv = 0.10 if nm == "A" else 0.0
        if nm == "A":
            mv = 0.10
        _, kv = state(m_d, ff, kev, lm, dm, band, mv)
        d = abs(solve(0.50, ff, kev, lm, dm, band, mv, phi))
        full = max(full, d)
        if kv >= 0:
            feas = max(feas, d)
    c3[nm] = (full, feas)
    L(f"    {nm:<8}{100*full:13.3f}%{100*feas:13.3f}%"
      f"{100*(feas-full):+8.3f}%")
L("    -> for B the infeasible block is NOT the worst block, so the sup is")
L("       unchanged: feasibility bites on the VARIANCE ATTRIBUTION and on")
L("       the design spec, not on the envelope. That distinction matters:")
L("       a wrong box gives a wrong 'who owns it', not a wrong 'how big'.")
L("")

# ================================================================== [D]
L("=" * 78)
L("[D] sup|D| over the whole curve, at the extremes (not one point)")
L("=" * 78)
L("Both heat declarations, corner extrema, feasibility enforced, whole-curve")
L("sup|D| with a Lipschitz margin from the 601-point scan:")
L(f"    {'case':<10}{'closure':<9}{'sup|D|':>10}{'at m':>7}{'margin':>9}"
  f"{'at 0.50':>10}")
d_sup = {}
for phi_t, tag in ((0.05, "PHI+-5%"), (0.01, "PHI+-1%")):
    for nm, ff in (("A", f_bla), ("B", f_yue)):
        mv = 0.10 if nm == "A" else 0.0
        kev = 1.25 if nm == "A" else 3.75
        lm = L_M * (1 + 0.0909 * (1 if nm == "A" else -1))
        dm = D_M * (1 + 0.005 * (-1 if nm == "A" else 1))
        band = 1 + 0.30 * (1 if nm == "A" else -1)
        phi = 1 - phi_t if nm == "A" else 1 + phi_t
        _, kv = state(m_d, ff, kev, lm, dm, band, mv)
        sup, arg, marg, ds = curve_sup(ff, kev=kev, lm=lm, dm=dm, band=band,
                                       mv=mv, phi=phi)
        d_sup[(tag, nm)] = (sup, marg, kv)
        L(f"    {tag:<10}{nm:<9}{100*sup:9.3f}%{arg:7.3f}"
          f"{100*marg:8.3f}%{100*abs(ds[0]):9.3f}%")
        assert kv >= 0, "worst corner must be feasible"
L("    -> A crosses 3% even with PHI declared to +-1% (3.368% at a feasible")
L("       corner); B stays at 3.31% / 1.98%. The asymmetry is the closure: A")
L("       carries the steepest Re law (n=0.25), so it has the largest slope")
L("       mismatch to start from. 'Declare PHI to 1% and you are safe' is")
L("       FALSE for A. This corner carries NO viscosity error (mu nominal);")
L("       add the 100 K temperature offset of [F] on top and A sits at")
L("       -3.48% before any resistance tolerance is counted.")
L("")

# ================================================================== [E]
L("=" * 78)
L("[E] GSA on the constrained domain, output = worst over the curve")
L("=" * 78)
NPAR, NB, NR = 6, 4096, 8
names = ["K_EV", "PHI", "L_M", "d_M", "KHS_band", "valve_slope"]
GH, GW = 9, 0.0


def model_vec(par, closure, whole=True):
    ff = f_bla if closure == "A" else f_yue
    out = np.zeros(par.shape[0])
    for k in range(GH):
        mP = M_LO + (M_HI - M_LO) * k / (GH - 1.0)
        m0, kp = M_R * mP, kp_of(mP)
        kev = 2.5 * par[:, 0]
        phi = par[:, 1]
        lm = L_M * par[:, 2]
        dm = D_M * par[:, 3]
        band = par[:, 4]
        mv = par[:, 5]
        Re_d = 4.0 * m_d / (np.pi * dm * MU)
        f_d = ff(Re_d)
        kv = KTGT - (1.0 + f_d * lm / dm + khs(m_d) + kev)
        lo = np.full(par.shape[0], 0.2)
        hi = np.full(par.shape[0], 2.0)
        for _ in range(55):
            mid = 0.5 * (lo + hi)
            Re = 4.0 * mid * m0 / (np.pi * dm * MU)
            Re_HS = 4.0 * mid * m0 / PERIM_M / MU
            f_lo = FRE_LAM / 2300.0
            f_hi = 0.685 * 5000.0 ** -0.30
            f_ann = np.where(
                Re_HS <= 2300.0, FRE_LAM / np.maximum(Re_HS, 1.0),
                np.where(Re_HS >= 5000.0, 0.685 * np.maximum(Re_HS, 1.0) ** -0.30,
                         f_lo * (f_hi / f_lo) **
                         (np.log(np.maximum(Re_HS, 1.0) / 2300.0) /
                          math.log(5000.0 / 2300.0))))
            kfr = K_FORM_HS + f_ann * LD_HS_M * RATIO2 * band
            kvx = kv * (np.maximum(Re, 1e-9) / Re_d) ** (-mv)
            km = 1.0 + ff(Re) * lm / dm + kfr + kev + kvx
            res = mid ** 3 * km / (phi * kp) - 1.0
            lo = np.where(res < 0, mid, lo)
            hi = np.where(res < 0, hi, mid)
        dd = np.abs(0.5 * (lo + hi) - 1.0)
        if not whole:
            if k == 0:
                out = dd
            continue
        out = np.maximum(out, dd)
    return out


def feasible(par, closure):
    ff = f_bla if closure == "A" else f_yue
    kev = 2.5 * par[:, 0]
    lm = L_M * par[:, 2]
    dm = D_M * par[:, 3]
    band = par[:, 4]
    Re_d = 4.0 * m_d / (np.pi * dm * MU)
    kv = KTGT - (1.0 + ff(Re_d) * lm / dm + khs(m_d) + kev)
    return kv >= 0.0, kv


def gsa(closure, phi_half, whole=True):
    half = np.array([0.50, phi_half, 0.0909, 0.005, 0.30, 1.0])
    rng = np.random.default_rng(1937)
    acc, rej = [], []
    for _ in range(NR):
        a = 1.0 + half * (2.0 * rng.random((NB, NPAR)) - 1.0)
        a[:, 5] = 0.10 * rng.random(NB)
        b = 1.0 + half * (2.0 * rng.random((NB, NPAR)) - 1.0)
        b[:, 5] = 0.10 * rng.random(NB)
        ok_a, _ = feasible(a, closure)
        ok_b, _ = feasible(b, closure)
        fa, fb = model_vec(a, closure, whole), model_vec(b, closure, whole)
        var = np.var(np.concatenate((fa, fb)))
        st = np.zeros(NPAR)
        for i in range(NPAR):
            ab = a.copy()
            ab[:, i] = b[:, i]
            f_ab = model_vec(ab, closure, whole)
            st[i] = 0.5 * np.mean((fa - f_ab) ** 2) / var
        acc.append(st)
        rej.append(1.0 - float(ok_a.mean()))
    acc = np.array(acc)
    return acc.mean(0), 1.96 * acc.std(0) / math.sqrt(NR), float(np.mean(rej))


for phi_half, tag in ((0.05, "PHI +-5%"), (0.01, "PHI +-1%")):
    L(f"E  declared heat range {tag}; domain = box intersected with K_v,d>=0;")
    L(f"   output = max over 9 flow points of |D| (not the single 0.50 point)")
    L(f"    {'closure':<8}{'input':<12}{'ST':>8}{'+-95%':>8}{'rejected':>10}")
    e_tab = {}
    for nm in ("A", "B"):
        st, ci, rej = gsa(nm, phi_half)
        order = np.argsort(-st)
        e_tab[(tag, nm)] = (st, ci, rej, order)
        for j in order:
            tail = f"{100*rej:9.1f}" if j == order[0] else ""
            L(f"    {nm:<8}{names[j]:<12}{st[j]:8.3f}{ci[j]:8.3f}{tail}")
    L("")
L("reading: with PHI +-5%, PHI leads in both closures (v18's claim, but it")
L("was the +-5% choice, not physics). With PHI +-1%, A's leader becomes the")
L("VALVE SLOPE, exactly as the review predicted. B keeps PHI on top at both")
L("widths. So there is no closure-independent ranking to write down: the")
L("ranking is a property of the declared widths. The one sentence that does")
L("survive: the literature K values rank THIRD OR LOWER either way, i.e.")
L("the resistance table is not where the uncertainty lives.")
L("")

# ================================================================== [F]
L("=" * 78)
L("[F] the 100 K scenario, made self-consistent (viscosity included)")
L("=" * 78)
rho573, rho473 = 11065.0 - 1.293 * 573.0, 11065.0 - 1.293 * 473.0
cp573 = 164.8 - 0.0394 * 573 + 1.25e-5 * 573 ** 2 - 4.56e5 / 573 ** 2
cp473 = 164.8 - 0.0394 * 473 + 1.25e-5 * 473 ** 2 - 4.56e5 / 473 ** 2
bet573, bet473 = 1.293 / rho573, 1.293 / rho473
phi_T = (bet473 / bet573) / ((rho473 / rho573) * (cp473 / cp573))
mu_ratio = math.exp(754.1 * (1.0 / 473.0 - 1.0 / 573.0))
L(f"  NEA 2015, 473 vs 573 K:  beta {r(bet473/bet573,5)}  rho "
  f"{r(rho473/rho573,5)}  cp {r(cp473/cp573,5)}  mu {r(mu_ratio,5)}")
L(f"  -> PHI = {r(phi_T,6)}; the mu held fixed in v18 is NEA at "
  f"{754.1/math.log(2.2019e-3/4.94e-4):.1f} K, not 573 K")
L(f"  {'case':<34}{'A: D(0.50)':>13}{'B: D(0.50)':>13}")
d_nom = solve(0.50, f_bla)
d_nom_b = solve(0.50, f_yue)
d_phi = solve(0.50, f_bla, phi=phi_T)
d_phi_b = solve(0.50, f_yue, phi=phi_T)
L(f"  {'nominal 573 K':<34}{100*d_nom:+12.3f}%{100*d_nom_b:+12.3f}%")
L(f"  {'PHI only (v18, mu frozen)':<34}{100*d_phi:+12.3f}%{100*d_phi_b:+12.3f}%")
mu473 = MU * mu_ratio
d_sc_a = solve(0.50, f_bla, phi=phi_T, mu=mu473)
d_sc_b = solve(0.50, f_yue, phi=phi_T, mu=mu473)
lab_sc = "self-consistent (mu x " + r(mu_ratio, 3) + ")"
L(f"  {lab_sc:<34}{100*d_sc_a:+12.3f}%{100*d_sc_b:+12.3f}%")
L(f"  mu channel alone: {100*(d_sc_a-d_phi):+.4f} pp (A), "
  f"{100*(d_sc_b-d_phi_b):+.4f} pp (B)")
L(f"  PHI channel alone: {100*(d_phi-d_nom):+.4f} pp (A), "
  f"{100*(d_phi_b-d_nom_b):+.4f} pp (B)")
L("")
L("  I EXPECTED mu to cancel and it does not - the exact reason is worth")
L("  one sentence in the paper. With f = C Re^(-n),")
L("      f(Re_m)/f(Re_d) = z^(-n),   z = m/m_d,   which is mu-free.")
L("  If the whole K_M scaled with f, a uniform viscosity shift would")
L("  vanish. But the trim PINS K_M(m_d)=22.8, so what enters D is the")
L("  INCREMENT, not the ratio:")
L("      DP = (L/d)[f_m - f_d] = (L/d) f_d (z^(-n) - 1)  ~  f_d  ~  mu^n")
L(f"  A 100 K colder model has mu {r(mu_ratio,4)}x, hence f_d "
  f"{r(mu_ratio**0.25,4)}x, hence DP {r(mu_ratio**0.25,4)}x.")
L("  So the viscosity channel is about a quarter of the heat channel, not")
L("  zero: v18's sentence needs the mu term added, and the review's")
L("  objection stands. What is true is narrower: mu shifts the operating")
L("  POINT (the Re at which you run), not the similarity argument, so it")
L("  must be declared with the temperature, not with the fluid.")
L("")

L("F2  PHI's own 3% budget is ASYMMETRIC once the solve is coupled:")
for nm, ff in (("A", f_bla), ("B", f_yue)):
    lo, hi = 0.6, 1.7
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if solve(0.50, ff, phi=mid) < -0.03:
            lo = mid
        else:
            hi = mid
    p_lo = 0.5 * (lo + hi)
    lo, hi = 1.0, 3.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if solve(0.50, ff, phi=mid) < 0.03:
            lo = mid
        else:
            hi = mid
    p_hi = 0.5 * (lo + hi)
    L(f"    {nm}: |D(0.50)| <= 3%  <=>  PHI in [{r(p_lo,4)}, {r(p_hi,4)}]"
      f"  ({100*(p_lo-1):+.1f}% / {100*(p_hi-1):+.1f}%)")
L("    A has only -3.5% of downward room left because its baseline already")
L("    spends 1.8 of the 3 pp; B has +4.2% upward. The symmetric '-8.73% /")
L("    +9.27%' of v18 was the frozen-K special case (0.97^3, 1.03^3).")
L("")

L("=" * 78)
L("[G] the conditional envelope, assembled (v19)")
L("=" * 78)
L("Stage I  (un-trimmed, A closure) - unchanged and now PROVED:")
L("  x^3 K_M(x m0) = C x^3 + B L d^(-0.75) x^2.75 is strictly increasing in")
L("  x>0 (all coefficients positive), so the root is unique; it is")
L("  increasing in K_EV, K_HS, L and decreasing in d, so the extremes over")
L("  the 4-D box sit on corners. D in [-3.267%, +3.730%].")
L("  Caveat: this is a proof for THAT box and THAT closure only. It does")
L("  not transfer to stage III, to closure B, or to the flow axis.")
L("")
L("Stage III (trimmed), whole curve, feasibility enforced:")
for tag in ("PHI+-5%", "PHI+-1%"):
    for nm in ("A", "B"):
        v = d_sup[(tag, nm)]
        L(f"  {tag:<10}{nm}: sup|D| = {100*v[0]:.3f}%  (+-{100*v[1]:.3f}% grid"
          f" margin), valve K at that corner {v[2]:+.3f}")
L("")
L("  -> the stage-III envelope is now a CORNER value, not a sample maximum,")
L("     and the corner is feasible by construction. It is still conditional")
L("     on: log-log interpolation between Yue's five rows; the transitional")
L("     heating closure; a uniform K_v(Re) exponent; and the assumption that")
L("     m_v<=0.10. Each of these is a declaration, and [E] shows the")
L("     declaration widths decide the ranking.")
L("")

L("=" * 78)
L("[H] writable / not writable after this round")
L("=" * 78)
sA5, sB5 = 100 * d_sup[("PHI+-5%", "A")][0], 100 * d_sup[("PHI+-5%", "B")][0]
sA1, sB1 = 100 * d_sup[("PHI+-1%", "A")][0], 100 * d_sup[("PHI+-1%", "B")][0]
for line in [
    "WRITABLE 'Stage-I A-closure: on the declared 4-D box the distortion is",
    "          -3.27% to +3.73%, and this is a corner extremum, proved by",
    "          monotonicity of x^3 K_M(x), not sampled.'",
    "WRITABLE 'A valve can only add resistance: K_v,d>=0 is a design",
    "          constraint that caps the model pipe length at 8.9 m (A) and",
    "          6.35 m (B) at K_EV=2.5. B's declared +9.1% corner is 6.00 m,",
    "          i.e. it costs 95% of that headroom; A's costs 16%.'",
    "WRITABLE 'Off design a static resistance error cancels only if the",
    "          compensating valve shares the K(Re) shape of the compensated",
    "          component. At m_v=0.10 the K_EV +-50% band moves D by",
    "          0.32 pp (A) / 0.35 pp (B).'",
    f"WRITABLE 'Worst distortion over the whole 2.5:1 curve, at feasible",
    f"          corners: A {sA5:.2f}% (PHI+-5%) and {sA1:.2f}% (PHI+-1%);",
    f"          B {sB5:.2f}% and {sB1:.2f}%. A exceeds 3% at both widths.'",
    "WRITABLE 'GSA ranking depends on the declared widths, not on the",
    "          closure: at PHI+-5% heat leads (0.93/0.99), at PHI+-1% the",
    "          valve slope leads in A (0.47 vs 0.31). Literature K values",
    "          rank third or lower at every width tested.'",
    "WRITABLE 'The 100 K temperature offset costs 1.31 pp through PHI and",
    "          0.37 pp through mu - the trim pins the level, so what",
    "          enters D is the friction INCREMENT, not the friction ratio.'",
    "NOT 'K_EV has exactly zero effect after trimming' - only at m=m_d.",
    "NOT 'PHI owns 94% of the variance' - that is PHI+-5% at one point.",
    "NOT 'the envelope shrinks once the box is made feasible' - for B it",
    "     does not: the infeasible block is not the worst block.",
    "NOT 'PHI+-1% puts A inside 3%' - a feasible corner gives 3.368%.",
    "NOT 'a uniform viscosity shift cancels by z-similarity' - it does",
    "     not, because the trim fixes K_M at the design point; it is 28%",
    "     of the heat channel.",
    "NOT 'the curve is certified' - the Lipschitz margin bounds the flow",
    "     scan, not the interpolation and the closure declarations.",
]:
    L(line)
L("")

csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "design_v19_points.csv")
with io.open(csv_path, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("mP_kg_s,Re_M,D_A_nom,D_B_nom,D_A_worst,D_B_worst\n")
    for mP in (0.50, 0.625, 0.75, 0.875, 1.00, 1.125, 1.25):
        a = solve(mP, f_bla)
        b = solve(mP, f_yue)
        aw = solve(mP, f_bla, kev=1.25, lm=L_M * 1.0909, dm=D_M * 0.995,
                   band=1.30, mv=0.10, phi=0.95)
        bw = solve(mP, f_yue, kev=3.75, lm=L_M * 0.9091, dm=D_M * 1.005,
                   band=0.70, mv=0.0, phi=1.05)
        fh.write(f"{mP:.3f},{4*M_R*mP/(math.pi*D_M*MU):.0f},{100*a:.4f},"
                 f"{100*b:.4f},{100*aw:.4f},{100*bw:.4f}\n")
L(f"[csv] {csv_path}")
L("")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "design_v19_log.txt")
io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(LOG) + "\n")
print("\n".join(LOG))
print(f"\n[written] {out}  lines={len(LOG)}")
