"""D9 (kür sonrası), D10 (tartımla ortalama kalınlık), D11 (spiralli tüpte toplam cidar). SI."""

from __future__ import annotations

import math


def cured_thickness(s_jel: float, h: float, eps: float, phi: float = 1.0) -> float:
    """D9: s_kür ≈ (1 − ε)·(s_jel + h_kuru), h_kuru = φ·h (plastisolde φ = 1)."""
    return (1.0 - eps) * (s_jel + phi * h)


def weighed_thickness(m: float, rho_p: float, L: float, R: float) -> float:
    """D10: s = √(R² + m/(ρ_p·π·L)) − R."""
    return math.sqrt(R**2 + m / (rho_p * math.pi * L)) - R


def expected_mass(s: float, rho_p: float, L: float, R: float) -> float:
    """D10'un tersi: s kalınlığındaki kaplamanın kütlesi (deneme planı için)."""
    return rho_p * math.pi * L * ((R + s) ** 2 - R**2)


def wall_target(ID: float, OD: float, OD_tol: float) -> tuple[float, float]:
    """D11: hedef w = (OD − ID)/2 ve toleransı ±OD_tol/2."""
    return 0.5 * (OD - ID), 0.5 * OD_tol


def spiral_wall(s_in: float, d_wire: float, s_out: float) -> float:
    """D11: w = s_iç + d_tel + s_dış."""
    return s_in + d_wire + s_out


def check_target(w: float, w_target: float, w_tol: float) -> tuple[float, bool]:
    """(sapma, uygun mu)."""
    dev = w - w_target
    return dev, abs(dev) <= w_tol + 1e-12
