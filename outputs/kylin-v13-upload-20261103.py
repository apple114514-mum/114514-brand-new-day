# -*- coding: utf-8 -*-
"""closure_v13.py —— Yue 2017 同篇五功率趋势：把缺口拆成三份账，并落成一个可测量

上一轮（v12）的结论是「联合固定闭合解释不了低功率趋势，且不能单独归给
散热 / 阀位 / 摩擦」。这一轮把这句话换成三条可核对的部分：

  [B] 三个候选因子各自能补多少 pp —— 物性几乎为零，阻力有硬上限；
  [C] 阻力上限：要让 K 单独解释，等效 Re 指数须 0.588，Table 2 自带 0.068；
  [D] 剩下必须由热账承担；这个比值是观测量，不需要模型；
  [E] 一个自由参数（恒定热损 L）能覆盖五点，L 的最优值与区间；
  [F] L 的量级检查与外部对照 —— 相容但不构成验证；
  [G] 这条曲线对 (K, eta) 是秩亏的，因此判据必须落在独立量上。

数据来源与定级：
  Fig.4(c) 的四个低功率流量 = 读图（L4 情景，不是仪表值）；
  17.9 kW 的 1.12 kg/s = Yue §5.2 正文直给（L1）；
  Table 2 的 K = 作者理论计算（L1），不是实测；
  功率 4.3/7.6/11.2/15.3/17.9 kW = §4.1 与 Fig.4 标注（L1）。
"""

import math
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = []


def dw(s):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)


def L(s=''):
    print(s)
    LOG.append(s)


def row(cells, widths, right=()):
    out = []
    for i, (c, w) in enumerate(zip(cells, widths)):
        c = str(c)
        pad = max(0, w - dw(c))
        out.append(' ' * pad + c if i in right else c + ' ' * pad)
    return '  '.join(out)


def rule(widths):
    return '  '.join('-' * w for w in widths)


def pct(x, nd=2):
    return ('%+.' + str(nd) + 'f%%') % (100.0 * x)


# ---------------------------------------------------------------- 闭合方程
# 回路：rho*g*beta*dT*H = K*mdot^2/(2*rho*A^2)，dT = P_net/(mdot*cp)
#   =>  mdot^3 = P_net / (K * C * H)，  C = cp/(2*beta*rho^2*g*A^2)
# 注意 C 里没有功率、没有 Re：它是纯物性组合。这一点决定了 [B] 的结论。

A_PIPE = math.pi * 0.026 ** 2 / 4.0        # 5.30929e-4 m^2（Yue Table 1）
G = 9.81


def rho(T):
    return 11096.0 - 1.3235 * T            # X26 式(15)


def beta(T):
    return 1.3235 / rho(T)                 # -(1/rho) drho/dT


def cp(T):
    return 164.8 - 0.0394 * T + 1.25e-5 * T ** 2 - 4.56e5 / T ** 2


def Ccomb(T):
    return cp(T) / (2.0 * beta(T) * rho(T) ** 2 * G * A_PIPE ** 2)


# Yue Table 2（理论计算，L1）：mdot kg/s 与 K_total、K_pipe
TAB_K = [(0.25, 24.5), (0.50, 24.2), (0.75, 23.8), (1.00, 23.3), (1.25, 22.8)]
TAB_KP = [(0.25, 19.1), (0.50, 18.9), (0.75, 18.5), (1.00, 18.1), (1.25, 17.7)]


def itp(tab, m):
    xs = [t[0] for t in tab]
    ks = [t[1] for t in tab]
    if m <= xs[0]:
        return ks[0] + (ks[1] - ks[0]) / (xs[1] - xs[0]) * (m - xs[0])
    for i in range(len(xs) - 1):
        if m <= xs[i + 1]:
            t = (m - xs[i]) / (xs[i + 1] - xs[i])
            return ks[i] + t * (ks[i + 1] - ks[i])
    return ks[-1]


def Kof(m):
    return itp(TAB_K, m)


