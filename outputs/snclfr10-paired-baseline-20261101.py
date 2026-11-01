#!/usr/bin/env python3
"""Recalculate the paired CFD ratios in Zhao et al. (2020), Tables 3--5.

These are published *numerical simulation* values, not measurements or
uncertainty bounds. Run with: python outputs/snclfr10-paired-baseline-20261101.py
"""

import csv
import math
import sys


LENGTH_RATIO = 2.0  # prototype / scaled facility, Zhao Table 3
CFD = {
    "system_mass_flow_kg_s": (540.0, 92.79, LENGTH_RATIO ** 2.5),
    "core_temperature_rise_K": (130.0, 136.70, 1.0),
    "core_pressure_drop_Pa": (3105.8, 1515.02, LENGTH_RATIO),
}


def cp_integral(t_in, t_out):
    """Integral of Zhao Table 4 c_p(T), assuming J/(kg K), T in K."""
    return (
        159.0 * (t_out - t_in)
        - 0.0272 * (t_out**2 - t_in**2) / 2.0
        + 7.12e-6 * (t_out**3 - t_in**3) / 3.0
    )


def rows():
    for name, (prototype, facility, ideal) in CFD.items():
        actual = prototype / facility
        signed = 100.0 * (actual / ideal - 1.0)
        yield {
            "fom": name,
            "prototype_CFD": prototype,
            "facility_CFD": facility,
            "ideal_prototype_over_facility": ideal,
            "actual_prototype_over_facility": actual,
            "signed_deviation_percent": signed,
            "absolute_deviation_percent": abs(signed),
            "source": "Zhao et al. 2020 Table 5; ideal ratios from Table 1 and Eq. 10/14",
        }


def main():
    fieldnames = list(next(rows()))
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows())
    for label, flow, t_in, t_out, nominal_mw in (
        ("prototype", 540.0, 533.15, 663.16, 10.0),
        ("facility", 92.79, 533.15, 669.85, 1.77),
    ):
        implied_mw = flow * cp_integral(t_in, t_out) / 1e6
        print(
            f"{label}: single-stream enthalpy estimate={implied_mw:.6f} MW; "
            f"Table 3 nominal={nominal_mw:.6f} MW; "
            f"difference={100 * (implied_mw / nominal_mw - 1):.3f}%",
            file=sys.stderr,
        )
    assert math.isclose(next(rows())["signed_deviation_percent"], 2.876835284172774)


if __name__ == "__main__":
    main()
