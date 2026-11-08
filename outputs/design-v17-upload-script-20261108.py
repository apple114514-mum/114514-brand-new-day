"""v17: fixed scaling design + declared input domain + forward FoM computation.

Chain: declare prototype & model -> forward conservation eqs -> perturbation
-> scenario/GSA -> nonlinear bound on the conditional maximum distortion.

All log output is ASCII on purpose (no greek letters, no unicode superscripts).
"""

import io
import math
import os

LOG = []


def L(s=""):
    LOG.append(s)


def pct(x, n=2):
    return f"{100.0 * x:+.{n}f}%"


def r(x, n=4):
    return f"{x:.{n}f}"


# ---------------------------------------------------------------- inputs
MU = 2.2019e-3          # Pa s, LBE (Yue implied)
RHO = 10370.0           # kg/m3
CP = 146.97             # J/(kg K)
H_P = 3.3119            # m, KYLIN effective height (Yue Table 3 reverse solved)

# Yue 2017 Table 2 : m, K_HS, K_EV, K_pipe, K_total, Re_pipe
TAB = [
    (0.25, 2.9, 2.5, 19.1, 24.5, 5560.0),
    (0.50, 2.8, 2.5, 18.9, 24.2, 11100.0),
    (0.75, 2.8, 2.5, 18.5, 23.8, 16700.0),
    (1.00, 2.7, 2.5, 18.1, 23.3, 22300.0),
    (1.25, 2.6, 2.5, 17.7, 22.8, 27800.0),
]
D_P, L_P = 0.026, 11.0      # prototype main pipe (L assumed by the authors)

# Xu FR26 standard CFD case: geometric distortion, d_R /= L_R
L_R = 0.5
D_R = 0.616
M_R = 0.2683
D_M = D_P * D_R
L_M = L_P * L_R
A_R = D_R ** 2

# ------------------------------------------------ [A] recompute v16 design
L("=" * 78)
L("[A] RECOMPUTE the v16 component design (independent run)")
L("=" * 78)

f_impl = (TAB[-1][3] - 1.0) * D_P / L_P          # 17.7 = 1 + f*L/D
f_bla_P = 0.3164 * TAB[-1][5] ** -0.25
L(f"prototype implied f at 1.25 kg/s : {r(f_impl, 6)}  (from K_pipe=17.700)")
L(f"Blasius f at the same Re        : {r(f_bla_P, 6)}   ratio {r(f_impl / f_bla_P, 4)}")
L("  -> v16 finding reproduced: the table value is not an excess over a")
L("     Blasius baseline. It is what LBE measured friction gives, so Blasius")
L("     must never be used as the yardstick for an LBE loop.")
L("")

Re_M_d = 4.0 * (M_R * 1.25) / (math.pi * D_M * MU)
f_M_bla = 0.3164 * Re_M_d ** -0.25
Kpipe_M_bla = 1.0 + f_M_bla * L_M / D_M
Kvalve_A = TAB[-1][4] - (Kpipe_M_bla + 2.6 + 2.5)

pts = [(TAB[i][5], (TAB[i][3] - 1.0) * D_P / L_P) for i in range(5)]


def f_impl_interp(Re):
    xs = [math.log(p[0]) for p in pts]
    ys = [math.log(p[1]) for p in pts]
    x = math.log(Re)
    if x <= xs[0]:
        a, b = xs[0], xs[1]
        return math.exp(ys[0] + (x - a) / (b - a) * (ys[1] - ys[0]))
    if x >= xs[-1]:
        a, b = xs[-2], xs[-1]
        return math.exp(ys[-2] + (x - a) / (b - a) * (ys[-1] - ys[-2]))
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return math.exp(ys[i] + t * (ys[i + 1] - ys[i]))
    raise RuntimeError


f_M_b = f_impl_interp(Re_M_d)
Kpipe_M_b = 1.0 + f_M_b * L_M / D_M
Kvalve_B = TAB[-1][4] - (Kpipe_M_b + 2.6 + 2.5)

