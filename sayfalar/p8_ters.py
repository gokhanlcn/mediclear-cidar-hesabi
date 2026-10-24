import math
from dataclasses import astuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from physics import inverse, preheat
from physics.inverse import AXES
from physics.model import ModelError, run_model
from physics.units import from_si, to_si
from ui import charts, compute, state
from ui.common import COLORS, assumptions, draft_banner, explain, num, show_fig

st.title("7. Ters tasarım")

with st.container(border=True):
    st.markdown(
        "**Ters tasarım nedir?** Önceki sayfalar *ayarlardan kalınlığı* hesaplar: mandrel sıcaklığı, bekleme "
        "süresi, çekme hızı … verilir, cidar kalınlığı bulunur. Ters tasarım bunun tersidir: **hedef kalınlık "
        "verilir, o kalınlığı veren ayarlar bulunur.** Bu sayfada iki araç var:\n\n"
        "- **A. Katman hedefinden ayar bul (önerilen):** İç katman ve örtü için hedef kalınlığı gir. Program her "
        "çekme hızı U için, 1. katı hedefe getiren mandrel sıcaklığını (T_m0) ve örtüyü hedefe getiren 2. "
        "daldırma sıcaklığını (T_m0,2) kendisi bulur. Fırın ayarını seçmek için kullanılır.\n"
        "- **B. İki değişkenli ayar haritası:** İki ayarı (ör. U ve t_süz) bir aralıkta tarar, her çift için "
        "toplam cidarı hesaplar ve hedefi tutturan bölgeyi haritada boyar. Ayarların birbirine göre ne kadar "
        "esnek olduğunu görmek için kullanılır.\n\n"
        "**Neden U önemli?** Kalınlık iki parçadan oluşur: **jel** (mandrelin ısısıyla katılaşan katman; "
        "mandrel sıcaklığı ve bekleme süresiyle artar) ve **film** (çekerken sürüklenen sıvı; çekme hızıyla "
        "artar). U büyüdükçe film kalınlaşır ve jele kalan pay azalır. Film tek başına hedefi aşarsa hiçbir "
        "sıcaklık hedefi tutturamaz; bu durumda U düşürülmelidir.")

mode = st.radio("Ne yapmak istiyorsun?",
                ["A. Katman hedefinden ayar bul", "B. İki değişkenli ayar haritası"], horizontal=True)

degC = lambda T: from_si(T, "°C")  # noqa: E731
mm = lambda x: from_si(x, "mm")  # noqa: E731


def furnace_columns(p: dict, R: float, T_m0: float) -> dict:
    """Banyoya T_m0 ile girmek için gereken fırın çıkışı (taşıma soğumasının tersi) ve fırın süresi (D1)."""
    if p.get("R_i", 0) > 0 or not all(k in p for k in ("T_oven", "h_oven", "T_0")):
        return {}
    T_exit = T_m0
    if all(k in p for k in ("t_tr", "T_amb", "h_amb")):
        tau_t = preheat.time_constant(p["rho_m"], p["c_m"], R, p["h_amb"])
        T_exit = p["T_amb"] + (T_m0 - p["T_amb"]) * math.exp(p["t_tr"] / tau_t)
    tau = preheat.time_constant(p["rho_m"], p["c_m"], R, p["h_oven"])
    t_pre = preheat.time_to_reach(T_exit, p["T_oven"], p["T_0"], tau)
    return {"Gerekli fırın çıkışı [°C]": round(degC(T_exit), 1),
            "Gerekli t_ön (D1) [s]": "ulaşılamaz (T_fırın düşük)" if math.isinf(t_pre) else round(t_pre)}