def Kpof(m):
    return itp(TAB_KP, m)


# Yue Fig.4(c)：四个读图点 + 一个正文直给点
PTS = [(4.3, 0.62), (7.6, 0.82), (11.2, 0.94), (15.3, 1.06), (17.9, 1.12)]
P0, M0 = PTS[-1]
PHI0 = M0 ** 3 * Kof(M0)
READ_STRESS = 0.03


def solve_dp(P, dP, kfn=None):
    """给定净热 P - dP，解 mdot^3 * K(mdot) = PHI0 * (P-dP)/(P0-dP)。"""
    kf = Kof if kfn is None else kfn
    if P - dP <= 0:
        return 0.0
    tgt = PHI0 * (P - dP) / (P0 - dP)
    lo, hi = 1e-6, 3.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if mid ** 3 * kf(mid) < tgt:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


L('=' * 78)
L('closure v13 —— Yue 2017 同篇五功率趋势：三份账与一个可测量')
L('=' * 78)
L()

# ------------------------------------------------------------------ [A]
L('[A] 复现：固定闭合的 0.696 与图读的 0.62')
L()
hdr = ['P kW', '图读 mdot', '固定闭合', '差', 'R=(P/m3)/R0', 'eta0/eta']
wid = [7, 10, 10, 8, 13, 10]
L(row(hdr, wid, right=(0, 1, 2, 3, 4, 5)))
L(rule(wid))
RR = {}
for p, m in PTS:
    pred = M0 * (p / P0) ** (1.0 / 3.0)
    R = (p / P0) / (m / M0) ** 3
    RR[p] = R
    L(row(['%.1f' % p, '%.3f' % m, '%.6f' % pred, '%+.4f' % (m - pred),
           '%.6f' % R, '%.6f' % (1.0 / R)], wid, right=(0, 1, 2, 3, 4, 5)))
L()
L('  固定闭合的 0.696236 与复核一致；4.3 kW 的缺口 -0.076236 kg/s 亦一致。')
L('  即使把图读值人为上移 %.2f kg/s，仍差 %.6f kg/s —— 与复核的 0.046 相符。'
  % (READ_STRESS, 0.696236 - 0.62 - READ_STRESS))
L()
L('  但读图有前提：允许 K 随 mdot 按 Table 2 变，预测会动：')
L()
hdr2 = ['P kW', 'K 一致解', '对图读偏差', '说明']
wid2 = [7, 11, 12, 40]
L(row(hdr2, wid2, right=(0, 1, 2)))
L(rule(wid2))
for p, m in PTS:
    mm = solve_dp(p, 0.0)
    L(row(['%.1f' % p, '%.6f' % mm, pct(mm / m - 1.0, 2),
           'L=0，K(ṁ) 自洽' if p == 4.3 else ''], wid2, right=(0, 1, 2)))
L()
M0K = solve_dp(4.3, 0.0)
GAP0 = 0.696236 - 0.62
GAP1 = M0K - 0.62
L('  4.3 kW 的固定闭合解从 0.696236 落到 %.6f（低流量 K 更大），' % M0K)
L('  缺口从 %.6f 缩到 %.6f —— 方向对，但只吃掉 %.1f%%。' % (
    GAP0, GAP1, 100 * (GAP0 - GAP1) / GAP0))
L()

# ------------------------------------------------------------------ [B]
L('[B] 三个候选因子各能补多少：物性几乎为零，阻力有天花板')
L()
L('  闭合式 mdot^3 = P_net/(K*C*H)，取对数微分：')
L('    dln(mdot) = (1/3)[dln(P_net) - dln K - dln C - dln H]')
L('  要解释 R = %.6f（4.3 相对 17.9），需要括号内累计 -%.6f。' % (RR[4.3], math.log(RR[4.3])))
L()

