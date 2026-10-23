"""Tel halkası bağıntıları; referans değerler Rev. 2 belgesindeki el hesaplarıdır."""

import math

import pytest

from physics import wire
from physics.model import Options, run_model

from conftest import TEST_FILM_MODEL


def test_volume_fraction_rev2():
    assert wire.volume_fraction(0.30e-3, 2.0e-3) == pytest.approx(0.118, abs=5e-4)


def test_mixture_heat_capacity_limits():
    assert wire.mixture_heat_capacity(0.0, 8000, 500, 1250, 1600) == pytest.approx(1250 * 1600)
    assert wire.mixture_heat_capacity(1.0, 8000, 500, 1250, 1600) == pytest.approx(8000 * 500)


def test_rayleigh_limits_and_bounds():
    assert wire.rayleigh_conductivity(0.0, 16.2, 0.155) == pytest.approx(0.155)
    assert wire.rayleigh_conductivity(0.3, 0.155, 0.155) == pytest.approx(0.155)
    phi = 0.118
    k = wire.rayleigh_conductivity(phi, 16.2, 0.155)
    parallel = phi * 16.2 + (1 - phi) * 0.155
    series = 1 / (phi / 16.2 + (1 - phi) / 0.155)
    assert series < k < parallel                      # Wiener sınırları arasında


def test_ring_temperature_energy_balance():
    phi = 0.118
    T = wire.ring_temperature(phi, 8000, 500, 373.15, 1220, 1600, 298.15)
    rc = wire.mixture_heat_capacity(phi, 8000, 500, 1220, 1600)
    assert rc * T == pytest.approx(phi * 4e6 * 373.15 + (1 - phi) * 1220 * 1600 * 298.15)
    assert 298.15 < T < 373.15


def test_groove_volume_rev2():
    # Rev. 2: 0,26 mm³/mm² (p = 2 mm, d = 0,30 mm)
    assert wire.groove_volume(wire.volume_fraction(0.3e-3, 2e-3), 0.3e-3) * 1e3 == pytest.approx(0.26, abs=0.005)


def test_effusivity_and_contact_temperature_rev2():
    e_s = wire.effusivity(16.2, 7990, 500)
    e_p = wire.effusivity(0.155, 1220, 1600)
    assert e_s == pytest.approx(8045, rel=0.005) and e_p == pytest.approx(550, rel=0.005)
    assert wire.contact_temperature(e_s, 100.0, e_p, 25.0) == pytest.approx(95.2, abs=0.1)
    # aynı malzemede temas sıcaklığı ortalamadır
    assert wire.contact_temperature(e_p, 96.0, e_p, 25.0) == pytest.approx(60.5)


def test_wire_gel_ring_rev2():
    # Rev. 2: T_t = 95–100 °C için 0,03–0,04 mm
    d = wire.wire_gel_ring(0.15e-3, 8000, 500, 373.15, 1220, 1600, 355.15, 298.15)
    assert 0.03e-3 < d < 0.045e-3
    assert wire.wire_gel_ring(0.15e-3, 8000, 500, 350.0, 1220, 1600, 355.15, 298.15) == 0.0


def test_model_has_wire_layer(nominal):
    res = run_model(nominal, Options(film_model=TEST_FILM_MODEL, quality="hızlı"))
    names = [L.name for L in res.dip2.gel_result.layers]
    assert names == ["mandrel", "iç PVC katmanı", "tel halkası"]
    assert res.wire.phi == pytest.approx(math.pi * nominal["d_wire"] / (4 * nominal["p_wire"]))
    assert res.dip2.gel_result.sol.energy_error < 1e-9
    assert res.dip2.R_s == pytest.approx(res.R + res.dip1.s_kur + nominal["d_wire"])


def test_hotter_wire_gives_more_second_dip_gel(nominal):
    opt = Options(film_model=TEST_FILM_MODEL, quality="hızlı")
    cold = run_model({**nominal, "T_t": nominal["T_b"]}, opt)
    hot = run_model(nominal, opt)
    assert hot.wire.T_ring > cold.wire.T_ring
    assert hot.dip2.s_jel >= cold.dip2.s_jel
