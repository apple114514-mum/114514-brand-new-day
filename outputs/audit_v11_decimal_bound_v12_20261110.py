"""Reproduce a counterexample to WorkBuddy v11's 288*u/a**2 error claim.

The tested expression and precision policy match `_mean_ratio_der` in the
user-provided ivcore.py.  MPFR-1024 is used only as a high-precision oracle;
the analytic source of the missing factor 1/a is described in the report.
"""

from decimal import Decimal, localcontext
import math

import gmpy2 as g


A_BINARY64 = 0.00010010536854846448
P = 32


def main():
    a = A_BINARY64
    with localcontext() as ctx:
        ctx.prec = P
        x = Decimal(a)  # exact conversion of the source binary64 input
        work = 1 / (x*x) - (-x).exp() / ((1-(-x).exp())**2)
    with g.context(g.get_context(), precision=1024):
        A = g.mpfr(a)
        E = g.exp(-A)
        exact = 1/(A*A) - E/((1-E)**2)
        work_mp = g.mpfr(str(work))
        rel_error = abs(work_mp-exact)/abs(exact)
        u = g.mpfr('5e-32')
        old_bound = 288*u/(A*A)
        corrected_h3_bound = 160*u/(A*A*A)
        rounded = float(work)
        rounded_error_ulp = abs(g.mpfr(rounded)-exact)/g.mpfr(math.ulp(rounded))
        print('a_binary64',repr(a))
        print('Decimal_working_precision',P)
        print('Decimal_output',work)
        print('MPFR_1024_reference_first_25_digits',str(exact)[:27])
        print('relative_working_error',f'{float(rel_error):.9e}')
        print('v11_claimed_relative_bound',f'{float(old_bound):.9e}')
        print('actual_divided_by_claim',f'{float(rel_error/old_bound):.6f}')
        print('corrected_160u_over_a3_bound',f'{float(corrected_h3_bound):.9e}')
        print('binary64_output_error_in_ulp',f'{float(rounded_error_ulp):.9f}')
        assert rel_error > old_bound*80
        assert rel_error < corrected_h3_bound
        assert rounded_error_ulp < 0.5
        print('VERDICT: v11 universal bound is false; this output remains well within 4 ulp.')


if __name__ == '__main__':
    main()