# =======================================================================================
# A. Katman hedefinden ayar bulma
# =======================================================================================
if mode.startswith("A"):
    solved = {"U", "T_m0", "T_m0_2", "T_s1", "T_t", "t_pre"}
    v = state.require_ready(optional=solved)
    s = state.settings()
    draft_banner(v, s)
    p = state.values_si()
    if not s.spiral:
        st.info("Spiral kapalı: yalnızca 1. kat için T_m0 aranır.")
    w_target = (p["OD"] - p["ID"]) / 2
    d = p.get("d_wire", 0.0) if s.spiral else 0.0

    with st.container(border=True):
        st.markdown("**1. Hedef katman kalınlıkları (kür sonrası)**")
        c1, c2, c3 = st.columns(3)
        s1_mm = c1.number_input("İç katman hedefi s_1 [mm]", min_value=0.05, max_value=5.0, value=0.55, step=0.01,
                                help="1. daldırmanın kür sonrası kalınlığı. veriler.md cidar yapısı: 0,55 / 0,30 / 0,55 mm.")
        s2_default = max(mm(w_target - d) - s1_mm, 0.05) if s.spiral else 0.0
        s2_mm = c2.number_input("Örtü hedefi s_2 [mm]", min_value=0.0, max_value=5.0, value=float(round(s2_default, 3)),
                                step=0.01, disabled=not s.spiral,
                                help="Telin tepesinden itibaren 2. daldırmanın kür sonrası kalınlığı. Varsayılan: "
                                     "w_hedef − s_1 − d_tel.")
        c3.metric("Toplam cidar", f"{num(s1_mm + mm(d) + (s2_mm if s.spiral else 0), 3)} mm",
                  help=f"s_1 + d_tel + s_2. Ürün hedefi w = (OD − ID)/2 = {num(mm(w_target), 3)} mm.")
        st.markdown("**2. Taranacak çekme hızları ve arama sınırı**")
        c1, c2, c3 = st.columns(3)
        U_rng = c1.slider("U aralığı [mm/s]", min_value=0.1, max_value=10.0, value=(0.5, 3.0), step=0.1)
        nU = c2.select_slider("U nokta sayısı", options=[3, 5, 6, 8, 11], value=6)
        T_max_c = c3.number_input("Sıcaklık arama üst sınırı [°C]", min_value=float(degC(p["T_g"])) + 5, max_value=500.0,
                                  value=300.0, step=10.0,
                                  help="T_m0 ve T_m0,2 bu sınıra kadar aranır (alt sınır T_g'dir: altında jel oluşmaz).")
        link = st.checkbox("2. daldırmada iç katman (T_s1) ve tel (T_t) sıcaklığı T_m0,2 ile aynı alınsın", value=True,
                           disabled=not s.spiral,
                           help="veriler.md varsayımı: ince iç katman ve tel mandrel sıcaklığına hızla gelir. "
                                "İşaretli değilse T_s1 ve T_t 0. Veri girişindeki değerlerinde sabit kalır.")

    U_vals = to_si(np.linspace(*U_rng, nU), "mm/s")
    opt = compute.options(quality="hızlı")
    sig = (tuple(sorted(p.items())), astuple(opt), tuple(U_vals), s1_mm, s2_mm, T_max_c, link, s.spiral)
    stored = st.session_state.get("ters_A")
    if st.button("🎯 Ayarları bul", type="primary"):
        bar = st.progress(0.0, text="Başlıyor…")
        sols = inverse.solve_layers(p, opt, U_vals, to_si(s1_mm, "mm"),
                                    to_si(s2_mm if s.spiral else 0.0, "mm"), to_si(T_max_c, "°C"), link_T2=link,
                                    progress=lambda i, n: bar.progress(i / n, text=f"{i} / {n} çekme hızı"))
        bar.empty()
        st.session_state["ters_A"] = stored = {"sig": sig, "sols": sols}
    if stored is None:
        st.info("Hedefleri ve U aralığını seçip **Ayarları bul** düğmesine bas. Her U için yaklaşık 1–2 saniye sürer.")
        st.stop()
    if stored["sig"] != sig:
        st.warning("Girdiler son hesaplamadan sonra değişti; sonuçlar eski. Güncellemek için yeniden hesapla.")

    sols = stored["sols"]
    R = p["ID"] / 2
    rows = []
    for so in sols:
        row = {"U [mm/s]": round(so.U * 1e3, 3),
               "T_m0 [°C]": None if so.T_m0 is None else round(degC(so.T_m0), 1),
               "1. kat jel [mm]": None if so.s_jel1 is None else round(mm(so.s_jel1), 3),
               "1. kat film [mm]": None if so.h1 is None else round(mm(so.h1), 3)}
        if s.spiral:
            row.update({"T_m0,2 [°C]": None if so.T_m0_2 is None else round(degC(so.T_m0_2), 1),
                        "Örtü jel [mm]": None if so.s_jel2 is None else round(mm(so.s_jel2), 3),
                        "Örtü film [mm]": None if so.h2 is None else round(mm(so.h2), 3),
                        "w [mm]": None if so.w is None else round(mm(so.w), 3)})
        if so.T_m0 is not None:
            row.update(furnace_columns(p, R, so.T_m0))
        row["Durum"] = "✅ bulundu" if not so.note else f"⚠️ {so.note}"
        rows.append(row)
    df = pd.DataFrame(rows)

    ok = [so for so in sols if so.T_m0 is not None and (so.T_m0_2 is not None or not s.spiral)]
    if ok:
        Ulo, Uhi = min(so.U for so in ok) * 1e3, max(so.U for so in ok) * 1e3
        st.success(f"**Sonuç:** Hedefler U ≈ {num(Ulo, 2)}–{num(Uhi, 2)} mm/s aralığında tutturulabiliyor. Bu aralıkta "
                   f"gereken T_m0 ≈ {num(min(degC(so.T_m0) for so in ok), 0)}–{num(max(degC(so.T_m0) for so in ok), 0)} °C"
                   + (f", T_m0,2 ≈ {num(min(degC(so.T_m0_2) for so in ok), 0)}–"
                      f"{num(max(degC(so.T_m0_2) for so in ok), 0)} °C" if s.spiral else "")
                   + ". Hız arttıkça film kalınlaştığı için gereken sıcaklık düşer.")
    else:
        st.error("Bu U aralığında hedefler tutturulamadı. Tablodaki Durum sütunu nedenini söyler.")

    fig = go.Figure()
    Uok = [so.U * 1e3 for so in sols]
    fig.add_scatter(x=Uok, y=[None if so.T_m0 is None else degC(so.T_m0) for so in sols], mode="lines+markers",
                    name="Gereken T_m0 (1. kat)", line=dict(color=COLORS["line"], width=3))
    if s.spiral:
        fig.add_scatter(x=Uok, y=[None if so.T_m0_2 is None else degC(so.T_m0_2) for so in sols],
                        mode="lines+markers", name="Gereken T_m0,2 (örtü)", line=dict(color=COLORS["plastisol"], width=3))
    fig.add_hline(y=degC(p["T_g"]), line=dict(color=COLORS["accent"], dash="dash"),
                  annotation_text="T_g (altında jel oluşmaz)", annotation_position="bottom right")
    fig.update_layout(title="Hedef kalınlık için gereken mandrel sıcaklığı – çekme hızı",
                      xaxis_title="Çekme hızı U [mm/s]", yaxis_title="Gereken sıcaklık [°C]")
    show_fig(fig, "ters_tasarim_katman_hedefi")
    explain("Her nokta, o çekme hızında katmanı tam hedef kalınlığa getiren mandrel sıcaklığıdır. Çizginin bittiği "
            "yerde hedef artık tutturulamaz: sağda film tek başına hedefi aşar (U çok yüksek), solda arama sınırına "
            "kadar ısıtmak bile yetmez (U çok düşük). Pratikte, fırının sağlayabildiği sıcaklık ve çevrim süresine "
            "uyan bir (U, T_m0, T_m0,2) üçlüsü bu eğrilerden seçilir.")

    st.subheader("Ayar tablosu")
    st.dataframe(df.astype(object).where(df.notna(), "–"), hide_index=True, width="stretch")
    st.caption("Jel + film, katmanın kür öncesi parçalarıdır; kür çekmesi (1 − ε) ile hedef kür sonrası kalınlığa "
               "eşitlenir. Gerekli fırın çıkışı: banyoya bu T_m0 ile girmek için fırından çıkış sıcaklığı (taşıma "
               "soğumasının tersi). Gerekli t_ön: tablodaki T_fırın ile bu çıkış sıcaklığına ulaşma süresi (D1).")
    st.download_button("💾 Ayar tablosunu CSV olarak indir", df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="ters_tasarim_katman_hedefi.csv", mime="text/csv")
    st.info("Bir satırı uygulamak için 0. Veri girişinde U'yu, hesap ayarlarında T_m0'ı **doğrudan gir** seçip T_m0'ı "
            "ve Tel / 2. daldırma sekmesinde T_m0,2, T_s1, T_t'yi bu değerlerle doldur; ardından diğer sayfalarda "
            "normal ağla doğrula.")
    assumptions([
        "Arama hızlı (kaba) ağla yapılır; bulunan ayarı diğer sayfalarda normal ağla doğrulayın (fark genellikle %1–2).",
        "Kalınlık sıcaklıkla monoton artar; T_g'nin altında jel yoktur, kalınlık yalnızca filmdir. Sıcaklık ikiye "
        "bölme yöntemiyle aranır.",
        "Bekleme süreleri (t_bekleme, t_bekleme,2), t_süz ve diğer tüm girdiler 0. Veri girişindeki değerlerindedir.",
        "1. kat aranırken T_m0 doğrudan verilir (D1 kullanılmaz); gerekli fırın ayarı tabloda ayrıca hesaplanır.",
    ] + (["2. daldırmada T_s1 ve T_t, T_m0,2 ile aynı alınır (veriler.md varsayımı)."] if (s.spiral and link) else []))
    st.stop()

