#!/usr/bin/env python3
"""Audit the v10 identifiability claims against the archived v5 scalar model.

This is a model and arithmetic audit, not evidence of an experimental input box.
Run: python outputs/identifiability-v10-independent-audit-20261103.py
"""

import importlib.util
import math
from pathlib import Path

source = Path(__file__).with_name("source-free-v5-upload-20261102.py")
spec = importlib.util.spec_from_file_location("source_free_v5", source)
v5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v5)

m = v5.Model(0.5, 0.5, 2.0, v5.QR_ZHAO, 0.25)
b0 = 0.291472160
x0 = m.solve_s(b0)
K = lambda x: x ** 3 / m.M_s(x)
f = lambda x: m.f_s(x)
k0, f0 = K(x0), f(x0)
a0 = k0 - b0 * f0

assert abs(k0 - 1.088839060851) < 1e-10
assert abs(x0 - 1.028768352858) < 1e-10
print(f"single paired point: x={x0:.12f}, D={(x0-1)*100:.9f}%, K={k0:.12f}")
print(f"one equation: A+B*f(x)={k0:.12f}; reference A={a0:.12f}, B={b0:.9f}")

for b in (0.0, b0 * 0.9, b0, b0 * 1.1, 0.6):
    a = k0 - b * f0
    assert abs(a + b * f0 - k0) < 1e-12
    print(f"calibration line: B={b:.9f}, A={a:.9f}, same observed D={(x0-1)*100:.6f}%")

for c in (0.6, 1.0, 1.5):
    w = b0 / c
    delta = a0 / (1 - w) - 1
    print(f"fixed A,B, varying unmeasured c={c:.1f}: w={w:.6f}, delta={delta*100:+.4f}%")

lower, upper = 0.97, 1.03
alow = K(lower) - b0 * f(lower)
aup = K(upper) - b0 * f(upper)
print(f"two-sided |D|<=3% model band at B={b0:.9f}: {alow:.12f} <= A <= {aup:.12f}")
print(f"reference A={a0:.12f}; lower margin={a0-alow:.9f}; upper margin={aup-a0:.9f}")
print(f"reported point lies {(upper-x0)*100:.6f} percentage points below +3%")

sigma_d = 0.005  # assumed absolute standard deviation of D, not observed uncertainty
for q in (1.25, 2.0, 5.0, 10.0):
    # Reproduces v10's *hypothetical* f spread, without asserting physical validity.
    spread = f0 * (1 - q ** (-1 / 12))
    sigma_b_abs = math.sqrt(2) * 3 * sigma_d / spread
    print(f"v10 hypothetical Q ratio={q:.2f}: |df|={spread:.6f}, "
          f"sigma_B_absolute={sigma_b_abs:.6f}, sigma_B/B={100*sigma_b_abs/b0:.1f}%")

# In v5, f is a P/M Reynolds-number *ratio*. Common scaling of both flow rates
# leaves Re_P/Re_M and x invariant when viscosity ratios and power ratio are fixed.
for q in (1.0, 5.0, 10.0):
    flow_multiplier = q ** (1 / 3)
    re_ratio = (1.0 * flow_multiplier) / (0.3461 * flow_multiplier)
    assert abs(re_ratio - 1 / 0.3461) < 1e-12
    print(f"paired common Q multiplier={q:.1f}: relative flow multiplier={flow_multiplier:.6f}, "
          f"Re_P/Re_M={re_ratio:.9f} (unchanged)")

# A direct local-loss measurement supplies an independent observation; therefore
# the lack of identification is specific to fitting from one scalar FoM alone.
assert (a0 + b0 * f0) == k0 or abs(a0 + b0 * f0 - k0) < 1e-12
print("audit complete: all numbers above are conditional on the archived v5 model")
