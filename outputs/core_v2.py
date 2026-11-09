"""v2 core: the frozen conditional input domain, one forward model.

Differences from the archived v1 core (`forward_v1_original_20261109.py`):

  * P's resistance is Yue (2017) Table 2, five printed rows of K(Re_tube),
    interpolated piecewise-linearly in tube Reynolds number.  The single
    K = 22.8 used in v1 is the mdot = 1.25 kg/s row of that table and is kept
    only as a comparator branch.
  * The interpolated K is evaluated inside `march` from the same `Re` that
    march already needs, so there is no second pass and no stale K.
  * The main box is ten axes.  k_P_fac, k_bend_fac and k_orif_fac are model
    FORM branches, not continuous uncertain parameters.
  * The FoM is named for what it measures: mass-flux deviation.

Neither the geometry nor the boundary condition is tuned to any output.
"""

from __future__ import annotations

import math

import numpy as np

G = 9.81
T_AMB = 293.15
T_IN_REF = 473.15          # declared controlled heater-inlet boundary, both sides
Q_REF_M = 6000.0
Q_REF_P = 17900.0

A_R = (0.016 / 0.026) ** 2      # (D_M/D_P)^2 = A_M/A_P, fixed before solving
Q_LO = 3000.0
Q_HI = 6000.0


# ---------------------------------------------------------------- properties
def rho_of(T, f=1.0):
    return f * (11065.0 - 1.293 * T)


def cp_of(T, f=1.0):
    return f * (164.8 - 3.94e-2 * T + 1.25e-5 * T * T - 4.56e5 / (T * T))


def mu_of(T, f=1.0):
    return f * 4.94e-4 * math.exp(754.1 / T)


# ---------------------------------------------------------------- components
def churchill(Re, rel_rough=0.0):
    """NEA Table 15.3.2 #6, circular pipe, all Re."""
    Re = max(Re, 1e-6)
    inner = (7.0 / Re) ** 0.9 + 0.27 * rel_rough
    a = (2.457 * math.log(1.0 / inner)) ** 16
    b = (37530.0 / Re) ** 16
    return 8.0 * ((8.0 / Re) ** 12 + (a + b) ** -1.5) ** (1.0 / 12.0)


def elbow_mitre(Re):
    """Al-Tameemi & Ricco 2018 Eq (4), 500 <= Re <= 60000, 90 deg sharp mitre."""
    return 427.5 * Re ** -0.77 + 0.9


def orifice_nea3(D_main, d_hole, t):
    """NEA Table 15.3.3 #3, finite thickness, Re_D > 1e3."""
    beta = (d_hole / D_main) ** 2
    c = 1.0 - beta
    ell = t / D_main
    inv = ell ** -8
    phi = 0.25 + 0.535 * inv / (0.05 + inv)
    tau = (2.4 - ell) * 10.0 ** (-phi)
    return (0.5 * c + c * c + tau * c ** 1.5) / beta ** 2


def orifice_nea2(D_main, d_hole, t):
    """NEA Table 15.3.3 #2, Re_D > 1e4 only.  Cross-check branch only."""
    beta = (d_hole / D_main) ** 2
    ell = t / D_main
    xi = 0.13 + 0.34 * 10.0 ** (-(3.4 * ell + 88.4 * ell ** 2.3))
    return (1.0 - beta + math.sqrt(xi) * (1.0 - beta) ** 0.375) ** 2 / beta ** 2


def u_ins(r_out, t_ins=0.050, k_ins=0.050, f_bridge=0.20):
    return 2.0 * math.pi * k_ins / math.log((r_out + t_ins) / r_out) * (1.0 + f_bridge)


# ---------------------------------------------------------------- Yue Table 2
# Yue 2017 NST 28:39, Table 2, printed page 4.  AUTHOR'S THEORETICAL VALUES,
# not component measurements.  All K terms are referred to the main-pipe
# dynamic head.  Columns: Re_tube, K_pipe, K_HS, K_EV, K_total.
TABLE2 = (
    (5560.0, 19.1, 2.9, 2.5, 24.5),
    (11100.0, 18.9, 2.8, 2.5, 24.2),
    (16700.0, 18.5, 2.8, 2.5, 23.8),
    (22300.0, 18.1, 2.7, 2.5, 23.3),
    (27800.0, 17.7, 2.6, 2.5, 22.8),
)
T2_LO = TABLE2[0][0]
T2_HI = TABLE2[-1][0]


