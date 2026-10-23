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
st.markdown(
    "Bu programın sonuçları teorik denklemlerden ve veri sayfası değerlerinden hesaplanır. Modeli "
    "doğrulamanın en basit deneysel yolu **tartımdır**: mandrel daldırmadan önce ve sonra tartılır, "
    "kütle farkından ortalama kaplama kalınlığı bulunur ve modelin öngördüğü kalınlıkla karşılaştırılır.")

with st.container(border=True):
    st.markdown(
        "**Doğrulama yöntemi (deneme yapılabildiğinde)**\n\n"
        "1. Kuru mandreli (2. daldırma için: iç katmanı ve teli takılı mandreli) hassas terazide tart.\n"
        "2. Tablodaki proses ayarlarıyla (T_m0, t_bekleme, U, t_süz) bir daldırma yap.\n"
        "3. Kaplamalı mandreli **kür fırınına girmeden önce** tekrar tart; fark kaplama kütlesi m'dir.\n"
        "4. Kaplanan boyu L ölç ve m'yi aşağıdaki tabloya gir. Birkaç numune ortalaması alınması önerilir.\n"
        "5. Tartımdan bulunan kalınlık, modelin öngördüğü kalınlığa yakınsa model doğrulanmış olur; değilse "
        "veri sayfası değerleri (özellikle T_g, η ve γ) ile film formülü seçimi gözden geçirilir.\n\n"
        "Şu an deney verisi yoksa bu sayfa, denemede **beklenen kütleleri** ve terazinin ayırt etmesi "
        "gereken kütle farkını verir.")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
p = state.values_si()
res = compute.run()
mm = lambda x: from_si(x, "mm")  # noqa: E731
g_ = lambda x: from_si(x, "g")  # noqa: E731

options = ["1. daldırma (çıplak mandrel)"] + (["2. daldırma (iç katman + tel üstü)"] if res.dip2 is not None else [])
which = st.radio("Tartılan daldırma", options, horizontal=True)
dip2_mode = which.startswith("2")

c1, c2 = st.columns(2)
L_mm = c1.number_input("L – kaplanan boy [mm]", min_value=1.0, value=float(mm(p["L"])), step=10.0,
                       help="Tartılan numunede plastisolle kaplanan boy.")
rho = c2.number_input("ρ_p – plastisol yoğunluğu [kg/m³]", min_value=100.0, value=float(p["rho_p"]), step=10.0)
Lb = to_si(L_mm, "mm")
R = res.R

st.header("Modelin öngördüğü kütle (kür öncesi, ıslak kaplama)")
if not dip2_mode:
    d = res.dip1
    s_model = d.s_toplam
    m_model = wall.expected_mass(s_model, rho, Lb, R)
    step("1. daldırma kaplama kütlesi",
         r"m_1 = \rho_p\,\pi\,L\,\left[(R + s)^2 - R^2\right],\qquad s = s_{jel,1} + \bar h_1",
         rf"{L(rho)} \cdot \pi \cdot {L(Lb)} \cdot \left[({L(R)} + {L(s_model)})^2 - {L(R)}^2\right]\;\text{{kg}}",
         rf"{L(g_(m_model))}\;\text{{g}}", f"s = {num(mm(d.s_jel), 3)} + {num(mm(d.h), 3)} = {num(mm(s_model), 3)} mm")
    R_base, m_groove = R, 0.0
else:
    d = res.dip2
    w = res.wire
    R1 = R + res.dip1.s_kur
    R2 = d.R_s
    s_model = d.s_toplam
    m_groove = wall.groove_mass(rho, Lb, R1, p["d_wire"], w.phi)
    m_cover = wall.expected_mass(s_model, rho, Lb, R2)
    m_model = m_groove + m_cover
    step("Oluklara dolan plastisol (tel halkasının plastisol kısmı)",
         r"m_{oluk} = \rho_p\,(1 - \varphi)\,\pi\,L\,\left[(R_1 + d)^2 - R_1^2\right],\qquad R_1 = R + s_1",
         rf"{L(rho)} \cdot (1 - {L(w.phi, 3)}) \cdot \pi \cdot {L(Lb)} \cdot \left[({L(R1)} + {L(p['d_wire'])})^2 - "
         rf"{L(R1)}^2\right]\;\text{{kg}}", rf"{L(g_(m_groove))}\;\text{{g}}",
         f"φ = πd/(4p) = {num(w.phi, 3)} (4. Tel halkası sayfası). Birim yüzey başına V'' = (1 − φ)d = "
         f"{num(w.V_groove * 1e3, 3)} mm³/mm².")
    step("Tel tepesi üzerindeki örtü",
         r"m_{\text{örtü}} = \rho_p\,\pi\,L\,\left[(R_2 + s_2)^2 - R_2^2\right],\qquad R_2 = R_1 + d,\; s_2 = s_{jel,2} + \bar h_2",
         rf"{L(rho)} \cdot \pi \cdot {L(Lb)} \cdot \left[({L(R2)} + {L(s_model)})^2 - {L(R2)}^2\right]\;\text{{kg}}",
         rf"{L(g_(m_cover))}\;\text{{g}}")
    step("2. daldırmada beklenen toplam kütle artışı",
         r"m_2 = m_{oluk} + m_{\text{örtü}}",
         rf"{L(g_(m_groove))} + {L(g_(m_cover))}\;\text{{g}}", rf"{L(g_(m_model))}\;\text{{g}}",
         "İkinci daldırmadan önceki tartımda iç katman ve tel mandrelin üzerindedir; fark yalnızca bu daldırmanın "
         "getirdiği plastisoldür.")
    R_base = R2

