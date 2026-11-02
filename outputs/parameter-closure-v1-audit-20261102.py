#!/usr/bin/env python3
"""Audit the proposed Reynolds threshold against the archived Zhao scalar model.

This checks a mathematical implication under declared model inputs. It does not
establish a physical bound for valve/bend losses or a prior Reynolds domain.
"""

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
source = HERE / "source-free-v5-upload-20261102.py"
spec = importlib.util.spec_from_file_location("source_free_v5", source)
model_code = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_code)

model = model_code.Model(0.5, 0.5, 2.0, model_code.QR_ZHAO, 0.25)
x_target = 1.03
K_plus = x_target**3 / model.M_s(x_target)
f_plus = model.f_s(x_target)
print(f"K_plus={K_plus:.12f}, f_plus={f_plus:.12f}")

for w in (0.0, 0.1, 0.2, 0.3):
    delta_allowed = (K_plus - w * f_plus) / (1.0 - w) - 1.0
    reynolds_min = (1.0 + delta_allowed) ** (-5.0)
    print(f"w={w:.1f}, allowed_delta={delta_allowed:.9f}, "
          f"Re_min_if_m=0.2={reynolds_min:.9f}")

assert abs(K_plus**-5 - 0.6417779446781373) < 1e-12
assert abs(1.03**-5 - 0.8626087843841639) < 1e-12

assumed_re_ratio = 0.65
delta_envelope = assumed_re_ratio**-0.2 - 1.0
G_at_target = (1 - 0.2) * (1 + delta_envelope) + 0.2 * f_plus
print(f"Re_R={assumed_re_ratio:.2f} gives delta_envelope={delta_envelope:.9f}; "
      f"at w=0.2, G(1.03)={G_at_target:.9f}>K_plus={K_plus:.9f}")
print(f"Zhao scalar result at that delta,w: "
      f"D={100*model_code.Model(0.5,0.5,2.0,model_code.QR_ZHAO,0.25,delta=delta_envelope).D_s(0.2):.6f}%")
assert G_at_target > K_plus

print(f"Xu standard-model c=length_ratio/diameter_ratio=0.5/0.616="
      f"{0.5/0.616:.9f}; uploaded closure uses c=0.5")
