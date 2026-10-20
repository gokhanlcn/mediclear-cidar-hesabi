import numpy as np
import pytest

from physics.symbols import PARAMS
from physics.units import from_si, known_units, to_si


def test_length():
    assert to_si(2.5, "mm") == pytest.approx(2.5e-3)
    assert from_si(2.5e-3, "mm") == pytest.approx(2.5)


def test_temperature():
    assert to_si(25, "°C") == pytest.approx(298.15)
    assert from_si(373.15, "°C") == pytest.approx(100.0)


def test_speed_and_mass():
    assert to_si(1, "mm/s") == pytest.approx(1e-3)
    assert to_si(3, "g") == pytest.approx(3e-3)


def test_identity_units():
    for u in ("Pa·s", "N/m", "J/mol", "kg/m³", "s", "–"):
        assert to_si(7.3, u) == 7.3


def test_array_round_trip():
    x = np.array([0.0, 12.5, 180.0])
    for u in ("mm", "°C", "mm/s", "g"):
        np.testing.assert_allclose(from_si(to_si(x, u), u), x)


def test_unknown_unit():
    with pytest.raises(ValueError):
        to_si(1.0, "inç")


def test_every_parameter_unit_is_known():
    assert {p.unit for p in PARAMS.values()} <= set(known_units())
