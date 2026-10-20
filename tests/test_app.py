"""Arayüzün hatasız açıldığını kontrol eden duman testleri (Streamlit AppTest)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def _app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def _texts(at):
    return " ".join(str(e.value) for e in list(at.error) + list(at.warning) + list(at.success)
                    + list(at.info) + list(at.sidebar.error) + list(at.sidebar.warning)
                    + list(at.sidebar.success))


def test_home_page_opens():
    at = _app()
    assert any("Daldırma Cidar" in t.value for t in at.title)


def test_parameter_page_example_and_draft():
    at = _app()
    at.switch_page("sayfalar/p1_parametre.py").run()
    assert not at.exception
    assert "hata" in _texts(at)                   # boş tablo
    next(b for b in at.button if "Örnek" in b.label).click().run()
    assert not at.exception
    assert "kaynaksız" in _texts(at)              # örnek değerler kaynaksız
    at.sidebar.toggle[0].set_value(True).run()
    assert not at.exception
    assert "hesaba hazır" in _texts(at)


def _ready_app():
    """Örnek değerler yüklenmiş, Taslak mod açık uygulama."""
    at = _app()
    at.switch_page("sayfalar/p1_parametre.py").run()
    next(b for b in at.button if "Örnek" in b.label).click().run()
    at.sidebar.toggle[0].set_value(True).run()
    assert not at.exception
    return at


CALC_PAGES = ["sayfalar/p2_onisitma.py", "sayfalar/p3_jel.py", "sayfalar/p4_film.py",
              "sayfalar/p5_toplam.py", "sayfalar/p6_tartim.py"]


@pytest.mark.parametrize("page", CALC_PAGES)
def test_calculation_pages_run(page):
    at = _ready_app()
    at.switch_page(page).run()
    assert not at.exception, at.exception
    assert not [e for e in at.error if "Uygun değil" not in e.value], [e.value for e in at.error]


def test_monte_carlo_page_runs():
    at = _ready_app()
    at.switch_page("sayfalar/p7_montecarlo.py").run()
    assert not at.exception
    at.number_input[0].set_value(30).run()
    next(b for b in at.button if "çalıştır" in b.label).click().run()
    assert not at.exception, at.exception
    labels = [m.label for m in at.metric]
    assert "P5" in labels and "Hedefi tutturma olasılığı" in labels
    assert at.session_state["mc"]["res"].n_ok > 0


def test_inverse_design_page_runs():
    at = _ready_app()
    at.switch_page("sayfalar/p8_ters.py").run()
    assert not at.exception
    at.select_slider[0].set_value(11).run()
    next(b for b in at.button if "Haritayı" in b.label).click().run()
    assert not at.exception, at.exception
    dm = at.session_state["ters"]["dm"]
    assert dm.w.shape == (11, 11)
    assert any("uygun bölge" in s.value for s in at.success) or at.error


def test_report_page_full_flow():
    at = _ready_app()
    at.switch_page("sayfalar/p7_montecarlo.py").run()
    at.number_input[0].set_value(30).run()
    next(b for b in at.button if "çalıştır" in b.label).click().run()
    at.switch_page("sayfalar/p8_ters.py").run()
    at.select_slider[0].set_value(11).run()
    next(b for b in at.button if "Haritayı" in b.label).click().run()
    at.switch_page("sayfalar/p9_numara.py").run()
    assert not at.exception, at.exception
    at.checkbox[0].check().run()                     # numara başına Monte Carlo
    next(b for b in at.button if "Tümünü" in b.label).click().run()
    assert not at.exception, at.exception
    res = at.session_state["numara_res"]
    assert len(res) == 1 and "P5–P95 [mm]" in res.columns
    next(b for b in at.button if "raporu hazırla" in b.label).click().run()
    assert not at.exception, at.exception
    html_text = at.session_state["report_html"]
    assert html_text.startswith("<!doctype html>") and "Ana grafikler" in html_text
    assert html_text.count('class="fig"') == 5      # jel, cidar, histogram, tornado, harita


def test_total_page_separate_second_dip():
    at = _ready_app()
    at.switch_page("sayfalar/p5_toplam.py").run()
    at.checkbox[0].check().run()
    assert not at.exception
    at.number_input[0].set_value(200.0).run()
    assert not at.exception
    assert len(at.number_input) == 2


@pytest.mark.parametrize("page", CALC_PAGES)
def test_calculation_pages_blocked_without_data(page):
    at = _app()
    at.switch_page(page).run()
    assert not at.exception
    assert any("hata" in e.value for e in at.error)


def test_gel_page_second_dip():
    at = _ready_app()
    at.switch_page("sayfalar/p3_jel.py").run()
    dip_radio = next(r for r in at.radio if r.label == "Daldırma")
    dip_radio.set_value(dip_radio.options[1]).run()
    assert not at.exception
    assert any("2. daldırma" in i.value for i in at.info)
