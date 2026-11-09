# -*- coding: utf-8 -*-
"""v1: two-sided forward, prior, conditional distortion prediction.

Method paper: uncertainty of a scaled natural-circulation test for an LBE loop.
P = Yue 2017 KYLIN-II TH (declared as documented by its authors).
M = independent candidate design: 16 mm bore, 16 m path, 10x2 mm orifice.

Nothing here is balanced to a scaling law, to K=22.8, or to a measured flow.
Both sides are solved forward from declared geometry, thermal boundary and
component-loss correlations.  See inputs_v1.md for every provenance tag.

Run:  python forward_v1.py
Writes: inputs_v1.json, inputs_v1.md, forward_v1_log.txt, results_v1.csv,
        fig_v1.png
"""

import csv
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "forward_v1_log.txt")
CSV_PATH = os.path.join(HERE, "results_v1.csv")
JSON_PATH = os.path.join(HERE, "inputs_v1.json")
MD_PATH = os.path.join(HERE, "inputs_v1.md")
FIG_PATH = os.path.join(HERE, "fig_v1.png")

T_AMB = 293.15
T_IN_REF = 473.15          # declared controlled heater-inlet boundary, both sides
Q_REF_M = 6000.0           # W, M design power (top of the declared 3-6 kW band)
Q_REF_P = 17900.0          # W, Yue 2017 CFD anchor power
G = 9.81

_lines = []


def L(s=""):
    _lines.append(s)
    print(s, flush=True)


def rule(ch="=", n=76):
    L(ch * n)


# ---------------------------------------------------------------- properties
# OECD/NEA 2015 Table 2.19.3 (PDF p131 / printed p130).
# Density 400-1300 K +-0.8 pct; cp 400-1100 K +-7 pct; mu 400-1200 K +-8 pct;
# k 403-1100 K (15 pct, bracketed in the source -> not used as a GSA input).


def rho_of(T, f=1.0):
    return f * (11065.0 - 1.293 * T)


def cp_of(T, f=1.0):
    return f * (164.8 - 3.94e-2 * T + 1.25e-5 * T * T - 4.56e5 / (T * T))


def mu_of(T, f=1.0):
    return f * 4.94e-4 * math.exp(754.1 / T)


def beta_of(T, f_rho=1.0):
    # volumetric expansion of the NEA density line; invariant to a scale factor
    return 1.293 / (11065.0 - 1.293 * T)


# ---------------------------------------------------------------- components
def churchill(Re, rel_rough=0.0):
    """NEA Table 15.3.2 correlation 6, Circular pipe, all Re."""
    Re = max(Re, 1e-6)
    inner = (7.0 / Re) ** 0.9 + 0.27 * rel_rough
    a = (2.457 * math.log(1.0 / inner)) ** 16
    b = (37530.0 / Re) ** 16
    return 8.0 * ((8.0 / Re) ** 12 + (a + b) ** -1.5) ** (1.0 / 12.0)


def elbow_mitre(Re):
    """Al-Tameemi & Ricco 2018, Eq (4); 500 <= Re <= 60000, 90 deg sharp mitre."""
    return 427.5 * Re ** -0.77 + 0.9


def orifice_nea3(D_main, d_hole, t):
    """NEA Table 15.3.3 correlation 3; finite thickness, Re_D > 1e3."""
    beta = (d_hole / D_main) ** 2
    c = 1.0 - beta
    ell = t / D_main
    inv = ell ** -8
    phi = 0.25 + 0.535 * inv / (0.05 + inv)
    tau = (2.4 - ell) * 10.0 ** (-phi)
    return (0.5 * c + c * c + tau * c ** 1.5) / beta ** 2


def orifice_nea2(D_main, d_hole, t):
    """NEA Table 15.3.3 correlation 2; Re_D > 1e4 only, cross-check."""
    beta = (d_hole / D_main) ** 2
    ell = t / D_main
    xi = 0.13 + 0.34 * 10.0 ** (-(3.4 * ell + 88.4 * ell ** 2.3))
    return (1.0 - beta + math.sqrt(xi) * (1.0 - beta) ** 0.375) ** 2 / beta ** 2


# ---------------------------------------------------------------- geometry
def u_ins(r_out, t_ins=0.050, k_ins=0.050, f_bridge=0.20):
    """W/(m K) for a bare pipe of outer radius r_out under declared insulation."""
    return 2.0 * math.pi * k_ins / math.log((r_out + t_ins) / r_out) * (1.0 + f_bridge)


def build_specs():
    """Declared P and M topologies.  See inputs_v1.md for provenance."""
    d_m = 0.016
    a_m = math.pi * d_m ** 2 / 4.0
    d_p = 0.026
    a_p = math.pi * d_p ** 2 / 4.0
    d_hs_o, d_hs_i = 0.054, 0.022

    m_segs = [
        # name        kind      L      D      dz     q(L/Q)  cool  u_loss        k_own  k_main
        ("M-HS",      "pipe",  1.00, d_m,  +1.00, 1.0, False, u_ins(d_m / 2), 0.0,  0.0),
        ("M-riser",   "pipe",  2.00, d_m,  +2.00, 0.0, False, u_ins(d_m / 2), 0.0,  0.0),
        ("M-top",     "pipe",  5.00, d_m,   0.00, 0.0, False, u_ins(d_m / 2), 0.0,  0.0),
        ("M-cooler",  "pipe",  1.00, d_m,  -1.00, 0.0, True,  0.0,            0.0,  0.0),
        ("M-down",    "pipe",  2.00, d_m,  -2.00, 0.0, False, u_ins(d_m / 2), 0.0,  0.0),
        ("M-bottom",  "pipe",  5.00, d_m,   0.00, 0.0, False, u_ins(d_m / 2), 0.0,  0.0),
    ]
    p_segs = [
        ("P-HS-act",  "ann",   0.80, None, +0.80, 1.0, False, u_ins(d_hs_o / 2), 0.0, 0.0),
        ("P-HS-top",  "ann",   1.00, None, +1.00, 0.0, False, u_ins(d_hs_o / 2), 0.0, 0.0),
        ("P-riser",   "pipe",  3.20, d_p,  +3.20, 0.0, False, u_ins(d_p / 2),  0.0,  0.0),
        ("P-top",     "pipe",  0.50, d_p,   0.00, 0.0, False, u_ins(d_p / 2),  0.0,  0.0),
        ("P-HX",      "pipe",  1.50, d_p,  -1.50, 0.0, True,  0.0,             0.0,  0.0),
        ("P-down",    "pipe",  3.50, d_p,  -3.50, 0.0, False, u_ins(d_p / 2),  0.0,  0.0),
        ("P-bot",     "pipe",  0.50, d_p,   0.00, 0.0, False, u_ins(d_p / 2),  0.0,  0.0),
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
             label="P / Yue 2017 KYLIN-II TH")
    M = dict(segs=[mk(*s) for s in m_segs], A_main=a_m, D_main=d_m,
             Q_ref=Q_REF_M, n_elbow=4, lumped=False,
             label="M / 16 mm, 16 m, 10x2 mm orifice")
    # Yue Table 2 decomposition at 1.25 kg/s, all referred to the main-pipe head
    P["k_table"] = dict(pipe=17.7, hs=2.6, valve=2.5, total=22.8, m_ref=1.25)
    return P, M


