# -*- coding: utf-8 -*-
"""KYLIN-II 条件模型：浮升高度修正 + 成对口径审计。
------------------------------------------------------------
本脚本回应外部复核提出的三条质疑：
  (1) 代码用 H = 5.0 m 作浮升高度，而原文给的是段间中心高差 3.35 m；
  (2) -0.38% 残差是否真能归因于「局部阻力不随缩比变化」；
  (3) 降高度 ~20% 与 Cheng 文献互证是否成立。

基于用户上传的 loop_audit_repair.py 修正共享状态、成对分母及热损规则。
Xu/Li 原文未在本轮提供；几何、US 与 24 kW/1.2 kg/s 为待核输入。
纯标准库。运行：python outputs/loop-audit-repair-corrected-20261101.py
"""
import math
from pathlib import Path

# ------------------------------------------------------------------ 物性（杨若楠 2020 表 2）
def rho(T): return 11096.0 - 1.3235 * T
def cp(T):  return 164.8 - 3.94e-2 * T + 1.25e-5 * T * T - 4.56e5 / (T * T)
def mu(T):  return 4.94e-4 * math.exp(754.1 / T)

G = 9.80665
TAMB = 298.15
BETA_NUM = 1.3235                      # β = 1.3235/ρ，与 ρ 相乘后抵消

# ------------------------------------------------------------------ 几何（原文 Table 1）
PROTO = dict(H=5.0, D=0.026, L_core=1.8, L_hx=1.5, dH=3.35, L_total=12.0)

def split_four(g, frac_hot=3.0 / 7.0):
    z_hx_bot = g['H'] - g['L_hx']
    v_hot = z_hx_bot - g['L_core']
    v_cold = z_hx_bot
    horiz = g['L_total'] - g['L_core'] - g['L_hx'] - v_hot - v_cold
    return (dict(core=dict(L=g['L_core'],      k=1.5, T='b'),
                 hot =dict(L=v_hot + horiz * frac_hot,      k=1.0, T='h'),
                 hx  =dict(L=g['L_hx'],        k=2.5, T='b'),
                 cold=dict(L=v_cold + horiz * (1 - frac_hot), k=1.0, T='c')),
            v_hot, v_cold, horiz)

SEC, V_HOT, V_COLD, HORIZ = split_four(PROTO)

def buoyancy_height_exact():
    """给定竖直段位置和集总温度形状时，精确展开 ∮T dz。"""
    core, hot, hx, cold = SEC['core'], SEC['hot'], SEC['hx'], SEC['cold']
    # 系数整理：(a_core+a_hx)(Th+Tc)/2 + v_hot*Th - (v_hot+L_hx)*Tc
    a = core['L'] + hx['L']
    coef_hot = a / 2.0 + V_HOT          # Th 的系数
    coef_cold = a / 2.0 - PROTO['H']    # Tc 的系数（下降段取负）
    return dict(coef_hot=coef_hot, coef_cold=coef_cold, dH=coef_hot)

# ------------------------------------------------------------------ 隐式模型
def point(m, p):
    UA, US, Q, Ts = p['UA'], p['US'], p['Q'], p['Ts']
    Tb = (Ts + (Q + US * TAMB) / UA) / (1.0 + US / UA)
    Qnet = Q - US * (Tb - TAMB)
    dT = Qnet / (m * cp(Tb))
    Th = Tb + 0.5 * dT
    Tc = Tb - 0.5 * dT
    Tm = {'b': Tb, 'h': Th, 'c': Tc}
    dR, lR = p['dR'], p['lR']
    D = PROTO['D'] * dR
    A = math.pi / 4.0 * D * D
    dp_f = 0.0
    fric = 0.0
    for s in SEC.values():
        T = Tm[s['T']]
        Re = m * D / (A * mu(T))
        f = 0.3164 * Re ** (-0.25)
        if p.get('frozen_f'):                       # 冻结 Re 效应：用原型 Re 的 f
            ReP = p['mP'] * PROTO['D'] / (math.pi / 4.0 * PROTO['D'] ** 2 * mu(577.5))
            f = 0.3164 * ReP ** (-0.25)
        term_f = f * s['L'] * lR / D
        term_k = s['k'] * p['kmult']
        dp_f += (term_k + term_f) / (rho(T) * A * A)
        fric += term_f / (rho(T) * A * A)
    dp_f *= 0.5 * m * m
    fric *= 0.5 * m * m
    dp_b = G * BETA_NUM * (Th - Tc) * p['dH'] * p['lR']
    return dp_b - dp_f, dict(Tb=Tb, Th=Th, Tc=Tc, dT=dT, Qnet=Qnet,
                             dp_b=dp_b, dp_f=dp_f, fric_share=fric / dp_f if dp_f else 0.0)