# =======================================================================================
# B. İki değişkenli ayar haritası
# =======================================================================================
st.markdown("Bu araç seçtiğin **iki ayarı** bir aralıkta tarar ve her ayar çifti için toplam cidarı (w) hesaplar. "
            "Hedefi tutturan bölge kırmızı bantla boyanır. Bandın genişliği, o ayarlarda ne kadar sapmaya izin "
            "olduğunu gösterir: geniş bant esnek, dar bant hassas bir proses demektir.")
keys = list(AXES)
c1, c2 = st.columns(2)
y_key = c1.selectbox("Dikey eksen", keys, index=keys.index("T_m0"), format_func=lambda k: AXES[k][0])
x_key = c2.selectbox("Yatay eksen", [k for k in keys if k != y_key],
                     index=0 if y_key != "T_m0" else [k for k in keys if k != y_key].index("U"),
                     format_func=lambda k: AXES[k][0])
st.caption("Örnekler: **T_m0 – U** fırın sıcaklığı ile çekme hızının birlikte seçimi · **U – t_süz** çekme hızı ve "
           "süzülme süresi · **T_m0 – t_bekleme** fırın ve bekleme süresi. Taranan değişkenlerin 0. Veri girişinde "
           "değeri olması gerekmez.")

v = state.require_ready(optional={x_key, y_key} | ({"t_pre"} if "T_m0" in (x_key, y_key) else set()))
s = state.settings()
draft_banner(v, s)
p = state.values_si()
Tg_c = degC(p["T_g"])