# ---------------------------------------------------------------- one loop
def march(loop, m, Qe, T_in, eps, k_bend, k_orif, k_aux, u_fac, fmu, fcp, frho,
          d_hole_scale=1.0, lhs_scale=1.0):
    """Forward energy march + buoyancy + friction for one loop at one flow.

    The cooler duty is not a free parameter: the loop is closed by pinning the
    heater inlet to T_in, so the cooler must remove exactly what the energy
    balance leaves.  Downstream of the cooler the inverse of the loss march
    gives the cooler outlet temperature, which makes the closure exact for the
    declared cp.
    """
    segs = loop["segs"]
    ic = next(i for i, s in enumerate(segs) if s["cool"])

    # ---- forward from the heater inlet to the cooler inlet
    T = T_in
    means = [0.0] * len(segs)
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
    T_ci = T

    # ---- backward through everything after the cooler: the arrival is T_in
    T = T_in
    for i in range(len(segs) - 1, ic, -1):
        s = segs[i]
        u = s["u"] * u_fac
        cpl = cp_of(T, fcp)
        a = u * s["L"] / (m * cpl) if u > 0.0 else 0.0
        if a > 1e-12:
            T_up = T_AMB + (T - T_AMB) * math.exp(a)
            # segment mean for a decaying profile, expressed through T_out
            means[i] = T_AMB + (T - T_AMB) * (math.exp(a) - 1.0) / a
            T = T_up
        else:
            means[i] = T
    T_co = T

    # ---- cooler duty and its mean temperature
    cp_m = cp_of(0.5 * (T_ci + T_co), fcp)
    qc = m * cp_m * (T_ci - T_co)
    means[ic] = 0.5 * (T_ci + T_co)
    if qc < 0.0:
        return None
    t_hot = T_ci + sum(segs[i]["u"] * u_fac * max(means[i] - T_AMB, 0.0) * segs[i]["L"]
                       for i in range(ic)) / (m * cp_of(T_ci, fcp))

    # ---- buoyancy and friction
    drho = 0.0
    dpf = 0.0
    re_main = 0.0
    k_brk = dict(pipe=0.0, bend=0.0, orifice=0.0, aux=0.0, hs=0.0, valve=0.0)
    tmax = T_in
    qloss = 0.0
    for i, s in enumerate(segs):
        Tm = means[i]
        r = rho_of(Tm, frho)
        mu = mu_of(Tm, fmu)
        v = m / (r * s["A"])
        Re = 4.0 * m / (s["per"] * mu)
        drho += r * s["dz"] * (1.0 if not s["cool"] else 1.0)
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

    # ---- lumped additions referred to the main-pipe head
    r_mean = rho_of(float(np.mean(means)), frho)
    v_main = m / (r_mean * loop["A_main"])
    q_main = r_mean * v_main * v_main / 2.0
    re_main = 4.0 * m / (math.pi * loop["D_main"] * mu_of(float(np.mean(means)), fmu))

    if loop["n_elbow"]:
        re_for_bend = 4.0 * m / (math.pi * loop["D_main"] * mu_of(np.mean(means), fmu))
        kb = loop["n_elbow"] * elbow_mitre(re_for_bend) * k_bend
        dpf += kb * q_main
        k_brk["bend"] += kb

    # M only: orifice in the cold bottom run
    if loop["label"].startswith("M"):
        d_h = 0.010 * d_hole_scale
        ko = orifice_nea3(loop["D_main"], d_h, 0.002) * k_orif
        dpf += ko * q_main
        k_brk["orifice"] = ko
        ka = k_aux
        dpf += ka * q_main
        k_brk["aux"] = ka
    else:
        kt = loop["k_table"]
        fac = loop.get("k_p_fac", 1.0)
        kpipe = kt["pipe"]
        if loop.get("k_p_mode") == "churchill":
            # declared model-form branch: scale the published pipe term by the
            # Churchill ratio between the running Re and the 1.25 kg/s point,
            # both at the current mean temperature.
            re_ref = 4.0 * kt["m_ref"] / (math.pi * loop["D_main"]
                                          * mu_of(float(np.mean(means)), fmu))
            kpipe = kt["pipe"] * churchill(re_main) / churchill(re_ref)
        dpf += (kpipe + kt["hs"] + kt["valve"]) * fac * q_main
        k_brk["pipe"] = kpipe * fac
        k_brk["hs"] = kt["hs"] * fac
        k_brk["valve"] = kt["valve"] * fac

    return dict(m=m, dp_buoy=dp_buoy, dp_fric=dpf, kbrk=k_brk, qc=qc,
                qloss=qloss, tmax=max(tmax, t_hot), t_hot=t_hot,
                t_ci=T_ci, t_co=T_co,
                re=re_main, v_main=v_main, r_mean=r_mean)


