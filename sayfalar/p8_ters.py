import math
from dataclasses import astuple

import numpy as np
import pandas as pd
import streamlit as st

from physics import inverse, preheat
from physics.units import from_si, to_si
from ui import charts, compute, state
from ui.common import assumptions, draft_banner, explain, num, show_fig

st.title("7. Ters tasarım – ayar haritası")
st.markdown("Bu sayfa şu soruyu cevaplar: **Hedef cidarı yakalamak için mandrel sıcaklığı (T_m0) ve "
            "bekleme süresi (t_bekleme) hangi aralıkta olmalı?** Program bir ızgaradaki her ayar için "
            "cidarı hesaplar ve hedefi tutturan bölgeyi haritada gösterir.")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
p = state.values_si()
mm = lambda x: from_si(x, "mm")  # noqa: E731
degC = lambda T: from_si(T, "°C")  # noqa: E731
Tg_c, Tm0_c = degC(p["T_g"]), degC(compute.run().T_m0)

# --- Ayarlar --------------------------------------------------------------------------
with st.container(border=True):
    st.markdown("**Ürün ve proses**")
    c1, c2, c3, c4 = st.columns(4)
    ID = c1.number_input("ID – iç çap [mm]", min_value=0.5, max_value=20.0, value=float(mm(p["ID"])), step=0.5)
    OD = c2.number_input("OD hedefi [mm]", min_value=0.6, max_value=30.0, value=float(mm(p["OD"])), step=0.1)
    OD_tol = c3.number_input("± OD toleransı [mm]", min_value=0.0, max_value=2.0, value=float(mm(p["OD_tol"])),
                             step=0.01, format="%.2f")
    U = c4.slider("U – çekme hızı [mm/s]", min_value=0.1, max_value=20.0, value=float(min(20.0, p["U"] * 1e3)),
                  step=0.1, help="Haritayı farklı çekme hızları için yeniden hesaplamak üzere kaydır.")
    st.markdown("**Harita sınırları**")
    c1, c2, c3 = st.columns(3)
    T_rng = c1.slider("T_m0 aralığı [°C]", min_value=float(math.floor(Tg_c)), max_value=400.0,
                      value=(float(math.ceil(Tg_c + 2)), float(min(400.0, max(Tm0_c + 50, Tg_c + 100)))), step=1.0)
    t_rng = c2.slider("t_bekleme aralığı [s]", min_value=0.5, max_value=300.0,
                      value=(1.0, float(max(30.0, 2 * p["t_wait"]))), step=0.5)
    n = c3.select_slider("Izgara çözünürlüğü", options=[11, 15, 21, 25, 31, 41], value=21,
                         help="Her eksende kaç nokta hesaplanacağı. Büyük değer daha düzgün harita, daha uzun süre.")

if ID >= OD:
    st.error("OD hedefi ID'den büyük olmalı.")
    st.stop()
if to_si(ID / 2, "mm") <= p["R_i"]:
    st.error("ID/2, mandrel iç yarıçapından (R_i) büyük olmalı.")
    st.stop()

pp = {**p, "ID": to_si(ID, "mm"), "OD": to_si(OD, "mm"), "OD_tol": to_si(OD_tol, "mm"), "U": to_si(U, "mm/s")}
opt = compute.options(quality="hızlı")
T_vals = to_si(np.linspace(*T_rng, n), "°C")
t_vals = np.linspace(*t_rng, n)
sig = (tuple(sorted(pp.items())), astuple(opt), tuple(T_vals), tuple(t_vals))
st.caption(f"{n}×{n} = {n * n} nokta hesaplanacak (hızlı ağ). "
           + ("Spiralli tüpte her iki daldırma aynı T_m0 ve t_bekleme ile yapılır." if s.spiral else ""))

