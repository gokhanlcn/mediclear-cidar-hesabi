import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from physics import film, params
from physics.symbols import GROUPS, MATERIALS, PARAMS
from physics.units import from_si, to_si
from ui import state
from ui.common import COLORS, explain, show_fig

st.title("1. Parametre girişi")
st.markdown(
    "Aşağıdaki tablo .md dosyasındaki **Veri giriş tablosu**nun aynısıdır. **Nominal** sütunu tek "
    "hesap için, **Min** ve **Max** belirsizlik analizi (Monte Carlo) için kullanılır. Her değerin "
    "**Kaynak** sütununa nereden aldığını yaz (ör. \"Vinnolit TDS, s. 2\")."
)

s = state.settings()

# --- Hızlı işlemler -------------------------------------------------------------------
c1, c2, c3 = st.columns(3)
if c1.button("📋 Örnek değerlerle doldur",
             help="Tüm tabloyu .md'deki 'Tipik aralık' değerleriyle doldurur (mevcut değerlerin "
                  "üzerine yazar). Değerler YAKLAŞIK'tır, kaynak sütunu boş kalır."):
    state.set_df(params.apply_material(params.example_table(), s.mandrel_material)
                 if s.mandrel_material in MATERIALS else params.example_table())
    st.toast("Örnek değerler yazıldı. Hepsi YAKLAŞIK – kaynağa göre teyit edin.", icon="📋")
if c2.button("±%10 uygula",
             help=".md kuralı: bir değer için tek kaynak varsa Min ve Max nominalin ±%10'u alınır. "
                  "Yalnızca Min ve Max'ı boş (veya nominale eşit) satırlara uygulanır."):
    new, changed = params.apply_pm10(state.df())
    state.set_df(new)
    st.toast(f"{len(changed)} satıra ±%10 uygulandı." if changed else
             "Min/Max'ı boş satır bulunamadı.", icon="✏️")
if c3.button("🗑️ Tabloyu temizle",
             help="Tüm değerleri, kaynakları ve notları siler."):
    state.set_df(params.empty_table())

# --- Ayarlar --------------------------------------------------------------------------
with st.expander("⚙️ Hesap ayarları", expanded=True):
    a1, a2 = st.columns(2)
    mode = a1.radio(
        "Daldırma anındaki mandrel sıcaklığı (T_m0)",
        ["Doğrudan gir", "D1'den hesapla (ön ısıtma fırını)"],
        index=0 if s.T_m0_mode == "direct" else 1,
        help="D1'den hesaplanırsa T_m0 = fırında t_ön süre sonra ulaşılan sıcaklık. "
             "D1 yalnızca dolu mandrel (R_i = 0) için geçerlidir.")
    s.T_m0_mode = "direct" if mode == "Doğrudan gir" else "D1"
    kind = a2.radio("Malzeme tipi", ["Plastisol", "Organosol"],
                    index=0 if s.material_type == "Plastisol" else 1,
                    help="Organosolde (solventli) kuruyunca yalnızca katı kısım kalır: h_kuru = φ·h (D9).")
    s.material_type = kind
    s.spiral = a1.checkbox(
        "Spiralli tüp (iki daldırma + yay teli)", value=s.spiral,
        help="İşaretliyse cidar w = s_1 + d_tel + s_2 olarak iki daldırmayla hesaplanır (D11).")
    mats = list(MATERIALS) + ["Diğer"]
    mat = a2.selectbox("Mandrel malzemesi", mats,
                       index=mats.index(s.mandrel_material) if s.mandrel_material in mats else 0,
                       help="Seçince ρ_m, c_m ve k_m için önerilen değerler yazılabilir.")
    if mat != s.mandrel_material:
        s.mandrel_material = mat
        if mat in MATERIALS:
            state.set_df(params.apply_material(state.df(), mat))
            st.toast(f"{mat} için ρ_m, c_m, k_m yazıldı (malzeme tablosu, YAKLAŞIK).", icon="🔩")