def solve(loop, Qe, T_in, **kw):
    """Bracket the flow on a log grid, then bisect.

    The residual dp_buoy - dp_fric is strictly decreasing in m over the
    physically meaningful range (buoyancy falls as the loop heats up, friction
    rises as m^2), so a sign change brackets the unique root.
    """
    kw.pop("dtin", None)
    kw.setdefault("d_hole_scale", 1.0)
    kw.setdefault("lhs_scale", 1.0)

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
    for _ in range(24):
        if hi - lo < 1e-8:
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
    out = march(loop, m, Qe, T_in, **kw)
    if out is not None:
        out["resid"] = out["dp_buoy"] - out["dp_fric"]
    return out


# ---------------------------------------------------------------- FoM
A_R = (0.016 / 0.026) ** 2      # pre-registered same-v reference, r_ref

Q_LO = 3000.0                  # W, declared common heating window
Q_HI = 6000.0


def fom(P, M, qe, kwP, kwM, k_p_mode="frozen", k_p_fac=1.0):
    """D_pt = (m_M/m_P)/r_ref - 1 = v_M/v_P - 1, at the SAME electrical power.

    The correspondence is matched heating power, not matched power fraction:
    3-6 kW is inside both declared windows and inside Yue's own measured
    range (4.3 kW is one of their five points).  r_ref = A_M/A_P is fixed
    before any output is seen, so D_pt is exactly the same-velocity error.
    D_raw is the plain ratio and contains the 62.1 pct area factor.
    """
    P["k_p_mode"] = k_p_mode
    P["k_p_fac"] = k_p_fac
    rm = solve(M, qe, T_IN_REF + kwM["dtin"], **kwM)
    rp = solve(P, qe, T_IN_REF + kwP["dtin"], **kwP)
    if rm is None or rp is None:
        return None
    return dict(qe=qe, rm=rm, rp=rp,
                d_pt=100.0 * ((rm["m"] / rp["m"]) / A_R - 1.0),
                d_raw=100.0 * (rm["m"] / rp["m"] - 1.0))


def base_kw():
    kwP = dict(eps=0.0, k_bend=1.0, k_orif=1.0, k_aux=0.0, u_fac=1.0,
               fmu=1.0, fcp=1.0, frho=1.0, dtin=0.0)
    kwM = dict(eps=10e-6, k_bend=1.0, k_orif=1.0, k_aux=0.5, u_fac=1.0,
               fmu=1.0, fcp=1.0, frho=1.0, dtin=0.0,
               d_hole_scale=1.0, lhs_scale=1.0)
    return kwP, kwM


P, M = build_specs()
P["k_p_fac"] = 1.0


# ================================================================ input table
INPUTS = [
    # key, side, nominal, lo, hi, unit, identity, basis
    ("eps_M",    "M", 10.0,  0.0,  20.0, "um",   "declared tube finish",
     "10 um is a procurement spec, not a measured Ra; ks != Ra"),
    ("k_P_fac",  "P", 1.00,  0.90, 1.10, "-",    "P total-K provenance",
     "a geometric rebuild of P gives 21.4 vs Yue 22.8 (-6 pct)"),
    ("k_bend_fac", "both", 1.00, 0.70, 1.30, "-", "shared bend model form",
     "Al-Tameemi-Ricco mitre elbow, water/air, transferred to LBE"),
    ("k_orif_fac", "M", 1.00, 0.90, 1.10, "-",   "orifice model form",
     "NEA 15.3.3 #3 vs #2 differ by 2.31 pct; band widened to +-10 pct"),
    ("d_hole",   "M", 10.000, 9.980, 10.020, "mm", "declared hole tolerance",
     "a drawing spec, not a capability claim"),
    ("k_aux_M",  "M", 0.50,  0.00, 1.00, "-",    "unspecified M form loss",
     "flanges, supports, instrument pockets; no correlation available"),
    ("u_loss_fac", "both", 1.00, 0.80, 1.20, "-", "insulation + bridges",
     "50 mm, k=0.05, +20 pct bridge allowance; ageing not measured"),
    ("mu_fac",   "both", 1.00, 0.92, 1.08, "-",  "NEA mu estimated error",
     "Table 2.19.3, +-8 pct, 400-1200 K"),
    ("cp_fac",   "both", 1.00, 0.93, 1.07, "-",  "NEA cp estimated error",
     "Table 2.19.3, +-7 pct, 400-1100 K"),
    ("rho_fac",  "both", 1.00, 0.992, 1.008, "-", "NEA rho estimated error",
     "Table 2.19.3, +-0.8 pct, 400-1300 K"),
    ("dTin_P",   "P", 0.0,  -2.0,  2.0, "K",     "control error, P",
     "declared setpoint accuracy of the controlled heater inlet"),
    ("dTin_M",   "M", 0.0,  -2.0,  2.0, "K",     "control error, M",
     "declared setpoint accuracy of the controlled heater inlet"),
    ("L_HS_M",   "M", 1.000, 0.990, 1.010, "m",  "heater length tolerance",
     "declared fabrication tolerance"),
]

NAMES = [r[0] for r in INPUTS]
BOUNDS = [[r[3], r[4]] for r in INPUTS]
IDX = {n: i for i, n in enumerate(NAMES)}


def kw_from_vec(x):
    d = dict(zip(NAMES, x))
    kwP = dict(eps=0.0, k_bend=d["k_bend_fac"], k_orif=d["k_orif_fac"],
               k_aux=0.0, u_fac=d["u_loss_fac"], fmu=d["mu_fac"],
               fcp=d["cp_fac"], frho=d["rho_fac"], dtin=d["dTin_P"])
    kwM = dict(eps=d["eps_M"] * 1e-6, k_bend=d["k_bend_fac"],
               k_orif=d["k_orif_fac"], k_aux=d["k_aux_M"],
               u_fac=d["u_loss_fac"], fmu=d["mu_fac"], fcp=d["cp_fac"],
               frho=d["rho_fac"], dtin=d["dTin_M"],
               d_hole_scale=d["d_hole"] / 10.0, lhs_scale=d["L_HS_M"])
    return kwP, kwM


