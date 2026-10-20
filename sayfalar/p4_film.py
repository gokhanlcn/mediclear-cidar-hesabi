import numpy as np
import plotly.graph_objects as go
import streamlit as st

from physics import film
from physics.units import from_si, to_si
from ui import compute, state
from ui.common import COLORS, assumptions, draft_banner, explain, num, show_fig
from ui.dips import select_dip

st.title("4. Sürüklenen film (D5–D8)")
st.markdown("Mandrel banyodan çekilirken jel katmanının üstüne ince bir **sıvı film** sürüklenir. "
            "Filmin kalınlığı viskoziteye, çekme hızına ve yüzey gerilimine bağlıdır; çekmeden sonra "
            "film yerçekimiyle aşağı süzülerek incelir.")

v = state.require_ready()
draft_banner(v, state.settings())
res = compute.run()
p = state.nominal_si()
dip = select_dip(res, "dip_film")
fc = dip.film
mm = lambda x: from_si(x, "mm")  # noqa: E731
R_film = dip.R_s + dip.s_jel
st.caption(f"Film, jel katmanının dış yüzeyine (yarıçap R_s + s_jel = {num(mm(R_film), 3)} mm) "
           "sürüklenir; D7b ve formül seçiminde bu yarıçap kullanılır.")

# --- D5 -------------------------------------------------------------------------------
st.header("D5 – Viskozitenin sıcaklığa bağlılığı")
st.latex(r"\eta(T) = \eta_{ref} \exp\left[\frac{E_a}{R_g}\left(\frac{1}{T} - \frac{1}{T_{ref}}\right)\right]")
c1, c2, c3 = st.columns(3)
c1.metric("η(T_b) – banyo sıcaklığında", f"{num(dip.eta_b, 3)} Pa·s")
c2.metric("η_ref", f"{num(p['eta_ref'], 3)} Pa·s", help=f"T_ref = {num(from_si(p['T_ref'], '°C'), 1)} °C'de")
c3.metric("T_b", f"{num(from_si(p['T_b'], '°C'), 1)} °C")
Tc = np.linspace(min(15.0, from_si(p["T_b"], "°C") - 5), max(50.0, from_si(p["T_b"], "°C") + 5), 100)
fig = go.Figure()
fig.add_scatter(x=Tc, y=film.viscosity(p["eta_ref"], p["E_a"], to_si(Tc, "°C"), p["T_ref"]),
                name="η(T)", line=dict(color=COLORS["line"], width=3))
fig.add_scatter(x=[from_si(p["T_ref"], "°C")], y=[p["eta_ref"]], mode="markers", name="η_ref (TDS)",
                marker=dict(size=11, color="gray", symbol="square"))
fig.add_scatter(x=[from_si(p["T_b"], "°C")], y=[dip.eta_b], mode="markers", name="Banyo (T_b)",
                marker=dict(size=13, color=COLORS["accent"], symbol="diamond"))
fig.update_layout(title="Plastisol viskozitesi – sıcaklık", xaxis_title="Sıcaklık [°C]",
                  yaxis_title="Viskozite η [Pa·s]")
show_fig(fig, "D5_viskozite", height=340)
explain("Eğri plastisolün sıcaklık arttıkça nasıl akışkanlaştığını gösterir. Gri kare veri sayfasındaki "
        "ölçüm noktası, kırmızı elmas banyo sıcaklığındaki değerdir. Banyo ısınırsa viskozite düşer ve "
        "sürüklenen film incelir.")

# --- D6 -------------------------------------------------------------------------------
st.header("D6 – Hangi film formülü geçerli?")
st.latex(r"Ca = \frac{\eta U}{\gamma}, \qquad \ell_c = \sqrt{\frac{\gamma}{\rho_p g}}")
c1, c2, c3 = st.columns(3)
c1.metric("Kapiler sayı Ca", num(fc.Ca, 4), help="Viskoz kuvvetin yüzey gerilimine oranı. Küçükse düşük hız.")
c2.metric("Kapiler uzunluk ℓ_c", f"{num(mm(fc.l_c), 3)} mm")
c3.metric("R / ℓ_c", num(R_film / fc.l_c, 2), help="1'den küçükse 'ince mandrel' (D7b), büyükse 'kalın mandrel' (D7a).")
box = st.warning if fc.transition else st.success
box(f"**Seçilen formül: {film.FORMULA_NAMES[fc.formula]}**\n\n{fc.reason}")

