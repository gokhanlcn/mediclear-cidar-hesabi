import plotly.graph_objects as go
import streamlit as st

from physics.units import from_si
from ui import compute, state
from ui.calc import L, step
from ui.common import COLORS, assumptions, draft_banner, explain, num, show_fig

st.title("4. Tel halkası (2. daldırma)")
st.markdown("Spiralli tüpte 1. daldırmadan sonra iç PVC katmanının üstüne yay teli sarılır. 2. daldırmada "
            "sarımlar arasındaki **oluklar** banyodaki plastisolle dolar. Bu sayfa tel bölgesini, kalınlığı "
            "tel çapı kadar olan bir **halka** (çelik tel + plastisol) olarak hesaplar ve bu halkayı "
            "2. daldırmanın ısı iletimi hesabına (D3) ayrı bir katman olarak verir.")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
if not s.spiral:
    st.info("Spiral kapalı (0. Veri girişi → Hesap ayarları): tel halkası hesaplanmıyor.")
    st.stop()

res = compute.run()
p = state.values_si()
w = res.wire
if w is None:
    st.info("Tel çapı 0 girildiği için tel halkası yok.")
    st.stop()
mm = lambda x: from_si(x, "mm")  # noqa: E731
C = lambda T: from_si(T, "°C")  # noqa: E731
d, pw = p["d_wire"], p["p_wire"]
rs_cs, rp_cp = p["rho_s"] * p["c_s"], p["rho_p"] * p["c_p"]

# --- Geometri ------------------------------------------------------------------------
st.header("Geometri")
step("Tel hacim oranı φ",
     r"\varphi = \frac{\pi d^2/4}{d\,p} = \frac{\pi\, d}{4\, p}",
     rf"\frac{{\pi \cdot {L(mm(d))}\,\text{{mm}}}}{{4 \cdot {L(mm(pw))}\,\text{{mm}}}}", L(w.phi, 3),
     "Bir hatve boyundaki halka kesitinde (d × p) telin kapladığı alan oranı.")
step("Oluklarda kalan plastisol (birim yüzey başına)",
     r"V'' = (1 - \varphi)\, d",
     rf"(1 - {L(w.phi, 3)}) \cdot {L(mm(d))}\,\text{{mm}}", rf"{L(w.V_groove * 1e3, 3)}\;\text{{mm}}^3/\text{{mm}}^2",
     "Oluklar daldırmada dolar; bu plastisol tellerin arasında kalır ve cidar kalınlığına ayrıca eklenmez "
     "(tel bölgesinin kalınlığı d'dir), ama kaplama kütlesine eklenir.")

# --- Isıl özellikler ------------------------------------------------------------------
st.header("Halkanın ısıl özellikleri")
step("Hacimsel ısı kapasitesi (karışım kuralı)",
     r"(\rho c)_{eff} = \varphi\,\rho_s c_s + (1-\varphi)\,\rho_p c_p",
     rf"{L(w.phi, 3)} \cdot {L(rs_cs)} + (1 - {L(w.phi, 3)}) \cdot {L(rp_cp)}",
     rf"{L(w.rhoc_eff)}\;\text{{J/(m}}^3\text{{K)}}")
step("Radyal ısıl iletkenlik (Rayleigh, tel eksenine dik ısı akışı)",
     r"k_{eff} = k_p\,\frac{k_s + k_p + \varphi\,(k_s - k_p)}{k_s + k_p - \varphi\,(k_s - k_p)}",
     rf"{L(p['k_p'])} \cdot \frac{{{L(p['k_s'])} + {L(p['k_p'])} + {L(w.phi, 3)}\,({L(p['k_s'])} - {L(p['k_p'])})}}"
     rf"{{{L(p['k_s'])} + {L(p['k_p'])} - {L(w.phi, 3)}\,({L(p['k_s'])} - {L(p['k_p'])})}}",
     rf"{L(w.k_eff)}\;\text{{W/(m·K)}}",
     "Rayleigh bağıntısı, matris içine gömülü paralel silindirler için ısı akışı silindir eksenine dik "
     "olduğunda geçerlidir. Radyal ısı akışı helis biçimli tele diktir.")

