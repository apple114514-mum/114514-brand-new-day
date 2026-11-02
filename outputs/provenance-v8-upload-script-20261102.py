#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""参数定级与输入分辨率审计 v8

对 2026-11-02 第七轮复核（parameter-provenance-20261102 / claim-matrix，main 381bf58）
的逐条处理：

  [A] 定级复核：我 21:38 那张溯源表有 7 行要动（含一处数字错误 w=0.370 -> 0.2915）
  [B] 两张图必须分开：数据归约 D_m(d; r_m, Q_R, H_R) 与 预测 D_s(w, delta, c, n)
  [C] ★ 主结果：D_m 的输入分辨率 —— 要支撑 1 pp 的 D_m，各输入需要多准
  [D] kappa = 0.9987384 的身份：它就是 Q_R 的取整比，应从论文删除
  [E] eps_Q：表 5 的 (Q, mdot, dT) 自己不闭合 => D_m 三个口径跨过 3%
  [F] 3% 可行带对 d 的脆弱性：w_+ = 0.204 / 0.304 / 0.509
  [G] c0 的可移植性：依赖声明比值，不能跨案例搬运
  [H] 物性标签缺陷：_mu_s 硬编码指数式，Zhao 表 4 的多项式黏度从未生效
  [I] 新结果：表 5 核心压降一致性 K_R,core = 1.03295
  [J] delta 的 Re 包络重定级：A1 是设计意图（L4），不是文献事实
  [K] 可写 / 不可写

