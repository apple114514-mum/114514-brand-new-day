"""Design-input closure audit for the proposed 16 mm forward-only LBE loop.

Section [A] reproduces the submitted component audit from the NEA text alone.
Sections [B]-[H] ask a different question: can all of the submitted inputs be
true at the same time?  Where they cannot, the section names the input that
has to move and what moving it costs.

No bound, no GSA, no interval certificate is produced here.  A single-axis
sensitivity is a local evaluation, not an extremum.
"""

import math

# ---------------------------------------------------------------- substances
def mu_lbe(t):
    """NEA 2015 Table 2.19.3; 400-1200 K; declared tolerance 8%."""
    return 4.94e-4 * math.exp(754.1 / t)


def rho_lbe(t):
    """NEA 2015 Table 2.19.3; 400-1300 K; 0.8%."""
    return 11065.0 - 1.293 * t


def cp_lbe(t):
    """NEA 2015 Table 2.19.3; 400-1100 K; 7%."""
    return 164.8 - 3.94e-2 * t + 1.25e-5 * t * t - 4.56e5 / (t * t)


def beta_lbe(t):
    """Isobaric expansion from the density line: beta = 1.293/rho."""
    return 1.293 / rho_lbe(t)


# ---------------------------------------------------------------- components
def churchill(re, rel_rough=0.0):
    """NEA 2015 Table 15.3.2 eq. 6, circular pipe, all ranges."""
    inner = (7.0 / re) ** 0.9 + 0.27 * rel_rough
    a = (2.457 * math.log(1.0 / inner)) ** 16
    b = (37530.0 / re) ** 16
    return 8.0 * ((8.0 / re) ** 12 + (a + b) ** -1.5) ** (1.0 / 12.0)


def orifice_nea(d_main, d_hole, thick):
    """NEA 2015 Table 15.3.3 eq. 3; Re_D > 1000; referred to main-pipe head."""
    beta = (d_hole / d_main) ** 2
    comp = 1.0 - beta
    ell = thick / d_main
    inv = ell ** -8
    phi = 0.25 + 0.535 * inv / (0.05 + inv)
    tau = (2.4 - ell) * 10.0 ** (-phi)
    return (0.5 * comp + comp ** 2 + tau * math.sqrt(comp) * comp) / beta ** 2


def elbow_mitre(re):
    """Al-Tameemi/Ricco eq. 4; 90 deg sharp mitre; 500 <= Re <= 60000."""
    return 427.5 * re ** -0.77 + 0.9


def reynolds(mass, dia, mu):
    return 4.0 * mass / (math.pi * dia * mu)


# ---------------------------------------------------------------- declarations
D_M = 0.016             # m  model bore, submitted
D_O = 0.020             # m  model outer diameter, submitted
D_P = 0.026             # m  prototype bore (Yue Table 1)
L_P = 11.0              # m  prototype pipe length (Yue, "conservatively assumed")
H_P = 3.35              # m  prototype source-sink centre distance (FR26-170 Table 1)
H_M = 2.00              # m  model source-sink centre distance, submitted
M_D = 1.25              # kg/s  prototype design-point mass flow (Yue Table 2)
KP_TOT = 22.8           # prototype total K at that point (Yue Table 2)
KP_LO, KP_HI = 19.308, 24.318   # the 8.7 m and 12.0 m readings of K_P

A_M = math.pi * D_M ** 2 / 4.0
A_P = math.pi * D_P ** 2 / 4.0

ORIF_D, ORIF_T = 0.010, 0.002

L_SUB, RISE_SUB, FLAT_SUB = 16.0, 3.0, 5.0     # submitted layout
T_CHECK, M_CHECK = 573.15, 0.20                # submitted nominal check point

U_INS = 0.17574312024704186                     # W/(m K), submitted insulation
INS_LEN = 16.04 - 0.99
BRIDGE = 0.5                                    # W/K
T_AMB = 293.15

