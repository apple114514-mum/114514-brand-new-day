"""Independent thermal FoM audit using the frozen v1/v2 conditional model.

This imports the independently checked Table-2 forward wrapper, not the
unprovided WorkBuddy core_v2.py.  The heater-exit bulk temperature is computed
from the FIRST heated segment's energy march, with the same cp convention.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

import numpy as np

import forward_v1_table2_recheck_20261109 as W


HERE = Path(__file__).resolve().parent
F = W.F
Q_GRID = (3000., 3500., 4000., 4300., 4500., 5000., 5500., 6000.)


def heater_out(loop, m, q, kw):
    """Bulk outlet of the first heated segment, not a wall or peak temperature."""
    s = loop["segs"][0]
    length = s["L"] * kw.get("lhs_scale", 1.)
    t_in = F.T_IN_REF + kw["dtin"]
    u = s["u"] * kw["u_fac"]
    cp = F.cp_of(t_in, kw["fcp"])
    a = u * length / (m * cp)
    q_per_length = q * s["qfrac"] / length
    t_eq = F.T_AMB + q_per_length / u
    return t_eq + (t_in - t_eq) * math.exp(-a)


def evaluate(x, q):
    base = W.result(np.asarray(x), q)
    kw_p, kw_m = F.kw_from_vec(W.full_vec(np.asarray(x)))
    t_in_p = F.T_IN_REF + kw_p["dtin"]
    t_in_m = F.T_IN_REF + kw_m["dtin"]
    t_out_p = heater_out(F.P, base["rp"]["m"], q, kw_p)
    t_out_m = heater_out(F.M, base["rm"]["m"], q, kw_m)
    dt_p, dt_m = t_out_p - t_in_p, t_out_m - t_in_m
    d_temp = 100. * (F.A_R * dt_m / dt_p - 1.)
    # This is an exact algebraic identity after defining the effective net
    # heater duties at the same bulk cp used by the one-segment energy march.
    qnet_p = base["rp"]["m"] * F.cp_of(t_in_p, kw_p["fcp"]) * dt_p
    qnet_m = base["rm"]["m"] * F.cp_of(t_in_m, kw_m["fcp"]) * dt_m
    thermal_factor = (qnet_m / qnet_p) * (F.cp_of(t_in_p, kw_p["fcp"]) /
                                           F.cp_of(t_in_m, kw_m["fcp"]))
    assert abs((1. + d_temp / 100.) * (1. + base["d_pt"] / 100.) - thermal_factor) < 1e-11
    return dict(Q_W=q, m_P=base["rp"]["m"], m_M=base["rm"]["m"],
                T_HS_out_P_K=t_out_p, T_HS_out_M_K=t_out_m,
                deltaT_HS_P_K=dt_p, deltaT_HS_M_K=dt_m,
                D_massflux_pct=base["d_pt"], D_temperature_pct=d_temp,
                Qnet_HS_P_W=qnet_p, Qnet_HS_M_W=qnet_m,
                thermal_factor=thermal_factor)


def main():
    from SALib.sample import sobol as sobol_sample
    from SALib.analyze import sobol as sobol_analyze

    rows = [evaluate(W.X0, q) for q in Q_GRID]
    with (HERE / "temperature_fom_v2_results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    searched = {}
    for q in (3000., 6000.):
        vals = []
        for bits in itertools.product((0, 1), repeat=len(W.NAMES)):
            x = [W.BOUNDS[i][bit] for i, bit in enumerate(bits)]
            vals.append(evaluate(x, q)["D_temperature_pct"])
        searched[str(int(q))] = dict(corner_min_pct=min(vals), corner_max_pct=max(vals))

    problem = dict(num_vars=len(W.NAMES), names=W.NAMES, bounds=W.BOUNDS)
    xs = sobol_sample.sample(problem, 512, calc_second_order=False, seed=W.SEED)
    ys = np.array([evaluate(x, 6000.)["D_temperature_pct"] for x in xs])
    si = sobol_analyze.analyze(problem, ys, calc_second_order=False,
                               num_resamples=300, seed=W.SEED, print_to_console=False)
    sobol = {n: dict(ST=float(si["ST"][i]), ST_conf=float(si["ST_conf"][i]),
                     S1=float(si["S1"][i]), S1_conf=float(si["S1_conf"][i]))
             for i, n in enumerate(W.NAMES)}
    report = dict(nominal=rows, searched_corners=searched, sobol_6kw=sobol,
                  sobol_meta=dict(N=512, calls=len(xs), seed=W.SEED,
                                  distribution="independent uniform design box"),
                  status="conditional model; searched corners are not certified global bounds",
                  definition="D_temperature=A_M/A_P * deltaT_HS_M/deltaT_HS_P - 1")
    (HERE / "temperature_fom_v2_analysis.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for row in rows:
        print(f'{row["Q_W"]/1000:.1f} kW: dT_P={row["deltaT_HS_P_K"]:.3f} K, '
              f'dT_M={row["deltaT_HS_M_K"]:.3f} K, D_T={row["D_temperature_pct"]:+.4f}%, '
              f'D_j={row["D_massflux_pct"]:+.4f}%')
    print("searched temperature corners:", searched)
    print("Sobol ST 6 kW:", sorted(((n, d["ST"], d["ST_conf"]) for n, d in sobol.items()),
                                  key=lambda v: -v[1]))


if __name__ == "__main__":
    main()