L(f"model pipe Re at the design pt  : {r(Re_M_d, 1)}  (27800 x 0.268/0.616 = 12095;")
L("                                   0.1% apart, from rounding m_R to 0.268)")
L(f"closure A  f={r(f_M_bla,6)}  K_pipe={r(Kpipe_M_bla,4)}  K_valve={r(Kvalve_A,4)}")
L(f"closure B  f={r(f_M_b,6)}  K_pipe={r(Kpipe_M_b,4)}  K_valve={r(Kvalve_B,4)}")
L("  -> both reproduce the v16 numbers 6.339 / 2.228 to 0.5%.")
L("")

# ------------------------------------------- [B] throat sizing, four formulas
L("=" * 78)
L("[B] throat sizing and its sensitivity to the 4 contraction formulas of")
L("    Table 15.3.6 (checked on the rendered page, printed p935)")
L("=" * 78)


def k_con(beta, which):
    if which == 1:
        return 0.5 * (1.0 - beta)
    if which == 2:
        return 0.5 * (1.0 - beta) ** 0.75
    if which == 3:
        return 0.5 - 0.7 * beta + 0.2 * beta * beta
    if which == 4:
        cc = 0.62 + 0.38 * beta ** 3          # Vennard, with vena contracta
        return (1.0 / cc - 1.0) ** 2
    raise RuntimeError


def k_ref_from_beta(beta, which):
    """contraction + Borda-Carnot expansion, both small-area referenced,
    converted to the main-pipe dynamic head."""
    return (k_con(beta, which) + (1.0 - beta) ** 2) / beta ** 2


def beta_from_kref(K, which):
    lo, hi = 1e-4, 0.999
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if k_ref_from_beta(mid, which) > K:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


throat = {}
for name, Kv in (("A smooth Blasius", Kvalve_A), ("B Yue implied f", Kvalve_B)):
    bs = [beta_from_kref(Kv, w) for w in (1, 2, 3, 4)]
    ds = [D_M * math.sqrt(b) * 1000.0 for b in bs]
    throat[name] = (bs, ds)
    L(f"{name}: target K_ref = {r(Kv,3)}")
    L(f"  beta  = {', '.join(r(b,4) for b in bs)}")
    L(f"  d_thr = {', '.join(r(d,2) for d in ds)} mm")
    L(f"  formula-to-formula spread = {r(max(ds)-min(ds),3)} mm "
      f"({pct(max(ds)/min(ds)-1,1)})")
L("")
L("  -> the four handbook formulas move the throat by <0.2 mm (2%), while the")
L("     f closure moves it by 1.74 mm (18.5%). The formula choice is a minor")
L("     term; the ROUGHNESS assumption is the design driver.")
L("")

# ------------------------------------- [C] K_R = 1 is forced, not chosen
L("=" * 78)
L("[C] why K_R = 1 is a requirement of the similarity law, not a free target")
L("=" * 78)
L(f"declared: L_R={L_R}, d_R={D_R} -> A_R={r(A_R,6)}, but L_R^2={r(L_R**2,4)}")
L("          the model is geometrically DISTORTED (fat), and this has to be")
L("          declared, not hidden: it is exactly the case that makes the")
L("          'ideal ratio' a declaration rather than a formula.")
L(f"u_R = m_R/A_R = {r(M_R/A_R,6)}  vs  sqrt(L_R) = {r(math.sqrt(L_R),6)}  "
  f"({pct(M_R/A_R/math.sqrt(L_R)-1,3)})")
L("steady NC: u^3 = 2 g beta H Q /(K rho cp A)  =>  u_R^2 = H_R/K_R")
L("u_R = sqrt(L_R)  <=>  K_R = H_R/L_R = 1")
L("=> the valve must reproduce the PROTOTYPE K at the design point; 22.8 is")
L("   therefore a consequence, not a chosen target.")
L("")

