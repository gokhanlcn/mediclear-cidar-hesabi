import numpy as np
import pytest

from physics import film

G = 9.81
CASE = dict(eta=3.0, U=1e-3, gamma=0.035, rho_p=1250.0)


def test_d7a_reference_value():
    h = film.h_lld(CASE["eta"], CASE["U"], CASE["gamma"], CASE["rho_p"], G)
    assert h * 1e3 == pytest.approx(0.31, abs=0.005)


def test_d7b_reference_value():
    h = film.h_fiber(2e-3, CASE["eta"], CASE["U"], CASE["gamma"])
    assert h * 1e3 == pytest.approx(0.52, abs=0.005)


def test_d7c_formula():
    h = film.h_gravity(3.0, 0.1, 1250.0, G)
    assert h == pytest.approx(0.8 * np.sqrt(0.3 / (1250 * G)))


def test_d5_reference_point_and_trend():
    assert film.viscosity(3.0, 45000, 297.15, 297.15) == pytest.approx(3.0)
    assert film.viscosity(3.0, 45000, 313.15, 297.15) < 3.0


def test_d5_fit_round_trip():
    T = np.array([298.15, 308.15, 318.15])
    eta = film.viscosity(4.0, 52000, T, 298.15)
    E_a, eta_ref, T_ref = film.fit_activation_energy(T, eta)
    assert E_a == pytest.approx(52000, rel=1e-6)
    assert eta_ref == pytest.approx(4.0, rel=1e-6)
    assert T_ref == 298.15


def test_d5_fit_needs_two_temperatures():
    with pytest.raises(ValueError):
        film.fit_activation_energy([298.15], [3.0])


def test_d6_numbers():
    assert film.capillary_number(3.0, 1e-3, 0.035) == pytest.approx(0.0857, rel=1e-3)
    assert film.capillary_length(0.035, 1250, G) == pytest.approx(1.689e-3, rel=1e-3)


def test_choice_thick_mandrel_low_speed():
    c = film.choose_film(10e-3, 3.0, 1e-3, 0.035, 1250, G)
    assert c.formula == "D7a" and not c.transition


def test_choice_thin_mandrel():
    c = film.choose_film(1e-3, 3.0, 1e-3, 0.035, 1250, G)
    assert c.formula == "D7b" and not c.transition


def test_choice_high_speed():
    c = film.choose_film(3e-3, 10.0, 10e-3, 0.035, 1250, G)
    assert c.Ca >= 1 and c.formula == "D7c"


def test_choice_transition_band():
    c = film.choose_film(2e-3, 3.0, 1e-3, 0.035, 1250, G)   # R/ℓ_c ≈ 1,18
    assert c.formula == "D7a" and c.transition
    assert c.h_low <= c.h0 <= c.h_high
    assert c.sample(0.0) == c.h_low and c.sample(1.0) == c.h_high
    assert "GEÇİŞ" in c.reason


def test_d8_profile_limits():
    x = np.linspace(0, 0.4, 101)
    h0, h_stop = 0.3e-3, 0.05e-3
    h = film.drained_profile(x, 60.0, h0, 3.0, 1250, G, h_stop)
    assert h.max() <= h0 and h.min() >= h_stop
    assert np.all(np.diff(h) >= 0)                      # üst uç daha ince


def test_d8_yield_stress_stops_drainage():
    x = np.linspace(0, 0.4, 11)
    h = film.drained_profile(x, 60.0, 0.3e-3, 3.0, 1250, G, 0.5e-3)
    np.testing.assert_allclose(h, 0.3e-3)


def test_d8_mean_between_bounds():
    m = film.drained_mean(0.4, 60.0, 0.3e-3, 3.0, 1250, G, 0.0)
    assert 0 < m <= 0.3e-3
