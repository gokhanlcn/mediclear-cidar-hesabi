import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from physics import params
from physics.model import ModelError, run_model
from physics.units import from_si, to_si
from ui import compute, report, state
from ui.common import draft_banner, num

st.title("8. Numara bazında sonuçlar ve rapor")
st.markdown("Her ET numarası (iç çap) için bir satır ekle; program hepsini tek tuşla hesaplar. Sonuçları "
            "Excel'e aktarabilir ve bitirme raporuna eklenebilecek tek dosyalık bir özet rapor alabilirsin.")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
p = state.values_si()
base = compute.run()
mm = lambda x: from_si(x, "mm")  # noqa: E731
degC = lambda T: from_si(T, "°C")  # noqa: E731

INPUT_COLS = ["ID [mm]", "OD hedefi [mm]", "± OD [mm]", "d_tel [mm]", "T_m0 [°C]", "t_bekleme [s]", "U [mm/s]",
              "U_2 [mm/s]"]


def _default_row() -> dict:
    # D1 modunda T_m0 boş bırakılır: her satırda kendi ID'siyle (R = ID/2) D1'den hesaplanır
    T0 = None if s.T_m0_mode == "D1" else round(degC(p["T_m0"]), 1)
    return {"ID [mm]": mm(p["ID"]), "OD hedefi [mm]": mm(p["OD"]), "± OD [mm]": mm(p["OD_tol"]),
            "d_tel [mm]": mm(p.get("d_wire", 0.0)), "T_m0 [°C]": T0,
            "t_bekleme [s]": p["t_wait"], "U [mm/s]": p["U"] * 1e3 if "U" in p else None,
            "U_2 [mm/s]": p["U_2"] * 1e3 if "U_2" in p else None}


if "numara_in" not in st.session_state:
    st.session_state["numara_in"] = pd.DataFrame([_default_row()], columns=INPUT_COLS)

# --- Girdi tablosu --------------------------------------------------------------------
st.subheader("Numaralar")
st.caption("Satır eklemek için tablonun altındaki **+** işaretine tıkla. Boş bırakılan hücreler 0. Veri "
           "girişindeki değerle doldurulur (OD hedefi zorunludur). "
           + ("**T_m0 boş bırakılırsa** her satırda o satırın ID'siyle D1'den (ön ısıtma) hesaplanır; dolu "
              "ise doğrudan o değer kullanılır." if s.T_m0_mode == "D1" else
              "T_m0 boş bırakılırsa tablodaki T_m0 kullanılır."))
if s.spiral:
    st.info("Tabloda olmayan girdiler her satırda **0. Veri girişindeki** değerleriyle kullanılır. 2. daldırma "
            f"ve tel için: T_m0,2 = {num(degC(p['T_m0_2']), 1)} °C, T_s1 = {num(degC(p['T_s1']), 1)} °C, "
            f"T_t = {num(degC(p['T_t']), 1)} °C, t_bekleme,2 = {num(p['t_wait_2'], 1)} s, hatve p = "
            f"{num(mm(p['p_wire']), 2)} mm.")
c1, c2 = st.columns(2)
if c1.button("↺ Tabloyu parametre değerleriyle sıfırla"):
    st.session_state["numara_in"] = pd.DataFrame([_default_row()], columns=INPUT_COLS)
    st.session_state.pop("numara_res", None)
    st.session_state["numara_ver"] = st.session_state.get("numara_ver", 0) + 1
edited = st.data_editor(st.session_state["numara_in"], num_rows="dynamic", hide_index=True,
                        key=f"numara_editor_{st.session_state.get('numara_ver', 0)}",
                        column_config={c: st.column_config.NumberColumn(c, min_value=0.0) for c in INPUT_COLS})