def table2_k(re, clamp=False):
    """Piecewise-linear K(Re_tube).  Raises outside the printed range.

    Extrapolation is refused rather than clamped: a root outside 5560-27800
    would not be supported by the source table at all.  `clamp=True` is used
    only while bracketing a root; the accepted root is always re-evaluated
    with clamp=False.
    """
    if not (T2_LO <= re <= T2_HI):
        if not clamp:
            raise ValueError("Re %.1f outside Table 2 printed range" % re)
        return TABLE2[0][1:4] if re < T2_LO else TABLE2[-1][1:4]
    for a, b in zip(TABLE2[:-1], TABLE2[1:]):
        if a[0] <= re <= b[0]:
            t = (re - a[0]) / (b[0] - a[0])
            kp = a[1] + t * (b[1] - a[1])
            kh = a[2] + t * (b[2] - a[2])
            kv = a[3] + t * (b[3] - a[3])
            return kp, kh, kv
    raise AssertionError("unreachable")


def table2_total(re):
    return sum(table2_k(re))


# ---------------------------------------------------------------- geometry
def build_specs():
    d_m = 0.016
    a_m = math.pi * d_m ** 2 / 4.0
    d_p = 0.026
    a_p = math.pi * d_p ** 2 / 4.0
    d_hs_o, d_hs_i = 0.054, 0.022

    m_segs = [
        ("M-HS",     "pipe", 1.00, d_m, +1.00, 1.0, False, u_ins(d_m / 2), 0.0, 0.0),
        ("M-riser",  "pipe", 2.00, d_m, +2.00, 0.0, False, u_ins(d_m / 2), 0.0, 0.0),
        ("M-top",    "pipe", 5.00, d_m,  0.00, 0.0, False, u_ins(d_m / 2), 0.0, 0.0),
        ("M-cooler", "pipe", 1.00, d_m, -1.00, 0.0, True,  0.0,             0.0, 0.0),
        ("M-down",   "pipe", 2.00, d_m, -2.00, 0.0, False, u_ins(d_m / 2), 0.0, 0.0),
        ("M-bottom", "pipe", 5.00, d_m,  0.00, 0.0, False, u_ins(d_m / 2), 0.0, 0.0),
    ]
    p_segs = [
        ("P-HS-act", "ann",  0.80, None, +0.80, 1.0, False, u_ins(d_hs_o / 2), 0.0, 0.0),
        ("P-HS-top", "ann",  1.00, None, +1.00, 0.0, False, u_ins(d_hs_o / 2), 0.0, 0.0),
        ("P-riser",  "pipe", 3.20, d_p,  +3.20, 0.0, False, u_ins(d_p / 2),  0.0, 0.0),
        ("P-top",    "pipe", 0.50, d_p,   0.00, 0.0, False, u_ins(d_p / 2),  0.0, 0.0),
        ("P-HX",     "pipe", 1.50, d_p,  -1.50, 0.0, True,  0.0,             0.0, 0.0),
        ("P-down",   "pipe", 3.50, d_p,  -3.50, 0.0, False, u_ins(d_p / 2),  0.0, 0.0),
        ("P-bot",    "pipe", 0.50, d_p,   0.00, 0.0, False, u_ins(d_p / 2),  0.0, 0.0),
    ]

    def mk(name, kind, Ln, D, dz, qfrac, cool, u, kown, kmain):
        if kind == "pipe":
            A = math.pi * D ** 2 / 4.0
            Dh = D
            per = math.pi * D
        else:
            A = math.pi * (d_hs_o ** 2 - d_hs_i ** 2) / 4.0
            Dh = d_hs_o - d_hs_i
            per = math.pi * (d_hs_o + d_hs_i)
        return dict(name=name, kind=kind, L=Ln, A=A, Dh=Dh, per=per, dz=dz,
                    qfrac=qfrac, cool=cool, u=u, kown=kown, kmain=kmain)

    P = dict(segs=[mk(*s) for s in p_segs], A_main=a_p, D_main=d_p,
             Q_ref=Q_REF_P, n_elbow=0, lumped=True,
             label="P / Yue 2017 KYLIN-II TH", k_p_mode="table2")
    M = dict(segs=[mk(*s) for s in m_segs], A_main=a_m, D_main=d_m,
             Q_ref=Q_REF_M, n_elbow=4, lumped=False,
             label="M / 16 mm, 16 m, 10x2 mm orifice", k_p_mode="none")
    return P, M


