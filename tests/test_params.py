import numpy as np
import pytest

from physics import params
from physics.params import Settings


def _set(df, key, **cols):
    df = df.copy()
    for c, v in cols.items():
        df.loc[df.Kod == key, c] = v
    return df


def test_empty_table_blocks_calculation():
    v = params.validate(params.empty_table(), Settings())
    assert v.errors and not v.can_calculate(draft=True)


def test_example_table_is_valid_but_needs_sources():
    v = params.validate(params.example_table(), Settings())
    assert not v.errors
    assert v.missing_source
    assert not v.can_calculate(draft=False) and v.can_calculate(draft=True)


def test_example_values_have_approx_note():
    df = params.example_table()
    assert (df.loc[df.Kod == "rho_p", "Not"] == params.APPROX_NOTE).all()


def test_min_nominal_max_order():
    df = _set(params.example_table(), "rho_p", Min=1300.0, Max=1200.0)
    v = params.validate(df, Settings())
    assert any(i.key == "rho_p" and i.level == "hata" for i in v.issues)


@pytest.mark.parametrize("key, value", [("rho_p", -5.0), ("eps", 1.5), ("k_m", 0.0)])
def test_bounds(key, value):
    df = _set(params.example_table(), key, Min=value, Nominal=value, Max=value)
    assert any(i.key == key for i in params.validate(df, Settings()).errors)


def test_temperature_relations():
    df = _set(params.example_table(), "T_b", Min=90.0, Nominal=90.0, Max=90.0)
    assert any(i.key == "T_b" for i in params.validate(df, Settings()).errors)
    df = _set(params.example_table(), "T_m0", Min=80.0, Nominal=80.0, Max=80.0)
    assert any(i.key == "T_m0" for i in params.validate(df, Settings()).errors)


def test_d1_requires_solid_mandrel():
    df = _set(params.example_table(), "R_i", Min=0.5, Nominal=0.5, Max=0.5)
    v = params.validate(df, Settings(T_m0_mode="D1"))
    assert any(i.key == "R_i" for i in v.errors)


def test_d1_mode_ignores_T_m0_row():
    df = _set(params.example_table(), "T_m0", Min=np.nan, Nominal=np.nan, Max=np.nan)
    assert not params.validate(df, Settings(T_m0_mode="D1")).errors
    assert params.validate(df, Settings()).errors


def test_model_keys_exclude_unused_d1_inputs():
    direct = params.model_keys(Settings())
    assert "T_0" not in direct and "T_m0" in direct
    d1 = params.model_keys(Settings(T_m0_mode="D1"))
    assert "T_0" in d1 and "T_m0" not in d1


def test_pm10():
    df = _set(params.example_table(), "gamma", Min=np.nan, Max=np.nan)
    new, changed = params.apply_pm10(df)
    row = new[new.Kod == "gamma"].iloc[0]
    assert "gamma" in changed and "rho_p" not in changed      # rho_p'nin aralığı zaten var
    assert not set(changed) & params.NO_PM10
    assert row.Min == pytest.approx(0.0315) and row.Max == pytest.approx(0.0385)
    assert params.PM10_NOTE in row.Not


def test_editor_changes_map_to_group_rows():
    df = params.example_table()
    pos = list(df[df.Grup == "Proses"].Kod).index("U")
    new = params.apply_editor_changes(df, "Proses", {pos: {"Nominal": 2.0, "Kaynak": "Servo föyü"},
                                                     0: {"Min": None}})
    row = new[new.Kod == "U"].iloc[0]
    assert row.Nominal == 2.0 and row.Kaynak == "Servo föyü"
    assert np.isnan(new[new.Grup == "Proses"].iloc[0].Min)
    assert new[new.Grup != "Proses"].equals(df[df.Grup != "Proses"])


def test_si_conversion():
    df = params.example_table()
    nom = params.nominal_si(df)
    assert nom["T_g"] == pytest.approx(358.15)
    assert nom["ID"] == pytest.approx(4e-3)
    assert params.ranges_si(df)["U"] == pytest.approx((0.5e-3, 1e-3, 5e-3))


def test_excel_round_trip():
    df = _set(params.example_table(), "rho_p", Kaynak="Test TDS s.2")
    s = Settings(T_m0_mode="D1", spiral=False, draft=True, mandrel_material="Alüminyum")
    back, s2, notes = params.load_file(params.to_excel_bytes(df, s), "x.xlsx")
    assert not notes
    assert back.loc[back.Kod == "rho_p", "Kaynak"].iloc[0] == "Test TDS s.2"
    np.testing.assert_allclose(back.Nominal.to_numpy(dtype=float), df.Nominal.to_numpy(dtype=float))
    assert s2 == s


def test_csv_round_trip():
    df = params.example_table()
    back, s2, _ = params.load_file(params.to_csv_bytes(df), "x.csv")
    assert s2 is None
    np.testing.assert_allclose(back.Max.to_numpy(dtype=float), df.Max.to_numpy(dtype=float))


def test_load_rejects_unknown_file():
    with pytest.raises(ValueError):
        params.load_file(b"abc", "x.txt")