def _row_inputs(r: pd.Series) -> tuple[dict, dict]:
    """Satırı SI parametre sözlüğüne ve Options değişikliklerine çevirir."""
    def get(col, default):
        val = r.get(col)
        return default if val is None or pd.isna(val) else float(val)

    pr = dict(p)
    pr["ID"] = to_si(get("ID [mm]", mm(p["ID"])), "mm")
    pr["OD"] = to_si(get("OD hedefi [mm]", np.nan), "mm")
    pr["OD_tol"] = to_si(get("± OD [mm]", mm(p["OD_tol"])), "mm")
    pr["d_wire"] = to_si(get("d_tel [mm]", mm(p.get("d_wire", 0.0))), "mm")
    pr["t_wait"] = get("t_bekleme [s]", p["t_wait"])
    pr["U"] = to_si(get("U [mm/s]", p.get("U", float("nan")) * 1e3), "mm/s")
    pr["U_2"] = to_si(get("U_2 [mm/s]", p.get("U_2", float("nan")) * 1e3), "mm/s")
    over = {}
    T = r.get("T_m0 [°C]")
    if T is not None and not pd.isna(T):
        pr["T_m0"] = to_si(float(T), "°C")
        over["T_m0_mode"] = "direct"
    return pr, over


if st.button("▶️ Tümünü hesapla", type="primary"):
    rows = [r for _, r in edited.iterrows() if not pd.isna(r.get("OD hedefi [mm]"))]
    if not rows:
        st.error("En az bir satırda OD hedefi girilmeli.")
        st.stop()
    bar = st.progress(0.0)
    out = []
    for i, r in enumerate(rows):
        pr, over = _row_inputs(r)
        opt = compute.options(keep_details=False, **over)
        rec = {"ID [mm]": mm(pr["ID"]), "R [mm]": mm(pr["ID"] / 2), "OD hedefi [mm]": mm(pr["OD"]),
               "w hedefi [mm]": mm((pr["OD"] - pr["ID"]) / 2), "d_tel [mm]": mm(pr["d_wire"]) if s.spiral else 0.0,
               "t_bekleme,1 [s]": pr["t_wait"], "U [mm/s]": pr["U"] * 1e3,
               "U_2 [mm/s]": pr["U_2"] * 1e3 if s.spiral else None}
        try:
            if pr["OD"] <= pr["ID"]:
                raise ModelError("OD hedefi ID'den büyük olmalı.")
            res = run_model(pr, opt)
            rec.update({"T_m0,1 [°C]": round(degC(res.T_m0), 1),
                        "s_jel,1 [mm]": mm(res.dip1.s_jel), "h_1 [mm]": mm(res.dip1.h),
                        "s_1 [mm]": mm(res.dip1.s_kur)})
            if res.dip2 is not None:
                rec.update({"s_jel,2 [mm]": mm(res.dip2.s_jel), "h_2 [mm]": mm(res.dip2.h),
                            "s_2 [mm]": mm(res.dip2.s_kur)})
            rec.update({"w [mm]": mm(res.w), "OD hesap [mm]": mm(pr["ID"] + 2 * res.w),
                        "Sapma [mm]": mm(res.deviation),
                        "Durum": "✅ Uygun" if res.ok else "❌ Uygun değil"})
        except (ModelError, ValueError) as exc:
            rec["Durum"] = f"⚠️ {exc}"
        out.append(rec)
        bar.progress((i + 1) / len(rows), text=f"{i + 1} / {len(rows)} numara")
    bar.empty()
    st.session_state["numara_in"] = edited
    st.session_state["numara_res"] = pd.DataFrame(out)

res_df = st.session_state.get("numara_res")
if res_df is not None:
    st.subheader("Sonuçlar")
    order = ["ID [mm]", "R [mm]", "OD hedefi [mm]", "w hedefi [mm]", "d_tel [mm]", "T_m0,1 [°C]",
             "t_bekleme,1 [s]", "U [mm/s]", "U_2 [mm/s]", "s_jel,1 [mm]", "h_1 [mm]", "s_1 [mm]", "s_jel,2 [mm]", "h_2 [mm]",
             "s_2 [mm]", "w [mm]", "OD hesap [mm]", "Sapma [mm]", "Durum"]
    res_df = res_df[[c for c in order if c in res_df.columns]]
    st.dataframe(res_df.round(3), hide_index=True, width="stretch")
    st.caption("s_jel,i ve h_i: i. daldırmanın jel ve ortalama film kalınlığı (kür öncesi). s_i: i. daldırmanın "
               "kür sonrası kalınlığı (D9). w: kür sonrası toplam cidar (spiralde w = s_1 + d_tel + s_2; tek "
               "daldırmada w = s_1). .md tablosundaki s_jel, h ve s_toplam sütunlarının daldırma bazında karşılıklarıdır.")