T_LO, T_HI = 483.0, 633.0     # Fig.4(a) 加热段入口/出口量级（读图，L4）
c_lo, c_hi = Ccomb(T_LO), Ccomb(T_HI)
L('  B1  物性组合 C = cp/(2*beta*rho^2*g*A^2)')
L('      T=%.0f K: cp=%.4f  beta=%.6e  rho=%.2f  C=%.4f' % (
    T_LO, cp(T_LO), beta(T_LO), rho(T_LO), c_lo))
L('      T=%.0f K: cp=%.4f  beta=%.6e  rho=%.2f  C=%.4f' % (
    T_HI, cp(T_HI), beta(T_HI), rho(T_HI), c_hi))
L('      C(低)/C(高) = %.6f —— 变化 %.3f%%。' % (c_lo / c_hi, 100 * (c_lo / c_hi - 1)))
L('      cp 降、rho 降、beta 升三者几乎精确抵消，**LBE 的 C 对温度不敏感**。')
L('      150 K 的温度跨度只给 C 带来 %.3f%% 的变化，折成流量 %.3f%%。'
  % (100 * (c_lo / c_hi - 1), 100 * ((c_lo / c_hi) ** (-1.0 / 3.0) - 1)))
L('      => 物性口径这条解释基本不存在；它连 1% 都补不到。')
L()

L('  B2  有效高度 H')
L('      几何不变，H 只能是 %.4f m（v12 六行反解值）。' % 3.3119)
L('      mdot ∝ H^(-1/3)，故 R = H/H0：要补满缺口需 H = %.4f m。' % (3.3119 * RR[4.3]))
L('      这比反解值高 %.1f%%，且超过 Xu 表 1 给的浮升 3.35 m 与 v12 的 ±0.02 m 区间。'
  % (100 * (RR[4.3] - 1)))
L('      => 排除；H 在单侧闭合里是常数，不是旋钮。')
L()

L('  B3  总阻力 K')
m_lo, m_hi = 0.62, 1.12
Kt_lo, Kt_hi = Kof(m_lo), Kof(m_hi)
Kp_lo, Kp_hi = Kpof(m_lo), Kpof(m_hi)
Kl_lo, Kl_hi = Kt_lo - Kp_lo, Kt_hi - Kp_hi
L('      Table 2 插值：K_total %.4f -> %.4f（%s），K_pipe %.4f -> %.4f' % (
    Kt_lo, Kt_hi, pct(Kt_lo / Kt_hi - 1.0, 2), Kp_lo, Kp_hi))
L('      沿程占 K_total 的 %.2f%%、局阻占 %.2f%%。' % (
    100 * Kp_lo / Kt_lo, 100 * Kl_lo / Kt_lo))
m_tab = math.log(Kt_lo / Kt_hi) / math.log(m_hi / m_lo)
need = math.log(RR[4.3]) / math.log(m_hi / m_lo)
L('      表内等效 Re 指数 m = %.5f；要单独解释趋势需 m = %.5f —— 差 %.1f 倍。'
  % (m_tab, need, need / m_tab))
L()
L('      表内这个指数与 v11 的反解（0.0487~0.068）自洽，但 v11 已查明它是')
L('      Table 2 的口径问题（等效 eps/D=9.5e-3、eps=0.25 mm），**不是物理**。')
L('      所以不能拿表内指数当阻力上限，改从锚点做物理分解：')
L('        K_pipe  = 1 + (K_pipe,hi - 1) * r^(-0.25)       r = mdot/1.12')
L('        K_local = K_local,hi * r^(-m_local)')
L('      以 1.12 kg/s 处的 %.3f / %.3f 为基准往 0.62 kg/s 外推：' % (Kp_hi, Kl_hi))
L()
hdr3 = ['m_local', 'K_pipe', 'K_local', 'K_total', 'K 比', '占 ln(R) 份额']
wid3 = [9, 9, 9, 9, 8, 14]
L(row(hdr3, wid3, right=(0, 1, 2, 3, 4, 5)))
L(rule(wid3))
COVER = {}
for ml_ in (0.25, 0.40, 0.60, 0.77):
    kp_ = 1.0 + (Kp_hi - 1.0) * (m_lo / m_hi) ** (-0.25)
    kl_ = Kl_hi * (m_lo / m_hi) ** (-ml_)
    kt_ = kp_ + kl_
    share = math.log(kt_ / Kt_hi) / math.log(RR[4.3])
    COVER[ml_] = (share, kt_)
    L(row(['%.2f' % ml_, '%.4f' % kp_, '%.4f' % kl_, '%.4f' % kt_,
           '%.4f' % (kt_ / Kt_hi), '%.1f%%' % (100 * share)],
          wid3, right=(0, 1, 2, 3, 4, 5)))
