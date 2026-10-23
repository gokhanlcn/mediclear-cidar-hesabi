import streamlit as st

from physics.units import from_si
from ui import charts, compute, state
from ui.calc import L, step
from ui.common import assumptions, draft_banner, explain, num, show_fig

st.title("5. Toplam ve spiralli cidar (D9, D11)")
st.markdown("Jel katmanı ile sürüklenen filmin toplamı kürde biraz çeker (D9). Spiralli tüpte cidar iki "
            "daldırma ve aradaki yay telinden oluşur (D11). Sonuç şartnamedeki hedefle karşılaştırılır.")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
p = state.values_si()
mm = lambda x: from_si(x, "mm")  # noqa: E731
degC = lambda T: from_si(T, "°C")  # noqa: E731

if s.spiral:
    st.info("**Spiralli tüp: iki daldırma modeli.** 1. daldırma: çıplak mandrel → s_1. Ardından yay teli "
            "sarılır. 2. daldırma: plastisolle temas eden yüzey R + s_1 + d_tel. 2. daldırmanın girdileri "
            "(T_m0,2, T_s1, T_t, t_bekleme,2) **0. Veri girişi → Tel / 2. daldırma** sekmesindedir; tel halkasının "
            "hesabı **4. Tel halkası** sayfasındadır. "
            "w = s_1 + d_tel + s_2.")
else:
    st.info("Spiral kapalı: tek daldırma hesaplanır, w = s_kür. Spirali 0. Veri girişi → Hesap ayarları'ndan açabilirsin.")
res = compute.run()
dips = [res.dip1] + ([res.dip2] if res.dip2 else [])

# --- D9 -------------------------------------------------------------------------------
st.header("D9 – Kür sonrası kalınlık")
phi = p.get("phi", 1.0) if s.material_type == "Organosol" else 1.0
for d in dips:
    step(f"{d.index}. daldırma",
         r"s_{\text{kür}} = (1 - \varepsilon)\,(s_{jel} + \varphi\, \bar h)",
         rf"(1 - {L(p['eps'])}) \cdot ({L(mm(d.s_jel))} + {L(phi)} \cdot {L(mm(d.h))})\;\text{{mm}}",
         rf"{L(mm(d.s_kur))}\;\text{{mm}}",
         f"T_m0 = {num(degC(d.T_m0), 1)} °C, t_bekleme = {num(d.t_wait, 1)} s. "
         "φ: plastisolde 1, organosolde katı oranı (h_kuru = φ·h).")

# --- D11 ------------------------------------------------------------------------------
st.header("D11 – Toplam cidar ve hedef")
if res.dip2 is not None:
    step("Hesaplanan cidar (spiralli tüp)",
         r"w = s_1 + d_{tel} + s_2",
         rf"{L(mm(res.dip1.s_kur))} + {L(mm(p['d_wire']))} + {L(mm(res.dip2.s_kur))}\;\text{{mm}}",
         rf"{L(mm(res.w))}\;\text{{mm}}", "s_1: iç katman (1. daldırma), s_2: telin tepesinden itibaren örtü (2. daldırma).")
else:
    step("Hesaplanan cidar (tek daldırma)", r"w = s_{\text{kür}}", None, rf"{L(mm(res.w))}\;\text{{mm}}")
step("Hedef cidar (şartname)",
     r"w_{hedef} = \frac{OD - ID}{2} \pm \frac{\Delta OD}{2}",
     rf"\frac{{{L(mm(p['OD']))} - {L(mm(p['ID']))}}}{{2}} \pm \frac{{{L(mm(p['OD_tol']))}}}{{2}}\;\text{{mm}}",
     rf"{L(mm(res.w_target))} \pm {L(mm(res.w_tol))}\;\text{{mm}}")
OD_calc = p["ID"] + 2 * res.w
step("Sapma ve hesaplanan dış çap",
     r"\Delta w = w - w_{hedef}, \qquad OD = ID + 2w",
     rf"{L(mm(res.w))} - {L(mm(res.w_target))},\qquad {L(mm(p['ID']))} + 2 \cdot {L(mm(res.w))}\;\text{{mm}}",
     rf"\Delta w = {L(mm(res.deviation))}\;\text{{mm}},\quad OD = {L(mm(OD_calc))}\;\text{{mm}}",
     "Pozitif sapma: cidar hedeften kalın; negatif: ince.")
if res.ok:
    st.success(f"## ✅ Uygun\nCidar hedef tolerans içinde (sapma {num(mm(res.deviation), 3)} mm).")
else:
    yon = "kalın" if res.deviation > 0 else "ince"
    st.error(f"## ❌ Uygun değil\nCidar hedeften {num(abs(mm(res.deviation)), 3)} mm {yon}. "
             "Hangi ayarın değişmesi gerektiğini **Ters tasarım** sayfası gösterecek "
             f"(genel yön: mandrel sıcaklığını, bekleme süresini veya çekme hızını "
             f"{'düşür' if yon == 'kalın' else 'artır'}).")

# Cidar bileşimi grafiği
show_fig(charts.wall_composition(res, p["eps"], phi, p.get("d_wire", 0.0)), "D11_cidar_bilesimi", height=330)
explain("Çubuk, tüp cidarını içten dışa katmanlarına ayırır: 1. daldırmanın jel ve film kısmı, yay teli "
        "ve 2. daldırmanın jel ve film kısmı. Yeşil bant şartnamedeki hedef aralıktır; çubuğun ucu bu "
        "bandın içindeyse tüp uygundur.")

assumptions([
    "Spiralli tüp iki daldırma olarak modellendi; 2. daldırmada katmanlar: mandrel, iç PVC katmanı ve "
    "tel halkası (ayrıntı: 4. Tel halkası sayfası).",
    "Kür çekmesi kalınlığa doğrudan (1 − ε) ile uygulandı (D9).",
])
