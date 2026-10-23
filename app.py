"""MediClear – Daldırma cidar kalınlığı hesap programı (Streamlit giriş noktası).

Çalıştırma: baslat.bat (Windows) veya baslat.sh (macOS/Linux).
"""

import streamlit as st

from ui import state
from ui.common import DISCLAIMER

st.set_page_config(page_title="MediClear Cidar Hesabı", page_icon="🧪", layout="wide")
state.init()

PAGES = {
    "Başlangıç": [
        st.Page("sayfalar/p0_giris.py", title="Nasıl kullanılır?", icon="🏠", default=True),
        st.Page("sayfalar/p1_parametre.py", title="0. Veri girişi", icon="📝", url_path="veri"),
    ],
    "Hesap adımları": [
        st.Page("sayfalar/p2_onisitma.py", title="1. Mandrel ön ısıtma (D1)", icon="🔥",
                url_path="onisitma"),
        st.Page("sayfalar/p3_jel.py", title="2. Jel katmanı (D2–D4)", icon="🧊", url_path="jel"),
        st.Page("sayfalar/p4_film.py", title="3. Sürüklenen film (D5–D8)", icon="💧", url_path="film"),
        st.Page("sayfalar/p5_toplam.py", title="4. Toplam cidar (D9, D11)", icon="📏", url_path="toplam"),
        st.Page("sayfalar/p6_tartim.py", title="5. Tartımla doğrulama (D10)", icon="⚖️", url_path="tartim"),
    ],
    "Analiz": [
        st.Page("sayfalar/p8_ters.py", title="6. Ters tasarım (ayar haritası)", icon="🗺️",
                url_path="ters-tasarim"),
    ],
    "Sonuç": [
        st.Page("sayfalar/p9_numara.py", title="7. Numara bazında sonuçlar ve rapor", icon="📄",
                url_path="rapor"),
    ],
}

nav = st.navigation(PAGES)

with st.sidebar:
    st.toggle("Taslak mod", key="draft_toggle",
              help="Açıkken Kaynak sütunu boş olan değerlerle de hesap yapılır; her sayfada ve "
                   "raporda uyarı gösterilir. Kapalıyken (.md kuralı) kaynaksız değer hesaba girmez.")
    status_box = st.empty()
    st.caption("Denklemler: cidar_kalinligi_hesabi.md (D1–D12)")
state.settings().draft = st.session_state["draft_toggle"]

st.info(f"ℹ️ {DISCLAIMER}")
try:
    nav.run()
finally:
    # Sayfadaki değişikliklerden sonra güncel durum
    v, s = state.validation(), state.settings()
    with status_box.container():
        if v.errors:
            st.error(f"🔴 {len(v.errors)} hata – hesap yapılamaz")
        elif v.missing_source and not s.draft:
            st.warning(f"🟡 {len(v.missing_source)} kaynaksız değer – Taslak mod kapalı")
        elif v.missing_source:
            st.warning(f"🟡 Taslak mod: {len(v.missing_source)} kaynaksız değer kullanılıyor")
        else:
            st.success("🟢 Veriler hesaba hazır")
