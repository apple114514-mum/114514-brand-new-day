#!/usr/bin/env python3
"""Yue 2017 Fig.4(c): conditional same-paper power trend check.

The four lower-power flows are analyst readings of a published plot, not
reported measurement precision.  +/-0.03 kg/s is an explicit readout
stress scenario, NOT a measurement uncertainty.  The 17.9 kW flow 1.12
kg/s is stated in Yue Sec.5.2, PDF p.6.  Powers are stated in Sec.4.1
and labeled on Fig.4(b,c), PDF p.4-5.
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_P = 17.9
BASE_M = 1.12
FIGURE_POINTS = [
    (4.3, 0.62, 'Fig.4(c), black; graph read'),
    (7.6, 0.82, 'Fig.4(c), red; graph read'),
    (11.2, 0.94, 'Fig.4(c), green; graph read'),
    (15.3, 1.06, 'Fig.4(c), blue; graph read'),
    (17.9, 1.12, 'Sec.5.2 direct stated value; Fig.4(c) olive curve'),
]
READ_STRESS = 0.03

rows = []
for p, m, locator in FIGURE_POINTS:
    predicted = BASE_M * (p / BASE_P) ** (1 / 3)
    ratio = (p / BASE_P) / (m / BASE_M) ** 3
    row = {
        'power_kW': p,
        'flow_kg_s': m,
        'flow_source': locator,
        'flow_method': 'heater energy balance (Yue Sec.5.1)',
        'oil_condition': 'held same across series; absolute inlet temperature not given here',
        'valve_position': 'not reported per point',
        'independent_net_heat_kW': 'not reported',
        'pred_fixed_K_eta_C_H_kg_s': round(predicted, 6),
        'flow_minus_pred_kg_s': round(m - predicted, 6),
        'P_over_m3_ratio_to_17p9': round(ratio, 6),
        'eta_ratio_if_K_C_H_fixed': round(1 / ratio, 6),
        'read_stress_kg_s': '' if p == BASE_P else READ_STRESS,
        'status': 'graph read, conditional trend only' if p != BASE_P else 'text stated calibration anchor',
    }
    rows.append(row)

out = HERE / 'kylin-same-paper-trend-20261103.csv'
with out.open('w', encoding='utf-8', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=rows[0], lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)

for r in rows:
    print(f"{r['power_kW']:4.1f} kW  observed~{r['flow_kg_s']:.2f}  "
          f"pred={r['pred_fixed_K_eta_C_H_kg_s']:.6f} kg/s  "
          f"P/m3 ratio={r['P_over_m3_ratio_to_17p9']:.3f}")
low_pred = rows[0]['pred_fixed_K_eta_C_H_kg_s']
assert low_pred > FIGURE_POINTS[0][1] + READ_STRESS
print(f"4.3 kW residual beyond +/-{READ_STRESS:.2f} graph-read stress = "
      f"{low_pred - FIGURE_POINTS[0][1] - READ_STRESS:.6f} kg/s")
alternate_base = 1.10  # Fig.4(c) plateau visually near 1.10; stress, not source text
alternate_low = alternate_base * (4.3 / BASE_P) ** (1 / 3)
print(f"using graph-only 17.9 kW anchor~{alternate_base:.2f}, low-power residual "
      f"beyond +/-{READ_STRESS:.2f} = "
      f"{alternate_low - FIGURE_POINTS[0][1] - READ_STRESS:.6f} kg/s")
print(f"Wrote {out.name}; graph-read stress is not instrument uncertainty")
