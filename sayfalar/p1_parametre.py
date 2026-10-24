import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from physics import film, params
from physics.symbols import GROUPS, MATERIALS, PARAMS
from physics.units import from_si, to_si
from ui import state
from ui.common import COLORS, explain, num, show_fig

st.title("0. Veri girişi")
st.markdown(
    "Hesapta kullanılan **her değer** bu sayfada girilir: malzeme özellikleri, proses ayarları, tel "
    "verileri ve formüllerin katsayıları. Programın içinde gizli bir katsayı yoktur. Her satırın "
    "**Kaynak** sütununa değeri nereden aldığını yaz (ör. \"Vinnolit TDS, s. 2\"). Satırların ne olduğu "
    "**Açıklama** sütununda ve her sekmenin altındaki listede yazar."
)

s = state.settings()

# --- Hızlı işlemler -------------------------------------------------------------------
st.caption("Program açılışta **MediClear proje verileriyle** (veriler.md, 23.10.2026) başlar. Belgede ters "
           "tasarımla belirlenecek olarak bırakılan değerler boştur; Not sütunu nedenini söyler.")
c0, c1, c2 = st.columns(3)
if c0.button("📄 MediClear proje verilerini yükle",
             help="Grubun kabul ettiği güncel parametreleri (veriler.md) kaynaklarıyla birlikte yükler; mevcut "
                  "değerlerin üzerine yazar."):
    st.session_state["pending_settings"] = params.project_settings()
    state.set_df(params.project_table())
    st.rerun()
if c1.button("📋 Örnek değerlerle doldur",
             help="Tabloyu genel örnek değerlerle (.md tipik aralıkları, ID 4 mm) doldurur; deneme içindir. "
                  "Kaynağı belli olanlara kaynak yazılır, diğerleri YAKLAŞIK işaretlenir."):
    state.set_df(params.apply_material(params.example_table(), s.mandrel_material)
                 if s.mandrel_material in MATERIALS else params.example_table())
    st.toast("Örnek değerler yazıldı. YAKLAŞIK olanları kaynağa göre teyit et.", icon="📋")
if c2.button("🗑️ Tabloyu temizle", help="Tüm değerleri, kaynakları ve notları siler."):
    state.set_df(params.empty_table())

# --- Ayarlar --------------------------------------------------------------------------
with st.expander("⚙️ Hesap ayarları", expanded=True):
    a1, a2 = st.columns(2)
    mode = a1.radio(
        "1. daldırmada mandrel sıcaklığı (T_m0)",
        ["Doğrudan gir", "D1 (fırın) + taşıma soğumasından hesapla"],
        index=0 if s.T_m0_mode == "direct" else 1,
        help="Hesaplanırsa: fırında t_ön sürede ulaşılan çıkış sıcaklığı (D1), ardından fırından banyoya "
             "t_taşıma süresince havada soğuma. D1 yalnızca dolu mandrel (R_i = 0) için geçerlidir.")
    s.T_m0_mode = "direct" if mode == "Doğrudan gir" else "D1"
    s.material_type = a2.radio("Malzeme tipi", ["Plastisol", "Organosol"],
                               index=0 if s.material_type == "Plastisol" else 1,
                               help="Organosolde (solventli) kuruyunca yalnızca katı kısım kalır: h_kuru = φ·h (D9).")
    s.spiral = a1.checkbox(
        "Spiralli tüp (iki daldırma + yay teli)", value=s.spiral,
        help="İşaretliyse cidar w = s_1 + d_tel + s_2 olarak iki daldırmayla hesaplanır (D11). "
             "Tel / 2. daldırma sekmesindeki değerler bu durumda gereklidir.")
    mats = list(MATERIALS) + ["Diğer"]
    mat = a2.selectbox("Mandrel malzemesi", mats,
                       index=mats.index(s.mandrel_material) if s.mandrel_material in mats else 0,
                       help="Seçince ρ_m, c_m ve k_m için malzeme tablosu değerleri yazılır.")
    if mat != s.mandrel_material:
        s.mandrel_material = mat
        if mat in MATERIALS:
            state.set_df(params.apply_material(state.df(), mat))
            st.toast(f"{mat} için ρ_m, c_m, k_m yazıldı (malzeme tablosu, YAKLAŞIK).", icon="🔩")

