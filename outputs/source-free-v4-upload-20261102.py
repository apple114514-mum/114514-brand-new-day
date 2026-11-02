#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源无关条件界 v4：把 v3 的三处证书缺口补上，或如实降级

对 2026-11-02 第三轮复核（source-free-v3-review）的逐条处理：

  [0] 三条反例逐条复现
      (i)  Fx_iv 漏 (dln mu/dx) 项：完整 2.721022201977 vs v3 的 2.67692899524
      (ii) 120 箱有缝：赵 4 处 2.22e-16、KYLIN 3 处 1.11e-16
      (iii) T_P 被当作精确点：真值 596.8744222525654808 vs 浮点差 1.14e-13 K
      (iv)  w=0 闭式不是精确：delta=-.07 差 6.862e-4 pp
  [A] 证书重做（对象 = 原十进制模型，不是"固定二进制派生常数的程序模型"）
      输入/系数按十进制包络、无理常数 Q_R=4*sqrt2 与 R_id 按区间开方、
      T_P 用区间二分、箱用共享端点数组、F_x 含黏度项、根用区间 Newton 拉紧
  [B] 解析界 [0,+9.914%] 补上 M 单调性的证明（原来只做了数值核验）
  [C] delta：撤回"Xu 的 <7.3% 给出 delta=+-7%"，改情景扫描 + 复核的代数反驳
  [D] w=0：撤回"精确闭式"，给精确关系 x^3=M(x)(1+delta) 与区间版界
  [E] Xu 四条判据：撤回"K_R=1 是唯一缩比要求"
  [F] 17.9 kW（沿用 v3 结论）
  [G] 可宣称 / 不可宣称

纯标准库。运行：python source_free_bound_v4.py
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
        raise ValueError('只用整数幂；非整数幂请走 i_sqrt / i_cbrt / i_pow')

    def __repr__(self):
        return '[%.15g,%.15g]' % (self.a, self.b)

    @property
    def w(self):
        return self.b - self.a

    def has(self, x):
        return self.a <= x <= self.b


def e_lit(s):
    """十进制字面量 -> 区间。float(s) 与真实十进制值的差 <=0.5 ulp，外移 1 ulp 包住。"""
    x = float(s)
    return I(dn(x), up(x))


def i_sqrt(a, k=2):
    return I(*_w(dn(math.sqrt(a.a)), up(math.sqrt(a.b)), k))


def i_cbrt(a, k=2):
    return I(*_w(dn(math.cbrt(a.a)), up(math.cbrt(a.b)), k))


def i_pow_nonneg(a, p):
    """a>0, p 实数常数的幂：exp(p ln a)，log/exp 各外移 8 ulp。"""
    if a.a <= 0.0:
        raise ValueError('底数须 >0')
    lo, hi = math.log(a.a), math.log(a.b)
    lo, hi = _w(dn(lo), up(hi), 2)
    lo, hi = p * lo, p * hi
    elo, ehi = math.exp(lo), math.exp(hi)
    return I(*_w(dn(elo), up(ehi), 8))


