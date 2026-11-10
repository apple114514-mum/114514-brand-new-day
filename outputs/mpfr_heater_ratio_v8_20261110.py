"""Independent MPFR heater-energy correction factor R_H at fixed powers.

It reuses the certified centered root brackets from mpfr_centered_bound_v8.
The common cp_fac cancels symbolically in cp_P/cp_M before interval division.
"""

import core_v2 as C
import mpfr_centered_bound_v8_20261110 as B
import mpfr_interval_v7_20261109 as M


def heater(side,q,m,x):
    seg=(C.P if side=='P' else C.M)['segs'][0]
    L=M.J(seg['L'])*(x['L_HS_M'] if side=='M' else M.J(1))
    ti=M.J(C.T_IN_REF)+x['dTin_'+side]
    u=M.J(seg['u'])*x['u_loss_fac']
    cp=M.cp_iv(ti,x['cp_fac'])
    a=u*L/(m*cp)
    mean=M.J(C.T_AMB)+(ti-M.J(C.T_AMB))*M.phi_iv(a)+(
        M.J(q)/(m*cp))*M.psi_iv(a)
    loss=u*L*(mean-M.J(C.T_AMB))
    return loss,M.cp_iv(ti,M.J(1))


def main():
    x=B.source_box()
    for q in (3000,4300,6000):
        B.verify_broad_brackets(q)
        B.verify_shared_signs(q)
        roots={s:M.J(B.root_edge(s,q,x,-1,18),
                     B.root_edge(s,q,x,1,18)) for s in ('P','M')}
        loss_p,cp_p=heater('P',q,roots['P'],x)
        loss_m,cp_m=heater('M',q,roots['M'],x)
        rh=(M.J(q)-loss_m)/(M.J(q)-loss_p)*(cp_p/cp_m)
        print(f'CERTIFIED R_H, Q={q} W: P loss={loss_p}, '
              f'M loss={loss_m}, R_H={rh}',flush=True)


if __name__=='__main__':main()
