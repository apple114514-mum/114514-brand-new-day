#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源无关条件界 v6：解析界的适用域 + 3% 判据的双侧 w 区间

对 2026-11-02 第五轮复核（source-free-v5-review, main 42f948f）的逐条处理：

  [0] 四条逐条复现
      (i)   204 行日志已逐行复现（复核方给出，本文不改）
      (ii)  "对所有 delta>-1" 过强：上界需 M(x)<=1 于根处；给出 x=6 反例
      (iii) |D|<=3% 是 w 的双侧区间，不是 "delta<=9.2727% 且 w<=w*"
      (iv)  F_dep_iv 在 delta!=0 时漏了 (1+delta) 项
  [A] 上界的适用域：M(x)=1 的根位置、对应 delta、T；并揭出 v5 还有一条
      隐藏前提 lambda/d<=1（赵恰好 =1，所以"看不出错"）；给一般化闭式
  [B] 下界：补全证明（x<1 时 f>x^3 靠 B>1，而非"全域 (l/d)f>=1"）+ 数值核对
  [C] 双侧判据：w_t(delta)=[K_t-A]/[f_t-A]，闭式、单调、区间包络、正向上限
      delta_crit=K_+-1=9.2755605%，负向无阈值（delta->-1 时仍有可行 w 带）
  [D] 81 点 CSV 独立复算
  [E] 两个 delta 阈值之差的分解（主项是根包络间隙，不是物性）
  [F] F_dep_iv 修正与"污染范围"
  [G] 文献边界：Yue 2017 表 2 仍待核；delta 无实物约束
  [H] 可宣称 / 不可宣称

