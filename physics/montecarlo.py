"""D12 – Monte Carlo belirsizlik analizi ve Spearman duyarlılığı. SI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace
from typing import Callable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .model import ModelError, Options, run_model

FILM_U = "_u_film"   # geçiş bölgesindeki film belirsizliği için ek rastgele sütun


def sample_inputs(ranges: dict[str, tuple[float, float, float]], n: int,
                  dist: str = "üçgen", seed: int | None = 0) -> pd.DataFrame:
    """Her parametre için n örnek. dist: "üçgen" (min, nominal, max) veya "düzgün" (min–max)."""
    rng = np.random.default_rng(seed)
    data = {}
    for key, (lo, nom, hi) in ranges.items():
        if hi <= lo:
            data[key] = np.full(n, nom)
        elif dist == "düzgün":
            data[key] = rng.uniform(lo, hi, n)
        else:
            data[key] = rng.triangular(lo, min(max(nom, lo), hi), hi, n)
    data[FILM_U] = rng.uniform(0.0, 1.0, n)
    return pd.DataFrame(data)


@dataclass
class MCResult:
    samples: pd.DataFrame         # yalnız başarılı örnekler
    outputs: pd.DataFrame         # aynı satırlar için model.summary()
    n_requested: int
    failures: Counter = field(default_factory=Counter)

    @property
    def n_ok(self) -> int:
        return len(self.outputs)


def run_monte_carlo(ranges: dict[str, tuple[float, float, float]], n: int, opt: Options,
                    dist: str = "üçgen", seed: int | None = 0,
                    progress: Callable[[int, int], None] | None = None) -> MCResult:
    samples = sample_inputs(ranges, n, dist, seed)
    rows, keep, failures = [], [], Counter()
    for i, row in enumerate(samples.to_dict("records")):
        try:
            res = run_model(row, replace(opt, film_u=row[FILM_U], keep_details=False))
            rows.append(res.summary())
            keep.append(i)
        except (ModelError, ValueError, FloatingPointError) as exc:
            failures[str(exc)] += 1
        if progress:
            progress(i + 1, n)
    return MCResult(samples=samples.iloc[keep].reset_index(drop=True),
                    outputs=pd.DataFrame(rows), n_requested=n, failures=failures)


def percentiles(values) -> dict[str, float]:
    p5, p50, p95 = np.percentile(np.asarray(values, dtype=float), [5, 50, 95])
    return {"P5": float(p5), "medyan": float(p50), "P95": float(p95)}


def hit_probability(values, target: float, tol: float) -> float:
    v = np.asarray(values, dtype=float)
    return float(np.mean(np.abs(v - target) <= tol + 1e-12)) if v.size else 0.0


def sensitivity(samples: pd.DataFrame, output, keys: list[str] | None = None) -> pd.Series:
    """Parametre başına Spearman korelasyonu, mutlak değere göre büyükten küçüğe."""
    y = np.asarray(output, dtype=float)
    keys = keys or list(samples.columns)   # FILM_U: D7 geçiş bölgesi belirsizliği
    corr = {}
    for k in keys:
        x = samples[k].to_numpy(dtype=float)
        if np.ptp(x) == 0 or np.ptp(y) == 0:
            continue
        corr[k] = float(spearmanr(x, y).statistic)
    s = pd.Series(corr, dtype=float)
    return s.reindex(s.abs().sort_values(ascending=False).index)