L()
L('      0.77 是 Al-Tameemi-Ricco 2018 弯头关联式 K=427.5Re^-0.77+0.9 的幂次；')
L('      该式只对水/空气、500<=Re<=6e4 成立，套到 KYLIN 的 LBE 上已是越界借用。')
L('      即便借到这个上限，阻力也只解释 R 的 %.0f%% —— **单独不够，但参与得不小**。'
  % (100 * COVER[0.77][0]))
L()
L('  B4  小结（三份账的份额，按 ln 计）')
L('      物性   : %.2f%%     （方向对，但比缺口的量级小两个数量级）'
  % (100 * abs(math.log(c_hi / c_lo)) / math.log(RR[4.3])))
L('      高度   : 0%        （几何约束，非旋钮）')
L('      阻力   : %.0f%%（表内口径）~ %.0f%%（越界上限）'
  % (100 * math.log(Kt_lo / Kt_hi) / math.log(RR[4.3]), 100 * COVER[0.77][0]))
L('      热账   : 剩下的 %.0f%% 或更多' % (100 - 100 * COVER[0.77][0]))
L()
L('  结论的形状：**不是「谁也解释不了」，而是「阻力至多六成，热账至少四成」**。')
L()

# ------------------------------------------------------------------ [C]
L('[C] 三档阻力口径下，热账分别要多少')
L()
L('  对每一档，求恒定热损 L，使 4.3 kW 的闭合解回到图读的 0.62 kg/s。')
L()


def L_for(K_lo, K_hi):
    ratio = (0.62 ** 3 * K_lo) / (m_hi ** 3 * K_hi)
    return (4.3 - ratio * 17.9) / (1.0 - ratio), ratio


hdr_c = ['阻力口径', 'K(0.62)', '需 L kW', 'K 比率', 'eta(4.3)/eta(17.9)']
wid_c = [22, 10, 10, 9, 18]
L(row(hdr_c, wid_c, right=(1, 2, 3, 4)))
L(rule(wid_c))
CASES = [('Table 2 直接插值', Kt_lo)]
for ml_ in (0.25, 0.60, 0.77):
    CASES.append(('物理分解 m_local=%.2f' % ml_, COVER[ml_][1]))
LCASE = {}
for tag, klo in CASES:
    Lv_, ratio_ = L_for(klo, Kt_hi)
    eta_r = (4.3 - Lv_) / 4.3 * 17.9 / (17.9 - Lv_)
    LCASE[tag] = Lv_
    L(row([tag, '%.4f' % klo, '%.4f' % Lv_, '%.4f' % (klo / Kt_hi), '%.4f' % eta_r],
          wid_c, right=(1, 2, 3, 4)))
L()
L('  K 比率 = K(0.62)/K(1.12)；eta 比 = (4.3-L)/4.3 * 17.9/(17.9-L)。')
L('  三档给出 L 从 %.2f 到 %.2f kW —— 阻力借得越狠，需要的热损越小，' % (
    LCASE['物理分解 m_local=0.77'], LCASE['Table 2 直接插值']))
L('  但**任何一档都不能把 L 压到 0**：即使借到越界上限，仍要 %.2f kW 的热账。'
  % LCASE['物理分解 m_local=0.77'])
