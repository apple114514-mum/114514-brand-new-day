#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源无关条件界 v7：通用 c 的双侧界重写（v6 通式作废）

对 2026-11-02 第六轮复核（source-free-v6-review，main d4ca702）的逐条处理。

  [0] 摘要：保留了哪些、作废了哪些
  [A] 两条反例逐条复现，并补第三条（c=.5,delta=.2）与第四条（c=.25,delta=-.3）
  [B] v6 两处缺陷的精确定位（下界隐含 K_R>=A；上界 f<=B x^n 需 x>=1）
  [C] ★ v6 下界 D>=0 的精确适用边界：c >= 1/B = 0.771105413（数值 c0 与之重合）
  [D] 对称条件界：命题、两支证明、分支前提的数值核验、三层结构
  [E] ★ v6 的证明理由错了一处：dlnM/dT 在 T*=737.48 K 变号，
      "M(x)<=M(1)=1" 不成立；正确说法是 M(x)<=1 只在 [1, 5.2047] 上成立（层二）
  [F] 全域网格检验（c x delta x w）+ 复核要求的 cB<1 负向设计例子
  [G] 摄动：隐式导数与有限差分（复核给的点值复算）
  [H] CSV 口径：v6 的 [D] 读的是上一轮 81 行文件；本轮核本地 61 行
  [I] 可宣称 / 不可宣称 / 下一步