_OUT = []


def L(s=""):
    _OUT.append(s)


def rule(ch="-", n=78):
    L(ch * n)


# ============================================================ [A] reproduce
rule("=")
L("[A] the submitted component audit, recomputed from the NEA text")
rule("=")
re_nom = reynolds(M_CHECK, D_M, mu_lbe(T_CHECK))
f_nom = churchill(re_nom)
kp_nom = f_nom * L_SUB / D_M
ke_nom = 4.0 * elbow_mitre(re_nom)
ko_nom = orifice_nea(D_M, ORIF_D, ORIF_T)
kt_nom = kp_nom + ke_nom + ko_nom
L("    nominal: m = 0.20 kg/s, T = 573.15 K, bore 16 mm, 16 m, 4 mitre elbows")
L("    {:<26}{:>14}{:>14}".format("quantity", "this script", "submitted"))
for nm, a, b in (("Re main", re_nom, 8643.447004),
                 ("K_pipe (Churchill)", kp_nom, 32.284926),
                 ("K 4 elbows", ke_nom, 5.191282),
                 ("K orifice 10 mm x 2 mm", ko_nom, 5.593959),
                 ("K_total", kt_nom, 43.070166)):
    L("    {:<26}{:>14.6f}{:>14.6f}".format(nm, a, b))
L("    -> agrees to the printed digit; the arithmetic in the submitted audit is")
L("       correct and my reproduction adds nothing to it.")
L("")

# 576-row grid
rows = 0
re_lo, re_hi = 1e9, -1e9
kt_lo, kt_hi = 1e9, -1e9
for m in (0.10, 0.20, 0.40):
    for t in (473.15, 573.15, 773.15):
        for db in (0.01595, 0.01605):
            for dh in (0.00998, 0.01002):
                for th in (0.00195, 0.00205):
                    for ll in (15.96, 16.04):
                        for rr in (0.0, 10e-6):
                            for ka in (0.0, 0.5):
                                r = reynolds(m, db, mu_lbe(t))
                                kk = (churchill(r, rr / db) * ll / db
                                      + 4.0 * elbow_mitre(r)
                                      + orifice_nea(db, dh, th) + ka)
                                rows += 1
                                re_lo, re_hi = min(re_lo, r), max(re_hi, r)
                                kt_lo, kt_hi = min(kt_lo, kk), max(kt_hi, kk)
L("    scenario grid: {} rows, Re {:.0f}-{:.0f}, K_total {:.3f}-{:.3f}".format(
    rows, re_lo, re_hi, kt_lo, kt_hi))
L("    (a discrete diagnostic grid; the two numbers are not extrema of a")
L("     continuous domain and are not offered as such.)")
q_loss_773 = (U_INS * INS_LEN + BRIDGE) * (773.15 - T_AMB)
L("    heat-loss bound as submitted, evaluated at T_max = 773.15 K:")
L("      Q_loss <= {:.1f} W ; 3 kW - that = {:.1f} W".format(
    q_loss_773, 3000.0 - q_loss_773))
L("")

# ============================================================ [B] scale ledger
rule("=")
L("[B] is this loop a scale model of the prototype?")
rule("=")
l_r_D = D_M / D_P
l_r_L = L_SUB / L_P
l_r_H = H_M / H_P
A_r = A_M / A_P
K_r = kt_nom / KP_TOT
L("    the three length scales of the submitted layout:")
L("      bore     16.00 / 26.00 mm   ->  l_r = {:.4f}".format(l_r_D))
L("      length   16.00 / 11.00 m    ->  l_r = {:.4f}".format(l_r_L))
L("      height    2.00 /  3.35 m    ->  l_r = {:.4f}".format(l_r_H))
L("    one number is not like the other two.  A scale model needs one l_r for")
L("    all three; here length is {:.2f}x the bore ratio.".format(l_r_L / l_r_D))
L("")
L("    the consequence is in L/D, which fixes how much of K is pipe friction:")
L("      prototype  L/D = 11.00/0.026 = {:.1f}".format(L_P / D_P))
L("      model      L/D = 16.00/0.016 = {:.1f}".format(L_SUB / D_M))
L("      ratio                        = {:.2f}".format((L_SUB / D_M) / (L_P / D_P)))
L("    and the prototype's own pipe term is K_pipe = 17.7 of 22.8, i.e. 77.6%.")
L("    The model's pipe term alone is {:.3f}, which is {:.1f}% of 22.8 -".format(
    kp_nom, 100.0 * kp_nom / KP_TOT))