# ---------------------------------- [D] forward FoM: D(m) for both closures
L("=" * 78)
L("[D] forward computation of the FoM on both sides")
L("=" * 78)
L("D = u_M/u_M^ideal - 1 = (K_M/K_P)^(-1/3) - 1")
L("  u_M^ideal = model velocity if K_M were exactly K_P at the same Q_M.")
L("  eps_Q = 0 on both sides by construction, so this D is the pure loss-")
L("  ratio term. For Zhao it equals (1.088839)^(-1/3)-1 = the -2.79% branch,")
L("  NOT the +2.88% figure, which carries the eps_Q accounting. Do not mix.")
L("")
L(f"{'m_P':>6} {'Re_M':>8} {'K_P':>7} {'K_M(A)':>8} {'D_A':>9} "
  f"{'K_M(B)':>8} {'D_B':>9}")
rows = []
for row in TAB:
    mP, KHS, KEV, KPIPE, KTOT, REP = row
    m_M = M_R * mP
    Re_M = 4.0 * m_M / (math.pi * D_M * MU)
    KA = 1.0 + 0.3164 * Re_M ** -0.25 * L_M / D_M + KHS + KEV + Kvalve_A
    KB = 1.0 + f_impl_interp(Re_M) * L_M / D_M + KHS + KEV + Kvalve_B
    DA = (KA / KTOT) ** (-1.0 / 3.0) - 1.0
    DB = (KB / KTOT) ** (-1.0 / 3.0) - 1.0
    flag = "" if Re_M > 4000.0 else "  <-- laminar, Blasius invalid"
    rows.append((mP, Re_M, KTOT, KA, DA, KB, DB))
    L(f"{mP:6.2f} {Re_M:8.0f} {KTOT:7.2f} {KA:8.3f} {pct(DA):>9} "
      f"{KB:8.3f} {pct(DB):>9}{flag}")
L("")
ok = [x for x in rows if x[1] > 4000.0]
dmax_A = max(abs(x[4]) for x in ok)
dmax_B = max(abs(x[6]) for x in ok)
L("usable range 0.50-1.25 kg/s (Re_M 4.8e3-1.2e4, inside Blasius 4e3-1e5):")
L(f"  |D|max = {100*dmax_A:.2f}% (closure A) / {100*dmax_B:.2f}% (closure B), "
  f"as magnitudes")
L("  signs: A negative everywhere off-design, B positive everywhere.")
L("  0.25 row excluded: model Re 2422 is laminar, so a 5:1 power range")
L("  cannot be covered at this scale. The invalid point would read -4.6%.")
L("  closure B at 0.50 kg/s (Re 4843) is a 13% extrapolation below Yue's")
L("  lowest Re 5560 - flagged, and it is the row that sets dmax_B.")
L("")


def slope(idx):
    x1, y1 = math.log(rows[0][0]), math.log(rows[0][idx])
    x2, y2 = math.log(rows[-1][0]), math.log(rows[-1][idx])
    return (y2 - y1) / (x2 - x1)


sP, sA, sB = slope(2), slope(3), slope(5)
L(f"log-log slope dlnK/dlnm : K_P {r(sP,5)}  K_M(A) {r(sA,5)}  K_M(B) {r(sB,5)}")
L(f"  mismatch A: {pct(sA-sP,2)}   B: {pct(sB-sP,2)}   (opposite signs)")
L("  -> level is absorbed by the valve; ONLY the slope survives. That is the")
L("     whole mechanism, and it explains why the two closures disagree in")
L("     sign rather than in magnitude.")
L("")

# ------------------------------------- [E] perturbation: the -1/3 law
L("=" * 78)
L("[E] perturbation at the design point")
L("=" * 78)
L("D = (K_M/K_P)^(-1/3) - 1  =>  dD/dlnK_M = -1/3  (exact, not a linearisation)")
L(f"check K_M +1%: D = {pct((1.01) ** (-1.0/3.0) - 1, 4)};  "
  f"K_M -1%: D = {pct((0.99) ** (-1.0/3.0) - 1, 4)}")