# --- Dışa aktarma ---------------------------------------------------------------------
st.header("Dışa aktar")
df = state.df()
nominal = pd.DataFrame([{"Daldırma": d.index, "T_m0 [°C]": degC(d.T_m0), "t_bekleme [s]": d.t_wait,
                         "s_max [mm]": mm(d.s_max), "s_jel [mm]": mm(d.s_jel), "C": d.C,
                         "D7 formülü": d.film.formula, "h_0 [mm]": mm(d.h0), "h ort. [mm]": mm(d.h),
                         "s_toplam [mm]": mm(d.s_toplam), "s_kür [mm]": mm(d.s_kur)}
                        for d in [base.dip1] + ([base.dip2] if base.dip2 else [])])
nominal.loc[len(nominal)] = {"Daldırma": "w (toplam)", "s_kür [mm]": mm(base.w)}
extra = {"Tablo değerleriyle sonuç": nominal}
if base.wire is not None:
    wr = base.wire
    extra["Tel halkası"] = pd.DataFrame({
        "Büyüklük": ["φ = πd/(4p)", "(ρc)_eff [J/(m³·K)]", "k_eff (Rayleigh) [W/(m·K)]", "T_halka [°C]",
                     "V'' = (1 − φ)d [mm³/mm²]", "T_c mandrel–plastisol [°C]", "T_c iç PVC–plastisol [°C]",
                     "T_c tel–plastisol [°C]", "δ_tel [mm]"],
        "Değer": [wr.phi, wr.rhoc_eff, wr.k_eff, degC(wr.T_ring), wr.V_groove * 1e3, degC(wr.T_c_dip1),
                  degC(wr.T_c_layer), degC(wr.T_c_wire), mm(wr.delta_wire)]})
if res_df is not None:
    extra["Numara sonuçları"] = res_df
stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
c1, c2 = st.columns(2)
c1.download_button("📊 Excel: tüm girdiler, kaynaklar ve sonuçlar", params.to_excel_bytes(df, s, extra),
                   file_name=f"mediclear_sonuclar_{stamp}.xlsx", width="stretch",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

ters = st.session_state.get("ters")
include = c2.multiselect("Rapora eklenecek analizler", ["Ters tasarım haritası"],
                         default=["Ters tasarım haritası"] if ters is not None else [],
                         placeholder="Analiz seç (isteğe bağlı)",
                         help="Yalnızca ilgili sayfada hesaplanmış analizler eklenebilir.")
if "Ters tasarım haritası" in include and ters is None:
    st.caption("Ters tasarım haritası henüz hesaplanmadı; 7. sayfada hesaplayınca rapora eklenebilir.")
if c2.button("📝 Özet raporu hazırla", width="stretch"):
    with st.spinner("Rapor hazırlanıyor…"):
        html_text = report.build_report(df, s, compute.run(), p, numara=res_df,
                                        ters=ters if "Ters tasarım haritası" in include else None)
    st.session_state["report_html"] = html_text
if "report_html" in st.session_state:
    st.download_button("⬇️ Özet raporu indir (HTML)", st.session_state["report_html"].encode("utf-8"),
                       file_name=f"mediclear_rapor_{stamp}.html", mime="text/html", type="primary")
    st.info("Raporu çift tıklayıp tarayıcıda aç. PDF için tarayıcıda **Yazdır → PDF olarak kaydet** seç "
            "(Arka plan grafikleri seçeneğini açık tut). Dosya internet bağlantısı olmadan da açılır.")