L("    the pipe by itself already exceeds the whole target.")
L("")
L("    minimum K reachable with this topology (no orifice, smooth, K_aux = 0):")
for t in (473.15, 573.15, 773.15):
    r = reynolds(M_CHECK, D_M, mu_lbe(t))
    kk = churchill(r) * L_SUB / D_M + 4.0 * elbow_mitre(r)
    L("      T = {:.2f} K  Re = {:6.0f}  K = {:7.3f}".format(t, r, kk))
_r773 = reynolds(M_CHECK, D_M, mu_lbe(773.15))
_k773 = churchill(_r773) * L_SUB / D_M + 4.0 * elbow_mitre(_r773)
L("    -> the lowest of these, {:.3f}, is still {:.1f}% above 22.8.  Deleting the".format(
    _k773, 100.0 * (_k773 / KP_TOT - 1.0)))
L("       orifice cannot rescue it: the deficit is negative, and no manufacture")
L("       tolerance or roughness choice changes the sign.")
L("")

# ============================================================ [C] length window
rule("=")
L("[C] which length belongs to the submitted orifice?")
rule("=")
L("    hold bore, elbows, K_aux = 0 and the nominal check point, and ask what")
L("    pipe length makes K_total equal to 22.8 for a given orifice:")
L("      {:<12}{:>10}{:>10}{:>12}{:>10}".format(
    "orifice", "K_orif", "K_pipe", "L needed", "L/D"))
for dh in (0.010, 0.011, 0.012, 0.013):
    ko = orifice_nea(D_M, dh, ORIF_T)
    kp_need = KP_TOT - ke_nom - ko
    ll = kp_need * D_M / f_nom
    L("      {:<12}{:>10.3f}{:>10.3f}{:>12.3f}{:>10.0f}".format(
        "{:.0f} mm".format(dh * 1000), ko, kp_need, ll, ll / D_M))
ko_no = 0.0
ll_no = (KP_TOT - ke_nom) * D_M / f_nom
L("      {:<12}{:>10.3f}{:>10.3f}{:>12.3f}{:>10.0f}".format(
    "none", ko_no, KP_TOT - ke_nom, ll_no, ll_no / D_M))
L("")
L("    -> the submitted 10 mm hole pairs with L = 5.95 m, not 16.00 m.")
L("       At 16.00 m the same hole would need K_orifice = {:.3f}, i.e. a".format(
    KP_TOT - ke_nom - kp_nom))
L("       NEGATIVE resistance element.  The two numbers in the spec come from")
L("       two different loops.")
L("")
L("    and the 5.95 m is not reachable either: with 3.00 m risers (which the")
L("    declared H_eff = 2.00 m forces) the loop is already 6.00 m before any")
L("    horizontal run.  So the orifice has no length to live at.")
L("")

# ============================================================ [D] 155D vs target
rule("=")
L("[D] the 155D requirement and the 22.8 target cannot both hold at 16 mm")
rule("=")
L("    the spec asks for >= 155D from each bottom elbow to the orifice, i.e. a")
L("    bottom leg of 2 x 155D = 310D = {:.2f} m at 16 mm.".format(310 * D_M))
for dd in (0.016, 0.020, 0.026):
    ll = 310 * dd + 2 * 3.00 + 0.10
    r = reynolds(M_CHECK, dd, mu_lbe(T_CHECK))
    kp = churchill(r) * ll / dd
    kk = kp + 4.0 * elbow_mitre(r)
    L("      bore {:4.1f} mm: bottom leg {:.2f} m, L = {:.2f} m, L/D = {:.0f},"
      " K = {:.2f}".format(dd * 1000, 310 * dd, ll, ll / dd, kk))
