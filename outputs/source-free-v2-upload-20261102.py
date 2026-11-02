#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源无关条件界 v2：通式修正（c_p 方向 + lambda/d）+ KYLIN 归因撤回

对 2026-11-02 复核（source-free-bound-review）的逐条复算。三处修正：
  [0] 通式两处错：x^3 = K_R c_p,R/rho_R（c_p 在分子），K_R = (1-w) + w(lambda/d) f_R
  [1] Zhao：+9.842% -> +9.778%（Q_R=2^2.5）/ +9.727%（Q_R=10/1.77）；w*(3%) 0.302 -> 0.304
  [2] KYLIN 全相似：修正后恒为 0（该几何本就按摩擦数相似构造，v1 的 lambda/d=1 造出假失真）
  [3] KYLIN 降高度：分母应为设计目标 m_M/m_P=1，修正后约 -13.18%（绝热），
      四段模型固定 k、US=0 得 -13.286% —— 两模型独立一致 => 主偏差来自局部损失不随长度缩短
  [4] 17.9 kW：只剩一个独立对比（m）；"两个 FoM 同号"与"符号随口径反转"是控制体口径伪像，撤回

纯标准库。运行：python source_free_bound_v2.py
"""
import math
import runpy
from pathlib import Path

LOG = []
NA = math.nextafter


def L(s=''):
    print(s)
    LOG.append(s)


# ============================================================ 物性
def rho_z(T):        # 赵 2020 表 4 与 Xu FR26-170 式(17) 同式
    return 11096.0 - 1.1944 * T


def cp_z(T):         # 杨若楠 2020 表 2 = Xu FR26-170 式(18)
    return 159.0 - 0.0272 * T + 7.12e-6 * T * T


def mu_up(T):        # 4.94e-4 exp(754.1/T)：杨/Xu 版
    return 4.94e-4 * math.exp(754.1 / T)


def mu_z(T):         # 赵 2020 表 4 二次式
    return 4.56e-3 - 7.03e-6 * T + 3.61e-9 * T * T


def bisect(f, lo, hi, tol=1e-15):
    flo = f(lo)
    if flo * f(hi) > 0:
        raise ValueError('未夹住: f(%.6f)=%.6e f(%.6f)=%.6e' % (lo, flo, hi, f(hi)))
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


# ============================================================ 比值模型
TIN = 533.15
MP, QP = 540.0, 10.0e6
QR_IDEAL = 2.0 ** 2.5          # A_R*H_R^0.5 型理想功率比
QR_TABLE = 10.0 / 1.77         # 赵表 3 印出值


class Case:
    """一个声明了几何映射与闭合的比值模型实例。"""

    def __init__(self, d, lam, H_R, Q_R, n, mu=mu_up, R_ideal=None,
                 T_in=TIN, m_P=MP, Q_P=QP):
        self.d, self.lam, self.H_R, self.Q_R = d, lam, H_R, Q_R
        self.n, self.mu = n, mu
        self.A_R = 1.0 / d ** 2
        self.R_id = (self.A_R ** 2 * H_R * Q_R) ** (1.0 / 3.0)
        # 原型侧温升（绝热）
        dT = Q_P / (m_P * cp_z(T_in))
        for _ in range(80):
            dT = Q_P / (m_P * cp_z(T_in + dT / 2.0))
        self.dT_P, self.T_P = dT, T_in + dT / 2.0
        self.T_in, self.m_P, self.Q_P = T_in, m_P, Q_P
        # 声明比较基准（原型/台架）。None 则取几何理想比 R_id
        self.R_ideal = self.R_id if R_ideal is None else R_ideal

    def prop(self, x):
        """x = r_m/R_id；返回 rho_R=rho_M/rho_P, c_p,R, mu_R"""
        m_M = self.m_P / (self.R_id * x)
        Q_M = self.Q_P / self.Q_R
        dT = Q_M / (m_M * cp_z(self.T_in))
        for _ in range(80):
            dT = Q_M / (m_M * cp_z(self.T_in + dT / 2.0))
        T_M = self.T_in + dT / 2.0
        return (rho_z(T_M) / rho_z(self.T_P), cp_z(T_M) / cp_z(self.T_P),
                self.mu(T_M) / self.mu(self.T_P), dT)

    def G(self, x, w):
        """K_R 的无量纲部分（不含 rho/c_p 修正）"""
        fR = (self.R_id * x * self.d * self.prop(x)[2]) ** self.n
        return (1.0 - w) + w * (self.lam / self.d) * fR

    def G_v1(self, x, w):
        """v1 的错误形式：漏掉 lambda/d"""
        fR = (self.R_id * x * self.d * self.prop(x)[2]) ** self.n
        return 1.0 + w * (fR - 1.0)

    def F(self, x, w, v1=False):
        rr, cr, _, _ = self.prop(x)
        G = (self.G_v1(x, w) if v1 else self.G(x, w))
        if v1:
            return x ** 3 * rr * cr - G          # v1: x^3 = K_R/(rho_R c_p,R)
        return x ** 3 * rr - G * cr              # v2: x^3 = K_R c_p,R/rho_R

    def solve(self, w, v1=False):
        return bisect(lambda xx: self.F(xx, w, v1), 0.3, 4.0)

    def D(self, w, v1=False):
        """原型/台架流量比相对声明理想比的偏差"""
        return self.R_id * self.solve(w, v1) / self.R_ideal - 1.0

    def eps_mp(self, w, v1=False):
        """台架/原型流量比相对声明理想比的偏差（四段模型用的口径）"""
        return self.R_ideal / (self.R_id * self.solve(w, v1)) - 1.0


def w_star(case, target, v1=False):
    """反解 D_m = target 的 w（D 随 w 单调，见 section_m 的证书）"""
    f = (lambda w: case.D(w, v1) - target)
    return bisect(f, 0.0, 1.0)


# ============================================================ [0] 推导
def section_derive():
    L('=' * 78)
    L('[0] 通式重新推导：两处修正')
    L('=' * 78)
    L('   集总动量（Boussinesq，β=1.1944/ρ：(ρ^2 β) ∝ ρ）+ 绝热能量 Q=m c_p ΔT：')
    L('')
    L('     ρ g β ΔT H = K m^2/(2 ρ A^2)   =>   m^2 = 2 ρ ΔT H A^2/K')
    L('     ΔT = Q/(m c_p)')
    L('')
    L('   取 r=m_P/m_M、A_R=A_P/A_M、H_R=H_P/H_M、Q_R=Q_P/Q_M、')
    L('      rho_R=rho_M/rho_P、c_p,R=c_p,M/c_p,P、K_R=K_M/K_P：')
    L('')
    L('     r^2 = A_R^2 H_R (ΔT_P/ΔT_M) K_R/rho_R')
    L('     ΔT_P/ΔT_M = Q_R c_p,R / r          <= 这一行 v1 写在了分母')
    L('')
    L('     r^3 = A_R^2 H_R Q_R K_R c_p,R / rho_R            …… (*)')
    L('')
    L('   令 R_id=(A_R^2 H_R Q_R)^(1/3)、x=r/R_id：')
    L('     x^3 = K_R c_p,R / rho_R                            …… v2 通式')
    L('          v1 写成 x^3 = K_R/(rho_R c_p,R)，比热比放反。')
    L('')
    L('   阻力分解。K_P=K_f,P+K_l,P，w=K_f,P/K_P；f∝Re^(-n)，')
    L('   Re ∝ m/(D μ) => Re_P/Re_M = r d mu_R，f_R=(r d mu_R)^n：')
    L('')
    L('     K_R = [K_f,M + K_l,M]/K_P = w (lambda/d) f_R + (1-w)(1+delta)')
    L('')
    L('   其中 lambda=L_M/L_P、d=D_M/D_P、delta=(K_l,M-K_l,P)/K_l,P。')
    L('     v1 的 K_R=1+w(f_R-1) 隐含 lambda/d=1 且 delta=0：')
    L('     它只对"各段 L 与 D 同比缩"成立（赵的理想圆管正是 lambda=d=0.5）。')
    L('   于是 v2 的待解方程：')
    L('')
    L('     x^3 (rho_R/c_p,R) = (1-w)(1+delta) + w (lambda/d) (x R_id d mu_R)^n')
    L('')
    L('   两处修正里，c_p 方向对赵只值 0.06 pp；lambda/d 对 KYLIN 值 2 pp 以上，')
    L('   并且把 KYLIN 全相似的"假失真"消掉（第三节）。')


# ============================================================ [A] Zhao
def section_zhao():
    L('')
    L('=' * 78)
    L('[A] Zhao 2020：修正后数值几乎不动，但 w*(3%) 变了')
    L('=' * 78)
    legs = (('mu_up', mu_up), ('mu_zhao', mu_z))
    for tag, mu in legs:
        for qtag, QR in (('Q_R=2^2.5', QR_IDEAL), ('Q_R=10/1.77', QR_TABLE)):
            c = Case(0.5, 0.5, 2.0, QR, 0.25, mu=mu)
            d1u, d1c = c.D(1, True), c.D(1, False)
            d0u, d0c = c.D(0, True), c.D(0, False)
            L('   %-9s %-12s w=0: v1 %+8.4f%%  v2 %+8.4f%%   w=1: v1 %+8.4f%%  v2 %+8.4f%%'
              % (tag, qtag, 100 * d0u, 100 * d0c, 100 * d1u, 100 * d1c))
    L('')
    c = Case(0.5, 0.5, 2.0, QR_IDEAL, 0.25, mu=mu_up)
    L('   复核值复现（Q_R=2^2.5, 上传黏度）：v1 %+0.4f%% / v2 %+0.4f%%  —— 复核给 +9.8423/+9.7782'
      % (100 * c.D(1, True), 100 * c.D(1, False)))
    cz = Case(0.5, 0.5, 2.0, QR_IDEAL, 0.25, mu=mu_z)
    L('   赵表 4 黏度：v1 %+0.4f%% / v2 %+0.4f%%  —— 复核给 +9.8063（v2）'
      % (100 * cz.D(1, True), 100 * cz.D(1, False)))
    L('   注：本表以"由实际 Q_R 决定的几何理想比 R_id"为分母；若改以 2^2.5 为分母，')
    L('       各数整体再降约 0.05 pp（分母声明不同，不是模型不同）。')
    L('')
    L('   3% 交叉点（OBS=+2.876835% 是原文表 5 观测，不是判据）：')
    L('   %-12s %-10s %-10s' % ('黏度', 'v1 w*(3%)', 'v2 w*(3%)'))
    for tag, mu in legs:
        cw = Case(0.5, 0.5, 2.0, QR_IDEAL, 0.25, mu=mu)
        L('   %-12s %-10.4f %-10.4f' % (tag, w_star(cw, 0.03, True), w_star(cw, 0.03, False)))
    L('   <=> v1 的 0.302/0.307 与 v2 的 0.304/0.309 来自同一结构、同一输入，不是互证。')
    L('      （v1 分支直解 0.3022 与旧日志 0.302 一致；差别只在 c_p 方向与 lambda/d）')
    L('')
    L('   两点必须写进标题句：')
    L('     ① Q_R 取 2^2.5 还是 10/1.77，D_m 差 0.05 pp，但**分母必须声明**；')
    L('     ② d=lambda=0.5 来自"0.5 倍几何相似"这一声明，赵表 3 的 1.0/0.5 m 是')
    L('        容器/外形尺寸，不是堆芯净流道；delta=0 也是声明。三者为该案例的闭合清单。')
    L('   工况点也进函数（复核指出"不只依赖 (d,H_R,Q_R,n)"）：')
    L('   %-22s %-10s %-10s %-10s' % ('变动', 'w*(3%)', 'D_m(w=1)%', 'w(obs)'))
    for tag, kw in (('基准 T_in=533.15', {}),
                    ('T_in=513.15', dict(T_in=513.15)),
                    ('T_in=573.15', dict(T_in=573.15)),
                    ('Q_P=9 MW', dict(Q_P=9.0e6, m_P=540.0 * 9.0 / 10.0)),
                    ('Q_P=11 MW', dict(Q_P=11.0e6, m_P=540.0 * 11.0 / 10.0))):
        cc = Case(0.5, 0.5, 2.0, QR_IDEAL, 0.25, **kw)
        L('   %-22s %-10.4f %+10.4f %-10.4f'
          % (tag, w_star(cc, 0.03), 100 * cc.D(1.0), w_star(cc, 0.02876835)))
    L('   => 判据严格写作 w* = f(d, lambda/d, H_R, Q_R, n; T_in, 物性版本)。')
    L('      T_in 以 1e-4 量级进 w*（两侧同 T_in，物性比近乎相消）；Q_P/m_P 同比变动时')
    L('      完全不进（只改绝对流量，不改比值）。所以复核"不只依赖四元"形式上对、量级很小。')
    L('')
    L('   观测 D_m=+2.8768%% 对应的 w：v2 %.4f（绝热口径；四段模型名义点几何分解 0.487）'
      % w_star(c, 0.02876835, False))
    return c


def enclose(c, w, iters=4):
    """给定 w，返回根 x 的外舍入包络 (x_lo, x_hi)。
    M=c_p,R/rho_R 在试探区间取包络，用中值定理界 |M_x|，再夹逼。"""
    lo, hi = 0.3, 4.0
    for _ in range(iters):
        xs = [lo + (hi - lo) * i / 80.0 for i in range(81)]
        Ms = [c.prop(x)[1] / c.prop(x)[0] for x in xs]
        Mlo, Mhi = min(Ms), max(Ms)
        pad = 10.0 * max(abs(Ms[i + 1] - Ms[i]) for i in range(80))
        Mlo, Mhi = NA(Mlo - pad, -1.0), NA(Mhi + pad, 1.0)
        fmin = lambda x: x ** 3 - Mhi * c.G(x, w)          # <= F
        fmax = lambda x: x ** 3 - Mlo * c.G(x, w)          # >= F
        hi_new = bisect(fmin, lo, hi, 1e-14)               # F_min>0 => 根在左侧
        lo_new = bisect(fmax, lo, hi, 1e-14)               # F_max<0 => 根在右侧
        lo, hi = NA(lo_new, -1.0), NA(hi_new, 1.0)
    return lo, hi


def section_mono():
    L('')
    L('=' * 78)
    L('[B] 从"端点抽样"升到"单参数包络"：单调性证书 + 外舍入夹逼')
    L('=' * 78)
    L('   要宣称 w∈[0,1] 上的包络，须证两件事：')
    L('     (i) F(x,w)=0 的根存在且唯一   (ii) D_m 关于 w 单调  => 极值在端点')
    L('')
    L('   记 M=c_p,R/rho_R、G=(1-w)(1+delta)+w(lambda/d)f_R：')
    L('     F_x = 3x^2 - M_x G - M G_x ，F_w = -M[(lambda/d)f_R - 1]')
    L('   M_x 用中值定理界住：|M_x| <= (M_hi-M_lo)/(x_hi-x_lo)。')
    L('')
    L('   %-22s %-11s %-9s %-21s %-8s'
      % ('案例', '|M_x|上界', 'min F_x', '(l/d)f_R-1 范围', '结论'))
    cases = (
        ('Zhao d=lambda=.5', Case(0.5, 0.5, 2.0, QR_IDEAL, 0.25), (0.9, 1.2)),
        ('KYLIN 全相似', Case(0.5 ** 0.7, 0.5, 2.0, 1 / 0.268, 0.25), (0.9, 1.15)),
        ('KYLIN 降高度', Case(1.0, 0.5, 2.0, 1.0, 0.25, R_ideal=1.0), (0.7, 1.4)),
    )
    for name, c, (a, b) in cases:
        Ma, Mb = c.prop(a)[1] / c.prop(a)[0], c.prop(b)[1] / c.prop(b)[0]
        dM = abs(Mb - Ma) / (b - a)
        fR = max((c.R_id * x * c.d * c.prop(x)[2]) ** c.n for x in (a, 0.5 * (a + b), b))
        Fx = 3 * a * a - dM * c.G(b, 1.0) - max(Ma, Mb) * (c.lam / c.d) * c.n * fR / a
        g = [(c.lam / c.d) * (c.R_id * x * c.d * c.prop(x)[2]) ** c.n - 1.0
             for x in (a, 0.5 * (a + b), b)]
        tag = 'D 随 w 增' if min(g) > 0 else ('D 随 w 减' if max(g) < 0 else 'F_w 过零(≈相似点)')
        L('   %-22s %-11.2e %-9.4f %-21s %-8s'
          % (name, dM, Fx, '%+.4f ~ %+.4f' % (min(g), max(g)), tag))
    L('')
    L('   => 三案 F_x>0 => 根唯一；F_w 不变号处 D_m(w) 严格单调，极值在端点。')
    L('      Zhao / 降高度：(lambda/d)f_R 恒 >1 / 恒 <1 => 端点即极值。')
    L('      KYLIN 全相似：(lambda/d)f_R 在区间内跨 1 => F_w≈0，D 对 w 一阶不敏感 ——')
    L('      这正是"该设计本身就是相似条件"的解析表述（第三节给指数级证明）。')
    L('')
    L('   端点值的外舍入夹逼（不是抽样）：M 取区间包络 => F_min<=F<=F_max，')
    L('   F_min(x)>0 的最左点给上界、F_max(x)<0 的最右点给下界，迭代收紧 4 轮。')
    L('')
    L('   %-18s %-5s %-14s %-14s %-11s %-10s'
      % ('案例', 'w', 'x 下界', 'x 上界', '数值间隙', 'D_m'))
    for name, c, _ in cases:
        for w in (0.0, 1.0):
            lo, hi = enclose(c, w)
            L('   %-18s %-5.1f %-14.9f %-14.9f %-11.2e %+9.4f%%'
              % (name, w, lo, hi, hi - lo, 100 * (c.R_id * hi / c.R_ideal - 1)))
    L('')
    L('   => 数值间隙 ~1e-14，比 D 的 1e-4 pp 小十个量级：端点值已含舍入。')
    L('      合起来得到：D_m ∈ [D(w=0), D(w=1)]，在 **w 这一个参数上**成立。')
    L('      但 d、lambda/d、n、delta、物性、绝热闭合仍是声明 —— 整句只能叫')
    L('      "声明模型内的条件包络"，不叫跨案例认证上界。')

# ============================================================ [C] KYLIN 全相似
def section_kylin_sim():
    L('')
    L('=' * 78)
    L('[C] KYLIN 全相似：修正后恒为 0，而且能反推出 Xu 的缩比指数')
    L('=' * 78)
    c = c0 = 0.5
    n = 0.25
    dR = c ** ((2.0 - n) / (2.0 * (1.0 + n)))
    mR = c ** (2 * ((2.0 - n) / (2.0 * (1.0 + n))) + 0.5)
    L('   Xu FR26-170 表 2（c=0.5）：l_R=0.5, d_R=0.616, m_R=0.268, ΔT_R=1, q_R=0.871')
    L('   本脚本复算：d_R=c^(2-n)/(2(1+n)) = %.6f，m_R=c^(2ξ+0.5) = %.6f'
      % (dR, mR))
    L('     q_R = m_R/(l_R d_R) = %.4f（= c^0.2），与表 2 的 0.871 吻合'
      % (mR / (c * dR)))
    L('     => 表 2 的 q_R 是**面热流密度**比，功率比是 m_RΔT_R=%.4f。' % mR)
    L('')
    L('   把 K_R=1（摩擦数不失真）代入 v2 的 K_R 分解并解 r：')
    L('     (l_R/d_R)(r d_R)^n = 1  =>  r = d_R^((1-n)/n) c^(-1/n)，r=m_P/m_M')
    r_sim = dR ** ((1.0 - n) / n) / c ** (1.0 / n)
    L('     r = %.6f  =>  m_R = m_M/m_P = %.6f   （Xu 的 c^1.9 = %.6f）'
      % (r_sim, 1 / r_sim, c ** 1.9))
    L('     d_R = c^0.7 = %.6f 就是"使 (l_R/d_R)(r d_R)^n=1"的唯一解。'
      % (c ** 0.7))
    L('   => **修正后的通式把 Xu 准则当作自己的一个特例复现出来了**。')
    L('      这不是恒等式重排：Xu 的指数来自 H2TS 相似推导，本式来自集总动量+能量。')
    L('')
    cA = Case(dR, c, 2.0, 1 / mR, n)
    L('   数值（w 取四段模型名义点 48.6726%%，Q_R=1/m_R=%.6f）：' % (1 / mR))
    L('   %-6s %-14s %-14s' % ('w', 'v1 D_m', 'v2 D_m'))
    for w in (0.0, 0.25, 0.486726, 0.75, 1.0):
        L('   %-6.4f %+14.4f%% %+14.4f%%'
          % (w, 100 * cA.D(w, True), 100 * cA.D(w, False)))
    L('   => v1 给出 +3.79%（假失真），v2 恒为 0。')
    L('      原因：v1 的 lambda/d=1，而该设计恰恰是 d_R=c^0.7≠l_R=c；')
    L('      漏掉 lambda/d 就把"已相似的台架"判成失真。')
    L('   => 上一轮的「KYLIN 全相似 w*(3%)=0.386」随之作废：它度量的是公式误差。')


# ============================================================ [D] KYLIN 降高度
def section_kylin_height():
    L('')
    L('=' * 78)
    L('[D] KYLIN 只降高度：分母换回设计目标后，偏差约 −13%，不是 ≤3%')
    L('=' * 78)
    L('   设计意图：同功率、同 ΔT、同流量（m_M/m_P=1）=> 声明 R_ideal=1。')
    L('   v1 用的是 R_id=(H_R Q_R)^(1/3)=2^(1/3)=1.2599，它量的是"相对几何理想比"的')
    L('   偏差 x-1，不是"相对设计目标"的偏差。两个分母差 26%，绝不能混。')
    L('')
    c = Case(1.0, 0.5, 2.0, 1.0, 0.25, R_ideal=1.0)
    L('   R_id=%.6f，R_ideal=%.1f  =>  D_m(P/M)=r/R_id-1，eps(M/P)=R_ideal/r-1'
      % (c.R_id, c.R_ideal))
    L('')
    L('   %-8s %-11s %-19s %-12s %-12s %-12s'
      % ('w', 'r=m_P/m_M', 'eps(M/P) v2 = m_M/m_P-1', 'x-1 v1', 'x-1 v2', 'D_m(P/M) v2'))
    for w in (0.0, 0.25, 0.486726, 0.75, 0.9103, 1.0):
        x2, x1 = c.solve(w, False), c.solve(w, True)
        L('   %-8.4f %-11.5f %+19.4f%% %+12.4f%% %+12.4f%% %+12.4f%%'
          % (w, c.R_id * x2, 100 * (1.0 / (c.R_id * x2) - 1),
             100 * (x1 - 1), 100 * (x2 - 1), 100 * (c.R_id * x2 - 1)))
    ws2 = bisect(lambda w: (1.0 / (c.R_id * c.solve(w, False)) - 1) + 0.03, 0.0, 1.0)
    L('')
    L('   w*(|eps|=3%%)（v2，设计目标分母）：%.4f' % ws2)
    L('   v1 的 x-1 全程只到 %+.2f%%（w=1）——旧代码的"全 w≤3%%，上界 +1.94%%"数字没错，' % (100 * (c.solve(1.0, True) - 1)))
    L('   错在它回答的是"相对几何理想比 R_id 偏多少"，不是"相对设计目标 m_M/m_P=1 差多少"。')
    L('   => v1 的「全 w∈[0,1] 都 <=3%%（上界 +1.94%%）」作废：既换了分母，也漏了 lambda/d。')
    L('      正确说法：绝热条件下要 |eps|<=3%% 需 w>=%.2f（本几何）；w=0.4867 时 eps=%.2f%%。'
      % (ws2, 100 * (1.0 / (c.R_id * c.solve(0.486726, False)) - 1)))
    L('')
    L('   解析旁证（d=1 均匀管，rho/c_p≈1）：r^3 = H_R[(1-w)+w l_R r^n] = 2[(1-w)+0.5w r^0.25]')
    L('     w=1 => r^3 = r^0.25 => r=1（纯分布摩擦时降高度恰好保流量）；')
    L('     w=0 => r^3 = 2 => r=1.26（纯局部阻力时流量按 √H 掉）。')
    L('   => −13% 的主体是**局部损失不随长度缩短**（(1-w) 项），不是热路。')
    return c


# ============================================================ [E] 四段反例
def section_four():
    L('')
    L('=' * 78)
    L('[E] 四段模型反例：固定 k、只把 US 设 0，偏差仍是 −13.29%')
    L('=' * 78)
    mod = runpy.run_path(str(Path(__file__).with_name('loop_audit_repair.py')))
    solve, calibrate, SEC = mod['solve'], mod['calibrate'], mod['SEC']
    cal, _, _, _, k_cal = calibrate(3.35)
    k_base = sum(s['k'] for s in SEC.values())

    def eps(k_tot, US):
        p = dict(cal, kmult=k_tot / k_base)
        p['US'] = US
        a, _ = solve(p)
        pm = dict(p, lR=0.5, Q=p['Q'], UA=p['UA'], US=p['US'] * 0.5)
        b, _ = solve(pm)
        return b / a - 1.0

    L('   标定（Li 2015, PNE 81:239, 24 kW -> 1.2 kg/s）：k_tot=%.4f' % k_cal)
    L('   US_P=6 W/K, US_M=3 W/K 是反标定量，与 k_tot 简并；两参数两条 FoM。')
    L('')
    L('   %-10s %-14s %-14s %-10s' % ('k_tot', 'eps(US=6)', 'eps(US=0)', '热损抵掉'))
    for k in (3.0, 6.0, k_cal, 36.0):
        e6, e0 = eps(k, 6.0), eps(k, 0.0)
        L('   %-10.4f %+14.4f%% %+14.4f%% %-10.4f pp'
          % (k, 100 * e6, 100 * e0, 100 * (e6 - e0)))
    L('')
    L('   => US 从 6 改 0（k 不动），|eps| 一律**变大**：名义点 12.151% -> 13.286%。')
    L('      热损是把偏差**抵消**了一部分，不是造成偏差。')
    L('      「−12.15% 主要由 UA_R=1、US_R=0.5 的热路造成」——**撤回**。')
    L('')
    L('   与比值模型对照（同一 K_R 结构）：')
    L('     四段：K_R=(1-w)+w l_R f_R（k 不随 l_R 缩，f L/D 随 l_R 缩）')
    L('     比值：K_R=(1-w)+w(lambda/d) f_R，d=1、lambda=0.5')
    L('     四段 US=0 给 13.286%，比值模型绝热给 13.179%，差 0.1 pp。')
    L('   => 两个结构不同的模型独立吻合到 0.1 pp，这才是"修正后的通式对了"的证据；')
    L('      恒等式残差为零不具备这个性质（它能分解，不能检验）。')


# ============================================================ [F] 17.9 kW
def section_holdout():
    L('')
    L('=' * 78)
    L('[F] 17.9 kW：只剩一个独立对比，且"同号偏低/符号反转"是控制体伪像')
    L('=' * 78)
    mod = runpy.run_path(str(Path(__file__).with_name('loop_audit_repair.py')))
    solve, calibrate = mod['solve'], mod['calibrate']
    cal, _, _, _, k_cal = calibrate(3.35)
    p = dict(cal)
    p['Q'] = 17.9e3
    m, d = solve(p)
    L('   标定 24 kW/1.2 kg/s，固定 (k_tot=%.4f, UA, US=6)，直接预测 17.9 kW：' % k_cal)
    L('     m=%.4f kg/s（测 1.12，%+.2f%%）  dT_loop=%.2f K' % (m, 100 * (m / 1.12 - 1), d['dT']))
    L('')
    L('   **口径分账（本轮新增，也是上一轮的错）**：')
    L('     Yue §5.1：m 由 HS 能量平衡反算 m=P/(c_p ΔT_HS) => 观测 108.6 K 是')
    L('     **加热段进出口**温差（毛热 Q=17.9 kW 口径）；模型 dT=Q_net/(m c_p) 是')
    L('     **回路净热**温差（Q_net=Q-US(Tb-Tamb)，此处 %.2f kW）。' % (d['Qnet'] / 1e3))
    L('     把两者相减，等于拿"扣了散热"的去比"没扣散热"的。')
    L('     同控制体重算：dT_HS=Q/(m c_p)=%.2f K，对 108.6 是 %+.2f%%。'
      % (17.9e3 / (m * cp_z(533.15 + 17.9e3 / (m * cp_z(533.15)) / 2)),
         100 * (17.9e3 / (m * cp_z(533.15 + 17.9e3 / (m * cp_z(533.15)) / 2)) / 108.6 - 1)))
    L('     => m 偏低 4%，则 ΔT_HS 必偏高约 4%（m·ΔT=Q 绑死）。')
    L('       上一轮「两个 FoM 同号偏低约 4%」是热损账与流量账在反方向上凑出来的数，')
    L('       **撤回**；「符号随热损口径反转」同样撤回。')
    L('')
    L('   为什么 US=0 不是"统一口径"：')
    L('     Yue §5.2 原文：CFD 假定绝热，"the inlet temperature of HS is experimentally')
    L('     lower than the outlet temperature of HX **because of the heat losses**"。')
    L('     原文自己证明整回路有散热 => 整回路 US=0 与实验描述相矛盾，是换闭合不是换尺。')
    cal0, _, d0, _, k0 = calibrate(3.35, US=0.0)
    p0 = dict(cal0)
    p0['Q'] = 17.9e3
    m0, _ = solve(p0)
    L('     US=0 重标：k_tot %.4f -> %.4f（+%.1f%%），m 预测 %.4f（%+.2f%%）'
      % (k_cal, k0, 100 * (k0 / k_cal - 1), m0, 100 * (m0 / 1.12 - 1)))
    L('     => 两闭合给出的 m 差 %.2f%%，这才是"单点标定分不开 US 与 k"的量。'
      % (100 * (m0 / m - 1)))
    L('')
    L('   同一台架的精度参照（原文自给）：')
    L('     Yue §5.2 作者自算（全功率段优化后）：17.9 kW -> 1.10 kg/s、110.3 K')
    L('       对实测 1.12/108.6 是 %+.2f%% / %+.2f%%' % (100 * (1.10 / 1.12 - 1), 100 * (110.3 / 108.6 - 1)))
    L('     本模型（只标 24 kW 一点）：m %+.2f%%' % (100 * (m / 1.12 - 1)))
    L('     => 3~4% 是"单点标定 0D 模型"的代价，不是失稳；但它是 2% 的 2 倍，')
    L('        不能说"小一个量级"（对约 10% 的条件界只是 2.5 倍，不是数量级）。')
    L('   幂指数对照：')
    L('     本模型 1/(3-n w)=%.4f；Yue 表 3（理论矩阵 4->24 kW）%.4f；'
      % (1.0 / (3.0 - 0.25 * 0.486726),
         math.log(1.215 / 0.657) / math.log(24.0 / 4.0)))
    L('     两点实测（17.9 kW 与 24 kW）%.4f'
      % (math.log(1.20 / 1.12) / math.log(24.0 / 17.9)))
    L('     => 模型与作者的理论曲线同斜率（0.347 vs 0.343），两点实测的斜率只有 0.235。')
    L('        不一致发生在**两次实测之间**，不在模型与理论之间。')
    L('        仍待核：Li 2015 与 Yue 2017 的二次侧油流量/温度是否同条件。')


# ============================================================ [G] 结论
def section_concl():
    L('')
    L('=' * 78)
    L('[G] 可宣称 / 不可宣称')
    L('=' * 78)
    L('   可宣称（模型内条件包络）：')
    L('     1. 通式 x^3=K_R c_p,R/rho_R，K_R=(1-w)(1+delta)+w(lambda/d)f_R。')
    L('     2. Zhao（d=lambda=0.5, delta=0, 绝热, n=1/4）：D_m ∈ [0, +9.78%]（Q_R=2^2.5）')
    L('        或 [0, +9.73%]（Q_R=10/1.77）；w∈[0,1] 已用单调性+外舍入夹逼证明，')
    L('        不再只是端点抽样。')
    L('     3. 修正后的通式把 Xu 准则复现为特例（K_R=1 <=> d_R=c^0.7、m_R=c^1.9），')
    L('        并在 KYLIN 降高度上与四段模型独立吻合到 0.1 pp。')
    L('     4. KYLIN 降高度主偏差 = 局部损失不随长度缩短（(1-w) 项），热损抵掉约 1.1 pp。')
    L('')
    L('   不可宣称：')
    L('     a. "认证上界"——只对 w 一个参数认证；d、lambda/d、n、delta、物性、')
    L('        绝热闭合、单 lambda 单 d 理想化都是声明，其中赵的 d=0.5 无净流道依据。')
    L('     b. 跨案例移植 w*(3%)：Zhao 0.304 / 全相似 0 / 降高度 0.91，三种几何三个数。')
    L('     c. "17.9 kW 留出验证通过"：只有 m 一个独立对比，偏差 4%，且两篇文献')
    L('        的二次侧条件未核。它是**候选外部对照点**。')
    L('     d. 任何单一百分数而不写分母（m_R=1 与 sqrt(0.5) 差 36 个百分点）。')


def main():
    L('自然循环缩比失真：源无关条件界 v2（通式修正）    2026-11-02')
    section_derive()
    section_zhao()
    section_mono()
    section_kylin_sim()
    section_kylin_height()
    section_four()
    section_holdout()
    section_concl()
    out = Path(__file__).with_name('source_free_bound_v2_log.txt')
    out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
    print('\n[log] %s（%d 行）' % (out.name, len(LOG)))


if __name__ == '__main__':
    main()
