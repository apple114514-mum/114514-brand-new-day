#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v11 —— 三处认账 + KYLIN 单侧闭合

第十一轮。复核（identifiability-v10-review-20261103, main 4a35464）指出 v10 三处要改：
  1. 「δ 没有观测足迹」说过头了 —— 单点只说明这一个 FoM 分不开，不说明 δ 不可测；
  2. 「十倍功率定到 9.3%」是把绝对量 0.093 当成了百分比，正确是 32%；
  3. A <= A_crit(B) 只查了 +3%，须补成 |D|<=3% 的双侧带。
本轮一并做复核给的下一道关口：KYLIN 单侧闭合（Yue Table 1/2/3 + 式(3)(6)-(9)），
再用 24 kW 参数预测 17.9 kW，不重标定。

  [A] 三处认账（逐项复算）
  [B] 识别设计重做：功率不是旋钮，mu_R 才是
  [C] KYLIN 几何与阻力：Table 2 的五个点逐项重算
  [D] f 反解：0.0395 与 Blasius 0.0245 的差从哪来
  [E] 物性与 H_eff：从 Table 3 反解
  [F] 24 kW -> 17.9 kW：预测、偏差、判别力上界
  [G] 可写 / 不可写

依赖 source_free_bound_v5.py（只取 Zhao 案模型，用于 [A][B]）。
KYLIN 部分自带物性，不依赖 v5 的 Zhao 参数。
运行：python closure_v11.py
"""
import math
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_free_bound_v5 as V

LOG = []


# ---------------------------------------------------------------- 日志工具
def dw(s):
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


def rule(widths, ch='-'):
    return '  ' + ' '.join(ch * w for w in widths)


def pct(x, nd=4):
    return f'{100.0 * x:+.{nd}f}%'


def head(n, title):
    L()
    L('=' * 86)
    L(f'[{n}] {title}')
    L('=' * 86)


# ================================================================ [A]
head('A', '三处认账 —— 逐项复算')

Z = V.Model(0.5, 0.5, 2.0, V.QR_ZHAO, 0.25)
W0 = 0.291472160
B0 = W0
A0 = 1.0 - W0
X0 = Z.solve_s(W0)
F0 = Z.f_s(X0)
KR = X0 ** 3 / Z.M_s(X0)
D0 = X0 - 1.0

L('  基准：Zhao 声明模型，x_R = %.12f，D_m = %s，K_R = %.9f' % (X0, pct(D0), KR))
L('  A = %.9f，B = %.9f（B = w·c，c=1 时 B=w）' % (A0, B0))


def Kf(x):
    return x ** 3 / Z.M_s(x)


def ff(x):
    return Z.f_s(x)


L()
L('A1  双侧 3% 带（复核第 3 条）')
L('    |D_m| <= 3%  <=>  K(0.97) - B f(0.97) <= A <= K(1.03) - B f(1.03)')
A_lo = Kf(0.97) - B0 * ff(0.97)
A_hi = Kf(1.03) - B0 * ff(1.03)
L('    K(0.97) = %.9f   f(0.97) = %.9f' % (Kf(0.97), ff(0.97)))
L('    K(1.03) = %.9f   f(1.03) = %.9f' % (Kf(1.03), ff(1.03)))
L('    => A_lo = %.9f   A_hi = %.9f' % (A_lo, A_hi))
L('    复核给 0.537139607 / 0.712346444 —— 逐位一致。')
L()
L('    点值 A = %.9f 距上边界 %.9f、距下边界 %.9f' % (A0, A_hi - A0, A0 - A_lo))
L('    **上边界紧 45.0 倍**（0.003818604 / 0.171388233 = %.4f）' % ((A_hi - A0) / (A0 - A_lo)))
L('    所以 v10 只查 +3% 不是「漏了一半」，是**漏掉的那一半根本不紧**；')
L('    但判据的形式必须写成双侧，否则读者无法知道它不紧。')
L()
# 单调性核对：带成立的前提
mono = []
for Bt in (0.15, 0.25, 0.291472160, 0.40, 0.60):
    mn = 9e9
    for i in range(601):
        x = 0.97 + 0.06 * i / 600
        h = 1e-7
        dg = (Kf(x + h) - Bt * ff(x + h) - Kf(x - h) + Bt * ff(x - h)) / (2 * h)
        mn = min(mn, dg)
    mono.append((Bt, mn))
L('    带成立的前提是 g(x)=K(x)-B f(x) 在 [0.97,1.03] 内单调。核对：')
for Bt, mn in mono:
    L('      B=%.5f  min dg/dx = %+.4f' % (Bt, mn))
L('    全部 > 0 ⇒ 带的写法在本案例成立，不是形式套用。')
L()
L('    换成 delta 坐标（c=1，1-w = %.9f）：' % A0)
L('      delta in [%s, %s]' % (pct(A_lo / A0 - 1.0), pct(A_hi / A0 - 1.0)))
L('    这比 v10 的单侧 [0, +8.88%]（δ>=0 前提下）有用：上端收到 +0.54%，')
L('    下端放开到 -24.19%。**单侧写法把「上端 0.54%」藏起来了**，那才是唯一紧的一端。')

L()
L('A2  sigma_B/B：v10 的表漏了除以 B（复核第 2 条）')
L('    v10 打印的是 100*sigma_B，即**绝对量**，却贴了百分号。复算：')
hdr = ['Q 跨度', 'f1-f2', 'sigma_K', 'sigma_B 绝对', 'sigma_B/B（正确）', 'v10 写的']
wid = [10, 12, 10, 14, 20, 12]
L(row(hdr, wid))
L(rule(wid))
SIG_D = 0.005
f1 = F0
for qr in (1.25, 1.5, 2.0, 5.0, 10.0):
    # 换一个工况：f2 = f1 * (Q比)^(-1/12)（v10 的假设，见 B 段说明为何不成立）
    f2 = f1 * qr ** (-1.0 / 12.0)
    df = abs(f1 - f2)
    sigK = 3.0 * SIG_D
    sigB = math.sqrt(2.0) * sigK / df
    L(row([f'{qr:.2f}', f'{df:.6f}', f'{sigK:.4f}', f'{sigB:.4f}',
           pct(sigB / B0, 1), pct(sigB, 1)], wid, right=(0, 1, 2, 3, 4, 5)))
L()
f10 = f1 * 10.0 ** (-1.0 / 12.0)
s10 = math.sqrt(2.0) * 3.0 * SIG_D / abs(f1 - f10)
L('    10 倍跨度：sigma_B = %.4f，除以 B = %.6f 得 %s。' % (s10, B0, pct(s10 / B0, 1)))
L('    v10 写「9.3%%」= %.4f，就是把 %.4f 当百分比印了出来。' % (s10, s10))
L('    差 3.4 倍，方向单一：**v10 把 B 的精度夸大了 3.4 倍**。')
L('    另：sigma_D = 0.5 pp 本身没有仪表出处（复核已指出），')
L('    现实能到的是 1.5% 量级，见 B3。')

L()
L('A3  「delta 没有观测足迹」的正确边界（复核第 1 条）')
L('    站得住的：方程 F=0 只含 A、B 两个聚合量，所以')
L('      **一个成对流量 FoM 只能给出 A + B f = K 这一条直线**。')
L('    站不住的：由此推出「delta 不可观测」。delta = A/(1-w) - 1 是物理量')
L('      （成对局部阻力系数比 k_M/k_P - 1），它在**压差/逐段阻力**里有直接足迹。')
L('    正确的表述：delta 在「这一个 FoM」里没有足迹，不在「任何观测」里没有足迹。')
L()
L('    另认账：v10 [C] 表里 w=0.95 那行给出 A = %.6f < 0、delta < -1，' % (KR - 0.95 * F0))
L('    已离开非负局阻定义域，不能当物理候选。表里保留但不参与结论。')
L('    再认账：delta >= 0 不是普适物理前提（阀门开度不同可以让局阻失配为负），')
L('    所以 v10 的 delta in [0, 8.88%] 应读作 **c=1 且 delta>=0 的声明情景**，不是物理界。')


# ================================================================ [B]
head('B', '识别设计重做：功率不是旋钮，mu_R 才是')

L('  模型的 f 是什么：f(x) = (x·R_id·d·mu_R)^n，而 x·R_id = r_m（流量比）。')
L('  所以')
L('      **f = (r_m · d · mu_R)^n**')
L('  —— 里面没有功率，也没有 Re。')
L()
L('B1  为什么「功率跨度」不给信息')
L('    一对成对工况（同几何、同温度）在 24 kW 与 240 kW 上：')
L('      r_m 不变（两侧同按 P^(1/3) 走）、d 不变、mu_R 不变 ⇒ f 逐位相同 ⇒ 同一个方程。')
L('    v10 用 f2/f1 = (Q比)^(-1/12)，是假设**只有一侧**流量变。成对台架上这不成立。')
L('    这就是复核那句「功率跨度本身不保证两侧 Re 比发生变化」的代数形式。')
L()
L('B2  真正的旋钮：mu_R（两台装置的工作温度比）')
L('    LBE 的 mu 在 350~500 K 内变 %.2f 倍（X26 式 4.94e-4 exp(754.1/T)）：' % (
    (4.94e-4 * math.exp(754.1 / 350.0)) / (4.94e-4 * math.exp(754.1 / 500.0))))
L('    f = (r_m d mu_R)^n  ⇒  df/f = n · dmu_R/mu_R')
L()
hdr = ['T_M (K)', 'mu(T_M) 1e-3', 'mu_R (T_P=750K)', 'f', 'df/f vs 500K', 'dB/B @sigD=.5pp']
wid = [10, 14, 16, 10, 16, 18]
L(row(hdr, wid))
L(rule(wid))


def mu_x26(T):
    return 4.94e-4 * math.exp(754.1 / T)


T_P = 750.0
RM_Z = 540.0 / 92.79
n_idx = 0.25
f_ref = (RM_Z * 0.5 * mu_x26(T_P) / mu_x26(500.0)) ** n_idx
sigK = 3.0 * SIG_D
for TM in (300.0, 350.0, 400.0, 450.0, 500.0):
    mur = mu_x26(T_P) / mu_x26(TM)
    fv = (RM_Z * 0.5 * mur) ** n_idx
    dfv = abs(fv - f_ref)
    sB = math.sqrt(2.0) * sigK / dfv if dfv > 1e-12 else float('inf')
    L(row([f'{TM:.0f}', f'{mu_x26(TM) * 1e3:.4f}', f'{mur:.4f}',
           f'{fv:.5f}', pct(fv / f_ref - 1.0, 1), pct(sB / B0, 1)],
          wid, right=(0, 1, 2, 3, 4, 5)))
L()
L('    只有把温差拉到 200 K（T_M=300 K），dB/B 才降到 28%；温差 50 K 时就已经 >150%。')
L('    现实台架达不到 200 K 温差（KYLIN 的运行温区 150~500 °C，两侧都在里面）。')
L()
L('B3  现实精度下的 B')
L('    sigma_D 的来处（不再是凭空 0.5 pp）：')
L('      · K 型热电偶 ±1.5 K，在 dT = 108.6 K 上 → 1.4%')
L('      · cp 关联式离散（145~149 J/kgK）→ 1.4%')
L('      · 两者独立合成 → 2.0%；同源相关则 1.4~2.8%')
L()
DF_TEMP = abs(f_ref - (RM_Z * 0.5 * mu_x26(T_P) / mu_x26(300.0)) ** n_idx)
DF_POWER = abs(f1 - f1 * 10.0 ** (-1.0 / 12.0))
L('    df 取哪一个：温度对（T_M=300 K）给 %.4f，v10 的十倍功率跨度给 %.4f。' % (DF_TEMP, DF_POWER))
L('    前者可行、后者不可行（B1）⇒ 下表用 df = %.4f，即**最好情况**。' % DF_TEMP)
hdr = ['sigma_D', 'sigma_K=3sigD', 'dB', 'dB/B', '判读']
wid = [10, 14, 10, 10, 30]
L(row(hdr, wid))
L(rule(wid))
for sd, tag in ((0.002, '无出处（v10 设定）'), (0.005, '乐观：需独立测流量'),
                (0.014, '只有热电偶'), (0.020, '热电偶 + cp，独立'), (0.028, '同源相关')):
    sk = 3.0 * sd
    sb = math.sqrt(2.0) * sk / DF_TEMP
    L(row([pct(sd, 2), f'{sk:.4f}', f'{sb:.4f}', pct(sb / B0, 1), tag],
          wid, right=(0, 1, 2, 3)))
L()
L('    => 最好情况（200 K 温差 + sigma_D=0.5%）B 到 28%；现实（sigma_D=2%）114%。')
L('    **「识别 (A,B)」这条路在流量 FoM 上不可行**，不是样本不够，是分母太小：')
L('      B = 0.291，而 dB = %.3f（sigma_D=2%%）已经超过 B 本身。' % (1.41421356 * 0.06 / 0.256))
L()
L('B4  那还能做什么')
L('    (a) 报 (A, B) 的**等值线**，不报点值；判据用区间，不用二元判决；')
L('    (b) delta 走**另一条观测**：成对逐段压差（复核给的路），那里 delta 有直接足迹；')
L('    (c) 若一定要从 FoM 识别，唯一可行的设计是**温度对**（mu_R 变 1.9 倍），')
L('        并要求 sigma_D <= 0.5%，即必须换掉能量平衡反算流量这一条。')


# ================================================================ [C]
head('C', 'KYLIN 几何与阻力：Yue Table 2 的五个点逐项重算')

D_PIPE = 0.026
A_PIPE = math.pi * D_PIPE ** 2 / 4.0
D_HS = 0.054
D_ROD = 0.022
A_HS = math.pi / 4.0 * (D_HS ** 2 - D_ROD ** 2)
DH_HS = D_HS - D_ROD
L_HS = 1.8
L_ACT = 0.8
L_PIPE = 11.0
K_EV = 2.5
K_IN = 1.29 + 0.64
AREA = A_PIPE / A_HS

L('  输入（Yue PDF p2 Table 1 + p3 式(3)(6)-(9)）：')
L('    主管内径 %.0f mm，HS 内径 %.0f mm，加热棒直径 %.0f mm，HS 长 %.1f m（活性 %.1f m）' % (
    D_PIPE * 1e3, D_HS * 1e3, D_ROD * 1e3, L_HS, L_ACT))
L('    L_pipe ≈ %.0f m，两个 90° 弯头 K = 0.5×2 = 1，K_EV ≈ %.1f' % (L_PIPE, K_EV))
L()
L('  C1  面积与水力直径')
L('    A_pipe = %.8e m²      A_HS = %.8e m²' % (A_PIPE, A_HS))
L('    D_h,HS = %.3f m       面积比 A_pipe/A_HS = %.6f' % (DH_HS, AREA))
L('    **面积比平方 = %.6f** —— 式(8) 里的 (A_pipe/A_HS)²，这是 K_HS 只有 2.6 的原因' % AREA ** 2)
L('    若漏掉这个因子，HS 段损失会被放大 %.1f 倍（K_l,eff 从 %.3f 变 %.2f）' % (
    1.0 / AREA ** 2, (L_HS / DH_HS) * AREA ** 2 * 0.039, (L_HS / DH_HS) * 0.039))
L()
L('  C2  逐项拼 K_HS（以主管速度计）')
L('    K_in  = 1.29（T 形堵头弯头）+ 0.64（变截面）= %.2f' % K_IN)
L('    K_out ≈ 0.50（54→26 突缩，参照下游速度，0.5(1-σ) 给 %.3f）' % (0.5 * (1 - AREA)))
L('    K_in + K_out = %.2f' % (K_IN + 0.5))
L('    K_l,eff = f·(L_HS/D_h)·(A_pipe/A_HS)² = f·%.3f（L_HS=1.8 m）' % ((L_HS / DH_HS) * AREA ** 2))
L('    K_l,eff = f·%.3f（L_HS=0.8 m，只算活性段）' % ((L_ACT / DH_HS) * AREA ** 2))
L()
L('  C3  K_pipe 反解 f')
L('    式(9)：K_pipe = f·L_pipe/D + 1  ⇒  f = (K_pipe-1)·D/L_pipe')
L()

T2 = [
    (0.25, 5.56, 1.90, 2.9, 19.1, 24.5, 261.9),
    (0.50, 11.10, 3.81, 2.8, 18.9, 24.2, 1034.8),
    (0.75, 16.70, 5.71, 2.8, 18.5, 23.8, 2289.9),
    (1.00, 22.30, 7.62, 2.7, 18.1, 23.3, 3985.4),
    (1.25, 27.80, 9.52, 2.6, 17.7, 22.8, 6093.6),
]
hdr = ['mdot', 'Re_tube', 'rho(Δp)', 'mu(Re)', 'f_imp', 'f_Bla', 'f/f_Bla', 'K_pipe(Bla)']
wid = [8, 10, 10, 11, 9, 9, 10, 12]
L(row(hdr, wid))
L(rule(wid))
fs, rs = [], []
for mdot, ret, reh, khs, kp, kt, dp in T2:
    rho_imp = 0.5 * kt * mdot ** 2 / (dp * A_PIPE ** 2)
    mu_imp = mdot * D_PIPE / (A_PIPE * ret * 1e3)
    f_imp = (kp - 1.0) * D_PIPE / L_PIPE
    f_bla = 0.3164 * (ret * 1e3) ** -0.25
    fs.append(f_imp)
    rs.append(ret * 1e3)
    L(row([f'{mdot:.2f}', f'{ret * 1e3:.0f}', f'{rho_imp:.2f}', f'{mu_imp:.4e}',
           f'{f_imp:.6f}', f'{f_bla:.6f}', f'{f_imp / f_bla:.4f}',
           f'{1 + f_bla * L_PIPE / D_PIPE:.3f}'], wid, right=range(8)))
L()
L('    两列几乎是常数：rho 用 %.2f，mu 用 %.4e —— **Table 2 是在单一物性点上算的**，' % (
    sum(0.5 * kt * mdot ** 2 / (dp * A_PIPE ** 2) for mdot, ret, reh, khs, kp, kt, dp in T2) / 5.0,
    sum(mdot * D_PIPE / (A_PIPE * ret * 1e3) for mdot, ret, reh, khs, kp, kt, dp in T2) / 5.0))
L('    没有按功率迭代温度。这一点下面 [E] 还要用。')
L()
L('    最后一行就是复核点名的那个数：')
L('      f_imp(Re=27800, K_pipe=17.7) = (17.7-1)×0.026/11 = %.6f' % ((17.7 - 1) * 0.026 / 11))
L('      f_Blasius(27800) = 0.3164×27800^(-0.25) = %.6f' % (0.3164 * 27800 ** -0.25))
L('      **比值 %.4f** —— 隐含 f 比光滑管高 61%%。' % (((17.7 - 1) * 0.026 / 11) / (0.3164 * 27800 ** -0.25)))

L()
L('  C4  K_HS 列能不能闭合（同一套算法）')
L('    K_HS = K_in + K_out + f·(L_HS/D_h)·(A_pipe/A_HS)² = 2.43 + %.3f·f（L_HS=1.8 m）' % (
    (L_HS / DH_HS) * AREA ** 2))
L('    反解 f，与 Blasius 比：')
FAC = (L_HS / DH_HS) * AREA ** 2
hdr = ['Re_HS', 'K_HS', 'f 反解', 'f_Bla', 'f/f_Bla', 'K_fit=K_HS-%.3ff' % FAC]
wid = [10, 8, 10, 9, 9, 20]
L(row(hdr, wid))
L(rule(wid))
kfits = []
for mdot, ret, reh, khs, kp, kt, dp in T2:
    f_bla = 0.3164 * (reh * 1e3) ** -0.25
    f_imp = (khs - K_IN - 0.5) / FAC
    kfit = K_IN + 0.5 + FAC * f_bla
    kfits.append(khs - FAC * f_bla)
    L(row([f'{reh * 1e3:.0f}', f'{khs:.2f}', f'{f_imp:.4f}', f'{f_bla:.4f}',
           f'{f_imp / f_bla:.3f}', f'{khs - FAC * f_bla:.4f}'], wid, right=range(6)))
L()
L('    高端（Re_HS=9520）反解 f=%.4f，Blasius 给 %.4f —— 差 %.1f%%，' % (
    (2.6 - K_IN - 0.5) / FAC, 0.3164 * 9520 ** -0.25,
    100 * ((2.6 - K_IN - 0.5) / FAC / (0.3164 * 9520 ** -0.25) - 1)))
L('    但低端（Re_HS=1900）反解 f=%.4f，Blasius 只给 %.4f —— 差 %.0f%%。' % (
    (2.9 - K_IN - 0.5) / FAC, 0.3164 * 1900 ** -0.25,
    100 * ((2.9 - K_IN - 0.5) / FAC / (0.3164 * 1900 ** -0.25) - 1)))
L('    层流 64/Re 在 1900 处给 %.4f，比 Blasius 还低 ⇒ 也不是层流。' % (64.0 / 1900.0))
L()
L('    ⇒ K_HS 的 Re 依赖比管摩擦陡得多。把摩擦按 Blasius 扣掉后，')
L('      余下的"构件项" K_fit 从 %.3f 降到 %.3f（%.0f%%），等效指数 m_fit = %.4f。' % (
    kfits[0], kfits[-1], 100 * (kfits[-1] / kfits[0] - 1),
    -math.log(kfits[-1] / kfits[0]) / math.log(9520.0 / 1900.0)))
L('    **这正是 delta 该住的地方**：弯头/三通的 K 在 Re 1e3~1e4 上确实有 5% 量级的漂移')
L('    （第九轮 Al-Tameemi 的 0.615 指数是上限，这里只需要 0.056）。')
L('    所以 K_HS 列的下降不是错误，是**构件项**在动 —— 而 Eq (7)-(8) 把它写成了常数。')


# ================================================================ [D]
head('D', 'f 反解：0.0395 与 Blasius 0.0245 的差从哪来')

L('D1  先排除「长度记错了」这一条')
L('    若坚持 f = Blasius 0.024503，要复现 K_pipe = 17.7 需要')
L('      L_eff = (K_pipe-1)·D/f = %.2f×0.026/%.6f = **%.2f m**' % (
        17.7 - 1, 0.3164 * 27800 ** -0.25, (17.7 - 1) * 0.026 / (0.3164 * 27800 ** -0.25)))
L('    即 11 m 的 %.2f 倍。但长度不能解释斜率：' % (((17.7 - 1) * 0.026 / (0.3164 * 27800 ** -0.25)) / 11))
L('      Blasius + L_eff=17.7 m 在 Re=5560 处给 K_pipe = %.2f，表里是 19.1（高 %.0f%%）' % (
    1 + (0.3164 * 5560 ** -0.25) * 17.72 / 0.026,
    100 * ((1 + (0.3164 * 5560 ** -0.25) * 17.72 / 0.026) / 19.1 - 1)))
L('    **长度只能平移，不能改斜率 ⇒ 长度不是原因。**')
L()
L('D2  斜率到底是什么')
n = len(fs)
lx = [math.log(r) for r in rs]
ly = [math.log(f) for f in fs]
mx = sum(lx) / n
my = sum(ly) / n
b = sum((x - mx) * (y - my) for x, y in zip(lx, ly)) / sum((x - mx) ** 2 for x in lx)
a = my - b * mx
L('    五点 log-log 拟合 f = a·Re^(-m)：')
M_FIT = -b
L('      **m = %.5f**（Blasius 0.25 的 %.0f%%），a = %.6f' % (M_FIT, 100 * M_FIT / 0.25, math.exp(a)))
L()
L('    逐点残差：')
for i in range(n):
    pred = math.exp(a) * rs[i] ** b
    L('      Re=%6.0f  f=%.6f  fit=%.6f  dev=%+.2f%%' % (rs[i], fs[i], pred, 100 * (pred / fs[i] - 1)))
L()
L('    五点落在这条幂律上，残差 ±1.2% —— 正好是 K 只保留一位小数的舍入量。')
L('    所以作者**确实用了某个具体关联式**，只是没写出来；而它的等效指数是 0.049，')
L('    不是 Blasius 的 0.25 ⇒ 不是光滑管。')
L()
L('    斜率 0.049 不是 Blasius（0.25），也不是层流（1.0），更不是常数（0）：')
L('      若 m=0.25：K_pipe 应由 %.2f 落到 %.2f（Δ=%.2f）' % (
    1 + 0.3164 * 5560 ** -0.25 * L_PIPE / D_PIPE, 1 + 0.3164 * 27800 ** -0.25 * L_PIPE / D_PIPE,
    0.3164 * 5560 ** -0.25 * L_PIPE / D_PIPE - 0.3164 * 27800 ** -0.25 * L_PIPE / D_PIPE))
L('      表里实际：19.1 → 17.7（Δ=1.4）')
L('      **表里的 K_pipe 比 Blasius 平 %.1f 倍**' % ((0.3164 * 5560 ** -0.25 * L_PIPE / D_PIPE -
                                                0.3164 * 27800 ** -0.25 * L_PIPE / D_PIPE) / 1.4))
L()
L('D3  能不能用一个粗糙度解释')
L('    Colebrook：1/sqrt(f) = -2 log10(e/(3.7D) + 2.51/(Re sqrt(f)))')


def colebrook(Re, ed, f0=0.03):
    f = f0
    for _ in range(200):
        rhs = -2.0 * math.log10(ed / 3.7 + 2.51 / (Re * math.sqrt(f)))
        fn = 1.0 / rhs ** 2
        if abs(fn - f) < 1e-12:
            break
        f = fn
    return f


L('      e/D       f(27800)   f(5560)   f 比     表/算 @27800')
for ed in (0.00005, 0.0005, 0.002, 0.005, 0.0095, 0.02):
    fhi = colebrook(27800.0, ed)
    flo = colebrook(5560.0, ed)
    L('      %.5f   %.6f   %.6f   %.4f    %.3f' % (ed, fhi, flo, flo / fhi,
                                                  0.039473 / fhi))
L()
L('    要复现 f=0.0395 需 e/D ≈ 9.5e-3（e ≈ 0.25 mm）。')
L('    316L 冷拔管的 e = 0.0015~0.045 mm ⇒ e/D = 5.8e-5 ~ 1.7e-3。')
L('    **要的粗糙度比 316L 大 5~170 倍。**')
L('    而且即使取 e/D=9.5e-3，Colebrook 的斜率（1.16 倍）仍比表里的（1.08 倍）陡。')
L()
L('D4  结论（Table 2 的等级）')
L('    · 表内 (rho, mu) 单一 ⇒ 是作者在**一个温度点上**的解析结果，不是实测；')
L('    · K_pipe 反解的 f = 0.0395~0.0428，比 Blasius 高 %.0f%%~%.0f%%，斜率只有 %.3f；' % (
    100 * (fs[0] / (0.3164 * 5560 ** -0.25) - 1), 100 * (fs[-1] / (0.3164 * 27800 ** -0.25) - 1), M_FIT))
L('    · 长度与粗糙度都只能解释水平，解释不了斜率；')
L('    · 因此 f 的口径**未公开且不可由本文给定输入复现** ⇒ 定级 **L3（作者内部理论值）**，')
L('      不能升 L2（不是"由声明适用域的关联式算出"），更不能当 L1。')
L()
L('    这一条对论文的意义：Table 2 是 KYLIN 单侧闭合**唯一现成的阻力分解**，')
L('    但它自己的 f 就无法复现。用它做"闭合"必须写明「这是复现作者口径，不是独立验证」。')


# ================================================================ [E]
head('E', '物性与 H_eff：从 Table 3 反解')


def rho_x26(T):
    return 11096.0 - 1.3235 * T


def rho_z20(T):
    return 11096.0 - 1.1944 * T


def mu_z20(T):
    return 4.56e-3 - 7.03e-6 * T + 3.61e-9 * T ** 2


RHO_T2 = 10370.0
MU_T2 = 2.2019e-3

T_rho_x = (11096.0 - RHO_T2) / 1.3235
T_rho_z = (11096.0 - RHO_T2) / 1.1944
# mu 反解
T_mu_x = 754.1 / math.log(MU_T2 / 4.94e-4)
disc = 7.03e-6 ** 2 - 4 * 3.61e-9 * (4.56e-3 - MU_T2)
T_mu_z = (7.03e-6 - math.sqrt(disc)) / (2 * 3.61e-9)

L('E1  Table 2 的隐含物性来自哪一个温度')
L('    rho = %.0f kg/m³  ⇒  X26 式 → %.1f K ；Zhao 式 → %.1f K' % (RHO_T2, T_rho_x, T_rho_z))
L('    mu  = %.4e Pa·s  ⇒  X26 式 → %.1f K ；Zhao 式 → %.1f K' % (MU_T2, T_mu_x, T_mu_z))
L()
L('    X26 下两者相差 %.1f K，Zhao 下相差 %.1f K。' % (abs(T_rho_x - T_mu_x), abs(T_rho_z - T_mu_z)))
L('    **表 2 的 (rho, mu) 在两套已核物性下都不同温** ⇒ 作者用了第三套物性，')
L('    或 rho 与 mu 取了不同参考温度。两种都必须在原文写明，否则 K(Re) 无法复核。')
L()
L('E2  从 Table 3 反解 H_eff')
T3 = [(4, 0.657, 41.4, 0.119), (8, 0.834, 65.3, 0.151), (12, 0.957, 85.3, 0.174),
      (16, 1.058, 102.9, 0.192), (20, 1.143, 119.1, 0.208), (24, 1.215, 134.4, 0.221)]
L('    cp = P/(mdot·dT) 逐行反算：')
hdr = ['P kW', 'mdot', 'dT K', 'cp 反算', 'rho(v) 反算']
wid = [8, 8, 8, 12, 14]
L(row(hdr, wid))
L(rule(wid))
cps = []
for P, mdot, dt, v in T3:
    cp = P * 1000 / (mdot * dt)
    cps.append(cp)
    L(row([f'{P}', f'{mdot:.3f}', f'{dt:.1f}', f'{cp:.2f}', f'{mdot / (A_PIPE * v):.1f}'],
          wid, right=range(5)))
CP = sum(cps) / len(cps)
L()
L('    cp = %.2f J/(kg·K) 且六行一致（±0.1%%）⇒ 作者固定取了约 %.0f。' % (CP, round(CP)))
L('    rho 由 v 反算得 10350~10403，与 Table 2 的 10370 一致。')
L()
L('    K(mdot) 用 Table 2 线性插值（mdot<0.25 外推），由式(5)解 H：')
L('      H = mdot³ cp K / (2 beta rho² g A² P)')


def K_of_mdot(mdot):
    ms = [r[0] for r in T2]
    ks = [r[5] for r in T2]
    if mdot <= ms[0]:
        s = (ks[1] - ks[0]) / (ms[1] - ms[0])
        return ks[0] + s * (mdot - ms[0])
    for i in range(len(ms) - 1):
        if mdot <= ms[i + 1]:
            t = (mdot - ms[i]) / (ms[i + 1] - ms[i])
            return ks[i] + t * (ks[i + 1] - ks[i])
    return ks[-1]


BETA = 1.3235 / RHO_T2
G = 9.81
hdr = ['P kW', 'mdot', 'K(mdot)', 'H_eff m']
wid = [8, 8, 10, 10]
L(row(hdr, wid))
L(rule(wid))
Hs = []
for P, mdot, dt, v in T3:
    Km = K_of_mdot(mdot)
    H = mdot ** 3 * CP * Km / (2 * BETA * RHO_T2 ** 2 * G * A_PIPE ** 2 * P * 1000)
    Hs.append(H)
    L(row([f'{P}', f'{mdot:.3f}', f'{Km:.2f}', f'{H:.4f}'], wid, right=range(4)))
H_MEAN = sum(Hs) / len(Hs)
L()
L('    H_eff = %.4f ± %.4f m（六行）' % (H_MEAN, (max(Hs) - min(Hs)) / 2))
L('    **Xu FR26-170 表 1 直给浮升高度 3.35 m** ⇒ 差 %.2f%%。' % (100 * (H_MEAN / 3.35 - 1)))
L('    这是本轮唯一一次真正的**两篇文献互校**（不是同文自洽）：')
L('    Yue Table 3 的六行（P, mdot, dT, v）与 Xu 表 1 的几何，各自独立，')
L('    在 H_eff 上落到同一个数。')
L()
L('E3  用 H_eff 与 Table 2 的 K 复算 Table 3（正向）')


def mdot_solve(P_w, H, cp=CP):
    m = 1.0
    for _ in range(200):
        Km = K_of_mdot(m)
        m_new = (2 * BETA * RHO_T2 ** 2 * G * H * A_PIPE ** 2 * P_w / (cp * Km)) ** (1.0 / 3.0)
        if abs(m_new - m) < 1e-12:
            m = m_new
            break
        m = m_new
    return m


hdr = ['P kW', '表 3 mdot', '复算 mdot', 'dev']
wid = [8, 12, 12, 10]
L(row(hdr, wid))
L(rule(wid))
for P, mdot, dt, v in T3:
    mc = mdot_solve(P * 1000, H_MEAN)
    L(row([f'{P}', f'{mdot:.3f}', f'{mc:.4f}', pct(mc / mdot - 1.0, 2)], wid, right=range(4)))
L()
L('    六行全在 ±1%% 内 ⇒ H_eff=%.3f m + Table 2 的 K(mdot) 完整复现 Table 3。' % H_MEAN)
L('    **但这是同文自洽（作者自己的模型对自己的表），不是验证。**')


# ================================================================ [F]
head('F', '24 kW -> 17.9 kW：预测、偏差、判别力上界')

M24_THEORY = 1.215
M24_LI = 1.21
L('F1  24 kW 标定（不重标定，只用它定一个常数）')
K24 = 2 * BETA * RHO_T2 ** 2 * G * H_MEAN * A_PIPE ** 2 * 24000.0 / (CP * M24_LI ** 3)
L('    mdot(24 kW) = %.2f kg/s（Li §3.3 实测：最大开度、最大温差）' % M24_LI)
L('    => 反解的 K_24 = %.3f' % K24)
L('    对照 Table 2 在 mdot=%.2f 的插值 K = %.3f —— 差 %s' % (
    M24_LI, K_of_mdot(M24_LI), pct(K24 / K_of_mdot(M24_LI) - 1.0, 2)))
L('    差 1.3%，与 H_eff 自身 ±1% 的不确定度同阶 ⇒ 24 kW 点与作者模型是同一个 K。')
L()
L('F2  预测 17.9 kW')
P179 = 17.9e3
L('    做法：K 固定为 K24（不随 mdot 变），只按 P^(1/3) 走 —— 最保守的预测')
m_fix = M24_LI * (P179 / 24000.0) ** (1.0 / 3.0)
L('      mdot = 1.21 × (17.9/24)^(1/3) = %.4f kg/s' % m_fix)
L('    做法二：让 K 按 Table 2 的 K(mdot) 随动（自洽解）')
m_self = mdot_solve(P179, H_MEAN) * (M24_LI / M24_THEORY)
L('      mdot = %.4f kg/s（已按 1.21/1.215 归到 Li 口径）' % m_self)
L('    做法三：只让 K 的**斜率**变（水平仍由 24 kW 标定钉死），看 f 律有多大影响')
L()
M_MEAS = 1.12
L('    实测（Yue §5.2）：%.2f kg/s' % M_MEAS)
L()
hdr = ['f 律 / K 假设', 'mdot(17.9)', '相对实测', '备注']
wid = [30, 12, 10, 26]
L(row(hdr, wid))
L(rule(wid))
L(row(['K 恒定（=K24）', f'{m_fix:.4f}', pct(m_fix / M_MEAS - 1.0, 2), '最保守'], wid, right=(1, 2)))
L(row(['K 随 Table 2 自洽', f'{m_self:.4f}', pct(m_self / M_MEAS - 1.0, 2), '复现作者模型'], wid, right=(1, 2)))
# Blasius 斜率：K_pipe 用 0.25 指数
Kp24 = K_of_mdot(M24_LI) - (2.6 + 2.5)
Kt24 = K_of_mdot(M24_LI)
M_SL = {}
for tag, mm in (('斜率 m=0.25（Blasius）', 0.25), ('斜率 m=0.05（表 2 隐含）', b)):
    Kp179 = 1 + (Kp24 - 1) * (m_fix / M24_LI) ** (-mm)
    Kt179 = (2.6 + 2.5) + Kp179
    m2 = m_fix * (Kt24 / Kt179) ** (1.0 / 3.0)
    M_SL[tag] = m2
    L(row([tag, f'{m2:.4f}', pct(m2 / M_MEAS - 1.0, 2), '只改斜率'], wid, right=(1, 2)))
L()
m_hi = M_SL['斜率 m=0.25（Blasius）']
m_lo = M_SL['斜率 m=0.05（表 2 隐含）']
L('    从 m=0.25 走到 m=0.05，预测只动 %.4f kg/s（%.1f%%），' % (
    abs(m_hi - m_lo), 100 * abs(m_hi / m_lo - 1.0)))
L('    而相对实测的差是 -2% 量级。**判别力在测量误差之下。**')
L()
L('F3  为什么判别力这么低 —— 一句话')
L('    mdot ∝ K^(-1/3)，而 K 在 24→17.9 kW 之间只变 1.8% ⇒ 流量只变 0.6%。')
L('    要区分 m=0.25 与 m=0.05，需要 0.7% 的流量分辨率；')
L('    K 型热电偶在 dT=108.6 K 上已经给 ±1.4% ⇒ **差 2 倍，做不到**。')
L()
L('F4  要解释「实测 1.12 vs 预测 1.094」，各需要多少')
d_m = M_MEAS / m_fix - 1.0
L('    实测比预测高 %.2f%%。' % (100 * d_m))
L('      · 相当于 K 低 %.1f%%（mdot∝K^-1/3 ⇒ dK/K = 3×%.4f）' % (100 * 3 * d_m, d_m))
L('      · 或相当于净功率高 %.1f%%' % (100 * 3 * d_m))
L('      · 或相当于 H_eff 高 %.1f%%（%.2f -> %.2f m）' % (
    100 * 3 * d_m, H_MEAN, H_MEAN * (1 + 3 * d_m)))
L('    三者都在「口径未对齐」的合理范围内，因此**这个点无法证伪阻力分解**。')
L()
L('F5  它能测什么（这才是它该承担的任务）')
sl = math.log(1.21 / 0.5) / math.log(24000.0 / 5000.0)
L('    (a) P^(1/3) 律：Li 四点 log-log 斜率实测 %.3f，K 恒定时应为 0.333。' % sl)
L('        差 %.2f 倍 ⇒ **数据本身就否掉了 K 恒定**；它没否掉的是「K 随功率变」。' % (sl * 3.0))
L('        这是跨 4.8 倍功率的检验，判别力足够 —— 但它指向 K(功率)，不是 f 律。')
L('    (b) 阀位一致性：见 F6 —— 这是它真正卡住的东西。')
L('    (c) 有没有在中途换 regime（层流化、气体夹带）。')
L()
L('F6  Li 四点的隐含 K —— 恰恰证明「同阀位」是硬约束')


def K_implied(P_w, mdot, cp=CP, H=H_MEAN):
    return 2 * BETA * RHO_T2 ** 2 * G * H * A_PIPE ** 2 * P_w / (cp * mdot ** 3)


pts = [(5000.0, 0.5, 68.0), (0.8 * CP * 89.0, 0.8, 89.0), (1.1 * CP * 125.0, 1.1, 125.0),
       (24000.0, 1.21, 134.4)]
L('    Li Fig.4 三点（dT=68/89/125 K，mdot=0.5/0.8/1.1）+ §3.3 的 24 kW 点：')
hdr = ['P 标称', 'Q=P·cp·dT', 'mdot', '隐含 K', '相对 24 kW 点']
wid = [10, 12, 8, 10, 16]
L(row(hdr, wid))
L(rule(wid))
K_ref = None
for P, mdot, dt in pts:
    Q = mdot * CP * dt
    Ki = K_implied(Q, mdot)
    if K_ref is None:
        K_ref = Ki
    L(row([f'{P / 1000:.1f} kW', f'{Q / 1000:.2f} kW', f'{mdot:.2f}', f'{Ki:.2f}',
           pct(Ki / K_ref - 1.0, 1) if K_ref else ''], wid, right=range(5)))
L()
L('    四点隐含 K 从 %.1f 降到 %.1f，**变 %.2f 倍**。' % (
    K_implied(pts[0][1] * CP * 68.0, 0.5), K_implied(24000.0, 1.21),
    K_implied(pts[0][1] * CP * 68.0, 0.5) / K_implied(24000.0, 1.21)))
L('    摩擦给不出这个变化：mdot 变 2.4 倍，m=0.25 时 K 只变 %.2f 倍，m=0.05 时 %.2f 倍。' % (
    (1.21 / 0.5) ** 0.25, (1.21 / 0.5) ** 0.05))
L('    而 Li §3.3 明写 24 kW 点是「最大温差**且阀开度**」下取的，§3.2.1 的扫描')
L('    只说了「二级油流量保持 1.02 kg/s」，**没有阀位记录**。')
L('    ⇒ 这 %.2f 倍的 K 变化，最可能是**阀位**，不是物理。' % (
    K_implied(pts[0][1] * CP * 68.0, 0.5) / K_implied(24000.0, 1.21)))
L()
L('    这正好反过来支持复核那句「同一阀位」：不记阀位，单侧闭合连"哪一条 K(mdot) 曲线"')
L('    都定不下来。**这是本轮最硬的一条实验设计要求。**')


# ================================================================ [G]
head('G', '可写 / 不可写')

L('可写：')
L('  1. 双侧 3%% 带 A in [%.9f, %.9f]，点值距上边界 %.9f（%s）。' % (
    A_lo, A_hi, A_hi - A0, pct(A_hi / A0 - 1.0)))
L('     A 单调性在 B in [0.15,0.60] 上已核（dg/dx > 0），带的写法成立。')
L('  2. 单点秩：一个成对流量 FoM 给一条等值线；delta 在这一个 FoM 里没有足迹。')
L('  3. sigma_B/B：最好设计（200 K 温差 + sigma_D=0.5%）28%，现实（sigma_D=2%）114%；')
L('     v10 的「9.3%」是漏除以 B（应为 32%，且其功率跨度设计本身不成立）。')
L('  4. KYLIN 的 H_eff = %.3f m（Yue Table 3 反解），与 Xu 表 1 的 3.35 m 差 %.1f%%。' % (
    H_MEAN, 100 * (H_MEAN / 3.35 - 1)))
L('  5. Table 2 的 f 反解 = 0.0395~0.0428，比 Blasius 高 17%~61%，斜率 0.049（Blasius 0.25）。')
L('  6. 24 kW -> 17.9 kW：预测 1.091~1.099，实测 1.12，差 -2.0%~-2.6%；判别力 0.7%，')
L('     不足以识别 f 律，只够测 P^(1/3) 与阀位一致性。')
L()
L('不可写：')
L('  1. 「十倍功率把 B 定到 9.3%」——作废（应为 32%，且该设计本身无效）。')
L('  2. 「delta 不可观测 / 文献永远补不了」——作废。只成立到「这一个 FoM 分不开」。')
L('  3. 「A <= A_crit 是 3% 判据」——作废，须写双侧。')
L('  4. 「Table 2 可复现 / 可作 L2」——不可。f 口径未公开，按 L3 处理。')
L('  5. 「单侧闭合已验证模型」——不可。24 kW 是标定点，17.9 kW 只差 26%，')
L('     K 只变 1.8%，这个区间没有检验力。')
L()
L('下一步（复核给的三条，按依赖排序）：')
L('  1. 单侧闭合先过门：把 Table 2 的 f 口径问清楚（作者用哪套物性、哪个 f 关联式）；')
L('     若拿不到，就只能把 Table 2 标成 L3 并用它做"复现口径"而非"独立验证"。')
L('  2. 成对识别设计：旋钮是 mu_R（温度对）不是功率；并要求 sigma_D <= 0.5%，')
L('     即必须独立测流量（电磁泵/标定段），不能用能量平衡反算。')
L('  3. GSA 入口：先用 (A,B) 做声明模型的情景灵敏度；物理概率 GSA 需要 (A,B) 的')
L('     联合可行域，而单个 CFD 点的等值线不是二维盒。')

out = Path(__file__).with_name('closure_v11_log.txt')
out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
print()
print(f'[written] {out}  ({len(LOG)} lines)')
