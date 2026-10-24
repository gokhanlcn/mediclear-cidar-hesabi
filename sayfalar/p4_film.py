import numpy as np
import plotly.graph_objects as go
import streamlit as st

from physics import film
from physics.units import from_si, to_si
from ui import compute, state
from ui.calc import L, step
from ui.common import COLORS, assumptions, draft_banner, explain, num, show_fig
from ui.dips import select_dip

st.title("3. Sürüklenen film (D5–D8)")
st.markdown("Mandrel banyodan çekilirken jel katmanının üstüne ince bir **sıvı film** sürüklenir. "
            "Filmin kalınlığı viskoziteye, çekme hızına ve yüzey gerilimine bağlıdır; çekmeden sonra "
            "film yerçekimiyle aşağı süzülerek incelir.")

v = state.require_ready()
draft_banner(v, state.settings())
res = compute.run()
p = state.values_si()
dip = select_dip(res, "dip_film")
fc = dip.film
mm = lambda x: from_si(x, "mm")  # noqa: E731
R_film = dip.R_s + dip.s_jel
st.caption(f"Film, jel katmanının dış yüzeyine (yarıçap R_s + s_jel = {num(mm(R_film), 3)} mm) "
           "sürüklenir; D7b ve R/ℓ_c bu yarıçapla hesaplanır.")

# --- D5 -------------------------------------------------------------------------------
st.header("D5 – Viskozitenin sıcaklığa bağlılığı")
TbK, TrefK = p["T_b"], p["T_ref"]
step("Banyo sıcaklığındaki viskozite (Arrhenius)",
     r"\eta(T_b) = \eta_{ref}\,\exp\left[\frac{E_a}{R_g}\left(\frac{1}{T_b} - \frac{1}{T_{ref}}\right)\right]",
     rf"{L(p['eta_ref'])} \cdot \exp\left[\frac{{{L(p['E_a'])}}}{{{L(film.R_GAS)}}}\left(\frac{{1}}{{{L(TbK)}}} - "
     rf"\frac{{1}}{{{L(TrefK)}}}\right)\right]", rf"{L(dip.eta_b)}\;\text{{Pa·s}}",
     "Sıcaklıklar kelvin (K). R_g = 8,314 J/(mol·K) evrensel gaz sabitidir.")
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
st.header("D6 – Boyutsuz sayılar")
step("Kapiler sayı",
     r"Ca = \frac{\eta\, U}{\gamma}",
     rf"\frac{{{L(dip.eta_b)} \cdot {L(p['U'])}}}{{{L(p['gamma'])}}}", L(fc.Ca),
     "Viskoz kuvvetin yüzey gerilimine oranı (U m/s cinsinden).")
step("Kapiler uzunluk",
     r"\ell_c = \sqrt{\frac{\gamma}{\rho_p\, g}}",
     rf"\sqrt{{\frac{{{L(p['gamma'])}}}{{{L(p['rho_p'])} \cdot {L(p['g'])}}}}}\;\text{{m}}",
     rf"{L(mm(fc.l_c))}\;\text{{mm}}")
step("Yarıçap oranı",
     r"\frac{R}{\ell_c}", rf"\frac{{{L(mm(R_film))}}}{{{L(mm(fc.l_c))}}}", L(R_film / fc.l_c, 3),
     "R: filmin sürüklendiği yüzeyin (jel yüzeyi) yarıçapı.")
if fc.geometry == "levha":
    step("Levha dallarının kesiştiği kapiler sayı",
         r"C_{LLD}\,Ca^{*\,2/3} = C_{grav}\,Ca^{*\,1/2} \;\Rightarrow\; Ca^{*} = \left(\frac{C_{grav}}{C_{LLD}}\right)^{6}",
         rf"\left(\frac{{{L(p['C_grav'])}}}{{{L(p['C_lld'])}}}\right)^{{6}}", L(fc.Ca_cross),
         "Ca < Ca* ise D7a (LLD) dalı, Ca > Ca* ise D7c (yerçekimi) dalı daha küçüktür.")
st.success(f"**Otomatik seçim:** {fc.reason}")

# --- D7 -------------------------------------------------------------------------------
st.header("D7 – Sürüklenen film kalınlığı")
eta, U_, gam, rg = dip.eta_b, p["U"], p["gamma"], p["rho_p"] * p["g"]
D7 = {
    "D7a": ("D7a – Landau–Levich–Derjaguin",
            r"h = C_{LLD}\,\frac{(\eta U)^{2/3}}{\gamma^{1/6}\,(\rho_p g)^{1/2}}",
            rf"{L(p['C_lld'])} \cdot \frac{{({L(eta)} \cdot {L(U_)})^{{2/3}}}}{{{L(gam)}^{{1/6}} \cdot ({L(rg)})^{{1/2}}}}\;\text{{m}}"),
    "D7b": ("D7b – Fiber kaplama",
            r"h = C_{fib}\,R\,Ca^{2/3}",
            rf"{L(p['C_fib'])} \cdot {L(R_film)} \cdot {L(fc.Ca)}^{{2/3}}\;\text{{m}}"),
    "D7c": ("D7c – Viskoz–yerçekimi",
            r"h = C_{grav}\,\sqrt{\frac{\eta\, U}{\rho_p\, g}}",
            rf"{L(p['C_grav'])} \cdot \sqrt{{\frac{{{L(eta)} \cdot {L(U_)}}}{{{L(rg)}}}}}\;\text{{m}}"),
}
used = ["D7a", "D7c"] if fc.geometry == "levha" else ["D7b"]
for k in used:
    title, form, sub = D7[k]
    step(title, form, sub, rf"{L(mm(fc.values[k]))}\;\text{{mm}}")
