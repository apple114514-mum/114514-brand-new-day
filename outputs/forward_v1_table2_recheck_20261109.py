"""Independent v1 audit: use Yue Table 2 K(Re) on P, preserve the declared M.

Run beside forward_v1_original_20261109.py. Outputs are written to the
same directory. This is a conditional design calculation, not validation of
an as-built loop or a certified global bound.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

import forward_v1_original_20261109 as F


HERE = Path(__file__).resolve().parent
SEED = 20261109
Q_GRID = (3000.0, 3500.0, 4000.0, 4300.0, 4500.0, 5000.0, 5500.0, 6000.0)

# Yue 2017, Table 2, printed page 4: theoretical, not measured. All K terms
# use the main-pipe dynamic head. Interpolate against the published tube Re,
# not mass flow, so shared viscosity changes act on both P and M.
TABLE2 = (
    (5560.0, 19.1, 2.9, 2.5),
    (11100.0, 18.9, 2.8, 2.5),
    (16700.0, 18.5, 2.8, 2.5),
    (22300.0, 18.1, 2.7, 2.5),
    (27800.0, 17.7, 2.6, 2.5),
)

# A model-form multiplier has no sampled physical probability law. Run it as
# a separate scenario instead of burying it in one uniform Sobol box.
BRANCH_KEYS = {"k_P_fac", "k_bend_fac", "k_orif_fac"}
PRIMARY = [r for r in F.INPUTS if r[0] not in BRANCH_KEYS]
NAMES = [r[0] for r in PRIMARY]
BOUNDS = [[r[3], r[4]] for r in PRIMARY]
IDX = {name: i for i, name in enumerate(NAMES)}
X0 = np.array([r[2] for r in PRIMARY], dtype=float)

_original_march = F.march


def table_k(re: float) -> tuple[float, float, float]:
    """Piecewise-linear K(Re); endpoint extension is only for root bracketing."""
    if re <= TABLE2[0][0]:
        return TABLE2[0][1:]
    if re >= TABLE2[-1][0]:
        return TABLE2[-1][1:]
    for a, b in zip(TABLE2[:-1], TABLE2[1:]):
        if a[0] <= re <= b[0]:
            t = (re - a[0]) / (b[0] - a[0])
            return tuple(a[i] + t * (b[i] - a[i]) for i in (1, 2, 3))
    raise AssertionError("unreachable")


def table_march(loop, mass, *args, **kwargs):
    if loop["lumped"]:
        # The fixed-mass thermal profile and tube Re do not depend on K.
        # The first pass retrieves Re; the second inserts source K(Re).
        preliminary = _original_march(loop, mass, *args, **kwargs)
        if preliminary is None:
            return None
        kp, khs, kev = table_k(preliminary["re"])
        loop["k_table"] = dict(pipe=kp, hs=khs, valve=kev,
                               total=kp + khs + kev, m_ref=1.25)
    return _original_march(loop, mass, *args, **kwargs)


F.march = table_march


def full_vec(x: np.ndarray) -> np.ndarray:
    d = dict(zip(NAMES, x))
    d.update(k_P_fac=1.0, k_bend_fac=1.0, k_orif_fac=1.0)
    return np.array([d[r[0]] for r in F.INPUTS], dtype=float)


def result(x: np.ndarray, power: float = 6000.0):
    kwp, kwm = F.kw_from_vec(full_vec(x))
    out = F.fom(F.P, F.M, power, kwp, kwm, k_p_fac=1.0)
    if out is None:
        raise ValueError("no paired steady root")
    if not (TABLE2[0][0] <= out["rp"]["re"] <= TABLE2[-1][0]):
        raise ValueError("P tube Re left the published Table 2 range")
    return out


def dpt(x: np.ndarray, power: float = 6000.0) -> float:
    return result(x, power)["d_pt"]


def main() -> None:
    from SALib.analyze import morris as morris_analyze
    from SALib.analyze import sobol as sobol_analyze
    from SALib.sample import morris as morris_sample
    from SALib.sample import sobol as sobol_sample
    from scipy.optimize import differential_evolution

    report = {}
    nominal = [result(X0, q) for q in Q_GRID]
    with (HERE / "results_v1_table2_recheck.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(("Q_W", "m_P_kg_s", "m_M_kg_s", "K_P_Table2", "K_M",
                    "D_massflux_pct", "D_velocity_pct", "D_curve_pct", "Re_P", "Re_M",
                    "Tmax_P_K", "Tmax_M_K"))
        base = nominal[-1]
        for row in nominal:
            kp = sum(table_k(row["rp"]["re"]))
            dcurve = 100.0 * ((row["rm"]["m"] / base["rm"]["m"]) /
                               (row["rp"]["m"] / base["rp"]["m"]) - 1.0)
            dvel = 100.0 * (row["rm"]["v_main"] / row["rp"]["v_main"] - 1.0)
            w.writerow((row["qe"], row["rp"]["m"], row["rm"]["m"], kp,
                        sum(row["rm"]["kbrk"].values()), row["d_pt"], dvel, dcurve,
                        row["rp"]["re"], row["rm"]["re"],
                        row["rp"]["tmax"], row["rm"]["tmax"]))
    report["nominal"] = [dict(Q_W=r["qe"], m_P=r["rp"]["m"], m_M=r["rm"]["m"],
                              K_P=sum(table_k(r["rp"]["re"])),
                              D_massflux_pct=r["d_pt"],
                              D_velocity_pct=100.0 * (r["rm"]["v_main"] / r["rp"]["v_main"] - 1.0))
                         for r in nominal]

    # The original frozen 22.8 model is retained as an explicit comparison.
    F.march = _original_march
    F.P["k_table"] = dict(pipe=17.7, hs=2.6, valve=2.5, total=22.8, m_ref=1.25)
    frozen = {str(int(q)): F.fom(F.P, F.M, q, *F.base_kw())["d_pt"] for q in Q_GRID}
    F.march = table_march
    report["frozen22_8_D_pt_pct"] = frozen

    problem = dict(num_vars=len(NAMES), names=NAMES, bounds=BOUNDS)
    Xm = morris_sample.sample(problem, N=60, num_levels=4, seed=SEED)
    Ym = np.array([dpt(row) for row in Xm])
    mi = morris_analyze.analyze(problem, Xm, Ym, num_levels=4, num_resamples=200,
                                seed=SEED, print_to_console=False)
    report["morris"] = {n: dict(mu_star=float(mi["mu_star"][i]),
                                 sigma=float(mi["sigma"][i]),
                                 mu_star_conf=float(mi["mu_star_conf"][i]))
                        for i, n in enumerate(NAMES)}

    Xs = sobol_sample.sample(problem, 512, calc_second_order=False, seed=SEED)
    Ys = np.array([dpt(row) for row in Xs])
    si = sobol_analyze.analyze(problem, Ys, calc_second_order=False,
                               num_resamples=300, seed=SEED, print_to_console=False)
    report["sobol"] = {n: dict(S1=float(si["S1"][i]), S1_conf=float(si["S1_conf"][i]),
                                ST=float(si["ST"][i]), ST_conf=float(si["ST_conf"][i]))
                       for i, n in enumerate(NAMES)}
    report["sobol_meta"] = dict(base_N=512, model_runs=len(Xs), seed=SEED,
                                distribution="independent uniform DESIGN scenarios")

    # Exhaustive corners are a search only unless full-domain monotonicity is proven.
    corners = []
    for mask in range(1 << len(NAMES)):
        x = np.array([BOUNDS[i][(mask >> i) & 1] for i in range(len(NAMES))])
        corners.append((dpt(x), mask))
    cmin, cmax = min(corners), max(corners)
    opt = []
    for sign in (1.0, -1.0):
        r = differential_evolution(lambda x: sign * dpt(np.asarray(x)), BOUNDS,
                                   seed=SEED, popsize=8, maxiter=40,
                                   polish=True, tol=1e-8)
        opt.append(dict(D_pt_pct=float(sign * r.fun), x=list(map(float, r.x)),
                        nfev=int(r.nfev), success=bool(r.success)))
    report["search"] = dict(corner_min_pct=cmin[0], corner_max_pct=cmax[0],
                             corner_min_mask=cmin[1], corner_max_mask=cmax[1],
                             global_heuristic=opt,
                             status="searched extrema only; no interval/analytic certificate")
    report["input_domain"] = [dict(name=r[0], nominal=r[2], lower=r[3], upper=r[4],
                                    unit=r[5], identity=r[6], basis=r[7]) for r in PRIMARY]
    report["model_form_branches"] = dict(P="Yue Table 2 piecewise-linear in tube Re main; frozen 22.8 comparator",
                                          bend="Al-Tameemi relation nominal; transfer factor not random",
                                          orifice="NEA 15.3.3 #3 nominal; alternate formula separate")
    report["design_choice"] = "Keep M 16 m and 3 m rise as preregistered candidate; changed geometry is discussion only"

    (HERE / "analysis_v1_table2_recheck.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["v1 Table-2 independent recheck", "",
             "P main closure: Yue Table 2 K(Re_tube), piecewise-linear within 5560-27800",
             "M design: 16 m / 16 mm / 10 mm hole / 3 m rise; no post hoc redesign", "",
             "Nominal comparison:",
             "Q kW   mP kg/s   Kp   mM kg/s   D_massflux %   D_velocity %   D_frozen %"]
    for row in report["nominal"]:
        lines.append(f'{row["Q_W"]/1000:4.1f}  {row["m_P"]:8.5f}  {row["K_P"]:5.3f}  '
                     f'{row["m_M"]:8.5f}  {row["D_massflux_pct"]:+9.4f}  '
                     f'{row["D_velocity_pct"]:+9.4f}  '
                     f'{frozen[str(int(row["Q_W"]))]:+9.4f}')
    lines += ["", "Sobol ST (95% bootstrap half-width), descending:"]
    for n in sorted(NAMES, key=lambda n: report["sobol"][n]["ST"], reverse=True):
        d = report["sobol"][n]
        lines.append(f'{n:13s} {d["ST"]:8.4f} +/- {d["ST_conf"]:8.4f}')
    lines += ["", "Morris mu_star (95% bootstrap half-width), descending:"]
    for n in sorted(NAMES, key=lambda n: report["morris"][n]["mu_star"], reverse=True):
        d = report["morris"][n]
        lines.append(f'{n:13s} {d["mu_star"]:8.4f} +/- {d["mu_star_conf"]:8.4f}')
    lines += ["", f'Corner search: [{cmin[0]:+.4f}, {cmax[0]:+.4f}] %',
              f'Heuristic optimizer: [{opt[0]["D_pt_pct"]:+.4f}, {opt[1]["D_pt_pct"]:+.4f}] %',
              "These are observed/search extrema, NOT certified global bounds."]
    (HERE / "forward_v1_table2_recheck_log.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
