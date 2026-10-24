import math
from dataclasses import astuple

import numpy as np
import pandas as pd
import streamlit as st

from physics import inverse, preheat
from physics.inverse import AXES
from physics.model import ModelError, run_model
from physics.units import from_si, to_si
from ui import charts, compute, state
from ui.common import assumptions, draft_banner, explain, num, show_fig

st.title("7. Ters tasarım – ayar haritası")
st.markdown("Bu sayfa şu soruyu cevaplar: **Hedef cidarı yakalamak için proses ayarları hangi aralıkta "
            "olmalı?** İki proses değişkeni seç; program bir ızgaradaki her ayar çifti için cidarı hesaplar ve "
            "hedefi tutturan bölgeyi haritada gösterir.")

# --- Eksen seçimi (hesaptan önce: taranan değişkenlerin tabloda değeri olması gerekmez) ---------
keys = list(AXES)
c1, c2 = st.columns(2)
y_key = c1.selectbox("Dikey eksen", keys, index=keys.index("T_m0"), format_func=lambda k: AXES[k][0])
x_key = c2.selectbox("Yatay eksen", [k for k in keys if k != y_key],
                     index=0 if y_key != "T_m0" else [k for k in keys if k != y_key].index("t_wait"),
                     format_func=lambda k: AXES[k][0])

v = state.require_ready(optional={x_key, y_key})
s = state.settings()
draft_banner(v, s)
p = state.values_si()
mm = lambda x: from_si(x, "mm")  # noqa: E731
degC = lambda T: from_si(T, "°C")  # noqa: E731
Tg_c = degC(p["T_g"])

# eksen sınırları (kullanıcı birimiyle): (en küçük, en büyük, varsayılan aralık, adım)
LIMITS = {
    "T_m0": (math.floor(Tg_c), 400.0, (math.ceil(Tg_c + 2), Tg_c + 100), 1.0),
    "t_wait": (0.5, 300.0, (1.0, 30.0), 0.5),
    "U": (0.05, 20.0, (0.1, 5.0), 0.05),
    "t_drain": (0.0, 600.0, (0.0, 120.0), 1.0),
}

with st.container(border=True):
    st.markdown("**Ürün**")
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
st.caption(f"{n}×{n} = {n * n} nokta hesaplanacak (hızlı ağ). Taranan: {AXES[y_key][0].split(' –')[0]} ve "
           f"{AXES[x_key][0].split(' –')[0]}. Sabit (0. Veri girişindeki değerleri): {', '.join(fixed)}"
           + (" ve 2. daldırma / tel girdileri." if s.spiral else "."))
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

# --- Harita ---------------------------------------------------------------------------
try:        # mevcut ayardaki T_m0 (D1 modunda hesaplanır); eksik girdi varsa işaret konmaz
    T_cur = run_model(p, compute.options(quality="hızlı", keep_details=False)).T_m0
except (ModelError, KeyError, ValueError):
    T_cur = p.get("T_m0")
nominal = tuple(T_cur if k == "T_m0" else p.get(k) for k in (dm.x_key, dm.y_key))
show_fig(charts.design_map(dm, title, nominal=nominal), f"ters_tasarim_ID{mm(pp['ID']):g}", height=520)
explain(f"Renkler ve eş-kalınlık çizgileri, her ({xs}, {ys}) çifti için hesaplanan cidar kalınlığını gösterir. "
        f"Kırmızı taralı bant hedef aralıktır ({num(lo, 3)}–{num(hi, 3)} mm): bu bandın içindeki her ayar hedef "
        "cidarı verir. Beyaz çarpı (varsa) 0. Veri girişindeki mevcut ayardır.")

# --- Yorum ve tablo -------------------------------------------------------------------
table = inverse.feasible_table(dm)
ok_rows = table.dropna()
if ok_rows.empty:
    w_min, w_max = np.nanmin(W), np.nanmax(W)
    if w_min > hi:
        st.error(f"Bu aralıkta en ince sonuç bile ({num(w_min, 3)} mm) hedeften kalın. Eksen aralıklarını "
                 "değiştir ya da sabit tutulan değerleri gözden geçir.")
    elif w_max < lo:
        st.error(f"Bu aralıkta en kalın sonuç bile ({num(w_max, 3)} mm) hedeften ince. Eksen aralıklarını "
                 "değiştir ya da sabit tutulan değerleri gözden geçir.")
    else:
        st.warning("Hedef bandı ızgara noktaları arasında kalıyor; çözünürlüğü artır.")
    st.stop()