# --- Tablolar -------------------------------------------------------------------------
v = state.validation()
active = params.active_keys(s)
SHOW = ["Durum", "Sembol", "Parametre", "Birim", "Min", "Nominal", "Max", "Kaynak", "Not", "Açıklama"]
LOCKED = ["Durum", "Sembol", "Parametre", "Birim", "Açıklama"]
COLCFG = {
    "Durum": st.column_config.TextColumn(width="small", help="🟢 tamam · 🟡 kaynak yok · "
                                         "🔴 hata · ⚪ bu ayarlarla kullanılmıyor"),
    "Sembol": st.column_config.TextColumn(width="small"),
    "Birim": st.column_config.TextColumn(width="small"),
    "Min": st.column_config.NumberColumn(help="Monte Carlo için en küçük olası değer"),
    "Nominal": st.column_config.NumberColumn(help="Tek hesapta kullanılan değer"),
    "Max": st.column_config.NumberColumn(help="Monte Carlo için en büyük olası değer"),
    "Kaynak": st.column_config.TextColumn(width="medium", help="Değerin alındığı belge (TDS, kitap, "
                                          "şartname…). Boşsa satır sarı görünür."),
    "Not": st.column_config.TextColumn(width="medium"),
    "Açıklama": st.column_config.TextColumn(width="large", help="Parametrenin kısa açıklaması"),
}


def _view(group: str) -> pd.DataFrame:
    df = state.df()
    sub = df[df.Grup == group].copy()
    sub["Durum"] = [v.status(k, k in active or k == "T_fuz") for k in sub.Kod]
    sub["Açıklama"] = [PARAMS[k].help for k in sub.Kod]
    return sub[SHOW]


def _apply_edits(group: str, key: str) -> None:
    edits = st.session_state[key].get("edited_rows", {})
    state.set_df(params.apply_editor_changes(state.df(), group, edits))


tabs = st.tabs([f"{g}" for g in GROUPS])
for tab, group in zip(tabs, GROUPS):
    with tab:
        key = f"editor_{group}_{st.session_state['table_ver']}"
        st.data_editor(_view(group), key=key, hide_index=True,
                       disabled=LOCKED, column_config=COLCFG, num_rows="fixed",
                       on_change=_apply_edits, args=(group, key))
        with st.expander("Bu sekmedeki parametreler: tipik aralık ve nereden bulunur"):
            for k in [k for k in params.TABLE_KEYS if PARAMS[k].group == group]:
                p = PARAMS[k]
                st.markdown(f"- **{p.sym}** – {p.name} [{p.unit}] · *Denklem:* {p.eqs} · "
                            f"*Tipik:* {p.typical} · *Nereden:* {p.source_hint}  \n  {p.help}")

        if group == "Plastisol":
            with st.expander("🧮 E_a yardımcısı – viskozite–sıcaklık eğrisinden E_a hesapla"):
                st.markdown(
                    "TDS'deki viskozite–sıcaklık eğrisinden en az iki nokta oku ve aşağıya yaz. "
                    "Program D5'i (Arrhenius) bu noktalara uydurup E_a'yı bulur.")
                pts = st.data_editor(
                    pd.DataFrame({"T (°C)": [25.0, 35.0, 45.0], "η (Pa·s)": [None, None, None]},
                                 dtype=float),
                    key="ea_points", num_rows="dynamic", hide_index=True)
                pts = pts.dropna()
                if len(pts) >= 2:
                    try:
                        T_K = to_si(pts["T (°C)"].to_numpy(), "°C")
                        E_a, eta_ref, T_ref = film.fit_activation_energy(T_K, pts["η (Pa·s)"].to_numpy())
                        st.success(f"E_a ≈ **{E_a:,.0f} J/mol** ({E_a / 1000:.1f} kJ/mol) · "
                                   f"η_ref = {eta_ref:.3g} Pa·s, T_ref = {from_si(T_ref, '°C'):g} °C"
                                   .replace(",", "."))
                        Tc = np.linspace(pts["T (°C)"].min(), pts["T (°C)"].max(), 100)
                        fig = go.Figure()
                        fig.add_scatter(x=pts["T (°C)"], y=pts["η (Pa·s)"], mode="markers",
                                        name="TDS'den okunan nokta",
                                        marker=dict(size=10, color=COLORS["accent"]))
                        fig.add_scatter(x=Tc, y=film.viscosity(eta_ref, E_a, to_si(Tc, "°C"), T_ref),
                                        name="D5 uydurması", line=dict(color=COLORS["line"]))
                        fig.update_layout(xaxis_title="Sıcaklık T [°C]", yaxis_title="Viskozite η [Pa·s]",
                                          title="Viskozite – sıcaklık (D5)")
                        show_fig(fig, "Ea_uydurma", height=320)
                        explain("Kırmızı noktalar veri sayfasından okuduğun değerler, mavi eğri D5 "
                                "formülünün bu noktalara en iyi uyan hali. Eğri noktalardan çok "
                                "sapıyorsa okuma hatası olabilir; noktaları kontrol et.")
                        also = st.checkbox("η_ref ve T_ref'i de ilk noktadan yaz", value=False)
                        if st.button("E_a'yı tabloya yaz"):
                            df = state.df().copy()
                            sel = df.Kod == "E_a"
                            df.loc[sel, params.VALUE_COLS] = [np.nan, round(E_a), np.nan]
                            df.loc[sel, "Not"] = ("E_a yardımcısıyla viskozite–sıcaklık eğrisinden "
                                                  "uyduruldu; Min/Max'ı gir veya ±%10 uygula")
                            if also:
                                df.loc[df.Kod == "eta_ref", "Nominal"] = eta_ref
                                df.loc[df.Kod == "T_ref", "Nominal"] = from_si(T_ref, "°C")
                            state.set_df(df)
                            st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                else:
                    st.caption("Sonucu görmek için en az iki satıra viskozite değeri yaz.")