# ---------------------------------------------------------------- one loop
def march(loop, m, Qe, T_in, eps, k_bend, k_orif, k_aux, u_fac, fmu, fcp, frho,
          d_hole_scale=1.0, lhs_scale=1.0, k_clamp=False):
    """Forward energy march + buoyancy + friction for one loop at one flow.

    The cooler duty is not a free parameter: the heater inlet is pinned to
    T_in, so the cooler removes exactly what the balance leaves.
    """
    segs = loop["segs"]
    ic = next(i for i, s in enumerate(segs) if s["cool"])

    T = T_in
    means = [0.0] * len(segs)
    T_hs = None                    # bulk outlet of the first heated segment
    for i in range(ic):
        s = segs[i]
        sL = s["L"] * (lhs_scale if i == 0 else 1.0)
        q = (Qe * s["qfrac"] / sL) if s["qfrac"] > 0 else 0.0
        u = s["u"] * u_fac
        cpl = cp_of(T, fcp)
        a = u * sL / (m * cpl) if u > 0.0 else 0.0
        if a > 1e-12:
            Teq = T_AMB + q / u
            e = math.exp(-a)
            T_new = Teq + (T - Teq) * e
            Tm = Teq + (T - Teq) * (1.0 - e) / a
        else:
            T_new = T + q * sL / (m * cpl)
            Tm = 0.5 * (T + T_new)
        means[i] = Tm
        T = T_new
        if s["qfrac"] > 0.0 and T_hs is None:
            T_hs = T
    T_ci = T

    T = T_in
    for i in range(len(segs) - 1, ic, -1):
        s = segs[i]
        u = s["u"] * u_fac
        cpl = cp_of(T, fcp)
        a = u * s["L"] / (m * cpl) if u > 0.0 else 0.0
        if a > 1e-12:
            T_up = T_AMB + (T - T_AMB) * math.exp(a)
            means[i] = T_AMB + (T - T_AMB) * (math.exp(a) - 1.0) / a
            T = T_up
        else:
            means[i] = T
    T_co = T

    cp_m = cp_of(0.5 * (T_ci + T_co), fcp)
    qc = m * cp_m * (T_ci - T_co)
    means[ic] = 0.5 * (T_ci + T_co)
    if qc < 0.0:
        return None
    t_hot = T_ci + sum(segs[i]["u"] * u_fac * max(means[i] - T_AMB, 0.0) * segs[i]["L"]
                       for i in range(ic)) / (m * cp_of(T_ci, fcp))

    drho = 0.0
    dpf = 0.0
    k_brk = dict(pipe=0.0, bend=0.0, orifice=0.0, aux=0.0, hs=0.0, valve=0.0)
    tmax = T_in
    qloss = 0.0
    for i, s in enumerate(segs):
        Tm = means[i]
        r = rho_of(Tm, frho)
        mu = mu_of(Tm, fmu)
        v = m / (r * s["A"])
        Re = 4.0 * m / (s["per"] * mu)
        drho += r * s["dz"]
        tmax = max(tmax, Tm)
        if s["cool"]:
            continue
        if s["u"] > 0.0:
            qloss += s["u"] * u_fac * max(Tm - T_AMB, 0.0) * s["L"]
        if loop["lumped"]:
            continue
        f = churchill(Re, eps / s["Dh"])
        kf = f * s["L"] / s["Dh"]
        dpf += (kf + s["kown"] * k_bend) * r * v * v / 2.0
        k_brk["pipe"] += kf
        k_brk["bend"] += s["kown"] * k_bend
    dp_buoy = -G * drho

    r_mean = rho_of(float(np.mean(means)), frho)
    v_main = m / (r_mean * loop["A_main"])
    q_main = r_mean * v_main * v_main / 2.0
    re_main = 4.0 * m / (math.pi * loop["D_main"] * mu_of(float(np.mean(means)), fmu))

    if loop["n_elbow"]:
        kb = loop["n_elbow"] * elbow_mitre(re_main) * k_bend
        dpf += kb * q_main
        k_brk["bend"] += kb

    if loop["label"].startswith("M"):
        d_h = 0.010 * d_hole_scale
        ko = orifice_nea3(loop["D_main"], d_h, 0.002) * k_orif
        dpf += ko * q_main
        k_brk["orifice"] = ko
        dpf += k_aux * q_main
        k_brk["aux"] = k_aux
    else:
        mode = loop.get("k_p_mode", "table2")
        if mode == "table2":
            kpipe, khs, kvev = table2_k(re_main, clamp=k_clamp)
        elif mode == "frozen":
            kpipe, khs, kvev = 17.7, 2.6, 2.5
        elif mode == "churchill":
            # model-form branch: scale the published pipe term by the
            # Churchill ratio to the 1.25 kg/s row, same mean temperature
            re_ref = 4.0 * 1.25 / (math.pi * loop["D_main"]
                                   * mu_of(float(np.mean(means)), fmu))
            kpipe, khs, kvev = 17.7 * churchill(re_main) / churchill(re_ref), 2.6, 2.5
        else:
            raise ValueError(mode)
        dpf += (kpipe + khs + kvev) * q_main
        k_brk["pipe"] = kpipe
        k_brk["hs"] = khs
        k_brk["valve"] = kvev

    return dict(m=m, dp_buoy=dp_buoy, dp_fric=dpf, kbrk=k_brk, qc=qc,
                qloss=qloss, tmax=max(tmax, t_hot), t_hot=t_hot,
                t_ci=T_ci, t_co=T_co, t_hs=T_hs,
                d_t_hs=(T_hs - T_in) if T_hs is not None else float("nan"),
                re=re_main, v_main=v_main, r_mean=r_mean)