if fc.geometry == "levha":
    step("Kullanılan film kalınlığı (levha: iki dalın küçüğü)",
         r"h_0 = \min(h_{D7a},\, h_{D7c})",
         rf"\min({L(mm(fc.values['D7a']))},\; {L(mm(fc.values['D7c']))})\;\text{{mm}}",
         rf"{L(mm(fc.h0))}\;\text{{mm}}", f"Belirleyici dal: {fc.formula}.")
others = [k for k in ("D7a", "D7b", "D7c") if k not in used]
st.caption("Karşılaştırma (bu geometride kullanılmayan formül): "
           + ", ".join(f"{k} = {num(mm(fc.values[k]), 3)} mm" for k in others)
           + ". Katsayılar 0. Veri girişi → Model katsayıları sekmesindedir.")
U_now = p["U"]
U = np.geomspace(min(0.05e-3, U_now / 5), max(20e-3, 5 * U_now), 240)
vals = film.all_formulas(R_film, dip.eta_b, U, p["gamma"], p["rho_p"], p["g"], p["C_lld"], p["C_fib"], p["C_grav"])
styles = {"D7a": COLORS["line"], "D7b": COLORS["ok"], "D7c": COLORS["accent"]}
fig = go.Figure()
for k, color in styles.items():
    fig.add_scatter(x=U * 1e3, y=mm(vals[k]), name=k, line=dict(color=color, width=1.5, dash="dot"))
fig.add_scatter(x=U * 1e3, y=mm(vals["min_ac" if fc.geometry == "levha" else "D7b"]),
                name="Otomatik seçim (levha: min(D7a, D7c); fiber: D7b)",
                line=dict(color="black", width=4))
fig.add_scatter(x=[U_now * 1e3], y=[mm(fc.h0)], mode="markers", name="Seçilen U",
                marker=dict(size=14, color="black", symbol="star"))
fig.update_layout(title="Film kalınlığı – çekme hızı", xaxis_title="Çekme hızı U [mm/s]",
                  yaxis_title="Film kalınlığı h_0 [mm]", xaxis_type="log", yaxis_type="log",
                  xaxis_dtick="D2", yaxis_dtick="D2")
show_fig(fig, f"D7_h_U_daldirma{dip.index}")
explain("Noktalı çizgiler üç formülün verdiği film kalınlığını, siyah kalın çizgi programın otomatik seçtiği "
        "sonucu gösterir: levhada iki dalın küçüğü (kırılma noktası Ca*), fiberde D7b. Yıldız tablodaki çekme "
        "hızıdır: daha hızlı çekmek daha kalın film demektir.")
# --- D8 -------------------------------------------------------------------------------
st.header("D8 – Süzülme ve akma gerilmesi")
L_dip = p["L"]
x = np.linspace(0, L_dip, 400)
args = (dip.h0, dip.eta_b, p["rho_p"], p["g"], dip.h_stop)
step("Akma gerilmesinin durdurduğu kalınlık",
     r"h_{dur} = C_{dur}\,\frac{\tau_y}{\rho_p\, g}",
     rf"{L(p['C_dur'])} \cdot \frac{{{L(p['tau_y'])}}}{{{L(p['rho_p'])} \cdot {L(p['g'])}}}\;\text{{m}}",
     rf"{L(mm(dip.h_stop))}\;\text{{mm}}")
if dip.h_stop >= dip.h0 or p["t_drain"] <= 0:
    st.info(f"h_dur = {num(mm(dip.h_stop), 3)} mm ≥ h_0 = {num(mm(dip.h0), 3)} mm (ya da t_süz = 0): akma "
            "gerilmesi filmi tutuyor, süzülme olmaz; film boy boyunca h_0 kalınlığındadır.")
else:
    t_d = p["t_drain"]
    step("Süzülme profili, alt uç (x = L, t = t_süz)",
         r"h(x,t) = \sqrt{\frac{\eta\, x}{\rho_p\, g\, t}},\qquad h_{dur} \le h \le h_0",
         rf"\sqrt{{\frac{{{L(dip.eta_b)} \cdot {L(L_dip)}}}{{{L(p['rho_p'])} \cdot {L(p['g'])} \cdot {L(t_d)}}}}}\;\text{{m}}"
         rf"\;\rightarrow\; \min(\cdot,\, h_0)",
         rf"{L(mm(dip.h_bottom))}\;\text{{mm}}",
         f"Üst uç (x = 0): {num(mm(dip.h_top), 3)} mm. Fark: {num(mm(dip.h_bottom - dip.h_top), 3)} mm.")
step("Boy boyunca ortalama film (D9'a giren h)",
     r"\bar h = \frac{1}{L}\int_0^L h(x, t_{\text{süz}})\,dx",
     rf"\frac{{1}}{{{L(L_dip)}}}\int_0^{{{L(L_dip)}}} h\,dx \;\;(\text{{sayısal integral, 401 nokta}})",
     rf"{L(mm(dip.h))}\;\text{{mm}}", "Tartım (D10) da ortalama kalınlık verdiği için toplamda ortalama kullanılır.")
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
    "Film formülü otomatik seçilir (levha: min(D7a, D7c), fiber: D7b); katsayılar 0. Veri girişindedir.",
    "Film, jel katmanının dış yüzeyine sürüklenir (yarıçap R_s + s_jel).",
    "Süzülme çekme bittikten sonra başlar; çekme sırasındaki süzülme ve kürde akma ihmal edildi.",
    "Toplam kalınlıkta filmin daldırma boyu L boyunca ortalaması kullanılır.",
])