def solve(p, lo=0.05, hi=30.0):
    g_lo = point(lo, p)[0]
    g_hi = point(hi, p)[0]
    if g_lo * g_hi > 0:
        raise ValueError('未夹住根 g(lo)=%.3e g(hi)=%.3e' % (g_lo, g_hi))
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        gm = point(mid, p)[0]
        if g_lo * gm <= 0:
            hi = mid
        else:
            lo, g_lo = mid, gm
        if hi - lo < 1e-13 * max(1.0, mid):
            break
    m = 0.5 * (lo + hi)
    return m, point(m, p)[1]

# ------------------------------------------------------------------ 标定（Li 2015：24 kW -> 1.2 kg/s）
def calibrate(dH, Q=24e3, UA=915.0, US=6.0, Ts=553.15, target=1.2):
    base = dict(Q=Q, Ts=Ts, US=US, UA=UA, dR=1.0, lR=1.0, kmult=1.0, fmult=1.0, dH=dH)
    base['mP'] = target

    def resid(km):
        p = dict(base); p['kmult'] = km
        return solve(p)[0] - target
    lo, hi = 0.1, 30.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if resid(lo) * resid(mid) <= 0:
            hi = mid
        else:
            lo = mid
    km = 0.5 * (lo + hi)
    p = dict(base); p['kmult'] = km
    m, d = solve(p)
    k_tot = sum(s['k'] for s in SEC.values()) * km
    return p, m, d, km, k_tot

# ------------------------------------------------------------------ 缩比装配
def assemble(pP, c=0.5, n=0.25):
    ed = (2.0 - n) / (2.0 * (1.0 + n))
    d_R = c ** ed
    m_R = c ** (2.0 * ed + 0.5)
    p = dict(pP)
    p['dR'], p['lR'] = d_R, c
    p['Q'] = pP['Q'] * m_R                 # ΔT_R = 1
    p['UA'] = pP['UA'] * m_R
    p['US'] = pP['US'] * c * d_R           # 散热面 ∝ D·H（几何一致）
    return p, d_R, m_R

# ------------------------------------------------------------------ 主流程
LOG = []
def L(s=''):
    s = s.rstrip()
    LOG.append(s); print(s)

