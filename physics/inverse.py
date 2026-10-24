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
