"""Numerically check whether the solver's root is the first sampled crossing.

This does NOT prove root uniqueness between scan nodes or over the input box.
"""

import itertools

import core_v2 as C
from proof_scout_v5_20261109 import residual


def main():
    for power in (3000.,6000.):
        for side,m0 in (('P',0.4),('M',0.15)):
            nbad_low=nmultiple=nroot_before=0
            min_low=float('inf')
            for bits in itertools.product((0,1),repeat=len(C.NAMES)):
                x=[C.BOUNDS[i][bit] for i,bit in enumerate(bits)]
                roots=C.fom(x,power)
                mr=roots['rp' if side=='P' else 'rm']['m']
                assert m0<mr
                v=[residual(side,m0+(1.1*mr-m0)*j/100,power,x)
                   for j in range(101)]
                min_low=min(min_low,v[0])
                if v[0]<=0: nbad_low+=1
                changes=sum(a*b<0 for a,b in zip(v[:-1],v[1:]))
                if changes != 1: nmultiple+=1
                first=next((m0+(1.1*mr-m0)*j/100 for j in range(1,101)
                            if v[j]<=0),None)
                if first is not None and first < mr-(1.1*mr-m0)/100:
                    nroot_before+=1
            print(f'{power/1000:g} kW {side}: m0={m0:g}; '
                  f'min F(m0)={min_low:.3f} Pa; '
                  f'nonpositive starts={nbad_low}; '
                  f'cases without exactly one sampled sign crossing={nmultiple}; '
                  f'first crossing well before solver root={nroot_before}')


if __name__=='__main__':
    main()