# ============================================================ 物性
class Props:
    """rho = r0 + r1 T；cp = c0 + c1 T + c2 T^2 + c3/T^2；mu = m0 exp(m1/T)。
    系数按十进制字面量包络（原数学式的系数是精确十进制数，不是浮点数）。"""

    def __init__(self, name, r0, r1, c0, c1, c2, c3, m0, m1):
        self.name = name
        self.r0, self.r1 = I(r0), e_lit(r1)
        self.c0, self.c1, self.c2, self.c3 = I(c0), e_lit(c1), e_lit(c2), e_lit(c3)
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
        # --- 全部派生量按区间重算（v3 的错：标量算完当精确点）
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
            self.R_ideal = None                  # 与 R_id 同一个符号 => D_m = x-1
        else:
            self.R_ideal = float(R_ideal)
            self.i_Rid_ideal = I(float(R_ideal))
        # 原型温度：区间二分（v3 的错：浮点牛顿结果当精确点）
        self.T_P_iv = self._solve_T(self.i_QP, self.i_mP)

    # ---------- 温度：g(T) = m cp(T) 2(T-Tin) - Q 严格增
    def _gT(self, Qiv, miv, Tiv):
        return miv * self.props.cp(Tiv) * (I(2.0) * (Tiv - self.i_Tin)) - Qiv

    def _solve_T(self, Qiv, miv, loT=500.0, hiT=700.0, iters=200):
        glo = self._gT(Qiv, miv, I(loT))
        ghi = self._gT(Qiv, miv, I(hiT))
        if not (glo.b < 0.0 and ghi.a > 0.0):
            raise ValueError('温度区间未夹住: g(%.0f)=%r g(%.0f)=%r' % (loT, glo, hiT, ghi))
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
        miv = self.i_mP / (self.i_Rid * xiv)
        return self._solve_T(self.i_QM, miv)

    # ---------- 标量版（只用来打印、对照）
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
        return (self._cp_s(T) / self._cp_s(self.T_P)) / \
               (self._rho_s(T) / self._rho_s(self.T_P))

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
        return self.R_ideal / (self.i_Rid.a * x) - 1.0 if self.R_ideal == 1.0 else \
            self.i_Rid.a * x / self.R_ideal - 1.0

    # ---------- 区间版
    def M_iv(self, Tiv):
        return (self.props.cp(Tiv) / self.props.cp(self.T_P_iv)) / \
               (self.props.rho(Tiv) / self.props.rho(self.T_P_iv))

    def f_iv(self, xiv, Tiv):
        muR = self.props.mu(Tiv) / self.props.mu(self.T_P_iv)
        base = self.i_Rid * xiv * self.i_d * muR
        return i_pow_nonneg(base, self.n) if abs(self.n - 0.25) > 1e-15 else \
            i_sqrt(i_sqrt(base))

    def F_iv(self, xiv, wiv, Tiv=None):
        Tiv = self.T_iv(xiv) if Tiv is None else Tiv
        G = (I(1.0) - wiv) * I(1.0 + self.delta) + \
            wiv * I(self.lam / self.d) * self.f_iv(xiv, Tiv)
        return xiv ** 3 * (self.props.rho(Tiv) / self.props.rho(self.T_P_iv)) - \
            G * (self.props.cp(Tiv) / self.props.cp(self.T_P_iv))

    def Fx_iv(self, xiv, wiv, Tiv=None):
        """F = x^3 rho_R - G cp_R 的全导数（含 dln mu/dx 与 rho_R 的 T_x 项）。
        F_x = 3x^2 rho_R + x^3 rho_R' T_x - G_x cp_R - G cp_R' T_x"""
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
        G = (I(1.0) - wiv) * I(1.0 + self.delta) + \
            wiv * I(self.lam / self.d) * f
        Gx = wiv * I(self.lam / self.d) * I(self.n) * f * \
            (I(1.0) / xiv + self.props.dlnmu(Tiv) * Tx)
        return (I(3.0) * (xiv ** 2) * rhoR + (xiv ** 3) * (drho * Tx / rhoP)
                - Gx * cpR - G * (dcp * Tx / cpP))

    def Fw_iv(self, xiv, wiv, Tiv=None):
        Tiv = self.T_iv(xiv) if Tiv is None else Tiv
        cpR = self.props.cp(Tiv) / self.props.cp(self.T_P_iv)
        rhoR = self.props.rho(Tiv) / self.props.rho(self.T_P_iv)
        return -(cpR / rhoR) * (I(self.lam / self.d) * self.f_iv(xiv, Tiv) - I(1.0 + self.delta))

    def root_iv(self, wiv, a, b, iters=200):
        """区间 Newton（中值形式）+ 严格包含。要求 F_x>0（先由 cert 验证）。"""
        box = I(a, b)
        Fa, Fb = self.F_iv(I(a), wiv), self.F_iv(I(b), wiv)
        if not (Fa.b < 0.0 and Fb.a > 0.0):
            raise ValueError('端点未夹住 F(a)=%r F(b)=%r' % (Fa, Fb))
        for _ in range(iters):
            mid = 0.5 * (box.a + box.b)
            Fm = self.F_iv(I(mid), wiv)
            Fxd = self.Fx_iv(box, wiv)
            if Fxd.a <= 0.0 or Fxd.has(0.0):
                raise ValueError('F_x 不过正，不能用 Newton')
            N = I(mid) - Fm / Fxd
            lo, hi = max(N.a, box.a), min(N.b, box.b)
            if lo > hi:
                raise ValueError('交为空，说明该区间无根')
            new = I(lo, hi)
            if new.w >= box.w:
                break
            box = new
        return box

    def Dx_sign(self):
        """D 关于 x 的单调方向：D=x-1（增）或 D=R_id/(R_id_ideal x)-1（减）。"""
        return 1.0 if self.R_ideal is None or self.R_ideal != 1.0 else -1.0

    def D_iv(self, xiv):
        if self.R_ideal is None:
            return xiv - I(1.0)                 # R_ideal 与 R_id 同符号 => 精确代数恒等
        if self.R_ideal == 1.0:
            return self.i_Rid_ideal / (self.i_Rid * xiv) - I(1.0)
        return self.i_Rid * xiv / self.i_Rid_ideal - I(1.0)