L("    -> at 16 mm the requirement alone gives K = {:.2f}, {:.1f}% above 22.8,"
  .format(churchill(reynolds(M_CHECK, 0.016, mu_lbe(T_CHECK))) * (310 * 0.016 + 6.10) / 0.016
          + 4 * elbow_mitre(reynolds(M_CHECK, 0.016, mu_lbe(T_CHECK))),
          100.0 * ((churchill(reynolds(M_CHECK, 0.016, mu_lbe(T_CHECK))) * (310 * 0.016 + 6.10) / 0.016
                    + 4 * elbow_mitre(reynolds(M_CHECK, 0.016, mu_lbe(T_CHECK)))) / KP_TOT - 1.0)))
L("       before any orifice is added.  A larger bore relaxes it only because")
L("       the riser stays 3.00 m while D grows; it does not relax the pipe")
L("       friction share, which is what K/L/D fixes.")
L("")
L("    so the design has to give up one of: the 155D distance, the four-elbow")
L("    topology, the 2.00 m height, or the 22.8 target.  There is no fifth way")
L("    at this bore.")
L("")

# ============================================================ [E] calibers
rule("=")
L("[E] three distortions, because the formula's premise is not stated")
rule("=")
_kp17662 = churchill(reynolds(0.37, D_M, mu_lbe(620.0))) * L_SUB / D_M
_kp_op_early = _kp17662 + 4.0 * elbow_mitre(reynolds(0.37, D_M, mu_lbe(620.0)))
u_P = M_D / (rho_lbe(573.15) * A_P)
L("    prototype design point: m = 1.25 kg/s, u = {:.4f} m/s".format(u_P))
L("")
L("    (1) pure K ratio, the formula used since v16:")
L("        D_K = (K_M/K_P)^(-1/3) - 1")
for kk in (kt_nom,):
    for kp in (KP_TOT, KP_LO, KP_HI):
        L("          K_M = {:.3f}, K_P = {:.3f}  ->  D = {:+.3f}%".format(
            kk, kp, 100.0 * ((kk / kp) ** (-1.0 / 3.0) - 1.0)))
L("        This form assumes the driving head is the same on both sides, i.e.")
L("        H_M = H_P and dT_M = dT_P.  Here H_M/H_P = {:.3f}, so the premise".format(l_r_H))
L("        fails by 40% and the number above is not the velocity error.")
L("        The same expression at the loop's own operating point (Re 17662,")
L("        K = {:.2f}) gives D = {:+.2f}%; the deficit is smaller there because".format(
    _kp_op_early, 100.0 * ((_kp_op_early / KP_TOT) ** (-1.0 / 3.0) - 1.0)))
L("        f falls with Re, but it is still six times the 3% target.")
L("")
L("    (2) Froude-normalised, dT matched:")
L("        u_r = sqrt(H_r/K_r), target u_r* = sqrt(l_r), D_F = u_r/u_r* - 1")
L("        H_r = {:.4f}, l_r = {:.4f}, K_r = {:.4f}".format(l_r_H, l_r_D, K_r))
L("        u_r = {:.4f}, u_r* = {:.4f}, D_F = {:+.2f}%".format(
    math.sqrt(l_r_H / K_r), math.sqrt(l_r_D),
    100.0 * (math.sqrt(l_r_H / K_r) / math.sqrt(l_r_D) - 1.0)))
L("        the same with K_r = 1 (length corrected):")
L("        u_r = {:.4f}, D_F = {:+.2f}%".format(
    math.sqrt(l_r_H), 100.0 * (math.sqrt(l_r_H) / math.sqrt(l_r_D) - 1.0)))
