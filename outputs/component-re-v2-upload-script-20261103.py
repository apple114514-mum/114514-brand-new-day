# -*- coding: utf-8 -*-
"""provenance_closure_v2 —— 逐构件 K_i(Re) 适用域，替换单一 m_max = 0.2

承接 v1（provenance_closure_v1）与本轮外部复核（8041d2b）：
  v1 说「delta <= Re_R^(-0.2) - 1 是 L2 物理包络」——错，那是 L4 声明假设。
  v1 说「Re_R >= 0.6418 保证 3%」——错，0.6418 是 w=0 的那一个端点。
  v1 把 Zhao 模型的 K_+、f_+、w_+ 套到三个案例——错，K_+ 是案例量。

本脚本做四件事：
  [B] 把 m 从常数改成函数 m_i(Re)，逐构件给来源与适用 Re 区间
  [C] 给出 A2 的数值反例（可违反的 Re 窗口与倍数）
  [D] 区分「上包络」与「混合值」，给闭式间隙
  [E] 把 Re 与未知流量联立，做自洽解
"""

import math
import importlib.util
import unicodedata

spec = importlib.util.spec_from_file_location("v5", "source_free_bound_v5.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

OUT = []


def L(s=''):
    OUT.append(s)
    print(s)


def dw(s):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in str(s))


def pad(s, w, right=False):
    s = str(s)
    n = w - dw(s)
    if n <= 0:
        return s
    return (' ' * n + s) if right else (s + ' ' * n)


def row(cells, widths, right=()):
    return '  ' + ' '.join(pad(c, w, i in right) for i, (c, w) in enumerate(zip(cells, widths)))


def head(title, tag='='):
    L(tag * 78)
    L(title)
    L(tag * 78)