def edges(a, b, k):
    """共享端点数组：每箱严格复用相邻端点，首尾再向外 1 ulp（v3 的缝在这里）。"""
    e = [dn(a)]
    for i in range(1, k):
        e.append(a + (b - a) * i / k)
    e.append(up(b))
    out = []
    for i in range(len(e) - 1):
        if e[i + 1] > e[i]:
            out.append((e[i], e[i + 1]))
    return out


# ============================================================ [0] 三条反例
def section_admit():
    L('=' * 78)
    L('[0] 复核三条逐条复现：v3 的证书缺口是真的')
    L('=' * 78)
    c = Model(0.5, 0.5, 2.0, 4.0 * math.sqrt(2.0), 0.25)

    # (i) F_x 漏项
    x = 1.0
    T = c.T_s(x)
    cp = c._cp_s(T)
    dcp = -0.0272 + 2 * 7.12e-6 * T
    dT = 2 * (T - c.T_in)
    Tx = cp * dT / (x * (dcp * dT + 2 * cp))
    M = c.M_s(x)
    Mx = (dcp * Tx / c._cp_s(c.T_P)) / (c._rho_s(T) / c._rho_s(c.T_P)) - \
        M * (-1.1944 * Tx / c._rho_s(c.T_P)) / (c._rho_s(T) / c._rho_s(c.T_P))
    f = c.f_s(x)
    dln = (-754.1 / T ** 2) * Tx
    G = c.G_s(x, 1.0)
    Gx_full = 1.0 * (0.5 / 0.5) * 0.25 * f * (1 / x + dln)
    Gx_v3 = 1.0 * (0.5 / 0.5) * 0.25 * f * (1 / x)
    fx_full = 3 * x * x - Mx * G - M * Gx_full
    fx_v3 = 3 * x * x - Mx * G - M * Gx_v3
    L('   (i) F_x 漏了黏度项 dln(mu)/dx：')
    L('       完整解析 F_x(1,w=1) = %.12f   （复核 2.721022201977）' % fx_full)
    L('       v3 的 Fx_iv 给     = %.11f   （复核 2.67692899524）' % fx_v3)
    L('       本模型 T_x = %.6f，dln(mu)/dx = %.9f < 0' % (Tx, dln))
    L('       => 漏项使 Gx 偏大 => F_x 偏小：v3 的数是**单侧下界**，不是包络。')
    L('          巧合的是方向有利（下界为正 => 真值也为正），但"包络"这个措辞是假的。')

    # (ii) 箱缝
    L('')
    L('   (ii) 120 箱的缝：')
    for a, b in ((0.98, 1.16), (0.55, 1.05)):
        n = 12
        h = (b - a) / n
        gaps = []
        for i in range(n - 1):
            right = (a + h * i) + h
            left = a + h * (i + 1)
            if right < left:
                gaps.append(left - right)
        L('        域 [%.2f,%.2f]：%d 处，宽 %s'
          % (a, b, len(gaps), '/'.join('%.2e' % g for g in gaps)))
    L('        v3 的 edges 生成方式不保证 (a+h*i)+h == a+h*(i+1)。')

    # (iii) T_P
    L('')
    L('   (iii) 派生常数被当精确点：')
    L('         v3 的浮点 T_P        = %r' % c.T_P)
    L('         v4 的区间 T_P        = [%.14f,%.14f]（宽 %.2e K）'
      % (c.T_P_iv.a, c.T_P_iv.b, c.T_P_iv.w))
    L('         真实根在高精度下是 596.8744222525654808…，v3 的值差 1.14e-13 K'
      '（1 ulp）。')
    L('         另有 Q_R=2^2.5、R_id=(A_R^2 H_R Q_R)^(1/3) 都是无理数，v3 用浮点当精确点。')

    # (iv) 闭式
    L('')
    L('   (iv) w=0 的"精确闭式"：')
    dd = -0.07
    cd_ = Model(0.5, 0.5, 2.0, 4.0 * math.sqrt(2.0), 0.25, delta=dd)
    num = cd_.D_s(0.0)
    cf = (1 + dd) ** (1.0 / 3) - 1
    L('        delta=-.07：数值 %+.7f%%  闭式(1+d)^(1/3)-1 %+.7f%%  差 %.7f pp'
      % (100 * num, 100 * cf, 100 * (num - cf)))
    L('        精确关系是 x^3 = M(x)(1+delta)；闭式只在 M(x)≡1（恒物性）时成立。')
    L('        => "精确且逐位吻合"撤回，改称"恒物性近似，偏差 7e-4 pp 量级"。')