# --- Doğrulama özeti ------------------------------------------------------------------
st.subheader("Kontrol sonucu")
v = state.validation()
if v.errors:
    empty = [i for i in v.errors if "girilmemiş" in i.message]
    other = [i for i in v.errors if i not in empty]
    if empty:
        syms = ", ".join(PARAMS[i.key].sym for i in empty)
        st.error(f"🔴 {len(empty)} parametrenin Nominal değeri boş: {syms}.\n\n"
                 "Veri sayfasından değerleri bulup Nominal sütununa yaz. Elinde henüz veri yoksa "
                 "yukarıdaki **Örnek değerlerle doldur** düğmesine bas.")
    if other:
        st.error(f"🔴 {len(other)} hata var – düzeltilmeden hesap yapılamaz:\n\n"
                 + "\n".join(f"- {i.message}" for i in other))
if v.missing_source:
    syms = ", ".join(PARAMS[k].sym for k in v.missing_source)
    msg = (f"🟡 Kaynağı boş {len(v.missing_source)} parametre: {syms}.\n\n"
           ".md kuralı: kaynağı olmayan değer hesaba girmez. ")
    msg += ("Taslak mod açık: bu değerlerle hesap yapılacak ama her sayfada uyarı gösterilecek."
            if s.draft else "Hesap yapmak için kaynakları doldur ya da sol menüden **Taslak mod**'u aç.")
    st.warning(msg)
if v.warnings:
    with st.expander(f"🟠 {len(v.warnings)} uyarı (hesabı engellemez)"):
        for i in v.warnings:
            st.markdown(f"- {i.message}")
if v.can_calculate(s.draft):
    st.success("🟢 Veriler hesaba hazır. Sol menüden sonraki sayfalara geçebilirsin.")

# --- Kaydet / yükle -------------------------------------------------------------------
st.subheader("Kaydet / yükle")
st.markdown("Veri setini kaydedip grup arkadaşlarınla paylaşabilir, sonra buradan geri yükleyebilirsin.")
k1, k2 = st.columns(2)
k1.download_button("💾 Excel olarak kaydet", params.to_excel_bytes(state.df(), s),
                   file_name="mediclear_parametreler.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
k2.download_button("💾 CSV olarak kaydet", params.to_csv_bytes(state.df()),
                   file_name="mediclear_parametreler.csv", mime="text/csv")
up = st.file_uploader("Kaydedilmiş dosyayı yükle (.xlsx veya .csv)", type=["xlsx", "csv"])
if up is not None and st.session_state.get("last_upload") != up.file_id:
    st.session_state["last_upload"] = up.file_id
    try:
        new_df, new_settings, notes = params.load_file(up.getvalue(), up.name)
        state.set_df(new_df)
        if new_settings is not None:
            st.session_state["pending_settings"] = new_settings
        st.session_state["load_notes"] = notes
        st.toast(f"'{up.name}' yüklendi.", icon="✅")
        st.rerun()
    except Exception as exc:  # okunamayan dosya: sade mesaj
        st.error(f"Dosya okunamadı: {exc}")
for n in st.session_state.pop("load_notes", []):
    st.warning(n)
