import math

import numpy as np
import pytest
from scipy.special import j0, j1, jn_zeros

from physics import gel

STEEL = dict(rho=8000.0, c=500.0, k=16.0)
PLASTISOL = dict(rho_p=1250.0, c_p=1600.0, k_p=0.15)


def _mandrel(R=2e-3, R_i=0.0, T=423.15, **props):
    p = {**STEEL, **props}
    return gel.Layer(R_i, R, p["rho"], p["c"], p["k"], T)


# --- D2 ------------------------------------------------------------------------------

def test_d2_thin_layer_limit():
    # s ≪ R: T_m0 jel sıcaklığına çok yakın → tam ifade ince katman yaklaşımına yaklaşır
    args = (8000, 500, 5e-3)
    tail = (1250, 1600, 298.15)
    _, full = gel.energy_ceiling(*args, 0.0, 358.65, 358.15, *tail)
    thin = gel.energy_ceiling_thin(*args, 358.65, 358.15, *tail)
    assert full < 0.01 * 5e-3          # gerçekten s ≪ R
    assert full == pytest.approx(thin, rel=0.01)


def test_d2_full_is_below_thin_for_thick_layers():
    _, full = gel.energy_ceiling(8000, 500, 2e-3, 0.0, 423.15, 358.15, 1250, 1600, 298.15)
    thin = gel.energy_ceiling_thin(8000, 500, 2e-3, 423.15, 358.15, 1250, 1600, 298.15)
    assert 0 < full < thin


def test_d2_no_gel_below_gel_temperature():
    assert gel.energy_ceiling(8000, 500, 2e-3, 0.0, 350.0, 358.15, 1250, 1600, 298.15)[1] == 0.0


def test_d2_layers_matches_single_mandrel():
    _, full = gel.energy_ceiling(8000, 500, 2e-3, 0.5e-3, 423.15, 358.15, 1250, 1600, 298.15)
    lay = gel.energy_ceiling_layers([_mandrel(R_i=0.5e-3)], 358.15, 1250, 1600, 298.15)
    assert lay == pytest.approx(full)


# --- D3: analitik çözümler -----------------------------------------------------------

def test_d3_single_region_bessel_series():
    """Tek bölge: yüzeyi T_0'da tutulan silindir (Bessel serisi çözümü)."""
    a, k, rho, c = 2e-3, 16.0, 8000.0, 500.0
    alpha = k / (rho * c)
    t_end = 0.1 * a**2 / alpha        # Fourier sayısı 0,1
    T1, T0 = 400.0, 300.0
    sol = gel.solve_radial([gel.Layer(0.0, a, rho, c, k, T1)], [200], T0, t_end, 400)
    lam = jn_zeros(0, 60)
    r = sol.rc[:, None]
    theta = np.sum(2.0 / (lam * j1(lam)) * j0(lam * r / a) * np.exp(-lam**2 * 0.1), axis=1)
    exact = T0 + (T1 - T0) * theta
    assert np.max(np.abs(sol.T[-1] - exact)) < 0.003 * (T1 - T0)


def test_d3_two_identical_regions_center_temperature():
    """Sonsuz ortamda sıcak silindir: T(0,t) = T0 + (T1 − T0)(1 − exp(−a²/4αt))."""
    a, k, rho, c = 2e-3, 0.15, 1250.0, 1600.0
    alpha = k / (rho * c)
    t_end = a**2 / (4 * alpha)
    T1, T0 = 423.15, 298.15
    far = a + 10 * math.sqrt(alpha * t_end)
    layers = [gel.Layer(0.0, a, rho, c, k, T1), gel.Layer(a, far, rho, c, k, T0)]
    sol = gel.solve_radial(layers, [100, 400], T0, t_end, 400)
    exact = T0 + (T1 - T0) * (1 - math.exp(-a**2 / (4 * alpha * t_end)))
    assert sol.T[-1, 0] == pytest.approx(exact, abs=0.003 * (T1 - T0))