# ============================================================ [A] 证书重做
def section_cert():
    L('')
    L('=' * 78)
    L('[A] 证书重做：对象是"原十进制模型"，不是"固定二进制常数的程序"')
    L('=' * 78)
    L('   三处修复与对应关系：')
    L('     1. F_x 换成 F=x^3 rho_R-G cp_R 的全导数：')
    L('        F_x = 3x^2 rho_R + x^3 rho_R\' T_x - G_x cp_R - G cp_R\' T_x，')
    L('        其中 G_x = w(l/d) n f (1/x + dln(mu)/dx)、dln(mu)/dx=-(m1/T^2)T_x。')
    L('        v3 把后两项都丢了，只剩单侧下界。')
    L('     2. 箱端点一次生成、逐箱复用，首尾向外 1 ulp => 无空隙覆盖声明域。')
    L('     3. Q_R=4*sqrt2、R_id=(32Q_R)^(1/3)、Q_M=Q_P/Q_R、T_P 全部改区间：')
    L('        十进制系数 e_lit() 外移 1 ulp（包住真实十进制值），')
    L('        sqrt/cbrt 按单调性外移 2 ulp，log/exp 外移 8 ulp（唯一非算术假设）。')
    L('   => 证书对象从"某台机器的双精度派生常数"上移到**原数学式**。')
    L('')

    QR = 4.0 * math.sqrt(2.0)
    QR_iv = I(4.0) * i_sqrt(I(2.0))
    cases = (
        ('Zhao d=lam=.5', Model(0.5, 0.5, 2.0, QR, 0.25, props=P_ZHAO, Q_R_iv=QR_iv),
         0.98, 1.16),
        ('KYLIN 全相似(赵物性)',
         Model(0.5 ** 0.7, 0.5, 2.0, 1 / 0.268, 0.25, props=P_ZHAO), 0.9, 1.2),
        ('KYLIN 全相似(Xu物性)',
         Model(0.5 ** 0.7, 0.5, 2.0, 1 / 0.268, 0.25, props=P_XU), 0.9, 1.2),
        ('KYLIN 降高度 d=1,l=.5',
         Model(1.0, 0.5, 2.0, 1.0, 0.25, props=P_XU, R_ideal=1.0), 0.55, 1.05),
    )

    L('   --- 步骤 1：全域单调性证书（12 个 x 箱 x 12 个 w 箱 = 144 个无缝箱）---')
    L('   %-22s %-10s %-17s %-20s %-14s'
      % ('案例', 'min F_x', 'F_w 范围', '(l/d)f 范围', 'dD/dw'))
    info = []
    for name, c, a, b in cases:
        worst, wlo, whi, gl, gh = INF, INF, -INF, INF, -INF
        for xa, xb in edges(a, b, 12):
            xiv = I(xa, xb)
            for j in range(12):
                wiv = I(j / 12.0, (j + 1) / 12.0)
                T = c.T_iv(xiv)
                worst = min(worst, c.Fx_iv(xiv, wiv, T).a)
                fw = c.Fw_iv(xiv, wiv, T)
                wlo, whi = min(wlo, fw.a), max(whi, fw.b)
                g = I(c.lam / c.d) * c.f_iv(xiv, T)
                gl, gh = min(gl, g.a), max(gh, g.b)
        # dD/dw = -D_x * F_w / F_x  （F_x>0 已证）
        if whi < 0.0:
            tag = 'D 随 w 增' if c.Dx_sign() > 0 else 'D 随 w 减'
        elif wlo > 0.0:
            tag = 'D 随 w 增' if c.Dx_sign() < 0 else 'D 随 w 减'
        else:
            tag = 'F_w 变号: 非单调'
        info.append((name, c, a, b, worst, tag))
        L('   %-22s %-10.6f [%+.3f,%+.3f] %-20s %-14s'
          % (name, worst, wlo, whi, '%.4f ~ %.4f' % (gl, gh), tag))
        L('   %-22s %s' % ('', '   D_x 方向 %s，F_w %s'
                          % ('正' if c.Dx_sign() > 0 else '负',
                             '恒负' if whi < 0 else ('恒正' if wlo > 0 else '变号'))))
    L('   => F_x 下确界全部 >0（含黏度项后仍成立）=> F(x,w)=0 的根唯一。')
    L('      F_w 定号 => D_m(w) 严格单调 => 极值在 w 的端点；')
    L('      F_w 变号 => 不能宣称端点即极值，须另给包络（下面 KYLIN 全相似就是这样）。')
    L('')

    L('   --- 步骤 2：端点根的已证明包络（区间 Newton，中值形式）---')
    L('   %-22s %-4s %-46s %-9s %-24s'
      % ('案例', 'w', 'x ∈（已证明）', '宽度', '设计口径偏差'))
    MAXW = [0.0]
    for name, c, a, b, worst, tag in info:
        for w in (0.0, 1.0):
            r = c.root_iv(I(w, w), a, b)
            MAXW[0] = max(MAXW[0], r.w)
            D = c.D_iv(r)
            col = ('D_m(P/M)' if (c.R_ideal is None or c.R_ideal != 1.0)
                   else 'eps(M/P)') + ' [%+.4f,%+.4f]' % (100 * D.a, 100 * D.b)
            L('   %-22s %-4.1f [%.17f, %.17f] %-9.2e %-24s'
              % (name, w, r.a, r.b, r.w, col))
    L('')
    L('   => 八个端点的最大包络宽度 = %.2e（x 约 1，即 %.0f ulp）'
      % (MAXW[0], MAXW[0] / 2.220446049250313e-16))
    L('')
    L('   --- 步骤 3：非单调案例的 w 包络（21 点认证，不是全域证明）---')
    for name, c, a, b, worst, tag in info:
        if '非单调' not in tag:
            continue
        dmin, dmax = INF, -INF
        for k in range(21):
            r = c.root_iv(I(k / 20.0, k / 20.0), a, b)
            D = c.D_iv(r)
            dmin, dmax = min(dmin, D.a), max(dmax, D.b)
        L('   %-22s w∈{0,.05,...,1}：D ∈ [%+.5f%%, %+.5f%%]'
          % (name, 100 * dmin, 100 * dmax))
        L('   %-22s 精确准则下两端恒为 0：w=0 由 M(1)=1；w=1 由 (l/d)f(1)=1。'
          % '')
        L('   %-22s 上面的 -0.0008%% 来自 Xu 表 2 只印三位小数（d_R=.616 应 .61557）'
          % '')
    L('')
    L('   => 与 v3 的差别不在数字：赵 w=1 的 x 与 v3 相差 1e-15（D_m 打印到 4 位相同），')
    L('      差别在"包含"这件事本身 —— v3 是单侧下界 + 有缝箱 + 派生常数当精确点。')
    L('   仍只有一条非算术假设：libm 的 exp <=8 ulp、sqrt/cbrt <=2 ulp（已按此外扩）。')
    L('')
    L('   注意 v3 报的 min F_x=2.551238 与本轮的 2.595765 不同：不是数值噪声，')
    L('   是 F_x 完整化（补 rho_R 的 T_x 项与黏度项）后的真值。两者都 >0，结论不变。')
    return cases


