#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源无关条件界 v5：F_w 修正 + 上界对 delta 的依赖 + KYLIN 根管证书

对 2026-11-02 第四轮复核（source-free-v4-review）的逐条处理：

  [0] 四条逐条复现
      (i)  delta=0.35 -> D(w=0)=+10.5176% 已超 w=1 端点的 +9.7782%；阈值 delta*=0.323078
      (ii) KYLIN 宽箱 F_w 跨零 != 曲线不单调；根管 [0.99998,1.00001] 内 (l/d)f-1 恒负
      (iii)KYLIN 的 -0.00081% 来自 m_R=.268 三位印数，不是 d_R=.616
      (iv) Fw_iv 多除了一个 rho_R：真 -0.323380318 vs v4 -0.323619701
  [A] Fw_iv 修正（不影响任何判号结论，因为 rho_R>0；但"F_w 区间"此前不是导数的包络）
  [B] 新结果：上界对 delta 的依赖有闭式
        D_m <= max{(1+delta)^(1/3), (R_id d)^(n/(3-n))} - 1
      四步初等证明（反证 + M<=1 + mu_R<=1），且在 delta=0 处退化为 +9.9131%
  [C] 两个 delta 阈值：端点交换 0.323078（数值根）/ 0.327849（解析 xbar^3-1）
  [D] 判据二参数化：|D|<=3% 需 delta<=9.2727% 且 w<=w*(3%;delta)
  [E] KYLIN：根管证书取代宽箱判号；D 严格递减，端点即极值
  [F] 证书对象分层：Zhao=十进制链，KYLIN=所写浮点设计输入
  [G] 文献归因更正：K_EV/K_HS/K_pipe 属 Yue 2017 表 2，不在 Xu FR26 表 2
  [H] 可宣称 / 不可宣称

