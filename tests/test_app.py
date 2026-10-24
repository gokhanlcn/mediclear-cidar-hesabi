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


def _empty_app():
    """Tablosu temizlenmiş uygulama (açılışta proje verileri tam dolu gelir)."""
    at = _app()
    at.switch_page("sayfalar/p1_parametre.py").run()
    next(b for b in at.button if "temizle" in b.label).click().run()
    assert not at.exception
    return at


def test_parameter_page_example_and_draft():
    at = _empty_app()
    assert "hata" in _texts(at)                   # boş tablo
    next(b for b in at.button if "Örnek" in b.label).click().run()
    assert not at.exception
    assert "kaynaksız" in _texts(at)              # örnek değerlerin bir kısmı kaynaksız
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
              "sayfalar/p45_tel.py", "sayfalar/p5_toplam.py", "sayfalar/p6_tartim.py"]


@pytest.mark.parametrize("page", CALC_PAGES)
def test_calculation_pages_run(page):
    at = _ready_app()
    at.switch_page(page).run()
    assert not at.exception, at.exception
    assert not [e for e in at.error if "Uygun değil" not in e.value], [e.value for e in at.error]


def test_inverse_design_page_runs():
    at = _ready_app()
    at.switch_page("sayfalar/p8_ters.py").run()
    assert not at.exception
    _map_mode(at)
    at.select_slider[0].set_value(11).run()
    next(b for b in at.button if "Haritayı" in b.label).click().run()
    assert not at.exception, at.exception
    dm = at.session_state["ters"]["dm"]
    assert dm.w.shape == (11, 11)
    assert any("uygun bölge" in s.value for s in at.success) or at.error


def test_report_page_full_flow():
    at = _ready_app()
    at.switch_page("sayfalar/p8_ters.py").run()
    _map_mode(at)
    at.select_slider[0].set_value(11).run()
    next(b for b in at.button if "Haritayı" in b.label).click().run()
    at.switch_page("sayfalar/p9_numara.py").run()
    assert not at.exception, at.exception
    next(b for b in at.button if "Tümünü" in b.label).click().run()
    assert not at.exception, at.exception
    res = at.session_state["numara_res"]
    assert len(res) == 1 and {"s_1 [mm]", "s_2 [mm]", "w [mm]", "OD hesap [mm]"} <= set(res.columns)
    next(b for b in at.button if "raporu hazırla" in b.label).click().run()
    assert not at.exception, at.exception
    html_text = at.session_state["report_html"]
    assert html_text.startswith("<!doctype html>") and "Ana grafikler" in html_text
    assert html_text.count('class="fig"') == 3      # jel, cidar, harita
    assert "Doğrulama durumu" in html_text and "Tel halkası (2. daldırma)" in html_text
    assert "D1–D12" not in html_text


@pytest.mark.parametrize("page", CALC_PAGES)
def test_calculation_pages_blocked_without_data(page):
    at = _empty_app()
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


def test_weighing_page_second_dip_expected_mass():
    at = _ready_app()
    at.switch_page("sayfalar/p6_tartim.py").run()
    r = next(r for r in at.radio if r.label == "Tartılan daldırma")
    r.set_value(r.options[1]).run()
    assert not at.exception, at.exception
    titles = " ".join(m.value for m in at.markdown)
    assert "Oluklara dolan plastisol" in titles and "beklenen toplam kütle" in titles

def test_inverse_design_U_vs_drain_axes():
    at = _ready_app()
    at.switch_page("sayfalar/p8_ters.py").run()
    _map_mode(at)
    sb = [s for s in at.selectbox]
    sb[0].set_value("U").run()                       # dikey eksen
    next(s for s in at.selectbox if s.label == "Yatay eksen").set_value("t_drain").run()
    at.select_slider[0].set_value(11).run()
    next(b for b in at.button if "Haritayı" in b.label).click().run()
    assert not at.exception, at.exception
    dm = at.session_state["ters"]["dm"]
    assert (dm.y_key, dm.x_key) == ("U", "t_drain") and dm.w.shape == (11, 11)

def _map_mode(at):
    next(r for r in at.radio if r.label == "Ne yapmak istiyorsun?").set_value("B. İki değişkenli ayar haritası").run()
    assert not at.exception, at.exception


def test_inverse_layer_targets():
    at = _ready_app()
    at.switch_page("sayfalar/p8_ters.py").run()
    assert not at.exception, at.exception
    at.select_slider[0].set_value(3).run()                   # U nokta sayısı
    next(b for b in at.button if "Ayarları bul" in b.label).click().run()
    assert not at.exception, at.exception
    sols = at.session_state["ters_A"]["sols"]
    assert len(sols) == 3
    # örnek veri setinde (ID 4 / OD 6, tel 0,3) örtüye 0,15 mm kalır; her satır ya çözülür ya da nedenini söyler
    assert all((s.T_m0 is not None and s.T_m0_2 is not None) or s.note for s in sols)
    assert any("U düşürülmeli" in s.note for s in sols)


def test_project_data_opens_ready():
    """Açılıştaki proje verileri (Özet Rapor, 24.10.2026) eksiksiz: toplam sayfası hesaplar."""
    at = _app()
    at.switch_page("sayfalar/p5_toplam.py").run()
    assert not at.exception, at.exception
    assert not [e for e in at.error if "Uygun değil" not in e.value], [e.value for e in at.error]
