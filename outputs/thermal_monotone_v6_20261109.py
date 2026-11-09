"""Cross-check the analytic hydraulic/temperature order on box edges.

The analytic argument is in v6-method-proof-section-20261109.md.  Edge checks
only detect implementation errors; they are not the continuous proof.
"""

import csv
import itertools
from pathlib import Path

import core_v2 as C

ROOT = Path(__file__).resolve().parent
AXES = ('eps_M', 'k_aux_M', 'd_hole')


def main():
    rows=[]
    h=C.M['segs'][0]
    q_min=3000.
    t_in_max=C.T_IN_REF+C.BOUNDS[C.IDX['dTin_M']][1]
    u_max=h['u']*C.BOUNDS[C.IDX['u_loss_fac']][1]
    l_max=h['L']*C.BOUNDS[C.IDX['L_HS_M']][1]
    heat_margin=q_min-u_max*l_max*(t_in_max-C.T_AMB)
    assert heat_margin>0
    print(f'M heater minimum Q - UL(Tin-Tamb) = {heat_margin:.9f} W > 0')

    for q in (3000.,4300.,6000.):
        vals={}
        for bits in itertools.product((0,1),repeat=len(C.NAMES)):
            x=[C.BOUNDS[i][bit] for i,bit in enumerate(bits)]
            r=C.fom(x,q)
            if r is None:raise RuntimeError((q,bits))
            vals[bits]=(r['d_j'],r['d_t'])
        for label,idx in [('Dj',0),('DT',1)]:
            for end,fun in [('min',min),('max',max)]:
                bb=fun(vals,key=lambda b:vals[b][idx])
                triple=''.join(str(bb[C.IDX[a]]) for a in AXES)
                print(f'{q/1000:g} kW {label} {end}: {vals[bb][idx]:+.6f}% '
                      f'corner bits {bb}, (eps,aux,hole)={triple}')
        for axis in AXES:
            i=C.IDX[axis]
            expected_dj=-1 if axis!='d_hole' else 1
            expected_dt=-expected_dj
            diffs=[]
            for bits in vals:
                if bits[i]:continue
                hi=bits[:i]+(1,)+bits[i+1:]
                lo_dj,lo_dt=vals[bits]
                hi_dj,hi_dt=vals[hi]
                diffs.append((hi_dj-lo_dj,hi_dt-lo_dt))
            row=dict(power_kW=q/1000,axis=axis,pairs=len(diffs),
                     min_expected_Dj_gain_pp=min(expected_dj*d[0] for d in diffs),
                     max_expected_Dj_gain_pp=max(expected_dj*d[0] for d in diffs),
                     min_expected_DT_gain_pp=min(expected_dt*d[1] for d in diffs),
                     max_expected_DT_gain_pp=max(expected_dt*d[1] for d in diffs),
                     Dj_violations=sum(expected_dj*d[0]<=0 for d in diffs),
                     DT_violations=sum(expected_dt*d[1]<=0 for d in diffs))
            rows.append(row)
            print(f'{q/1000:g} kW {axis}: {len(diffs)} pairs, '
                  f'expected Dj margin {row["min_expected_Dj_gain_pp"]:.6f}..'
                  f'{row["max_expected_Dj_gain_pp"]:.6f} pp, '
                  f'expected DT margin {row["min_expected_DT_gain_pp"]:.6f}..'
                  f'{row["max_expected_DT_gain_pp"]:.6f} pp, '
                  f'violations {row["Dj_violations"]}/{row["DT_violations"]}')
    with (ROOT/'thermal_monotone_v6_20261109.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)


if __name__=='__main__':
    main()