# --- D7 -------------------------------------------------------------------------------
st.header("D7 – Sürüklenen film kalınlığı")
st.latex(r"\text{D7a: } h = 0{,}94 \frac{(\eta U)^{2/3}}{\gamma^{1/6} (\rho_p g)^{1/2}} \qquad "
         r"\text{D7b: } h \approx 1{,}34\, R\, Ca^{2/3} \qquad "
         r"\text{D7c: } h \approx 0{,}8 \sqrt{\frac{\eta U}{\rho_p g}}")
cols = st.columns(4)
for col, key in zip(cols, ["D7a", "D7b", "D7c"]):
    col.metric(key + (" ✔" if key == fc.formula else ""), f"{num(mm(fc.values[key]), 3)} mm")
cols[3].metric("Kullanılan h_0", f"{num(mm(fc.h0), 3)} mm",
               help="Çekme anındaki film kalınlığı (seçilen formül).")
if fc.transition:
    st.info(f"Geçiş bölgesi: aday formüllerin aralığı **{num(mm(fc.h_low), 3)} – {num(mm(fc.h_high), 3)} mm**. "
            "Tek hesapta seçilen formül kullanılır; Monte Carlo bu aralıktan örnek alır.")

U_now = p["U"]
U = np.geomspace(min(0.05e-3, U_now / 5), max(20e-3, 5 * U_now), 240)
vals = {k: np.empty_like(U) for k in ("D7a", "D7b", "D7c")}
chosen = np.empty(U.size, dtype=object)
trans = np.zeros(U.size, dtype=bool)
for i, u in enumerate(U):
    c = film.choose_film(R_film, dip.eta_b, u, p["gamma"], p["rho_p"], p["g"])
    for k in vals:
        vals[k][i] = c.values[k]
    chosen[i], trans[i] = c.formula, c.transition
styles = {"D7a": COLORS["line"], "D7b": COLORS["ok"], "D7c": COLORS["accent"]}
fig = go.Figure()
for k, color in styles.items():
    fig.add_scatter(x=U * 1e3, y=mm(vals[k]), name=f"{k} (tüm aralık)", line=dict(color=color, width=1, dash="dot"),
                    legendgroup=k, showlegend=False)
    y = np.where(chosen == k, mm(vals[k]), np.nan)
    fig.add_scatter(x=U * 1e3, y=y, name=film.FORMULA_NAMES[k].split(" (")[0], legendgroup=k,
                    line=dict(color=color, width=4))
# Ca geçiş bandı
U_lo, U_hi = film.CA_LOW * p["gamma"] / dip.eta_b, film.CA_HIGH * p["gamma"] / dip.eta_b
fig.add_vrect(x0=U_lo * 1e3, x1=U_hi * 1e3, fillcolor="orange", opacity=0.12, line_width=0,
              annotation_text="0,1 < Ca < 1 (geçiş)", annotation_position="top left")
fig.add_scatter(x=[U_now * 1e3], y=[mm(fc.h0)], mode="markers", name="Seçilen U",
                marker=dict(size=14, color="black", symbol="star"))
fig.update_layout(title="Film kalınlığı – çekme hızı", xaxis_title="Çekme hızı U [mm/s]",
                  yaxis_title="Film kalınlığı h_0 [mm]", xaxis_type="log", yaxis_type="log",
                  xaxis_dtick="D2", yaxis_dtick="D2")
