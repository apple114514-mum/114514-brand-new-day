"""Rerun v18's own model with Phi +/-1% and Jansen total indices.

This checks the declared-input-box dependence of the GSA ranking. It is
not an independent implementation of the flow model and not a certified
bound. Needs numpy, as does the uploaded v18 script.
"""

import contextlib
import io
from pathlib import Path
import runpy
import shutil
import tempfile

import numpy as np


SOURCE = Path(__file__).with_name("design-v18-upload-script-20261108.py")
with tempfile.TemporaryDirectory() as directory:
    source_copy = Path(directory) / "design_v18.py"
    shutil.copyfile(SOURCE, source_copy)
    with contextlib.redirect_stdout(io.StringIO()):
        namespace = runpy.run_path(str(source_copy))

model = namespace["model_vec"]
names = namespace["names"]
n = 8192
rng = np.random.default_rng(812)
half = np.array([.50, .01, .0909, .005, .30, 1.])
a = 1 + half * (2*rng.random((n,6))-1)
b = 1 + half * (2*rng.random((n,6))-1)
a[:,5] = .10*rng.random(n)
b[:,5] = .10*rng.random(n)

for closure in ("A","B"):
    fa,fb = model(a,closure),model(b,closure)
    variance = np.var(np.r_[fa,fb])
    indices=[]
    for i,name in enumerate(names):
        ab=a.copy()
        ab[:,i]=b[:,i]
        fab=model(ab,closure)
        st=.5*np.mean((fa-fab)**2)/variance
        indices.append((name,round(float(st),6)))
    print(closure,"Phi +/-1%",sorted(indices,key=lambda item:-item[1]))

print("Exploratory point-output GSA only: |D| at m_P=0.50 kg/s; no confidence intervals.")