纯标准库。运行：python source_free_bound_v5.py
"""
import math
from pathlib import Path

LOG = []
INF = math.inf


def L(s=''):
    print(s)
    LOG.append(s)


# ============================================================ 区间核
def dn(x):
    return math.nextafter(x, -INF)


def up(x):
    return math.nextafter(x, INF)


def _w(lo, hi, k=4):
    for _ in range(k):
        lo, hi = dn(lo), up(hi)
    return lo, hi


class I:
    """闭区间。每个运算两端外移 >=1 ulp（round-to-nearest 误差 <=0.5 ulp）。"""

    __slots__ = ('a', 'b')

    def __init__(self, a, b=None):
        a = float(a)
        b = a if b is None else float(b)
        if a > b:
            raise ValueError('空区间 [%r,%r]' % (a, b))
        self.a, self.b = a, b

    @staticmethod
    def of(x):
        return x if isinstance(x, I) else I(float(x), float(x))

    def __add__(self, o):
        o = I.of(o)
        return I(dn(self.a + o.a), up(self.b + o.b))

    __radd__ = __add__

    def __neg__(self):
        return I(-self.b, -self.a)

    def __sub__(self, o):
        return self + (-I.of(o))

    def __rsub__(self, o):
        return I.of(o) - self

    def __mul__(self, o):
        o = I.of(o)
        v = (self.a * o.a, self.a * o.b, self.b * o.a, self.b * o.b)
        return I(dn(min(v)), up(max(v)))

    __rmul__ = __mul__

    def inv(self):
        if self.a <= 0.0 <= self.b:
            raise ZeroDivisionError('[%r,%r] 含 0' % (self.a, self.b))
        return I(dn(1.0 / self.b), up(1.0 / self.a))

    def __truediv__(self, o):
        return self * I.of(o).inv()

    def __rtruediv__(self, o):
        return I.of(o) * self.inv()

    def __pow__(self, p):
        if isinstance(p, int):
            r = I(1.0)
            for _ in range(p):
                r = r * self
            return r
        raise ValueError('只用整数幂；非整数幂请走 i_sqrt / i_cbrt / i_pow_nonneg')

    def __repr__(self):
        return '[%.15g,%.15g]' % (self.a, self.b)

    @property
    def w(self):
        return self.b - self.a

    def has(self, x):
        return self.a <= x <= self.b


def e_lit(s):
    """十进制字面量 -> 区间。float(s) 与真实十进制值差 <=0.5 ulp，外移 1 ulp 包住。"""
    x = float(s)
    return I(dn(x), up(x))


def i_sqrt(a, k=2):
    return I(*_w(dn(math.sqrt(a.a)), up(math.sqrt(a.b)), k))


def i_cbrt(a, k=2):
    return I(*_w(dn(math.cbrt(a.a)), up(math.cbrt(a.b)), k))


def i_pow_nonneg(a, p):
    """a>0, p 实数：exp(p ln a)，log/exp 各外移 8 ulp。"""
    if a.a <= 0.0:
        raise ValueError('底数须 >0')
    lo, hi = math.log(a.a), math.log(a.b)
    lo, hi = _w(dn(lo), up(hi), 2)
    lo, hi = p * lo, p * hi
    elo, ehi = math.exp(lo), math.exp(hi)
    return I(*_w(dn(elo), up(ehi), 8))


# ============================================================ 物性
class Props:
    """rho = r0 + r1 T；cp = c0 + c1 T + c2 T^2 + c3/T^2；mu = m0 exp(m1/T)。"""

    def __init__(self, name, r0, r1, c0, c1, c2, c3, m0, m1):
        self.name = name
        self.r0 = I(r0) if float(r0).is_integer() else e_lit(r0)
        self.r1 = e_lit(r1)
        self.c0 = I(c0) if float(c0).is_integer() else e_lit(c0)   # v4 的错：c0 当点区间
        self.c1, self.c2, self.c3 = e_lit(c1), e_lit(c2), e_lit(c3)
        self.m0, self.m1 = e_lit(m0), e_lit(m1)

    def cp(self, T):
        return self.c0 + self.c1 * T + self.c2 * (T * T) + self.c3 / (T * T)

    def dcp(self, T):
        return self.c1 + I(2.0) * self.c2 * T - I(2.0) * self.c3 / (T * T * T)

    def rho(self, T):
        return self.r0 + self.r1 * T

    def drho(self, T):
        return self.r1

    def mu(self, T):
        ex = self.m1 / T
        lo, hi = math.exp(ex.a), math.exp(ex.b)
        return self.m0 * I(*_w(dn(lo), up(hi), 8))

    def dlnmu(self, T):
        return -self.m1 / (T * T)


P_ZHAO = Props('Zhao2020 表4', 11096, '-1.1944', 159, '-0.0272', '7.12e-6', '0.0',
               '4.94e-4', '754.1')
P_XU = Props('Xu FR26 式(15)(17)(18)', 11096, '-1.3235', '164.8', '-0.0394',
             '1.25e-5', '-4.56e5', '4.94e-4', '754.1')

TIN = 533.15
MP = 540.0
QP = 10.0e6


# ============================================================ 模型
class Model:
    def __init__(self, d, lam, H_R, Q_R, n, props=P_ZHAO, R_ideal=None,
                 T_in=TIN, m_P=MP, Q_P=QP, delta=0.0, Q_R_iv=None):
        self.d, self.lam, self.H_R, self.n = d, lam, H_R, n
        self.props, self.delta = props, delta
        self.T_in, self.m_P, self.Q_P = T_in, m_P, Q_P
        self.Q_R_decl = Q_R
        self.i_Q_R = Q_R if Q_R_iv is None else Q_R_iv
        self.i_Tin = e_lit(T_in)
        self.i_mP = I(m_P)
        self.i_QP = I(Q_P)
        self.i_d = I(d)
        self.i_lam = I(lam)
        self.i_H = I(H_R)
        A_R = I(1.0) / (self.i_d * self.i_d)
        self.i_Rid = i_cbrt(A_R * A_R * self.i_H * self.i_Q_R)
        self.i_QM = self.i_QP / self.i_Q_R
        if R_ideal is None:
            self.R_ideal = None
        else:
            self.R_ideal = float(R_ideal)
            self.i_Rid_ideal = I(float(R_ideal))
        self.T_P_iv = self._solve_T(self.i_QP, self.i_mP)

    # ---------- 温度
    def _gT(self, Qiv, miv, Tiv):
        return miv * self.props.cp(Tiv) * (I(2.0) * (Tiv - self.i_Tin)) - Qiv

    def _solve_T(self, Qiv, miv, loT=500.0, hiT=700.0, iters=200):
        glo = self._gT(Qiv, miv, I(loT))
        ghi = self._gT(Qiv, miv, I(hiT))
        if not (glo.b < 0.0 and ghi.a > 0.0):
            raise ValueError('温度区间未夹住')
        lo, hi = loT, hiT
        for _ in range(iters):
            mid = 0.5 * (lo + hi)
            if mid <= lo or mid >= hi:
                break
            gm = self._gT(Qiv, miv, I(mid))
            if gm.b < 0.0:
                lo = mid
            elif gm.a > 0.0:
                hi = mid
            else:
                break
        return I(lo, hi)

    def T_iv(self, xiv):
        return self._solve_T(self.i_QM, self.i_mP / (self.i_Rid * xiv))

    # ---------- 标量版（打印/对照）
    def _cp_s(self, T):
        p = self.props
        return (p.c0.a + p.c1.a * T + p.c2.a * T * T + p.c3.a / (T * T))

    def _rho_s(self, T):
        return self.props.r0.a + self.props.r1.a * T

    def _mu_s(self, T):
        return self.props.m0.a * math.exp(self.props.m1.a / T)

    def T_s(self, x):
        m = self.m_P / (self.i_Rid.a * x)
        Q = self.i_QM.a
        dT = Q / (m * self._cp_s(self.T_in))
        for _ in range(300):
            dT = Q / (m * self._cp_s(self.T_in + dT / 2.0))
        return self.T_in + dT / 2.0

    @property
    def T_P(self):
        return 0.5 * (self.T_P_iv.a + self.T_P_iv.b)

    def M_s(self, x):
        T = self.T_s(x)
        return (self._cp_s(T) / self._cp_s(self.T_P)) / (self._rho_s(T) / self._rho_s(self.T_P))

    def f_s(self, x):
        T = self.T_s(x)
        return (self.i_Rid.a * x * self.d * self._mu_s(T) / self._mu_s(self.T_P)) ** self.n

    def G_s(self, x, w):
        return (1.0 - w) * (1.0 + self.delta) + w * (self.lam / self.d) * self.f_s(x)

    def F_s(self, x, w):
        return x ** 3 * (self._rho_s(self.T_s(x)) / self._rho_s(self.T_P)) - \
            self.G_s(x, w) * (self._cp_s(self.T_s(x)) / self._cp_s(self.T_P))

    def solve_s(self, w):
        lo, hi = 0.05, 6.0
        for _ in range(400):
            mid = 0.5 * (lo + hi)
            if self.F_s(mid, w) < 0:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def D_s(self, w):
        x = self.solve_s(w)
        if self.R_ideal is None:
            return x - 1.0
        if self.R_ideal == 1.0:
            return 1.0 / (self.i_Rid.a * x) - 1.0
        return self.i_Rid.a * x / self.R_ideal - 1.0

    # ---------- 区间版
    def f_iv(self, xiv, Tiv):
        muR = self.props.mu(Tiv) / self.props.mu(self.T_P_iv)
        base = self.i_Rid * xiv * self.i_d * muR
        return i_pow_nonneg(base, self.n) if abs(self.n - 0.25) > 1e-15 else \
            i_sqrt(i_sqrt(base))

    def F_iv(self, xiv, wiv, Tiv=None):
        Tiv = self.T_iv(xiv) if Tiv is None else Tiv
        G = (I(1.0) - wiv) * I(1.0 + self.delta) + wiv * I(self.lam / self.d) * self.f_iv(xiv, Tiv)
        return xiv ** 3 * (self.props.rho(Tiv) / self.props.rho(self.T_P_iv)) - \
            G * (self.props.cp(Tiv) / self.props.cp(self.T_P_iv))

    def F_dep_iv(self, xiv, wiv, Tiv=None):
        """等价写 G = 1 + w[(l/d)f - (1+delta)]，在根附近条件数好得多。"""
        Tiv = self.T_iv(xiv) if Tiv is None else Tiv
        mm = I(self.lam / self.d) * self.f_iv(xiv, Tiv) - I(1.0 + self.delta)
        return xiv ** 3 * (self.props.rho(Tiv) / self.props.rho(self.T_P_iv)) - \
            (I(1.0) + wiv * mm) * (self.props.cp(Tiv) / self.props.cp(self.T_P_iv))

    def Fx_iv(self, xiv, wiv, Tiv=None):
        """F = x^3 rho_R - G cp_R 的全导数（含 dln mu/dx 与 rho_R 的 T_x 项）。"""
        Tiv = self.T_iv(xiv) if Tiv is None else Tiv
        dT = I(2.0) * (Tiv - self.i_Tin)
        cp = self.props.cp(Tiv)
        dcp = self.props.dcp(Tiv)
        drho = self.props.drho(Tiv)
        Tx = cp * dT / (xiv * (dcp * dT + I(2.0) * cp))
        cpP, rhoP = self.props.cp(self.T_P_iv), self.props.rho(self.T_P_iv)
        cpR = cp / cpP
        rhoR = self.props.rho(Tiv) / rhoP
        f = self.f_iv(xiv, Tiv)
        G = (I(1.0) - wiv) * I(1.0 + self.delta) + wiv * I(self.lam / self.d) * f
        Gx = wiv * I(self.lam / self.d) * I(self.n) * f * \
            (I(1.0) / xiv + self.props.dlnmu(Tiv) * Tx)
        return (I(3.0) * (xiv ** 2) * rhoR + (xiv ** 3) * (drho * Tx / rhoP)
                - Gx * cpR - G * (dcp * Tx / cpP))

    def Fw_iv(self, xiv, wiv=None, Tiv=None):
        """v5 修正：F=x^3 rho_R - G cp_R 对 w 的偏导
           dF/dw = -cp_R [(l/d)f - (1+delta)]
        v4 返回 -（cp_R/rho_R)[...]，多除的 rho_R 来自把 F/rho_R 当成 F。"""
        Tiv = self.T_iv(xiv) if Tiv is None else Tiv
        cpR = self.props.cp(Tiv) / self.props.cp(self.T_P_iv)
        return -cpR * (I(self.lam / self.d) * self.f_iv(xiv, Tiv) - I(1.0 + self.delta))

    def root_iv(self, wiv, a, b, iters=200):
        box = I(a, b)
        Fa, Fb = self.F_iv(I(a), wiv), self.F_iv(I(b), wiv)
        if not (Fa.b < 0.0 and Fb.a > 0.0):
            raise ValueError('端点未夹住 F(a)=%r F(b)=%r' % (Fa, Fb))
        for _ in range(iters):
            mid = 0.5 * (box.a + box.b)
            Fm = self.F_iv(I(mid), wiv)
            Fxd = self.Fx_iv(box, wiv)
            if Fxd.a <= 0.0 or Fxd.has(0.0):
                raise ValueError('F_x 不过正')
            N = I(mid) - Fm / Fxd
            lo, hi = max(N.a, box.a), min(N.b, box.b)
            if lo > hi:
                raise ValueError('交为空')
            new = I(lo, hi)
            if new.w >= box.w:
                break
            box = new
        return box

    def Dx_sign(self):
        return 1.0 if self.R_ideal is None or self.R_ideal != 1.0 else -1.0

    def D_iv(self, xiv):
        if self.R_ideal is None:
            return xiv - I(1.0)
        if self.R_ideal == 1.0:
            return self.i_Rid_ideal / (self.i_Rid * xiv) - I(1.0)
        return self.i_Rid * xiv / self.i_Rid_ideal - I(1.0)


def edges(a, b, k):
    e = [dn(a)]
    for i in range(1, k):
        e.append(a + (b - a) * i / k)
    e.append(up(b))
    return [(e[i], e[i + 1]) for i in range(len(e) - 1) if e[i + 1] > e[i]]


QR_ZHAO = 4.0 * math.sqrt(2.0)
QR_ZHAO_IV = I(4.0) * i_sqrt(I(2.0))


# ============================================================ [0] 四条复核
def section_admit():
    L('=' * 78)
    L('[0] 第四轮复核四条逐条复现')
    L('=' * 78)

    # (i) delta=0.35 反例
    L('   (i) 上界依赖 delta —— 成立')
    for dd in (0.0, 0.07, 0.35, 0.40):
        c = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25, delta=dd)
        L('       delta=%.2f  D(w=0)=%+9.4f%%   D(w=1)=%+9.4f%%   端点次序 %s'
          % (dd, 100 * c.D_s(0.0), 100 * c.D_s(1.0),
             'w=1 更大' if c.D_s(1) > c.D_s(0) else 'w=0 更大'))
    z = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25)
    x1 = z.solve_s(1.0)
    M1 = z.M_s(x1)
    L('       两端相等的阈值 delta* = x1^3/M(x1)-1 = %+.9f（复核 0.323078）'
      % (x1 ** 3 / M1 - 1.0))
    L('       => "delta 只动下端" 只在 delta<=delta* 时成立，超出后上界由 w=0 给出。')

    # (ii)(iii) KYLIN
    L('')
    L('   (ii) 宽箱 F_w 跨零 != 曲线不单调 —— 成立；根管证书见 [E]')
    L('   (iii) -0.00081% 的来源 —— 成立，是 m_R=.268 的三位印数')
    r = Model(0.5 ** 0.7, 0.5, 2.0, 1 / 0.268, 0.25)
    e = Model(0.5 ** 0.7, 0.5, 2.0, 1 / (0.5 ** 1.9), 0.25)
    L('       m_R=.268（印数）：D(w=1) = %+.8f%%' % (100 * r.D_s(1.0)))
    L('       m_R=c^1.9（解析）：D(w=1) = %+.3e%%' % (100 * e.D_s(1.0)))
    L('       Q_R 相对差 = %.4f%%（1/.268 vs 1/c^1.9）；d 用的是 c^0.7=%.6f，不是 .616'
      % (100 * (1 / 0.268 / (1 / 0.5 ** 1.9) - 1.0), 0.5 ** 0.7))
    L('       => v4 把那 8e-4 pp 归给"d_R=.616 印刷取整"是错的；d 早已用解析指数。')

    # (iv) F_w
    L('')
    L('   (iv) Fw_iv 多除一个 rho_R —— 成立')
    x = 1.1
    T = z.T_s(x)
    cpR = z._cp_s(T) / z._cp_s(z.T_P)
    rhoR = z._rho_s(T) / z._rho_s(z.T_P)
    mm = z.lam / z.d * z.f_s(x) - 1.0
    L('       x=1.1,w=1：(l/d)f-1 = %+.9f' % mm)
    L('       真 dF/dw   = -cp_R*[(l/d)f-1]      = %+.12f   （复核 -0.323380318）'
      % (-cpR * mm))
    L('       v4 返回    = -(cp_R/rho_R)*[(l/d)f-1] = %+.12f' % (-cpR / rhoR * mm))
    L('       rho_R = %.9f，1/rho_R = %.9f' % (rhoR, 1.0 / rhoR))
    L('       => 判号方向不变（rho_R>0，全区间 [0.99882,1.0] 恒正），')
    L('          Zhao 的单调性结论保留；但"F_w 区间范围"此前不是导数的包络。')


# ============================================================ [A] F_w 修正后重证
def section_cert():
    L('')
    L('=' * 78)
    L('[A] F_w 修正后重证 Zhao：端点即极值这件事没变，变的是它依赖的条件')
    L('=' * 78)
    c = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25, props=P_ZHAO, Q_R_iv=QR_ZHAO_IV)
    worst, wlo, whi, gl, gh = INF, INF, -INF, INF, -INF
    for xa, xb in edges(0.98, 1.16, 12):
        xiv = I(xa, xb)
        for j in range(12):
            wiv = I(j / 12.0, (j + 1) / 12.0)
            T = c.T_iv(xiv)
            worst = min(worst, c.Fx_iv(xiv, wiv, T).a)
            fw = c.Fw_iv(xiv, wiv, T)
            wlo, whi = min(wlo, fw.a), max(whi, fw.b)
            g = I(c.lam / c.d) * c.f_iv(xiv, T)
            gl, gh = min(gl, g.a), max(gh, g.b)
    L('   144 箱（12 x 箱 x 12 w 箱，无缝）：')
    L('     min F_x            = %.6f  (>0 => 根唯一)' % worst)
    L('     F_w 范围（修正后） = [%+.6f, %+.6f]  恒负' % (wlo, whi))
    L('     (l/d)f 范围        = [%.6f, %.6f]  恒 >1' % (gl, gh))
    L('   => F_w<0 且 D=x-1 关于 x 增 => dD/dw = -F_w/F_x > 0 => D(w) 严格递增')
    L('      => w=1 是上界、w=0 是下界（仅在 delta=0 这一列）。')
    L('')
    L('   %-6s %-46s %-9s %-22s' % ('w', 'x ∈（已证明）', '宽度', 'D_m (P/M)'))
    for w in (0.0, 1.0):
        r = c.root_iv(I(w, w), 0.98, 1.16)
        D = c.D_iv(r)
        L('   %-6.1f [%.17f, %.17f] %-9.2e [%+.4f,%+.4f]%%'
          % (w, r.a, r.b, r.w, 100 * D.a, 100 * D.b))
    L('   => 紧包络 D_m ∈ [0,+9.7782%]（宽 6e-15）。这个数本轮未变，')
    L('      但它的合法前提要写全：delta=0、仅 w 变、其余全声明。')


# ============================================================ [B] 统一解析界
def section_unified():
    L('')
    L('=' * 78)
    L('[B] 新结果：上界对 delta 的依赖有闭式，且不需要单调性')
    L('=' * 78)
    L('   记 A=1+delta，B=(R_id d)^n，xbar=B^(1/(3-n))。断言：')
    L('')
    L('        x <= max{ A^(1/3), xbar }       对所有 w∈[0,1]、所有 delta>-1')
    L('')
    L('   证明（四步，只用 M<=1 与 mu_R<=1）：')
    L('     1. x>=1 时 T_M>=T_P；mu=m0 exp(m1/T) 随 T 减（m1=754.1>0）=> mu_R<=1')
    L('        => f=(R_id x d mu_R)^n <= B x^n。')
    L('     2. F=0 且 M<=1  =>  x^3 = M[(1-w)A+w(l/d)f] <= (1-w)A + w B x^n。')
    L('     3. 反设 x>max{A^(1/3),xbar}：则 x^3>A 且 x^(3-n)>B => B x^n < x^3，')
    L('        右端 < (1-w)x^3 + w x^3 = x^3，与第 2 步矛盾。')
    L('     4. x<1 时 D_m=x-1<0 <= max{A^(1/3),xbar}-1（因 xbar>1）。')
    L('   => 成立。下端要多一条前提：(l/d)f>=1 于声明域（本案例 [A] 已验：1.250~1.397）。')
    L('      在此前提下 G>=(1-w)(1+delta)+w*1>=min{1+delta,1}，于是：')
    L('        delta<=0：F_w<0 => D 递增 => 最小在 w=0；w=0 处 x^3=M(x)(1+delta)>=(1+delta)')
    L('                  （x<=1 时 M>=1）=> x>=A^(1/3)')
    L('        delta>=0：G>=1 => 若 x<1 则 x^3>=M(x)>1 矛盾，故 x>=1 => D>=0')
    L('      合起来（前提：M<=1、mu_R<=1、(l/d)f>=1）：')
    L('')
    L('        min{0, A^(1/3)-1}  <=  D_m  <=  max{A^(1/3), xbar} - 1')
    L('')
    L('   注意这条**没有用到 F_x>0、没有用到单调性、没有用数值根**；三条前提里 M<=1 与 mu_R<=1')
    L('   是物性方向给的，(l/d)f>=1 是几何/工况给的（本案 1.250~1.397，若某台架 w 很小时')
    L('   (l/d)f 可能 <1，那时下端要重算 —— 这不是普遍成立的条件）。')
    L('   所以它对 delta 全区间成立，不受"delta 只是情景"的限制。')
    L('')
    z = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25)
    d, n = 0.5, 0.25
    xbar = (z.i_Rid.a * d) ** (n / (3.0 - n))
    L('   赵几何：R_id=%.9f，R_id*d=%.9f，xbar=(R_id d)^(1/11)=%.10f'
      % (z.i_Rid.a, z.i_Rid.a * d, xbar))
    L('')
    L('   %-8s %-24s %-26s %-12s'
      % ('delta', '解析界', '端点（数值根）', '界宽出端点'))
    for dd in (-0.07, 0.0, 0.07, 0.20, 0.30, 0.35, 0.40, 0.60):
        c = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25, delta=dd)
        upv = max((1 + dd) ** (1 / 3), xbar) - 1
        lov = min(0.0, (1 + dd) ** (1 / 3) - 1)
        end = max(c.D_s(0.0), c.D_s(1.0))
        L('   %-8.2f [%+8.4f%%, %+8.4f%%]   %+9.4f%% ~ %+9.4f%%     %+8.4f%%'
          % (dd, 100 * lov, 100 * upv,
             min(100 * c.D_s(0.0), 100 * c.D_s(1.0)),
             max(100 * c.D_s(0.0), 100 * c.D_s(1.0)),
             100 * (upv - end)))
    L('')
    L('   => 界宽出端点 0.002~0.006 pp（delta=0.35 时 +10.5209 vs +10.5176）。')
    L('      端点先取 max 再比较，是因为 delta>delta* 后次序翻转 —— 这里已显式取 max。')
    L('   delta=0 时退化为 xbar-1 = +9.9131%，与 [A] 的紧包络差 0.135 pp。')


# ============================================================ [C] 两个阈值
def section_threshold():
    L('')
    L('=' * 78)
    L('[C] 两个 delta 阈值：端点交换 0.323078，解析 0.327849')
    L('=' * 78)
    z = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25)
    x1 = z.solve_s(1.0)
    M1 = z.M_s(x1)
    xbar = (z.i_Rid.a * 0.5) ** (0.25 / 2.75)
    L('   (a) 数值阈值（含变物性）：D(w=0)=D(w=1) <=> x(0)=x1')
    L('       由 w=0 关系 x^3=M(x)(1+delta)  =>  delta_num = x1^3/M(x1)-1')
    L('       x1=%.15f，M(x1)=%.12f  =>  delta_num = %+.9f' % (x1, M1, x1 ** 3 / M1 - 1))
    L('   (b) 解析阈值（M≡1 的上界式）：delta_ana = xbar^3-1 = %+.9f'
      % (xbar ** 3 - 1))
    L('       两者差 %.6f，正好是 M(x1) 偏离 1 的量（1-M=%.3e 的三倍）'
      % (xbar ** 3 - 1 - (x1 ** 3 / M1 - 1), 1 - M1))
    L('   => 报判据用 (b)（保守、可手算）；报"哪个端点更大"用 (a)。')
    L('')
    L('   物理含义：delta>0.323 时，**纯分布摩擦（w=1）反而比纯局阻（w=0）更不离谱**。')
    L('   这不是数值奇观，是两个上界的竞争：')
    L('     局阻线   x=(1+delta)^(1/3)          与 delta 同增')
    L('     摩擦线   x=(R_id d)^(n/(3-n))       与 delta 无关')
    L('   后者由 Re 内生的 f~(Re)^(-n) 给出，前者由 (1+delta)^(1/3) 给出。')


# ============================================================ [D] 判据二参数
def section_criterion():
    L('')
    L('=' * 78)
    L('[D] 判据二参数化：|D|<=3% 需 delta<=9.2727% 且 w<=w*(3%;delta)')
    L('=' * 78)
    L('   delta 现在有硬上限：w=0 端 x=(1+delta)^(1/3)，要 <=1.03 就得')
    L('     delta <= 1.03^3 - 1 = %+.6f  = 9.2727%%' % (1.03 ** 3 - 1))
    L('   超过它，无论 w 取多少（含 w=0）都做不到 3%。')
    L('')
    L('   %-9s %-14s %-14s %-16s' % ('delta', 'D(w=0)', 'w*(3%)', '说明'))
    z0 = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25)

    def wstar(c):
        if c.D_s(0.0) >= 0.03:
            return 0.0
        if c.D_s(1.0) < 0.03:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(60):
            m = 0.5 * (lo + hi)
            if c.D_s(m) < 0.03:
                lo = m
            else:
                hi = m
        return 0.5 * (lo + hi)

    for dd in (0.0, 0.02, 0.05, 0.07, 0.09, 0.0927):
        c = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25, delta=dd)
        ws = wstar(c)
        note = '基准（v2~v4 只报这一列）' if dd == 0.0 else (
            '±7%% 约定上限，判据收紧 68%%' % () if abs(dd - 0.07) < 1e-9 else
            ('临界，只剩 w~0' if dd > 0.09 else ''))
        L('   %-9.4f %+13.4f%% %-14.4f %-16s' % (dd, 100 * c.D_s(0.0), ws, note))
    L('')
    L('   两个结构性结论：')
    L('     1. delta<=0 时判据不变（w*(3%)=0.304，因为 D(0)=0 不动）；')
    L('     2. delta>0 时判据迅速收紧：delta=5% 时 w* 从 0.304 掉到 0.168，')
    L('        delta=9% 时只剩 0.013。')
    L('   => "判据 = w*(3%)" 是 delta=0 的特例；一般形式是 (delta, w) 平面上的边界。')
    L('      论文里必须写成两参数，否则 delta 的未知会被误读成"只影响下端"。')


# ============================================================ [E] KYLIN 根管
def section_kylin():
    L('')
    L('=' * 78)
    L('[E] KYLIN：宽箱跨零不等于变号 —— 改用根管证书，D 严格递减')
    L('=' * 78)
    L('   思路：宽箱 [0.9,1.2] 上 F_w 的区间跨 1，只说明"判不出号"。')
    L('   先证根落在很窄的管子里，再在管内判号。')
    L('')
    L('   %-28s %-30s %-30s' % ('物性版本', 'F(0.99998,·)', 'F(1.00001,·)'))
    tubes = []
    for props in (P_ZHAO, P_XU):
        c = Model(0.5 ** 0.7, 0.5, 2.0, 1 / 0.268, 0.25, props=props)
        wiv = I(0.0, 1.0)
        Fa = c.F_dep_iv(I(0.99998), wiv)
        Fb = c.F_dep_iv(I(1.00001), wiv)
        tubes.append((props, c, Fa, Fb))
        L('   %-28s [%+.3e,%+.3e] [%+.3e,%+.3e]'
          % (props.name, Fa.a, Fa.b, Fb.a, Fb.b))
    L('')
    L('   %-28s %-28s %-24s %-10s'
      % ('物性版本', '(l/d)f-1 在管内', 'F_x 在管内', 'F_w 号'))
    for props, c, Fa, Fb in tubes:
        tube = I(0.99998, 1.00001)
        T = c.T_iv(tube)
        mm = I(c.lam / c.d) * c.f_iv(tube, T) - I(1.0)
        Fx = c.Fx_iv(tube, I(0.0, 1.0), T)
        Fw = c.Fw_iv(tube, None, T)
        L('   %-28s [%+.3e,%+.3e] [%.4f,%.4f] %-10s'
          % (props.name, mm.a, mm.b, Fx.a, Fx.b, '正' if Fw.a > 0 else '未定'))
    L('')
    L('   由于 F(a,w)<0<F(b,w) 对整个 w∈[0,1] 成立，且 F_x>0 于管内，')
    L('   每个 w 的根唯一落在 [0.99998,1.00001]；在该管内 F_w>0（因 (l/d)f<1）')
    L('   => dx/dw = -F_w/F_x < 0 => D(w) 严格递减 => 端点即极值。')
    L('   => v4 的"KYLIN 非单调、只能 21 点扫描"撤回。')
    L('')
    L('   舍入归因（复核意见）：')
    r = Model(0.5 ** 0.7, 0.5, 2.0, 1 / 0.268, 0.25)
    e = Model(0.5 ** 0.7, 0.5, 2.0, 1 / (0.5 ** 1.9), 0.25)
    L('     m_R=.268（表 2 印三位）：D(w=1) = %+.8f%%' % (100 * r.D_s(1.0)))
    L('     m_R=c^1.9（解析指数）  ：D(w=1) = %+.3e%%' % (100 * e.D_s(1.0)))
    L('     若换成 d_R=.616（印数）、m_R 用解析值，D(w=1) = %+.8f%%'
      % (100 * Model(0.616, 0.5, 2.0, 1 / (0.5 ** 1.9), 0.25).D_s(1.0)))
    L('     => 8e-4 pp 主要由 m_R 承担，不是 d_R。v4 那句归因写错。')


# ============================================================ [F] 证书对象分层
def section_object():
    L('')
    L('=' * 78)
    L('[F] 证书对象要分层：Zhao 是十进制链，KYLIN 是浮点设计输入')
    L('=' * 78)
    L('   Zhao：所有输入都是十进制字面量（0.5 / 2 / 0.25 / 4*sqrt2 / 物性系数），')
    L('         经 e_lit、i_sqrt、i_cbrt 进入区间 => 可以说"原十进制模型的包含"。')
    L('   KYLIN：d=0.5**0.7、Q_R=1/0.268 都是**浮点运算结果**，本身带 0.5~1 ulp 误差，')
    L('         且两位印数 .268 与解析 c^1.9 差 0.021%。')
    L('         => 只能叫"所写浮点设计输入下的条件结果"，不能并进同一句"原十进制证书"。')
    L('   修法（本脚本）：P_XU 的 c0=164.8 由 I() 点区间改为 e_lit()；')
    L('         KYLIN 两例在表格标题里显式标 [浮点输入]。')
    L('   => 论文只能给 Zhao 一句"含浮点误差界的条件包络"；KYLIN 给"端点数值"。')


# ============================================================ [G] 文献归因
def section_refs():
    L('')
    L('=' * 78)
    L('[G] 文献归因更正：K_EV/K_HS/K_pipe 不在 Xu FR26 表 2')
    L('=' * 78)
    L('   Xu FR26-170（本地 文献原文/FR26-170_Xu.pdf）核对结果：')
    L('     - 全文检索 K_EV / K_HS / K_pipe / local resistance：**零命中**。')
    L('     - 表 2 只有 l_R, d_R, m_R, dT_R, q_R 与标准/简化回路编号。')
    L('     - 唯一提到阻力的是 §4 的"electric regulating valve"（标定手段，无数值）。')
    L('   => 我上一轮把 Yue 2017 表 2 的 K_EV≈2.5 / K_HS 2.6-2.9 / K_pipe 17.7-19.1')
    L('      误记为"Xu 表 2"，并据此提出"用它们给 delta 定界"的下一步。')
    L('      该项撤回：delta 目前仍然**没有任何一手来源**。')
    L('')
    L('   现状清单（哪些有一手、哪些没有）：')
    L('     %-34s %-12s %s' % ('量', '一手来源', '状态'))
    L('     %-34s %-12s %s' % ('浮升高差 3.35 m', 'Xu 表 1', '有'))
    L('     %-34s %-12s %s' % ('HS 1.8 / HX 1.5 / 总长 12 / D 26', 'Xu 表 1 + LFR-21', '有'))
    L('     %-34s %-12s %s' % ('24 kW / 2.6 cm / 导热油二次侧', 'LFR-21 档案', '有'))
    L('     %-34s %-12s %s' % ('逐段阻力 K_EV/K_HS/K_pipe', 'Yue 2017 表 2（付费，未核）', '缺'))
    L('     %-34s %-12s %s' % ('净流道 d/D 与湿周', '无', '缺'))
    L('     %-34s %-12s %s' % ('delta 的物理范围', '无', '缺'))
    L('')
    L('   在 delta 无源的情况下，[B] 的解析界仍是可用的最强陈述，因为它是')
    L('   把 delta 当**自由参数**给出的显式函数，而不是替它假设一个范围。')


# ============================================================ [H] 结论
def section_concl():
    L('')
    L('=' * 78)
    L('[H] 可宣称 / 不可宣称（v5）')
    L('=' * 78)
    L('   可宣称：')
    L('     1. 声明模型内、delta=0、仅 w∈[0,1] 变化时，Zhao 的 D_m∈[0,+9.7782%]，')
    L('        区间证书宽度 6e-15（前提：libm exp<=8 ulp、sqrt/cbrt<=2 ulp）。')
    L('     2. 把 delta 放开为自由参数，有**显式**界')
    L('           min{0,(1+delta)^(1/3)-1} <= D_m <= max{(1+delta)^(1/3), (R_id d)^(n/(3-n))} - 1')
    L('        四步初等证明，不用单调性、不用数值根；delta=0 时退化为 +9.9131%。')
    L('     3. 判据是二参数边界：delta<=9.2727% 且 w<=w*(3%;delta)。')
    L('     4. KYLIN 全相似（印数输入）D(w) 严格递减，端点即极值；偏差 -8e-4 pp')
    L('        主要来自 m_R 三位印数，不是模型失真。')
    L('   不可宣称：')
    L('     a. "delta 只影响下端"（delta>0.323 后上界改由 w=0 给出，且随 delta 增长）。')
    L('     b. "KYLIN 的 D(w) 不单调"（宽箱判不出号 != 变号；根管内是严格单调）。')
    L('     c. "w=0 有精确立方根闭式"（恒物性近似）。')
    L('     d. "K_R=1 是唯一缩比要求"（Xu 四条判据，只豁免壁导热）。')
    L('     e. "Xu 表 2 的局阻数据可给 delta 定界"（Xu 表 2 无阻力数值）。')
    L('     f. 任何把 +9.7782% 当"物理上界"的句子：它是 delta=0 假设下的界。')


def main():
    L('自然循环缩比失真：源无关条件界 v5（F_w 修正 + 上界对 delta 的依赖）  2026-11-02')
    section_admit()
    section_cert()
    section_unified()
    section_threshold()
    section_criterion()
    section_kylin()
    section_object()
    section_refs()
    section_concl()
    out = Path(__file__).with_name('source_free_bound_v5_log.txt')
    out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
    print('\n[log] %s（%d 行）' % (out.name, len(LOG)))


if __name__ == '__main__':
    main()
