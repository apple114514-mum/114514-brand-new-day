"""Check edges where sampled implicit derivatives change sign.

Optimization on those edges is a numerical check, not a certified extremum.
"""

import csv
import itertools
from collections import defaultdict
from pathlib import Path

from scipy.optimize import minimize_scalar

import core_v2 as C

ROOT = Path(__file__).resolve().parent
N = len(C.NAMES)


def vector(key, i, value):
    bits = iter(key)
    x = [C.BOUNDS[j][int(next(bits))] if j != i else value for j in range(N)]
    return x


def main():
    scout=list(csv.DictReader((ROOT/'proof_scout_v5_20261109.csv').open()))
    out=[]
    for power, name in ((6000.,'u_loss_fac'),(3000.,'dTin_M')):
        i=C.IDX[name]
        signs=defaultdict(dict)
        for r in scout:
            if float(r['power_kW']) != power/1000 or r['axis'] != name:
                continue
            bits=r['corner_bits']
            key=bits[:i]+bits[i+1:]
            signs[key][bits[i]]=float(r['dlog_massflux_daxis'])
        edge_flips=0
        for key,s in signs.items():
            if s['0']*s['1'] >= 0:
                continue
            edge_flips += 1
            lo,hi=C.BOUNDS[i]
            def fun(t):
                return C.fom(vector(key,i,t),power)['d_j']
            f0,f1=fun(lo),fun(hi)
            mode='maximum' if s['0']>0 else 'minimum'
            opt=minimize_scalar(lambda t: -fun(t) if mode=='maximum' else fun(t),
                                bounds=(lo,hi),method='bounded',
                                options={'xatol':(hi-lo)*1e-8})
            fopt=fun(opt.x)
            gain=(fopt-max(f0,f1)) if mode=='maximum' else (min(f0,f1)-fopt)
            out.append(dict(power_kW=power/1000,axis=name,edge_other_bits=key,
                            mode=mode,axis_lo=lo,axis_hi=hi,axis_opt=opt.x,
                            Dj_lo_pct=f0,Dj_hi_pct=f1,Dj_opt_pct=fopt,
                            interior_gain_pp=gain,deriv_lo=s['0'],deriv_hi=s['1']))
        candidate=[r for r in out if r['power_kW']==power/1000 and r['axis']==name]
        best=max(candidate,key=lambda r:r['interior_gain_pp'])
        print(f'{power/1000:g} kW {name}: {edge_flips} edge sign flips; '
              f'largest interior gain {best["interior_gain_pp"]:.6f} pp at '
              f'{best["axis_opt"]:.7f} ({best["mode"]}); '
              f'endpoints {best["Dj_lo_pct"]:.6f}, {best["Dj_hi_pct"]:.6f}; '
              f'interior {best["Dj_opt_pct"]:.6f}')
    with (ROOT/'interior_edge_v5_20261109.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,out[0].keys());w.writeheader();w.writerows(out)
    for power in (3000.,6000.):
        vals=[]
        for bits in itertools.product((0,1),repeat=N):
            x=[C.BOUNDS[i][bit] for i,bit in enumerate(bits)]
            vals.append(C.fom(x,power)['d_j'])
        subset=[r for r in out if r['power_kW']==power/1000]
        print(f'{power/1000:g} kW: corner D_j [{min(vals):.6f},{max(vals):.6f}]%; '
              f'explored interior edges '
              f'[{min(r["Dj_opt_pct"] for r in subset):.6f},'
              f'{max(r["Dj_opt_pct"] for r in subset):.6f}]%')


if __name__=='__main__':
    main()