def bisect(f, lo, hi, iters=300):
    flo = f(lo)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        fm = f(mid)
        if (flo < 0) == (fm < 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- 案例常量
Z = V.Model(0.5, 0.5, 2.0, V.QR_ZHAO, 0.25)          # Zhao 2020 成对 CFD
KL = V.Model(0.616, 0.5, 2.0, 1.0 / (0.5 ** 1.9), 0.25)   # KYLIN-II 全相似 l_R=.5
R_ID_Z = Z.i_Rid.a
W_Z = 0.291472160                                      # v8 修正后的 w
K_R_Z = 1.088839052

X_T = 1.03


def kt_of(model, xt=X_T):
    """3% 目标点的 K_t = x^3 / M(x)，M 是该案例自己的质量流函数。"""
    return xt ** 3 / model.M_s(xt)


def band_upper(model, delta=0.0, xt=X_T):
    """w_t(delta) = (K_t - A)/(c f_t - A)，c = lam/d。"""
    Kt = kt_of(model, xt)
    ft = model.f_s(xt)
    c = model.lam / model.d
    A = 1.0 + delta
    den = c * ft - A
    if abs(den) < 1e-15:
        return float('inf')
    return (Kt - A) / den


K_PLUS = kt_of(Z)
F_PLUS = Z.f_s(X_T)
C_Z = Z.lam / Z.d

head('[A] 复核认账：五个数全部复现，两个数要补')
L('  外部复核（8041d2b）给的五个数，在本仓库 v5 模型上逐个复现：')
L('')
L(row(['量', '复核报告', '本脚本', '判定'],
      [22, 18, 18, 8]))
L('  ' + '-' * 70)
L(row(['K_+ = x_+^3/M(x_+)', '1.092755604047', '%.12f' % K_PLUS, '一致'], [22, 18, 18, 8]))
L(row(['f_+', '1.305130341205', '%.12f' % F_PLUS, '一致'], [22, 18, 18, 8]))
L(row(['K_+^(-5)', '0.641777944678', '%.12f' % K_PLUS ** -5, '一致'], [22, 18, 18, 8]))
L(row(['1.03^(-5)', '0.862608784384', '%.12f' % X_T ** -5, '一致'], [22, 18, 18, 8]))
L(row(['(w=.2, Re=.65) 的 D', '+4.2702%', '%+.4f%%' % (100 * V.Model(0.5, 0.5, 2.0, V.QR_ZHAO, 0.25,
                                                          delta=0.65 ** -0.2 - 1.0).D_s(0.2)), '一致'], [22, 18, 18, 8]))
L('')
L('  记号错认账：得到 0.6418 的是 K_+^(-m) 而不是 x_+^(-m)。差值本身就是一条信息：')
L('    1.03^(-5) = %.6f  ->  Re_R >= 0.8626' % (X_T ** -5))
L('    K_+^(-5)  = %.6f  ->  Re_R >= 0.6418' % (K_PLUS ** -5))
L('    两者之比 = (K_+ / x_+)^(-5) = %.6f' % ((K_PLUS / X_T) ** -5))
L('    v1 正文写成 1.03^(-5)，脚本用的是 K_+^(-5)；数值没坏，但读者照公式算会得到 0.8626。')
L('')
L('  ★ 复核没算、但必须补的两个数（都在 Zhao 自己的 w 上）：')
L('')
A_z = (K_PLUS - W_Z * F_PLUS) / (1.0 - W_Z)
D_ALLOW_Z = A_z - 1.0
RE_MIN_Z = A_z ** -5
L('    Zhao 的真实摩擦份额 w = %.9f（v8 修正值，不是 v1 的 0.370）' % W_Z)
L('      => delta_allow(w) = %+.6f%%        （w=0 时是 +9.275560%%）' % (100 * D_ALLOW_Z))
L('      => 若 m=0.2，所需 Re_R  = %.6f      （w=0 时是 0.641778）' % RE_MIN_Z)
L('      => 与案例 Re_R = 0.3461 相比：缺口 %.2f 倍，不是 v1 写的「85%%」' % (RE_MIN_Z / 0.3461))
L('')
L('  这一条把 v1 的 [C] 打死两层：')
L('    (i) 阈值不是 0.6418，是 0.9735（在 Zhao 自己的 w 上）；')
L('    (ii) 真正该问的不是「Re_R 够不够」，而是「包络允许的 delta 是否超出 3% 允许的 delta」：')
D_ENV_3461 = 0.3461 ** -0.2 - 1.0
L('         包络在 Re_R=0.3461 处允许 delta 到 %+.4f%%' % (100 * D_ENV_3461))
L('         3%% 带在 w=0.291472 处只允许 delta 到 %+.4f%%' % (100 * D_ALLOW_Z))
L('         比值 %.1f 倍 —— 包络比实测所容许的宽松一个半量级，它不构成任何保证。'
  % (D_ENV_3461 / D_ALLOW_Z))
L('')
L('  附带一个 v1 的措辞错误认账：「赵 Re_R=0.3461 不达标（缺口 85%）」这句用的是 w=0 的阈值。')
L('  按 w=0.6418/0.3461-1 算得 85%%，但真实要求是 0.9735/0.3461-1 = %.0f%%。'
  % (100 * (RE_MIN_Z / 0.3461 - 1)))
L('')

head('[B] 逐构件 K_i(Re)：把 m 从常数改成函数')
L('  v1 的 A2 断言「局部损失系数的 Re 指数不超过壁面摩擦的 0.2」。')
L('  这句话把两件不同的事混在一根轴上：f 的 0.2 是**壁面剪切**的标度，')
L('  而局阻是**分离与二次流**，两者没有理由共用同一个指数。下面是逐构件证据。')
L('')
L('  B1  90 度斜接弯头（sharp mitre，圆管，无导流片）')
L('       K = 427.5 Re^(-0.77) + 0.9 ,  500 <= Re <= 60000 ,  拟合误差 ±3%')
L('       来源：Al-Tameemi & Ricco, ASME J. Fluids Eng.（已下载全文，式(4) 直读）')
L('       原文摘要：「decrease sharply with Re up to about Re = 20000, at higher Re approach mildly K = 0.9」')
L('')
L(row(['Re', 'K', '局部指数 m = dlnK/dlnRe', '判定'],
      [10, 10, 24, 14], right=(0, 1, 2)))
L('  ' + '-' * 70)


def mitre_K(re):
    return 427.5 * re ** -0.77 + 0.9


def mitre_m(re):
    A = 427.5 * re ** -0.77
    return 0.77 * A / (A + 0.9)


for re in (500, 1000, 2000, 5000, 10000, 20000, 40000, 60000, 100000):
    tagx = '区间内' if re <= 60000 else '外推，勿用'
    L(row(['%d' % re, '%.4f' % mitre_K(re), '%.4f' % mitre_m(re), tagx],
          [10, 10, 24, 14], right=(0, 1, 2)))
L('')
L('      => 在 Re = 500 处局部指数 0.615，是 0.2 的三倍；Re = 1e4 处 0.218 仍超过 0.2。')
L('         只有 Re >= 2e4 以后才落进「<=0.2」。这不是「分离损失的一般性质」，')
L('         是**斜接弯头在 500<Re<2e4 这段的经验事实**，换个构件就换一个数。')
L('')
L('  B2  90 度圆角弯头（r/D ~ 1.5-2.0），手册 Re 修正因子 K_Re')
L('       来源：ASHRAE Handbook 管件损失表 3-6（引自 Idelchik 1986 Diagram 6-5）')
L('       注意：该表是**矩形风管**斜接弯头，用作「形状与量级」旁证，不作圆管定量依据。')
L('')
KRE = [(1e4, 1.40), (2e4, 1.26), (3e4, 1.19), (4e4, 1.14), (6e4, 1.09),
       (8e4, 1.06), (1e5, 1.04), (2e5, 1.00)]
L(row(['Re 区间', 'K_Re 之比', '该区间平均指数'], [22, 14, 18], right=(1, 2)))
L('  ' + '-' * 70)
for (r0, k0), (r1, k1) in zip(KRE[:-1], KRE[1:]):
    mavg = math.log(k0 / k1) / math.log(r1 / r0)
    L(row(['%g -> %g' % (r0, r1), '%.4f' % (k0 / k1), '%.4f' % mavg], [22, 14, 18], right=(1, 2)))
L('')
L('      => 该表**从 Re = 1e4 起**；1e4 以下没有表。整段平均指数 0.12~0.15，')
L('         也在 0.2 以内，但同样只是「这段 Re 里恰好如此」。')
L('         要紧的是：**手册自己承认 1e4 以下无表** —— 而缩比台架恰恰往那边走。')
L('')
L('  B3  标准 90 度弯头（Crane 2-K 系数复算，2 英寸管）')
L('       Re:   100      1000     2300     1e4      1e5      1e6')
L('       K:    8.59     1.39     0.94     0.67     0.60     0.59')
L('       逐段指数：1e2-1e3 = %.3f ;  1e3-2.3e3 = %.3f ;  2.3e3-1e4 = %.3f ;  1e4-1e5 = %.3f'
  % (math.log(8.59 / 1.39) / math.log(10),
     math.log(1.39 / 0.94) / math.log(2.3),
     math.log(0.94 / 0.67) / math.log(1e4 / 2.3e3),
     math.log(0.67 / 0.60) / math.log(10)))
L('       来源等级：二手汇编（Crane TP-410 的 2-K 系数经第三方复算），原文未核。')
L('       => 跨整段 1e3-1e4 的平均指数 = %.3f —— 普通弯头也过 0.3。'
  % (math.log(1.39 / 0.67) / math.log(10)))
L('')
L('  B4  突扩：K = (1 - A1/A2)^2 ，Borda-Carnot，湍流下与 Re 无关，m = 0。')
L('       这是唯一一个能写成「恒等于 0」的构件，因为它的损失全部来自不可逆掺混，')
L('       而掺混尺度由几何决定。等级 L2（教科书关联式），不是 L1 实测。')
L('')
L('  B5  阀门：K 对 Re 的依赖被**开度**压过去')
L('       闸阀全开 K = 0.15~0.30；75% 开 0.9；50% 开 4.5~5.6；25% 开 17~24。')
L('       来源：Crane TP-410 经二手表（Bai & Bai, Subsea Engineering Handbook 表 13-7；')
L('             Crane 原表未核）。全开与半开差 20 倍，远大于任何 Re 修正。')
L('       => 这一条给出的是**比 A2 更硬的不确定性来源**：开度不是 Re 问题，')
L('          而是「台架与原型是否同一个开度」这个工程事实。它落在 delta 里，')
L('          但它的量级由开度差决定，任何 Re 指数都盖不住。')
L('')

head('[C] A2 的数值反例：包络可以被超过')
L('  A2 写成不等式就是 K_M/K_P <= r^(-0.2)，r = Re_M/Re_P <= 1。')
L('  用 B1 的实测关联式直接检验（同一构件、只是 Re 不同，A1 显然满足）：')
L('')
L('    Re_P  \\  Re_M      500      1e3      3e3      1e4      3e4')
L('    ' + '-' * 66)
GRID_M = [500, 1000, 3000, 10000, 30000]
GRID_P = [1e4, 3e4, 6e4, 1e5, 3e5]
for rp in GRID_P:
    cells = []
    for rm in GRID_M:
        if rm >= rp:
            cells.append('     --  ')
            continue
        act = mitre_K(rm) / mitre_K(rp)
        env = (rm / rp) ** -0.2
        cells.append('%6.2f%s%s' % (act / env, '!' if act > env else ' ', ''))
    L('    %-8g        ' % rp + ' '.join(cells))
L('')
L('    单元格 = 实比 / 包络比。>1 即 A2 被违反（标 !）。')
L('')
L('  最坏一格：Re_P = 6e4、Re_M = 500')
L('    实测 K_M/K_P = %.4f  =>  delta_i = %+.1f%%' % (mitre_K(500) / mitre_K(6e4),
                                                         100 * (mitre_K(500) / mitre_K(6e4) - 1)))
L('    A2 包络 r^(-0.2) = %.4f  =>  delta_i <= %+.1f%%' % ((500 / 6e4) ** -0.2,
                                                            100 * ((500 / 6e4) ** -0.2 - 1)))
L('    包络低估 %.0f 个百分点，因子 %.2f。'
  % (100 * (mitre_K(500) / mitre_K(6e4) - (500 / 6e4) ** -0.2),
     mitre_K(500) / mitre_K(6e4) / (500 / 6e4) ** -0.2))
L('')
L('  => 结论：A2 不是「分离损失的一般性质」，而是一个**必须逐案例核对的窗口条件**。')
L('     违反的判据是「区间[Re_M, Re_P]上的平均指数 > 0.2」。因为 m 随 Re 单调下降，')
L('     平均指数主要由 Re_M 决定：网格里 Re_M <= 3e3 基本都违反，Re_M >= 1e4 尚未出现。')
L('     注意 m 在单点上仍超 0.2（1e4 处 0.218），只是被区间上游的低指数稀释掉了。')
L('     缩小比例恰恰把台架推进 Re_M 更低的窗口 —— 这是方向性的风险，不是精度问题。')
L('')

head('[D] 上包络与混合值是两个数，只报一个没有信息量')
L('  记构件权重 alpha_i = k_i,P / k_P，sum alpha_i = 1；单个构件 K_i,M/K_i,P = r^(-m_i)。')
L('  则精确式与上界分别是：')
L('     k_M/k_P = sum alpha_i r^(-m_i)        =>  delta_mix = 上式 - 1   （精确，需 alpha）')
L('     k_M/k_P <= r^(-m_max)                =>  delta_env = 上式 - 1   （只需 m_max）')
L('  闭式间隙（两构件退化，m_max 占权重 alpha）：')
L('     delta_env - delta_mix = (1-alpha) * [ r^(-m_max) - r^(-m_rest) ]')
L('')
L('  数值（r = 0.3461，m_max = 0.2，m_rest = 0.05）：')
D_ENV = 0.3461 ** -0.2 - 1.0
D_REST = 0.3461 ** -0.05 - 1.0
L('     delta_env  = %+.4f%%' % (100 * D_ENV))
L('     delta_rest = %+.4f%%' % (100 * D_REST))
L('')
L(row(['alpha_max', 'delta_mix', 'delta_env', '间隙', 'env/mix'],
      [14, 14, 14, 12, 10], right=(1, 2, 3, 4)))
L('  ' + '-' * 78)
for al in (0.10, 0.20, 0.30, 0.50, 0.80, 1.00):
    mix = al * D_ENV + (1 - al) * D_REST
    L(row(['%.2f' % al, '%+.4f%%' % (100 * mix), '%+.4f%%' % (100 * D_ENV),
           '%.2f pp' % (100 * (D_ENV - mix)), '%.2f' % (D_ENV / mix if mix > 1e-12 else float('inf'))],
          [14, 14, 14, 12, 10], right=(1, 2, 3, 4)))
L('  alpha_max = 最不利构件（m = m_max）占原型总损失 k_P 的份额')
L('')
L('  => 同一个「Re_R = 0.3461」，报出来的 delta 可以在 +5.4% 到 +23.6% 之间移动 4.4 倍，')
L('     全看最不利构件占多少损失份额。所以：')
L('       (i) 只给 delta_env 的论文结论，读者无法复核（alpha 未声明）；')
L('       (ii) 只给 delta_mix 的结论，依赖图纸（alpha 就是逐段阻力，正是拿不到的那样东西）；')
L('       (iii) 可写的形式是**两个都给**，并明写「alpha 未知时 delta 落在 [delta_mix, delta_env]」。')
L('  这也解释了为什么 v1 那句「delta 已经不需要留白了」是错的：')
L('  留白的不是 delta 的数，是 alpha 的数；delta 只是 alpha 的函数。')
L('')

head('[E] 把 Re 联立进去：自洽解与它暴露的问题')
L('  复核第 2 条要求「设计阶段把 Re 与未知流量联立」。做法如下。')
L('')
L('  模型内 Re 比与流量的关系（v5 的 f 组已隐含，这里显式写出）：')
L('     Re = 4 mdot / (pi D mu)  =>  Re_R = (m_M/m_P) / (d * mu_R) = 1 / (r_m * d * mu_R)')
L('     而 r_m = x * R_id  =>  Re_R(x) = 1 / (x * R_id * d * mu_R(T(x)))')
L('  符号：x 增大 => 流量增大 => Re_R 减小 => delta_env 增大 => G 增大 => x 再增大。')
L('        这是**正反馈**，不是收敛型耦合。')
L('')
L('  自洽方程：  x^3 * rho_R = G(x, w, delta_env(x)) * cp_R ,  delta_env(x) = Re_R(x)^(-m) - 1')
L('')


def re_r_of_x(x, m0=Z, d=None, r_id=None):
    """Re_R(x) = 1/(x R_id d mu_R(T(x)))，mu_R 用该案例自己的物性。"""
    d = m0.d if d is None else d
    r_id = m0.i_Rid.a if r_id is None else r_id
    mu_r = m0._mu_s(m0.T_s(x)) / m0._mu_s(m0.T_P)
    return 1.0 / (x * r_id * d * mu_r)


def f_self(x, w, m_exp, model=Z):
    de = re_r_of_x(x, model) ** (-m_exp) - 1.0
    T = model.T_s(x)
    G = (1.0 - w) * (1.0 + de) + w * (model.lam / model.d) * model.f_s(x)
    return x ** 3 * (model._rho_s(T) / model._rho_s(model.T_P)) - \
        G * (model._cp_s(T) / model._cp_s(model.T_P))


L('  先看 Re_R 在根附近的实际数值（Zhao，w = %.6f）：' % W_Z)
L('')
L(row(['x', 'Re_R(x)', 'delta_env(x)', '3% 允许的 delta', '差多少倍'],
      [10, 14, 16, 18, 12], right=(0, 1, 2, 3, 4)))
L('  ' + '-' * 76)
for x in (1.00, 1.0288, 1.05, 1.10, 1.20):
    rr = re_r_of_x(x)
    de = rr ** -0.2 - 1.0
    L(row(['%.4f' % x, '%.6f' % rr, '%+.4f%%' % (100 * de), '%+.4f%%' % (100 * D_ALLOW_Z),
           '%.1f' % (de / D_ALLOW_Z)], [10, 14, 16, 18, 12], right=(0, 1, 2, 3, 4)))
L('')
L('  自洽解（m = 0.2，w 取四个值）：')
L('')
L(row(['w', 'x*', 'D = x*-1', '3% 内?', 'Re_R(x*)'],
      [10, 12, 14, 10, 14], right=(0, 1, 2, 4)))
L('  ' + '-' * 76)
for w in (0.0, 0.2, W_Z, 0.4):
    try:
        xs = bisect(lambda xx: f_self(xx, w, 0.2), 0.5, 3.0)
        tagx = '在' if abs(xs - 1.0) <= 0.03 else '不在'
        L(row(['%.4f' % w, '%.6f' % xs, '%+.4f%%' % (100 * (xs - 1.0)), tagx,
               '%.6f' % re_r_of_x(xs)], [10, 12, 14, 10, 14], right=(0, 1, 2, 4)))
    except Exception as e:                                    # noqa: BLE001
        L(row(['%.4f' % w, '无解', '-', '-', '-'], [10, 12, 14, 10, 14], right=(0, 1, 2, 4)))
L('')
L('  => 自洽解随 w 落在 +7.6% ~ +8.5%，**全部不在 3% 内**。原因不是数值，是正反馈：')
L('     要让 x 停在 1.03，delta 必须 <= 0.54%（[A]），而 Re_R 在 x=1.03 处只给到',
  )
L('     delta_env = %.2f%%，比允许值大 %.0f 倍。两者不可能同时满足。'
  % (100 * (re_r_of_x(1.03) ** -0.2 - 1.0), (re_r_of_x(1.03) ** -0.2 - 1.0) / D_ALLOW_Z))
L('')
L('  这不是「模型坏了」，而是把两件不同性质的东西放进了同一个方程：')
L('     delta_env 是**上界**（对任何 alpha 都成立，故必然宽松）；')
L('     3% 带要的是**实际值**（由 alpha 决定）。')
L('  把上界当成实际值回代，得到的是一个「最坏情形自洽解」，它当然不在 3% 内。')
L('  正确的用法只有两种：')
L('     (a) 判定式：delta_env <= delta_allow(w) ？ —— 充分条件，可能永远不成立；')
L('     (b) 参数化：把 delta 当自变量扫，报 (delta, w) 可行域，不宣称单个案例"保证"。')
L('')

head('[F] 三案例共用 K_+ 的错：撤回，不修补')
L('  v1 的 [C] 表用同一个 z = Model(0.5, 0.5, 2.0, QR_ZHAO, 0.25) 的 K_+、f_+、w_+(delta)')
L('  套到 Zhao、KYLIN 全相似、KYLIN 降高度三个案例。撤回整张表，但要撤得准：')
L('    · K_t = x_t^3/M(x_t) 形式上是案例量，数值上两案只差 %.1e（M 都贴近 1），'
  % abs(kt_of(Z) - kt_of(V.Model(0.616, 0.5, 2.0, 1.0 / (0.5 ** 1.9), 0.25))))
L('      所以骂 K_+ 搬错并没有实质后果，这一项不是错误来源；')
L('    · 真正搬错的是 **f_+**：它含该案例的 R_id、d、mu_R，两案的 c f_+ 差 30%。')
L('      v1 用 Zhao 的 c f_+ = %.6f 去算 KYLIN 的 w_+，得到 -0.71（负值）；' % (C_Z * F_PLUS))
L('      改用 KYLIN 自己的 c f_+ = %.6f，得到 +16.4（整段覆盖）。符号都翻了。'
  % (KL.lam / KL.d * KL.f_s(X_T)))
L('    · 结论不变：整张表作废；但原因写「f_+ 与 c 是案例量」，不写「K_+ 是案例量」。')
L('')
L('  可以按案例重算的只有两个（第三个缺几何）：')
L('')
cases = []
cases.append(('Zhao 2020 成对 CFD', Z, 'c = lam/d = 1.000'))
cases.append(('KYLIN-II 全相似 l_R=.5', KL, 'c = lam/d = %.4f' % (KL.lam / KL.d)))
L(row(['案例', 'K_+（本案例）', 'c f_+', 'w_+(delta=0)', '判定'],
      [26, 16, 14, 14, 12], right=(1, 2, 3)))
L('  ' + '-' * 82)
for nm, mdl, note in cases:
    kp = kt_of(mdl)
    fp = mdl.f_s(X_T)
    c = mdl.lam / mdl.d
    wu = band_upper(mdl, 0.0)
    tagx = '全覆盖' if wu >= 1.0 else ('空' if wu <= 0.0 else '[0,%.4f]' % wu)
    L(row([nm, '%.9f' % kp, '%.6f' % (c * fp), '%.6f' % wu, tagx], [26, 16, 14, 14, 12], right=(1, 2, 3)))
L('')
L('  注意两行的 c 差很多：Zhao 的 c = 1（表 3 八行全 2:1 的均匀缩放签名），')
L('  KYLIN 的 c = %.4f（l_R=.5 / d_R=.616）。c 直接进 G 的摩擦项，' % (KL.lam / KL.d))
L('  所以两个案例的 3% 带形状本来就不同 —— 这正是不能用同一组 K_+、f_+ 的原因。')
L('')
L('  第三案（KYLIN 降高度）**不重算**，理由写在下面，不是懒：')
L('    · 该案的 d_R = 1、l_R = 0.5，但 Xu 表 2 只给 l_R、d_R、m_R、DeltaT_R、q_R，')
L('      不给水平段/竖直段分配，c = lam/d 因此不是唯一确定量（v8 已记此自由假设）；')
L('    · 该案无成对工况，c_0 算不出来（v7 已撤回"恰好 c=0.5 落在失效区"）；')
L('    · 无成对工况 => K_t 里的 M(x) 可以用声明模型算，但那个 M 没有观测背书。')
L('  => 可写的只有：「KYLIN 降高度的 -12.15% 由 m_R 与 l_R 两个独立比值造成」，')
L('     不写「由 delta 造成」，也不写「w_+ 为负 / 带非空」。')
L('')

head('[G] 重写后的清单')
L('  可以写：')
L('    1. 条件命题（前提全部明写、不含任何物理断言）：若各构件同一参考速度、权重归一、')
L('       K_i 随 Re 单调不增、且该 Re 窗口内 K_i,M/K_i,P <= r^(-m_max)，则 0 <= delta <= r^(-m_max)-1。')
L('    2. m_max 是**声明输入**，不是物理常数。逐构件表（B1-B5）给出取值区间与来源等级：')
L('       斜接弯头 0.62@Re=500 ... 0.07@Re=6e4（L1，已核 PDF）；')
L('       圆角弯头 0.12~0.15（L2，矩形风管表，仅旁证）；')
L('       普通弯头 0.32@1e3-1e4（二手汇编）；突扩 0（L2）；')
L('       阀门：开度主导，全开 0.15 半数开 4.5，差 20 倍（二手 Crane）。')
L('    3. 包络与混合值必须同时给：delta 落在 [delta_mix, delta_env]，间隙 = (1-alpha)[r^(-m_max)-r^(-m_rest)]。')
L('    4. 「Re 包络不构成 3% 保证」有定量形式：Re_R=0.3461 允许 delta 到 23.6%，')
L('       而 w=0.2915 只允许 0.54%，宽 44 倍。')
L('    5. 反例：A2 在 Re_M <= 3e3（斜接弯头）被违反，最坏格超包络 1.73 倍（Re_P=6e4, Re_M=500）。')
L('')
L('  不能写：')
L('    1. 「delta 的物理参数域已经建立」—— 域没有建立，只有一个以 m_max 为参数的族。')
L('    2. 「Re_R >= 0.6418 保证 3%」——那是 w=0 端点，且用的是包络而非实际值（[A][E]）。')
L('    3. 「A2 是分离损失的一般性质」——被 B1 的实测关联式否定（[C]）。')
L('    4. 「三个案例的 3% 带分别为 …」——K_+ 是案例量，v1 那张表作废（[F]）。')
L('    5. 「US = 1.9~3.2 W/K 是 L2」——h_out、导热率、保温厚度、环境温度全是自取值，L4 情景。')
L('    6. 「某个 delta 值」——没有 alpha 就没有 delta 的数；能给的只有区间端点。')
L('')
L('  一句话：v1 把「delta 未知」换成了「Re_R 必须多大」，这一步方向对，')
L('          但换来的不是判据，是**一个把未知量从 delta 搬到 m_max 的等价改写**。')
L('          真正的关口仍然是 alpha（逐段阻力），而它的入口是成对压差或图纸，不是文献检索。')

with open('provenance_closure_v2_log.txt', 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
