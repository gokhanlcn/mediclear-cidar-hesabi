import numpy as np
import plotly.colors as pc
import plotly.graph_objects as go
import streamlit as st

from physics.units import from_si
from ui import charts, compute, state
from ui.calc import L, step
from ui.dips import select_dip
from ui.common import COLORS, assumptions, draft_banner, explain, num, show_fig

st.title("2. Jel katmanı (D2, D3, D4)")
st.markdown("Sıcak mandrel banyoya girince ısısını plastisole verir; sıcaklığı **T_g**'yi geçen "
            "plastisol jelleşir. Bu sayfa jel katmanının kalınlığını üç yolla hesaplar: enerji tavanı "
            "(D2, üst sınır), ısı iletimi modeli (D3, asıl sonuç) ve difüzyon yaklaşımı (D4, kontrol).")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
compute.quality_selector()
res = compute.run()
p = state.values_si()
mm = lambda x: from_si(x, "mm")  # noqa: E731
degC = lambda T: from_si(T, "°C")  # noqa: E731

dip = select_dip(res, "dip_jel")
g = dip.gel_result
sol = g.sol

if dip.index == 2:
    st.info(f"2. daldırma: plastisolle temas eden yüzey R + s_1 + d_tel = {num(mm(dip.R_s), 3)} mm. "
            "Katmanlar: mandrel, iç PVC katmanı ve tel halkası (ayrıntı: 4. Tel halkası sayfası).")

# --- D2 -------------------------------------------------------------------------------
st.header("D2 – Enerji tavanı")
st.caption("Mandrelin (ve 2. daldırmada iç katmanların) T_g üzerinde depoladığı ısının tamamı plastisolü "
           "T_g'ye çıkarmaya gitseydi oluşacak en büyük jel kalınlığı. Değerler SI birimleriyle (m).")
Tg, Tb = degC(p["T_g"]), degC(p["T_b"])
rpcp = p["rho_p"] * p["c_p"]
if dip.index == 1:
    R, Ri, Tm = dip.R_s, p["R_i"], degC(dip.T_m0)
    X = p["rho_m"] * p["c_m"] * (R**2 - Ri**2) * max(Tm - Tg, 0) / (rpcp * R**2 * (Tg - Tb))
    step("Boyutsuz ısı oranı X",
         r"X = \frac{\rho_m c_m\,(R^2 - R_i^2)\,(T_{m0} - T_g)}{\rho_p c_p\, R^2\,(T_g - T_b)}",
         rf"\frac{{{L(p['rho_m'])} \cdot {L(p['c_m'])} \cdot ({L(R)}^2 - {L(Ri)}^2) \cdot ({L(Tm)} - {L(Tg)})}}"
         rf"{{{L(p['rho_p'])} \cdot {L(p['c_p'])} \cdot {L(R)}^2 \cdot ({L(Tg)} - {L(Tb)})}}", L(X))
else:
    R = dip.R_s
    terms = [(Ly, Ly.rho * Ly.c * (Ly.r_out**2 - Ly.r_in**2) * max(degC(Ly.T_init) - Tg, 0)) for Ly in g.layers]
    X = sum(t for _, t in terms) / (rpcp * R**2 * (Tg - Tb))
    with st.container(border=True):
        st.markdown("**Katmanların T_g üzerinde depoladığı ısı (birim boydaki ısının π'ye bölümü, J/m)**")
        st.latex(r"Q_i = (\rho c)_i\,\left(r_{\text{dış},i}^2 - r_{\text{iç},i}^2\right)\,\max(T_i - T_g,\,0)")
        st.latex(r"\begin{aligned}" + r" \\ ".join(
            rf"Q_{{\text{{{Ly.name}}}}} &= {L(Ly.rho * Ly.c)} \cdot ({L(Ly.r_out)}^2 - {L(Ly.r_in)}^2) \cdot "
            rf"\max({L(degC(Ly.T_init))} - {L(Tg)},\,0) = \mathbf{{{L(t)}}}" for Ly, t in terms) + r"\end{aligned}")
    step("Boyutsuz ısı oranı X (bileşik bölge)",
         r"X = \frac{\sum_i Q_i}{\rho_p c_p\, R_2^2\,(T_g - T_b)}",
         rf"\frac{{{L(sum(t for _, t in terms))}}}{{{L(rpcp)} \cdot {L(R)}^2 \cdot ({L(Tg)} - {L(Tb)})}}", L(X),
         "R_2: plastisolle temas eden yüzeyin (tel tepesi) yarıçapı.")
