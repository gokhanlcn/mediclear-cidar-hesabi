"""D5–D8 – Viskozite, boyutsuz sayılar, sürüklenen film ve süzülme. Tüm girdiler SI.

Formüllerin sayısal katsayıları (C_LLD, C_fib, C_grav, C_dur) kullanıcı girdisidir; gizli katsayı yoktur.
Film formülü otomatik seçilir (film_thickness): levhada min(D7a, D7c), fiberde D7b. Sayısal eşik
tanımlanmaz; levha/fiber ayrımı R ile ℓ_c'nin karşılaştırmasıdır.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

R_GAS = 8.314462618   # J/(mol·K), evrensel gaz sabiti

FORMULA_NAMES = {
    "D7a": "D7a – Landau–Levich–Derjaguin (kalın mandrel, düşük hız)",
    "D7b": "D7b – Fiber kaplama (ince mandrel)",
    "D7c": "D7c – Viskoz–yerçekimi (yüksek hız)",
    "min_ac": "D7a ile D7c'nin küçüğü (Rev. 2 yaklaşımı)",
}


# --- D5 --------------------------------------------------------------------------------

def viscosity(eta_ref: float, E_a: float, T: float, T_ref: float):
    """Arrhenius: η(T) = η_ref·exp[E_a/R_g·(1/T − 1/T_ref)], T ve T_ref [K]."""
    return eta_ref * np.exp(E_a / R_GAS * (1.0 / np.asarray(T, dtype=float) - 1.0 / T_ref))


def fit_activation_energy(T, eta) -> tuple[float, float, float]:
    """(T [K], η) noktalarından D5 uydurur: (E_a, η_ref, T_ref).

    T_ref ilk noktanın sıcaklığı alınır; ln η = ln η_ref + E_a/R_g·(1/T − 1/T_ref).
    """
    T = np.asarray(T, dtype=float)
    eta = np.asarray(eta, dtype=float)
    if T.size < 2 or np.ptp(T) == 0:
        raise ValueError("En az iki farklı sıcaklıkta viskozite noktası gerekli.")
    if np.any(eta <= 0) or np.any(T <= 0):
        raise ValueError("Viskozite ve sıcaklık değerleri pozitif olmalı.")
    T_ref = float(T[0])
    x = 1.0 / T - 1.0 / T_ref
    slope, intercept = np.polyfit(x, np.log(eta), 1)
    return float(slope * R_GAS), float(math.exp(intercept)), T_ref


# --- D6 --------------------------------------------------------------------------------

def capillary_number(eta: float, U: float, gamma: float) -> float:
    return eta * U / gamma


def capillary_length(gamma: float, rho_p: float, g: float) -> float:
    return math.sqrt(gamma / (rho_p * g))


# --- D7 --------------------------------------------------------------------------------

def h_lld(eta, U, gamma, rho_p, g, C_lld):
    """D7a: h = C_LLD·(ηU)^(2/3) / (γ^(1/6)·(ρ_p g)^(1/2))."""
    return C_lld * (eta * U) ** (2.0 / 3.0) / (gamma ** (1.0 / 6.0) * (rho_p * g) ** 0.5)


def h_fiber(R, eta, U, gamma, C_fib):
    """D7b: h = C_fib·R·Ca^(2/3)."""
    return C_fib * R * (eta * U / gamma) ** (2.0 / 3.0)


def h_gravity(eta, U, rho_p, g, C_grav):
    """D7c: h = C_grav·√(ηU/(ρ_p g))."""
    return C_grav * np.sqrt(eta * U / (rho_p * g))


def all_formulas(R, eta, U, gamma, rho_p, g, C_lld, C_fib, C_grav) -> dict[str, float]:
    a = h_lld(eta, U, gamma, rho_p, g, C_lld)
    c = h_gravity(eta, U, rho_p, g, C_grav)
    return {"D7a": a, "D7b": h_fiber(R, eta, U, gamma, C_fib), "D7c": c, "min_ac": np.minimum(a, c)}


@dataclass
class FilmResult:
    formula: str                 # hesapta kullanılan dal: "D7a", "D7c" (levha) veya "D7b" (fiber)
    h0: float                    # çekme anındaki film kalınlığı [m]
    Ca: float
    l_c: float
    R: float                     # filmin sürüklendiği yüzeyin yarıçapı [m]
    geometry: str = ""           # "levha" (R > ℓ_c) veya "fiber" (R ≤ ℓ_c)
    Ca_cross: float = float("nan")   # levhada D7a ve D7c dallarının kesiştiği kapiler sayı
    reason: str = ""
    values: dict[str, float] = field(default_factory=dict)   # tüm formüllerin sonucu (karşılaştırma)


def crossover_capillary(C_lld: float, C_grav: float) -> float:
    """Levha dallarının kesişimi: C_LLD·Ca^(2/3) = C_grav·Ca^(1/2) → Ca* = (C_grav/C_LLD)^6."""
    return (C_grav / C_lld) ** 6


def film_thickness(R: float, eta: float, U: float, gamma: float, rho_p: float, g: float,
                   C_lld: float, C_fib: float, C_grav: float) -> FilmResult:
    """D7 – otomatik seçim (eşik tanımlanmaz):

    * R > ℓ_c (levha): h = ℓ_c·min(C_LLD·Ca^(2/3), C_grav·Ca^(1/2)) = min(D7a, D7c)
      (Rev. 2 Bölüm 2.4; Rio & Boulogne 2017). Düşük Ca'da LLD dalı, yüksek Ca'da yerçekimi dalı
      kendiliğinden küçük kalır; geçiş Ca* = (C_grav/C_LLD)^6'da olur.
    * R ≤ ℓ_c (fiber): h = C_fib·R·Ca^(2/3) (D7b).
    """
    vals = {k: float(v) for k, v in all_formulas(R, eta, U, gamma, rho_p, g, C_lld, C_fib, C_grav).items()}
    Ca, l_c = capillary_number(eta, U, gamma), capillary_length(gamma, rho_p, g)
    Ca_x = crossover_capillary(C_lld, C_grav)
    r = f"{R / l_c:.3g}".replace(".", ",")
    if R > l_c:
        branch = "D7a" if vals["D7a"] <= vals["D7c"] else "D7c"
        ca, cax = (f"{x:.3g}".replace(".", ",") for x in (Ca, Ca_x))
        reason = (f"R/ℓ_c = {r} > 1 → levha. h = min(D7a, D7c); Ca = {ca} "
                  f"{'<' if Ca < Ca_x else '≥'} Ca* = {cax} olduğu için {branch} dalı daha küçük.")
        return FilmResult(formula=branch, h0=vals["min_ac"], Ca=Ca, l_c=l_c, R=R, geometry="levha",
                          Ca_cross=Ca_x, reason=reason, values=vals)
    reason = f"R/ℓ_c = {r} ≤ 1 → fiber (ince mandrel). h = D7b."
    return FilmResult(formula="D7b", h0=vals["D7b"], Ca=Ca, l_c=l_c, R=R, geometry="fiber",
                      Ca_cross=Ca_x, reason=reason, values=vals)

# --- D8 --------------------------------------------------------------------------------

def stop_thickness(tau_y: float, rho_p: float, g: float, C_dur: float) -> float:
    """h_dur = C_dur·τ_y / (ρ_p·g)."""
    return C_dur * tau_y / (rho_p * g)


def drained_profile(x, t_drain: float, h0: float, eta: float, rho_p: float, g: float,
                    h_stop: float) -> np.ndarray:
    """D8: süzülme sonrası h(x) = √(ηx/(ρ_p g t)), x üst uçtan mesafe [m].

    Film h_0'ı aşamaz; h_dur < h_0 ise h_dur'un altına inemez; h_dur ≥ h_0 ise film akmaz.
    """
    x = np.asarray(x, dtype=float)
    if t_drain <= 0 or h_stop >= h0:
        return np.full_like(x, h0)
    h = np.sqrt(eta * x / (rho_p * g * t_drain))
    return np.clip(h, h_stop, h0)


def drained_mean(L: float, t_drain: float, h0: float, eta: float, rho_p: float, g: float,
                 h_stop: float, n: int = 401) -> float:
    """Daldırma boyu boyunca ortalama film kalınlığı."""
    x = np.linspace(0.0, L, n)
    return float(np.trapezoid(drained_profile(x, t_drain, h0, eta, rho_p, g, h_stop), x) / L)