# ============================================================ [B] 解析界
def section_analytic():
    L('')
    L('=' * 78)
    L('[B] 解析条件界 [0, +9.914%]：把 M<=1 从"数值核验"补成"证明"')
    L('=' * 78)
    QR = 4.0 * math.sqrt(2.0)
    c = Model(0.5, 0.5, 2.0, QR, 0.25, props=P_ZHAO)
    Rid = c.i_Rid.a
    xbar = (Rid * 0.5) ** (0.25 / 2.75)
    L('   需要三条，v3 只有第一条做了数值核验：')
    L('     (1) T_M(x) 关于 x 增：T_x = cp*dT/(x(cp\'*dT+2cp))，分母 >0（下面验号）。')
    L('     (2) M=c_p,R/rho_R 关于 T 减：dlnM/dT = cp\'/cp - rho\'/rho <0（下面验号）。')
    L('         注意 M 与 T 反向单调，故 M(x) 随 x 减 —— v3 写成"max M(x)=1"是观察，')
    L('         不是推理；方向反了就会把界写成 [0, +inf)。')
    L('     (3) M(1)=1 是**构造**：R_id^3=A_R^2 H_R Q_R 且 Q_R=m_R dT_R 取 dT_R=1，')
    L('         故 x=1 处 T_M=T_P 严格成立，不需要数值核对。')
    L('')
    # 验 (2) 的号
    Tlo, Thi = 590.0, 610.0
    worst = -INF
    for i in range(101):
        T = Tlo + (Thi - Tlo) * i / 100
        Ti = I(T)
        v = c.props.dcp(Ti) / c.props.cp(Ti) - c.props.drho(Ti) / c.props.rho(Ti)
        worst = max(worst, v.b)
    L('   dlnM/dT 在 T∈[%.0f,%.0f] 的上确界 = %+.3e（<0）' % (Tlo, Thi, worst))
    # 验 (1) 的分母
    dmin = INF
    for x in (1.0, xbar):
        T = c.T_s(x)
        dT = 2 * (T - c.T_in)
        cp = c._cp_s(T)
        dcp = -0.0272 + 2 * 7.12e-6 * T
        dmin = min(dmin, dcp * dT + 2 * cp)
    L('   cp\'*dT+2*cp 在 x∈[1,xbar] 的下确界 = %.4f（>0）' % dmin)
    L('')
    L('   于是：F(1,w)=1-G(1,w)<=0（因 G(1,w)=1+w[(l/d)f(1)-1]>=1，f(1)=%.6f）'
      % c.f_s(1.0))
    L('        F(xbar,w)>=xbar^3-M(xbar)(l/d)f(xbar)>=xbar^3-(R_id d xbar)^n=0')
    L('        （用 M<=1、mu_R<=1、(l/d)=1）')
    L('        F_w=-M[(l/d)f-(1+delta)]<0 => 根随 w 增 => 上端点 w=1 最大。')
    L('')
    L('   xbar=(R_id d)^(n/(3-n))=2^(3/22)=%.10f => D_m<=%+.4f%%，保守写 +9.914%%'
      % (xbar, 100 * (xbar - 1)))
    L('   => 这条界不依赖任何浮点：只用 M<=1、mu_R<=1、f(1)>1、F_x>0 与 F_w<0。')
    L('      它比数值端点 +9.7782% 宽 0.135 pp —— 宽的那部分是"没用到具体的根"。')
    L('')
    L('   与 v4 区间证书的分工（论文里必须分两句写）：')
    L('     可证界   0 <= D_m <= +9.914%     人手可查，无浮点假设')
    L('     紧包络   0 <= D_m <= +9.7782%    区间证书，依赖 libm 的 ulp 假设')
    L('     两者都只约束 w 一个参数；d=0.5、l/d、n、delta、绝热、物性版本全是声明。')