L("        -> the height is consistent with the bore (0.597 against 0.615);")
L("           the whole distortion is the length.")
L("")
L("    (3) same heater power on both sides, Q_r = 1:")
L("        u_r = [H_r/(A_r K_r)]^(1/3) = {:.4f}".format(
    (l_r_H / (A_r * K_r)) ** (1.0 / 3.0)))
L("        this is not a similarity criterion, only 'one heater, two benches'.")
L("")
L("    which one is the paper's FoM is a declaration, not a calculation.")
L("    The first two are far outside 3%, and both are dominated by the same")
L("    input: L = 16.00 m.")
L("")

# ============================================================ [F] correlation
rule("=")
L("[F] the correlation domain the operating point actually visits")
rule("=")
L("    Churchill eq. 6 is not monotone in the transition.  Scan f(Re):")
lows, highs = [], []
prev = None
for i in range(2000, 6001, 1):
    fv = churchill(float(i))
    if prev is not None:
        d = fv - prev
        if d > 0:
            lows.append(i)
        else:
            highs.append(i)
    prev = fv
L("      d f/dRe > 0 between Re = {} and Re = {}".format(
    min(lows) if lows else 0, max(lows) if lows else 0))
f_peak = churchill(3115.0)
f_min = churchill(2200.0)
L("      local minimum at Re = 2200: f = {:.5f}".format(f_min))
L("      local maximum at Re = 3115: f = {:.5f}   (+{:.1f}% over the minimum)".format(
    f_peak, 100.0 * (f_peak / f_min - 1.0)))
L("    -> a steady state that sits on the rising branch has dK/dRe > 0, and the")
L("       uniqueness argument (3 + s_M > 0) used in v20 does not apply there.")
L("")
L("    the submitted admissibility window 0.10 <= m <= 0.40 kg/s:")
for m, t in ((0.10, 473.15), (0.10, 573.15), (0.40, 773.15)):
    r = reynolds(m, D_M, mu_lbe(t))
    L("      m = {:.2f}, T = {:.2f} K -> Re = {:6.0f}   {} ".format(
        m, t, r, "ABOVE peak" if r > 3115 else "ON RISING BRANCH") +
      "margin to peak {:+.0f}".format(r - 3115.0))
L("      with the 8% viscosity tolerance, the lowest of these becomes {:.0f}".format(
    reynolds(0.10, D_M, mu_lbe(473.15) * 1.08)))
L("    -> the lower flow bound clears the hump by {:.0f} in Re, i.e. 5%.".format(
    reynolds(0.10, D_M, mu_lbe(473.15)) - 3115.0))
L("       A -8% viscosity or a -5% flow puts it on the rising branch, where two")
L("       steady states are possible.  The lower bound should be 0.12 kg/s,")
L("       which gives Re = {:.0f}.".format(reynolds(0.12, D_M, mu_lbe(473.15))))
L("")

# ============================================================ [G] thermal
rule("=")
L("[G] the thermal boundary: the 1.510 kW is evaluated at a T the loop never sees")
rule("=")


def heat_loss(t_hot):
    return (U_INS * INS_LEN + BRIDGE) * (t_hot - T_AMB)


def coupled(q_elec, k_tot, t_in=473.15):
    """Quasi-1D steady operating point: buoyancy = friction, one bulk dT."""
    q_net = q_elec - 600.0
    d_t = 60.0
    for _ in range(400):
        t_avg = t_in + 0.5 * d_t
        u = (2.0 * 9.81 * beta_lbe(t_avg) * H_M * q_net
             / (k_tot * rho_lbe(t_avg) * A_M * cp_lbe(t_avg))) ** (1.0 / 3.0)
        mass = rho_lbe(t_avg) * A_M * u
        d_t = q_net / (mass * cp_lbe(t_avg))
        t_max = t_in + d_t
        q_net = q_elec - heat_loss(t_max)
    return q_net, u, mass, d_t, t_max, t_avg