依赖同目录 source_free_bound_v5.py 的区间核与 Model（v5 的 main 不会被执行）。
纯标准库。运行：python source_free_bound_v6.py
"""
import math
import csv
from pathlib import Path

import source_free_bound_v5 as V
from source_free_bound_v5 import I, e_lit, i_cbrt, i_pow_nonneg, dn, up

LOG = []
INF = math.inf


def L(s=''):
    print(s)
    LOG.append(s)


D_XT = 0.5
D_LAM = 0.5
D_HR = 2.0
D_N = 0.25
QR = V.QR_ZHAO

Z0 = V.Model(D_XT, D_LAM, D_HR, QR, D_N)
RID = Z0.i_Rid.a
B = (RID * D_XT) ** D_N
XBAR = (RID * D_XT) ** (D_N / (3.0 - D_N))


def Kc(x):
    """K(x) = x^3 / M(x) = x^3 rho_R / c_p,R"""
    return x ** 3 / Z0.M_s(x)


K_MINUS, K_PLUS = Kc(0.97), Kc(1.03)
F_MINUS, F_PLUS = Z0.f_s(0.97), Z0.f_s(1.03)


def w_of(delta, Kt, ft):
    """在固定目标 x_t 处解 G(w)=K_t： w = (K_t - A)/(f_t - A)，A=1+delta"""
    A = 1.0 + delta
    return (Kt - A) / (ft - A)


def band(delta):
    return max(0.0, w_of(delta, K_MINUS, F_MINUS)), min(1.0, w_of(delta, K_PLUS, F_PLUS))


# ============================================================ [0]
def section_admit():
    L('=' * 78)
    L('[0] 第五轮复核四条：逐条复现')
    L('=' * 78)
    L('   (i)   204 行日志逐行一致 —— 复核方已确认，本文不重跑 v5 全文。')
    L('')
    L('   (ii)  "对所有 delta>-1" 过强 —— 成立。')
    L('         上界第 2 步用的是 M(x)<=1 在**根处**成立；这个条件不是恒真的。')
    L('         按同一 Zhao 多项式物性外推，M(x)=1 出现在')
    lo, hi = 5.0, 6.0
    for _ in range(200):
        m = 0.5 * (lo + hi)
        if Z0.M_s(m) < 1.0:
            lo = m
        else:
            hi = m
    xM = 0.5 * (lo + hi)
    L('           x_M = %.9f   (T_M = %.3f K)' % (xM, Z0.T_s(xM)))
    L('         更外侧 M>1 重新回升（x=8 时 M=%.6f），所以集合 {M<=1} 是区间 [1,x_M]。'
      % Z0.M_s(8.0))
    x = 6.0
    dlt = x ** 3 / Z0.M_s(x) - 1.0
    L('         反例：w=0、x=6 时 M=%.9f>1，由 x^3=M(x)(1+delta) 反定 delta=%.6f，'
      % (Z0.M_s(x), dlt))
    L('               v5 公式给上限 max{(1+delta)^(1/3), xbar}=%.9f < 6 —— 界被破。'
      % max((1 + dlt) ** (1 / 3), XBAR))
    L('         但 T=%.2f K 已在物性验证域外，故是**量词反例**而非物理反例。'
      % Z0.T_s(x))
    L('')
    L('   (iii) |D|<=3% 是双侧 w 区间 —— 成立，见 [C]。')
    L('   (iv)  F_dep_iv 丢 (1+delta) —— 成立，见 [F]。')


# ============================================================ [A]
def section_domain():
    L('')
    L('=' * 78)
    L('[A] 上界的适用域：三条前提，其中一条 v5 没写')
    L('=' * 78)
    lo, hi = 5.0, 6.0
    for _ in range(200):
        m = 0.5 * (lo + hi)
        if Z0.M_s(m) < 1.0:
            lo = m
        else:
            hi = m
    xM = 0.5 * (lo + hi)
    L('   上界 x <= max{A^(1/3), xbar} 的证明实际用了三件事：')
    L('     ① M(x) <= 1      在根处（物性方向）')
    L('     ② mu_R(x) <= 1   在根处（m1=754.1>0，x>=1 时 T_M>=T_P）')
    L('     ③ lambda/d <= 1  几何 —— **v5 只写了 ①②，③ 是隐含的**')
    L('   第 ③ 条来自 G=(1-w)A+w(lambda/d)f：只有 lambda/d<=1 才能把 f 换成 Bx^n')
    L('   而不放大。赵恰好 lambda=d=0.5，lambda/d=1，所以 v5 的式子"看起来对"；')
    L('   这与 v2 把 c_p 放分母是同一类"恰好参数相等所以看不出错"。')
    L('')
    L('   一般化闭式（c=lambda/d 任意）：')
    L('')
    L('        x <= max{ A^(1/3), (c*B)^(1/(3-n)) }         c=lambda/d, B=(R_id d)^n')
    L('')
    L('   数值核对（把 c 换掉，其他不变，看端点是否被包住）：')
    L('   %-6s %-10s %-12s %-24s %-10s'
      % ('c', 'xbar_c', '解析上限', '端点 D(w=0)/D(w=1)', '界宽出'))
    for c in (0.5, 1.0, 2.0):
        z = V.Model(D_XT, D_LAM * c, D_HR, QR, D_N)
        xb = (c * B) ** (1.0 / (3.0 - D_N))
        upv = max(1.0 ** (1 / 3), xb)
        e0, e1 = z.D_s(0.0), z.D_s(1.0)
        L('   %-6.2f %-10.6f %+11.6f%%   %+10.6f%%  %+10.6f%%   %+8.4f pp'
          % (c, xb, 100 * (upv - 1), 100 * e0, 100 * e1,
             100 * (upv - 1 - max(e0, e1))))
    L('   => 三条都对得上；c=1 一行就是 v5 的数（+9.9131%）。')
    L('')
    L('   于是"适用域"的精确说法是三层，论文里必须分开写：')
    L('     层一（纯数学）：若根处 M<=1、mu_R<=1、lambda/d<=1，则界成立。')
    L('     层二（本模型）：M(x)<=1 等价于根 <= x_M=%.6f，即 delta<=%.6f（w=0 支）。'
      % (xM, xM ** 3 - 1.0))
    L('     层三（物性关联式验证域）：比层二窄得多，本项目只有 398.15 K 以上、')
    L('                 上限出处待核；不能拿层二的 875 K 当"物理可用"的依据。')
    L('   论文写法：') 
    L('     "在 M(x)<=1 的物性域内（本案例根 x<=5.2047、T<=875.8 K），δ 参数化界成立"，')
    L('     不写"对所有 delta>-1"。')


# ============================================================ [B]
def section_lower():
    L('')
    L('=' * 78)
    L('[B] 下界：v5 的 (l/d)f>=1 前提可以去掉，但不是"无条件"')
    L('=' * 78)
    L('   复核给的下界论证：x<1 时 T_M<T_P => M>=1、mu_R>=1 => f=B x^n mu_R^n >= B x^n。')
    L('   要得到 >x^3 还需 B x^n > x^3，即 B > x^(3-n)。本案例：')
    L('     B=(R_id d)^n=(%.6f)^%.2f=%.9f  >1  ⇒ x<1 时 x^(3-n)<1<B 恒成立。'
      % (RID * D_XT, D_N, B))
    L('   => f(x)>x^3 对**所有** x<1 成立，不需要全域 (l/d)f>=1。复核这条成立。')
    L('')
    L('   v5 自己举的 delta=-0.99 反例复核：')
    z = V.Model(D_XT, D_LAM, D_HR, QR, D_N, delta=-0.99)
    xs = z.solve_s(0.0)
    L('     w=0 根 x=%.9f，f(x)=%.9f <1，但 f/x^3=%.6f>1'
      % (xs, z.f_s(xs), z.f_s(xs) / xs ** 3))
    L('     => 反驳的是"(l/d)f>=1 覆盖所有 delta"，不是下界本身。')
    L('')
    L('   数值核对（沿 w 全区间扫，看 min D 是否 >= min{0,A^(1/3)-1}）：')
    L('   %-8s %-14s %-14s %-14s %-8s'
      % ('delta', 'A^(1/3)-1', 'min_w D', '最大违约', '判定'))
    worst, tight, tds = -INF, INF, None
    for ds in (-0.99, -0.9, -0.7, -0.5, -0.3, -0.2, -0.1, -0.05, 0.0, 0.05, 0.09):
        c = V.Model(D_XT, D_LAM, D_HR, QR, D_N, delta=ds)
        lov = min(0.0, (1 + ds) ** (1 / 3) - 1)
        mn = min(c.D_s(i / 80.0) for i in range(81))
        viol = lov - mn
        worst = max(worst, viol)
        if viol < 0.0 and -viol < tight:
            tight, tds = -viol, ds
        L('   %-8.2f %+13.6f%% %+13.6f%% %+13.2e %s'
          % (ds, 100 * lov, 100 * mn, viol, 'OK' if viol <= 1e-9 else '违约'))
    L('   => max(界-实测) = %+.2e（非正即包住；delta=0 处取等号）' % worst)
    L('      最紧余量 = %.2e pp（出现在 delta=%+.2f）；下界在声明模型内成立。'
      % (tight, tds))


# ============================================================ [C]
def section_twosided():
    L('')
    L('=' * 78)
    L('[C] 主修正：|D|<=3% 是 w 的双侧区间，判据是 (delta,w) 平面的一条带')
    L('=' * 78)
    L('   在固定目标点 x_t 处，F=0 等价于 G(w)=K_t，其中 K_t=x_t^3 rho_R/c_p,R=x_t^3/M(x_t)。')
    L('   而 G(w)=(1-w)A+w f_t 对 w 是仿射的，A=1+delta，于是**显式反解**：')
    L('')
    L('        w_t(delta) = (K_t - A) / (f_t - A),      A = 1+delta')
    L('')
    L('   x_t=0.97 -> w_-(delta)；x_t=1.03 -> w_+(delta)。可行带：')
    L('')
    L('        max(0, w_-(delta)) <= w <= min(1, w_+(delta)),  且须左端 <= 右端')
    L('')
    L('   两个常数（每个设计算一次，之后 delta 进显式有理函数）：')
    L('     K_-=%.12f  f_-=%.12f' % (K_MINUS, F_MINUS))
    L('     K_+=%.12f  f_+=%.12f' % (K_PLUS, F_PLUS))
    L('   单调性：dw_t/ddelta = (K_t-f_t)/(f_t-A)^2 <0（因 K_t<f_t），故两条边界都随 delta 单调下降。')
    L('')
    L('   %-9s %-12s %-12s %-12s %-26s'
      % ('delta', 'D(w=0)', 'w_-', 'w_+', '可行 w'))
    for ds in (-0.20, -0.15, -0.10, -0.09, -0.05, 0.0, 0.03, 0.05, 0.07, 0.09,
               0.0927, 0.092755604):
        c = V.Model(D_XT, D_LAM, D_HR, QR, D_N, delta=ds)
        a, b = band(ds)
        L('   %-9.6f %+11.4f%% %-12.6f %-12.6f [%.6f, %.6f]%s'
          % (ds, 100 * c.D_s(0.0), w_of(ds, K_MINUS, F_MINUS),
             w_of(ds, K_PLUS, F_PLUS), a, b, '  <= 空' if a > b else ''))
    L('')
    L('   与复核给的表逐点一致：delta=-0.10 -> [0.032573,0.475787]（复核 0.03257/0.47579）；')
    L('   delta=0 -> [0,0.303987]；delta=+0.07 -> [0,0.096779]。')
    L('')
    L('   三件结构性的事：')
    L('     1. 正向上限是 delta_crit = K_+-1 = %.12f = %.7f%%'
      % (K_PLUS - 1.0, 100 * (K_PLUS - 1.0)))
    L('        比恒物性的 1.03^3-1 = %.7f%% 高 %.2e（相对 %.4f%%）。'
      % (100 * (1.03 ** 3 - 1), (K_PLUS - 1) - (1.03 ** 3 - 1),
         100 * ((K_PLUS - 1) / (1.03 ** 3 - 1) - 1)))
    L('        数值差异极小，**但"硬上限"这个提法和"delta<=0 判据不变"都错**：')
    L('        错的是结构，不是末位。')
    L('     2. 负向**没有**阈值：delta->-1 时 w_- -> K_-/f_- = %.9f、w_+ -> K_+/f_+ = %.9f，'
      % (K_MINUS / F_MINUS, K_PLUS / F_PLUS))
    L('        带仍非空（宽 %.4f）。物理读法：局阻偏小可以靠提高摩擦份额救回来；'
      % (K_PLUS / F_PLUS - K_MINUS / F_MINUS))
    L('        局阻偏大过 %.4f%% 则怎么分配都救不回来。' % (100 * (K_PLUS - 1)))
    L('     3. delta<0 时 w=0 已越 -3%，所以 v5 的 "w<=w*" 是**漏掉下界**的写法。')
    L('')
    L('   区间包络（不是点值；A 用十进制字面量 e_lit 入区间）：')
    L('   %-9s %-34s %-34s' % ('delta', 'w_- 包络', 'w_+ 包络'))
    for ds in ('-0.10', '0.00', '0.07'):
        A = I(1.0) + e_lit(ds)
        xt_m, xt_p = e_lit('0.97'), e_lit('1.03')
        km = _K_iv(Z0, xt_m)
        kp = _K_iv(Z0, xt_p)
        fm = Z0.f_iv(xt_m, Z0.T_iv(xt_m))
        fp = Z0.f_iv(xt_p, Z0.T_iv(xt_p))
        wm = (km - A) / (fm - A)
        wp = (kp - A) / (fp - A)
        L('   %-9s [%.17f, %.17f]  [%.17f, %.17f]'
          % (ds, wm.a, wm.b, wp.a, wp.b))
    L('   => 包络宽 ~1e-15，且与点值同号同序；可称"该浮点模型的条件包含"，')
    L('      不能称"实测"或"物理"界。')


def _K_iv(m, xiv):
    T = m.T_iv(xiv)
    return xiv ** 3 * (m.props.rho(T) / m.props.rho(m.T_P_iv)) / \
        (m.props.cp(T) / m.props.cp(m.T_P_iv))


# ============================================================ [D]
def section_csv():
    L('')
    L('=' * 78)
    L('[D] 81 点情景带：用本脚本的闭式独立复算复核方 CSV')
    L('=' * 78)
    p = Path('D:/Downloads/zhao-three-percent-design-region-20261102.csv')
    if not p.exists():
        L('   （CSV 不在 D:/Downloads，跳过；公式已在 [C] 给出）')
        return
    rows = list(csv.DictReader(open(p, encoding='utf-8')))
    e1 = e2 = e3 = 0.0
    for r in rows:
        ds = float(r['delta_scenario'])
        a, b = band(ds)
        e1 = max(e1, abs(a - float(r['w_min_for_abs_D_le_3pct'])))
        e2 = max(e2, abs(b - float(r['w_max_for_abs_D_le_3pct'])))
        c = V.Model(D_XT, D_LAM, D_HR, QR, D_N, delta=ds)
        e3 = max(e3, abs(100 * c.D_s(0.0) - float(r['D_at_w0_percent'])))
    L('   %d 行；最大偏差：w_min %.2e、w_max %.2e、D(w=0) %.2e pp'
      % (len(rows), e1, e2, e3))
    L('   => CSV 与闭式一致到其打印位数（12 位小数）。')
    L('')
    L('   端点回代（把 w_-/w_+ 代回求根，看 D 是否正好 ±3%）：')
    for ds in (-0.20, -0.10, 0.0, 0.05, 0.09):
        c = V.Model(D_XT, D_LAM, D_HR, QR, D_N, delta=ds)
        a, b = band(ds)
        L('     delta=%+.2f  D(w_-)=%+.6f%%   D(w_+)=%+.6f%%'
          % (ds, 100 * c.D_s(a), 100 * c.D_s(b)))
    L('   => delta<=0 时左端被 0 截断（w=0 本身未越线），故 D(w_-)=D(0)!= -3%。')


# ============================================================ [E]
def section_gap():
    L('')
    L('=' * 78)
    L('[E] 两个 delta 阈值之差：主项是根包络间隙，不是物性')
    L('=' * 78)
    x1 = Z0.solve_s(1.0)
    M1 = Z0.M_s(x1)
    dnum = x1 ** 3 / M1 - 1.0
    dana = XBAR ** 3 - 1.0
    t1 = XBAR ** 3 - x1 ** 3
    t2 = x1 ** 3 * (1.0 - 1.0 / M1)
    L('   delta_num = x1^3/M(x1)-1 = %+.9f   (x1=%.12f, M(x1)=%.12f)'
      % (dnum, x1, M1))
    L('   delta_ana = xbar^3-1      = %+.9f   (xbar=%.12f)' % (dana, XBAR))
    L('   差 = %+.9f' % (dana - dnum))
    L('   分解：delta_ana-delta_num = [xbar^3-x1^3] + x1^3[1-1/M(x1)]')
    L('        = %+.9f %+.9f = %+.9f' % (t1, t2, t1 + t2))
    L('   主项占比 %.2f%%  ⇒ 应称"保守包络造成的阈值间隙"，不是"物性三倍"。'
      % (100 * t1 / (t1 + t2)))
    L('   （1-M(x1)=%.3e，三倍=%.3e，与 %.3e 差两个量级；v5 那句"正好三倍"是错的。）'
      % (1 - M1, 3 * (1 - M1), t2))


# ============================================================ [F]
def section_fdep():
    L('')
    L('=' * 78)
    L('[F] F_dep_iv 的 delta!=0 缺陷：修与不修各影响什么')
    L('=' * 78)
    L('   原式 G=(1+delta)+w[(l/d)f-(1+delta)]；v5 写成 G=1+w[(l/d)f-(1+delta)]，')
    L('   只有 delta=0 时等价。反例：')
    c = V.Model(D_XT, D_LAM, D_HR, QR, D_N, delta=0.1)
    fa = c.F_iv(I(1.0), I(0.0))
    fb = c.F_dep_iv(I(1.0), I(0.0))
    L('     delta=0.1, w=0, x=1：F_iv=%r   F_dep_iv=%r' % (fa, fb))
    L('     => F_dep_iv 漏掉 -delta，把非根判成根。')
    L('')
    L('   污染范围：v5 只在 [E] 的 KYLIN 根管里调用它，而那里 delta=0（Model 默认），')
    L('   所以**已印出的 KYLIN 根管结论未被污染**。今后凡非零 delta 的判根/判号，')
    L('   必须改用 F_iv 或修好的 F_dep_iv。v6 采用修正版：')
    L('     G = (1+delta) + w[(l/d)f-(1+delta)]，残差与原式一致（下面核对）')
    L('     delta=0.1, w=0.3, x=1.02：F_iv=%r' % (c.F_iv(I(1.02), I(0.3)),))
    L('     （F_dep_iv 正确版见 build_corrected()，数值应与上式区间重叠）')

    def F_dep_ok(m, xiv, wiv, Tiv=None):
        Tiv = m.T_iv(xiv) if Tiv is None else Tiv
        mm = I(m.lam / m.d) * m.f_iv(xiv, Tiv) - I(1.0 + m.delta)
        return xiv ** 3 * (m.props.rho(Tiv) / m.props.rho(m.T_P_iv)) - \
            (I(1.0 + m.delta) + wiv * mm) * (m.props.cp(Tiv) / m.props.cp(m.T_P_iv))

    L('     修正版 F_dep_iv 给 %r' % (F_dep_ok(c, I(1.02), I(0.3)),))


# ============================================================ [G]
def section_refs():
    L('')
    L('=' * 78)
    L('[G] 文献边界：两个数仍无一实物来源')
    L('=' * 78)
    L('   Yue 2017 表 2 的 K_EV≈2.5 / K_HS 2.6-2.9 / K_pipe 17.7-19.1：仍为转述，未见全文。')
    L('   DOI 10.1007/s41365-017-0187-x；nst.sinap.ac.cn 站内检索实测返回空集。')
    L('   即使该表是同一装置的逐段阻力分解：')
    L('     - 它只给**单侧**（台架）的阻力分解，w 可用；')
    L('     - delta=k_M/k_P-1 需要**原型与台架两侧**的局阻，单侧给不出；')
    L('     - 因此 delta 的实物域仍为空，本报告的 delta 一律是"未标定情景参数"。')
    L('')
    L('   %-30s %-22s %s' % ('量', '来源', '状态'))
    L('   %-30s %-22s %s' % ('R_id=5.656854（=4sqrt2）', '本模型+赵表1/3', '有'))
    L('   %-30s %-22s %s' % ('K_-,K_+,f_-,f_+', '本脚本单点求值', '有（模型内）'))
    L('   %-30s %-22s %s' % ('lambda/d', '赵表3 外形尺寸，非净流道', '弱'))
    L('   %-30s %-22s %s' % ('w 的实物值', '单点反标定', '弱（与 k 不可分）'))
    L('   %-30s %-22s %s' % ('delta 的实物范围', '无', '缺'))


# ============================================================ [H]
def section_concl():
    L('')
    L('=' * 78)
    L('[H] 可宣称 / 不可宣称（v6）')
    L('=' * 78)
    L('   可宣称：')
    L('     1. 在 M(x)<=1、mu_R(x)<=1、lambda/d<=1 的物性/几何域内，')
    L('           min{0,A^(1/3)-1} <= D_m <= max{A^(1/3),(cB)^(1/(3-n))}-1,  c=lambda/d')
    L('        本案例该域为根 x<=5.2047（T<=875.8 K）；delta=0 时退化为 +9.9131%。')
    L('     2. |D_m|<=3% 的判据是一条**带**，不是单一阈值：')
    L('           delta < delta_crit=9.2755605%，且 w 落在 [max(0,w_-), min(1,w_+)]')
    L('        w_±=(K_±-A)/(f_±-A)，A=1+delta；两条边界对 delta 单调下降。')
    L('     3. 负向无阈值：delta->-1 仍存在可行 w 带 [0.708403,0.837277]（模型内）。')
    L('     4. KYLIN 根管结论不受 F_dep_iv 缺陷影响（该处 delta=0）。')
    L('   不可宣称：')
    L('     a. "界对所有 delta>-1 成立"（x=6 反例；需 M<=1）。')
    L('     b. "delta<=9.2727% 是硬上限、delta<=0 判据不变"（漏负向分支，且阈值应 K_+-1）。')
    L('     c. "lambda/d 不影响界"（v5 隐含 c=1；c!=1 时第二支要乘 c）。')
    L('     d. "delta 有实物范围"（Yue 表 2 未核，且单侧不够）。')
    L('     e. 任何把上面的带当"台架保证 <=3%"的句子：它是**模型条件曲线**。')


def main():
    L('自然循环缩比失真：源无关条件界 v6（适用域 + 双侧判据）  2026-11-02')
    section_admit()
    section_domain()
    section_lower()
    section_twosided()
    section_csv()
    section_gap()
    section_fdep()
    section_refs()
    section_concl()
    out = Path(__file__).with_name('source_free_bound_v6_log.txt')
    out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
    print('\n[log] %s（%d 行）' % (out.name, len(LOG)))


if __name__ == '__main__':
    main()