step("Enerji tavanı (tam ifade)",
     r"s_{max} = R\left(\sqrt{1 + X} - 1\right)",
     rf"{L(R)} \cdot \left(\sqrt{{1 + {L(X)}}} - 1\right)\;\text{{m}}", rf"{L(mm(dip.s_max))}\;\text{{mm}}")
if dip.s_max_thin is not None:
    step("Enerji tavanı (ince katman yaklaşımı, s ≪ R)",
         r"s_{max} \approx \frac{\rho_m c_m\, R\,(T_{m0} - T_g)}{2\,\rho_p c_p\,(T_g - T_b)}",
         rf"\frac{{{L(p['rho_m'])} \cdot {L(p['c_m'])} \cdot {L(R)} \cdot ({L(Tm)} - {L(Tg)})}}"
         rf"{{2 \cdot {L(p['rho_p'])} \cdot {L(p['c_p'])} \cdot ({L(Tg)} - {L(Tb)})}}\;\text{{m}}",
         rf"{L(mm(dip.s_max_thin))}\;\text{{mm}}",
         f"Tam ifadeden farkı %{num(100 * (dip.s_max_thin / dip.s_max - 1), 0)}. Fark büyükse katman ince "
         "değildir ve tam ifade kullanılmalıdır." if dip.s_max > 0 else None)

# --- D3 -------------------------------------------------------------------------------
st.header("D3 – Isı iletimi modeli (sayısal çözüm)")
n_cells = len(sol.rc)
bath = sol.region == sol.region.max()
with st.container(border=True):
    st.markdown("**Denklem ve jel tanımı**")
    st.latex(r"\rho c \frac{\partial T}{\partial t} = \frac{1}{r}\frac{\partial}{\partial r}"
             r"\left(k\, r\, \frac{\partial T}{\partial r}\right)")
    st.latex(r"s_{jel}(t) = \max\{ r : \max_{t' \le t} T(r,t') \ge T_g \} - R")
    st.markdown(
        "**Yöntem:** silindirik koordinatta sonlu hacim; zamanda Crank–Nicolson (ilk 4 adım tam örtük). "
        "Katman arayüzlerinde harmonik ortalama iletkenlik, r = 0'da simetri, dış sınırda T = T_b.\n\n"
        f"- Katmanlar: {', '.join(Ly.name for Ly in g.layers)}, plastisol banyosu\n"
        f"- Hücre sayısı: {n_cells} (banyoda {int(bath.sum())}, Δr = {num(mm(np.diff(sol.faces)[bath][0]) * 1000, 1)} µm)\n"
        f"- Dış sınır: r = {num(mm(sol.faces[-1]), 2)} mm (yüzeyden {num(mm(sol.faces[-1] - dip.R_s), 2)} mm; "
        f"en az 5·√(α_p·t) ve 3 mm)\n"
        f"- Zaman adımı sayısı: {len(sol.t) - 1}, toplam süre t_bekleme = {num(dip.t_wait, 1)} s\n"
        f"- Enerji dengesi hatası: {sol.energy_error:.1e} (dış sınırdan çıkan ısı dahil)")
    st.latex(rf"s_{{jel}}(t_{{bekleme}} = {L(dip.t_wait)}\,\text{{s}}) = \mathbf{{{L(mm(dip.s_jel))}\;\text{{mm}}}}")
    if dip.s_max > 0:
        st.caption(f"s_jel / s_max = %{num(100 * dip.s_jel / dip.s_max, 0)} (enerji tavanını aşamaz).")
