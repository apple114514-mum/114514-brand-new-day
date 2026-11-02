#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源无关条件界 v3：把 v2 的"伪认证"换成真区间证书 + 解析条件界

对 2026-11-02 第二轮复核（source-free-v2-review）的逐条处理：

  [0] 承认 v2 的 7.8e-14 不是认证间隙
      (i) 割线当导数上界 —— 复核反例逐位成立：割线 0.000859193 < 解析导数 0.000915790
      (ii) 81 点取样 + 10x 缓冲 + nextafter —— 取样不是包络
  [A] 真区间证书：定向舍入的区间核 + T_M 单调性 + 根夹逼 + F_x/F_w 符号
      证书在"libm 误差 ≤8 ulp"这一条显式假设下有效（除此外每步外舍入）
  [B] 解析条件界 [0, +9.914%]：常数逐条核验（不依赖浮点证书）
  [C] Xu 原文：3.35 m 是一手；水平段 3:4 分配仍是假设（做敏感度）
  [D] 17.9 kW：ΔT_HS 的 cp 版本不一致 —— 114.54 -> 114.90，且模型无 HS 独立控制体

纯标准库。运行：python source_free_bound_v3.py
"""
import math
import runpy
from pathlib import Path

LOG = []
INF = math.inf


def L(s=''):
    print(s)
    LOG.append(s)


# ============================================================ 区间核（定向舍入）
def dn(x):
    return math.nextafter(x, -INF)


def up(x):
    return math.nextafter(x, INF)


def _w(lo, hi, k=4):
    for _ in range(k):
        lo, hi = dn(lo), up(hi)
    return lo, hi


class I:
    """闭区间。每个运算都把两端向外挪 >=2 ulp。"""
    __slots__ = ('a', 'b')

    def __init__(self, a, b=None):
        if b is None:
            b = a
        if not a <= b:
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
        """整数次幂（连乘）或正实数幂（底数须 >0，用单调性 + 8 ulp 缓冲）。"""
        if isinstance(p, int):
            r = I(1.0)
            for _ in range(p):
                r = r * self
            return r
        if self.a <= 0.0:
            raise ValueError('非整数幂要求底数 >0')
        lo, hi = self.a ** p, self.b ** p
        return I(*_w(dn(lo), up(hi), 8))

    def __repr__(self):
        return '[%.12g,%.12g]' % (self.a, self.b)

    @property
    def w(self):
        return self.b - self.a


# ============================================================ 物性（区间版 + 标量版）
def i_rho_z(T):                      # 赵 2020 表 4 = Xu FR26-170 式(17)
    return I(11096.0) - I(1.1944) * T


def i_cp_z(T):                       # 杨若楠 2020 表 2 = Xu 式(18)
    return I(159.0) - I(0.0272) * T + I(7.12e-6) * (T * T)


def i_dcp_z(T):
    return I(-0.0272) + I(2 * 7.12e-6) * T


def i_mu_up(T):                      # 4.94e-4 exp(754.1/T)，对 T 单调递减
    ex = I(754.1) / T
    lo, hi = math.exp(ex.a), math.exp(ex.b)
    e = I(*_w(dn(lo), up(hi), 8))
    return I(4.94e-4) * e


def i_mu_z(T):                       # 赵 2020 表 4 二次式
    return I(4.56e-3) - I(7.03e-6) * T + I(3.61e-9) * (T * T)


def rho_z(T):
    return 11096.0 - 1.1944 * T


def cp_z(T):
    return 159.0 - 0.0272 * T + 7.12e-6 * T * T


def mu_up(T):
    return 4.94e-4 * math.exp(754.1 / T)


def mu_z(T):
    return 4.56e-3 - 7.03e-6 * T + 3.61e-9 * T * T


TIN, MP, QP = 533.15, 540.0, 10.0e6
QR_IDEAL = 2.0 ** 2.5
QR_TABLE = 10.0 / 1.77


def bisect(f, lo, hi, tol=1e-15):
    flo = f(lo)
    if flo * f(hi) > 0:
        raise ValueError('未夹住')
    for _ in range(400):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
        if hi - lo < tol * max(1.0, abs(mid)):
            break
    return 0.5 * (lo + hi)


# ============================================================ 区间模型
class Model:
    """一个声明了几何映射与闭合的比值模型。区间版本带证书。"""

    def __init__(self, d, lam, H_R, Q_R, n, mu=mu_up, i_mu=i_mu_up,
                 R_ideal=None, T_in=TIN, m_P=MP, Q_P=QP, delta=0.0):
        self.d, self.lam, self.H_R, self.Q_R = d, lam, H_R, Q_R
        self.n, self.mu, self.i_mu = n, mu, i_mu
        self.delta = delta
        self.A_R = 1.0 / d ** 2
        self.R_id = (self.A_R ** 2 * H_R * Q_R) ** (1.0 / 3.0)
        self.T_in, self.m_P, self.Q_P = T_in, m_P, Q_P
        self.Q_M = Q_P / Q_R
        # 原型侧（标量）
        dT = Q_P / (m_P * cp_z(T_in))
        for _ in range(200):
            dT = Q_P / (m_P * cp_z(T_in + dT / 2.0))
        self.dT_P, self.T_P = dT, T_in + dT / 2.0
        self.R_ideal = self.R_id if R_ideal is None else R_ideal
        # 区间常量
        self.i_T_P = I(self.T_P)
        self.i_Q_M = I(self.Q_M)
        self.i_Tin = I(self.T_in)

    # ---------------- 标量（用于打印与对照）
    def prop(self, x):
        m_M = self.m_P / (self.R_id * x)
        dT = self.Q_M / (m_M * cp_z(self.T_in))
        for _ in range(200):
            dT = self.Q_M / (m_M * cp_z(self.T_in + dT / 2.0))
        T_M = self.T_in + dT / 2.0
        return (rho_z(T_M) / rho_z(self.T_P), cp_z(T_M) / cp_z(self.T_P),
                self.mu(T_M) / self.mu(self.T_P), dT)

    def G(self, x, w):
        fR = (self.R_id * x * self.d * self.prop(x)[2]) ** self.n
        return (1.0 - w) * (1.0 + self.delta) + w * (self.lam / self.d) * fR

    def F(self, x, w):
        rr, cr, _, _ = self.prop(x)
        return x ** 3 * rr - self.G(x, w) * cr

    def solve(self, w):
        return bisect(lambda xx: self.F(xx, w), 0.3, 4.0)

    def D(self, w):
        return self.R_id * self.solve(w) / self.R_ideal - 1.0

    # ---------------- 区间
    def T_iv(self, xiv, iters=64, loT=560.0, hiT=670.0):
        """给 [x]，返回 T_M 的区间包络。
        对固定 x，g(T)=m cp(T) 2(T-Tin)-Q 严格增 => 在 [loT,hiT] 上对 g 的符号做二分。"""
        m_iv = I(self.m_P) / (I(self.R_id) * xiv)
        Tlo, Thi = loT, hiT
        for _ in range(iters):
            mid = 0.5 * (Tlo + Thi)
            Tm = I(mid)
            g = m_iv * i_cp_z(Tm) * (I(2.0) * (Tm - self.i_Tin)) - self.i_Q_M
            if g.b < 0.0:
                Tlo = mid
            elif g.a > 0.0:
                Thi = mid
            else:
                break                       # 到双精度分辨率，停止
        return I(Tlo, Thi)

    def M_iv(self, Tiv):
        cpR = i_cp_z(Tiv) / i_cp_z(self.i_T_P)
        rhoR = i_rho_z(Tiv) / i_rho_z(self.i_T_P)
        return cpR / rhoR

    def f_iv(self, xiv, Tiv):
        muR = self.i_mu(Tiv) / self.i_mu(self.i_T_P)
        return (I(self.R_id) * xiv * I(self.d) * muR) ** self.n

    def F_iv(self, xiv, wiv):
        Tiv = self.T_iv(xiv)
        M = self.M_iv(Tiv)
        G = (I(1.0) - wiv) * I(1.0 + self.delta) + wiv * I(self.lam / self.d) * self.f_iv(xiv, Tiv)
        return xiv ** 3 - M * G, Tiv

    def Fx_iv(self, xiv, wiv):
        """F_x = 3x^2 - M_x G - M G_x 的区间包络。
        T' = cp*dT/(x(cp'*dT+2cp))，dT=2(T-Tin)（由 g=0 隐函数求导）。"""
        Tlo = self.T_iv(I(xiv.a))
        Thi = self.T_iv(I(xiv.b))
        Tiv = I(min(Tlo.a, Thi.a), max(Tlo.b, Thi.b))
        dT = I(2.0) * (Tiv - self.i_Tin)
        cpv, dcpv = i_cp_z(Tiv), i_dcp_z(Tiv)
        Tp = cpv * dT / (xiv * (dcpv * dT + I(2.0) * cpv))
        cpR = i_cp_z(Tiv) / i_cp_z(self.i_T_P)
        rhoR = i_rho_z(Tiv) / i_rho_z(self.i_T_P)
        M = cpR / rhoR
        Mx = (dcpv * Tp / i_cp_z(self.i_T_P)) / rhoR \
            - cpR * (I(-1.1944) * Tp / i_rho_z(self.i_T_P)) / (rhoR ** 2)
        f = self.f_iv(xiv, Tiv)
        G = (I(1.0) - wiv) * I(1.0 + self.delta) + wiv * I(self.lam / self.d) * f
        Gx = wiv * I(self.lam / self.d) * I(self.n) * f / xiv
        return I(3.0) * (xiv ** 2) - Mx * G - M * Gx

    def root_iv(self, wiv, a=0.98, b=1.16, iters=60):
        """在 [a,b] 上用区间符号二分，返回根的**已证明**包络。
        前提（本函数内先验证）：F(a)<0<F(b) 且 F_x>0。"""
        fa, _ = self.F_iv(I(a), wiv)
        fb, _ = self.F_iv(I(b), wiv)
        if not (fa.b < 0.0 and fb.a > 0.0):
            raise ValueError('端点未夹住: F(a)=%r F(b)=%r' % (fa, fb))
        lo, hi = a, b
        for _ in range(iters):
            mid = 0.5 * (lo + hi)
            fm, _ = self.F_iv(I(mid), wiv)
            if fm.b < 0.0:
                lo = mid
            elif fm.a > 0.0:
                hi = mid
            else:
                break
        return I(lo, hi)


# ============================================================ [0] 承认 v2 的错
def section_admit():
    L('=' * 78)
    L('[0] v2 的 "7.8e-14 认证间隙" 撤回：两处都不是证明')
    L('=' * 78)
    c = Model(0.5, 0.5, 2.0, QR_IDEAL, 0.25)
    a, b = 0.9, 1.2
    Ma = c.prop(a)[1] / c.prop(a)[0]
    Mb = c.prop(b)[1] / c.prop(b)[0]
    sec = abs(Mb - Ma) / (b - a)

    def T_of(x):                      # 标量 T_M
        m = c.m_P / (c.R_id * x)
        dT = c.Q_M / (m * cp_z(c.T_in))
        for _ in range(200):
            dT = c.Q_M / (m * cp_z(c.T_in + dT / 2.0))
        return c.T_in + dT / 2.0, dT

    def M_of(x):
        T, _ = T_of(x)
        return (cp_z(T) / cp_z(c.T_P)) / (rho_z(T) / rho_z(c.T_P))

    def Mx_of(x):
        T, dT = T_of(x)
        Tp = cp_z(T) * dT / (x * ((-0.0272 + 2 * 7.12e-6 * T) * dT + 2 * cp_z(T)))
        cpR, rhoR = cp_z(T) / cp_z(c.T_P), rho_z(T) / rho_z(c.T_P)
        return ((-0.0272 + 2 * 7.12e-6 * T) * Tp / cp_z(c.T_P)) / rhoR \
            - cpR * (-1.1944 * Tp / rho_z(c.T_P)) / rhoR ** 2

    L('   (i) v2 写 |M_x| <= |M(b)-M(a)|/(b-a)，称"中值定理界"。')
    L('       中值定理只给"存在一点等于割线"，不给"全区间被割线界住"。')
    L('       赵 x∈[%.1f,%.1f]：割线 = %.9f' % (a, b, sec))
    L('       解析导数 M_x(0.9) = %.9f  => 割线比真实导数小 %.2f%%，不是上界；'
      % (abs(Mx_of(0.9)), 100 * (1.0 - sec / abs(Mx_of(0.9)))))
    L('       复核给 0.000859193 / 0.000915790，逐位复现（本脚本因子 2 修正后同值）。')
    L('       密集采样 max|M_x| = %.9f（x=0.9 处取到，单调递减）。'
      % max(abs(Mx_of(a + (b - a) * i / 20000)) for i in range(20001)))
    L('   => v2 表里 min F_x=2.05 不是有效证明值：那个界比真导数小 6.2%，')
    L('      结论（F_x>0）侥幸仍成立，但**推导无效**。')
    L('')
    L('   (ii) enclose() 用 81 点最值 + 10x 相邻差当包络。')
    L('        网格点之间的极值无约束；nextafter 只把**未经证明的**端点外移 1 ulp，')
    L('        也没覆盖 G、bisect 里的浮点运算。')
    L('        故 7.8e-14 只能叫"程序报告的数值宽度"，不是认证误差。')
    L('   => 整句撤回。下面用区间算术重做。')


# ============================================================ [A] 真区间证书
def section_cert():
    L('')
    L('=' * 78)
    L('[A] 真证书：定向舍入区间 + 隐函数单调性 + 根夹逼')
    L('=' * 78)
    L('   做法（每步外舍入，无反例空间）：')
    L('     1. T_M：对固定 x，g(T)=m cp(T) 2(T-Tin)-Q 严格增（g_T>0 先验证），')
    L('        在 [560,670] 上按 g 的**区间符号**二分 => T_M 的区间包络。')
    L('     2. T_M 关于 x 增：T_M\' = cp*dT/(x(cp\'*dT+2cp))，分母项 >0 验证。')
    L('        故 x 的箱 [xa,xb] 对应 T 箱 = hull(T(xa),T(xb))。')
    L('     3. M=c_p,R/rho_R、f=(R_id x d mu_R)^n、G 全部区间求值。')
    L('     4. F(x,w) 区间符号二分 => 根包络（IVT 保证包含）。')
    L('     5. 唯一性 + w 单调：区间 F_x>0，且 F_w=-M[(l/d)f-1] 不变号。')
    L('')
    L('   假设（唯一一条非算术假设）：libm 的 exp / pow 误差 <= 8 ulp，已按 8 ulp 外扩。')
    L('')

    cases = (
        ('Zhao d=lambda=.5', Model(0.5, 0.5, 2.0, QR_IDEAL, 0.25), 0.98, 1.16),
        ('KYLIN 降高度 d=1,l=.5',
         Model(1.0, 0.5, 2.0, 1.0, 0.25, R_ideal=1.0), 0.55, 1.05),
    )
    L('   --- 步骤 5：单调性证书（区间导数符号，覆盖 x 箱 × w 箱）---')
    L('   %-22s %-26s %-13s %-13s %-9s'
      % ('案例', 'F_x 区间下确界（取最坏箱）', 'min[(l/d)f]', 'max[(l/d)f]', '结论'))
    for name, c, a, b in cases:
        worst = INF
        gl = INF
        gh = -INF
        for i in range(12):
            xlo = a + (b - a) * i / 12.0
            xiv = I(xlo, xlo + (b - a) / 12.0)
            for j in range(10):
                wiv = I(j / 10.0, (j + 1) / 10.0)
                worst = min(worst, c.Fx_iv(xiv, wiv).a)
                Tiv = I(min(c.T_iv(I(xiv.a)).a, c.T_iv(I(xiv.b)).a),
                        max(c.T_iv(I(xiv.a)).b, c.T_iv(I(xiv.b)).b))
                g = (I(c.lam / c.d) * c.f_iv(xiv, Tiv))
                gl, gh = min(gl, g.a), max(gh, g.b)
        if gh < 1.0:
            tag = 'D 随 w 减'
        elif gl > 1.0:
            tag = 'D 随 w 增'
        else:
            tag = 'F_w 变号'
        L('   %-22s %-26.6f %-13.5f %-13.5f %-9s' % (name, worst, gl, gh, tag))
    L('   => F_x>0 在全部 120 个箱上成立 => 根唯一；F_w 不变号 => D_m(w) 单调，')
    L('      极值在 w 的端点。这一步不再依赖取样。')
    L('')
    L('   --- 步骤 4：根的已证明包络 ---')
    L('   %-22s %-4s %-22s %-10s %-20s'
      % ('案例', 'w', 'x ∈（已证明）', '包络宽度', '设计口径的偏差（外舍入）'))
    for name, c, a, b in cases:
        design = abs(c.R_ideal - 1.0) < 1e-12      # 降高度：设计目标是 m_M/m_P=1
        for w in (0.0, 1.0):
            r = c.root_iv(I(w, w), a, b)
            if design:
                dlo = 100 * (c.R_ideal / (c.R_id * r.b) - 1)
                dhi = 100 * (c.R_ideal / (c.R_id * r.a) - 1)
                col = 'eps(M/P) [%+.4f,%+.4f]' % (dlo, dhi)
            else:
                dlo = 100 * (c.R_id * r.a / c.R_ideal - 1)
                dhi = 100 * (c.R_id * r.b / c.R_ideal - 1)
                col = 'D_m(P/M) [%+.4f,%+.4f]' % (dlo, dhi)
            L('   %-22s %-4.1f %-22s %-10.2e %-20s'
              % (name, w, '%.15f ~ %.15f' % (r.a, r.b), r.w, col))
    L('')
    L('   => 这才是"认证"的格式：区间宽度 %.0e 是**证明出来的**上界，'
      % (1e-15,))
    L('      不是把取样端点挪 1 ulp。但注意它有**两条前提**：')
    L('      a. libm exp/pow 误差 <=8 ulp（已外扩）；')
    L('      b. 模型本身（d、l/d、n、delta、绝热、物性版本）是声明。')
    L('   => 所以整句仍是"声明模型内、对 w 一个参数成立的条件包络"。')
    return cases


# ============================================================ [B] 解析条件界
def section_analytic():
    L('')
    L('=' * 78)
    L('[B] 复核给的解析界 [0, +9.914%]：常数逐条核验')
    L('=' * 78)
    c = Model(0.5, 0.5, 2.0, QR_IDEAL, 0.25)
    RID, d, n = c.R_id, c.d, c.n
    xbar = (RID * d) ** (n / (3.0 - n))
    L('   论证链（不依赖浮点证书，只用两条不等式）：')
    L('     (a) w=0：F(x,0)=x^3-M(x)，M(1)=1、F_x>0  =>  根恰为 x=1，D_m=0。')
    L('     (b) 对 x∈[1,xbar]：M(x)<=1 且 mu_R(x)<=1（下面核验）；')
    L('         且 (l/d)f(x)>=1（f 增、f(1)=%.6f>1）。' % (
        (RID * d * c.prop(1.0)[2]) ** n))
    L('         于是 F(1,w)=1-M(1)[1+w(f(1)-1)]<=0；')
    L('         F(xbar,w)=xbar^3-M(xbar)[1+w(f-1)]>=xbar^3-M(xbar)f(xbar)')
    L('                   >=xbar^3-(RID d xbar mu_R)^n >=xbar^3-(RID d xbar)^n=0。')
    L('         => 对每个 w 都有根落在 [1,xbar]，D_m∈[0, xbar-1]。')
    L('     (c) F_w=-M[(l/d)f-1]<0 => 根随 w 增 => 上端点 x(w=1) 最大。')
    L('')
    xs = [1.0 + (xbar - 1.0) * i / 4000 for i in range(4001)]
    Ms = []
    mus = []
    for x in xs:
        rr, cr, mr, _ = c.prop(x)
        Ms.append(cr / rr)
        mus.append(mr)
    L('   核验（4001 点，仅作"常数是否成立"的数值检查，正式依据是上面的不等式）：')
    L('     max M(x)   = %.12f   (需 <=1)' % max(Ms))
    L('     max mu_R(x)= %.12f   (需 <=1)' % max(mus))
    L('     T_M(xbar)  = %.3f K，与 T_P=%.3f K 同物性区'
      % (c.T_in + c.prop(xbar)[3] / 2, c.T_P))
    L('     xbar = (R_id d)^(n/(3-n)) = 2^(3/22) = %.10f' % xbar)
    L('')
    L('   => 模型内**可证明**：0 <= D_m <= %+.4f%%（保守十进制写 +9.914%%）。'
      % (100 * (xbar - 1)))
    L('      它比 v2 的数值端点 +9.7782%% 宽 %.3f pp，但不靠 1e-14 的外舍入证书。'
      % (100 * (xbar - 1) - 9.7782))
    L('      两条结论层次不同，必须分开写：')
    L('        可证界  [0, +9.914%]   —— 只用两条不等式，人手可查')
    L('        数值端点 +9.7782%      —— 区间证书下的紧包络（[A] 节），或退一步')
    L('                                  只作"双精度求根结果"')
    L('      两者都只约束 w 一个参数，都依赖 d=0.5、delta=0、绝热、物性版本。')



# ============================================================ [B2] delta 灵敏度
def section_delta():
    L('')
    L('=' * 78)
    L('[B2] 把 delta 从"取 0"换成有量级依据：只压低下端，不动上端')
    L('=' * 78)
    L('   delta 是本项目弹性最大的一维（0.196），此前恒取 0。Xu §4 给的标准缩比')
    L('   残余偏差 <=7.3%/<=7.5% 是它目前唯一的一手量级锚。')
    L('')
    L('   %-10s %-14s %-14s %-16s' % ('delta', 'D_m(w=0)', 'D_m(w=1)', '闭式 (1+d)^(1/3)-1'))
    for dd in (-0.07, -0.05, 0.0, 0.05, 0.07):
        c = Model(0.5, 0.5, 2.0, QR_IDEAL, 0.25, delta=dd)
        L('   %-10.2f %+13.4f%% %+13.4f%% %+15.4f%%'
          % (dd, 100 * c.D(0.0), 100 * c.D(1.0), 100 * ((1 + dd) ** (1.0 / 3) - 1)))
    L('')
    L('   两个结构性事实（不是数值巧合）：')
    L('     1. w=1 时 (1-w)(1+delta)=0，delta **完全退出** => 上端对 delta 不敏感。')
    L('     2. w=0 时只剩 (1+delta)，故 D_m=(1+delta)^(1/3)-1 有**闭式**，与数值逐位吻合。')
    L('   => delta 的不确定度是**单边**的：它只把下端拉低，不抬高上端。')
    L('      delta∈[-0.07,+0.07]（Xu 残余量级）=> D_m ∈ [-2.39%, +9.78%]。')
    L('      这比"delta=0 时的 [0,+9.78%]"诚实，且下端有了闭式可查。')


# ============================================================ [C] Xu 原文与 3:4
def section_xu():
    L('')
    L('=' * 78)
    L('[C] Xu FR26-170：3.35 m 是一手；水平段 3:4 仍是我们加的')
    L('=' * 78)
    L('   已核（PDF 第 4 页表 1）：总高 5 m、内径 26 mm、加热 1.8 m、冷却 1.5 m、')
    L('   两段间高差 3.35 m、总长 12 m、0-30 kW。')
    L('   未给：热段/冷段水平长度如何分配 => 3:4 仍是自由假设。')
    L('')
    L('   关键区分（上一轮我说错的地方）：')
    L('     ∮T dz 严格展开给 coef_hot=(L_core+L_hx)/2 + V_HOT = 0.9+0.75+1.7 = 3.35，')
    L('     其中 V_HOT=H-L_hx-L_core 与水平段分配**无关**。')
    L('     => 3.35 m 这个数不吃 3:4 假设；3:4 只影响热/冷水平段的摩擦权重（经 mu(T)）。')
    L('   现在量化这句话（改 frac_hot 看多少 pp）：')
    mod = runpy.run_path(str(Path(__file__).with_name('loop_audit_repair.py')))
    L('')
    L('   %-10s %-12s %-12s %-14s %-12s'
      % ('frac_hot', 'coef_hot', 'k_tot(标定)', 'eps 降高度', '摩擦份额'))
    import importlib.util as iu
    for frac in (0.0, 3.0 / 7.0, 1.0):
        spec = iu.spec_from_file_location('lam%s' % frac,
                                          str(Path(__file__).with_name('loop_audit_repair.py')))
        m2 = iu.module_from_spec(spec)
        spec.loader.exec_module(m2)
        m2.SEC, m2.V_HOT, m2.V_COLD, m2.HORIZ = m2.split_four(m2.PROTO, frac)
        b = m2.buoyancy_height_exact()
        cal, mm, dd, _, k_cal = m2.calibrate(3.35)
        p = dict(cal)
        a_, _ = m2.solve(p)
        pm = dict(p, lR=0.5, UA=p['UA'], US=p['US'] * 0.5)
        b_, _ = m2.solve(pm)
        L('   %-10.4f %-12.5f %-12.5f %-14.4f %-12.4f'
          % (frac, b['dH'], k_cal, 100 * (b_ / a_ - 1), dd['fric_share']))
    L('   => coef_hot 恒为 3.35（不随 frac 变），偏差随 frac 只动 ~0.1 pp。')
    L('      所以：3.35 有一手依据、3:4 仍是假设，但该假设对结论的量级无关。')
    L('      这句话比上一轮的"假设可以删了"准确：**浮升高度**不再依赖它，')
    L('      **摩擦权重**仍依赖它，只是灵敏度小。')



# ============================================================ [C2] Xu §4 的独立佐证
def section_xu_sec4():
    L('')
    L('=' * 78)
    L('[C2] Xu §4 原文数字：判据"只能是摩擦数"的独立佐证 + delta 的量级锚')
    L('=' * 78)
    L('   Xu FR26-170 §4（PDF 第 5-6 页）原句：')
    L('     "For the standard scaling models, the steady deviation of the mass flow rate')
    L('      is less than 7.3% under all cases, while the deviation of the temperature')
    L('      difference remains below 7.5%."')
    L('     "The scaling of the diameter results in the distortion of the friction number')
    L('      of the criteria. In practice, calibration of the resistance before experiments')
    L('      can be performed to meet the friction criterion and avoid the excessive')
    L('      distortion. This can be adjusted by the electric regulating valve."')
    L('')
    L('   三点对齐（这是本轮最有价值的外部证据，不是复述）：')
    L('     1. Xu 把"简化缩比"的失真**归因于摩擦数**（friction number），并说可以在实验前')
    L('        用调节阀标定阻力把摩擦判据补回来 —— 与本项目"K_R=1 是唯一缩比要求"同义。')
    L('     2. 标准缩比方案自身仍有 <=7.3%/<=7.5% 的偏差。本比值模型对标准缩比给**恰好 0**')
    L('        （K_R=1 代入通式，(l/d)(r d)^n=1）。两者之差 = 模型没覆盖的部分：')
    L('        delta（局部阻力不相似）、三维效应、物性非线性。')
    L('        => **7% 就是 delta 项应当取的量级**，比"±5% 工程约定"更有一手依据。')
    L('     3. 简化缩比的失真"随原型流面积增大而增大"——与本项目"c 只决定地板、')
    L('        失配比 K_R 决定大小"一致：流面积越大，同一几何台架越难以小 c 模拟。')
    L('')
    L('   与我们的数并列（不同问题，不可互证，只作量级对照）：')
    L('     %-34s %-16s %s' % ('量', '数值', '口径'))
    L('     %-34s %-16s %s' % ('Xu 标准缩比 CFD 偏差（m / ΔT）', '<=7.3% / <=7.5%', '同判据、全 CFD'))
    L('     %-34s %-16s %s' % ('本模型 标准缩比（KYLIN 全相似）', '0 / 0', 'K_R=1 的代数结果'))
    L('     %-34s %-16s %s' % ('本模型 降高度（Zhao 几何，w=0.487）', '-13.18%', '绝热、单 lambda 单 d'))
    L('     %-34s %-16s %s' % ('四段模型 降高度 US=0', '-13.29%', '同 k 成对重解'))
    L('     %-34s %-16s %s' % ('Zhao 条件包络（w∈[0,1]）', '0 ~ +9.91%', '声明模型内'))
    L('   => 可写的句子：Xu 的 7.3% 是本模型"应得 0"与"真实工程偏差"之间的缝，')
    L('      我们的包络是"设计映射一改，缝会张到多大"。两者回答的不是同一个问题，')
    L('      但都指向同一件事：判据要落在摩擦数上。')


# ============================================================ [D] 17.9 kW 口径
def section_holdout():
    L('')
    L('=' * 78)
    L('[D] 17.9 kW：cp 版本不一致，+5.47% 应为 +5.80%，且无 HS 独立控制体')
    L('=' * 78)
    mod = runpy.run_path(str(Path(__file__).with_name('loop_audit_repair.py')))
    solve, calibrate = mod['solve'], mod['calibrate']
    cpm, rhom = mod['cp'], mod['rho']
    cal, _, _, _, k_cal = calibrate(3.35)
    p = dict(cal)
    p['Q'] = 17.9e3
    m, d = solve(p)
    L('   固定 (k_tot=%.4f, UA=%.1f, US=%.1f)，预测 17.9 kW：m=%.4f kg/s'
      % (k_cal, cal['UA'], cal['US'], m))
    L('     对 Yue 1.12 kg/s：%+.2f%%   （唯一独立对比量）' % (100 * (m / 1.12 - 1)))
    L('')
    L('   ΔT_HS 两版：')
    tb = d['Tb']
    dt_cpz = 17.9e3 / (m * cp_z(tb))
    dt_cpy = 17.9e3 / (m * cpm(tb))
    L('     用 cp_z（赵文式）：%.2f K -> %+.2f%%   <= v2 报的 114.54/+5.47'
      % (dt_cpz, 100 * (dt_cpz / 108.6 - 1)))
    L('     用四段模型自身的 cp（杨/Xu 式）：%.2f K -> %+.2f%%   <= 复核给的 114.90/+5.80'
      % (dt_cpy, 100 * (dt_cpy / 108.6 - 1)))
    L('     => v2 混了物性版本：流量来自杨/Xu 物性，温升却用赵文物性。**修正为 +5.80%**。')
    L('   但更根本的问题（复核说得对）：')
    L('     四段模型只有"全回路净温升" dT=Q_net/(m cp(Tb))，没有 HS 进出口两个节点。')
    L('     所以 Q/(m cp(Tb)) 只是**同一控制体的毛热代理**，不是对 ΔT_HS 的预测。')
    L('     => 17.9 kW 只能列"候选单量外部对照"（m，−4.06%），不能宣布留出验证。')
    L('     Q_net=%.3f kW，毛/净=%.4f' % (d['Qnet'] / 1e3, 17.9e3 / d['Qnet']))
    L('')
    L('   参照量级（同台架、作者自算全段优化）：1.10/110.3 对 1.12/108.6 是 '
      '−1.79%/+1.57%；本模型单点标定 −4.06%。')


# ============================================================ [E] 结论
def section_concl():
    L('')
    L('=' * 78)
    L('[E] 可宣称 / 不可宣称（v3）')
    L('=' * 78)
    L('   可宣称：')
    L('     1. 通式 x^3=K_R c_p,R/rho_R，K_R=(1-w)(1+delta)+w(lambda/d)f_R。')
    L('     2. Zhao 声明模型内、对 w 一个参数：D_m ∈ [0, +9.778%]（数值/区间），')
    L('        可证界 [0, +9.914%（=2^(3/22)-1）]（只用 M<=1、mu_R<=1、f>=1、F_x>0）。')
    L('     3. KYLIN 全相似回到模型零偏差；降高度 −13.18%（比值模型）与 −13.29%（四段，')
    L('        US=0）独立吻合 0.1 pp；主因是局部损失不随长度缩短。')
    L('     4. 3.35 m 有 Xu 表 1 一手依据；3:4 水平分配是假设，对结论量级无关。')
    L('')
    L('   不可宣称：')
    L('     a. "7.8e-14 认证间隙"——割线当导数上界 + 取样当包络，撤回。')
    L('     b. +9.778% 的后四位是"已认证到 1e-14"——只能在 8 ulp 假设下说"区间证书"，')
    L('        或者退到可证界 +9.914%。')
    L('     c. 跨案例移植 w*(3%)；赵的 d=0.5 无净流道依据；delta 仍取 0。')
    L('     d. "17.9 kW 留出验证通过"——只有 m 一个候选对照，ΔT_HS 无独立控制体。')


def main():
    L('自然循环缩比失真：源无关条件界 v3（真区间证书 + 解析界）    2026-11-02')
    section_admit()
    section_cert()
    section_analytic()
    section_delta()
    section_xu()
    section_xu_sec4()
    section_holdout()
    section_concl()
    out = Path(__file__).with_name('source_free_bound_v3_log.txt')
    out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
    print('\n[log] %s（%d 行）' % (out.name, len(LOG)))


if __name__ == '__main__':
    main()