# eksen sınırları (kullanıcı birimiyle): (en küçük, en büyük, varsayılan aralık, adım)
LIMITS = {
    "T_m0": (math.floor(Tg_c), 400.0, (math.ceil(Tg_c + 2), Tg_c + 100), 1.0),
    "t_wait": (0.5, 300.0, (1.0, 30.0), 0.5),
    "U": (0.05, 20.0, (0.1, 5.0), 0.05),
    "t_drain": (0.0, 600.0, (0.0, 120.0), 1.0),
}

with st.container(border=True):
    st.markdown("**Ürün hedefi**")
    c1, c2, c3 = st.columns(3)
    ID = c1.number_input("ID – iç çap [mm]", min_value=0.5, max_value=20.0, value=float(mm(p["ID"])), step=0.5)
    OD = c2.number_input("OD hedefi [mm]", min_value=0.6, max_value=30.0, value=float(mm(p["OD"])), step=0.1)
    OD_tol = c3.number_input("± OD toleransı [mm]", min_value=0.0, max_value=2.0, value=float(mm(p["OD_tol"])),
                             step=0.01, format="%.2f")
    st.markdown("**Harita sınırları**")
    c1, c2, c3 = st.columns(3)
    rng = {}
    for col, k in ((c1, y_key), (c2, x_key)):
        lo, hi, (d0, d1), stp = LIMITS[k]
        rng[k] = col.slider(f"{AXES[k][0].split(' –')[0]} aralığı [{AXES[k][1]}]", min_value=float(lo),
                            max_value=float(hi), value=(float(d0), float(min(d1, hi))), step=float(stp))
    n = c3.select_slider("Izgara çözünürlüğü", options=[11, 15, 21, 25, 31, 41], value=21,
                         help="Her eksende kaç nokta hesaplanacağı. Büyük değer daha düzgün harita, daha uzun süre.")