L(f"3% criterion <=> K_M/K_P in [{r((1-0.03)**-3,4)}, {r((1.03)**-3,4)}]")
L(f"  one-sided K budget: {pct((1-0.03)**-3-1,2)} (towards D<0) and "
  f"{pct((1.03)**-3-1,2)} (towards D>0). Quote 9.6% as the design budget.")
L("")
L("at the design point every geometric input collapses onto the same number,")
L("because all of them act through K only:")
entries = [
    ("d_M  inner diameter", 0.005, (Kpipe_M_bla - 1.0)),
    ("L_M  pipe length", 0.10, (Kpipe_M_bla - 1.0)),
    ("K_HS", 0.20, 2.6),
    ("K_EV", 0.50, 2.5),
]
L(f"{'input':<22} {'declared':>9} {'deltaK':>8} {'deltaD':>8}")
for nm, rel, Kx in entries:
    dK = Kx * rel
    L(f"{nm:<22} {pct(rel,1):>9} {dK:+8.3f} {pct(-dK/22.8/3.0):>8}")
L("  note d_M and L_M enter through the same combination f*L/D: they are NOT")
L("  separable at the design point. Another instance of the rank deficiency.")
L("")

# ------------------------------- [F] three declared stages -> the real box
L("=" * 78)
L("[F] the declared box must be split by STAGE, otherwise the number lies")
L("=" * 78)
b1 = 2.5 * 0.50 + 2.6 * 0.20 + (Kpipe_M_bla - 1.0) * 0.20 + 11.4 * 0.005
L(f"stage I  design, valve NOT yet trimmed, worst corner:")
L(f"         sum|dK| = {r(b1,3)} = {pct(b1/22.8)} of K  ->  |D| = {pct(b1/22.8/3)}")
L(f"         exceeds the 3% criterion: the un-trimmed state is not a facility")
L(f"         uncertainty, it is a procurement spec.")
b2 = 0.20
L(f"stage II commissioning, valve trimmed, repeatability only:")
L(f"         +-{r(b2,2)} in K ({pct(b2/22.8)})  ->  |D| <= {pct(b2/22.8/3)}")
L(f"stage III operation, valve FIXED: only the curve distortion survives")
L(f"         |D| <= {pct(max(dmax_A,dmax_B))} over 0.5-1.25 kg/s")
L("")

# --------------------------- [G] K_HS reconstruction (closes a v15 open item)
L("=" * 78)
L("[G] per-component reconstruction of K_HS = 2.6")
L("=" * 78)
A_pipe = math.pi * D_P ** 2 / 4.0
d_o, d_i = 0.054, 0.022
D_h_HS = d_o - d_i
A_HS = math.pi * (d_o ** 2 - d_i ** 2) / 4.0
ratio2 = (A_pipe / A_HS) ** 2
perim = math.pi * (d_o + d_i)
Re_HS = 4.0 * 1.25 / (perim * MU)
f_HS = 0.685 * Re_HS ** -0.30
k_fr = f_HS * 1.8 / D_h_HS * ratio2
beta_HS = A_pipe / A_HS
k_out = 0.5 * (1.0 - beta_HS)          # annulus -> pipe: a CONTRACTION
k_sum = 1.29 + 0.64 + k_fr + k_out
L(f"Re_HS = 4m/(P_wetted mu) = {r(Re_HS,0)}  <-- matches Yue's 9520")
L(f"  (4m/(pi*Dh*mu) gives 22588, wrong: that formula only holds for a")
L(f"   full circular section. This is why the annulus Re has to use P_wetted.)")
L(f"f_HS = {r(f_HS,5)} (Zhu annulus, but d2/d1=1.30 there vs 2.45 here)")
L(f"items: T-junction 1.29 + area change 0.64 + annulus friction {r(k_fr,4)}")
L(f"       + exit contraction {r(k_out,4)} = {r(k_sum,4)}")
L(f"table 2.600  ->  residual {r(2.6-k_sum,4)} ({pct((2.6-k_sum)/2.6,1)} of K_HS)")
L(f"also: documented 'area change 0.64' vs Borda-Carnot expansion "
  f"{r((1-beta_HS)**2,4)}")