y_ok = from_si(ok_rows["y"].to_numpy(), yu)
st.success(f"**Hedef cidar için uygun bölge:** {ys} ≈ {num(y_ok.min(), 2)}–{num(y_ok.max(), 2)} {yu}; "
           f"{xs} {num(from_si(ok_rows['x_min'].min(), xu), 2)}–{num(from_si(ok_rows['x_max'].max(), xu), 2)} {xu}. "
           "Ayrıntı aşağıdaki tabloda.")

furnace = dm.y_key == "T_m0" and p["R_i"] <= 0 and all(k in p for k in ("T_oven", "h_oven", "T_0"))
R = pp["ID"] / 2
rows = []
for _, r in table.iterrows():
    feasible = not (math.isnan(r.x_min) or math.isnan(r.x_max))
    row = {f"{ys} [{yu}]": round(float(from_si(r.y, yu)), 3),
           f"{xs} min [{xu}]": round(float(from_si(r.x_min, xu)), 3) if feasible else None,
           f"{xs} max [{xu}]": round(float(from_si(r.x_max, xu)), 3) if feasible else None,
           "Durum": "✅ hedef tutar" if feasible else "—"}
    if furnace and feasible:
        # banyoya T_m0 ile girmek için gereken fırın çıkışı (taşıma soğumasının tersi) ve fırın süresi
        T_exit = r.y
        if all(k in p for k in ("t_tr", "T_amb", "h_amb")):
            tau_t = preheat.time_constant(p["rho_m"], p["c_m"], R, p["h_amb"])
            T_exit = p["T_amb"] + (r.y - p["T_amb"]) * math.exp(p["t_tr"] / tau_t)
        tau = preheat.time_constant(p["rho_m"], p["c_m"], R, p["h_oven"])
        t_pre = preheat.time_to_reach(T_exit, p["T_oven"], p["T_0"], tau)
        row["Gerekli fırın çıkışı [°C]"] = round(degC(T_exit), 1)
        row["Gerekli t_ön (D1) [s]"] = "ulaşılamaz" if math.isinf(t_pre) else round(t_pre)
    rows.append(row)
df = pd.DataFrame(rows)
st.subheader("Ayar tablosu")
show_all = st.checkbox("Hedefi tutmayan satırları da göster", value=False)
view = df if show_all else df[df["Durum"] != "—"]
st.dataframe(view.astype(object).where(view.notna(), "–"), hide_index=True, width="stretch")
if furnace:
    st.caption(f"Gerekli fırın çıkışı: banyoya T_m0 ile girmek için taşıma soğumasının tersinden "
               f"(t_taşıma, T_ortam, h_ortam). Gerekli t_ön: T_fırın = {num(degC(p['T_oven']), 0)} °C, "
               f"h_fırın = {num(p['h_oven'], 0)} W/(m²·K), T_0 = {num(degC(p['T_0']), 0)} °C ile D1'den.")
st.download_button("💾 Ayar tablosunu CSV olarak indir",
                   df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                   file_name=f"ters_tasarim_ID{ID:g}.csv", mime="text/csv")

assumptions([
    "Harita hızlı (kaba) ağla hesaplanır; seçilen noktayı diğer sayfalarda normal ağla doğrulayın.",
    "Taranmayan tüm girdiler 0. Veri girişindeki değerlerinde sabittir; ID, OD ve tolerans bu sayfadaki "
    "değerlerdir. T_m0 eksenlerden biriyse doğrudan verilmiş kabul edilir (D1 kullanılmaz).",
] + (["Spiralli tüpte 2. daldırmanın girdileri (T_m0,2, T_s1, T_t, t_bekleme,2) haritada değişmez."]
     if s.spiral else []))
