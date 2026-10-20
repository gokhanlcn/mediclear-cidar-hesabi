"""D5–D8 – Viskozite, boyutsuz sayılar, sürüklenen film ve süzülme. Tüm girdiler SI.

D7 formül seçimi (proje kararı, .md D6'daki kuralların boşluklarını kapatır):
* Ca ≥ 1           → D7c
* R ≤ ℓ_c          → D7b
* R > ℓ_c          → D7a
* Geçiş bölgesi: 0,1 < Ca < 1 veya ℓ_c < R < 3·ℓ_c. Seçilen formül nominal değeri verir;
  aday formüllerin min–max aralığı gösterilir ve Monte Carlo'da bu aralıktan örnek alınır.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

R_GAS = 8.314462618   # J/(mol·K)
CA_LOW = 0.1
CA_HIGH = 1.0
R_TRANSITION = 3.0    # ℓ_c < R < 3·ℓ_c geçiş bölgesi

FORMULA_NAMES = {
    "D7a": "D7a – Landau–Levich–Derjaguin (kalın mandrel, düşük hız)",
    "D7b": "D7b – Fiber kaplama (ince mandrel)",
    "D7c": "D7c – Yüksek hız (viskoz–yerçekimi dengesi)",
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

def h_lld(eta, U, gamma, rho_p, g):
    """D7a."""
    return 0.94 * (eta * U) ** (2.0 / 3.0) / (gamma ** (1.0 / 6.0) * (rho_p * g) ** 0.5)


def h_fiber(R, eta, U, gamma):
    """D7b."""
    return 1.34 * R * (eta * U / gamma) ** (2.0 / 3.0)


def h_gravity(eta, U, rho_p, g):
    """D7c."""
    return 0.8 * np.sqrt(eta * U / (rho_p * g))


def all_formulas(R, eta, U, gamma, rho_p, g) -> dict[str, float]:
    return {"D7a": h_lld(eta, U, gamma, rho_p, g),
            "D7b": h_fiber(R, eta, U, gamma),
            "D7c": h_gravity(eta, U, rho_p, g)}


@dataclass
class FilmChoice:
    formula: str                 # seçilen formül anahtarı
    h0: float                    # nominal film kalınlığı [m]
    h_low: float                 # geçiş bölgesinde aday formüllerin en küçüğü
    h_high: float                # ... en büyüğü
    transition: bool
    Ca: float
    l_c: float
    values: dict[str, float] = field(default_factory=dict)
    reason: str = ""

    def sample(self, u: float) -> float:
        """Monte Carlo için: geçiş bölgesinde [h_low, h_high] aralığından u∈[0,1] ile değer."""
        return self.h_low + u * (self.h_high - self.h_low) if self.transition else self.h0


def choose_film(R: float, eta: float, U: float, gamma: float, rho_p: float, g: float) -> FilmChoice:
    Ca = capillary_number(eta, U, gamma)
    l_c = capillary_length(gamma, rho_p, g)
    vals = all_formulas(R, eta, U, gamma, rho_p, g)
    ratio = R / l_c
    geom = "D7b" if ratio <= 1.0 else "D7a"
    notes = []

    if Ca >= CA_HIGH:
        formula = "D7c"
        notes.append(f"Ca = {Ca:.3g} ≥ 1 olduğu için yüksek hız formülü (D7c) seçildi.")
    else:
        formula = geom
        if geom == "D7b":
            notes.append(f"R/ℓ_c = {ratio:.2f} ≤ 1 (ince mandrel) olduğu için D7b seçildi.")
        else:
            notes.append(f"R/ℓ_c = {ratio:.2f} > 1 (kalın mandrel) olduğu için D7a seçildi.")
        if Ca <= CA_LOW:
            notes.append(f"Ca = {Ca:.3g} ≤ 0,1: düşük hız koşulu sağlanıyor.")

    candidates = {formula}
    if CA_LOW < Ca < CA_HIGH:
        candidates |= {geom, "D7c"}
        notes.append(f"Ca = {Ca:.3g}, 0,1 ile 1 arasında: .md kuralları bu bölgeyi kapsamıyor "
                     "(GEÇİŞ BÖLGESİ).")
    if 1.0 < ratio < R_TRANSITION and Ca < CA_HIGH:
        candidates |= {"D7a", "D7b"}
        notes.append(f"R/ℓ_c = {ratio:.2f}, 1 ile {R_TRANSITION:g} arasında: R ≫ ℓ_c koşulu tam "
                     "sağlanmıyor (GEÇİŞ BÖLGESİ).")
    transition = len(candidates) > 1
    cand_vals = [vals[c] for c in sorted(candidates)]
    if transition:
        notes.append("Nominal değer seçilen formülden; belirsizlik için "
                     + ", ".join(sorted(candidates)) + " formüllerinin aralığı kullanılır.")
    return FilmChoice(formula=formula, h0=vals[formula], h_low=min(cand_vals),
                      h_high=max(cand_vals), transition=transition, Ca=Ca, l_c=l_c, values=vals,
                      reason=" ".join(notes))


# --- D8 --------------------------------------------------------------------------------

def stop_thickness(tau_y: float, rho_p: float, g: float) -> float:
    """h_dur = τ_y / (ρ_p·g)."""
    return tau_y / (rho_p * g)


def drained_profile(x, t_drain: float, h0: float, eta: float, rho_p: float, g: float,
                    h_stop: float) -> np.ndarray:
    """D8: süzülme sonrası h(x), x üst uçtan mesafe [m].

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