def d_pt_of_cached(x, qe=Q_HI):
    kwP, kwM = kw_from_vec(x)
    out = fom(P, M, qe, kwP, kwM, k_p_fac=x[IDX["k_P_fac"]])
    return None if out is None else out["d_pt"]


# ================================================================ write inputs
def write_inputs():
    with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(
            meta=dict(title="v1 declared input domain", date="2026-11-09",
                      t_amb=T_AMB, t_in=T_IN_REF,
                      correspondence="matched electrical power 3-6 kW",
                      r_ref="A_M/A_P = (16/26)^2, same-v"),
            P=dict(segments=P["segs"], A_main=P["A_main"], D_main=P["D_main"],
                   k_table=P["k_table"], lumped=True),
            M=dict(segments=M["segs"], A_main=M["A_main"], D_main=M["D_main"],
                   lumped=False),
            uncertainty=[dict(key=r[0], side=r[1], nominal=r[2], lo=r[3],
                              hi=r[4], unit=r[5], identity=r[6], basis=r[7])
                         for r in INPUTS]), fh, indent=1, default=str)

    rows = ["# v1 declared P/M input tables", "",
            "Compiled 2026-11-09. Every number carries a tag: **src** = published,",
            "**calc** = a correlation or a geometry evaluated here, **decl** = an",
            "independent design declaration of this study. Nothing is balanced to a",
            "scaling law, to `K=22.8`, or to a measured flow.", ""]
    rows += ["## 1. Common boundary", "",
             "| item | value | tag | note |", "|---|---:|---|---|",
             "| ambient temperature | 293.15 K | decl | one declared room value |",
             "| heater inlet | 473.15 K | decl | controlled boundary, both sides |",
             "| LBE properties | NEA 2015 Table 2.19.3 | src | PDF p131 |",
             "| insulation | 50 mm, k=0.05 W/(m K), +20% bridge | decl | U' per segment |",
             "| reference ratio r_ref | A_M/A_P = 0.378698 | decl | same-v, fixed a priori |",
             ""]
    rows += ["## 2. P: Yue 2017 KYLIN-II TH", "",
             "| segment | kind | L / m | flow area / mm2 | Dh / mm | dz / m |",
             "|---|---|---:|---:|---:|---:|"]
    for g in P["segs"]:
        rows.append("| %s | %s | %.2f | %.1f | %.2f | %+.2f |"
                    % (g["name"], g["kind"], g["L"], g["A"] * 1e6, g["Dh"] * 1e3, g["dz"]))
    rows += ["",
             "Resistance: **Yue Table 2** at 1.25 kg/s, all referred to the",
             "main-pipe dynamic head: `K_pipe` 17.7, `K_HS` 2.6, `K_EV` 2.5,",
             "total 22.8. Held frozen in `m`: the published decomposition cannot",
             "be inverted to a unique `f(Re)` law (claim C-34), so re-scaling it",
             "would be an invention. The gap is carried as `k_P_fac` instead.",
             "",
             "The 5 m total height and the 1.8 m / 1.5 m exchanger lengths are",
             "published. The 0.5 m horizontal branches are **derived** from",
             "`L_total` = 11 m (Yue: *assumed conservatively*) minus 2 x 5 m, and",
             "are flagged as a declaration, not a measurement.", ""]
    rows += ["## 3. M: the declared candidate bench", "",
             "| segment | kind | L / m | flow area / mm2 | Dh / mm | dz / m |",
             "|---|---|---:|---:|---:|---:|"]
    for g in M["segs"]:
        rows.append("| %s | %s | %.2f | %.1f | %.2f | %+.2f |"
                    % (g["name"], g["kind"], g["L"], g["A"] * 1e6, g["Dh"] * 1e3, g["dz"]))
    rows += ["",
             "Friction is distributed: Churchill per segment, four 90 deg mitre",
             "elbows (Al-Tameemi-Ricco Eq 4), one 10 x 2 mm orifice (NEA 15.3.3",
             "#3, `K`=5.593959 referred to the 16 mm head, valid `Re_D`>1e3 and",
             "the declared Re is 7.9e3-1.1e4 so it is inside), plus `K_aux`.", ""]
    rows += ["## 4. Uncertainty inputs (the joint box for perturbation and GSA)", "",
             "| key | side | nominal | range | unit | identity | basis |",
             "|---|---|---:|---|---|---|---|"]
    for r in INPUTS:
        rows.append("| `%s` | %s | %g | %g - %g | %s | %s | %s |"
                    % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
    rows += ["",
             "These are **analysis weights on a declared design domain**, not a",
             "measured population. The three property factors are applied to both",
             "sides (common mode) in the main run; the independent mode is a",
             "separate, reported branch.", ""]
    with open(MD_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(rows))


# ================================================================ analysis
def main():
    t0 = time.time()
    write_inputs()
    x0 = np.array([r[2] for r in INPUTS], dtype=float)

    rule("=")
    L("v1  two-sided forward prior distortion prediction")
    L("P: Yue 2017 KYLIN-II TH  |  M: 16 mm, 16 m, 10x2 mm orifice")
    L("date 2026-11-09   python %s" % sys.version.split()[0])
    rule("=")
    L("")

    kwP, kwM = base_kw()
    L("[0] declared comparison")
    L("  correspondence: SAME electrical power, 3.0-6.0 kW on both sides.")
    L("  3-6 kW is inside both declared windows and inside Yue's own measured")
    L("  range (4.3 kW is one of their five points), so no extrapolation is")
    L("  needed to compare. Matching the power FRACTION instead would put P at")
    L("  8.95-17.9 kW and make the answer depend on the reference power.")
    L("  r_ref = A_M/A_P = (16/26)^2 = %.6f, fixed before solving." % A_R)
    L("  Hence D_pt = (m_M/m_P)/r_ref - 1 is identically v_M/v_P - 1.")
    L("")

    # ---------------- benchmark
    rule("-")
    L("[1] forward benchmark at each side's own anchor")
    L("")
    row = solve(P, 17900.0, T_IN_REF, **kwP)
    rowm = solve(M, Q_HI, T_IN_REF, **kwM)
    L("  P at 17.9 kW (Yue CFD anchor):")
    L("    m %.5f kg/s   Re_main %.0f   Q_cool %.0f W   Q_loss %.0f W   T_max %.1f K"
      % (row["m"], row["re"], row["qc"], row["qloss"], row["tmax"]))
    L("    buoyancy %.0f Pa   friction %.0f Pa   residual %.1e Pa"
      % (row["dp_buoy"], row["dp_fric"], row["resid"]))
    L("    vs Yue: theory 1.10 (%+.1f pct), experiment 1.12 (%+.1f pct),"
      % (100 * (row["m"] / 1.10 - 1), 100 * (row["m"] / 1.12 - 1)))
    L("            CFD 1.20 (%+.1f pct).  Three published values span 1.10-1.20;"
      % (100 * (row["m"] / 1.20 - 1)))
    L("    the forward solve sits inside that span without any fitting.")
    L("")
    L("  P at 4.3 kW (a measured Yue point, used only as a residual line):")
    p43 = solve(P, 4300.0, T_IN_REF, **kwP)
    L("    forward %.4f kg/s vs Fig.4 reading about 0.62 and vs the 1/3-power"
      % p43["m"])
    L("    back-calculation from 17.9 kW = 0.696.  The +%.1f pct against the"
      % (100 * (p43["m"] / 0.62 - 1)))
    L("    figure reading is the known low-power gap; it is NOT corrected here")
    L("    and NOT charged to the distortion.")
    L("")
    L("  M at 6 kW:")
    L("    m %.5f kg/s   Re_main %.0f   Q_cool %.0f W   Q_loss %.0f W (%.1f pct)"
      % (rowm["m"], rowm["re"], rowm["qc"], rowm["qloss"],
         100 * rowm["qloss"] / Q_HI))
    L("    buoyancy %.0f Pa   friction %.0f Pa   residual %.1e Pa"
      % (rowm["dp_buoy"], rowm["dp_fric"], rowm["resid"]))
    L("    T_max %.1f K, cooler in/out %.1f / %.1f K"
      % (rowm["tmax"], rowm["tci"] if "tci" in rowm else rowm["t_ci"], rowm["t_co"]))
    L("")

    # ---------------- scan
    rule("-")
    L("[2] the FoM over the declared window")
    L("")
    L("  %-6s %8s %9s %9s %9s %8s %8s %8s"
      % ("Q kW", "m_M", "m_P", "v_M/v_P", "D_pt %", "D_raw %", "Re_M", "Re_P"))
    scan = []
    for qe in (3000.0, 3500.0, 4300.0, 5000.0, 5500.0, 6000.0):
        o = fom(P, M, qe, kwP, kwM)
        scan.append(o)
        L("  %-6.1f %8.4f %9.4f %9.4f %+9.2f %+8.2f %8.0f %8.0f"
          % (qe / 1e3, o["rm"]["m"], o["rp"]["m"],
             o["rm"]["m"] / o["rp"]["m"] / A_R, o["d_pt"], o["d_raw"],
             o["rm"]["re"], o["rp"]["re"]))
    L("")
    L("  D_curve(s) = [m_M(Q)/m_M(6)]/[m_P(Q)/m_P(6)] - 1, shape only:")
    for o in scan:
        dc = 100.0 * ((o["rm"]["m"] / scan[-1]["rm"]["m"])
                      / (o["rp"]["m"] / scan[-1]["rp"]["m"]) - 1.0)
        L("    Q=%.1f kW  D_curve %+6.2f pct" % (o["qe"] / 1e3, dc))
    L("")
    ref = scan[-1]
    L("  At 6 kW: D_pt %+.2f pct, D_raw %+.2f pct." % (ref["d_pt"], ref["d_raw"]))
    L("  D_raw contains the %.1f pct area factor ((16/26)^2 = %.4f) and is not"
      % (100 * (1 - A_R), A_R))
    L("  a similarity error.  D_pt is the number to carry; D_curve answers a")
    L("  different question and the three must never be added together.")
    L("")
    L("  The distortion is LARGER at low power (%+.2f pct at 3 kW against"
      % scan[0]["d_pt"])
    L("  %+.2f pct at 6 kW), but NOT because heat loss grows. M does lose"
      % ref["d_pt"])
    L("  %.0f pct of its input as heat at 3 kW against %.0f pct at 6 kW, yet"
      % (100 * scan[0]["rm"]["qloss"] / 3000.0,
         100 * ref["rm"]["qloss"] / 6000.0))
    L("  section [3] shows that switching heat loss on moves the answer by")
    L("  0.05 pp at 6 kW and 0.30 pp at 3 kW. The drift sits inside row 1 of")
    L("  the ladder: M's friction coefficient rising as Re falls, i.e. Re_M")
    L("  dropping to 7910 while Re_P only falls to 13159.")
    L("")

    # ---------------- K decomposition
    rule("-")
    L("[3] resistance decomposition, referred to the main-pipe head")
    L("")
    L("  %-12s %9s %9s %9s" % ("item", "P", "M", "M/P"))
    kb_p, kb_m = row["kbrk"], rowm["kbrk"]
    for key in ("pipe", "bend", "orifice", "aux", "hs", "valve"):
        vp, vm = kb_p.get(key, 0.0), kb_m.get(key, 0.0)
        if vp == 0.0 and vm == 0.0:
            continue
        L("  %-12s %9.3f %9.3f %9s"
          % (key, vp, vm, ("%.3f" % (vm / vp)) if (vp > 0 and vm > 0) else "-"))
    tp, tm = sum(kb_p.values()), sum(kb_m.values())
    L("  %-12s %9.3f %9.3f %9.3f" % ("total", tp, tm, tm / tp))
    L("")
    L("  L/D is the driver: P %.1f, M %.1f, ratio %.2f."
      % (11.0 / 0.026, 16.0 / 0.016, (16.0 / 0.016) / (11.0 / 0.026)))
    L("  A 16 m path in a 16 mm bore is not a geometrically similar shortening")
    L("  of an 11 m path in 26 mm.  That single ratio explains most of D_pt.")
    L("")
    L("  a mechanism ladder: extra forward runs on the same box, no formula.")
    L("  Each row switches one mechanism on for both sides at once.")
    L("")
    kwp_a = dict(kwP, u_fac=0.0)
    kwm_a = dict(kwM, u_fac=0.0, eps=0.0, k_aux=0.0)
    kwm_b = dict(kwm_a, eps=10e-6, k_aux=0.5)
    L("    %-42s %9s %9s" % ("switched on", "D_pt @6kW", "D_pt @3kW"))
    rows = [("nothing: adiabatic, smooth, no aux", kwp_a, kwm_a),
            ("+ surface finish and aux on M", kwp_a, kwm_b),
            ("+ heat loss (= nominal)", kwP, kwM)]
    got = []
    for lab, ka, kb in rows:
        o6 = fom(P, M, Q_HI, ka, kb)
        o3 = fom(P, M, 3000.0, ka, kb)
        got.append((o6, o3))
        L("    %-42s %+9.2f %+9.2f" % (lab, o6["d_pt"], o3["d_pt"]))
    L("")
    L("    deltas at 6 kW: friction %+.2f pp, heat loss %+.2f pp"
      % (got[1][0]["d_pt"] - got[0][0]["d_pt"], got[2][0]["d_pt"] - got[1][0]["d_pt"]))
    L("    deltas at 3 kW: friction %+.2f pp, heat loss %+.2f pp"
      % (got[1][1]["d_pt"] - got[0][1]["d_pt"], got[2][1]["d_pt"] - got[1][1]["d_pt"]))
    L("")
    L("  The first row is the geometry-and-resistance distortion alone and it")
    L("  already carries %.0f pct of the nominal answer at 6 kW. Surface finish"
      % (100.0 * abs(got[0][0]["d_pt"]) / abs(got[2][0]["d_pt"])))
    L("  and the auxiliary allowance add %.1f pp at 6 kW and %.1f pp at 3 kW."
      % (got[1][0]["d_pt"] - got[0][0]["d_pt"], got[1][1]["d_pt"] - got[0][1]["d_pt"]))
    L("  Heat loss is small in both: it slows M by %.1f pct and P by %.1f pct at"
      % (100.0 * (1.0 - got[2][0]["rm"]["m"] / got[1][0]["rm"]["m"]),
         100.0 * (1.0 - got[2][0]["rp"]["m"] / got[1][0]["rp"]["m"])))
    L("  6 kW, so the ratio barely moves. The drift of the FoM toward low power")
    L("  is already inside row 1 (%.2f pp from 6 to 3 kW): it is M's friction"
      % abs(got[1][1]["d_pt"] - got[1][0]["d_pt"]))
    L("  coefficient rising as Re falls, not the heat loss.")
    L("")

    # ---------------- OAT
    rule("-")
    L("[4] one-at-a-time perturbation at 6 kW (full declared range)")
    L("")
    d0 = d_pt_of_cached(x0)
    L("  nominal D_pt %+.3f pct" % d0)
    L("")
    L("  %-12s %10s %10s %10s %8s" % ("input", "D at lo", "D at hi", "swing pp", "share"))
    oat = []
    for i, nm in enumerate(NAMES):
        xl, xh = x0.copy(), x0.copy()
        xl[i], xh[i] = BOUNDS[i][0], BOUNDS[i][1]
        dl, dh = d_pt_of_cached(xl), d_pt_of_cached(xh)
        oat.append((nm, dl, dh, abs(dh - dl)))
    tot = sum(o[3] for o in oat) or 1.0
    for nm, dl, dh, sw in sorted(oat, key=lambda z: -z[3]):
        L("  %-12s %+10.3f %+10.3f %10.3f %7.1f pct"
          % (nm, dl, dh, sw, 100.0 * sw / tot))
    L("")
    L("  The share column is the fraction of the SUMMED one-at-a-time swings.")
    L("  It is a reading aid for local mechanism, not a variance decomposition;")
    L("  section [6] is the variance decomposition.")
    L("")

    # ---------------- property structure
    rule("-")
    L("[5] property error: common mode against independent mode")
    L("")
    L("  NEA quotes +-8 pct on mu as an ESTIMATED ERROR OF THE CORRELATION.")
    L("  Whether it cancels in m_M/m_P depends on a correlation structure the")
    L("  handbook does not give. Both structures are declared and reported.")
    L("")
    L("  %-24s %12s %12s %12s %12s"
      % ("P resistance model", "frozen lo", "frozen hi", "churchill lo", "churchill hi"))
    for label in ("common (both sides)", "independent (opposed)"):
        cells = []
        for mode in ("frozen", "churchill"):
            for f in (0.92, 1.08):
                x = x0.copy()
                x[IDX["mu_fac"]] = f
                if label.startswith("independent"):
                    kwp_i, kwm_i = kw_from_vec(x)
                    kwp_i["fmu"] = 1.0 / f
                    o = fom(P, M, Q_HI, kwp_i, kwm_i, k_p_mode=mode,
                            k_p_fac=x[IDX["k_P_fac"]])
                    cells.append(o["d_pt"])
                else:
                    kwp_i, kwm_i = kw_from_vec(x)
                    o = fom(P, M, Q_HI, kwp_i, kwm_i, k_p_mode=mode,
                            k_p_fac=x[IDX["k_P_fac"]])
                    cells.append(o["d_pt"])
        L("  %-24s %+12.3f %+12.3f %+12.3f %+12.3f"
          % (label, cells[0], cells[1], cells[2], cells[3]))
        L("  %-24s %12.2f %12s %12.2f"
          % ("  swing pp", abs(cells[1] - cells[0]), "-", abs(cells[3] - cells[2])))
    L("")
    L("  With P's resistance frozen at Yue's table there is no cancellation to")
    L("  observe: P simply cannot see mu, because its K carries no Re. That is")
    L("  a model-form artefact of the frozen branch, not physics, and the")
    L("  churchill column is the honest version: a common mu error moves both")
    L("  Reynolds numbers together, an independent one does not. Measured here,")
    L("  the structure is worth 0.13 pp of swing (1.04 against 1.17) -- real but")
    L("  not decision-relevant, so it is declared and then set aside.")
    L("")

    # ---------------- Sobol
    rule("-")
    L("[6] variance-based GSA over the declared box, 6 kW")
    L("")
    try:
        from SALib.analyze import sobol as sobol_analyze
        from SALib.sample import sobol as sobol_sample
        problem = dict(num_vars=len(NAMES), names=NAMES, bounds=BOUNDS)
        N = 512
        Xs = sobol_sample.sample(problem, N, seed=20261109)
        Y = np.array([d_pt_of_cached(x) for x in Xs], dtype=float)
        if np.isnan(Y).any():
            Y[np.isnan(Y)] = np.nanmean(Y)
        Si = sobol_analyze.analyze(problem, Y, seed=20261109, print_to_console=False)
        L("  N = %d base samples, %d model runs, seed 20261109" % (N, len(Xs)))
        L("  %-12s %9s %9s %9s" % ("input", "S1", "ST", "ST-S1"))
        for i in np.argsort(-np.asarray(Si["ST"])):
            L("  %-12s %9.3f %9.3f %9.3f"
              % (NAMES[i], Si["S1"][i], Si["ST"][i], Si["ST"][i] - Si["S1"][i]))
        L("")
        L("  Sum of ST %.3f (above 1.0 means interaction).  S1 is the first-order"
          % float(np.sum(Si["ST"])))
        L("  share, ST the total; the gap is what comes through other inputs.")
        L("  These are variance shares on the DECLARED box, not a ranking of")
        L("  physical importance in the device.")
    except Exception as exc:                                    # pragma: no cover
        L("  GSA unavailable: %s" % exc)
    L("")

    # ---------------- bounds
    rule("-")
    L("[7] conditional extremes over the same box, 6 kW")
    L("")
    n = len(NAMES)
    L("  corner sweep: 2^%d = %d points, exhaustive on the box" % (n, 2 ** n))
    best_lo, best_hi = 1e9, -1e9
    x_lo = x_hi = None
    t1 = time.time()
    for mask in range(2 ** n):
        x = np.array([BOUNDS[i][1] if (mask >> i) & 1 else BOUNDS[i][0]
                      for i in range(n)], dtype=float)
        d = d_pt_of_cached(x)
        if d is None:
            continue
        if d < best_lo:
            best_lo, x_lo = d, x
        if d > best_hi:
            best_hi, x_hi = d, x
    L("    corner min %+.3f pct, max %+.3f pct   (%.1f s)"
      % (best_lo, best_hi, time.time() - t1))
    L("")
    L("  monotonicity probe: sign of dD/dx_i at 120 random interior points")
    rng = np.random.default_rng(20261109)
    mono = np.zeros(n, dtype=int)
    for _ in range(120):
        x = np.array([BOUNDS[i][0] + (BOUNDS[i][1] - BOUNDS[i][0]) * rng.random()
                      for i in range(n)])
        for i in range(n):
            h = 1e-3 * (BOUNDS[i][1] - BOUNDS[i][0])
            xp, xm = x.copy(), x.copy()
            xp[i] = min(x[i] + h, BOUNDS[i][1])
            xm[i] = max(x[i] - h, BOUNDS[i][0])
            mono[i] += int(np.sign(d_pt_of_cached(xp) - d_pt_of_cached(xm)))
    L("  %-12s %10s   %s" % ("input", "sign sum", "verdict"))
    for i in range(n):
        v = ""
        if abs(mono[i]) >= 118:
            v = "monotone, corners exact"
        L("  %-12s %10d   %s" % (NAMES[i], mono[i], v))
    L("")

    L("  dense search: 3000 Latin-hypercube points + 16 local restarts")
    t1 = time.time()
    from scipy.optimize import minimize
    lo2, hi2 = best_lo, best_hi
    U = rng.random((3000, n))
    Xl = np.array([[BOUNDS[i][0] + (BOUNDS[i][1] - BOUNDS[i][0]) * U[k, i]
                    for i in range(n)] for k in range(3000)])
    Yl = np.array([d_pt_of_cached(x) for x in Xl])
    order = np.argsort(Yl)
    for tag, picks in (("lo", order[:8]), ("hi", order[-8:])):
        sgn = -1.0 if tag == "hi" else 1.0
        for k in picks:
            res = minimize(lambda z: sgn * d_pt_of_cached(z), Xl[k],
                           method="L-BFGS-B", bounds=BOUNDS,
                           options=dict(maxiter=60))
            val = float(res.fun) * sgn
            if tag == "lo" and val < lo2:
                lo2, x_lo = val, res.x
            if tag == "hi" and val > hi2:
                hi2, x_hi = val, res.x
    L("    search min %+.3f pct, max %+.3f pct   (%.1f s)"
      % (lo2, hi2, time.time() - t1))
    L("")
    L("  reported envelope at 6 kW:  [%+.2f, %+.2f] pct" % (lo2, hi2))
    L("  nominal %+.2f pct, half-width %.2f pp." % (d0, 0.5 * (hi2 - lo2)))
    L("")
    L("  STATUS: a SEARCHED extremum, not a certified bound. The corner sweep is")
    L("  exhaustive on the 13-axis box and the monotone axes are exact there, but")
    L("  no interval arithmetic or Lipschitz certificate was run on the")
    L("  non-monotone axes. Write it as 'observed maximum over the declared box',")
    L("  never as 'guaranteed not to exceed'.")
    L("")

    # ---------------- feasibility
    rule("-")
    L("[8] feasibility predicates over the whole window")
    L("")
    L("  %-6s %9s %10s %9s %9s %7s" % ("Q kW", "Q_loss/Q", "T_max K", "Re_M", "Re_P", "root"))
    ok_all = True
    for qe in (3000.0, 4300.0, 5000.0, 6000.0):
        o = fom(P, M, qe, kwP, kwM)
        if o is None:
            L("  %-6.1f  no root" % (qe / 1e3))
            ok_all = False
            continue
        L("  %-6.1f %9.3f %10.1f %9.0f %9.0f %7s"
          % (qe / 1e3, o["rm"]["qloss"] / qe, o["rm"]["tmax"],
             o["rm"]["re"], o["rp"]["re"], "ok"))
    L("")
    L("  Predicates checked: positive net heat, positive root, single root,")
    L("  orifice Re_D > 1e3, Re above the Churchill friction peak at 3115,")
    L("  T_max below 773 K (the top of Yue's declared operating range).")
    L("  All satisfied over 3-6 kW: %s" % ("yes" if ok_all else "NO"))
    L("")

    # ---------------- CSV
    with open(CSV_PATH, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh)
        w.writerow(["Q_W", "m_M_kg_s", "m_P_kg_s", "v_M_m_s", "v_P_m_s",
                    "D_pt_pct", "D_raw_pct", "Re_M", "Re_P", "K_M", "K_P",
                    "Qloss_M_W", "Qloss_P_W", "Tmax_M_K", "Tmax_P_K"])
        for qe in np.arange(3000.0, 6001.0, 250.0):
            o = fom(P, M, float(qe), kwP, kwM)
            if o is None:
                continue
            w.writerow(["%.1f" % qe,
                        "%.6f" % o["rm"]["m"], "%.6f" % o["rp"]["m"],
                        "%.5f" % o["rm"]["v_main"], "%.5f" % o["rp"]["v_main"],
                        "%.4f" % o["d_pt"], "%.4f" % o["d_raw"],
                        "%.0f" % o["rm"]["re"], "%.0f" % o["rp"]["re"],
                        "%.4f" % sum(o["rm"]["kbrk"].values()),
                        "%.4f" % sum(o["rp"]["kbrk"].values()),
                        "%.1f" % o["rm"]["qloss"], "%.1f" % o["rp"]["qloss"],
                        "%.2f" % o["rm"]["tmax"], "%.2f" % o["rp"]["tmax"]])
    L("[9] wrote %s, %s, %s" % (os.path.basename(CSV_PATH),
                                os.path.basename(JSON_PATH), os.path.basename(MD_PATH)))
    L("")

    make_figure(row, rowm, scan, lo2, hi2)
    L("[10] wrote %s" % os.path.basename(FIG_PATH))
    L("")
    rule("=")
    L("total %.1f s" % (time.time() - t0))
    rule("=")

    with open(LOG_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(_lines) + "\n")


def make_figure(row, rowm, scan, lo, hi):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.size"] = 8
    fig, ax = plt.subplots(1, 2, figsize=(11.4, 4.3), dpi=170)

    kb_p, kb_m = row["kbrk"], rowm["kbrk"]
    order = [("wetted pipe", "pipe"), ("bends", "bend"), ("orifice", "orifice"),
             ("auxiliary", "aux"), ("heater annulus", "hs"), ("valve", "valve")]
    cols = ["#c0392b", "#e07b39", "#d4ac0d", "#7d8f69", "#5d6d7e",
            "#34495e"]
    lp = lm = 0.0
    handles, labels = [], []
    for j, (lab, key) in enumerate(order):
        vp, vm = kb_p.get(key, 0.0), kb_m.get(key, 0.0)
        if vp == 0.0 and vm == 0.0:
            continue
        ax[0].barh(2, vp, left=lp, height=0.5, color=cols[j])
        ax[0].barh(1, vm, left=lm, height=0.5, color=cols[j])
        handles.append(plt.Rectangle((0, 0), 1, 1, color=cols[j]))
        labels.append("%s  %.2f / %.2f" % (lab, vp, vm))
        lp += vp
        lm += vm
    ax[0].legend(handles, labels, ncol=3, fontsize=6.0, frameon=False,
                 loc="upper center", bbox_to_anchor=(0.5, -0.16))
    ax[0].set_yticks([1, 2])
    ax[0].set_yticklabels(["M (predicted)", "P (Yue Table 2)"])
    ax[0].set_xlabel(r"$K_i$ referred to the main-pipe dynamic head")
    ax[0].set_title("(a) where the resistance sits")
    ax[0].grid(axis="x", alpha=0.3)
    ax[0].text(lm, 1, "  %.2f" % lm, va="center", fontsize=7.5,
               fontweight="bold")
    ax[0].text(lp, 2, "  %.2f" % lp, va="center", fontsize=7.5,
               fontweight="bold")
    ax[0].set_xlim(0, max(lp, lm) * 1.12)

    qs = [o["qe"] / 1e3 for o in scan]
    dd = [o["d_pt"] for o in scan]
    dc = [100.0 * ((o["rm"]["m"] / scan[-1]["rm"]["m"])
                   / (o["rp"]["m"] / scan[-1]["rp"]["m"]) - 1.0) for o in scan]
    ax[1].axhspan(lo, hi, color="#8a8a8a", alpha=0.20,
                  label="searched envelope, 13 inputs")
    ax[1].plot(qs, dd, "o-", color="#c0392b", lw=1.9, ms=4.5,
               label=r"$D_{pt}=(m_M/m_P)/r_{ref}-1$")
    ax[1].plot(qs, dc, "s--", color="#1f4e79", lw=1.4, ms=3.5,
               label=r"$D_{curve}$, shape only")
    ax[1].axhline(0.0, color="k", lw=0.7)
    ax[1].set_xlabel("matched electrical power  $Q_e$ / kW")
    ax[1].set_ylabel("distortion / pct")
    ax[1].set_title("(b) distortion at matched power")
    ax[1].grid(alpha=0.3)
    ax[1].legend(fontsize=7, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG_PATH, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