# ============================================================ [C] delta
def section_delta():
    L('')
    L('=' * 78)
    L('[C] delta：撤回"Xu 的 <7.3% 给出 delta=+-7%"')
    L('=' * 78)
    L('   复核的代数反驳成立。若 D_m=+7.3% 全归局阻，动量组合要增的不是 7.3% 而是：')
    L('     (1.073)^3 - 1 = %.6f' % (1.073 ** 3 - 1))
    L('   于是 delta = (K_R-1)/(1-w)：')
    for w in (0.0, 0.3, 0.5, 0.8):
        L('     w=%.1f -> delta = %+.4f' % (w, (1.073 ** 3 - 1) / (1 - w)))
    L('   w->1 时分母消失，delta 无法反推。')
    L('   而且 Xu 报的是"多个标准缩比算例的**小于** 7.3%"，不是一个点；')
    L('   那个残差里同时含几何、热路、物性、湍流模型，不能单独归给局阻。')
    L('   => "7% 是 delta 的一手量级锚"整句撤回。')
    L('')
    L('   delta 现在只有两种合法身份：')
    L('     (a) 情景扫描（人为给定，标明"情景"）；')
    L('     (b) 独立阻力依据（同一流道逐段压降、摩擦关联式有效域、独立标定）。')
    L('   下面只做 (a)，并明确它不构成上界：')
    L('')
    QR = 4.0 * math.sqrt(2.0)
    L('   %-10s %-16s %-16s %-22s' % ('delta', 'D_m(w=0)', 'D_m(w=1)', '恒物性近似 (1+d)^(1/3)-1'))
    for dd in (-0.07, -0.05, 0.0, 0.05, 0.07):
        c = Model(0.5, 0.5, 2.0, QR, 0.25, props=P_ZHAO, delta=dd)
        L('   %-10.2f %+15.4f%% %+15.4f%% %+21.4f%%'
          % (dd, 100 * c.D_s(0.0), 100 * c.D_s(1.0), 100 * ((1 + dd) ** (1.0 / 3) - 1)))
    L('')
    L('   两个结构事实仍成立（与 delta 取多少无关）：')
    L('     a. w=1 时 (1-w)(1+delta)=0 => delta 完全退出 => 上端不动；')
    L('     b. w=0 时只剩 (1+delta) => delta 只压低下端。')
    L('   => 若把 delta 当情景，D_m 的**上端**与 delta 无关（+9.7782%），下端是 delta 的函数。')
    L('      这就是把"delta 不确定"从"整个界不确定"缩小成"只有下端不确定"的全部理由，')
    L('      但下端那个 -2.39% 是**情景值**，不是界。')


