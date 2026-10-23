import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from physics import preheat
from physics.units import from_si
from ui import state
from ui.calc import L, step
from ui.common import COLORS, assumptions, draft_banner, explain, num, show_fig

st.title("1. Mandrel ön ısıtma (D1)")
st.markdown("Mandrelin fırında ne kadar sürede istenen sıcaklığa geldiğini **toplu kütle modeli** "
            "ile hesaplar. Model, mandrelin içinde sıcaklığın her yerde aynı olduğunu varsayar; "
            "bu varsayım Biot sayısı 0,1'den küçükse geçerlidir.")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
p = state.values_si()
C = lambda T: from_si(T, "°C")  # noqa: E731

R = p["ID"] / 2
if p["R_i"] > 0:
    st.warning("D1 yalnızca **dolu mandrel** için tanımlı (proje kararı). Mandrel içi boş "
               f"(R_i = {num(from_si(p['R_i'], 'mm'), 2)} mm) olduğu için bu sayfa hesap yapmaz; "
               "T_m0 doğrudan girilen değerdir.")
    st.stop()

res = preheat.preheat(p["rho_m"], p["c_m"], p["k_m"], R, p["R_i"], p["h_oven"], p["T_oven"],
                      p["T_0"], p["t_pre"])
tau, Bi = res["tau"], res["Bi"]
target = res["T_m_end"] if s.T_m0_mode == "D1" else p["T_m0"]
t_reach = preheat.time_to_reach(target, p["T_oven"], p["T_0"], tau)

Tf, T0 = C(p["T_oven"]), C(p["T_0"])
st.caption("Değerler SI birimleriyle yerine konur (R metre); sıcaklık farklarında °C ve K aynıdır.")
step("Zaman sabiti τ (dolu silindir, karakteristik boy V/A = R/2)",
     r"\tau = \frac{\rho_m\, c_m\, R}{2\, h_{\text{fırın}}}",
     rf"\frac{{{L(p['rho_m'])} \cdot {L(p['c_m'])} \cdot {L(R)}}}{{2 \cdot {L(p['h_oven'])}}}",
     rf"{L(tau)}\;\text{{s}}", "Mandrelin fırın sıcaklığına olan farkının %63'ünü kapattığı süre.")
step("Biot sayısı",
     r"Bi = \frac{h_{\text{fırın}}\, R}{2\, k_m}",
     rf"\frac{{{L(p['h_oven'])} \cdot {L(R)}}}{{2 \cdot {L(p['k_m'])}}}", L(Bi),
     "Toplu kütle modeli (mandrel içinde tek sıcaklık) Bi < 0,1 iken geçerlidir.")
step(f"t_ön = {num(p['t_pre'], 0)} s sonunda mandrel sıcaklığı",
     r"T_m(t) = T_{\text{fırın}} - (T_{\text{fırın}} - T_0)\, e^{-t/\tau}",
     rf"{L(Tf)} - ({L(Tf)} - {L(T0)}) \cdot e^{{-{L(p['t_pre'])}/{L(tau)}}}",
     rf"{L(C(res['T_m_end']))}\;°\text{{C}}",
     "D1 modunda bu değer 1. daldırmanın T_m0'ıdır." if s.T_m0_mode == "D1" else None)
if math.isfinite(t_reach):
    step(f"T_m0 = {num(C(target), 1)} °C'ye ulaşma süresi",
         r"t = \tau\, \ln\frac{T_{\text{fırın}} - T_0}{T_{\text{fırın}} - T_{m0}}",
         rf"{L(tau)} \cdot \ln\frac{{{L(Tf)} - {L(T0)}}}{{{L(Tf)} - {L(C(target))}}}",
         rf"{L(t_reach)}\;\text{{s}}")