依赖 source_free_bound_v5.py 的模型与区间核。纯标准库 + unicodedata。
运行：python provenance_audit_v8.py
"""
import math
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_free_bound_v5 as V

LOG = []
HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 日志工具
def dw(s):
    """CJK 全角计 2，其余计 1。"""
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)


def pad(s, w, right=False):
    s = str(s)
    n = w - dw(s)
    if n <= 0:
        return s
    return (' ' * n + s) if right else (s + ' ' * n)


def L(s=''):
    print(s)
    LOG.append(s)


def row(cells, widths, right=()):
    return '  ' + ' '.join(pad(c, w, i in right) for i, (c, w) in enumerate(zip(cells, widths)))


def sec(tag, title):
    L('')
    L('=' * 78)
    L('[%s] %s' % (tag, title))
    L('=' * 78)


# ---------------------------------------------------------------- 案例常量
HR = 2.0                     # 循环高度比 H_P/H_M（Z20 表3：2/1）
N_IDX = 0.25                 # 摩擦关联式指数（Blake）
RM = 540.0 / 92.79           # 流量比 m_P/m_M（Z20 表5，CFD）
QR_DECL = 4.0 * math.sqrt(2)  # 脚本里声明的功率比（<=> Q_M = 1.7678 MW）
QR_TAB = 10.0 / 1.77         # 表 3 印数直接相除（<=> Q_M = 1.7700 MW）
D_ZHAO = 0.5                 # 长度比（Z20 表3 全部八行均为 2:1）
D_XT = 0.5
M0 = V.Model(D_ZHAO, 0.5, HR, QR_DECL, N_IDX, delta=0.0)


def r_id(d, Q_R=QR_DECL, H_R=HR):
    """理想流量比 R_id = (H_R Q_R / d^4)^(1/3)。"""
    return (H_R * Q_R / d ** 4) ** (1.0 / 3.0)


def d_m(d, Q_R=QR_DECL, H_R=HR, r_m=RM):
    """数据归约（Map I）：D_m = r_m / R_id - 1。与 w、delta、n 无关。"""
    return r_m / r_id(d, Q_R, H_R) - 1.0


def bisect(f, lo, hi, iters=300):
    flo = f(lo)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        if (flo < 0) == (f(mid) < 0):
            lo, flo = mid, f(mid)
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ================================================================ [A]
def section_grading():
    sec('A', '定级复核：我 21:38 那张表有 7 行要动')
    W = [24, 18, 16, 42]
    L(row(['行', '我写的', '实际', '依据 / 改法'], W))
    L('  ' + '-' * 100)
    items = [
        ('rho、cp、mu 三行', 'L1（杨若楠 2020）', 'L1 但分两套',
         'Z20 表4 与 X26 式(15)-(18) 是两套；rho 斜率 1.1944 vs 1.3235'),
        ('mu(T) 的函数形式', '指数式', '多项式（Z20）',
         'Z20 表4 给 4.56e-3-7.03e-6T+3.61e-9T^2；指数式属 X26'),
        ('lambda_R = L_M/L_P', 'L1', 'L2（推论）',
         '表3 八行全为 2:1 => 均匀缩放；逐段流道长度仍未列'),
        ('d_R = D_M/D_P', 'L1*（仅外形）', 'L2（比率可靠）',
         '比率由均匀缩放支持；净流通面积绝对量仍不可知'),
        ('w（赵）', '0.370', '0.2915', '旧值含 kappa 与 eps_Q；见 [D][E]'),
        ('delta 的 Re 包络', 'L2', 'L4+L2 混合',
         'A1（同构件类型与数量）是设计意图，非文献事实'),
        ('物性下限 398.15 K', 'L4，出处缺', 'L4，已确认缺',
         '两篇原文表 4 / 式(15)-(18) 均未列适用温区'),
    ]
    for r in items:
        L(row(list(r), W))
    L('')
    L('  => 一处数字错误（w）、一处标签错误（mu 形式）、五处等级过高。')
    L('     下面逐条给出改后的数。')


# ================================================================ [B]
def section_two_maps():
    sec('B', '两张图必须分开：数据归约 与 预测')
    L('  Map I  数据归约：D_m = r_m d^(4/3) / (H_R Q_R)^(1/3) - 1')
    L('                   输入只有 r_m、d（面积比）、Q_R、H_R；与 w、delta、n 无关。')
    L('  Map II 预测    ：D_m = D_s(w, delta, c, n)，由 F(x;p)=0 求根。')
    L('                   输入是设计量：摩擦份额、局阻失配、路径/管径比、关联式指数。')
    L('  桥              ：K_R = (1+D_m)^3 rho_R / c_p,R  —— 用 Map I 的观测去标定 Map II。')
    L('')
    L('  这不是文字游戏：两张图的主导参数完全不同，混用会得出相反的结论。')
    L('')
    W = [22, 14, 14, 30]
    L(row(['输入', 'Map I 弹性', 'Map II 弹性', '说明'], W))
    L('  ' + '-' * 88)
    d0 = d_m(D_ZHAO)
    w0 = 0.291472131
    m0 = M0
    e = 1e-6

    def el2(mk):
        return (mk(e).solve_s(w0) - mk(-e).solve_s(w0)) / (2 * e)

    rows = [
        ('r_m（流量比）', '%.4f' % (1 + d0), '0（不进入）', 'Map I 里是主项'),
        ('d（长度比）', '%.4f' % (4.0 / 3.0 * (1 + d0)), '%.4f' % el2(
            lambda t: V.Model(D_ZHAO * math.exp(t), 0.5, HR, QR_DECL, N_IDX)),
         'Map I 正、Map II 负，符号相反'),
        ('lambda（路径长）', '0（不进入）', '%.4f' % el2(
            lambda t: V.Model(D_ZHAO, 0.5 * math.exp(t), HR, QR_DECL, N_IDX)),
         '只通过 c=lambda/d 进 Map II'),
        ('Q_R', '%.4f' % (-1.0 / 3.0 * (1 + d0)), '%.4f' % el2(
            lambda t: V.Model(D_ZHAO, 0.5, HR, QR_DECL * math.exp(t), N_IDX)),
         'Map II 里几乎不敏感'),
        ('n', '0（不进入）', '%.4f' % el2(
            lambda t: V.Model(D_ZHAO, 0.5, HR, QR_DECL, N_IDX * math.exp(t))),
         'Map II 里比 d 更敏感'),
    ]
    for r in rows:
        L(row(list(r), W))
    L('')
    L('  （Map II 弹性取 w=%.6f、delta=0、d=lambda=0.5 处的中心差分）' % w0)
    L('  => 上一轮 Morris 说「w 稳居第一」，那是 Map II 的结论；')
    L('     而在 Map I（赵案真正在做的事）里 w 根本不是输入。两者不矛盾，但必须标图名。')


# ================================================================ [C]
def section_resolution():
    sec('C', '★ 主结果：D_m 的输入分辨率')
    d0 = d_m(D_ZHAO)
    L('  赵案现值：r_m = %.9f, d = %.4f, Q_R = %.9f, H_R = %.2f'
      % (RM, D_ZHAO, QR_DECL, HR))
    L('            R_id = %.9f   D_m = %+.9f%%' % (r_id(D_ZHAO), 100 * d0))
    L('  可观测量只有四个，D_m 是它们的显式函数，不需要求根。')
    L('')
    W = [16, 12, 24, 30]
    L(row(['输入', '弹性 dD/dln', '1 pp 预算所需精度', '备注'], W))
    L('  ' + '-' * 86)
    table = [
        ('r_m 流量比', 1.0, '0.97%', '表5 两位有效数字已是 0.05%'),
        ('d 长度比', 4.0 / 3.0, '0.73%', '只能由均匀缩放推'),
        ('A_R 面积比', 2.0 / 3.0, '1.46%', '净流道，最不确定的一项'),
        ('Q_R 功率比', -1.0 / 3.0, '2.92%', '两表口径差 2%，见 [E]'),
        ('H_R 高度比', -1.0 / 3.0, '2.92%', '表3 直给 2/1'),
    ]
    for nm, el, need, note in table:
        L(row([nm, '%+.4f' % (el * (1 + d0)), need, note], W))
    L('')
    L('  「1 pp 预算」= 允许 D_m 有 1 个百分点的不确定度时，该输入需要准到多少。')
    L('  这不是误差传播练习，它直接给出实验/设计侧的可交付要求：')
    L('    要做 3% 级别的失真判定，净流通面积比必须准到 1.5% 以内。')
    L('')
    L('  反过来说，D_m = 0 的临界值（把单个输入放开、其余不动）：')
    W2 = [14, 16, 16, 14]
    L(row(['输入', '现值', '使 D_m=0', '相对变化'], W2))
    L('  ' + '-' * 68)
    d_z = bisect(lambda x: d_m(x), 0.45, 0.55)
    a_z = bisect(lambda x: d_m(math.sqrt(x)), 0.20, 0.30)
    q_z = bisect(lambda x: d_m(D_ZHAO, x), 5.0, 7.0)
    for nm, base, zero in (('d 长度比', D_ZHAO, d_z),
                           ('A_R 面积比', D_ZHAO ** 2, a_z),
                           ('Q_R 功率比', QR_DECL, q_z)):
        L(row([nm, '%.6f' % base, '%.6f' % zero, '%+.3f%%' % (100 * (zero / base - 1))], W2))
    L('')
    L('  => 净流通面积比偏小 4.17%（0.2500 -> 0.2396），+2.88% 的失真就归零。')
    L('     物理上这意味着：若台架流道未按几何比例缩（例如堆芯棒径保持原型值），')
    L('     名义上的"相似"就不再是真相似，观测到的偏差会全部被输入假设吸收。')
    L('     换句话说：该案例声称的失真量级，与它自身输入的不确定度同阶。')
    L('     这不是坏消息 —— 它把「测不准」换成了「要测到多准」，是可交付的结论。')


# ================================================================ [D]
def section_kappa():
    sec('D', 'kappa = 0.9987384 的身份：它就是 Q_R 的取整比')
    kap = QR_TAB / QR_DECL
    L('  Q_R(表3 印数 10/1.77) / Q_R(脚本声明 4*sqrt2) = %.10f' % kap)
    L('  记忆里记的 kappa                                    = 0.9987384000')
    L('  相对差 = %.2e  （即 7 位有效数字内相同）' % abs(kap - 0.9987384))
    L('')
    L('  Q_R = 4*sqrt2  <=>  Q_M = %.6f MW，表中印作 1.77 MW' % (10.0 / QR_DECL))
    L('  Q_R = 10/1.77  <=>  Q_M = %.6f MW' % 1.77)
    L('  => 4*sqrt2 是「把 1.7678 圆整成 1.77」的另一种写法，两者都符合原文。')
    L('')
    # 恒等式闭合检验
    x = 1.0 + d_m(D_ZHAO)
    T_P, T_M = M0.T_s(1.0), M0.T_s(x)
    cp_R = M0._cp_s(T_M) / M0._cp_s(T_P)
    rho_R = M0._rho_s(T_M) / M0._rho_s(T_P)
    wcal = bisect(lambda w: M0.D_s(w) - d_m(D_ZHAO), 0.0, 1.0)
    G = 1.0 + wcal * (1.0 * M0.f_s(M0.solve_s(wcal)) - 1.0)
    lhs = x ** 3
    L('  恒等式闭合检验（T_P = %.6f K, T_M = %.6f K, w_cal = %.9f）:' % (T_P, T_M, wcal))
    L('    c_p,R = %.12f   rho_R = %.12f   G = K_R = %.12f' % (cp_R, rho_R, G))
    L('    %-14s %-22s %-14s' % ('kappa', 'c_p,R*G/rho_R', '残差'))
    for k in (1.0, 0.9987384):
        rhs = k * cp_R * G / rho_R
        L('    %-14.10f %-22.12f %+.3e' % (k, rhs, rhs - lhs))
    L('')
    L('  => kappa = 1 时残差 6.7e-16（就是浮点噪声）；kappa = 0.9987 时残差 1.4e-3。')
    L('     结论：恒等式的干净形式是 (1+D_m)^3 = c_p,R*K_R/rho_R，没有 kappa。')
    L('     旧记录里的 kappa 是为「R_id 用 4*sqrt2、K_R 用 10/1.77」这种混搭打的补丁，')
    L('     现在两处统一取同一个 Q_R 即可，kappa 应从论文里删掉。')
    L('')
    L('  连带更正：K_R = 1.1125 与 w = 0.370 都不成立。')
    L('    K_R = %.9f（由 D_m 反解，delta=0）' % G)
    L('    w   = %.9f（= (K_R-1)/(f_R-1)，f_R = %.9f）' % (wcal, M0.f_s(M0.solve_s(wcal))))
    L('    1.1125 与 0.370 是 kappa 与 eps_Q 同时压进 K_R 的产物，两项都不该进 K_R。')


# ================================================================ [E]
def section_epsq():
    sec('E', 'eps_Q：表 5 的 (Q, mdot, dT) 自己不闭合')
    def cp(T):
        return 159.0 - 0.0272 * T + 7.12e-6 * T * T

    rows = [('原型', 533.15, 663.16, 540.0, 10.0),
            ('台架', 533.15, 669.85, 92.79, 1.77)]
    Q = []
    W = [10, 12, 12, 16, 16, 12]
    L(row(['', 'T_mean/K', 'c_p', 'Q(能量平衡)/MW', 'Q(设计)/MW', 'eps_Q'], W))
    L('  ' + '-' * 82)
    for nm, t1, t2, md, qd in rows:
        tm = 0.5 * (t1 + t2)
        q = md * cp(tm) * (t2 - t1) / 1e6
        Q.append(q)
        L(row([nm, '%.2f' % tm, '%.3f' % cp(tm), '%.6f' % q, '%.4f' % qd,
               '%+.4f%%' % (100 * (q / qd - 1))], W))
    L('')
    L('  成对：Q_R(能量平衡) = %.9f   声明 Q_R = %.9f   差 %+.4f%%'
      % (Q[0] / Q[1], QR_TAB, 100 * ((Q[0] / Q[1]) / QR_TAB - 1)))
    L('  => 表 5 的出口温度与表 3 的功率不同源：并排使用必然带 2~4% 的口径差。')
    L('     这正是 eps_Q 该管的事，不该混进 delta，也不该混进 K_R。')
    L('')
    L('  三个口径下的同一个 D_m（Map I，d=0.5 不动）：')
    W2 = [30, 14, 16]
    L(row(['Q_R 的来源', 'Q_R', 'D_m'], W2))
    L('  ' + '-' * 62)
    for nm, qr in (('脚本声明 4*sqrt2', QR_DECL),
                   ('表3 印数 10/1.77', QR_TAB),
                   ('表5 能量平衡反算', Q[0] / Q[1])):
        L(row([nm, '%.9f' % qr, '%+.6f%%' % (100 * d_m(D_ZHAO, qr))], W2))
    L('')
    dm_lo, dm_hi = 100 * d_m(D_ZHAO, QR_DECL), 100 * d_m(D_ZHAO, Q[0] / Q[1])
    L('  => D_m 从 %+.4f%% 到 %+.4f%%，跨距 %.3f pp，而且**跨过 3%% 判据**。'
      % (dm_lo, dm_hi, dm_hi - dm_lo))
    L('     「赵案满足 3%」这句话只在「用表 3 功率」这一口径下成立；')
    L('     换成「用表 5 的 (mdot, dT) 反算功率」就不成立。这不是误差，是口径。')


# ================================================================ [F]
def section_band_d():
    sec('F', '3% 可行带对 d 的脆弱性')
    W = [8, 10, 14, 14, 14]
    L(row(['d', 'c=lambda/d', 'w_-', 'w_+', 'D(w=1)'], W))
    L('  ' + '-' * 66)
    for d in (0.45, 0.475, 0.50, 0.525, 0.55):
        m = V.Model(d, 0.5, HR, QR_DECL, N_IDX, delta=0.0)
        wp = bisect(lambda w: m.D_s(w) - 0.03, 0.0, 1.0)
        wm = None
        if m.D_s(0.0) > -0.03:
            wm = '无解'      # D(w=0)=0 恒成立，delta>=0 时永远到不了 -3%
        else:
            wm = '%.6f' % bisect(lambda w: m.D_s(w) + 0.03, 0.0, 1.0)
        L(row(['%.3f' % d, '%.4f' % (0.5 / d), str(wm), '%.6f' % wp,
               '%+.4f%%' % (100 * m.D_s(1.0))], W))
    L('')
    L('  => w_+ 从 0.204（d=0.45）到 0.509（d=0.55），d 偏 10% 使判据松紧差 2.5 倍。')
    L('     delta>=0 时下边界恒为空：D(w=0)=0 是恒等式，不是数值巧合。')
    L('     所以「3% 带」只在 delta<0 时才是双侧的 —— 与 v6 的说法一致，但边界值随 d 动。')


# ================================================================ [G]
def section_c0():
    sec('G', 'c0 的可移植性：它是声明比值的函数，不是几何常数')
    L('  c0 = 1/B，B = (R_id d)^n = (H_R Q_R / d)^(n/3)')
    L('  =>  c0 = (d / (H_R Q_R))^(n/3)')
    L('')
    W = [10, 14, 14, 14]
    L(row(['d', 'B', 'c0', 'c=lambda/d'], W))
    L('  ' + '-' * 54)
    for d in (0.40, 0.45, 0.50, 0.55, 0.60):
        b = (r_id(d) * d) ** N_IDX
        L(row(['%.2f' % d, '%.9f' % b, '%.9f' % (1 / b), '%.4f' % (0.5 / d)], W))
    L('')
    L('  数值稳健性（c0 对三个声明比值的对数弹性，n=0.25）：')
    for nm, el in (('d', N_IDX / 3.0), ('H_R', -N_IDX / 3.0), ('Q_R', -N_IDX / 3.0)):
        L('    %-6s  dln c0/dln = %+.4f   => 该量偏 10%%，c0 只动 %.3f%%'
          % (nm, el, 100 * abs(el) * 0.10))
    L('')
    L('  => c0 的数值很稳（任何单个比值偏 10%，c0 只动 0.83%），')
    L('     但它的**语义**完全依赖声明的 (H_R, Q_R, d, n)。换一个案例就得重算。')
    L('     Xu 标准 CFD 的 c = 0.5/0.616 = %.4f，与赵的 c0 = %.6f 不能直接比：'
      % (0.5 / 0.616, 1 / (r_id(D_ZHAO) * D_ZHAO) ** N_IDX))
    L('     那一案没有给出成对工况，H_R、Q_R 都未声明，因此它的 c0 本身无法算出。')
    L('     「KYLIN 落在阈值哪一侧」在现有材料下不可判定 —— 这一条复核是对的。')


# ================================================================ [H]
def section_mu():
    sec('H', '物性标签缺陷：mu 的函数形式被硬编码')
    def mu_exp(T):
        return 4.94e-4 * math.exp(754.1 / T)

    def mu_pol(T):
        return 4.56e-3 - 7.03e-6 * T + 3.61e-9 * T * T

    L('  Model._mu_s 的实现是  m0*exp(m1/T)，与 Props 里传什么无关：')
    L('    标量路径 T_s / f_s / M_s 全部走这一支 => P_ZHAO 名字叫「Zhao 表4」，')
    L('    mu 用的却是 X26 式(15) 的指数式。Z20 表4 的多项式从未生效。')
    L('')
    L('  两式的差别（同一温度点）：')
    W = [10, 14, 14, 12]
    L(row(['T/K', 'mu(指数)', 'mu(多项式)', '相对差'], W))
    L('  ' + '-' * 54)
    for T in (533.15, 596.874422, 598.723261, 663.16):
        L(row(['%.2f' % T, '%.6e' % mu_exp(T), '%.6e' % mu_pol(T),
               '%+.3f%%' % (100 * (mu_pol(T) / mu_exp(T) - 1))], W))
    L('')
    T_P, T_M = M0.T_s(1.0), M0.T_s(1.02876835)
    L('  该模型实际用到的只有比值 mu_R = mu(T_M)/mu(T_P)，T_P=%.4f, T_M=%.4f：'
      % (T_P, T_M))
    L('    指数式 mu_R = %.9f   多项式 mu_R = %.9f   差 %+.4f%%'
      % (mu_exp(T_M) / mu_exp(T_P), mu_pol(T_M) / mu_pol(T_P),
         100 * ((mu_pol(T_M) / mu_pol(T_P)) / (mu_exp(T_M) / mu_exp(T_P)) - 1)))
    L('    => f_R 差约 %.4f%%，经 dD/df_R ~ w/3 折算，D_m 差约 %.4f pp。'
      % (100 * (N_IDX * ((mu_pol(T_M) / mu_pol(T_P)) / (mu_exp(T_M) / mu_exp(T_P)) - 1)),
         100 * (1 + d_m(D_ZHAO)) / 3.0 * 0.291472131 /
         (1 + 0.291472131 * (M0.f_s(M0.solve_s(0.291472131)) - 1.0)) *
         N_IDX * ((mu_pol(T_M) / mu_pol(T_P)) / (mu_exp(T_M) / mu_exp(T_P)) - 1) * 1.3))
    L('')
    L('  => 数值上无关紧要（百分之几 pp 的千分之一），但**标签必须改**：')
    L('     论文里若写「物性取自文献原表」，而实际用的是另一篇的 mu 形式，就是 C-05 违规。')
    L('     正确写法：「rho、c_p 取 Z20 表4；mu 取 X26 式(15)，两式 T 标度不同，已核差异 <0.01 pp」。')


# ================================================================ [I]
def section_core():
    sec('I', '新结果：表 5 核心压降的一致性 K_R,core')
    dpP, dpM = 3105.8, 1515.02
    mP_, mM_ = 540.0, 92.79
    TmP, TmM = 0.5 * (533.15 + 663.16), 0.5 * (533.15 + 669.85)
    rho = lambda T: 11096.0 - 1.1944 * T
    rhoR = rho(TmM) / rho(TmP)
    AR = (1.071 / 2.142) ** 2
    vR = (mM_ / mP_) / AR
    K = (dpM / dpP) / (vR * vR * rhoR)
    L('  只用表 5 的四个数与表 3 的核心直径，不需要任何关联式：')
    L('    rho_R = %.9f   A_R(核心) = (1.071/2.142)^2 = %.9f' % (rhoR, AR))
    L('    v_R   = (mdot_M/mdot_P)/A_R = %.9f   动压比 = %.9f' % (vR, vR * vR * rhoR))
    L('    dp_R  = %.9f' % (dpM / dpP))
    L('    => K_R,core = dp_R / 动压比 = %.9f   (delta_core = %+.4f%%)' % (K, 100 * (K - 1)))
    L('')
    Kr_loop = 1.0 + 0.291472131 * (1.0 * M0.f_s(M0.solve_s(0.291472131)) - 1.0)
    L('    回路级 %.9f   核心段 %.9f   核心比回路更接近 1，差 %+.2f%%'
      % (Kr_loop, K, 100 * (K / Kr_loop - 1)))
    L('')
    L('  解释：CFD 在核心段的损失结构几乎等比例保持（3.3% 的偏差），')
    L('        回路级 8.9% 的偏差主要来自核心之外（连接管、换热器、阀门）。')
    L('        这正是 delta 该住的地方 —— 第一次有一个**可核的数值**指向它，')
    L('        虽然仍不是成对局阻本身。')
    L('  限制：表 5 的 dp 标为「堆芯压降」，是否含进出口联箱未说明；')
    L('        核心按多孔介质处理，A_R 用的是 2.142/1.071 两个「直径」，')
    L('        若这两个是容器内径而非净流道，则 K_R,core 会偏小。')


# ================================================================ [J]
def section_envelope():
    sec('J', 'delta 的 Re 包络重定级')
    L('  上一轮写的：0 <= delta <= Re_R^(-0.2) - 1，前提 A1、A2。')
    L('  重定级：')
    W = [8, 30, 12, 34]
    L(row(['前提', '内容', '等级', '为什么'], W))
    L('  ' + '-' * 86)
    L(row(['A1', '两侧同湍流、构件类型与数量相同', 'L4', '这是设计意图，三篇原文都没给清单'], W))
    L(row(['A2', 'K_i(Re) 单调不增、指数 <= 0.2', 'L2', '分离损失比壁面摩擦对 Re 更钝，属关联式性质'], W))
    L('')
    L('  因此这条的等级是「L4 前提 + L2 关联式 = 条件包络」，不是「物理范围」。')
    L('  数值（mu_R 计入后）：')
    W2 = [22, 12, 14, 26]
    L(row(['案例', 'Re_R', 'delta 上端', 'mu 比的口径'], W2))
    L('  ' + '-' * 78)
    # Re = rho v D / mu  =>  Re_R = (1/r_m)(1/d)(mu_P/mu_M)
    mu_ratio_zhao = 1.0 / (4.94e-4 * math.exp(754.1 / 598.723261)) * (4.94e-4 * math.exp(754.1 / 596.874422))
    for nm, r_m, d, mur, note in (
            ('赵 2020 成对 CFD', RM, 0.5, mu_ratio_zhao, '由模型自身温度场'),
            ('赵（表5 温度口径）', RM, 0.5, 1.007118, '由表5 平均温度'),
            ('KYLIN 标准 CFD', 1 / 0.268, 0.616, 1.0, '温度场未建模，取 1')):
        ReR = (1.0 / r_m) * (1.0 / d) * mur
        L(row([nm, '%.4f' % ReR, '%.4f%%' % (100 * (ReR ** -0.2 - 1)), note], W2))
    L('')
    L('  A1 一旦不成立（台架多装一台流量计、少一个弯头），上端立刻失去意义。')
    L('  所以正文明写：「在构件逐项对应的前提下，delta 不超过 X%」。')
    L('  这比「delta 未知」有用，比「delta = +-7%」诚实。')


# ================================================================ [K]
def section_verdict():
    sec('K', '可写 / 不可写')
    L('  可写（本轮之后仍成立）：')
    L('    · D_m 是数据归约量：只依赖四个比值，与 w、delta 无关 [B][C]')
    L('    · 输入分辨率表：要支撑 1 pp，面积比须准到 1.46% [C]')
    L('    · 恒等式不含 kappa，K_R = 1.088839、w = 0.291472 [D]')
    L('    · 3% 带在 delta>=0 时只有上边界，且 w_+ 随 d 大幅移动 [F]')
    L('    · 核心段 K_R = 1.03295，残差主要在核心之外 [I]')
    L('    · delta 的条件包络（A1 明写为设计意图）[J]')
    L('')
    L('  不可写：')
    L('    · 「赵案实测失真 2.88%」——它是 CFD，且口径换成表5 反算即 3.61% [E]')
    L('    · 「KYLIN 降高度 c=0.5 落在失效区」——c=0.5 是我构造的情景 [G]')
    L('    · 「K_R = 1.1125 / w = 0.370」——含 kappa 与 eps_Q [D]')
    L('    · 「delta 的物理范围」——不存在，只有条件包络 [J]')
    L('    · 「物性取自 Zhao 表4」——mu 形式其实来自 X26 [H]')
    L('')
    L('  下一步只剩三件有用的事：')
    L('    1) 拿 Li 2015 / Yue 2017 全文，补逐段阻力与功率矩阵（唯一能升级 delta 的路径）')
    L('    2) 用表 5 的 (mdot, dT) 反算功率作为第二口径，把 3.61% 一并报出')
    L('    3) 把输入分辨率表写进正文 —— 它是本轮唯一新增的可交付设计判据')


def main():
    section_grading()
    section_two_maps()
    section_resolution()
    section_kappa()
    section_epsq()
    section_band_d()
    section_c0()
    section_mu()
    section_core()
    section_envelope()
    section_verdict()
    out = HERE / 'provenance_audit_v8_log.txt'
    out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
    L('')
    L('[日志] %s（%d 行）' % (out.name, len(LOG)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