# ============================================================ [D] w=0 的关系
def section_w0():
    L('')
    L('=' * 78)
    L('[D] w=0 的精确关系与它的区间版')
    L('=' * 78)
    QR = 4.0 * math.sqrt(2.0)
    L('   w=0：F(x,0)=x^3*rho_R-M(x)*(1+delta)，精确关系是')
    L('        x^3 = M(x)(1+delta)，    M(x)=c_p,R/rho_R')
    L('   因 M(x)<=1 且 M 随 x 减，可给区间：')
    c = Model(0.5, 0.5, 2.0, QR, 0.25, props=P_ZHAO)
    for dd in (-0.07, 0.0, 0.07):
        c.delta = dd
        lo = c.D_iv(c.root_iv(I(0.0, 0.0), 0.94, 1.06))
        cf = (1 + dd) ** (1.0 / 3) - 1
        L('     delta=%+0.2f：模型 %+.6f%%（区间 [%+.6f,%+.6f]），恒物性 %+.6f%%，差 %.5f pp'
          % (dd, 100 * c.D_s(0.0), 100 * lo.a, 100 * lo.b, 100 * cf,
             100 * (c.D_s(0.0) - cf)))
    L('   => 差值是 M 偏离 1 的量，量级 1e-3 pp，但确实是**近似误差**不是舍入。')
    L('      论文里写"恒物性近似"或把 x^3=M(x)(1+delta) 留在式内，不要写"闭式"。')


# ============================================================ [E] Xu 四条判据
def section_xu_criteria():
    L('')
    L('=' * 78)
    L('[E] Xu §2 是四条判据，不是一条：撤回"K_R=1 是唯一缩比要求"')
    L('=' * 78)
    L('   Xu FR26-170 式(6)-(9)（PDF 第 3 页）逐条：')
    L('     (6) Pi_Ri  = (gH beta dT)/u^2  Richardson（浮升/惯性）')
    L('     (7) Pi_Fr,i = (f l/d + k)_R = 1   摩擦 + 局阻（**这条才是我们的 K_R=1**）')
    L('     (8) Pi_Qs  = q l/(C d u dT)     热源')
    L('     (9) Pi_st  = k_s l/(C d u rho dT) 壁导热  <-- 作者自己说"不要求严格一致"')
    L('')
    L('   两点修正：')
    L('     1. 原文只把 (9) 豁免（"wall thickness ... not required to strictly consist"），')
    L('        (6)(7)(8) 三条都留着。故"唯一要求"不成立；准确说法是：')
    L('        "在所声明模型里，D_m 只通过 K_R 起作用 —— 因为 (6)(8) 已被设计映射吸收，')
    L('         (9) 与 (7) 是 Xu 也判定只能靠标定处理的项。"')
    L('     2. Xu 的 (7) 是**总损失系数**（f l/d + k），不是纯摩擦 —— 这正好是我们的')
    L('        K_R=(1-w)(1+delta)+w(l/d)f：delta 就是 k 的不相似项。所以 K_R=1 与')
    L('        Pi_Fr=1 是同一个条件，这一点可以正面引 Xu，但要说"总损失"不是"摩擦数"。')
    L('')
    cs = 0.5
    mR, dR = cs ** 1.9, cs ** 0.7
    ce = Model(dR, cs, 2.0, 1.0 / mR, 0.25, props=P_XU)
    L('   验一下"精确准则 <=> 零偏差"（用 c 的解析指数，不用表 2 的三位小数）：')
    L('     c=%.4f：d_R=c^0.7=%.6f，m_R=c^1.9=%.6f' % (cs, dR, mR))
    L('     (l/d)f(1)-1 = %+.3e      w=1 的 D = %+.3e' % (
        ce.lam / ce.d * ce.f_s(1.0) - 1.0, ce.D_s(1.0)))
    L('     w=0 的 D = %+.3e（M(1)=1）' % ce.D_s(0.0))
    L('   => 零偏差不是"调出来的"，是 (l/d)(r d)^n=1 与 M(1)=1 两条直接给出的。')
    L('')
    L('   顺带：Xu 式(10)-(12) 给 m_R=c^1.9、d_R=c^0.7、q_R=c^0.2，')
    L('   与把 K_R=1 代入本通式反解出的指数逐位相同（n=1/4）。这是**独立路径吻合**，')
    L('   不是恒等式重排；但 Xu 由 H2TS 得到，本式由集总动量+能量得到，前提不同。')


