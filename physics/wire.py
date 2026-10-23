"""Spiralli tüpte yay teli bölgesi (2. daldırma). Tüm girdiler SI.

Tel bölgesi, kalınlığı tel çapı d olan bir halka olarak modellenir. 2. daldırmada sarımlar
arasındaki oluklar banyodaki plastisolle dolar; halka = çelik tel + plastisol matris.
Bağıntılar (Rev. 2, Bölüm 2.5) türetilmiştir; ayarlanan katsayı içermez:

* Tel hacim oranı: φ = (πd²/4) / (d·p) = πd / (4p)                (geometri)
* Hacimsel ısı kapasitesi: (ρc)_eff = φ·ρ_s c_s + (1−φ)·ρ_p c_p    (karışım kuralı, kesin)
* Radyal iletkenlik (tel eksenine dik akı, matris içinde silindirler – Rayleigh):
      k_eff = k_p·[k_s + k_p + φ(k_s − k_p)] / [k_s + k_p − φ(k_s − k_p)]
* Halkanın başlangıç sıcaklığı (tel T_t, oluk plastisolü T_b; enerji dengesi):
      T_halka = [φ·ρ_s c_s·T_t + (1−φ)·ρ_p c_p·T_b] / (ρc)_eff
* Oluklarda kalan plastisol hacmi (birim yüzey başına): V'' = (1 − φ)·d

Kontrol (el) hesapları:
* Temas sıcaklığı (iki yarı sonsuz cisim): T_c = (e₁T₁ + e₂T₂)/(e₁ + e₂), e = √(kρc)
* Tel çevresindeki en büyük jel halkası (telin T_g üstündeki ısısının tamamı plastisolü T_g'ye
  çıkarsaydı): δ = √(r_t² + Q'/(π ρ_p c_p (T_g − T_b))) − r_t,  Q' = ρ_s c_s π r_t² (T_t − T_g)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def volume_fraction(d: float, p: float) -> float:
    """φ = πd/(4p)."""
    return math.pi * d / (4.0 * p)


def mixture_heat_capacity(phi: float, rho_s: float, c_s: float, rho_p: float, c_p: float) -> float:
    """(ρc)_eff = φ ρ_s c_s + (1 − φ) ρ_p c_p  [J/(m³·K)]."""
    return phi * rho_s * c_s + (1.0 - phi) * rho_p * c_p


def rayleigh_conductivity(phi: float, k_s: float, k_m: float) -> float:
    """Matris (k_m) içinde paralel silindirler (k_s), silindir eksenine dik ısı akışı."""
    return k_m * (k_s + k_m + phi * (k_s - k_m)) / (k_s + k_m - phi * (k_s - k_m))


def ring_temperature(phi: float, rho_s: float, c_s: float, T_t: float, rho_p: float, c_p: float,
                     T_b: float) -> float:
    """Halkanın daldırma başındaki sıcaklığı (enerji dengesi) [K]."""
    rc = mixture_heat_capacity(phi, rho_s, c_s, rho_p, c_p)
    return (phi * rho_s * c_s * T_t + (1.0 - phi) * rho_p * c_p * T_b) / rc


def groove_volume(phi: float, d: float) -> float:
    """Birim yüzey alanı başına oluklarda kalan plastisol hacmi V'' = (1 − φ)d  [m³/m²]."""
    return (1.0 - phi) * d


def effusivity(k: float, rho: float, c: float) -> float:
    """e = √(kρc)  [W·s^½/(m²·K)]."""
    return math.sqrt(k * rho * c)


def contact_temperature(e1: float, T1: float, e2: float, T2: float) -> float:
    """İki yarı sonsuz cismin ani temas sıcaklığı."""
    return (e1 * T1 + e2 * T2) / (e1 + e2)


def wire_gel_ring(r_t: float, rho_s: float, c_s: float, T_t: float, rho_p: float, c_p: float,
                  T_g: float, T_b: float) -> float:
    """Tel çevresinde oluşabilecek en kalın jel halkası (enerji üst sınırı) [m]."""
    if T_t <= T_g:
        return 0.0
    Q = rho_s * c_s * math.pi * r_t**2 * (T_t - T_g)
    return math.sqrt(r_t**2 + Q / (math.pi * rho_p * c_p * (T_g - T_b))) - r_t


@dataclass
class WireResult:
    phi: float            # tel hacim oranı
    rhoc_eff: float       # halkanın hacimsel ısı kapasitesi
    k_eff: float          # halkanın radyal iletkenliği (Rayleigh)
    T_ring: float         # halkanın başlangıç sıcaklığı [K]
    V_groove: float       # oluk plastisolü [m³/m²]
    e_s: float            # tel efüzivitesi
    e_p: float            # plastisol efüzivitesi
    e_m: float            # mandrel efüzivitesi
    T_c_dip1: float       # 1. daldırma: mandrel–plastisol temas sıcaklığı
    T_c_layer: float      # 2. daldırma: iç katman (PVC)–plastisol temas sıcaklığı (oluk tabanı)
    T_c_wire: float       # 2. daldırma: tel–plastisol temas sıcaklığı
    delta_wire: float     # tel çevresindeki en büyük jel halkası [m]


def analyze(p: dict, T_m0: float) -> WireResult:
    """p: SI parametre sözlüğü (tel ve 2. daldırma girdileri dahil)."""
    phi = volume_fraction(p["d_wire"], p["p_wire"])
    rc = mixture_heat_capacity(phi, p["rho_s"], p["c_s"], p["rho_p"], p["c_p"])
    e_s = effusivity(p["k_s"], p["rho_s"], p["c_s"])
    e_p = effusivity(p["k_p"], p["rho_p"], p["c_p"])
    e_m = effusivity(p["k_m"], p["rho_m"], p["c_m"])
    return WireResult(
        phi=phi, rhoc_eff=rc, k_eff=rayleigh_conductivity(phi, p["k_s"], p["k_p"]),
        T_ring=ring_temperature(phi, p["rho_s"], p["c_s"], p["T_t"], p["rho_p"], p["c_p"], p["T_b"]),
        V_groove=groove_volume(phi, p["d_wire"]), e_s=e_s, e_p=e_p, e_m=e_m,
        T_c_dip1=contact_temperature(e_m, T_m0, e_p, p["T_b"]),
        T_c_layer=contact_temperature(e_p, p["T_s1"], e_p, p["T_b"]),
        T_c_wire=contact_temperature(e_s, p["T_t"], e_p, p["T_b"]),
        delta_wire=wire_gel_ring(p["d_wire"] / 2, p["rho_s"], p["c_s"], p["T_t"], p["rho_p"], p["c_p"],
                                 p["T_g"], p["T_b"]),
    )