for kk, tag in ((kt_nom, "K as submitted (43.07)"),
                (KP_TOT, "K corrected to 22.8")):
    L("    " + tag + ":")
    L("      {:<10}{:>10}{:>9}{:>9}{:>9}{:>9}{:>10}{:>9}".format(
        "Q_elec", "Q_net", "u", "m_dot", "dT", "T_max", "Re", "Q_loss"))
    for qe in (3000.0, 3900.0, 4600.0, 6000.0):
        qn, u, mass, dt, tmx, tav = coupled(qe, kk)
        re_ = reynolds(mass, D_M, mu_lbe(tmx))
        L("      {:>7.0f} kW{:>10.0f}{:>9.4f}{:>9.4f}{:>9.1f}{:>9.1f}{:>10.0f}{:>9.0f}".format(
            qe / 1000.0, qn, u, mass, dt, tmx, re_, heat_loss(tmx)))
L("    -> the loop runs at T_max = 536-607 K, not 773 K.  The submitted heat")
L("       bound therefore overstates the loss by 1.5-1.9x, and the line")
L("       '3 kW - 1.510 kW = 1.49 kW' is a bound on a hypothetical loop, not")
L("       on this one.  At 3 kW the real loss is about {:.0f} W.".format(
    heat_loss(coupled(3000.0, kt_nom)[4])))
L("")
L("    flow and temperature both land inside the declared window (0.10-0.40")
L("    kg/s, 473-773 K).  This part of the input set closes.")
L("")
L("    one thing the thermal solve exposes and cannot settle: the model runs")
L("    at 536-607 K, while the prototype's Table 2 implies 504.6 K and LI")
L("    2015 quotes 723 K as the bench's nominal temperature.  Those two")
L("    differ by 1.4x in viscosity.  Until the prototype's reference")
L("    temperature is declared, Re_r has no defined target.")
L("")

# power needed for Froude-similar velocity
u_target = math.sqrt(l_r_D) * u_P
for kk, tag in ((kt_nom, "K = 43.07"), (KP_TOT, "K = 22.80")):
    tav = 550.0
    q_need = (u_target ** 3 * kk * rho_lbe(tav) * A_M * cp_lbe(tav)
              / (2.0 * 9.81 * beta_lbe(tav) * H_M))
    L("    to reach u = sqrt(l_r) u_P = {:.4f} m/s with {}, Q_net = {:.1f} kW".format(
        u_target, tag, q_need / 1000.0))
    L("      i.e. Q_elec about {:.1f} kW.  The declared ceiling is 6 kW.".format(
        (q_need + heat_loss(600.0)) / 1000.0))
L("    -> at 6 kW the bench runs at {:.0f}% of the Froude velocity, so the".format(
    100.0 * coupled(6000.0, KP_TOT)[1] / u_target))
L("       heater is the binding input if velocity similarity is wanted.")
L("")

# cooler
for qe in (3000.0, 6000.0):
    qn, u, mass, dt, tmx, tav = coupled(qe, KP_TOT)
    q_c = qn - heat_loss(tmx)
    lmtd = ((tmx - 433.15) - (473.15 - 433.15)) / math.log((tmx - 433.15) / 40.0)
    L("    Q_elec {:.0f} kW: cooler duty {:.0f} W, LMTD {:.1f} K, UA needed"
      " {:.0f} W/K".format(qe / 1000.0, q_c, lmtd, q_c / lmtd))
L("    -> the declared UA >= 150 W/K is 5x the need; the cooler must be")
L("       throttled, i.e. it is a controlled boundary, not a fixed UA.")
L("")

# ============================================================ [H] design space
rule("=")
L("[H] what length the same separation rule gives if the orifice is removed")
rule("=")
L("    with an orifice in the bottom leg, the spec's 155D to the orifice forces")
L("    that leg to 310D = {:.2f} m, and L to 16 m.  Without an orifice the".format(
    310 * D_M))