if Bi >= preheat.BIOT_LIMIT:
    st.error(f"⚠️ Bi = {num(Bi, 3)} ≥ 0,1: **toplu kütle modeli geçersiz.** Mandrelin içi ile yüzeyi "
             "arasında belirgin sıcaklık farkı olur; süre bu sayfadakinden uzun çıkabilir. "
             "Daha iletken malzeme (Al) veya daha ince mandrel bu sorunu azaltır.")
else:
    st.success(f"Bi = {num(Bi, 4)} < 0,1: toplu kütle modeli geçerli.")
if math.isinf(t_reach):
    st.error("Fırın sıcaklığı hedef T_m0'dan düşük; mandrel bu sıcaklığa hiç ulaşamaz. "
             "T_fırın'ı artır veya hedef T_m0'ı düşür.")
elif s.T_m0_mode == "direct" and t_reach > p["t_pre"]:
    st.warning(f"Girilen ön ısıtma süresi (t_ön = {num(p['t_pre'], 0)} s), hedef T_m0'a ulaşmak için "
               f"gereken {num(t_reach, 0)} s'den kısa.")
elif s.T_m0_mode == "direct" and res["T_m_end"] - target > 5:
    st.info(f"Girilen t_ön = {num(p['t_pre'], 0)} s ile mandrel {num(C(res['T_m_end']), 1)} °C'ye "
            f"çıkar; hesaplarda ise doğrudan girilen T_m0 = {num(C(target), 1)} °C kullanılıyor. "
            f"İkisini tutarlı yapmak için t_ön'ü yaklaşık {num(t_reach, 0)} s yap ya da Veri "
            "girişi sayfasında T_m0'ı **D1'den hesapla** seçeneğine geç.")

t_max = max(1.3 * p["t_pre"], 5 * tau, 1.2 * t_reach if math.isfinite(t_reach) else 0)
t = np.linspace(0, t_max, 400)
fig = go.Figure()
fig.add_scatter(x=t, y=C(preheat.mandrel_temperature(t, p["T_oven"], p["T_0"], tau)),
                name="Mandrel sıcaklığı T_m(t)", line=dict(color=COLORS["line"], width=3))
fig.add_hline(y=C(p["T_oven"]), line=dict(dash="dash", color=COLORS["accent"]),
              annotation_text="T_fırın", annotation_position="top left")
fig.add_hline(y=C(p["T_g"]), line=dict(dash="dot", color=COLORS["plastisol"]),
              annotation_text="T_g (jelleşme)", annotation_position="bottom right")
fig.add_hline(y=C(target), line=dict(dash="dashdot", color=COLORS["ok"]),
              annotation_text="T_m0 (daldırma)", annotation_position="top right")
fig.add_vline(x=p["t_pre"], line=dict(dash="dash", color="gray"), annotation_text="t_ön")
if math.isfinite(t_reach):
    fig.add_scatter(x=[t_reach], y=[C(target)], mode="markers", name="Hedefe ulaşma",
                    marker=dict(size=12, color=COLORS["ok"], symbol="diamond"))
fig.update_layout(title="Mandrelin fırında ısınması (D1)", xaxis_title="Süre t [s]",
                  yaxis_title="Sıcaklık [°C]")
show_fig(fig, "D1_on_isitma")
explain("Mavi eğri mandrelin fırında zamanla nasıl ısındığını gösterir. Başta hızlı ısınır, fırın "
        "sıcaklığına yaklaştıkça yavaşlar. Yeşil elmas mandrelin daldırma sıcaklığına (T_m0) ulaştığı "
        "anı, gri dikey çizgi seçilen ön ısıtma süresini gösterir; elmas çizginin solundaysa süre yeterlidir.")

assumptions([
    "Mandrel içinde sıcaklık her noktada aynı (toplu kütle, Bi < 0,1).",
    "Fırın konveksiyon katsayısı h_fırın sabit; ışınım ayrıca hesaba katılmadı.",
    "Fırından banyoya transfer sırasındaki soğuma ihmal edildi.",
    "D1 yalnızca dolu mandrel için kullanılır (τ ifadesi dolu silindir içindir).",
])