L()
L('  也就是说：即便阻力取到越界上限，热账仍须让 4.3 kW 的有效效率比 17.9 kW')
L('  低 %.1f%%；若用 Table 2 口径，则低 %.1f%%。' % (
    100 * (1 - (4.3 - LCASE['物理分解 m_local=0.77']) / 4.3 * 17.9 / (17.9 - LCASE['物理分解 m_local=0.77'])),
    100 * (1 - (4.3 - LCASE['Table 2 直接插值']) / 4.3 * 17.9 / (17.9 - LCASE['Table 2 直接插值']))))
L()

# ------------------------------------------------------------------ [D]
L('[D] 这个效率比是观测比值，不需要模型')
L()
L('  在「K、C、H 不变」的前提下，mdot^3 = P_net/(K*C*H) 给出')
L('    eta(P)/eta(P0) = (mdot/mdot0)^3 * P0/P = 1/R')
L('  4.3 kW：1/%.6f = %.6f；7.6 kW：%.6f；11.2 kW：%.6f；15.3 kW：%.6f'
  % (RR[4.3], 1 / RR[4.3], 1 / RR[7.6], 1 / RR[11.2], 1 / RR[15.3]))
L('  这是「K 固定」口径；若 K 按 Table 2 变，4.3 kW 的比值升到 %.4f（见 [C]）。'
  % ((4.3 - LCASE['Table 2 直接插值']) / 4.3 * 17.9 / (17.9 - LCASE['Table 2 直接插值'])))
L()
L('  但这里有个必须说清的口径：**流动的 mdot 本来就是由加热段能量平衡反算的**')
L('  （Yue §5.1）。所以图 (c) 已经把作者隐含的热账吸收进去了 —— 这条曲线对')
L('  eta 的读数，不是对 eta 的**独立测量**，而是对「作者反算口径」的读数。')
L('  这层自指是 v12 就点过的，本轮不改变它。')
L()

# ------------------------------------------------------------------ [E]
L('[E] 一个自由参数：恒定热损 L')
L()
L('  参数化 eta(P) = (P - L)/P，L 与功率无关（辐射+自然对流，壁温变化有限）。')
L('  闭合变成 mdot^3 * K(mdot) = (P - L)/(C*H)，用 17.9 kW 锚定 C*H。')
L()
hdr4 = ['L kW'] + ['%.1f kW' % p for p, _ in PTS] + ['max|res|']
wid4 = [7] + [9] * 5 + [10]
L(row(hdr4, wid4, right=tuple(range(7))))
L(rule(wid4))
for Lv in (0.0, 0.5, 0.8, 1.0, 1.2, 1.4, 1.5, 2.0):
    res = [solve_dp(p, Lv) - m for p, m in PTS]
    L(row(['%.1f' % Lv] + ['%+.3f' % r for r in res] + ['%.4f' % max(abs(r) for r in res)],
          wid4, right=tuple(range(7))))
L()
best = None
Lv = 0.0
while Lv <= 3.0:
    s = sum((solve_dp(p, Lv) - m) ** 2 for p, m in PTS)
    if best is None or s < best[1]:
        best = (Lv, s)
    Lv += 0.0005
L_OPT = best[0]
L('  最小二乘 L = %.3f kW，残差平方和 %.6f：' % (L_OPT, best[1]))
L()
hdr5 = ['P kW', '模型 mdot', '图读 mdot', '残差', '相对']
wid5 = [7, 10, 10, 9, 9]
L(row(hdr5, wid5, right=(0, 1, 2, 3, 4)))
L(rule(wid5))
for p, m in PTS:
    mm = solve_dp(p, L_OPT)
    L(row(['%.1f' % p, '%.6f' % mm, '%.3f' % m, '%+.4f' % (mm - m),
           pct(mm / m - 1.0, 2)], wid5, right=(0, 1, 2, 3, 4)))
