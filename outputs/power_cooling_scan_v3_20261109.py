"""Audit the v3 conditional model across power and every input-box corner.

The extrema remain searched corner extrema, not certified continuous bounds.
Oil temperature 433.15 K is an *illustrative isothermal lower-bound* sizing
assumption; finite oil warming can only raise the required UA.
"""

import csv
import itertools
import json
import math
from pathlib import Path

import core_v2 as C


ROOT = Path(__file__).resolve().parent
OIL_K = 433.15
OIL_FLOW_KG_S = 0.50  # an illustrative secondary-side scenario, not an input datum
OIL_CP_J_KG_K = 2300.0
POWER = [3000. + 250. * i for i in range(13)]
CORNERS = [([C.BOUNDS[i][bit] for i, bit in enumerate(bits)], bits)
           for bits in itertools.product((0, 1), repeat=len(C.NAMES))]


def required_ua(root):
    hot = root["t_ci"] - OIL_K
    cold = root["t_co"] - OIL_K
    if hot <= 0. or cold <= 0.:
        return math.inf
    lmtd = (hot - cold) / math.log(hot / cold) if abs(hot-cold) > 1e-10 else hot
    return root["qc"] / lmtd


def required_ua_finite_oil(root):
    """Illustrative counterflow duty with finite warming of 0.50 kg/s oil."""
    t_oil_out = OIL_K + root["qc"] / (OIL_FLOW_KG_S * OIL_CP_J_KG_K)
    dt_hot = root["t_ci"] - t_oil_out
    dt_cold = root["t_co"] - OIL_K
    if min(dt_hot, dt_cold) <= 0.0:
        return math.inf
    lmtd = ((dt_hot - dt_cold) / math.log(dt_hot / dt_cold)
            if abs(dt_hot - dt_cold) > 1e-10 else dt_hot)
    return root["qc"] / lmtd


def record(x, power):
    r = C.fom(x, power)
    if r is None:
        return None
    return dict(d_j=r["d_j"], d_t=r["d_t"],
                ua_p=required_ua(r["rp"]), ua_m=required_ua(r["rm"]),
                qc_p=r["rp"]["qc"], qc_m=r["rm"]["qc"],
                m_p=r["rp"]["m"], m_m=r["rm"]["m"],
                re_p=r["rp"]["re"], re_m=r["rm"]["re"])


def main():
    rows = []
    nbad = 0
    for power in POWER:
        nominal = record(C.X0, power)
        vals = [record(x, power) for x, _ in CORNERS]
        nbad += sum(v is None for v in vals)
        vals = [v for v in vals if v is not None]
        if not vals:
            raise RuntimeError(f"no roots at {power}")
        row = {"Q_kW": power/1000, "nominal_D_j_pct": nominal["d_j"],
               "corner_D_j_min_pct": min(v["d_j"] for v in vals),
               "corner_D_j_max_pct": max(v["d_j"] for v in vals),
               "nominal_D_T_pct": nominal["d_t"],
               "corner_D_T_min_pct": min(v["d_t"] for v in vals),
               "corner_D_T_max_pct": max(v["d_t"] for v in vals),
               "nominal_Qc_P_W": nominal["qc_p"], "nominal_Qc_M_W": nominal["qc_m"],
               "nominal_UAreq_P_W_K": nominal["ua_p"],
               "nominal_UAreq_M_W_K": nominal["ua_m"],
               "corner_UAreq_P_min_W_K": min(v["ua_p"] for v in vals),
               "corner_UAreq_P_max_W_K": max(v["ua_p"] for v in vals),
               "corner_UAreq_M_min_W_K": min(v["ua_m"] for v in vals),
               "corner_UAreq_M_max_W_K": max(v["ua_m"] for v in vals),
               "corner_M_pass_if_UA45_frac": sum(v["ua_m"] <= 45. for v in vals)/len(vals),
               "corner_M_pass_if_UA70_frac": sum(v["ua_m"] <= 70. for v in vals)/len(vals),
               "corner_Re_P_min": min(v["re_p"] for v in vals),
               "corner_Re_P_max": max(v["re_p"] for v in vals),
               "corner_Re_M_min": min(v["re_m"] for v in vals),
               "corner_Re_M_max": max(v["re_m"] for v in vals),
               "roots": len(vals)}
        rows.append(row)
        print(f'{power/1000:.2f} kW: Dj {row["corner_D_j_min_pct"]:+.4f}..'
              f'{row["corner_D_j_max_pct"]:+.4f}; DT '
              f'{row["corner_D_T_min_pct"]:+.4f}..{row["corner_D_T_max_pct"]:+.4f}; '
              f'UA_M {row["corner_UAreq_M_min_W_K"]:.1f}..'
              f'{row["corner_UAreq_M_max_W_K"]:.1f}', flush=True)

    with (ROOT/'power_cooling_scan_v3_20261109.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader();w.writerows(rows)
    worst_flow=min(rows,key=lambda r:r['corner_D_j_min_pct'])
    worst_temp=max(rows,key=lambda r:r['corner_D_T_max_pct'])
    result={"power_grid_kW":[r['Q_kW'] for r in rows],
            "corners_per_power":len(CORNERS),"missing_roots":nbad,
            "most_negative_searched_flow":worst_flow,
            "largest_searched_temperature":worst_temp,
            "warning":"power grid and box corners are searches, not global certification; UA uses isothermal oil lower bound"}
    (ROOT/'power_cooling_scan_v3_20261109.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('most negative searched flow:',worst_flow['Q_kW'],worst_flow['corner_D_j_min_pct'])
    print('largest searched temperature:',worst_temp['Q_kW'],worst_temp['corner_D_T_max_pct'])
    print('missing roots:',nbad)

    # These are scenario checks, deliberately outside the main ten-axis box.
    for power in (3000., 6000.):
        p_ua, m_ua = [], []
        for x, _ in CORNERS:
            r = C.fom(x, power)
            p_ua.append(required_ua_finite_oil(r["rp"]))
            m_ua.append(required_ua_finite_oil(r["rm"]))
        print(f'finite oil scenario at {power/1000:.1f} kW: '
              f'P UA {min(p_ua):.4f}..{max(p_ua):.4f}; '
              f'M UA {min(m_ua):.4f}..{max(m_ua):.4f} W/K')


if __name__=='__main__':
    main()
