import math

import numpy as np
import pytest

from physics import inverse, montecarlo, wall
from physics.model import ModelError, Options, run_model


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
    res = run_model(nominal, Options(quality="hızlı"))
    assert res.dip2 is not None
    assert res.w == pytest.approx(res.dip1.s_kur + nominal["d_wire"] + res.dip2.s_kur)
    assert res.dip1.s_jel <= res.dip1.s_max
    assert res.dip2.R_s == pytest.approx(res.R + res.dip1.s_kur + nominal["d_wire"])


def test_model_single_dip(nominal):
    res = run_model(nominal, Options(spiral=False, quality="hızlı"))
    assert res.dip2 is None and res.w == res.dip1.s_kur


def test_model_rejects_bath_above_gel_temperature(nominal):
    with pytest.raises(ModelError):
        run_model({**nominal, "T_b": nominal["T_g"] + 1}, Options(quality="hızlı"))


def test_model_d1_only_solid_mandrel(nominal):
    with pytest.raises(ModelError):
        run_model({**nominal, "R_i": 0.5e-3}, Options(T_m0_mode="D1", quality="hızlı"))
    res = run_model(nominal, Options(T_m0_mode="D1", quality="hızlı"))
    assert nominal["T_0"] < res.T_m0 < nominal["T_oven"]


def test_monte_carlo_small(nominal):
    from physics.symbols import PARAMS
    from physics.units import to_si
    ranges = {k: tuple(to_si(v, p.unit) for v in p.example) for k, p in PARAMS.items() if p.example}
    mc = montecarlo.run_monte_carlo(ranges, 20, Options(quality="hızlı"), seed=1)
    assert mc.n_ok + sum(mc.failures.values()) == 20
    pct = montecarlo.percentiles(mc.outputs["w"])
    assert pct["P5"] <= pct["medyan"] <= pct["P95"]
    sens = montecarlo.sensitivity(mc.samples, mc.outputs["w"])
    assert list(sens.abs()) == sorted(sens.abs(), reverse=True)


def test_sampling_bounds_and_constants():
    df = montecarlo.sample_inputs({"a": (1.0, 2.0, 4.0), "b": (5.0, 5.0, 5.0)}, 500, seed=3)
    assert df["a"].between(1.0, 4.0).all() and (df["b"] == 5.0).all()
    du = montecarlo.sample_inputs({"a": (1.0, 2.0, 4.0)}, 500, dist="düzgün", seed=3)
    assert du["a"].between(1.0, 4.0).all()


def test_sensitivity_sign():
    rng = np.random.default_rng(0)
    import pandas as pd
    df = pd.DataFrame({"x": rng.uniform(size=200), "y": rng.uniform(size=200)})
    s = montecarlo.sensitivity(df, 3 * df["x"] - 0.1 * df["y"])
    assert s.index[0] == "x" and s["x"] > 0.9


def test_feasible_intervals_monotonic():
    t = np.linspace(0, 10, 11)
    w = 0.1 * t                       # hedef 0,5 ± 0,1 → t ∈ [4, 6]
    (lo, hi), = inverse.feasible_intervals(t, w, 0.5, 0.1)
    assert lo == pytest.approx(4.0) and hi == pytest.approx(6.0)


def test_design_map_small(nominal):
    dm = inverse.design_map(nominal, Options(quality="hızlı"), [403.15, 453.15], [5.0, 20.0])
    assert dm.w.shape == (2, 2) and np.all(np.isfinite(dm.w))
    assert dm.w[1, 1] > dm.w[0, 0]        # daha sıcak ve uzun → daha kalın