L()
L('  五点最大残差 %.2f%%，全部落在读图扰动之内；L=0 时 4.3 kW 差 %.2f%%。'
  % (100 * max(abs(solve_dp(p, L_OPT) / m - 1) for p, m in PTS),
     100 * abs(solve_dp(4.3, 0.0) / 0.62 - 1)))
L()
L('  E1  L 的区间（把 ±%.2f kg/s 当作读图扰动，不是仪表不确定度）' % READ_STRESS)
for mm in (0.62 - READ_STRESS, 0.62 + READ_STRESS):
    lo, hi = 0.0, 4.29
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if solve_dp(4.3, mid) > mm:
            lo = mid
        else:
            hi = mid
    L('      图读 %.2f kg/s -> L = %.4f kW' % (mm, 0.5 * (lo + hi)))
lo, hi = 0.0, 4.29
for _ in range(300):
    mid = 0.5 * (lo + hi)
    if solve_dp(4.3, mid) > 0.62:
        lo = mid
    else:
        hi = mid
L_ONLY = 0.5 * (lo + hi)
L('      只用 4.3 单点定标：L = %.4f kW；五点最小二乘 %.4f kW。' % (L_ONLY, L_OPT))
L('      两者差 %.4f kW，说明 L 不是靠五个点硬凑的 —— 一个点就已经指向同一量级。'
  % abs(L_ONLY - L_OPT))


L()
L('  E1b 插值口径敏感性：Table 2 只有五点，K(mdot) 在两表之间怎么插没有唯一答案')
_xs = [t[0] for t in TAB_K]
_ys = [t[1] for t in TAB_K]
_n = len(_xs)
_sx = sum(math.log(v) for v in _xs)
_sy = sum(math.log(v) for v in _ys)
_sxx = sum(math.log(v) ** 2 for v in _xs)
_sxy = sum(math.log(v) * math.log(w) for v, w in zip(_xs, _ys))
_bp = (_n * _sxy - _sx * _sy) / (_n * _sxx - _sx * _sx)
_ap = math.exp((_sy - _bp * _sx) / _n)


def Kpow(m):
    return _ap * m ** _bp


def mdot_with(kf, P, dP):
    phi0 = m_hi ** 3 * kf(m_hi)
    if P - dP <= 0:
        return 0.0
    tgt = phi0 * (P - dP) / (P0 - dP)
    lo, hi = 1e-6, 3.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if mid ** 3 * kf(mid) < tgt:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


_best = None
_lv = 0.0
while _lv <= 3.0:
    _s = sum((mdot_with(Kpow, p, _lv) - m) ** 2 for p, m in PTS)
    if _best is None or _s < _best[1]:
        _best = (_lv, _s)
    _lv += 0.001
L('      幂律拟合 K = %.4f * mdot^(%.5f)，其下 L(LSQ) = %.4f kW（线性插值 %.4f）。'
  % (_ap, _bp, _best[0], L_OPT))
L('      两者差 %.2f kW，即 %.0f%%。所以 L 的可报精度是「约 1.2~1.4 kW」，'
  % (abs(_best[0] - L_OPT), 100 * abs(_best[0] - L_OPT) / L_OPT))
L('      不是三位小数 —— **这个数只能报到一位小数**。')
L()
L('  E2  等价说法：需要的等效 net-heat 份额')
L('      L=%.2f 时 eta(4.3)=%.4f、eta(17.9)=%.4f；17.9 是锚，故只有比值可读。' % (
    L_OPT, (4.3 - L_OPT) / 4.3, (17.9 - L_OPT) / 17.9))
L('      不要把 eta(4.3)=%.2f 写成「实测热效率」—— 它是把缺口参数化后的等效值。'
  % ((4.3 - L_OPT) / 4.3))
L()