def solve(loop, Qe, T_in, **kw):
    """Bracket the flow by geometric expansion, then bisect."""
    kw.pop("dtin", None)
    kw.setdefault("d_hole_scale", 1.0)
    kw.setdefault("lhs_scale", 1.0)
    kw.setdefault("k_clamp", True)

    def resid(mm):
        r = march(loop, mm, Qe, T_in, **kw)
        if r is None:
            return None
        v = r["dp_buoy"] - r["dp_fric"]
        return v if math.isfinite(v) else None

    lo = 0.02
    rv = resid(lo)
    if rv is None or rv <= 0.0:
        return None
    hi = lo
    for _ in range(30):
        hi *= 1.7
        rv = resid(hi)
        if rv is None:
            return None
        if rv <= 0.0:
            break
    else:
        return None
    for _ in range(26):
        if hi - lo < 1e-9:
            break
        mid = 0.5 * (lo + hi)
        rv = resid(mid)
        if rv is None:
            return None
        if rv > 0.0:
            lo = mid
        else:
            hi = mid
    m = 0.5 * (lo + hi)
    kw["k_clamp"] = False                      # never accept a clamped root
    try:
        out = march(loop, m, Qe, T_in, **kw)
    except ValueError:
        return None
    if out is not None:
        out["resid"] = out["dp_buoy"] - out["dp_fric"]
    return out


# ---------------------------------------------------------------- input box
INPUTS = [
    # key, side, nominal, lo, hi, unit, identity, basis
    ("eps_M",      "M",   10.0,   0.0,  20.0, "um",  "declared tube finish",
     "10 um is a procurement spec, not a measured Ra; ks != Ra"),
    ("d_hole",     "M",   10.000, 9.980, 10.020, "mm", "declared hole tolerance",
     "a drawing spec, not a capability claim"),
    ("k_aux_M",    "M",   0.50,   0.00,  1.00, "-",   "unspecified M form loss",
     "flanges, supports, instrument pockets; no correlation available"),
    ("u_loss_fac", "both", 1.00,  0.80,  1.20, "-",   "insulation + bridges",
     "50 mm, k=0.05, +20 pct bridge allowance; ageing not measured"),
    ("mu_fac",     "both", 1.00,  0.92,  1.08, "-",   "NEA mu estimated error",
     "Table 2.19.3, +-8 pct, 400-1200 K"),
    ("cp_fac",     "both", 1.00,  0.93,  1.07, "-",   "NEA cp estimated error",
     "Table 2.19.3, +-7 pct, 400-1100 K"),
    ("rho_fac",    "both", 1.00,  0.992, 1.008, "-",  "NEA rho estimated error",
     "Table 2.19.3, +-0.8 pct, 400-1300 K"),
    ("dTin_P",     "P",    0.0,  -2.0,   2.0, "K",    "control error, P",
     "declared setpoint accuracy of the controlled heater inlet"),
    ("dTin_M",     "M",    0.0,  -2.0,   2.0, "K",    "control error, M",
     "declared setpoint accuracy of the controlled heater inlet"),
    ("L_HS_M",     "M",    1.000, 0.990, 1.010, "m",  "heater length tolerance",
     "declared fabrication tolerance"),
]

