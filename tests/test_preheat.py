import math

import numpy as np
import pytest

from physics import preheat


def test_numeric_matches_analytic():
    tau = preheat.time_constant(8000, 500, 2e-3, 50)
    t = np.linspace(0, 600, 61)
    exact = preheat.mandrel_temperature(t, 493.15, 298.15, tau)
    num = preheat.mandrel_temperature_numeric(t, 493.15, 298.15, tau)
    np.testing.assert_allclose(num, exact, rtol=1e-6)


def test_time_constant_and_biot():
    assert preheat.time_constant(8000, 500, 2e-3, 50) == pytest.approx(80.0)
    assert preheat.biot(50, 2e-3, 16) == pytest.approx(0.003125)


def test_time_to_reach_inverts_curve():
    tau = 80.0
    t = preheat.time_to_reach(423.15, 493.15, 298.15, tau)
    assert preheat.mandrel_temperature(t, 493.15, 298.15, tau) == pytest.approx(423.15)
    assert preheat.time_to_reach(500.0, 493.15, 298.15, tau) == math.inf
    assert preheat.time_to_reach(290.0, 493.15, 298.15, tau) == 0.0


def test_biot_flag():
    res = preheat.preheat(2700, 900, 1.0, 5e-3, 0.0, 100, 493.15, 298.15, 600)
    assert res["Bi"] == pytest.approx(0.25)
    assert not res["biot_ok"]