if ID >= OD:
    st.error("OD hedefi ID'den büyük olmalı.")
    st.stop()
if to_si(ID / 2, "mm") <= p["R_i"]:
    st.error("ID/2, mandrel iç yarıçapından (R_i) büyük olmalı.")
    st.stop()

pp = {**p, "ID": to_si(ID, "mm"), "OD": to_si(OD, "mm"), "OD_tol": to_si(OD_tol, "mm")}
opt = compute.options(quality="hızlı")
x_vals = to_si(np.linspace(*rng[x_key], n), AXES[x_key][1])
y_vals = to_si(np.linspace(*rng[y_key], n), AXES[y_key][1])
sig = (tuple(sorted(pp.items())), astuple(opt), x_key, tuple(x_vals), y_key, tuple(y_vals))
fixed = [AXES[k][0].split(" –")[0] for k in AXES if k not in (x_key, y_key)]
st.caption(f"{n}×{n} = {n * n} nokta hesaplanacak (hızlı ağ). Sabit tutulanlar (0. Veri girişindeki değerleri): "
           f"{', '.join(fixed)}" + (" ve 2. daldırma / tel girdileri." if s.spiral else "."))
if "T_m0" not in (x_key, y_key) and s.T_m0_mode == "D1":
    st.caption("T_m0 bu haritada D1 (ön ısıtma) + taşıma soğumasından hesaplanır.")