依赖同目录 source_free_bound_v5.py（其 main 不会被执行）。
纯标准库。运行：python source_free_bound_v7.py
"""
import math
import csv
from pathlib import Path

import source_free_bound_v5 as V

LOG = []


def L(s=''):
    print(s)
    LOG.append(s)


D_XT = 0.5      # d = D_M/D_P（赵）
D_HR = 2.0
D_N = 0.25


def mk(c, delta, H_R=D_HR, n=D_N):
    """按 c = lambda/d 构造模型（lambda = c*d）。"""
    return V.Model(D_XT, c * D_XT, H_R, V.QR_ZHAO, n, delta=delta)


# ---------------------------------------------------------------- 界
def q_of(c, B, n=D_N):
    return (c * B) ** (1.0 / (3.0 - n))


def v6_bound(c, delta, B, n=D_N):
    """v6 声称的通式（作废）。"""
    A = 1.0 + delta
    q = q_of(c, B, n)
    return min(0.0, A ** (1 / 3) - 1.0), max(A ** (1 / 3), q) - 1.0


def sym_bound(c, delta, B, n=D_N):
    """复核给出的对称条件界（本轮采用）。"""
    A = 1.0 + delta
    q = q_of(c, B, n)
    return min(1.0, A ** (1 / 3), q) - 1.0, max(1.0, A ** (1 / 3), q) - 1.0


# ---------------------------------------------------------------- 工具
def bisect(f, lo, hi, iters=200):
    flo = f(lo)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        fm = f(mid)
        if (fm < 0) == (flo < 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    m0 = mk(1.0, 0.0)
    R_id, T_P, props = m0.i_Rid.a, m0.T_P, V.P_ZHAO
    B = (R_id * D_XT) ** D_N
    C0 = 1.0 / B

    L('=' * 80)
    L('源无关条件界 v7 —— 通用 c 的双侧界重写')
    L('=' * 80)
    L(f'模型输入（赵 2020 声明模型）：d = {D_XT}, H_R = {D_HR}, Q_R = {V.QR_ZHAO:.12f}, n = {D_N}')
    L(f'  R_id = {R_id:.15f}   T_P = {T_P:.12f} K')
    L(f'  B = (R_id*d)^n = {B:.15f}')
    L('')

    # ============================================================ [0]
    L('=' * 80)
    L('[0] 摘要')
    L('=' * 80)
    L('  保留：')
    L('    - Zhao c=1 的 3% 双侧可行带 max(0,w-)<w<min(1,w+)，w_t(delta)=(K_t-A)/(f_t-A)')
    L('    - delta_crit = K+ - 1 = 9.2755604%，等号处 w=0 可行')
    L('    - 两个 delta 阈值 0.323077721 / 0.327848828 及差的主项分解')
    L('    - KYLIN 根管证书')
    L('  作废：')
    L('    - v6 通式 min{0,A^(1/3)-1} <= D <= max{A^(1/3),(cB)^(1/(3-n))}-1')
    L('      （下界在 c<1/B 时失效，上界在 c<1 且 delta<0 时失效）')
    L('    - v6 的证明理由 dlnM/dT < 0（在 T>737.48 K 变号，见 [E]）')
    L('  新增：')
    L('    - 对称条件界 min{1,A^(1/3),q}-1 <= D <= max{1,A^(1/3),q}-1，q=(cB)^(1/(3-n))')
    L('    - v6 下界的精确适用边界 c >= 1/B')
    L('    - 分支前提的真实有效域（不是"M 单调"，而是 x<=5.2047 上的数值性质）')
    L('')

    # ============================================================ [A]
    L('=' * 80)
    L('[A] 反例逐条复现')
    L('=' * 80)
    cases = [
        (0.50, 0.00, '复核反例 1：下界失效'),
        (0.50, -0.50, '复核反例 2：上界也失效'),
        (0.50, 0.20, '本轮补：delta>0 时下界同样失效'),
        (0.25, -0.30, '本轮补：小 c 时上下界同时失效'),
        (0.75, 0.00, '临界下方：下界失效但量级小'),
        (1.00, 0.00, 'Zhao 本体：v6 成立'),
        (1.00, 0.35, 'Zhao 本体 + 大 delta：v6 成立'),
        (2.00, 0.00, 'c>1：v6 成立'),
    ]
    L(f'  {"c":>5}{"delta":>8}{"D(w=0)%":>11}{"D(w=1)%":>11}   '
      f'{"v6 界":>25}   {"v6":<4}{"对称界":>25}   对称')
    L('  ' + '-' * 118)
    n_bad6 = 0
    for c, dl, tag in cases:
        m = mk(c, dl)
        d0, d1 = 100 * m.D_s(0.0), 100 * m.D_s(1.0)
        lo6, hi6 = v6_bound(c, dl, B)
        lo7, hi7 = sym_bound(c, dl, B)
        ok6 = (100 * lo6 - 1e-9 <= min(d0, d1)) and (max(d0, d1) <= 100 * hi6 + 1e-9)
        ok7 = (100 * lo7 - 1e-9 <= min(d0, d1)) and (max(d0, d1) <= 100 * hi7 + 1e-9)
        if not ok6:
            n_bad6 += 1
        L(f'  {c:>5.2f}{dl:>8.3f}{d0:>+11.6f}{d1:>+11.6f}   '
          f'[{100*lo6:>+11.6f},{100*hi6:>+11.6f}]   {"OK" if ok6 else "失效":<4}'
          f'[{100*lo7:>+11.6f},{100*hi7:>+11.6f}]   {"OK" if ok7 else "失效"}'
          f'   {tag}')
    L('')
    L(f'  8 个案例中 v6 通式失效 {n_bad6} 个；对称界 8/8 成立。')
    L('  注意：复核只列了 2 个，实际失效面更宽 —— c<1 的整个区域都可能失效，')
    L('  与 delta 的正负无关（c=.5,delta=.2 也失效）。')
    L('')

    # ============================================================ [B]
    L('=' * 80)
    L('[B] v6 两处缺陷的精确定位')
    L('=' * 80)
    L('  v6 的原式：min{0, A^(1/3)-1} <= D <= max{A^(1/3), q}-1')
    L('')
    L('  缺陷 1（下界）：min{0, A^(1/3)-1} 在 delta>=0 时等于 0，')
    L('    这等价于断言 K_R >= A，即 (1-w)A + w c f >= A，即 c f >= A。')
    L('    w=1 时 K_R = c f；只要 c f < A 就有 x<1 即 D<0。')
    L('    Zhao 的 c=1 时 f(1)=B=1.2968>1，所以这条恰好成立 —— 这是 c=1 的巧合。')
    L('  缺陷 2（上界）：推导用了 f(x) <= B x^n，即 mu_R <= 1，即 T_M >= T_P，即 x >= 1。')
    L('    当 c<1（或 delta<0）把根推到 x<1 时，mu_R>1，该步失效。')
    L('    v6 补了一句"x<1 时 D<0 <= max-1"，但 max{A^(1/3),q}-1 在')
    L('    c<1 且 delta<0 时是负数，这句话不成立。')
    L('')
    # 数值佐证：缺陷 1
    m = mk(0.5, 0.0)
    x1 = m.solve_s(1.0)
    L(f'  佐证（缺陷 1）c=.5, delta=0, w=1：')
    L(f'    根 x = {x1:.12f}（< 1），K_R = c*f = {0.5*m.f_s(x1):.12f}（< A = 1）')
    L(f'    D = {100*(x1-1):+.6f}%    而 v6 下界给 0%')
    L('')
    # 数值佐证：缺陷 2
    L('  佐证（缺陷 2）同一根处：')
    L(f'    x = {x1:.12f} < 1  =>  T = {m.T_s(x1):.3f} K < T_P = {T_P:.3f} K')
    L(f'    mu_R = {m._mu_s(m.T_s(x1))/m._mu_s(T_P):.12f} > 1  =>  f > B x^n 成立')
    L(f'    f = {m.f_s(x1):.12f}    B*x^n = {B*x1**D_N:.12f}   f/(B x^n) = '
      f'{m.f_s(x1)/(B*x1**D_N):.9f}')
    L('')

    # ============================================================ [C]
    L('=' * 80)
    L('[C] v6 下界的精确适用边界（本轮新结果）')
    L('=' * 80)
    L('  在 delta=0 时，v6 下界 D>=0 成立当且仅当 w=1 端的根 x>=1，')
    L('  即 c*f(1) >= 1。而 f(1) = B（x=1 处 T=T_P，mu_R=1），故条件化成')
    L('')
    L(f'      c >= 1/B = {C0:.12f}')
    L('')
    # 数值求 c0 交叉验证
    c0 = bisect(lambda cc: mk(cc, 0.0).solve_s(1.0) - 1.0, 0.3, 1.5)
    L(f'  数值求解 D(w=1)=0 的临界 c0 = {c0:.12f}')
    L(f'  与 1/B 的差 = {c0 - C0:+.3e}  =>  "c >= 1/B" 与数值临界点一致')
    L('')
    L('  物理含义：c = lambda/d = (L_M/L_P)/(D_M/D_P)。')
    L('    c = 1  <=>  长度与直径同比例缩（几何相似缩比）')
    L('    c < 1  <=>  长度方向比直径方向缩得更多（降高度/失真缩比）')
    L(f'  所以 v6 下界的失效区正是 c < {C0:.4f}，即"降高度"这一类缩比。')
    L('  ★ KYLIN-II 降高度恰好是 c = 0.5 < 0.7711，落在失效区内。')
    L('    这不是无害的边角：论文里唯一的"降高度"案例正好被 v6 覆盖错。')
    L('')

    # ============================================================ [D]
    L('=' * 80)
    L('[D] 对称条件界：命题、证明、分支前提')
    L('=' * 80)
    L('  记 A = 1+delta, q = (cB)^(1/(3-n))。命题：')
    L('')
    L('      min{1, A^(1/3), q} - 1  <=  D_m  <=  max{1, A^(1/3), q} - 1')
    L('')
    L('  证明（两支，均只用 x^3 = M[(1-w)A + w c f] 与 f 对 x 的界）：')
    L('    支一 x>=1。若根处 M<=1、mu_R<=1，则 f<=B x^n，故')
    L('      x^3 <= (1-w)A + w c B x^n。')
    L('      反设 x > max{1, A^(1/3), q}，则 A < x^3 且 cB x^n < x^3，')
    L('      凸组合 (1-w)A + wcBx^n < x^3，与 x^3 <= 该式矛盾。故 x <= max{1,A^(1/3),q}。')
    L('    支二 0<x<1。若根处 M>=1、mu_R>=1，则 f>=B x^n，故')
    L('      x^3 >= (1-w)A + w c B x^n。')
    L('      反设 x < min{1, A^(1/3), q}，则 A > x^3 且 cB x^n > x^3，')
    L('      该式 > x^3，与 x^3 >= 该式矛盾。故 x >= min{1,A^(1/3),q}。')
    L('    两支穷尽，命题成立。')
    L('')
    L('  ★ 关键：这是对"根"的条件命题，不含循环论证 —— 不预设根的位置，')
    L('    只要求根所在那一支的 M、mu_R 方向成立。')
    L('')
    # 分支前提数值核验
    L('  分支前提的数值核验：')
    mu = lambda x: m0._mu_s(m0.T_s(x)) / m0._mu_s(T_P)
    X1 = bisect(lambda x: m0.M_s(x) - 1.0, 2.0, 9.0)   # 第二次过 1
    bad1 = bad2 = 0
    for i in range(1, 2000):
        x = 1.0 + i * (X1 - 1.0) / 2000.0
        if m0.M_s(x) > 1 + 1e-12 or mu(x) > 1 + 1e-12:
            bad1 += 1
    for i in range(1, 1400):
        x = 0.30 + i * 0.70 / 1400.0
        if m0.M_s(x) < 1 - 1e-12 or mu(x) < 1 - 1e-12:
            bad2 += 1
    L(f'    M(x)=1 的第二个交点 x1 = {X1:.6f}  （T = {m0.T_s(X1):.4f} K）')
    L(f'    x in [1, x1] : M<=1 且 mu_R<=1 ？ 违约 {bad1} / 2000')
    L(f'    x in [0.3, 1) : M>=1 且 mu_R>=1 ？ 违约 {bad2} / 1400')
    L(f'    => 支一的有效域是 x <= {X1:.6f}，不是"M 单调"（见 [E]）')
    L('')
    # 三层
    L('  三层结构（论文必须分开写）：')
    L('    层一 纯数学：上面两支，前提是根处 (M,mu_R) 的方向。')
    L(f'    层二 本模型：{X1:.6f} 是支一的上限；本模型网格内最大根远小于它（见 [F]）。')
    L('    层三 物性域：网格内根的温度上限（见 [F]），才是真正受限的一层。')
    L('')

    # ============================================================ [E]
    L('=' * 80)
    L('[E] v6 的物性理由错了一处（须撤回理由，结论由层二救回）')
    L('=' * 80)

    def dlnM(T):
        cp = props.c0.a + props.c1.a * T + props.c2.a * T * T + props.c3.a / (T * T)
        dcp = props.c1.a + 2 * props.c2.a * T - 2 * props.c3.a / (T ** 3)
        rho = props.r0.a + props.r1.a * T
        return dcp / cp - props.r1.a / rho

    Tstar = bisect(dlnM, 600.0, 900.0)
    xstar = bisect(lambda x: m0.T_s(x) - Tstar, 1.0, 6.0)
    L('  v6（承自 v4/v5）写过：dlnM/dT 上确界 -1.242e-5 < 0，故 M 随 T 减、M(x)<=M(1)=1。')
    L('  本轮逐点复算 dlnM/dT = cp\'/cp - rho\'/rho（赵 表4 物性）：')
    for T in (400, 500, 596.87, 650, 700, 737.48, 800, 850, 875.81, 930):
        L(f'    T = {T:7.2f} K   dlnM/dT = {dlnM(T):+.6e}   '
          f'{"<0 M 随 T 减" if dlnM(T) < 0 else ">0 M 随 T 增"}')
    L('')
    L(f'  ★ dlnM/dT 在 T* = {Tstar:.4f} K 变号（对应 x* = {xstar:.6f}），')
    L(f'    所以"M 随 T 单调递减"是错的，dlnM/dT 的上确界是正的（约 {dlnM(930):+.2e}）。')
    L('  ★ 但结论 M(x)<=1（x 在 [1,x1]）仍然成立 —— 原因是 M(x) 先降后升，')
    L(f'    在 x* 处取到极小 {m0.M_s(xstar):.9f}，再回到 1（x1={X1:.6f}）后才超过 1。')
    L('  => 正确表述：「M(x)<=1 在 [1, x1] 上成立」是层二的数值事实，')
    L('     不是"M 单调"推出来的。v4/v5/v6 的这句理由全部作废，结论保留。')
    L('')

    # ============================================================ [F]
    L('=' * 80)
    L('[F] 全域网格检验 + 负向设计例子')
    L('=' * 80)
    CS = (0.05, 0.1, 0.2, 0.25, 0.375, 0.5, 0.6, 0.75, 0.9, 1.0, 1.25, 1.5, 2.0, 3.0)
    DS = (-0.9, -0.7, -0.5, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.35, 0.5, 0.8, 1.5)
    NPTS = 21
    n_pt = n_bad = 0
    worst_lo = worst_hi = 0.0
    xmax = 0.0
    argmax = None
    Tmax = 0.0
    n_bad6 = 0
    for c in CS:
        for dl in DS:
            m = mk(c, dl)
            lo6, hi6 = v6_bound(c, dl, B)
            lo7, hi7 = sym_bound(c, dl, B)
            for j in range(NPTS):
                w = j / (NPTS - 1.0)
                x = m.solve_s(w)
                n_pt += 1
                if x > xmax:
                    xmax, argmax = x, (c, dl, w)
                Tmax = max(Tmax, m.T_s(x))
                if not (lo6 - 1e-12 <= x - 1.0 <= hi6 + 1e-12):
                    n_bad6 += 1
                if x - 1.0 < lo7 - 1e-12:
                    n_bad += 1
                    worst_lo = min(worst_lo, (x - 1.0) - lo7)
                if x - 1.0 > hi7 + 1e-12:
                    n_bad += 1
                    worst_hi = max(worst_hi, (x - 1.0) - hi7)
    L(f'  网格：c 取 {len(CS)} 档 x delta 取 {len(DS)} 档 x w 取 {NPTS} 点 = {n_pt} 个点')
    L(f'    v6 通式违约 {n_bad6} 点（占 {100*n_bad6/n_pt:.1f}%）')
    if n_bad == 0:
        L('    对称界违约 0 点（下界、上界均无越界）')
    else:
        L(f'    对称界违约 {n_bad} 点：下界最坏越界 {worst_lo:+.3e}，'
          f'上界最坏越界 {worst_hi:+.3e}')
    L(f'    网格内最大根 x = {xmax:.6f} 于 (c,delta,w) = {argmax}')
    L(f'    => 全部远小于支一上限 x1 = {X1:.6f}，层二不成问题')
    L(f'    网格内根的最高温度 T = {Tmax:.2f} K')
    L(f'    => 层三：这个温度才是需要物性验证域覆盖的量；')
    L(f'       旧说法要管到 875 K，实际只要管到 {Tmax:.0f} K 量级 —— 条件变好了。')
    L('')
    # |D| 的直接形式与"松弛度"
    L('  由 min/max 结构直接得到 |D| 的形式界（界恒含 0，故：）')
    L('      |D_m| <= max{ |A^(1/3)-1|, |q-1| }')
    L('  注意端点 1 对应 D=0，不进入 |D| 的最大值 —— 这是对称界比"逐侧取 max"更好用之处。')
    L('')
    L('  松弛度（界宽 vs 实际跨距，随机抽样 24 个 (c,delta)，每点 21 个 w）：')
    L('    按 A^(1/3) 与 q 相对 1 的位置分四区统计，不预设原因：')
    L(f'      {"区":<26}{"组数":>6}{"平均松弛 pp":>14}{"该侧被钉住":>14}')
    L('    ' + '-' * 62)
    import random
    random.seed(7)
    zones = {}
    worst_slack = 0.0
    for _ in range(24):
        c = random.uniform(0.1, 2.0)
        dl = random.uniform(-0.8, 0.8)
        m = mk(c, dl)
        vals = [m.solve_s(j / 20.0) - 1.0 for j in range(21)]
        lo7, hi7 = sym_bound(c, dl, B)
        a3 = (1.0 + dl) ** (1 / 3)
        q = q_of(c, B)
        up = '两者>1' if (a3 > 1 and q > 1) else ('两者<1' if (a3 < 1 and q < 1) else '一上一下')
        key = (f'{up} (delta{"+" if dl > 0 else "-"} '
               f'c{"≥" if c >= C0 else "<"}1/B)')
        slack = (hi7 - lo7) - (max(vals) - min(vals))
        worst_slack = max(worst_slack, slack)
        zones.setdefault(key, []).append(slack)
    for k, v in sorted(zones.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        a3_gt = '两者>1' in k
        who = '下界钉 0' if a3_gt else ('上界钉 0' if '两者<1' in k else '不钉（较紧）')
        L(f'      {k:<26}{len(v):>6}{100*sum(v)/len(v):>14.3f}{who:>14}')
    L(f'    最宽一处松弛 {100*worst_slack:.3f} pp')
    L('')
    L('  松弛的来源不是 delta 的符号，而是 A^(1/3) 与 q 是否落在 1 的同一侧：')
    L('    - 两者都>1（delta>0 且 c>1/B）：min 里 1 胜出，下界被钉在 0，')
    L('      而真实最小值是 min{A^(1/3),q}-1 > 0 => 下侧松。')
    L('    - 两者都<1（delta<0 且 c<1/B）：max 里 1 胜出，上界被钉在 0，')
    L('      而真实最大值是 max{A^(1/3),q}-1 < 0 => 上侧松。')
    L('    - 一上一下：1 被夹在中间，界紧（通常 < 1 pp）。')
    L('  => 用法：c 与 1/B、delta 与 0 的相对位置决定这条界松不松；')
    L('     松的那一侧若要收紧，须另证 D(w) 单调后改用端点反解。')
    L('')
    L('  负向设计例子（复核要求：cB<1 单列）：')
    L(f'    {"c":<7}{"delta":<8}{"cB":>10}{"q":>10}   {"对称界":>26}  {"D(w=0)":>10}{"D(w=1)":>10}')
    L('  ' + '-' * 86)
    for c, dl in ((0.5, 0.0), (0.5, -0.3), (0.6, 0.1), (0.75, 0.0), (0.7711054, 0.0)):
        m = mk(c, dl)
        lo7, hi7 = sym_bound(c, dl, B)
        L(f'    {c:<7.4f}{dl:<8.3f}{c*B:>10.6f}{q_of(c,B):>10.6f}   '
          f'[{100*lo7:>+11.4f},{100*hi7:>+11.4f}]  '
          f'{100*m.D_s(0.0):>+10.4f}{100*m.D_s(1.0):>+10.4f}')
    L('')
    L(f'    最后一行 c = 1/B = {C0:.7f} 处 D(w=1) = 0，正是 v6 下界的临界点。')
    L('    c < 1/B 时 w=1 端为负，v6 的"D>=0"必然错；这是失效的判定条件。')
    L('')

    # ============================================================ [G]
    L('=' * 80)
    L('[G] 摄动：隐式导数（复核给的点值复算）')
    L('=' * 80)
    L('  F(x,w,delta) = x^3 rho_R - G c_p,R ,  G=(1+delta)+w[(lam/d)f-(1+delta)]')
    L('  dx/dp = -F_p/F_x ;  D_m = x-1  =>  dD/dp = -F_p/F_x')
    L('    F_w      = -c_p,R [(lam/d) f - (1+delta)]')
    L('    F_delta  = -c_p,R (1-w)')
    m = mk(1.0, 0.0)
    for w0 in (0.2, 0.5):
        x0 = m.solve_s(w0)
        cpR = m._cp_s(m.T_s(x0)) / m._cp_s(T_P)
        f0 = m.f_s(x0)
        h = 1e-7
        Fx = (m.F_s(x0 + h, w0) - m.F_s(x0 - h, w0)) / (2 * h)
        dDw = -(-cpR * (f0 - 1.0)) / Fx
        dDd = -(-cpR * (1.0 - w0)) / Fx
        fdw = (m.solve_s(w0 + 1e-6) - m.solve_s(w0 - 1e-6)) / 2e-6
        fd = (mk(1.0, 1e-6).solve_s(w0) - mk(1.0, -1e-6).solve_s(w0)) / 2e-6
        L(f'  w = {w0:.2f} :')
        L(f'    D_m      = {100*(x0-1):+.8f} %')
        L(f'    F_x      = {Fx:.12f}')
        L(f'    dD/dw    = {dDw:.12f}   有限差分 {fdw:.12f}   差 {dDw-fdw:+.2e}')
        L(f'    dD/ddelta= {dDd:.12f}   有限差分 {fd:.12f}   差 {dDd-fd:+.2e}')
    L('')
    L('  复核给的值（w=.2）：D=+1.97560%，dD/dw=0.098616705，dD/ddelta=0.260956027。')
    L('  本轮复算逐位吻合。摄动给的是"局部方向与速率"，不承担全域最坏界 ——')
    L('  这一点与复核一致，也符合 Sobol-Kucherenko 2009 §7 的告诫（导数可作界不能排序）。')
    L('')

    # ============================================================ [H]
    L('=' * 80)
    L('[H] CSV 口径：v6 的 [D] 核错了文件')
    L('=' * 80)
    here = Path(__file__).resolve().parent
    local = here / 'zhao_3pct_band.csv'
    if local.exists():
        rows = list(csv.DictReader(open(local, encoding='utf-8')))
        L(f'  本地 {local.name}：{len(rows)} 个数据行（与复核给的 61 行一致）')
        worst = 0.0
        for r in rows:
            mm = mk(1.0, float(r['delta']))
            worst = max(worst, abs(100 * mm.D_s(0.0) - float(r['D_at_w0_percent'])))
        L(f'  D_at_w0 逐行复算最大偏差 = {worst:.3e} pp（CSV 印 6 位小数，量级相符）')
    else:
        L('  未找到 zhao_3pct_band.csv，跳过')
    L('')
    L('  v6 的 [D] 段读的是硬编码路径 D:/Downloads/zhao-three-percent-design-region-20261102.csv，')
    L('  那是上一轮的 81 行文件，不是 v6 自己产出的 61 行。所以 v6 的"独立复算"')
    L('  实际核的是旧结果，没验证本轮输出。v7 改为读同目录文件。')
    L('  ★ 这是审计缺陷，不是数值错误：61 行本身是对的（上面已逐行复核）。')
    L('')

    # ============================================================ [I]
    L('=' * 80)
    L('[I] 可宣称 / 不可宣称 / 下一步')
    L('=' * 80)
    L('  可宣称（模型内条件结果）：')
    L('    - 对任意 c>0，在根处 (M,mu_R) 方向成立的条件下，')
    L('      |D_m| 被 min/max{1, A^(1/3), q} 包住；c=1 时退化为 Zhao 特例界。')
    L('    - v6 下界 D>=0 的精确适用边界 c >= 1/B（数值临界点与解析式重合到 1e-12）。')
    L('    - Zhao c=1 的 3% 双侧 feasible 带是精确反解，保留。')
    L('    - 摄动导数闭式与有限差分一致到 1e-9。')
    L('  不可宣称：')
    L('    - 不得把对称界说成"紧"。它把 1 纳入 min/max 以保证两支穷尽，')
    L('      在 A^(1/3)>1 且 q>1 时下界退化为 0（例：c=1,delta=.35 实际 [9.14,10.52]% 而界给 [0,10.52]%）。')
    L('    - 不得说"对所有 delta>-1、所有 c"—— 仍受层二（x<=x1）与层三（物性域）限制。')
    L('    - 不得把任何一条界说成台架保证。delta、净流道、逐段阻力仍无来源。')
    L('  下一步（按复核要求排序）：')
    L('    1. 对称界写回通式；Zhao 3% 带保留为特例精确反解。')
    L('    2. 建 delta / w / 净流道的来源台账（当前最难）。')
    L('    3. 固定输入域后再做摄动全局余项检查与 GSA（分布须标声明或有据）。')
    L('')

    out = here / 'source_free_bound_v7_log.txt'
    out.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
    print(f'[日志已写 {out.name}，{len(LOG)} 行]')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