t_ms = g.t
alpha_p = g.alpha_p
show_fig(charts.gel_growth(dip), f"D3_s_jel_daldirma{dip.index}")
explain("Mavi eğri, banyoda beklerken jel katmanının nasıl kalınlaştığını gösterir: başta hızlı, "
        "mandrel soğudukça yavaş büyür. Kırmızı kesikli çizgi enerji tavanıdır; mavi eğri bu çizgiyi "
        "geçemez. Turuncu kesikli eğri basit difüzyon tahminidir (D4); mavi eğriye yakınsa sonuç "
        "mertebe olarak tutarlıdır.")

# Radyal profil
st.subheader("Radyal sıcaklık profili")
t_sel = st.slider("Zaman [s]", 0.0, float(t_ms[-1]), float(t_ms[-1]),
                  step=max(float(t_ms[-1]) / 200, 0.01), format="%.2f s",
                  help="Kaydırarak sıcaklık profilinin zamanla nasıl değiştiğini izle.")
n = int(np.argmin(np.abs(t_ms - t_sel)))
r_mm = mm(sol.rc)
r_max_plot = mm(dip.R_s + max(3 * dip.s_max, 4 * np.sqrt(alpha_p * t_ms[-1]), 1e-3))
fig = go.Figure()
x0 = mm(sol.faces[0])
for i, Ly in enumerate(g.layers):
    color = COLORS["mandrel"] if i == 0 else COLORS["plastisol"]
    fig.add_vrect(x0=mm(Ly.r_in), x1=mm(Ly.r_out), fillcolor=color, opacity=0.25 if i == 0 else 0.35,
                  line_width=0, annotation_text=Ly.name or "katı", annotation_position="top left")
fig.add_vrect(x0=mm(dip.R_s), x1=r_max_plot, fillcolor=COLORS["plastisol"], opacity=0.10, line_width=0,
              annotation_text="plastisol banyosu", annotation_position="top right")
fig.add_scatter(x=r_mm, y=degC(sol.T[n]), name=f"T(r), t = {num(t_ms[n], 2)} s",
                line=dict(color=COLORS["line"], width=3))
fig.add_scatter(x=r_mm, y=degC(sol.T[0]), name="Başlangıç (t = 0)",
                line=dict(color="gray", dash="dot"))
fig.add_hline(y=degC(p["T_g"]), line=dict(color=COLORS["accent"], dash="dash"),
              annotation_text="T_g", annotation_position="bottom right")
front = dip.R_s + g.s_gel[n]
if g.s_gel[n] > 0:
    fig.add_vrect(x0=mm(dip.R_s), x1=mm(front), fillcolor=COLORS["ok"], opacity=0.25, line_width=0,
                  annotation_text="jel", annotation_position="bottom left")
fig.update_layout(title="Mandrel ve plastisolde sıcaklık dağılımı", xaxis_title="Yarıçap r [mm]",
                  yaxis_title="Sıcaklık [°C]", xaxis_range=[x0, r_max_plot])
show_fig(fig, f"D3_radyal_profil_daldirma{dip.index}")
explain("Yatay eksen mandrelin merkezinden dışarıya doğru mesafedir. Gri bölge mandrel, turuncu bölge "
        "plastisoldür. Mavi eğri seçilen andaki sıcaklığı gösterir; kırmızı kesikli çizginin (T_g) "
        "üstünde kalan plastisol jelleşir. Yeşil bant o ana kadar oluşan jel katmanıdır.")