# --- Başlangıç sıcaklığı ------------------------------------------------------------
st.header("Halkanın başlangıç sıcaklığı")
step("Enerji dengesi (tel T_t, oluklara dolan plastisol T_b)",
     r"T_{halka} = \frac{\varphi\,\rho_s c_s\,T_t + (1-\varphi)\,\rho_p c_p\,T_b}{(\rho c)_{eff}}",
     rf"\frac{{{L(w.phi, 3)} \cdot {L(rs_cs)} \cdot {L(C(p['T_t']))} + (1 - {L(w.phi, 3)}) \cdot {L(rp_cp)} \cdot "
     rf"{L(C(p['T_b']))}}}{{{L(w.rhoc_eff)}}}",
     rf"{L(C(w.T_ring), 3)}\;°\text{{C}}")

# --- Kontrol hesapları ----------------------------------------------------------------
st.header("Kontrol hesapları")
st.markdown("Aşağıdaki el hesapları, D3 sayısal çözümünün sonucunu mertebe olarak kontrol etmek içindir.")
with st.container(border=True):
    st.markdown("**Isıl etkinlik (efüzivite)**")
    st.latex(r"e = \sqrt{k\,\rho\,c}")
    st.latex(r"\begin{aligned}"
             rf"e_m &= \sqrt{{{L(p['k_m'])} \cdot {L(p['rho_m'])} \cdot {L(p['c_m'])}}} = \mathbf{{{L(w.e_m, 4)}}} \\"
             rf"e_s &= \sqrt{{{L(p['k_s'])} \cdot {L(p['rho_s'])} \cdot {L(p['c_s'])}}} = \mathbf{{{L(w.e_s, 4)}}} \\"
             rf"e_p &= \sqrt{{{L(p['k_p'])} \cdot {L(p['rho_p'])} \cdot {L(p['c_p'])}}} = \mathbf{{{L(w.e_p, 3)}}}"
             r"\end{aligned}")
    st.caption("Birim: W·s^½/(m²·K). m: mandrel, s: tel, p: plastisol (iç PVC katmanı da plastisol özellikleriyle).")


def _tc(title, e1, T1, name1):
    Tc = (e1 * T1 + w.e_p * p["T_b"]) / (e1 + w.e_p)
    ok = Tc >= p["T_g"]
    step(title, r"T_c = \frac{e_1 T_1 + e_p T_b}{e_1 + e_p}",
         rf"\frac{{{L(e1, 4)} \cdot {L(C(T1))} + {L(w.e_p, 3)} \cdot {L(C(p['T_b']))}}}{{{L(e1, 4)} + {L(w.e_p, 3)}}}",
         rf"{L(C(Tc), 3)}\;°\text{{C}}",
         f"{name1} ile plastisolün ilk temas sıcaklığı. T_g = {num(C(p['T_g']), 1)} °C → "
         + ("T_c ≥ T_g: temas anında jel başlar." if ok else "T_c < T_g: temas anında jel oluşmaz."))


_tc("1. daldırma: mandrel – plastisol temas sıcaklığı", w.e_m, res.T_m0, "Mandrel")
_tc("2. daldırma: iç PVC katmanı (oluk tabanı) – plastisol temas sıcaklığı", w.e_p, p["T_s1"], "İç PVC katmanı")
_tc("2. daldırma: tel – plastisol temas sıcaklığı", w.e_s, p["T_t"], "Tel")
r_t = d / 2
if p["T_t"] <= p["T_g"]:
    st.info(f"Tel çevresi jel halkası: T_t = {num(C(p['T_t']), 1)} °C ≤ T_g = {num(C(p['T_g']), 1)} °C olduğu "
            "için tel çevresinde jel oluşmaz (δ_tel = 0).")
