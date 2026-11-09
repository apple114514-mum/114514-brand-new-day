"""Audit v24's scale-target and thermal-balance claims.

The 1-D solve is a conditional counterexample to 'the 16 m inputs have no
steady solution', not a verified plant prediction or a FoM upper bound.
"""

import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "components", HERE / "fluid-component-prior-domain-20261108.py"
)
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)

D = .016
AREA = math.pi * D**2 / 4
K_ORIFICE = C.orifice_idelchik_3(D, .010, .002)
U_INS = 2 * math.pi * .05 / math.log((.01005 + .050) / .01005)
T_IN = 473.15
T_AMB = 293.15
G = 9.81


def cp(t):
    return 164.8 - .0394*t + 1.25e-5*t*t - 4.56e5/(t*t)


def elbow(re):
    return 427.5 * re**(-.77) + .9


# (name, length m, dz/ds, heater W/m, cooler W/m, insulated)
def segments(qe, qc, horiz=5.0):
    return (
        ("heater", 1., +1., qe, 0., True),
        ("hot_rest", 2., +1., 0., 0., True),
        ("top_left", horiz/2, 0., 0., 0., True),
        ("top_right", horiz/2, 0., 0., 0., True),
        ("cooler", 1., -1., 0., qc, False),
        ("cold_rest", 2., -1., 0., 0., True),
        ("bottom_right", horiz/2, 0., 0., 0., True),
        ("bottom_left", horiz/2, 0., 0., 0., True),
    )


def integrate(m, qe, qc, step=.05, full=False, horiz=5.0, orifice=True):
    t = T_IN
    qloss = drive = friction = 0.
    tmax = t
    tmin = t
    cooler_t = []
    u_bridge = .5 / (5.0 + 2*horiz)
    for name, length, dzds, heat, cool, insulated in segments(qe, qc, horiz):
        n = round(length / step)
        ds = length / n
        u = (U_INS + u_bridge) if insulated else 0.
        for _ in range(n):
            def slope(temp):
                return (heat - cool - u*(temp-T_AMB))/(m*cp(temp))
            tm = t + .5*ds*slope(t)
            t += ds*slope(tm)
            qloss += u*(tm-T_AMB)*ds
            tmax, tmin = max(tmax,t), min(tmin,t)
            if full:
                rho = C.lbe_rho(tm)
                re = C.reynolds(m,D,C.lbe_mu(tm))
                f = C.churchill_darcy(re)
                drive += -rho*G*dzds*ds
                friction += f*ds/D * m*m/(2*rho*AREA*AREA)
                if name=="cooler":
                    cooler_t.append(t)
        if full and name in ("heater","top_right","cold_rest","bottom_left"):
            re = C.reynolds(m,D,C.lbe_mu(t))
            friction += elbow(re)*m*m/(2*C.lbe_rho(t)*AREA*AREA)
        if full and orifice and name=="bottom_right":
            friction += K_ORIFICE*m*m/(2*C.lbe_rho(t)*AREA*AREA)
    return dict(end=t, loss=qloss, drive=drive, friction=friction,
                max=tmax, min=tmin, cooler_t=cooler_t)


def cooler_for(m,qe,step,horiz=5.0,orifice=True):
    lo,hi=0.,qe
    for _ in range(48):
        mid=(lo+hi)/2
        if integrate(m,qe,mid,step,horiz=horiz,orifice=orifice)["end"] > T_IN:
            lo=mid
        else:
            hi=mid
    qc=(lo+hi)/2
    return qc,integrate(m,qe,qc,step,True,horiz,orifice)


def solve(qe,step=.05,horiz=5.0,orifice=True):
    lo,hi=.10,.40
    # Small-mass-flow trial can leave NEA's property range; it only brackets.
    for _ in range(48):
        mid=(lo+hi)/2
        qc,r=cooler_for(mid,qe,step,horiz,orifice)
        if r["drive"]-r["friction"] > 0:
            lo=mid
        else:
            hi=mid
    m=(lo+hi)/2
    qc,r=cooler_for(m,qe,step,horiz,orifice)
    return m,qc,r


def main():
    print("A. Equal-temperature component check, not a scaling constraint")
    re=C.reynolds(.2,D,C.lbe_mu(573.15))
    kp=C.churchill_darcy(re)*16/D
    kb=4*elbow(re)
    kt=kp+kb+K_ORIFICE
    print(f"Re={re:.6f}, Kpipe={kp:.6f}, K4elbow={kb:.6f}, "
          f"Korifice={K_ORIFICE:.6f}, Ktotal={kt:.6f}")
    print("Ktotal=22.8 has NOT been imposed as an input condition.")

    print("B. v24 energy identity")
    for qe,ql in ((3000.,764.0293534144305),(6000.,909.6858260127169)):
        qnet=qe-ql
        v24_cool=qnet-ql
        print(f"Qe={qe:.0f} W, Qloss={ql:.3f} W, Qnet={qnet:.3f} W, "
              f"v24_Qcool={v24_cool:.3f} W, correct_Qcool={qnet:.3f} W, "
              f"balance_residual={qe-ql-v24_cool:.3f} W")

    print("C. A self-consistent 1-D conditional counterexample")
    print("heater and cooler: 1 m uniform source/sink; "
          "0.5 W/K bridge budget spread over the insulated length; "
          "no K_aux; roughness=0")
    print("m is solved; coolant duty is solved from T_end=T_heater_in; "
          "buoyancy integrates rho(T) around the 3 m vertical legs")
    for horiz,orifice in ((5.0,True),(2.5,False)):
      print(f"layout: horizontal legs {horiz:.2f} m, "
            f"insulated length {5+2*horiz:.2f} m, orifice={orifice}")
      for qe in (3000.,6000.):
        for step in (.05,.025):
            m,qc,r=solve(qe,step,horiz,orifice)
            cooler_min=min(r["cooler_t"])
            print(f"Qe={qe:.0f} W ds={step:.3f} m -> "
                  f"m={m:.7f} kg/s, Tmax={r['max']:.4f} K, "
                  f"Qloss={r['loss']:.3f} W, Qcool={qc:.3f} W, "
                  f"heat_res={qe-r['loss']-qc:+.6f} W, "
                  f"drive={r['drive']:.3f} Pa, "
                  f"friction={r['friction']:.3f} Pa, "
                  f"cooler_Tmin={cooler_min:.3f} K, "
                  f"UA_sufficient_at_oil433={qc/(cooler_min-433.15):.2f} W/K")

    print("D. Churchill transition sign check")
    re0=C.reynolds(.1,D,C.lbe_mu(473.15))
    print(f"Re(.10 kg/s,473.15 K)={re0:.3f}; "
          f"mu+8% -> {re0/1.08:.3f}; mu-8% -> {re0/.92:.3f}")
    print("Positive df/dRe makes K rise with m locally; it does not by "
          "itself imply multiple steady roots.")


if __name__=="__main__":
    main()
