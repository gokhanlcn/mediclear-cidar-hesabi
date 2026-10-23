import numpy as np
import pytest

from physics import film

G = 9.81
CASE = dict(eta=3.0, U=1e-3, gamma=0.035, rho_p=1250.0)
COEF = dict(C_lld=0.94, C_fib=1.34, C_grav=0.8)


def test_d7a_reference_value():
    h = film.h_lld(CASE["eta"], CASE["U"], CASE["gamma"], CASE["rho_p"], G, 0.94)
    assert h * 1e3 == pytest.approx(0.31, abs=0.005)


def test_d7b_reference_value():
    h = film.h_fiber(2e-3, CASE["eta"], CASE["U"], CASE["gamma"], 1.34)
    assert h * 1e3 == pytest.approx(0.52, abs=0.005)


def test_d7c_formula():
    h = film.h_gravity(3.0, 0.1, 1250.0, G, 0.8)
    assert h == pytest.approx(0.8 * np.sqrt(0.3 / (1250 * G)))


def test_coefficients_are_linear_inputs():
    a1 = film.h_lld(3.0, 1e-3, 0.035, 1250, G, 1.0)
    assert film.h_lld(3.0, 1e-3, 0.035, 1250, G, 0.5) == pytest.approx(0.5 * a1)


def test_d7a_equals_plate_form():
    # h = C·ℓ_c·Ca^(2/3) ile aynı ifade (Rev. 2 yazımı)
    Ca = film.capillary_number(3.0, 1e-3, 0.035)
    lc = film.capillary_length(0.035, 1250, G)
    assert film.h_lld(3.0, 1e-3, 0.035, 1250, G, 0.94) == pytest.approx(0.94 * lc * Ca ** (2 / 3))


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


@pytest.mark.parametrize("model", ["D7a", "D7b", "D7c"])
def test_film_thickness_uses_selected_formula(model):
    r = film.film_thickness(model, 2e-3, 3.0, 1e-3, 0.035, 1250, G, **COEF)
    assert r.formula == model and r.h0 == pytest.approx(r.values[model])


def test_film_thickness_min_branch():
    r = film.film_thickness("min_ac", 2e-3, 3.0, 1e-3, 0.035, 1250, G, **COEF)
    assert r.h0 == pytest.approx(min(r.values["D7a"], r.values["D7c"]))


def test_film_thickness_requires_choice():
    with pytest.raises(ValueError):
        film.film_thickness("", 2e-3, 3.0, 1e-3, 0.035, 1250, G, **COEF)


def test_md_criteria_info_has_no_verdict():
    crit = film.md_criteria(1e-3, 0.05, 1.7e-3)
    assert [k for k, _, _ in crit] == ["D7a", "D7b", "D7c"]
    assert all(isinstance(v, str) and "=" in v for _, _, v in crit)


def test_d8_stop_thickness_coefficient():
    assert film.stop_thickness(12.0, 1220, G, 0.3) == pytest.approx(0.3 * 12 / (1220 * G))


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