stored = st.session_state.get("ters")
if st.button("🗺️ Haritayı hesapla", type="primary"):
    bar = st.progress(0.0, text="Başlıyor…")
    step = max(1, n * n // 100)

    def progress(i, total):
        if i % step == 0 or i == total:
            bar.progress(i / total, text=f"{i} / {total} nokta")

    dm = inverse.design_map(pp, opt, T_vals, t_vals, progress=progress)
    bar.empty()
    st.session_state["ters"] = stored = {"sig": sig, "dm": dm, "pp": pp}

if stored is None:
    st.info("Ayarları seçip **Haritayı hesapla** düğmesine bas.")
    st.stop()
if stored["sig"] != sig:
    st.warning("Ayarlar son hesaplamadan sonra değişti; harita eski. Güncellemek için yeniden hesapla.")

dm, pp = stored["dm"], stored["pp"]
W = mm(dm.w)
lo, hi = mm(dm.w_target - dm.w_tol), mm(dm.w_target + dm.w_tol)
title = f"Toplam cidar w – ID {num(mm(pp['ID']), 1)} mm, U = {num(pp['U'] * 1e3, 1)} mm/s"
stored["title"] = title          # rapor sayfası için

# --- Harita ---------------------------------------------------------------------------
show_fig(charts.design_map(dm, title, nominal=(p["t_wait"], compute.run().T_m0)),
         f"ters_tasarim_ID{mm(pp['ID']):g}", height=520)
explain(f"Renkler ve eş-kalınlık çizgileri, her (bekleme süresi, mandrel sıcaklığı) çifti için hesaplanan "
        f"cidar kalınlığını gösterir. Kırmızı taralı bant hedef aralıktır ({num(lo, 3)}–{num(hi, 3)} mm): "
        "bu bandın içindeki her ayar hedef cidarı verir. Beyaz çarpı parametre tablosundaki mevcut ayardır.")

# --- Yorum ve tablo -------------------------------------------------------------------
table = inverse.feasible_table(dm)
ok_rows = table.dropna()
if ok_rows.empty:
    w_min, w_max = np.nanmin(W), np.nanmax(W)
    if w_min > hi:
        st.error(f"Bu aralıkta en ince sonuç bile ({num(w_min, 3)} mm) hedeften kalın. Çekme hızını "
                 "düşür, T_m0 aralığını aşağı genişlet, daha ince tel kullan ya da (spiralde) 2. daldırma "
                 "ayarlarını ayrı düşün.")
    elif w_max < lo:
        st.error(f"Bu aralıkta en kalın sonuç bile ({num(w_max, 3)} mm) hedeften ince. Çekme hızını "
                 "artır, T_m0 veya t_bekleme aralığını yukarı genişlet.")
    else:
        st.warning("Hedef bandı ızgara noktaları arasında kalıyor; çözünürlüğü artır.")
    st.stop()

T_ok = degC(ok_rows["T_m0"].to_numpy())
st.success(f"**Hedef cidar için uygun bölge:** T_m0 ≈ {num(T_ok.min(), 0)}–{num(T_ok.max(), 0)} °C; "
           f"t_bekleme {num(ok_rows['t_min'].min(), 1)}–{num(ok_rows['t_max'].max(), 1)} s "
           f"(U = {num(U, 1)} mm/s). Ayrıntı aşağıdaki tabloda.")

R = pp["ID"] / 2
solid = p["R_i"] <= 0
tau = preheat.time_constant(p["rho_m"], p["c_m"], R, p["h_oven"])
t_pull = p["L"] / pp["U"]
rows = []
for _, r in table.iterrows():
    feasible = not (math.isnan(r.t_min) or math.isnan(r.t_max))
    t_pre = preheat.time_to_reach(r.T_m0, p["T_oven"], p["T_0"], tau) if solid else float("nan")
    row = {
        "T_m0 [°C]": round(degC(r.T_m0), 1),
        "t_bekleme min [s]": round(r.t_min, 1) if feasible else None,
        "t_bekleme max [s]": round(r.t_max, 1) if feasible else None,
        "Durum": "✅ hedef tutar" if feasible else "—",
        "Gerekli t_ön (D1) [s]": (None if math.isnan(t_pre) else ("ulaşılamaz" if math.isinf(t_pre) else round(t_pre)))
        if feasible else None,
        "Çekme süresi L/U [s]": round(t_pull, 1) if feasible else None,
    }
    if feasible and solid and math.isfinite(t_pre):
        row["Tahmini çevrim (1 daldırma) [s]"] = round(t_pre + r.t_min + t_pull + p["t_drain"])
    rows.append(row)
df = pd.DataFrame(rows)
st.subheader("Fırın ve çevrim süresi tasarımı için ayar tablosu")
show_all = st.checkbox("Hedefi tutmayan sıcaklıkları da göster", value=False)
view = df if show_all else df[df["Durum"] != "—"]
st.dataframe(view.astype(object).where(view.notna(), "–"), hide_index=True, width="stretch")
st.caption(f"t_ön: T_fırın = {num(degC(p['T_oven']), 0)} °C, h_fırın = {num(p['h_oven'], 0)} W/(m²·K) ve "
           f"T_0 = {num(degC(p['T_0']), 0)} °C ile D1'den hesaplanır"
           + ("" if solid else " (içi boş mandrelde D1 tanımsız, boş bırakıldı)")
           + ". Tahmini çevrim = t_ön + en kısa t_bekleme + çekme süresi + t_süz; kür ve soğutma hariç.")
st.download_button("💾 Ayar tablosunu CSV olarak indir",
                   df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                   file_name=f"ters_tasarim_ID{ID:g}.csv", mime="text/csv")

assumptions([
    "Harita hızlı (kaba) ağla hesaplanır; seçilen noktayı diğer sayfalarda normal ağla doğrulayın.",
    "T_m0 doğrudan verilmiş kabul edilir; diğer tüm parametreler nominal değerlerinde sabittir.",
] + (["Spiralli tüpte her iki daldırma aynı T_m0 ve t_bekleme ile yapılır (2. daldırma için ayrı "
      "girilen değerler bu haritada kullanılmaz)."] if s.spiral else []))