st.subheader("Terazi hassasiyeti")
ds_um = st.number_input("Ayırt edilmek istenen kalınlık farkı Δs [µm]", min_value=1.0, value=10.0, step=1.0,
                        help="Tartımla fark edilmesini istediğin en küçük kalınlık değişimi.")
dmds = wall.mass_sensitivity(rho, Lb, R_base, s_model)
step("Δs kalınlık farkına karşılık gelen kütle farkı",
     r"\Delta m \approx \frac{dm}{ds}\,\Delta s = 2\,\rho_p\,\pi\,L\,(R + s)\,\Delta s",
     rf"2 \cdot {L(rho)} \cdot \pi \cdot {L(Lb)} \cdot ({L(R_base)} + {L(s_model)}) \cdot {L(ds_um * 1e-6)}\;\text{{kg}}",
     rf"{L(g_(dmds * ds_um * 1e-6) * 1000)}\;\text{{mg}}",
     "Terazinin okuma hassasiyeti bu değerden küçük olmalıdır.")

# --- Ölçümler (varsa) -----------------------------------------------------------------
st.header("Ölçüm sonuçları (deneme yapıldığında)")
st.caption("Her numune için daldırma öncesi–sonrası kütle farkını (m, gram) yaz. Satır ekleyebilirsin. "
           "Veri yoksa bu bölüm boş kalır.")
meas = st.data_editor(pd.DataFrame({"Numune": ["1"], "m [g]": [np.nan]}), num_rows="dynamic",
                      hide_index=True, key=f"tartim_{int(dip2_mode)}",
                      column_config={"m [g]": st.column_config.NumberColumn(min_value=0.0, format="%.4f")})
m_g = pd.to_numeric(meas["m [g]"], errors="coerce").dropna()
m_g = m_g[m_g > 0]
if m_g.empty:
    st.info("Ölçüm girilmedi. Deney yapıldığında m değerlerini girince tartımdan bulunan kalınlık modelle "
            "karşılaştırılır.")
    st.stop()

m_mean = to_si(float(m_g.mean()), "g")
if not dip2_mode:
    s_meas = wall.weighed_thickness(m_mean, rho, Lb, R)
    step("Tartımdan ortalama kalınlık (D10)",
         r"s = \sqrt{R^2 + \frac{m}{\rho_p\,\pi\,L}} - R",
         rf"\sqrt{{{L(R)}^2 + \frac{{{L(m_mean)}}}{{{L(rho)} \cdot \pi \cdot {L(Lb)}}}}} - {L(R)}\;\text{{m}}",
         rf"{L(mm(s_meas))}\;\text{{mm}}", f"m: {len(m_g)} ölçümün ortalaması.")
    per = [wall.weighed_thickness(to_si(x, "g"), rho, Lb, R) for x in m_g]
else:
    s_meas = wall.weighed_cover_thickness(m_mean, m_groove, rho, Lb, R_base)
    step("Tartımdan örtü kalınlığı (D10, 2. daldırma)",
         r"s_2 = \sqrt{R_2^2 + \frac{m - m_{oluk}}{\rho_p\,\pi\,L}} - R_2",
         rf"\sqrt{{{L(R_base)}^2 + \frac{{{L(m_mean)} - {L(m_groove)}}}{{{L(rho)} \cdot \pi \cdot {L(Lb)}}}}} - {L(R_base)}\;\text{{m}}",
         rf"{L(mm(s_meas))}\;\text{{mm}}", f"m: {len(m_g)} ölçümün ortalaması; m_oluk modelden.")
    per = [wall.weighed_cover_thickness(to_si(x, "g"), m_groove, rho, Lb, R_base) for x in m_g]

c1, c2, c3 = st.columns(3)
c1.metric("Tartımdan kalınlık", f"{num(mm(s_meas), 3)} mm")
c2.metric("Model", f"{num(mm(s_model), 3)} mm")
c3.metric("Fark (ölçüm − model)", f"{num(mm(s_meas - s_model), 3)} mm",
          delta=f"{num(100 * (s_meas / s_model - 1), 0)} %" if s_model > 0 else None, delta_color="off")

fig = go.Figure()
fig.add_bar(x=["Model – jel", "Model – film"], y=[mm(d.s_jel), mm(d.h)],
            marker_color=[COLORS["line"], "#7FB3E0"], name="Model")
fig.add_bar(x=["Tartım"], y=[mm(s_meas)], marker_color=COLORS["plastisol"], name="Tartım (ortalama)")
fig.add_scatter(x=["Tartım"] * len(per), y=mm(np.array(per)), mode="markers", name="Tek ölçümler",
                marker=dict(color="black", size=9))
fig.add_hline(y=mm(s_model), line=dict(color=COLORS["line"], dash="dash"), annotation_text="model toplamı")
fig.update_layout(title="Model ve tartım karşılaştırması", yaxis_title="Kalınlık [mm]", barmode="stack")
show_fig(fig, "D10_tartim_karsilastirma", height=380)
explain("Mavi çubuklar modelin jel ve film kalınlığını, turuncu çubuk tartımdan bulunan kalınlığı gösterir; "
        "siyah noktalar tek tek ölçümlerdir. İkisi yakınsa model doğrulanmış olur. Büyük fark varsa önce veri "
        "sayfası değerlerini (özellikle T_g, η ve γ) ve film formülü seçimini kontrol et.")