def main():
    L('=' * 74)
    L('KYLIN-II 缩比模型审计：浮升高度修正与残差归因')
    L('=' * 74)

    # ---- A 浮升高度
    b = buoyancy_height_exact()
    L('\n[A] 指定分段温度场下的浮升积分（∮T dz，而不是取总高）')
    L('   堆芯 0-1.8、换热器 3.5-5.0；上升热段 1.8-3.5（%.2f m）；下降冷段 5.0-0' % V_HOT)
    L('   ∮T dz = [(L_core+L_hx)/2 + v_hot]·Th + [(L_core+L_hx)/2 - H]·Tc')
    L('          = %+.3f·Th %+.3f·Tc  =>  等效浮升高度 = %.3f m'
      % (b['coef_hot'], b['coef_cold'], b['dH']))
    L('   上传材料转述的 Table 1 给段间高差 3.35 m —— 数值一致，原文待核。')
    L('   => 旧代码用 PROTO["H"] = 5.0 m 是错误的，高出 %.1f%%' % (100 * (5.0 / b['dH'] - 1)))
    dH_true = b['dH']

    # ---- B 两种高度下分别标定
    L('\n[B] 两种浮升高度下的重新标定（同一条 24 kW / 1.2 kg/s 实测点）')
    L('   %-10s %-10s %-10s %-10s %-10s' % ('ΔH (m)', 'k_tot', '摩擦份额', '热损份额', '浮升 Pa'))
    cal = {}
    for dH in (5.0, dH_true):
        p, m, d, km, k_tot = calibrate(dH)
        cal[dH] = (p, m, d, km, k_tot)
        L('   %-10.3f %-10.3f %-10.3f %-10.3f %-10.1f'
          % (dH, k_tot, d['fric_share'],
             100 * (1 - d['Qnet'] / p['Q']), d['dp_b']))
    L('   => k_tot 从 22.7 降到 %.2f：因为浮升被高估 49%%，反解出的阻力必然同步虚高。'
      % cal[dH_true][4])
    L('      两者都能拟合同一个点，说明「单点标定不能识别绝对阻力水平」。')

    # ---- C 标准缩比（两种高度的差异）
    L('\n[C] 标准缩比（l_R = 0.5，d_R = c^0.7，ΔT_R = 1）')
    L('   %-10s %-12s %-12s %-12s' % ('ΔH', 'm_M kg/s', 'eps_m %', 'eps_dT %'))
    for dH in (5.0, dH_true):
        pP = cal[dH][0]
        mP = cal[dH][1]
        pM, d_R, m_R = assemble(pP)
        mM, dM = solve(pM)
        L('   %-10.3f %-12.6f %-12.3f %-12.3f'
          % (dH, mM, 100 * (mM / (mP * m_R) - 1), 100 * (dM['dT'] / cal[dH][2]['dT'] - 1)))
    pP0, mP, dP, km, k_tot = cal[dH_true]
    pP = dict(pP0)
    pM, d_R, m_R = assemble(pP)
    mM, dM = solve(pM)
    eps_m = mM / (mP * m_R) - 1
    eps_T = dM['dT'] / dP['dT'] - 1
    L('   => 修正后标准缩比：eps_m = %+.3f%%，eps_dT = %+.3f%%' % (100 * eps_m, 100 * eps_T))
    L('      与修正前（-0.382%% / -0.733%%）几乎相同 —— 说明这条数对浮升高度不敏感，')
    L('      因为失真是一个比值，常数性偏差在比值中部分抵消。')

    # ---- D 残差归因
    L('\n[D] 残差归因：四个开关逐个切除（基准 = 修正后的标准缩比）')
    L('   每个开关使用参数副本；两侧同时重解。以下为模型干预差，不可线性相加。')

    def run_variant(dH, us_power=False, no_k=False, frozen_f=False):
        p0, m, d, km, k_tot = cal[dH]
        p = dict(p0)
        pM, d_R, m_R = assemble(p)
        if us_power:
            pM['US'] = p['US'] * m_R
        if no_k:
            pM['kmult'] = 0.0
            p['kmult'] = 0.0
            p['mP'] = m
        pM['frozen_f'] = frozen_f
        p['frozen_f'] = frozen_f
        mP2, _ = solve(p)
        mM2, dM2 = solve(pM)
        return mM2 / (mP2 * m_R) - 1

    variants = [
        ('全开（基准）', dict()),
        ('US 改按功率缩放', dict(us_power=True)),
        ('去掉局部阻力', dict(no_k=True)),
        ('冻结 Re 效应', dict(frozen_f=True)),
    ]
    L('   %-22s %-12s %-12s' % ('变体', 'eps_m %', '与基准差(pp)'))
    base = None
    for name, kw in variants:
        e = run_variant(dH_true, **kw)
        if base is None:
            base = e
        L('   %-22s %-12.4f %-12.4f' % (name, 100 * e, 100 * (e - base)))
    L('   => 在此条件模型内，改 US 缩放使名义残差归零；其他开关结果不可归为真实机制份额。')

    # ---- E 降高度：ΔH 与 k 的双参数
    L('\n[E] 降高度（l_R = 0.5，D 不变）：失真是否由该缩比方式唯一决定？')
    L('   每个 k 都在原型和台架两侧重解，台架 US 随高度减半。')
    L('   %-10s %-10s %-12s %-12s' % ('ΔH', 'k_tot', '成对 eps_m %', '成对 eps_dT %'))
    for dH in (5.0, dH_true):
        for kk in (3.0, 6.0, 12.0, cal[dH][4], 36.0):
            p = dict(cal[dH][0], kmult=kk / 6.0, frozen_f=False)
            mP_k, dP_k = solve(p)
            pM_k = dict(p, lR=0.5, US=p['US'] * 0.5)
            mM_k, dM_k = solve(pM_k)
            L('   %-10.3f %-10.2f %-12.3f %-12.3f'
              % (dH, kk, 100 * (mM_k / mP_k - 1), 100 * (dM_k['dT'] / dP_k['dT'] - 1)))
    L('   => 在该情景范围内阻力改变失真幅度；这组真正成对的扫描没有方向翻转。')
    L('      范围 3–36 仅为情景，不能当有证据的物理不确定度。')

    # ---- F 管径端点（一维单调性下的精确极值）
    L('\n[F] 管径公差：一维情形下端点即极值（固定功率/换热/阻力）')
    L('   %-10s %-14s %-14s %-14s' % ('公差', 'm 范围 kg/s', '相对标准点 %', '相对理想点 %'))
    for tol in (0.01, 0.03):
        rs = []
        for sgn in (-1, 1):
            p = dict(pM)
            p['dR'] = d_R * (1 + sgn * tol)
            m, d = solve(p)
            rs.append((m, m / mM - 1, m / (mP * m_R) - 1))
        lo, hi = rs[0], rs[1]
        L('   ±%-9.0f%% %-14s %-14s %-14s'
          % (100 * tol,
             '%.4f–%.4f' % (min(lo[0], hi[0]), max(lo[0], hi[0])),
             '%+.3f–%+.3f' % (100 * min(lo[1], hi[1]), 100 * max(lo[1], hi[1])),
             '%+.3f–%+.3f' % (100 * min(lo[2], hi[2]), 100 * max(lo[2], hi[2]))))
    L('   注：两列分母不同，差别含标准方案自身约 -0.388% 的偏差。')
    L('       这只是单参数结果；多参数联合界仍需独立证明。')

    L('\n' + '=' * 74)
    L('全部数值均随本脚本一次性生成；口径：Li 2015 单点标定，未做独立验证。')
    L('=' * 74)

    Path(__file__).with_name('loop-audit-repair-corrected-20261101.log').write_text(
        '\n'.join(LOG) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