show_fig(fig, f"D7_h_U_daldirma{dip.index}")
explain("Üç formülün verdiği film kalınlığı çekme hızına göre çizildi. Kalın çizgi, o hızda geçerli "
        "kabul edilen formüldür; noktalı çizgiler formülün geçerli olmadığı yerlerdir. Turuncu bant "
        "formüllerin arasında kalan geçiş bölgesidir. Yıldız seçilen çekme hızıdır: daha hızlı çekmek "
        "daha kalın film demektir.")

# --- D8 -------------------------------------------------------------------------------
st.header("D8 – Süzülme ve akma gerilmesi")
st.latex(r"h(x,t) \approx \sqrt{\frac{\eta\, x}{\rho_p g\, t}}, \qquad h_{dur} \approx \frac{\tau_y}{\rho_p g}")
L = p["L"]
x = np.linspace(0, L, 400)
args = (dip.h0, dip.eta_b, p["rho_p"], p["g"], dip.h_stop)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Üst uç", f"{num(mm(dip.h_top), 3)} mm")
c2.metric("Alt uç", f"{num(mm(dip.h_bottom), 3)} mm")
c3.metric("Üst–alt farkı", f"{num(mm(dip.h_bottom - dip.h_top), 3)} mm")
c4.metric("Boy boyunca ortalama h", f"{num(mm(dip.h), 3)} mm",
          help="Toplam kalınlıkta (D9) bu ortalama kullanılır; tartım (D10) da ortalama kalınlık verir.")
if dip.h_stop >= dip.h0:
    st.info(f"h_dur = {num(mm(dip.h_stop), 3)} mm ≥ h_0: akma gerilmesi filmi tutuyor, süzülme olmaz.")
fig = go.Figure()
t_d = p["t_drain"]
for f, dash in ((0.25, "dot"), (4.0, "dash")):
    fig.add_scatter(x=mm(x), y=mm(film.drained_profile(x, f * t_d, *args)), name=f"t = {num(f * t_d, 0)} s",
                    line=dict(color="gray", dash=dash, width=1))
fig.add_scatter(x=mm(x), y=mm(film.drained_profile(x, t_d, *args)), name=f"t_süz = {num(t_d, 0)} s",
                line=dict(color=COLORS["line"], width=3))
fig.add_hline(y=mm(dip.h0), line=dict(color=COLORS["accent"], dash="dash"), annotation_text="h_0 (çekme anı)")
if dip.h_stop > 0:
    fig.add_hline(y=mm(dip.h_stop), line=dict(color=COLORS["ok"], dash="dash"),
                  annotation_text="h_dur (akma gerilmesi)", annotation_position="bottom right")
fig.update_layout(title="Mandrel boyunca film kalınlığı (süzülme sonrası)",
                  xaxis_title="Üst uçtan mesafe x [mm]", yaxis_title="Film kalınlığı h [mm]",
                  yaxis_rangemode="tozero")
show_fig(fig, f"D8_suzulme_daldirma{dip.index}")
explain("Çekmeden sonra sıvı film yerçekimiyle aşağı akar; bu yüzden mandrelin üst ucu alttan daha ince "
        "kalır. Mavi eğri kür fırınına girme anındaki profildir, gri eğriler daha kısa ve daha uzun "
        "bekleme süreleri için karşılaştırmadır. Film çekme anındaki kalınlığı (kırmızı) aşamaz; akma "
        "gerilmesi varsa yeşil çizginin altına inmez.")

assumptions([
    "D7 formülleri Newtonyen sıvı içindir; akma gerilmesi yalnızca D8'de hesaba katıldı.",
    "Formül seçimi (proje kararı): Ca ≥ 1 → D7c, R ≤ ℓ_c → D7b, R > ℓ_c → D7a; 0,1 < Ca < 1 veya "
    "ℓ_c < R < 3ℓ_c geçiş bölgesidir.",
    "Film, jel katmanının dış yüzeyine sürüklenir (yarıçap R_s + s_jel).",
    "Süzülme çekme bittikten sonra başlar; çekme sırasındaki süzülme ve kürde akma ihmal edildi.",
    "Toplam kalınlıkta filmin daldırma boyu L boyunca ortalaması kullanılır.",
])
