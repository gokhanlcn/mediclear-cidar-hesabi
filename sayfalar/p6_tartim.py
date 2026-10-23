import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from physics import wall
from physics.units import from_si, to_si
from ui import compute, state
from ui.calc import L, step
from ui.common import COLORS, draft_banner, explain, num, show_fig

st.title("6. Tartımla doğrulama (D10)")
st.markdown("Bir deneme daldırmasında mandreli daldırmadan önce ve sonra tartarsan, kütle farkından "
            "ortalama kaplama kalınlığını bulabilirsin. Bu, modeli doğrulayan **tek gerçek veridir**.")

v = state.require_ready()
draft_banner(v, state.settings())
p = state.values_si()
res = compute.run()
d1 = res.dip1
mm = lambda x: from_si(x, "mm")  # noqa: E731

c1, c2, c3 = st.columns(3)
L_mm = c1.number_input("L – kaplanan boy [mm]", min_value=1.0, value=float(mm(p["L"])), step=10.0,
                       help="Tartılan numunede plastisolle kaplanan boy.")
R_mm = c2.number_input("R – mandrel yarıçapı [mm]", min_value=0.1, value=float(mm(res.R)), step=0.1,
                       help="Varsayılan: ID/2.")
rho = c3.number_input("ρ_p – plastisol yoğunluğu [kg/m³]", min_value=100.0, value=float(p["rho_p"]), step=10.0)
Lb, R = to_si(L_mm, "mm"), to_si(R_mm, "mm")

st.subheader("Ölçümler")
st.caption("Her deneme için daldırma öncesi–sonrası kütle farkını (m, gram) yaz. Satır ekleyebilirsin.")
meas = st.data_editor(pd.DataFrame({"Numune": ["1"], "m [g]": [np.nan]}), num_rows="dynamic",
                      hide_index=True, key="tartim",
                      column_config={"m [g]": st.column_config.NumberColumn(min_value=0.0, format="%.4f")})
m_g = pd.to_numeric(meas["m [g]"], errors="coerce").dropna()
m_g = m_g[m_g > 0]

s_model = d1.s_toplam
m_expected = wall.expected_mass(s_model, rho, Lb, R)
step("Modelin beklediği kaplama kütlesi (1. daldırma, kür öncesi)",
     r"m = \rho_p\,\pi\,L\,\left[(R + s)^2 - R^2\right]",
     rf"{L(rho)} \cdot \pi \cdot {L(Lb)} \cdot \left[({L(R)} + {L(s_model)})^2 - {L(R)}^2\right]\;\text{{kg}}",
     rf"{L(from_si(m_expected, 'g'))}\;\text{{g}}",
     f"s = s_toplam = s_jel + h̄ = {num(mm(s_model), 3)} mm. Deneme planlarken terazinin bu kütleyi yeterli "
     "hassasiyetle ölçebildiğinden emin ol.")

if m_g.empty:
    st.caption("Sonucu görmek için en az bir ölçüm gir.")
    st.stop()

s_meas = np.array([wall.weighed_thickness(to_si(m, "g"), rho, Lb, R) for m in m_g])
m_mean = float(m_g.mean())
mean = wall.weighed_thickness(to_si(m_mean, "g"), rho, Lb, R)   # ortalama kütleden kalınlık
step("Tartımdan ortalama kalınlık (D10)",
     r"s = \sqrt{R^2 + \frac{m}{\rho_p\,\pi\,L}} - R",
     rf"\sqrt{{{L(R)}^2 + \frac{{{L(to_si(m_mean, 'g'))}}}{{{L(rho)} \cdot \pi \cdot {L(Lb)}}}}} - {L(R)}\;\text{{m}}",
     rf"{L(mm(mean))}\;\text{{mm}}",
     f"m: {len(m_g)} ölçümün ortalaması ({num(m_mean, 4)} g).")
c1, c2, c3 = st.columns(3)
c1.metric("Tartımdan ortalama kalınlık", f"{num(mm(mean), 3)} mm",
          help=f"{len(s_meas)} ölçüm" + (f", std = {num(mm(s_meas.std(ddof=1)), 3)} mm" if len(s_meas) > 1 else ""))
c2.metric("Model (s_toplam, 1. daldırma)", f"{num(mm(s_model), 3)} mm")
c3.metric("Fark (ölçüm − model)", f"{num(mm(mean - s_model), 3)} mm",
          delta=f"{num(100 * (mean / s_model - 1), 0)} %" if s_model > 0 else None, delta_color="off")

fig = go.Figure()
fig.add_bar(x=["Model – jel", "Model – film"], y=[mm(d1.s_jel), mm(d1.h)],
            marker_color=[COLORS["line"], "#7FB3E0"], name="Model")
fig.add_bar(x=["Tartım (ortalama)"], y=[mm(mean)], marker_color=COLORS["plastisol"], name="Tartım")
fig.add_scatter(x=["Tartım (ortalama)"] * len(s_meas), y=mm(s_meas), mode="markers", name="Tek ölçümler",
                marker=dict(color="black", size=9))
fig.add_hline(y=mm(s_model), line=dict(color=COLORS["line"], dash="dash"), annotation_text="model toplamı")
fig.update_layout(title="Model ve tartım karşılaştırması", yaxis_title="Kalınlık [mm]", barmode="stack")
show_fig(fig, "D10_tartim_karsilastirma", height=380)
explain("Mavi çubuklar modelin jel ve film kalınlığını, turuncu çubuk tartımdan bulunan ortalama "
        "kalınlığı gösterir; siyah noktalar tek tek ölçümlerdir. İkisi yakınsa model güvenilirdir. "
        "Büyük fark varsa önce veri sayfası değerlerini (özellikle T_g, η ve γ) kontrol et.")
st.caption("Tartım, kür öncesi ıslak kaplamanın kütlesidir; bu yüzden model tarafında kür öncesi "
           "s_toplam (= s_jel + h) kullanıldı.")
