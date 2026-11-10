"""Diagnostic: does a naive normalized B/R slope tighten d ln(mM/mP)/dQ?

Only the first shared-input cell at 6000 W is tested.  This is not a
full-domain certificate.  The purpose is to check whether merely rewriting
B as (Q/m)*g and R as m^2*h gives an interval advantage before a larger
symbolic refactor of the temperature march is attempted.
"""

import core_v2 as C
import factored_interval_v7_20261109 as V
import mpfr_centered_bound_v8_20261110 as B
import mpfr_derivative_v7_20261109 as D
import mpfr_global_bound_v9_20261110 as G
import mpfr_interval_v7_20261109 as M


def side_rate(side, x, k, q=6000, parent=5):
    lower = G.edge(side,q,x,-1,G.WINDOWS[parent][side],16)
    upper = G.edge(side,q,x,+1,G.WINDOWS[parent][side],16)
    m = M.J(lower,upper)
    dx = {name:D.D(value) for name,value in x.items()}
    residual,b,fr,*_ = V.interval_residual(
        side,D.D(m,M.J(1)),D.D(M.J(q)),dx)
    fm = residual.d
    bm,rm = b.d,fr.d
    residual,b,fr,*_ = V.interval_residual(
        side,D.D(m),D.D(M.J(q),M.J(1)),dx)
    fq = residual.d
    bq,rq = b.d,fr.d
    direct = -fq/(m*fm)
    # Exact only at F=B-R=0, which the root enclosure contains.
    exponent = (M.J(q)*(bq/b.v-rq/fr.v))/(m*(rm/fr.v-bm/b.v))
    return direct,exponent/M.J(q)


def main():
    D.activate()
    q = 6000
    for k in (2,4,8,16):
        x = B.source_box()
        for name in B.SHARED:
            v = x[name]
            x[name] = M.J(v.lo,v.lo+(v.hi-v.lo)/k)
        xm = dict(x)
        for name in B.MONO_M:
            v=xm[name]
            xm[name]=M.J(v.lo if B.SIGNS[name]<0 else v.hi)
        p_direct,p_normal=side_rate('P',x,k)
        m_direct,m_normal=side_rate('M',xm,k)
        print('k',k,'first-cell dlnr/dQ direct',m_direct-p_direct,
              'normalized-B/R',m_normal-p_normal,flush=True)
    print('DIAGNOSTIC ONLY: both forms cross zero on this cell; the naive '
          'normalized rewrite is wider here.')


if __name__=='__main__':
    main()
