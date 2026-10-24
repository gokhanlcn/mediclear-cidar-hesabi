"""Ters tasarım: seçilen iki proses değişkeni düzleminde w haritası ve hedefi tutturan aralıklar. SI.

Taranabilen değişkenler AXES'te tanımlıdır (1. daldırmanın T_m0'ı, t_bekleme, U, t_süz). Taranmayan
tüm girdiler tablodaki değerlerinde sabit kalır. T_m0 eksenlerden biriyse T_m0 doğrudan verilmiş kabul
edilir (D1 modu o harita için kullanılmaz).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import numpy as np
import pandas as pd

from .model import ModelError, Options, run_model

# kod: (arayüz adı, kullanıcı birimi)
AXES: dict[str, tuple[str, str]] = {
    "T_m0": ("T_m0 – 1. daldırmada mandrel sıcaklığı", "°C"),
    "t_wait": ("t_bekleme – 1. daldırmada bekleme süresi", "s"),
    "U": ("U – çekme hızı", "mm/s"),
    "t_drain": ("t_süz – süzülme süresi", "s"),
}


@dataclass
class DesignMap:
    x_key: str
    x: np.ndarray          # (nx,) SI
    y_key: str
    y: np.ndarray          # (ny,) SI
    w: np.ndarray          # (ny, nx) [m]; hesaplanamayan noktalar NaN
    w_target: float
    w_tol: float


def design_map(p: dict, opt: Options, x_key: str, x_values, y_key: str, y_values,
               progress: Callable[[int, int], None] | None = None) -> DesignMap:
    if x_key == y_key or x_key not in AXES or y_key not in AXES:
        raise ValueError("İki farklı eksen seçilmeli.")
    xs = np.asarray(x_values, dtype=float)
    ys = np.asarray(y_values, dtype=float)
    W = np.full((ys.size, xs.size), np.nan)
    run_opt = replace(opt, keep_details=False)
    if "T_m0" in (x_key, y_key):
        run_opt = replace(run_opt, T_m0_mode="direct")
    w_target = w_tol = float("nan")
    total, done = W.size, 0
    for i, yv in enumerate(ys):
        for j, xv in enumerate(xs):
            try:
                res = run_model({**p, x_key: xv, y_key: yv}, run_opt)
                W[i, j] = res.w
                w_target, w_tol = res.w_target, res.w_tol
            except (ModelError, ValueError):
                pass
            done += 1
            if progress:
                progress(done, total)
    return DesignMap(x_key, xs, y_key, ys, W, w_target, w_tol)


def feasible_intervals(t: np.ndarray, w: np.ndarray, target: float, tol: float) -> list[tuple[float, float]]:
    """w(t) eğrisinde |w − hedef| ≤ tol olan t aralıkları (doğrusal interpolasyonla)."""
    inside = np.abs(w - target) <= tol
    f = tol - np.abs(w - target)          # ≥ 0 ise içeride
    intervals, start = [], None
    for j in range(len(t)):
        if np.isnan(w[j]):
            if start is not None:
                intervals.append((start, t[j - 1]))
                start = None
            continue
        if inside[j] and start is None:
            start = t[j] if j == 0 or np.isnan(w[j - 1]) else _cross(t, f, j - 1, j)
        elif not inside[j] and start is not None:
            intervals.append((start, _cross(t, f, j - 1, j)))
            start = None
    if start is not None:
        intervals.append((start, t[-1]))
    return intervals


def _cross(t, f, a, b) -> float:
    fa, fb = f[a], f[b]
    return float(t[a] + (t[b] - t[a]) * fa / (fa - fb)) if fa != fb else float(t[a])


def feasible_table(dm: DesignMap) -> pd.DataFrame:
    """Her y değeri için hedefi tutturan x aralığı (SI). Sütunlar: y, x_min, x_max."""
    rows = []
    for i, yv in enumerate(dm.y):
        for lo, hi in feasible_intervals(dm.x, dm.w[i], dm.w_target, dm.w_tol) or [(np.nan, np.nan)]:
            rows.append({"y": yv, "x_min": lo, "x_max": hi})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Katman hedefinden ayar bulma: her U için gereken T_m0 (1. kat) ve T_m0,2 (örtü)
# ---------------------------------------------------------------------------------------

@dataclass
class LayerSolution:
    U: float
    T_m0: float | None          # 1. katı hedefe getiren T_m0 [K]; None: bulunamadı
    s_jel1: float | None
    h1: float | None
    T_m0_2: float | None        # örtüyü hedefe getiren T_m0,2 [K]
    s_jel2: float | None
    h2: float | None
    w: float | None
    note: str = ""


def _bisect(f, lo: float, hi: float, n: int = 24) -> float:
    flo = f(lo)
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def solve_layers(p: dict, opt: Options, U_values, s1_target: float, s2_target: float,
                 T_max: float, link_T2: bool = True,
                 progress: Callable[[int, int], None] | None = None) -> list[LayerSolution]:
    """Her U için s_1 = s1_target veren T_m0'ı ve s_2 = s2_target veren T_m0,2'yi bulur (ikiye bölme).

    Kalınlık sıcaklıkla monoton artar: T ≤ T_g'de jel yoktur, kalınlık yalnızca filmdir. Bu yüzden
    T_g'nin hemen üstünde kalınlık hedeften büyükse hedef o U ile tutturulamaz (film tek başına fazla);
    T_max'ta hedeften küçükse arama aralığı yetmez. link_T2: T_s1 ve T_t de T_m0,2 ile birlikte değişir.
    """
    o1 = replace(opt, spiral=False, T_m0_mode="direct", keep_details=False)   # 1. kat tek başına
    o2 = replace(opt, T_m0_mode="direct", keep_details=False)
    T_lo = p["T_g"] + 0.01
    out = []
    Us = list(U_values)
    for i, U in enumerate(Us):
        q = {**p, "U": U}
        s1 = lambda T: run_model({**q, "T_m0": T}, o1).dip1.s_kur - s1_target  # noqa: E731
        sol = LayerSolution(U, None, None, None, None, None, None, None)
        try:
            if s1(T_lo) > 0:
                sol.note = "Film tek başına 1. kat hedefinden kalın → U düşürülmeli"
            elif s1(T_max) < 0:
                sol.note = "T_m0 üst sınırda bile 1. kat ince → U artırılmalı ya da T üst sınırı yükseltilmeli"
            else:
                T1 = _bisect(s1, T_lo, T_max)
                r1 = run_model({**q, "T_m0": T1}, o1).dip1
                sol.T_m0, sol.s_jel1, sol.h1 = T1, r1.s_jel, r1.h
                q1 = {**q, "T_m0": T1}

                def args(T):
                    return {**q1, "T_m0_2": T, **({"T_s1": T, "T_t": T} if link_T2 else {})}
                s2 = lambda T: run_model(args(T), o2).dip2.s_kur - s2_target  # noqa: E731
                if s2(T_lo) > 0:
                    sol.note = "Film tek başına örtü hedefinden kalın → U düşürülmeli"
                elif s2(T_max) < 0:
                    sol.note = "T_m0,2 üst sınırda bile örtü ince"
                else:
                    T2 = _bisect(s2, T_lo, T_max)
                    r = run_model(args(T2), o2)
                    sol.T_m0_2, sol.s_jel2, sol.h2, sol.w = T2, r.dip2.s_jel, r.dip2.h, r.w
        except (ModelError, ValueError) as exc:
            sol.note = str(exc)
        out.append(sol)
        if progress:
            progress(i + 1, len(Us))
    return out