import math

import numpy as np
import pytest

from physics import inverse, wall
from physics.model import ModelError, Options, run_model

from conftest import TEST_FILM_MODEL


def O(**kw):
    return Options(film_model=TEST_FILM_MODEL, **kw)


def test_d9_cure():
    assert wall.cured_thickness(0.4e-3, 0.3e-3, 0.02) == pytest.approx(0.98 * 0.7e-3)
    assert wall.cured_thickness(0.4e-3, 0.3e-3, 0.0, phi=0.5) == pytest.approx(0.55e-3)


def test_d10_round_trip():
    R, s, L, rho = 2e-3, 0.8e-3, 0.3, 1250.0
    m = rho * math.pi * L * ((R + s) ** 2 - R**2)
    assert wall.weighed_thickness(m, rho, L, R) == pytest.approx(s)
    assert wall.expected_mass(s, rho, L, R) == pytest.approx(m)


def test_d11_example_target():
    w, tol = wall.wall_target(4.0e-3, 6.0e-3, 0.1e-3)
    assert w == pytest.approx(1.0e-3) and tol == pytest.approx(0.05e-3)
    assert wall.spiral_wall(0.3e-3, 0.3e-3, 0.4e-3) == pytest.approx(1.0e-3)
    assert wall.check_target(1.04e-3, w, tol)[1]
    assert not wall.check_target(1.06e-3, w, tol)[1]


def test_model_runs_with_example_values(nominal):
    res = run_model(nominal, O(quality="hızlı"))
    assert res.dip2 is not None
    assert res.w == pytest.approx(res.dip1.s_kur + nominal["d_wire"] + res.dip2.s_kur)
    assert res.dip1.s_jel <= res.dip1.s_max
    assert res.dip2.R_s == pytest.approx(res.R + res.dip1.s_kur + nominal["d_wire"])


def test_model_single_dip(nominal):
    res = run_model(nominal, O(spiral=False, quality="hızlı"))
    assert res.dip2 is None and res.w == res.dip1.s_kur


def test_model_rejects_bath_above_gel_temperature(nominal):
    with pytest.raises(ModelError):
        run_model({**nominal, "T_b": nominal["T_g"] + 1}, O(quality="hızlı"))


def test_model_d1_only_solid_mandrel(nominal):
    with pytest.raises(ModelError):
        run_model({**nominal, "R_i": 0.5e-3}, O(T_m0_mode="D1", quality="hızlı"))
    res = run_model(nominal, O(T_m0_mode="D1", quality="hızlı"))
    assert nominal["T_0"] < res.T_m0 < nominal["T_oven"]


def test_feasible_intervals_monotonic():
    t = np.linspace(0, 10, 11)
    w = 0.1 * t                       # hedef 0,5 ± 0,1 → t ∈ [4, 6]
    (lo, hi), = inverse.feasible_intervals(t, w, 0.5, 0.1)
    assert lo == pytest.approx(4.0) and hi == pytest.approx(6.0)


def test_design_map_small(nominal):
    dm = inverse.design_map(nominal, O(quality="hızlı"), [403.15, 453.15], [5.0, 20.0])
    assert dm.w.shape == (2, 2) and np.all(np.isfinite(dm.w))
    assert dm.w[1, 1] > dm.w[0, 0]        # daha sıcak ve uzun → daha kalın


def test_model_requires_film_choice(nominal):
    with pytest.raises(ModelError):
        run_model(nominal, Options(quality="hızlı"))


def test_second_dip_uses_table_inputs(nominal):
    hot = run_model({**nominal, "T_m0_2": nominal["T_m0_2"] + 50, "T_s1": nominal["T_s1"] + 50}, O(quality="hızlı"))
    base = run_model(nominal, O(quality="hızlı"))
    assert hot.dip2.s_jel > base.dip2.s_jel and hot.dip1.s_jel == pytest.approx(base.dip1.s_jel)


def test_film_coefficients_flow_into_model(nominal):
    a = run_model(nominal, O(quality="hızlı"))
    b = run_model({**nominal, "C_lld": 2 * nominal["C_lld"]}, O(quality="hızlı"))
    assert b.dip1.h0 == pytest.approx(2 * a.dip1.h0)