# --- D3: sayısal özellikler -----------------------------------------------------------

def test_d3_energy_conserved():
    res = gel.gel_layer([_mandrel()], **PLASTISOL, T_b=298.15, T_g=358.15, t_wait=10.0)
    assert res.sol.energy_error < 1e-9


def test_d3_energy_conserved_hollow_two_layers():
    layers = [_mandrel(R_i=1e-3), gel.Layer(2e-3, 2.8e-3, 1250, 1600, 0.15, 423.15)]
    res = gel.gel_layer(layers, **PLASTISOL, T_b=298.15, T_g=358.15, t_wait=20.0)
    assert res.sol.energy_error < 1e-9


def test_d3_mesh_convergence():
    levels = [{"bath": 40 * f, "mandrel": 10 * f, "steps": 50 * f} for f in (1, 2, 4, 8, 16)]
    s = [gel.gel_layer([_mandrel()], **PLASTISOL, T_b=298.15, T_g=358.15, t_wait=10.0,
                       quality=q).s_final for q in levels]
    ref = s[-1]
    errors = [abs(x - ref) for x in s[:-1]]
    assert all(e2 <= e1 + 1e-9 for e1, e2 in zip(errors, errors[1:]))
    assert errors[-1] / ref < 0.005


def test_d3_quality_presets_agree():
    res = {q: gel.gel_layer([_mandrel()], **PLASTISOL, T_b=298.15, T_g=358.15, t_wait=10.0,
                            quality=q).s_final for q in gel.QUALITY}
    assert res["hızlı"] == pytest.approx(res["hassas"], rel=0.02)
    assert res["normal"] == pytest.approx(res["hassas"], rel=0.005)


@pytest.mark.parametrize("props, T_m0, t_wait, R", [
    (STEEL, 423.15, 10.0, 2e-3),
    (STEEL, 473.15, 60.0, 1e-3),
    (dict(rho=2700.0, c=900.0, k=200.0), 453.15, 30.0, 5.5e-3),
    (STEEL, 393.15, 300.0, 1e-3),
])
def test_d3_never_exceeds_energy_ceiling(props, T_m0, t_wait, R):
    m = _mandrel(R=R, T=T_m0, **props)
    res = gel.gel_layer([m], **PLASTISOL, T_b=298.15, T_g=358.15, t_wait=t_wait, quality="hızlı")
    _, s_max = gel.energy_ceiling(m.rho, m.c, R, 0.0, T_m0, 358.15, 1250, 1600, 298.15)
    assert res.s_gel.max() <= s_max


def test_d3_gelation_irreversible():
    # ince mandrel, uzun bekleme: mandrel soğur, anlık cephe geri çekilir; jel kalınlığı geri gitmez
    res = gel.gel_layer([_mandrel(R=1e-3)], **PLASTISOL, T_b=298.15, T_g=358.15, t_wait=300.0)
    assert np.all(np.diff(res.s_gel) >= 0)
    assert np.all(res.s_gel >= res.s_raw - 1e-15)
    assert res.s_raw[-1] < res.s_gel[-1]


def test_d3_no_gel_when_mandrel_too_cold():
    res = gel.gel_layer([_mandrel(T=350.0)], **PLASTISOL, T_b=298.15, T_g=358.15, t_wait=10.0)
    assert res.s_final == 0.0


# --- D4 ------------------------------------------------------------------------------

def test_d4_fit_recovers_coefficient():
    t = np.linspace(0, 20, 50)
    alpha = 7.5e-8
    s = gel.diffusion_estimate(0.6, alpha, t)
    assert gel.fit_diffusion_coefficient(t, s, alpha) == pytest.approx(0.6)


def test_d4_coefficient_order_of_magnitude():
    res = gel.gel_layer([_mandrel()], **PLASTISOL, T_b=298.15, T_g=358.15, t_wait=10.0)
    C = gel.fit_diffusion_coefficient(res.t, res.s_gel, res.alpha_p)
    assert 0.1 < C < 3.0
