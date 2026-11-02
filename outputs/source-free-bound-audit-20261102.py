#!/usr/bin/env python3
"""Independent algebra check of the uploaded 'source-free' ratio model.

The CSV contrasts the uploaded ratio equation with one that retains the
heat-capacity orientation and the distributed-loss length/diameter factor.
These are conditional model calculations, not validated facility bounds.
Run from repository root:
  python outputs/source-free-bound-audit-20261102.py > outputs/source-free-bound-audit-20261102.csv
"""

import csv
import math
from pathlib import Path
import runpy
import sys


def bisect(fun, lo, hi, steps=90):
    flo, fhi = fun(lo), fun(hi)
    if not (flo < 0 < fhi):
        raise ValueError(f"root not bracketed: [{lo},{hi}] -> [{flo},{fhi}]")
    for _ in range(steps):
        mid = (lo + hi) / 2
        if fun(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def zhao_rho(t): return 11096.0 - 1.1944*t
def zhao_cp(t): return 159.0 - 0.0272*t + 7.12e-6*t*t
def zhao_mu(t): return 4.56e-3 - 7.03e-6*t + 3.61e-9*t*t
def uploaded_mu(t): return 4.94e-4*math.exp(754.1/t)

def yang_rho(t): return 11096.0 - 1.3235*t
def yang_cp(t): return 164.8 - .0394*t + 1.25e-5*t*t - 4.56e5/(t*t)
def yang_mu(t): return uploaded_mu(t)


ZHAO_UPLOAD = dict(rho=zhao_rho, cp=zhao_cp, mu=uploaded_mu)
ZHAO_TABLE4 = dict(rho=zhao_rho, cp=zhao_cp, mu=zhao_mu)
YANG = dict(rho=yang_rho, cp=yang_cp, mu=yang_mu)


def rise(q, m, tin, cp):
    return bisect(lambda dt: m*cp(tin+dt/2)*dt-q, 1e-10, 1000.0)


def ratio_state(*, d, length_ratio, height_pm, heat_pm, w, n,
                tin, mass_p, power_p, fluid, mode):
    """Return a root of the chosen scalar ratio equation.

    d = D_M/D_P, length_ratio = L_M/L_P, height_pm = H_P/H_M,
    heat_pm = Q_P/Q_M. All loss coefficients are assumed nonnegative and the
    local-loss ratio is assumed exactly one. The geometry factors are design
    hypotheses, not supplied net flow areas for Zhao's porous core.
    """
    rho, cp, mu = fluid['rho'], fluid['cp'], fluid['mu']
    r_ideal = (d**-4 * height_pm * heat_pm)**(1/3)
    dt_p = rise(power_p, mass_p, tin, cp)
    t_p = tin+dt_p/2

    def terms(x):
        mass_m = mass_p/(r_ideal*x)
        dt_m = rise(power_p/heat_pm, mass_m, tin, cp)
        t_m = tin+dt_m/2
        rho_ratio = rho(t_m)/rho(t_p)
        cp_ratio = cp(t_m)/cp(t_p)
        mu_ratio = mu(t_m)/mu(t_p)
        f_ratio = (r_ideal*x*d*mu_ratio)**n
        if mode == 'uploaded':
            k_ratio = 1+w*(f_ratio-1)
            residual = x**3-k_ratio/(rho_ratio*cp_ratio)
        elif mode == 'corrected':
            k_ratio = 1+w*((length_ratio/d)*f_ratio-1)
            residual = x**3-k_ratio*cp_ratio/rho_ratio
        else:
            raise ValueError(mode)
        return residual, mass_m, dt_m, t_m, k_ratio, cp_ratio, rho_ratio

    x = bisect(lambda xx: terms(xx)[0], .3, 2.0)
    residual, mass_m, dt_m, t_m, k_ratio, cp_ratio, rho_ratio = terms(x)
    return dict(x=x, mass_ratio_pm=r_ideal*x, mass_ratio_mp=1/(r_ideal*x),
                temp_ratio_mp=dt_m/dt_p, cold_m=tin, hot_m=tin+dt_m,
                k_ratio=k_ratio, cp_ratio=cp_ratio, rho_ratio=rho_ratio,
                residual=residual)


def row(writer, label, d, length_ratio, height_pm, heat_pm, target_pm,
        w, n, tin, mass_p, power_p, fluid, mode, note):
    r = ratio_state(d=d, length_ratio=length_ratio, height_pm=height_pm,
                    heat_pm=heat_pm, w=w, n=n, tin=tin, mass_p=mass_p,
                    power_p=power_p, fluid=fluid, mode=mode)
    writer.writerow((label, mode, f'{d:.7f}', f'{length_ratio:.7f}',
                     f'{height_pm:.7f}', f'{heat_pm:.7f}', f'{target_pm:.7f}',
                     f'{w:.9f}', f'{r["mass_ratio_pm"]:.9f}',
                     f'{100*(r["mass_ratio_pm"]/target_pm-1):.9f}',
                     f'{100*(target_pm/r["mass_ratio_pm"]-1):.9f}',
                     f'{r["temp_ratio_mp"]:.9f}', f'{r["cp_ratio"]:.9f}',
                     f'{r["k_ratio"]:.9f}', f'{r["residual"]:.3g}', note))
    return r


def w_at_target(fun, target, lo=0.0, hi=1.0):
    flo, fhi = fun(lo)-target, fun(hi)-target
    if flo*fhi >= 0:
        return None
    if flo < 0:
        return bisect(lambda w: fun(w)-target, lo, hi)
    return bisect(lambda w: target-fun(w), lo, hi)


def main():
    out=csv.writer(sys.stdout,lineterminator='\n')
    out.writerow(('case','equation','diameter_M_over_P','length_M_over_P',
                  'height_P_over_M','power_P_over_M','target_mass_P_over_M',
                  'prototype_friction_share_w','predicted_mass_P_over_M',
                  'D_mass_P_over_M_percent','epsilon_mass_M_over_P_percent',
                  'temp_M_over_P','cp_M_over_P','K_M_over_P','equation_residual','note'))
    zhao=(.5,.5,2.0,2**2.5,2**2.5,533.15,540.0,10e6)
    for mode,fluid,tag in (('uploaded',ZHAO_UPLOAD,'mixed viscosity'),
                           ('corrected',ZHAO_UPLOAD,'same viscosity as uploaded'),
                           ('corrected',ZHAO_TABLE4,'same-source Zhao Table 4 viscosity')):
        for w in (0.0,.3,1.0):
            row(out, 'Zhao_2020_'+tag.replace(' ','_'), *zhao[:5],w,.25,
                *zhao[5:], fluid,mode,tag)
    # KYLIN's original full-similarity ratios, evaluated with the Yang fluid
    # and an explicit *conditional* nominal operating state.
    d=.5**.7
    heat_pm=1/(.5**1.9)
    target_pm=1/(.5**1.9)
    for mode in ('uploaded','corrected'):
        for w in (0.0,.4867262,1.0):
            row(out,'KYLIN_full_similarity',d,.5,2.,heat_pm,target_pm,
                w,.25,513.33,1.2,24e3,YANG,mode,
                'conditional adiabatic ratio, not a measured performance bound')
    for mode in ('uploaded','corrected'):
        for w in (0.0,.4867262,1.0):
            row(out,'KYLIN_height_only',1.,.5,2.,1.,1.,w,.25,
                513.33,1.2,24e3,YANG,mode,
                'target mass P/M = 1 from same-power same-rise design')

    # A separate check in the prior four-section model: the local-loss sum is
    # fixed when US is changed, so this intervention isolates the heat closure.
    m=runpy.run_path(str(Path(__file__).with_name('loop-audit-repair-corrected-20261101.py')))
    p,_,_,_,ktot=m['calibrate'](3.35,US=6)
    for us in (6.0,0.0):
        pp=dict(p,US=us)
        pm=dict(pp,lR=.5,US=us*.5)
        mp,dp=m['solve'](pp)
        mm,dm=m['solve'](pm)
        out.writerow(('KYLIN_four_section_fixed_k_US_'+str(us),'full_four_section',
                      '1','0.5','2','1','1','',f'{mp/mm:.9f}',
                      f'{100*(mp/mm-1):.9f}',f'{100*(mm/mp-1):.9f}',
                      f'{dm["dT"]/dp["dT"]:.9f}','','','',
                      f'k_local_sum={ktot:.6f}, US_P={us:.1f} W/K'))

    kwargs=dict(d=.5,length_ratio=.5,height_pm=2.,heat_pm=2**2.5,
                n=.25,tin=533.15,mass_p=540.,power_p=10e6,fluid=ZHAO_UPLOAD)
    wz=w_at_target(lambda w:ratio_state(**kwargs,w=w,mode='corrected')['x']-1,.03)
    kh=dict(d=1.,length_ratio=.5,height_pm=2.,heat_pm=1.,n=.25,
            tin=513.33,mass_p=1.2,power_p=24e3,fluid=YANG)
    wh=w_at_target(lambda w:ratio_state(**kh,w=w,mode='corrected')['mass_ratio_mp']-1,-.03)
    print(f'Zhao corrected conditional w at +3% P/M = {wz:.9f}',file=sys.stderr)
    print(f'KYLIN height-only conditional w at -3% M/P = {wh:.9f}',file=sys.stderr)


if __name__=='__main__':
    main()
