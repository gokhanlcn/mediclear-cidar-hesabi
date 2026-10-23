import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from physics import params
from physics.model import ModelError, run_model
from physics.units import from_si, to_si
from ui import compute, report, state
from ui.common import draft_banner

st.title("7. Numara bazında sonuçlar ve rapor")
st.markdown("Her ET numarası (iç çap) için bir satır ekle; program hepsini tek tuşla hesaplar. Sonuçları "
            "Excel'e aktarabilir ve bitirme raporuna eklenebilecek tek dosyalık bir özet rapor alabilirsin.")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
p = state.values_si()
base = compute.run()
mm = lambda x: from_si(x, "mm")  # noqa: E731
degC = lambda T: from_si(T, "°C")  # noqa: E731

INPUT_COLS = ["ID [mm]", "OD hedefi [mm]", "± OD [mm]", "d_tel [mm]", "T_m0 [°C]", "t_bekleme [s]", "U [mm/s]"]


def _default_row() -> dict:
    return {"ID [mm]": mm(p["ID"]), "OD hedefi [mm]": mm(p["OD"]), "± OD [mm]": mm(p["OD_tol"]),
            "d_tel [mm]": mm(p.get("d_wire", 0.0)), "T_m0 [°C]": round(degC(base.T_m0), 1),
            "t_bekleme [s]": p["t_wait"], "U [mm/s]": p["U"] * 1e3}


if "numara_in" not in st.session_state:
    st.session_state["numara_in"] = pd.DataFrame([_default_row()], columns=INPUT_COLS)

# --- Girdi tablosu --------------------------------------------------------------------
st.subheader("Numaralar")
st.caption("Satır eklemek için tablonun altındaki **+** işaretine tıkla. Boş bırakılan hücreler parametre "
           "tablosundaki değerle doldurulur (OD hedefi zorunludur).")
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
    pr["U"] = to_si(get("U [mm/s]", p["U"] * 1e3), "mm/s")
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
               "t_bekleme [s]": pr["t_wait"], "U [mm/s]": pr["U"] * 1e3}
        try:
            if pr["OD"] <= pr["ID"]:
                raise ModelError("OD hedefi ID'den büyük olmalı.")
            res = run_model(pr, opt)
            dips = [res.dip1] + ([res.dip2] if res.dip2 else [])
            rec.update({"T_m0 [°C]": round(degC(res.T_m0), 1),
                        "s_jel [mm]": sum(mm(d.s_jel) for d in dips),
                        "h [mm]": sum(mm(d.h) for d in dips),
                        "s_toplam [mm]": mm(res.w),
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
    order = ["ID [mm]", "R [mm]", "OD hedefi [mm]", "w hedefi [mm]", "d_tel [mm]", "T_m0 [°C]", "t_bekleme [s]",
             "U [mm/s]", "s_jel [mm]", "h [mm]", "s_toplam [mm]", "Sapma [mm]",
             "Durum"]
    res_df = res_df[[c for c in order if c in res_df.columns]]
    st.dataframe(res_df.round(3), hide_index=True, width="stretch")
    st.caption("s_jel ve h: tüm daldırmaların toplamı (kür öncesi). s_toplam: kür sonrası toplam cidar w "
               "(spiralde s_1 + d_tel + s_2). Sütunlar .md'deki 'Numara bazında hedefler ve sonuçlar' tablosuyla aynıdır.")

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
    st.caption("Ters tasarım haritası henüz hesaplanmadı; 6. sayfada hesaplayınca rapora eklenebilir.")
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
