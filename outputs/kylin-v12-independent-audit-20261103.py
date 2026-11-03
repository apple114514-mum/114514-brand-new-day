#!/usr/bin/env python3
"""Independent arithmetic checks for Workbuddy KYLIN v12.

Source coordinates: Li 2015 PDF p.4 Fig.4 and p.2 Sec.2; Yue 2017
PDF p.4 Table 2 and p.6 Sec.5.2.  Source values read from the PDFs.
This script checks arithmetic only; no uncertain input is treated as data.
"""

import math


def out(label, value):
    print(f"{label}: {value}")


# Li Fig.4(c,d): m is given in Sec.3.2.1 to one decimal; P is graph-read.
p5, m5, p20, m20 = 5.0, 0.5, 20.0, 1.1
r = (p5 / m5**3) / (p20 / m20**3)
eta_ratio = 1.0 / r
assert math.isclose(r, 2.662, rel_tol=1e-12)
out("Li Fig.4 graph-read (P/m^3)_5/(P/m^3)_20", f"{r:.6f}")
out("eta_5/eta_20 if K,H,properties fixed", f"{eta_ratio:.6f}")
out("eta_5 if eta_20=0.8 under those assumptions", f"{eta_ratio*0.8:.6f}")
for dm in (0.0, 0.05):
    low = 0.25 * ((m20-dm) / (m5+dm))**3
    high = 0.25 * ((m20+dm) / (m5-dm))**3
    out(f"illustrative m±{dm:.2f} kg/s, fixed P ratio, proxy range", f"[{low:.3f},{high:.3f}]")

# Two conditional, positive-exponent models.  Use v12's actual roots.
mu05, mu25, observed = 1.095992, 1.090340, 1.12
gap = mu05 - mu25
assert gap > 0
out("conditional flow gap", f"{gap:.6f} kg/s")
out("half-gap / nominal flow", f"{gap/2:.6f} kg/s; {100*gap/2/1.1:.3f}%")
out("two 95% (±1.96 sigma) bands nonoverlap if", f"sigma < {gap/(2*1.96):.6f} kg/s")
out("95% correct nearest-mean classification, ideal normal error, if", f"sigma < {gap/(2*1.644854):.6f} kg/s")
out("observed - model .05 / .25", f"{observed-mu05:.6f} / {observed-mu25:.6f} kg/s")

# Exact factors under a single-parameter intervention and fixed closure.
fixed = 1.097318
out("K-only factor to match 1.12", f"{(fixed/observed)**3:.6f}")
out("(net heat/H)-only factor to match 1.12", f"{(observed/fixed)**3:.6f}")

# Different nominal models and source types; not a same-condition conflict.
theory_share_lo, theory_share_hi, calibrated_share = 0.732, 0.739, 0.4867
out("friction-share nominal difference", f"{100*(theory_share_lo-calibrated_share):.2f}–{100*(theory_share_hi-calibrated_share):.2f} percentage points")
out("friction-share nominal factor", f"{theory_share_lo/calibrated_share:.2f}–{theory_share_hi/calibrated_share:.2f}")
