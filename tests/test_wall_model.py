import math

import numpy as np
import pytest

from physics import inverse, wall
from physics.model import ModelError, Options, run_model



def O(**kw):
    return Options(**kw)


def test_d9_cure():
    assert wall.cured_thickness(0.4e-3, 0.3e-3, 0.02) == pytest.approx(0.98 * 0.7e-3)
    assert wall.cured_thickness(0.4e-3, 0.3e-3, 0.0, phi=0.5) == pytest.approx(0.55e-3)


def test_d10_round_trip():
    R, s, L, rho = 2e-3, 0.8e-3, 0.3, 1250.0
    m = rho * math.pi * L * ((R + s) ** 2 - R**2)
    assert wall.weighed_thickness(m, rho, L, R) == pytest.approx(s)
    assert wall.expected_mass(s, rho, L, R) == pytest.approx(m)


def test_groove_and_cover_weighing_round_trip():
    rho, L, R1, d, phi = 1250.0, 0.4, 2.6e-3, 0.3e-3, 0.118
    mg = wall.groove_mass(rho, L, R1, d, phi)
    # ince halka için V'' = (1 − φ)d yaklaşımıyla aynı mertebe
    assert mg == pytest.approx(rho * (1 - phi) * d * 2 * math.pi * (R1 + d / 2) * L)
    R2, s = R1 + d, 0.3e-3
    m = mg + wall.expected_mass(s, rho, L, R2)
    assert wall.weighed_cover_thickness(m, mg, rho, L, R2) == pytest.approx(s)


def test_mass_sensitivity_matches_derivative():
    rho, L, R, s, ds = 1250.0, 0.4, 2e-3, 0.5e-3, 1e-7
    num_d = (wall.expected_mass(s + ds, rho, L, R) - wall.expected_mass(s - ds, rho, L, R)) / (2 * ds)
    assert wall.mass_sensitivity(rho, L, R, s) == pytest.approx(num_d, rel=1e-6)


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
    dm = inverse.design_map(nominal, O(quality="hızlı"), "t_wait", [5.0, 20.0], "T_m0", [403.15, 453.15])
    assert dm.w.shape == (2, 2) and np.all(np.isfinite(dm.w))
    assert dm.w[1, 1] > dm.w[0, 0]        # daha sıcak ve uzun → daha kalın


def test_d1_mode_applies_transfer_cooling(nominal):
    res = run_model(nominal, O(T_m0_mode="D1", quality="hızlı"))
    pre = res.preheat
    assert pre["T_exit"] > res.T_m0 > nominal["T_amb"]
    expect = nominal["T_amb"] + (pre["T_exit"] - nominal["T_amb"]) * math.exp(-nominal["t_tr"] / pre["tau_t"])
    assert res.T_m0 == pytest.approx(expect)


def test_second_dip_uses_table_inputs(nominal):
    hot = run_model({**nominal, "T_m0_2": nominal["T_m0_2"] + 50, "T_s1": nominal["T_s1"] + 50}, O(quality="hızlı"))
    base = run_model(nominal, O(quality="hızlı"))
    assert hot.dip2.s_jel > base.dip2.s_jel and hot.dip1.s_jel == pytest.approx(base.dip1.s_jel)


def test_film_coefficients_flow_into_model(nominal):
    a = run_model(nominal, O(quality="hızlı"))
    assert a.dip1.film.formula == "D7a"                       # örnek değerlerde LLD dalı küçük
    b = run_model({**nominal, "C_lld": 0.5 * nominal["C_lld"]}, O(quality="hızlı"))
    assert b.dip1.h0 == pytest.approx(0.5 * a.dip1.h0)
    c = run_model({**nominal, "C_lld": 3 * nominal["C_lld"]}, O(quality="hızlı"))
    assert c.dip1.film.formula == "D7c" and c.dip1.h0 == pytest.approx(c.dip1.film.values["D7c"])


def test_design_map_other_axes(nominal):
    dm = inverse.design_map(nominal, O(quality="hızlı"), "t_drain", [10.0, 120.0], "U", [0.5e-3, 2e-3])
    assert dm.w.shape == (2, 2) and np.all(np.isfinite(dm.w))
    assert dm.w[1, 0] > dm.w[0, 0]          # daha hızlı çekme → daha kalın

def test_solve_layers_hits_targets_with_project_data():
    from physics import params
    p = {**params.values_si(params.project_table()), "t_drain": 5.0, "t_wait": 9.0, "t_wait_2": 22.0}
    sols = inverse.solve_layers(p, O(quality="hızlı"), [1e-3, 3e-3], 0.55e-3, 0.55e-3, 573.15)
    ok, too_fast = sols
    assert ok.T_m0 is not None and ok.T_m0_2 is not None and not ok.note
    # bulunan ayarlar gerçekten hedefi verir
    chk = run_model({**p, "U": 1e-3, "T_m0": ok.T_m0, "T_m0_2": ok.T_m0_2, "T_s1": ok.T_m0_2, "T_t": ok.T_m0_2},
                    O(T_m0_mode="direct", quality="hızlı"))
    assert chk.dip1.s_kur == pytest.approx(0.55e-3, abs=2e-6)
    assert chk.dip2.s_kur == pytest.approx(0.55e-3, abs=2e-6)
    assert chk.w == pytest.approx(1.40e-3, abs=5e-6)
    # 3 mm/s'de film tek başına 0,55 mm'yi aşar
    assert too_fast.T_m0 is None and "U düşürülmeli" in too_fast.note