else:
    Qp = rs_cs * 3.141592653589793 * r_t**2 * (p["T_t"] - p["T_g"])
    step("Telin birim boyunda T_g üzerinde depoladığı ısı",
         r"Q' = \rho_s c_s\,\pi r_t^2\,(T_t - T_g)",
         rf"{L(rs_cs)} \cdot \pi \cdot ({L(r_t)})^2 \cdot ({L(C(p['T_t']))} - {L(C(p['T_g']))})",
         rf"{L(Qp)}\;\text{{J/m}}", "r_t = d/2, metre cinsinden.")
    step("Tel çevresinde oluşabilecek en kalın jel halkası (enerji üst sınırı)",
         r"\delta_{tel} = \sqrt{r_t^2 + \frac{Q'}{\pi\,\rho_p c_p\,(T_g - T_b)}} - r_t",
         rf"\sqrt{{({L(r_t)})^2 + \frac{{{L(Qp)}}}{{\pi \cdot {L(rp_cp)} \cdot ({L(C(p['T_g']))} - {L(C(p['T_b']))})}}}} - {L(r_t)}\;\text{{m}}",
         rf"{L(mm(w.delta_wire), 3)}\;\text{{mm}}",
         "Telin T_g üzerindeki ısısının tamamı plastisolü T_g'ye çıkarmaya gitseydi oluşacak en kalın jel "
         f"(karşılaştırma: tel çapı {num(mm(d), 2)} mm).")
# --- 2. daldırma D3 sonucu -----------------------------------------------------------
st.header("2. daldırmada jel (D3, sayısal çözüm)")
d2 = res.dip2
g = d2.gel_result
c1, c2, c3 = st.columns(3)
c1.metric("Tel tepesinin yarıçapı R_2", f"{num(mm(d2.R_s), 3)} mm", help="R + s_1 + d")
c2.metric("s_jel,2", f"{num(mm(d2.s_jel), 3)} mm", help="Tel tepesinin üzerinde oluşan jel")
c3.metric("Örtü (s_2, kür sonrası)", f"{num(mm(d2.s_kur), 3)} mm", help="Tel tepesinden itibaren")
sol = g.sol
fig = go.Figure()
colors = {"mandrel": COLORS["mandrel"], "iç PVC katmanı": "#7FB3E0", "tel halkası": "#B07AA1"}
for Lyr in g.layers:
    fig.add_vrect(x0=mm(Lyr.r_in), x1=mm(Lyr.r_out), fillcolor=colors.get(Lyr.name, "gray"), opacity=0.25,
                  line_width=0, annotation_text=Lyr.name, annotation_position="top left")
fig.add_scatter(x=mm(sol.rc), y=C(sol.T[0]), name="t = 0", line=dict(color="gray", dash="dot"))
fig.add_scatter(x=mm(sol.rc), y=C(sol.T[-1]), name=f"t = {num(d2.t_wait, 0)} s",
                line=dict(color=COLORS["line"], width=3))
fig.add_hline(y=C(p["T_g"]), line=dict(color=COLORS["accent"], dash="dash"), annotation_text="T_g")
fig.update_layout(title="2. daldırmada radyal sıcaklık", xaxis_title="Yarıçap r [mm]", yaxis_title="Sıcaklık [°C]",
                  xaxis_range=[mm(sol.faces[0]), mm(d2.R_s) + 2.5])
show_fig(fig, "tel_halkasi_radyal_profil")
explain("Gri bölge mandrel, mavi bölge 1. daldırmadan gelen iç PVC katmanı, mor bölge tel halkasıdır. "
        "Noktalı çizgi daldırma anındaki, mavi çizgi bekleme sonundaki sıcaklıktır. Halka, oluklara dolan soğuk "
        "plastisol yüzünden tel ve iç katmandan daha soğuk başlar; tel tepesinin dışında sıcaklık T_g'yi "
        "(kırmızı) geçmezse 2. daldırmada jel oluşmaz ve örtünün tamamı sürüklenen filmden gelir.")

assumptions([
    "Tel bölgesi, kalınlığı tel çapı d olan homojen bir halka olarak modellendi (helis, eksene paralel "
    "silindirler gibi ele alındı).",
    "Halkanın iletkenliği Rayleigh bağıntısıyla: tel ile matris arasında tam ısıl temas, ısı akışı tel eksenine dik.",
    "Oluklar daldırma anında banyo sıcaklığındaki (T_b) plastisolle dolar.",
    "İç PVC katmanının ısıl özellikleri plastisolünkiyle aynı alındı (ρ_p, c_p, k_p).",
    "Temas sıcaklığı ve tel çevresi jel halkası el hesaplarıdır (kontrol amaçlı); kalınlık D3 sayısal çözümünden alınır.",
])