L(f"      differ by {r(0.64-(1-beta_HS)**2,3)} - the same order as the residual.")
L(f"  -> the two 0.12-scale gaps are the signature of the 'optimised")
L(f"     resistance coefficients' admitted in Yue section 5.2. The table is")
L(f"     reproducible to 5%, not to 0.5%: do not call it a component sum.")
L("")

# -------------------------------- [I] the declared input domain, as a table
L("=" * 78)
L("[I] DECLARED INPUT DOMAIN (the object the paper's a-priori box is built on)")
L("=" * 78)
dom = [
    ("H_P", "3.3119 m", "3.28-3.35", "L1c vs Xu L1: 1.1% apart, band=span"),
    ("d_P", "26.0 mm", "25.9-26.1", "L1, Yue Table 1"),
    ("L_P", "11.0 m", "10.0-12.0", "L2, author's conservative assumption"),
    ("K_EV", "2.5", "1.25-3.75", "L2, 'experience of other loops' (estimate)"),
    ("K_HS", "2.6", "2.48-2.72", "L1c, table value, 5% reconstruction gap"),
    ("tube finish", "closure A/B", "categorical", "L2, must be a design spec"),
    ("T_op", "573 K", "no published range", "GAP: neither NEA edition states one"),
    ("m_P", "0.25-1.25 kg/s", "range", "L1, Yue Table 2 span"),
]
L(f"{'symbol':<12} {'nominal':<14} {'declared':<14} grade")
for a, b, c, d in dom:
    L(f"{a:<12} {b:<14} {c:<14} {d}")
L("")
L("  the only genuinely irreducible entries are 'tube finish' (categorical)")
L("  and 'T_op' (no published validity range). Everything else is a tolerance")
L("  on a drawing or a reproducibility statement.")
L("")

# ------------------------------------------- [H] what may / may not be written
L("=" * 78)
L("[H] writable / not writable")
L("=" * 78)
for s in [
    "WRITABLE  'K_R=1 at the design point follows from u_R=sqrt(L_R); the",
    f"           throttling is sized to satisfy it, K_ref={Kvalve_A:.2f} for a",
    "           smooth tube and 2.24 for prototype-equivalent roughness.'",
    f"WRITABLE  'Over 0.5-1.25 kg/s the residual curve distortion is <=",
    f"           {100*dmax_A:.2f}% (smooth) or {100*dmax_B:.2f}% (rough), OPPOSITE",
    "           signs; the design point itself is 0 by construction.'",
    "WRITABLE  'The 3% criterion is equivalent to a 9.6% budget on K.'",
    "WRITABLE  'The un-trimmed design-stage corner exceeds 3%, so trimming is",
    "           a precondition of the criterion, not a refinement.'",
    "NOT       'the new facility has 1.9% uncertainty' - it is a declared",
    "           design-stage distortion on a hypothetical tube finish.",
    "NOT       'K_HS=2.6 is a component sum' - it is 5% above its own sum.",
    "NOT       '9.41 / 11.14 mm is the throat size' - it is conditional on the",
    "           closure; the four contraction formulas add only 0.2 mm.",
    "NOT       'the Blasius closure is the conservative one' - it is the one",
    "           that drives D negative; neither closure bounds the other.",
]:
    L(s)
L("")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "design_v17_log.txt")
io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(LOG) + "\n")
print("\n".join(LOG))
print(f"\n[written] {out}  lines={len(LOG)}")