L("    binding distance is elbow-to-elbow, and the correlation asks for 140D:")
L("      4 legs at >= 140D              L >= {:.2f} m".format(4 * 140 * D_M))
L("      but the risers are fixed by H = 2.00 m:  L = 2(3.00) + 2h, h >= 2.24")
L("      so the real floor is               L >= {:.2f} m".format(6.0 + 2 * 140 * D_M))
L("")
L("    at L = 11.00 m (h = 2.50 m, 156D) the loop gives, at its own operating")
L("    point (0.37 kg/s, 620 K, Re 17662):")
r_op = reynolds(0.37, D_M, mu_lbe(620.0))
kp_op = churchill(r_op) * 11.0 / D_M
ke_op = 4.0 * elbow_mitre(r_op)
L("      K_pipe {:.3f} + 4 elbows {:.3f} = K {:.3f}   against 22.8".format(
    kp_op, ke_op, kp_op + ke_op))
L("      -> D = {:+.3f}%".format(
    100.0 * (((kp_op + ke_op) / KP_TOT) ** (-1.0 / 3.0) - 1.0)))
L("    -> four mitre elbows already cost {:.1f} K.  The components the model does".format(
    ke_op))
L("       not have (expansion tank 2.5 + annular heater 2.6 = 5.1 K) are paid")
L("       for.  The orifice was never needed - and it is what forced 16 m,")
L("       which then cost more than the orifice could supply.")
L("")
L("    the orifice branch, for comparison (evaluated at the check point):")
L("      {:<7}{:>7}{:>7}{:>9}{:>12}{:>9}{:>9}{:>11}".format(
    "h (m)", "L (m)", "L/D", "K_pipe", "K (no orif)", "D_K %", "hole mm",
    "elb-elb/D"))
for h in (0.30, 1.00, 1.365):
    ll = 6.0 + 2.0 * h
    kp = f_nom * ll / D_M
    kt = kp + ke_nom
    need = KP_TOT - kt
    dk = 100.0 * ((kt / KP_TOT) ** (-1.0 / 3.0) - 1.0)
    if need > 0.05:
        lo, hi = 0.004, 0.0159
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if orifice_nea(D_M, mid, ORIF_T) > need:
                lo = mid
            else:
                hi = mid
        hole = "{:.2f}".format(1000 * 0.5 * (lo + hi))
    else:
        hole = "none"
    L("      {:<7.3f}{:>7.2f}{:>7.0f}{:>9.3f}{:>12.3f}{:>9.2f}{:>9}{:>11.0f}".format(
        h, ll, ll / D_M, kp, kt, dk, hole, h / D_M))
L("    -> with an orifice the feasible band is h <= 1.365 m, i.e. 85D, which")
L("       fails the 140D rule; without one, h = 2.50 m satisfies it and lands")
L("       on the target.  (The h = 2.50 row is absent here because at this")
L("       check point it gives K = 27.4, not 22.8; the same length is right")
L("       only at the operating point, which is the paragraph below.)")
L("")
L("    the design point is itself an undeclared input, and it moves L:")
L("      {:<34}{:>8}{:>8}{:>9}{:>9}".format(
    "evaluation point", "Re", "f", "L (m)", "h (m)"))
for tag, mass, temp in (("submitted check 0.20 kg/s, 573 K", 0.20, 573.15),
                        ("6 kW coupled operating point", 0.319, 582.4),
                        ("Froude point 0.37 kg/s, 620 K", 0.37, 620.0)):
    r = reynolds(mass, D_M, mu_lbe(temp))
    ff = churchill(r)
    ll = (KP_TOT - 4.0 * elbow_mitre(r)) * D_M / ff
    L("      {:<34}{:>8.0f}{:>8.5f}{:>9.2f}{:>9.2f}".format(
        tag, r, ff, ll, 0.5 * (ll - 6.0)))