# ------------------------------------------------------------------ [F]
L('[F] 量级检查与外部对照：相容，但不构成验证')
L()
L('  F1  热流密度（保温层外表面，粗糙估算，只为判量级）')
AREA_CASES = [
    ('保守：保温好、附件少', 4.0, 8.0, 10.0),
    ('中性：含换热器/膨胀箱/法兰', 7.5, 10.0, 15.0),
    ('宽松：未保温段多', 10.0, 12.0, 20.0),
]
L()
hdr6 = ['情景', '外表面积 m2', 'h W/m2K', 'dT K', '推算热损 kW']
wid6 = [28, 12, 11, 8, 13]
L(row(hdr6, wid6, right=(1, 2, 3, 4)))
L(rule(wid6))
for tag, a, h, dt in AREA_CASES:
    L(row([tag, '%.1f' % a, '%.1f' % h, '%.0f' % dt, '%.2f' % (a * h * dt / 1000.0)],
          wid6, right=(1, 2, 3, 4)))
L()
L('      推算区间约 0.3~2.4 kW，中性 1.1 kW；拟合值 %.2f kW 落在中位。' % L_OPT)
L('      **这是量级相容，不是验证**：面积、保温热阻、附件数量全是假设，')
L('      而可假设的范围恰好覆盖了拟合值。要定 L，只能实测。')
L()

L('  F2  外部对照：Li 2015 的 24 kW')
L('      Li §3.3 给 24 kW、1.21 kg/s（最大温差且最大阀开度）。用同一条曲线外推：')
for Lv in (0.0, L_OPT, 1.45):
    mm = solve_dp(24.0, Lv)
    L('        L=%.2f -> %.4f kg/s，对 1.21 差 %s' % (Lv, mm, pct(mm / 1.21 - 1.0, 2)))
L('      注意：**L=0 反而更接近 1.21**。所以这个跨论文点不支持 L>0，')
L('      也不否定它 —— 它的阀位（最大开度）与 Yue 五点的阀位关系未知，')
L('      K 不可比。如实记：这一格是空白，不是佐证。')
L()

L('  F3  读图自洽性：图 (b) 与图 (c) 是同一条能量平衡')
L('      若 mdot 确实由 mdot = P/(cp*dT) 反算，则 mdot*cp*dT/P 应恒为 1。')
L('      用图 (b) 平台读数粗核（dT 读图误差 ±5 K，在 45 K 上是 11%）：')
L()
DT = {4.3: 45.0, 7.6: 58.0, 11.2: 72.0, 15.3: 95.0, 17.9: 108.6}
hdr7 = ['P kW', 'mdot', 'dT K', 'mdot*cp*dT/P']
wid7 = [7, 8, 8, 15]
L(row(hdr7, wid7, right=(0, 1, 2, 3)))
L(rule(wid7))
for p, m in PTS:
    t = 500.0
    L(row(['%.1f' % p, '%.2f' % m, '%.1f' % DT[p],
           '%.4f' % (m * cp(t) * DT[p] * 1000.0 / (p * 1e6))], wid7, right=(0, 1, 2, 3)))
L()
L('      注意这不是随机散布而是**系统性偏低 0~11%**：说明我的 dT 平台读数普遍')
L('      取低了一点（每个差 0~5 K，仍在 ±5 K 内）。这恰好是读图误差的直接证据。')
L('      两个结论：① 图 (b)(c) 不能互证（同源）；② 我的读图精度上限约 6%，')
L('      所以 4.3 kW 那个 11% 的缺口只比读图噪声大一倍 —— 不是「铁证」，')
L('      但恒定热损能把残差压到 1.8%，**比读图自洽性还好**，这一点反而支持它。')
L()

