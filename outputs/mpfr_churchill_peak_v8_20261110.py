"""Counterexample to 'a single Churchill expression has no transition peak'."""

import factored_interval_v7_20261109 as V
import mpfr_derivative_v7_20261109 as D
import mpfr_interval_v7_20261109 as M


def main():
    D.activate()
    rr=D.D(M.J(0,.00125))  # eps_M=0..20 um divided by D_M=16 mm
    for re in (3000,3300):
        f=V.churchill_iv(D.D(M.J(re),M.J(1)),rr)
        print(f'Re={re}, all roughness: df/dRe in '
              f'[{float(f.d.lo):+.12e},{float(f.d.hi):+.12e}]')
        assert (f.d.lo>0 if re==3000 else f.d.hi<0)
    print('CERTIFIED: a smooth local maximum exists between Re=3000 and '
          '3300 for every declared roughness; the accepted root bracket '
          'is above this range.')


if __name__=='__main__':main()
