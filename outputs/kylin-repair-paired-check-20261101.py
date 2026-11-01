#!/usr/bin/env python3
"""Pair-consistent check of the uploaded KYLIN-II repair script.

Uses the self-contained conditional model already delivered as
``outputs/kylin-audit-20261101.py``. This script does not verify the Xu/Li
source papers or the assumed heat-loss coefficient. It separates comparisons
to a re-solved prototype from comparisons to a fixed 1.2 kg/s calibration
point and labels the two bore-tolerance denominators.

Run: python outputs/kylin-repair-paired-check-20261101.py > results.csv
"""

import csv
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


SOURCE = Path(__file__).with_name("kylin-audit-20261101.py")
spec = spec_from_file_location("kylin_conditional_model", SOURCE)
model = module_from_spec(spec)
spec.loader.exec_module(model)


def row(writer, case, effective_height, k_sum, m_p, m_m, dt_p, dt_m,
        ideal_mass_ratio, note, fixed_ref=False):
    writer.writerow((case, f"{effective_height:.4f}", f"{k_sum:.6f}",
                     f"{m_p:.9f}", f"{m_m:.9f}",
                     f"{100*(m_m/(m_p*ideal_mass_ratio)-1):.6f}",
                     f"{100*(m_m/1.2-1):.6f}" if fixed_ref else "",
                     f"{100*(dt_m/dt_p-1):.6f}", note))


def main():
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("case", "effective_height_m", "sum_k", "prototype_m_kg_s",
                     "facility_m_kg_s", "paired_mass_deviation_percent",
                     "facility_vs_fixed_1p2_percent", "paired_deltaT_deviation_percent",
                     "note"))

    for h in (5.0, 3.35):
        p = model.prototype(h)
        mp = model.root(p, h)
        _, local, friction, dtp, *_ = model.terms(mp, p, h)
        print(f"height={h:.2f} m: fitted sum(k)={6*p['kmult']:.6f}, "
              f"actual nominal friction share={friction/(local+friction):.6f}", file=sys.stderr)
        ps = model.standard(p)
        ms = model.root(ps, h)
        dts = model.terms(ms, ps, h)[3]
        row(writer, "standard", h, 6*p["kmult"], mp, ms,
            dtp, dts, model.M_R, "Facility flow is the actual model output")

        if h == 3.35:
            matched = model.standard(p, us_ratio=model.M_R)
            mm = model.root(matched, h)
            row(writer, "US_scaled_with_power", h, 6*p["kmult"], mp, mm,
                dtp, model.terms(mm, matched, h)[3], model.M_R,
                "Counterfactual: heat-loss coefficient scales with Q and UA")

            pnok = dict(p, kmult=0.0)
            mnok = model.root(pnok, h)
            pmnok = model.standard(pnok)
            mmnok = model.root(pmnok, h)
            row(writer, "no_local_losses_both_sides", h, 0.0, mnok, mmnok,
                model.terms(mnok, pnok, h)[3], model.terms(mmnok, pmnok, h)[3], model.M_R,
                "Changed both designs; not a physical estimate of the removed loss")

            for k_sum in (3.0, 6.0, 11.5934097737, 36.0):
                pp = dict(p, kmult=k_sum/6)
                mp_k = model.root(pp, h)
                pm = dict(pp, lR=0.5, US=model.US_P*0.5)
                mm_k = model.root(pm, h)
                row(writer, "height_only_pair_consistent", h, k_sum,
                    mp_k, mm_k, model.terms(mp_k, pp, h)[3],
                    model.terms(mm_k, pm, h)[3], 1.0,
                    "Same k on both designs; US halved as in original reduced-height scenario", True)

if __name__ == "__main__":
    main()
