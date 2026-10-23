import numpy as np
import pytest

from physics import params
from physics.params import VALUE_COL, Settings
from physics.symbols import GROUPS, PARAMS

READY = dict(film_model="D7a")


def _set(df, key, **cols):
    df = df.copy()
    for c, v in cols.items():
        df.loc[df.Kod == key, VALUE_COL if c == "val" else c] = v
    return df


def test_table_columns_have_no_ranges():
    df = params.empty_table()
    assert list(df.columns) == params.COLUMNS
    assert "Min" not in df.columns and "Max" not in df.columns


def test_every_parameter_group_is_a_tab():
    assert {p.group for p in PARAMS.values()} <= set(GROUPS)


def test_empty_table_blocks_calculation():
    v = params.validate(params.empty_table(), Settings(**READY))
    assert v.errors and not v.can_calculate(draft=True)


def test_film_model_must_be_chosen():
    v = params.validate(params.example_table(), Settings())
    assert any("Film formülü" in i.message for i in v.errors)
    assert not params.validate(params.example_table(), Settings(**READY)).errors


def test_example_table_sources():
    df = params.example_table()
    v = params.validate(df, Settings(**READY))
    assert v.missing_source and v.can_calculate(draft=True) and not v.can_calculate(draft=False)
    # kaynağı belli örnekler (model katsayıları) kaynakla gelir, diğerleri YAKLAŞIK
    assert "C_lld" not in v.missing_source
    assert (df.loc[df.Kod == "rho_p", "Not"] == params.APPROX_NOTE).all()


def test_unused_coefficients_not_required():
    df = _set(params.example_table(), "C_fib", val=np.nan)
    assert not params.validate(df, Settings(film_model="D7a")).errors
    assert params.validate(df, Settings(film_model="D7b")).errors


def test_wire_inputs_only_with_spiral():
    df = _set(params.example_table(), "p_wire", val=np.nan)
    assert not params.validate(df, Settings(spiral=False, **READY)).errors
    assert params.validate(df, Settings(spiral=True, **READY)).errors


def test_pitch_smaller_than_wire_is_error():
    df = _set(params.example_table(), "p_wire", val=0.1)
    assert any(i.key == "p_wire" for i in params.validate(df, Settings(**READY)).errors)


@pytest.mark.parametrize("key, value", [("rho_p", -5.0), ("eps", 1.5), ("k_m", 0.0)])
def test_bounds(key, value):
    df = _set(params.example_table(), key, val=value)
    assert any(i.key == key for i in params.validate(df, Settings(**READY)).errors)


def test_temperature_relations():
    df = _set(params.example_table(), "T_b", val=90.0)
    assert any(i.key == "T_b" for i in params.validate(df, Settings(**READY)).errors)
    df = _set(params.example_table(), "T_m0", val=80.0)
    assert any(i.key == "T_m0" for i in params.validate(df, Settings(**READY)).errors)


def test_d1_requires_solid_mandrel():
    df = _set(params.example_table(), "R_i", val=0.5)
    v = params.validate(df, Settings(T_m0_mode="D1", **READY))
    assert any(i.key == "R_i" for i in v.errors)


def test_d1_mode_ignores_T_m0_row():
    df = _set(params.example_table(), "T_m0", val=np.nan)
    assert not params.validate(df, Settings(T_m0_mode="D1", **READY)).errors
    assert params.validate(df, Settings(**READY)).errors


def test_editor_changes_map_to_group_rows():
    df = params.example_table()
    pos = list(df[df.Grup == "Proses"].Kod).index("U")
    new = params.apply_editor_changes(df, "Proses", {pos: {VALUE_COL: 2.0, "Kaynak": "Servo föyü"},
                                                     0: {VALUE_COL: None}})
    row = new[new.Kod == "U"].iloc[0]
    assert row[VALUE_COL] == 2.0 and row.Kaynak == "Servo föyü"
    assert np.isnan(new[new.Grup == "Proses"].iloc[0][VALUE_COL])
    assert new[new.Grup != "Proses"].equals(df[df.Grup != "Proses"])


def test_si_conversion():
    v = params.values_si(params.example_table())
    assert v["T_g"] == pytest.approx(358.15)
    assert v["ID"] == pytest.approx(4e-3)
    assert v["U"] == pytest.approx(1e-3)
    assert v["C_lld"] == pytest.approx(0.94)


