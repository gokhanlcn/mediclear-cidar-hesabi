"""D1 – Mandrel ön ısıtma (toplu kütle modeli). Tüm girdiler SI.

    T_m(t) = T_fırın − (T_fırın − T_0)·exp(−t/τ),   τ = ρ_m·c_m·R / (2·h_fırın),
    Bi = h_fırın·R / (2·k_m) < 0,1

.md'deki τ ifadesi dolu mandrel içindir; proje kararıyla D1 yalnızca dolu mandrelde
(R_i = 0) kullanılır.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import solve_ivp

BIOT_LIMIT = 0.1


def time_constant(rho_m: float, c_m: float, R: float, h_oven: float) -> float:
    return rho_m * c_m * R / (2.0 * h_oven)


def biot(h_oven: float, R: float, k_m: float) -> float:
    return h_oven * R / (2.0 * k_m)


def mandrel_temperature(t, T_oven: float, T_0: float, tau: float):
    """Analitik çözüm, t skaler veya dizi olabilir."""
    return T_oven - (T_oven - T_0) * np.exp(-np.asarray(t, dtype=float) / tau)


def mandrel_temperature_numeric(t, T_oven: float, T_0: float, tau: float) -> np.ndarray:
    """Aynı ODE'nin sayısal çözümü (dT/dt = (T_fırın − T)/τ) – doğrulama için."""
    t = np.atleast_1d(np.asarray(t, dtype=float))
    sol = solve_ivp(lambda _t, T: (T_oven - T) / tau, (0.0, float(t.max())), [T_0],
                    t_eval=t, rtol=1e-9, atol=1e-9, method="LSODA")
    return sol.y[0]


def time_to_reach(T_target: float, T_oven: float, T_0: float, tau: float) -> float:
    """Mandrelin T_target'a ulaşma süresi. Ulaşamıyorsa math.inf, zaten üstündeyse 0."""
    if T_target <= T_0:
        return 0.0
    if T_target >= T_oven:
        return math.inf
    return -tau * math.log((T_oven - T_target) / (T_oven - T_0))


def transfer_cooling(T_exit: float, T_amb: float, rho_m: float, c_m: float, R: float, h_amb: float,
                     t_tr: float) -> tuple[float, float]:
    """Fırından banyoya taşımada havada soğuma (aynı toplu kütle modeli, ortam havası):

        T_m0 = T_ortam + (T_çıkış − T_ortam)·exp(−t_taşıma/τ_t),   τ_t = ρ_m c_m R / (2 h_ortam)

    Döner: (T_m0, τ_t).
    """
    tau_t = time_constant(rho_m, c_m, R, h_amb)
    return float(T_amb + (T_exit - T_amb) * math.exp(-t_tr / tau_t)), tau_t


def preheat(rho_m: float, c_m: float, k_m: float, R: float, R_i: float, h_oven: float,
            T_oven: float, T_0: float, t_pre: float) -> dict:
    """D1 özet sonucu. R_i > 0 ise model uygulanmaz (valid=False)."""
    tau = time_constant(rho_m, c_m, R, h_oven)
    Bi = biot(h_oven, R, k_m)
    return {
        "tau": tau,
        "Bi": Bi,
        "biot_ok": Bi < BIOT_LIMIT,
        "solid": R_i <= 0.0,
        "T_m_end": float(mandrel_temperature(t_pre, T_oven, T_0, tau)),
    }