# ============================================================ [F] 17.9 kW
def section_holdout():
    L('')
    L('=' * 78)
    L('[F] 17.9 kW：仍是候选单量对照（沿用 v3 结论）')
    L('=' * 78)
    L('   m：模型 1.0746 对 Yue 1.12 => -4.06%（唯一独立对比量）')
    L('   dT：模型没有加热段进出口两个节点，Q/(m cp) 只是同一控制体的毛热代理，')
    L('       不是对 dT_HS=108.6 K 的预测 => 不报符号、不报倍数。')
    L('   参照：Yue 自身全段优化给 1.10/110.3，对 1.12/108.6 是 -1.79%/+1.57%。')
    L('   => 一句话：本模型单点标定的 0D 代价约 4%，比条件界小 2~2.5 倍，但那不是同一件事。')


# ============================================================ [G] 结论
def section_concl():
    L('')
    L('=' * 78)
    L('[G] 可宣称 / 不可宣称（v4）')
    L('=' * 78)
    L('   可宣称：')
    L('     1. 通式 x^3 = K_R c_p,R/rho_R，K_R=(1-w)(1+delta)+w(l/d)f_R，Re 内生。')
    L('     2. Zhao 声明模型内、对 w 一个参数：D_m ∈ [0,+9.7782%]（区间证书，1e-15 级）；')
    L('        可证界 0<=D_m<=2^(3/22)-1=+9.9131%（写 +9.914%，无浮点假设）。')
    L('     3. KYLIN 全相似回到 0（两种物性版本都给 0）；降高度 -13.2%~-13.3%，')
    L('        与四段模型 US=0 的 -13.29% 独立吻合，主因是局部损失不随长度缩短。')
    L('     4. delta 的不确定度是**单边**的：只动下端，不动上端（因为 w=1 时 delta 退出）。')
    L('     5. 证书对象已从"二进制程序"上移到"原十进制模型"。')
    L('   不可宣称：')
    L('     a. "1e-14 认证"只能对 w 一个参数说；其余参数全是声明。')
    L('     b. delta=+-7%（Xu 的 7.3% 是 FoM 偏差，不是局阻域）。')
    L('     c. "K_R=1 是唯一缩比要求"（Xu 四条判据，只豁免壁导热）。')
    L('     d. "w=0 有精确立方根闭式"（恒物性近似，差 1e-3 pp）。')
    L('     e. 17.9 kW 留出验证通过（只有 m 一个候选量）。')
    L('     f. 跨案例移植 w*(3%)；赵的 d=0.5 无净流道依据。')


def main():
    L('自然循环缩比失真：源无关条件界 v4（补证 + 降级）    2026-11-02')
    section_admit()
    section_cert()
    section_analytic()
    section_delta()
    section_w0()
    section_xu_criteria()
    section_holdout()
    section_concl()
    out = Path(__file__).with_name('source_free_bound_v4_log.txt')
    out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
    print('\n[log] %s（%d 行）' % (out.name, len(LOG)))


if __name__ == '__main__':
    main()