def test_excel_round_trip():
    df = _set(params.example_table(), "rho_p", Kaynak="Test TDS s.2")
    s = Settings(T_m0_mode="D1", spiral=False, draft=True, mandrel_material="Alüminyum", film_model="min_ac")
    back, s2, notes = params.load_file(params.to_excel_bytes(df, s), "x.xlsx")
    assert not notes
    assert back.loc[back.Kod == "rho_p", "Kaynak"].iloc[0] == "Test TDS s.2"
    np.testing.assert_allclose(back[VALUE_COL].to_numpy(dtype=float), df[VALUE_COL].to_numpy(dtype=float))
    assert s2 == s


def test_csv_round_trip():
    df = params.example_table()
    back, s2, _ = params.load_file(params.to_csv_bytes(df), "x.csv")
    assert s2 is None
    np.testing.assert_allclose(back[VALUE_COL].to_numpy(dtype=float), df[VALUE_COL].to_numpy(dtype=float))


def test_old_files_with_nominal_column_load():
    old = params.example_table().rename(columns={VALUE_COL: "Nominal"})
    old["Min"], old["Max"] = old["Nominal"], old["Nominal"]
    data = old[["Kod", "Sembol", "Parametre", "Birim", "Min", "Nominal", "Max", "Kaynak", "Not"]].to_csv(
        index=False, sep=";", decimal=",").encode("utf-8-sig")
    back, _, _ = params.load_file(data, "eski.csv")
    assert back.loc[back.Kod == "rho_p", VALUE_COL].iloc[0] == 1250


def test_load_rejects_unknown_file():
    with pytest.raises(ValueError):
        params.load_file(b"abc", "x.txt")


def test_project_table_matches_veriler_md():
    from physics.project_data import PROJECT_DATA, missing_keys
    df = params.project_table()
    v = params.values_si(df)
    assert v["ID"] == pytest.approx(8e-3) and v["OD"] == pytest.approx(10.8e-3)
    assert v["OD_tol"] == pytest.approx(0.2e-3) and v["p_wire"] == pytest.approx(1.3e-3)
    assert v["rho_m"] == 7990 and v["C_grav"] == 1.0 and v["C_dur"] == 0.3
    assert v["T_g"] == pytest.approx(343.15) and v["tau_y"] == 0.0
    # değeri olan her satırın kaynağı var; değeri olmayanlar boş
    for k, (val, src, _) in PROJECT_DATA.items():
        row = df[df.Kod == k].iloc[0]
        assert (np.isnan(row[VALUE_COL]) if val is None else bool(row.Kaynak))
    assert set(missing_keys()) == {"t_pre", "T_m0", "U", "t_drain", "T_m0_2", "T_s1", "T_t"}
    assert params.project_settings().mandrel_material == "316L paslanmaz"


def test_t_pre_not_required_in_direct_mode():
    assert "t_pre" not in params.active_keys(Settings())
    assert "t_pre" in params.active_keys(Settings(T_m0_mode="D1"))


def test_link_second_dip_temperatures():
    df = _set(params.project_table(), "T_m0", val=100.0)
    new, changed = params.link_second_dip_temperatures(df)
    assert set(changed) == {"T_m0_2", "T_s1", "T_t"}
    for k in ("T_m0_2", "T_s1", "T_t"):
        assert new.loc[new.Kod == k, VALUE_COL].iloc[0] == 100.0
    new2, changed2 = params.link_second_dip_temperatures(_set(new, "T_m0_2", val=95.0))
    assert new2.loc[new2.Kod == "T_t", VALUE_COL].iloc[0] == 95.0 and "T_m0_2" not in changed2
    _, none = params.link_second_dip_temperatures(params.project_table())
    assert none == []


def test_project_data_runs_once_open_values_given():
    from physics.model import Options, run_model
    df = params.project_table()
    for k, val in (("T_m0", 100.0), ("U", 1.0), ("t_drain", 10.0)):
        df = _set(df, k, val=val, Kaynak="test")
    df, _ = params.link_second_dip_temperatures(df)
    s = Settings(film_model="D7c")
    assert not params.validate(df, s).errors
    res = run_model(params.values_si(df), Options(film_model="D7c", quality="hızlı"))
    assert res.dip2 is not None and res.w > 0