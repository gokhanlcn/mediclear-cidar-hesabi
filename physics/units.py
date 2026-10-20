"""Birim dönüşümü – programdaki TEK dönüşüm noktası.

Kullanıcı alışılmış birimlerle girer (mm, °C, mm/s, g ...); hesaplar SI ile yapılır
(m, K, m/s, kg ...). Her birim için  SI = değer * çarpan + kaydırma  ilişkisi tutulur.
"""

from __future__ import annotations

import numpy as np

KELVIN_OFFSET = 273.15

# görüntülenen birim -> (çarpan, kaydırma, SI birimi)
_UNITS: dict[str, tuple[float, float, str]] = {
    "mm": (1e-3, 0.0, "m"),
    "m": (1.0, 0.0, "m"),
    "°C": (1.0, KELVIN_OFFSET, "K"),
    "K": (1.0, 0.0, "K"),
    "mm/s": (1e-3, 0.0, "m/s"),
    "g": (1e-3, 0.0, "kg"),
    "s": (1.0, 0.0, "s"),
    "kg/m³": (1.0, 0.0, "kg/m³"),
    "J/(kg·K)": (1.0, 0.0, "J/(kg·K)"),
    "W/(m·K)": (1.0, 0.0, "W/(m·K)"),
    "W/(m²·K)": (1.0, 0.0, "W/(m²·K)"),
    "Pa·s": (1.0, 0.0, "Pa·s"),
    "Pa": (1.0, 0.0, "Pa"),
    "N/m": (1.0, 0.0, "N/m"),
    "J/mol": (1.0, 0.0, "J/mol"),
    "m/s²": (1.0, 0.0, "m/s²"),
    "–": (1.0, 0.0, "–"),
}


def known_units() -> list[str]:
    return list(_UNITS)


def to_si(value, unit: str):
    """Görüntülenen birimdeki değeri SI'ya çevirir (skaler veya dizi)."""
    factor, offset, _ = _lookup(unit)
    return np.asarray(value, dtype=float) * factor + offset if _is_array(value) else float(value) * factor + offset


def from_si(value, unit: str):
    """SI değeri görüntülenen birime çevirir (skaler veya dizi)."""
    factor, offset, _ = _lookup(unit)
    return (np.asarray(value, dtype=float) - offset) / factor if _is_array(value) else (float(value) - offset) / factor


def si_unit(unit: str) -> str:
    return _lookup(unit)[2]


def is_temperature(unit: str) -> bool:
    return unit in ("°C", "K")


def _lookup(unit: str) -> tuple[float, float, str]:
    try:
        return _UNITS[unit]
    except KeyError as exc:
        raise ValueError(f"Bilinmeyen birim: {unit!r}") from exc


def _is_array(value) -> bool:
    return isinstance(value, (list, tuple, np.ndarray))