stored = st.session_state.get("ters")
if st.button("🗺️ Haritayı hesapla", type="primary"):
    bar = st.progress(0.0, text="Başlıyor…")
    step = max(1, n * n // 100)

    def progress(i, total):
        if i % step == 0 or i == total:
            bar.progress(i / total, text=f"{i} / {total} nokta")

    dm = inverse.design_map(pp, opt, x_key, x_vals, y_key, y_vals, progress=progress)
    bar.empty()
    st.session_state["ters"] = stored = {"sig": sig, "dm": dm, "pp": pp}

if stored is None:
    st.info("Eksenleri ve sınırları seçip **Haritayı hesapla** düğmesine bas.")
    st.stop()
if stored["sig"] != sig:
    st.warning("Ayarlar son hesaplamadan sonra değişti; harita eski. Güncellemek için yeniden hesapla.")

dm, pp = stored["dm"], stored["pp"]
(xn, xu), (yn, yu) = AXES[dm.x_key], AXES[dm.y_key]
xs, ys = xn.split(" –")[0], yn.split(" –")[0]
W = mm(dm.w)
lo, hi = mm(dm.w_target - dm.w_tol), mm(dm.w_target + dm.w_tol)
title = f"Toplam cidar w – ID {num(mm(pp['ID']), 1)} mm ({ys} – {xs})"
stored["title"] = title          # rapor sayfası için

try:        # mevcut ayardaki T_m0 (D1 modunda hesaplanır); eksik girdi varsa işaret konmaz
    T_cur = run_model(p, compute.options(quality="hızlı", keep_details=False)).T_m0
except (ModelError, KeyError, ValueError):
    T_cur = p.get("T_m0")
nominal = tuple(T_cur if k == "T_m0" else p.get(k) for k in (dm.x_key, dm.y_key))
show_fig(charts.design_map(dm, title, nominal=nominal), f"ters_tasarim_ID{mm(pp['ID']):g}", height=520)
explain(f"**Nasıl okunur:** Haritadaki her nokta bir ({xs}, {ys}) ayar çiftidir; rengi o ayarda hesaplanan toplam "
        f"cidardır, ince çizgiler eşit kalınlık çizgileridir. **Kırmızı bant** hedef aralıktır ({num(lo, 3)}–"
        f"{num(hi, 3)} mm): bandın içindeki her ayar hedefi verir. Bant boyunca ilerlemek, bir ayardaki değişikliği "
        "diğeriyle telafi etmek demektir (ör. U artarsa T_m0 düşürülür). Beyaz çarpı (varsa) 0. Veri girişindeki "
        "mevcut ayardır; bandın dışındaysa mevcut ayar hedefi tutturmuyordur.")

table = inverse.feasible_table(dm)
ok_rows = table.dropna()
if ok_rows.empty:
    w_min, w_max = np.nanmin(W), np.nanmax(W)
    if w_min > hi:
        st.error(f"Bu aralıkta en ince sonuç bile ({num(w_min, 3)} mm) hedeften kalın. Eksen aralıklarını "
                 "değiştir (ör. U'yu veya sıcaklığı düşür) ya da sabit tutulan değerleri gözden geçir.")
    elif w_max < lo:
        st.error(f"Bu aralıkta en kalın sonuç bile ({num(w_max, 3)} mm) hedeften ince. Eksen aralıklarını "
                 "değiştir ya da sabit tutulan değerleri gözden geçir.")
    else:
        st.warning("Hedef bandı ızgara noktaları arasında kalıyor; çözünürlüğü artır.")
    st.stop()

y_ok = from_si(ok_rows["y"].to_numpy(), yu)
st.success(f"**Hedef cidar için uygun bölge:** {ys} ≈ {num(y_ok.min(), 2)}–{num(y_ok.max(), 2)} {yu}; "
           f"{xs} {num(from_si(ok_rows['x_min'].min(), xu), 2)}–{num(from_si(ok_rows['x_max'].max(), xu), 2)} {xu}. "
           "Her satırın kendi aralığı aşağıdaki tabloda.")

R = pp["ID"] / 2
rows = []
for _, r in table.iterrows():
    feasible = not (math.isnan(r.x_min) or math.isnan(r.x_max))
    row = {f"{ys} [{yu}]": round(float(from_si(r.y, yu)), 3),
           f"{xs} min [{xu}]": round(float(from_si(r.x_min, xu)), 3) if feasible else None,
           f"{xs} max [{xu}]": round(float(from_si(r.x_max, xu)), 3) if feasible else None,
           "Durum": "✅ hedef tutar" if feasible else "—"}
    if dm.y_key == "T_m0" and feasible:
        row.update(furnace_columns(p, R, r.y))
    rows.append(row)
df = pd.DataFrame(rows)
st.subheader("Ayar tablosu")
st.caption(f"Her satır bir {ys} değeri için hedefi tutturan {xs} aralığını verir (aralık sınırları doğrusal "
           "interpolasyonla).")
show_all = st.checkbox("Hedefi tutmayan satırları da göster", value=False)
view = df if show_all else df[df["Durum"] != "—"]
st.dataframe(view.astype(object).where(view.notna(), "–"), hide_index=True, width="stretch")
st.download_button("💾 Ayar tablosunu CSV olarak indir",
                   df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                   file_name=f"ters_tasarim_ID{ID:g}.csv", mime="text/csv")

assumptions([
    "Harita hızlı (kaba) ağla hesaplanır; seçilen noktayı diğer sayfalarda normal ağla doğrulayın.",
    "Taranmayan tüm girdiler 0. Veri girişindeki değerlerinde sabittir; ID, OD ve tolerans bu sayfadaki "
    "değerlerdir. T_m0 eksenlerden biriyse doğrudan verilmiş kabul edilir (D1 kullanılmaz).",
] + (["Spiralli tüpte 2. daldırmanın girdileri (T_m0,2, T_s1, T_t, t_bekleme,2) haritada değişmez; "
      "2. daldırma için A aracını kullan."] if s.spiral else []))
