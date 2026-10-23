"""Ters tasarım: T_m0 – t_bekleme düzleminde w haritası ve hedefi tutturan aralıklar. SI.

Haritada 1. daldırmanın T_m0 ve t_bekleme değerleri taranır; 2. daldırma girdileri (T_m0,2,
T_s1, t_bekleme,2 …) tablodaki değerlerinde sabit kalır. T_m0 doğrudan girilmiş kabul edilir.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import numpy as np
import pandas as pd

from .model import ModelError, Options, run_model


@dataclass
class DesignMap:
    T_m0: np.ndarray       # (nT,) [K]
    t_wait: np.ndarray     # (nt,) [s]
    w: np.ndarray          # (nT, nt) [m]; hesaplanamayan noktalar NaN
    w_target: float
    w_tol: float


def design_map(p: dict, opt: Options, T_m0_values, t_wait_values,
               progress: Callable[[int, int], None] | None = None) -> DesignMap:
    T_vals = np.asarray(T_m0_values, dtype=float)
    t_vals = np.asarray(t_wait_values, dtype=float)
    W = np.full((T_vals.size, t_vals.size), np.nan)
    run_opt = replace(opt, T_m0_mode="direct", keep_details=False)
    w_target = w_tol = float("nan")
    total, done = W.size, 0
    for i, T in enumerate(T_vals):
        for j, t in enumerate(t_vals):
            try:
                res = run_model({**p, "T_m0": T, "t_wait": t}, run_opt)
                W[i, j] = res.w
                w_target, w_tol = res.w_target, res.w_tol
            except (ModelError, ValueError):
                pass
            done += 1
            if progress:
                progress(done, total)
    return DesignMap(T_vals, t_vals, W, w_target, w_tol)


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
    """Her T_m0 için hedefi tutturan t_bekleme aralığı (SI)."""
    rows = []
    for i, T in enumerate(dm.T_m0):
        for lo, hi in feasible_intervals(dm.t_wait, dm.w[i], dm.w_target, dm.w_tol) or [(np.nan, np.nan)]:
            rows.append({"T_m0": T, "t_min": lo, "t_max": hi})
    return pd.DataFrame(rows)
