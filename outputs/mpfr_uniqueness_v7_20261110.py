"""Adaptive MPFR proof of F_m<0 for the entire M input box.

Only mass flow, power and pipe roughness are bisected.  The other nine
coordinates remain at their full declared ranges in every certified box.
Each child reuses its parent's midpoint, so the subdivision has no gaps.
"""

import time

import gmpy2 as g

import factored_interval_v7_20261109 as V
import mpfr_derivative_v7_20261109 as D
import mpfr_interval_v7_20261109 as M


def main():
    D.activate()
    inputs=V.box_inputs(False)
    start=(M.mp(.15),M.mp(.32),M.mp(3000),M.mp(6000),M.mp(0),M.mp(20),0)
    stack=[start]
    checked=accepted=0
    max_depth=0
    worst=-g.inf()
    margin=M.mp(-1000)  # Pa/(kg/s), stricter than the zero needed for uniqueness
    begin=time.monotonic()
    while stack:
        ml,mh,ql,qh,el,eh,depth=stack.pop()
        x=dict(inputs)
        x['eps_M']=D.D(M.J(el,eh))
        f,*_=V.interval_residual('M',D.D(M.J(ml,mh),M.J(1)),D.D(M.J(ql,qh)),x)
        checked+=1
        if f.d.hi<margin:
            accepted+=1
            worst=max(worst,f.d.hi)
            max_depth=max(max_depth,depth)
            continue
        if checked%5000==0:
            print(f'progress checked={checked}, leaves={accepted}, stack={len(stack)}, '
                  f'depth={depth}, time={time.monotonic()-begin:.1f}s',flush=True)
        if depth>40 or checked>200000:
            print('INCOMPLETE',checked,accepted,str(f.d),
                  tuple(map(str,(ml,mh,ql,qh,el,eh))))
            return
        # Dimensionless widths; mass flow gets a modest priority because it
        # most strongly reduces the direct interval dependency in Churchill.
        widths=[(mh-ml)/M.mp('.17')*M.mp(1.5),
                (qh-ql)/M.mp(3000),
                (eh-el)/M.mp(20)]
        axis=max(range(3),key=lambda j:widths[j])
        if axis==0:
            mid=(ml+mh)/2
            stack.extend([(mid,mh,ql,qh,el,eh,depth+1),
                          (ml,mid,ql,qh,el,eh,depth+1)])
        elif axis==1:
            mid=(ql+qh)/2
            stack.extend([(ml,mh,mid,qh,el,eh,depth+1),
                          (ml,mh,ql,mid,el,eh,depth+1)])
        else:
            mid=(el+eh)/2
            stack.extend([(ml,mh,ql,qh,mid,eh,depth+1),
                          (ml,mh,ql,qh,el,mid,depth+1)])
    print(f'CERTIFIED M: checked={checked}, accepted={accepted}, '
          f'max_depth={max_depth}, max_F_m={float(worst):.6f} Pa/(kg/s), '
          f'seconds={time.monotonic()-begin:.1f}')


if __name__=='__main__':main()
