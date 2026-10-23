import numpy as np
import plotly.colors as pc
import plotly.graph_objects as go
import streamlit as st

from physics.units import from_si
from ui import charts, compute, state
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
st.latex(r"X = \frac{\rho_m c_m (R^2 - R_i^2)(T_{m0} - T_g)}{\rho_p c_p R^2 (T_g - T_b)}, \qquad "
         r"s_{max} = R\left(\sqrt{1 + X} - 1\right), \qquad "
         r"s_{max} \approx \frac{\rho_m c_m R (T_{m0} - T_g)}{2 \rho_p c_p (T_g - T_b)}")
c1, c2 = st.columns(2)
c1.metric("s_max – tam ifade", f"{num(mm(dip.s_max), 3)} mm",
          help="Mandrelin depoladığı ısının tamamı plastisolü jel sıcaklığına çıkarmaya gitseydi "
               "oluşacak en büyük kalınlık.")
if dip.s_max_thin is not None:
    c2.metric("s_max – ince katman yaklaşımı", f"{num(mm(dip.s_max_thin), 3)} mm",
              delta=f"{num(100 * (dip.s_max_thin / dip.s_max - 1), 0)} % fark" if dip.s_max > 0 else None,
              delta_color="off",
              help="s ≪ R ise tam ifadeye yaklaşır. Fark büyükse katman ince değildir; tam ifade kullanılmalı.")
else:
    c2.info("İnce katman yaklaşımı yalnızca dolu mandrelin 1. daldırması için tanımlı. "
            + ("2. daldırmada D2 bileşik bölgeye (mandrel + 1. kat) uygulandı." if dip.index == 2 else ""))

# --- D3 -------------------------------------------------------------------------------
st.header("D3 – Isı iletimi modeli")
st.latex(r"\rho c \frac{\partial T}{\partial t} = \frac{1}{r}\frac{\partial}{\partial r}"
         r"\left(k r \frac{\partial T}{\partial r}\right), \qquad "
         r"s_{jel}(t) = \max\{ r : T(r,t) \ge T_g \} - R")
c1, c2, c3 = st.columns(3)
c1.metric(f"s_jel (t_bekleme = {num(dip.t_wait, 0)} s)", f"{num(mm(dip.s_jel), 3)} mm")
c2.metric("s_jel / s_max", f"{num(100 * dip.s_jel / dip.s_max, 0)} %" if dip.s_max > 0 else "–",
          help="Mandrel ısısının ne kadarının jelleşmeye gittiğinin kabaca ölçüsü. %100'ü geçemez.")
c3.metric("Enerji dengesi hatası", f"{sol.energy_error:.1e}",
          help="Sayısal çözümün enerjiyi ne kadar koruduğu (dış sınırdan çıkan ısı dahil). "
               "Küçük olması çözümün güvenilir olduğunu gösterir.")

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
for i, L in enumerate(g.layers):
    color = COLORS["mandrel"] if i == 0 else COLORS["plastisol"]
    fig.add_vrect(x0=mm(L.r_in), x1=mm(L.r_out), fillcolor=color, opacity=0.25 if i == 0 else 0.35,
                  line_width=0, annotation_text=L.name or "katı", annotation_position="top left")
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
st.latex(r"s_{jel}(t) \approx C \sqrt{\alpha_p \, t_{bekleme}}, \qquad \alpha_p = \frac{k_p}{\rho_p c_p}")
c1, c2, c3 = st.columns(3)
c1.metric("C (D3'e uydurulan)", num(dip.C, 3))
c2.metric("α_p", f"{alpha_p:.2e} m²/s".replace(".", ","))
c3.metric("D4 tahmini", f"{num(mm(dip.C * np.sqrt(alpha_p * dip.t_wait)), 3)} mm",
          help="C·√(α_p·t_bekleme). D3 sonucuyla aynı mertebede olmalı.")
st.caption("C, D3'ün s_jel(t) eğrisine en küçük kareler yöntemiyle uydurulmuştur. C'nin 1 civarında "
           "olması, jel cephesinin ısının plastisolde yayılma mesafesi kadar ilerlediğini gösterir.")

assumptions([
    "Jelleşme gizli ısısı ihmal edildi.",
    "Banyodaki konveksiyon (sıvı hareketi) ihmal edildi; ısı yalnızca iletimle yayılır.",
    "Malzeme özellikleri sıcaklıkla değişmez kabul edildi.",
    "Jelleşme geri dönüşsüz: cephe bir kez ilerlediyse mandrel soğusa da geri gitmez.",
    "Uzak sınır T = T_b, yüzeyden en az 5·√(α_p·t_bekleme) ve 3 mm uzakta.",
    "Sayısal çözüm: Crank–Nicolson (ilk adımlar tam örtük), mandrel ve plastisol arasında harmonik "
    "ortalama iletkenlik.",
] + (["2. daldırmada 1. kat + tel bölgesi plastisol özellikleriyle tek katı katman sayıldı."]
     if dip.index == 2 else []))