# Isı haritası
st.subheader("Sıcaklık haritası (r – t)")
step_t = max(1, len(t_ms) // 200)
mask = sol.rc <= r_max_plot / 1000
step_r = max(1, int(mask.sum()) // 200)
Z = degC(sol.T[::step_t][:, mask][:, ::step_r]).T
fig = go.Figure()
# Inferno; ilk renk (#000004) tarayıcı tarafında bozulduğu için çok koyu laciyle değiştirildi
HEAT = ["#06040f"] + pc.sequential.Inferno[1:]
fig.add_heatmap(x=t_ms[::step_t], y=r_mm[mask][::step_r], z=Z, colorscale=HEAT,
                colorbar=dict(title="°C"))
fig.add_contour(x=t_ms[::step_t], y=r_mm[mask][::step_r], z=Z, showscale=False,
                contours=dict(start=degC(p["T_g"]), end=degC(p["T_g"]), size=1, coloring="none",
                              showlabels=True, labelfont=dict(color="white")),
                line=dict(color="white", width=2, dash="dash"), name="T_g izotermi", hoverinfo="skip")
fig.add_hline(y=mm(dip.R_s), line=dict(color="cyan", width=1), annotation_text="yüzey",
              annotation_position="bottom right")
fig.update_layout(title="Zaman ve yarıçapa göre sıcaklık", xaxis_title="Süre t [s]",
                  yaxis_title="Yarıçap r [mm]")
show_fig(fig, f"D3_isi_haritasi_daldirma{dip.index}", height=460)
explain("Her noktanın rengi o anda o yarıçaptaki sıcaklıktır (açık renk sıcak). Mavi-yeşil yatay çizgi "
        "mandrel yüzeyi, beyaz kesikli çizgi T_g sıcaklığının geçtiği yerdir. Beyaz çizginin yüzeyden "
        "uzaklaşması jel cephesinin ilerlemesidir.")

# --- D4 -------------------------------------------------------------------------------
st.header("D4 – Difüzyon yaklaşımı (kontrol)")
step("Plastisolün ısıl yayınımı",
     r"\alpha_p = \frac{k_p}{\rho_p\, c_p}",
     rf"\frac{{{L(p['k_p'])}}}{{{L(p['rho_p'])} \cdot {L(p['c_p'])}}}", rf"{L(alpha_p)}\;\text{{m}}^2/\text{{s}}")
step("C katsayısı (D3'ün s_jel(t) eğrisine en küçük kareler uydurması)",
     r"C = \frac{\sum_k s_{jel}(t_k)\,\sqrt{\alpha_p t_k}}{\sum_k \alpha_p\, t_k}",
     None, L(dip.C, 3),
     "C, D3 sonucundan hesaplanır; girdi değildir. 1 civarında olması jel cephesinin ısının yayılma mesafesi "
     "kadar ilerlediğini gösterir.")
step("D4 tahmini",
     r"s_{jel} \approx C\,\sqrt{\alpha_p\, t_{bekleme}}",
     rf"{L(dip.C, 3)} \cdot \sqrt{{{L(alpha_p)} \cdot {L(dip.t_wait)}}}\;\text{{m}}",
     rf"{L(mm(dip.C * np.sqrt(alpha_p * dip.t_wait)))}\;\text{{mm}}",
     f"D3 sonucu: {num(mm(dip.s_jel), 3)} mm. Aynı mertebede olmaları beklenir.")
assumptions([
    "Jelleşme gizli ısısı ihmal edildi.",
    "Banyodaki konveksiyon (sıvı hareketi) ihmal edildi; ısı yalnızca iletimle yayılır.",
    "Malzeme özellikleri sıcaklıkla değişmez kabul edildi.",
    "Jelleşme geri dönüşsüz: cephe bir kez ilerlediyse mandrel soğusa da geri gitmez.",
    "Uzak sınır T = T_b, yüzeyden en az 5·√(α_p·t_bekleme) ve 3 mm uzakta.",
    "Sayısal çözüm: Crank–Nicolson (ilk adımlar tam örtük), mandrel ve plastisol arasında harmonik "
    "ortalama iletkenlik.",
] + (["2. daldırmada katmanlar: mandrel, iç PVC katmanı (plastisol özellikleri) ve tel halkası "
      "(4. Tel halkası sayfası)."] if dip.index == 2 else []))