# ------------------------------------------------------------------ [G]
L('[G] 秩亏：这条曲线分不开 K 与 eta')
L()
L('  观测只有一条 mdot(P)。闭合式给出')
L('    K(P)/eta(P) = P/(mdot^3 * C * H)')
L('  右边是观测量，左边是两个未知函数的**比值**。给定 C、H，一条曲线只能定')
L('  K/eta；要分开，必须有第二个不经过能量平衡的量。')
L()
L('  这与本项目主线的「不可辨识量不进盒」是同一条：')
L('    - 单点只给 A+Bf=K_R 一条等值线（Zhao 侧）；')
L('    - 一条功率曲线只给 K/eta 一个组合（KYLIN 侧）。')
L('  两侧是同一个秩缺陷的两个面孔。')
L()
L('  能分开的独立量（三选一）')
L('    1. 直接测主流量（电磁/科氏/文丘里）：直接给 mdot，绕开能量平衡；')
L('       对 LBE 需高温湿部兼容，代价最高，信息最直接。')
L('    2. 加热段外表面热损（热流计或分段能量平衡）：直接给 L(P)，')
L('       即本轮的 L，不必从流量反推。')
L('    3. 二次油侧焓差 mc_pdT：给换热器热负荷，能约束「进入二次侧」的热，')
L('       但不能单独定加热段的净热 —— 需要与 2 合用。')
L()
L('  判据（可判、可证伪；阈值取自 [C] 表）')
L('    若实测 L >= %.2f kW ：相当于 Table 2 口径，阻力几乎不动，热账全责；'
  % LCASE['Table 2 直接插值'])
L('    若实测 L 在 %.2f ~ %.2f kW：阻力参与，需同时引入 K(P)（局阻指数 0.25~0.77）；'
  % (LCASE['物理分解 m_local=0.77'], LCASE['Table 2 直接插值']))
L('    若实测 L <= %.2f kW ：**连阻力上限也补不上，模型缺一个机制**。'
  % LCASE['物理分解 m_local=0.77'])
L()
L('  这三条把「解释不了」变成了「测一个 1 kW 级的量就能判」。')
L()

L('[H] 可写 / 不可写')
L()
L('  可写：')
L('    1. 同篇五功率、油侧同设定，是比跨论文更干净的内部趋势检查（L1+读图）。')
L('    2. 固定闭合在 4.3 kW 差 -0.076 kg/s（-11.0%%），是 ±0.03 读图扰动的 %.1f 倍。'
  % (GAP0 / READ_STRESS))
L('       但 F3 显示读图自洽性本身有 6~11% 的不确定度 ⇒ 这是量级提示，不是铁证。')
L('    3. 三份账：物性 %.2f%%、高度 0%%、阻力 %.0f%%（表内）~ %.0f%%（越界上限）。'
  % (100 * abs(math.log(c_hi / c_lo)) / math.log(RR[4.3]),
     100 * math.log(Kt_lo / Kt_hi) / math.log(RR[4.3]), 100 * COVER[0.77][0]))
L('    4. 剩余须由热账承担；等效 eta(4.3)/eta(17.9) = %.3f（K 固定口径）。' % (1 / RR[4.3]))
L('    5. 恒定热损 L = %.2f kW 可把五点压到 %.1f%% 以内（读图精度内）。' % (
    L_OPT, 100 * max(abs(solve_dp(p, L_OPT) / m - 1) for p, m in PTS)))
L('    6. 该曲线对 (K, eta) 秩亏，故判据须落在独立量上（给三条）。')
L()
L('  不可写：')
L('    1. 「4.3 kW 偏差来自散热」—— 恒定热损只是一种参数化，未验证。')
L('    2. 「L = %.2f kW 是实测热损」—— 它是拟合值，量级检查的假设范围恰好覆盖它。' % L_OPT)
L('    3. 「eta(4.3) = %.2f」—— 等效值，不是热效率读数。' % ((4.3 - L_OPT) / 4.3))
L('    4. 「阻力已排除」—— 只排除到「单独不够」，没排除「参与」。')
L('    5. 「17.9 kW 是留出验证点」—— 仍是锚点；而且同篇内部就有 11% 的未解释漂移。')
L('    6. 「5 点 1 参数拟合 = 验证」—— 4 个自由度配 1 参数，残差小是必然的。')
L()

out = HERE / 'closure_v13_log.txt'
out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
print('[written]', out.name, len(LOG), 'lines')