# --- Tablolar -------------------------------------------------------------------------
v = state.validation()
active = params.active_keys(s)
VAL = params.VALUE_COL
SHOW = ["Durum", "Sembol", "Parametre", "Birim", VAL, "Kaynak", "Not", "Açıklama"]
LOCKED = ["Durum", "Sembol", "Parametre", "Birim", "Açıklama"]
COLCFG = {
    "Durum": st.column_config.TextColumn(width="small", help="🟢 tamam · 🟡 kaynak yok · "
                                         "🔴 hata · ⚪ bu ayarlarla kullanılmıyor"),
    "Sembol": st.column_config.TextColumn(width="small"),
    "Birim": st.column_config.TextColumn(width="small"),
    VAL: st.column_config.NumberColumn(help="Hesapta kullanılan değer (Birim sütunundaki birimle)"),
    "Kaynak": st.column_config.TextColumn(width="medium", help="Değerin alındığı belge (TDS, kitap, "
                                          "şartname…). Boşsa satır sarı görünür."),
    "Not": st.column_config.TextColumn(width="medium"),
    "Açıklama": st.column_config.TextColumn(width="large", help="Parametrenin ne olduğu"),
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


def _editor(group: str) -> None:
    key = f"editor_{group}_{st.session_state['table_ver']}"
    st.data_editor(_view(group), key=key, hide_index=True, width="stretch",
                   disabled=LOCKED, column_config=COLCFG, num_rows="fixed",
                   on_change=_apply_edits, args=(group, key))
    with st.expander("Bu sekmedeki değerler: ne oldukları, tipik değerleri ve nereden bulunurlar"):
        for k in [k for k in params.TABLE_KEYS if PARAMS[k].group == group]:
            p = PARAMS[k]
            st.markdown(f"- **{p.sym}** – {p.name} [{p.unit}] · *Denklem:* {p.eqs} · "
                        f"*Tipik:* {p.typical} · *Nereden:* {p.source_hint}  \n  {p.help}")


def _ea_helper() -> None:
    with st.expander("🧮 E_a yardımcısı – viskozite–sıcaklık eğrisinden E_a hesapla"):
        st.markdown("TDS'deki viskozite–sıcaklık eğrisinden en az iki nokta oku ve aşağıya yaz. "
                    "Program D5'i (Arrhenius) bu noktalara uydurup E_a'yı bulur.")
        pts = st.data_editor(pd.DataFrame({"T (°C)": [25.0, 35.0, 45.0], "η (Pa·s)": [None, None, None]},
                                          dtype=float), key="ea_points", num_rows="dynamic", hide_index=True)
        pts = pts.dropna()
        if len(pts) < 2:
            st.caption("Sonucu görmek için en az iki satıra viskozite değeri yaz.")
            return
        try:
            T_K = to_si(pts["T (°C)"].to_numpy(), "°C")
            E_a, eta_ref, T_ref = film.fit_activation_energy(T_K, pts["η (Pa·s)"].to_numpy())
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success(f"E_a ≈ **{E_a:,.0f} J/mol** ({E_a / 1000:.1f} kJ/mol) · η_ref = {eta_ref:.3g} Pa·s, "
                   f"T_ref = {from_si(T_ref, '°C'):g} °C".replace(",", "."))
        Tc = np.linspace(pts["T (°C)"].min(), pts["T (°C)"].max(), 100)
        fig = go.Figure()
        fig.add_scatter(x=pts["T (°C)"], y=pts["η (Pa·s)"], mode="markers", name="TDS'den okunan nokta",
                        marker=dict(size=10, color=COLORS["accent"]))
        fig.add_scatter(x=Tc, y=film.viscosity(eta_ref, E_a, to_si(Tc, "°C"), T_ref), name="D5 uydurması",
                        line=dict(color=COLORS["line"]))
        fig.update_layout(title="Viskozite – sıcaklık (D5)", xaxis_title="Sıcaklık T [°C]",
                          yaxis_title="Viskozite η [Pa·s]")
        show_fig(fig, "Ea_uydurma", height=320)
        explain("Kırmızı noktalar veri sayfasından okuduğun değerler, mavi eğri D5 formülünün bu noktalara "
                "en iyi uyan hali. Eğri noktalardan çok sapıyorsa okuma hatası olabilir; noktaları kontrol et.")
        also = st.checkbox("η_ref ve T_ref'i de ilk noktadan yaz", value=False)
        if st.button("E_a'yı tabloya yaz"):
            df = state.df().copy()
            df.loc[df.Kod == "E_a", VAL] = round(E_a)
            df.loc[df.Kod == "E_a", "Not"] = "E_a yardımcısıyla viskozite–sıcaklık eğrisinden uyduruldu"
            if also:
                df.loc[df.Kod == "eta_ref", VAL] = eta_ref
                df.loc[df.Kod == "T_ref", VAL] = from_si(T_ref, "°C")
            state.set_df(df)
            st.rerun()


def _film_model_panel() -> None:
    st.markdown("#### Film formülü (otomatik)")
    st.markdown("Program film formülünü kendisi seçer; sayısal eşik kullanılmaz:\n\n"
                "- **R > ℓ_c (levha):** h = min(D7a, D7c) = ℓ_c·min(C_LLD·Ca^(2/3), C_grav·Ca^(1/2)). Düşük "
                "Ca'da LLD dalı, yüksek Ca'da yerçekimi dalı kendiliğinden küçük kalır (Rev. 2 Bölüm 2.4; "
                "Rio & Boulogne 2017).\n"
                "- **R ≤ ℓ_c (fiber, ince mandrel):** h = D7b.\n\n"
                "Hesapta R, filmin sürüklendiği jel yüzeyinin yarıçapıdır; sonuç **3. Sürüklenen film** "
                "sayfasında adım adım gösterilir.")
    st.latex(r"Ca = \frac{\eta U}{\gamma}, \qquad \ell_c = \sqrt{\frac{\gamma}{\rho_p g}}, \qquad "
             r"Ca^{*} = \left(\frac{C_{grav}}{C_{LLD}}\right)^{6}")
    vals = state.values_si()
    need = ["eta_ref", "E_a", "T_b", "T_ref", "U", "gamma", "rho_p", "g", "ID", "C_lld", "C_grav"]
    if all(k in vals for k in need):
        eta = float(film.viscosity(vals["eta_ref"], vals["E_a"], vals["T_b"], vals["T_ref"]))
        R = vals["ID"] / 2
        Ca = film.capillary_number(eta, vals["U"], vals["gamma"])
        lc = film.capillary_length(vals["gamma"], vals["rho_p"], vals["g"])
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        c1.metric("Ca", num(Ca, 4))
        c2.metric("Ca* (dalların kesişimi)", num(film.crossover_capillary(vals["C_lld"], vals["C_grav"]), 3))
        c3.metric("ℓ_c", f"{num(lc * 1e3, 3)} mm")
        c4.metric("R / ℓ_c (mandrel)", num(R / lc, 2),
                  help="R = ID/2. Film jel yüzeyine sürüklendiği için hesapta yarıçap biraz daha büyüktür.")
    else:
        st.caption("Ca ve ℓ_c'yi görmek için η_ref, E_a, T_b, T_ref, U, γ, ρ_p, ID ve katsayıları gir.")
    st.latex(r"\text{D7a: } h = C_{LLD}\,\frac{(\eta U)^{2/3}}{\gamma^{1/6}(\rho_p g)^{1/2}} \qquad "
             r"\text{D7b: } h = C_{fib}\,R\,Ca^{2/3}")
    st.latex(r"\text{D7c: } h = C_{grav}\sqrt{\frac{\eta U}{\rho_p g}} \qquad "
             r"\text{D8: } h_{dur} = C_{dur}\,\frac{\tau_y}{\rho_p g}")

tabs = st.tabs(list(GROUPS))
for tab, group in zip(tabs, GROUPS):
    with tab:
        if group == "Tel / 2. daldırma" and not s.spiral:
            st.info("Spiral kapalı (Hesap ayarları): bu sekmedeki değerler hesapta kullanılmıyor.")
        if group == "Tel / 2. daldırma":
            st.markdown("Spiralli tüpte 1. daldırmadan sonra yay teli sarılır ve 2. daldırma yapılır. "
                        "2. daldırmada plastisolle temas eden yüzey telin tepesidir (R + s_1 + d_tel). "
                        "Aşağıdaki sıcaklıklar mandrelin, iç katmanın ve telin **2. daldırmaya girerken** "
                        "sahip olduğu sıcaklıklardır.")
        if group == "Model katsayıları":
            _film_model_panel()
            st.markdown("#### Katsayılar")
        _editor(group)
        if group == "Plastisol":
            _ea_helper()

# --- Doğrulama özeti ------------------------------------------------------------------
st.subheader("Kontrol sonucu")
v = state.validation()
if v.errors:
    empty = [i for i in v.errors if "girilmemiş" in i.message]
    other = [i for i in v.errors if i not in empty]
    if empty:
        syms = ", ".join(PARAMS[i.key].sym for i in empty)
        st.error(f"🔴 {len(empty)} parametrenin değeri boş: {syms}.\n\n"
                 "Değerleri Değer sütununa yaz; neden boş oldukları ilgili satırın **Not** sütununda yazar "
                 "(ör. ters tasarımla belirlenecek). Yalnızca programı denemek için **Örnek değerlerle doldur** "
                 "düğmesini kullanabilirsin.")
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
                   file_name="mediclear_veriler.xlsx", width="stretch",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
k2.download_button("💾 CSV olarak kaydet", params.to_csv_bytes(state.df()),
                   file_name="mediclear_veriler.csv", mime="text/csv", width="stretch")
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