L("    -> 8.7 to 11.0 m.  The spread is 26%, which is why the design point has")
L("       to be declared before the drawing is frozen.  None of the three is")
L("       16.00 m; the submitted length is 45-85% too long.")
L("")
L("    the recommended input set (a proposal, for the user to decide):")
L("      bore 16.00 mm, risers 3.00 m, horizontals 2.50 m, L = 11.00 m")
L("      no resistance element in the main path")
L("      4 mitre elbows at 156D elbow-to-elbow")
L("      K = {:.2f} at the operating point, against 22.8".format(kp_op + ke_op))
L("      pipe share {:.1f}%, elbow share {:.1f}%  (prototype 77.6 / 22.4)".format(
    100.0 * kp_op / (kp_op + ke_op), 100.0 * ke_op / (kp_op + ke_op)))
L("    the cost, stated plainly: l_r is 0.615 in bore and 0.597 in height but")
L("    1.00 in length.  This is a friction-similar loop, not a geometrically")
L("    similar one.  K and geometry cannot both be matched, and this design")
L("    chooses K because K is what sets the velocity.")
L("")
L("    single-axis evaluation at L = 11.00 m, 0.37 kg/s, 620 K (not an extremum):")


def kk_of(ll=11.0, db=0.016, rr=0.0, ka=0.0, mass=0.37, tt=620.0):
    r = reynolds(mass, db, mu_lbe(tt))
    return churchill(r, rr / db) * ll / db + 4.0 * elbow_mitre(r) + ka


def dv(kk):
    return 100.0 * (math.sqrt(l_r_H / (kk / KP_TOT)) / math.sqrt(l_r_D) - 1.0)


L("      {:<34}{:>12}{:>12}{:>10}".format("axis", "K", "D_F %", "delta pp"))
base = kk_of()
L("      {:<34}{:>12.4f}{:>12.3f}".format("nominal", base, dv(base)))
for tag, kw in (("legs +0.01 m each (L +0.04)", dict(ll=11.04)),
                ("legs -0.01 m each", dict(ll=10.96)),
                ("bore +0.05 mm", dict(db=0.01605)),
                ("bore -0.05 mm", dict(db=0.01595)),
                ("roughness 10 um", dict(rr=10e-6)),
                ("K_aux 0.5", dict(ka=0.5))):
    kk = kk_of(**kw)
    L("      {:<34}{:>12.4f}{:>12.3f}{:>+10.2f}".format(
        tag, kk, dv(kk), dv(kk) - dv(base)))
L("    -> roughness (-2.0 pp) and K_aux (-1.1 pp) dominate; the length and bore")
L("       tolerances are worth 0.2 pp together.  Both dominant items are")
L("       acceptance conditions on the drawing, not measured values, and both")
L("       act in the same direction: a rougher pipe or a real auxiliary port")
L("       makes K too high, i.e. the model too slow.")
L("")

rule("=")
L("SUMMARY")
rule("=")
L("  verified: 43.070, 1.510 kW, the 576-row grid, Re 8643.4, every component.")
L("  not verified, because it is false: that this loop is a scale model.")
L("    l_r = 0.615 (bore), 0.597 (height), 1.455 (length).")
L("    K_pipe alone 32.285 > 22.8 at the check point, 26.7 at the operating")
L("    point.  The orifice deficit is negative at both: -14.7 and -8.4.")
L("  closable: the thermal boundary.  m = 0.24-0.32 kg/s, T_max 536-583 K,")
L("    Q_loss 0.76-0.91 kW; all inside the declared window.")
L("  the one decision that closes it: drop the orifice, L = 11.0 m (h = 2.50),")
L("    which restores K = 22.85 at the operating point and 156D separation.")
L("")

with open("design_v24_log.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(_OUT) + "\n")
print("\n".join(_OUT))