NAMES = [r[0] for r in INPUTS]
BOUNDS = [[r[3], r[4]] for r in INPUTS]
IDX = {n: i for i, n in enumerate(NAMES)}
X0 = np.array([r[2] for r in INPUTS], dtype=float)


def kw_from_vec(x):
    d = dict(zip(NAMES, x))
    kwP = dict(eps=0.0, k_bend=1.0, k_orif=1.0, k_aux=0.0,
               u_fac=d["u_loss_fac"], fmu=d["mu_fac"], fcp=d["cp_fac"],
               frho=d["rho_fac"], dtin=d["dTin_P"])
    kwM = dict(eps=d["eps_M"] * 1e-6, k_bend=1.0, k_orif=1.0, k_aux=d["k_aux_M"],
               u_fac=d["u_loss_fac"], fmu=d["mu_fac"], fcp=d["cp_fac"],
               frho=d["rho_fac"], dtin=d["dTin_M"],
               d_hole_scale=d["d_hole"] / 10.0, lhs_scale=d["L_HS_M"])
    return kwP, kwM


BASE_KWP, BASE_KWM = kw_from_vec(X0)
P, M = build_specs()


# ---------------------------------------------------------------- FoM
def fom(x, qe=Q_HI, k_p_mode="table2", k_bend=1.0, k_orif=1.0,
        P_=None, M_=None):
    """Return the paired roots and the pre-declared FoMs.

    D_j  = (m_M/A_M)/(m_P/A_P) - 1     mass-flux deviation, THE formal FoM
    D_T  = (A_M/A_P)(dT_HS_M/dT_HS_P) - 1   heater temperature-rise deviation
    D_v  = v_M/v_P - 1                 velocity deviation, separate name
    r_ref = A_M/A_P, so D_j = (m_M/m_P)/r_ref - 1 exactly.

    D_T uses the bulk rise across the FIRST HEATED SEGMENT on each side, from
    each side's own controlled inlet.  It is not a wall temperature and not a
    cooler or cold-leg temperature.  Its reference ratio A_P/A_M is a protocol
    choice of this study (same power AND same mass flux), not a H2TS result;
    it makes D_T vanish wherever D_j vanishes, which is why the two are not
    independent evidence.

    k_p_mode / k_bend / k_orif are MODEL FORM branches.  They are arguments,
    never sampled axes, and are reported separately from the ten-axis box.
    """
    P_ = P if P_ is None else P_
    M_ = M if M_ is None else M_
    P_["k_p_mode"] = k_p_mode
    kwP, kwM = kw_from_vec(np.asarray(x, dtype=float))
    kwP["k_bend"] = k_bend
    kwM["k_bend"] = k_bend
    kwM["k_orif"] = k_orif
    rm = solve(M_, qe, T_IN_REF + kwM["dtin"], **kwM)
    rp = solve(P_, qe, T_IN_REF + kwP["dtin"], **kwP)
    if rm is None or rp is None:
        return None
    return dict(
        qe=qe, rm=rm, rp=rp,
        d_j=100.0 * ((rm["m"] / rp["m"]) / A_R - 1.0),
        d_t=100.0 * (A_R * rm["d_t_hs"] / rp["d_t_hs"] - 1.0),
        d_traw=100.0 * (rm["d_t_hs"] / rp["d_t_hs"] - 1.0),
        d_v=100.0 * (rm["v_main"] / rp["v_main"] - 1.0),
        d_raw=100.0 * (rm["m"] / rp["m"] - 1.0),
    )


def d_j_of(x, qe=Q_HI, **branch):
    out = fom(np.asarray(x, dtype=float), qe, **branch)
    if out is None:
        raise ValueError("no paired root")
    return out["d_j"]
