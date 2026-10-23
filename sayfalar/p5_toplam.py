import streamlit as st

from physics.units import from_si
from ui import charts, compute, state
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
st.latex(r"s_{\text{kür}} \approx (1 - \varepsilon)(s_{jel} + h), \qquad h_{kuru} = \varphi\, h \;\text{(organosol)}")
rows = []
for d in dips:
    rows.append({"Daldırma": f"{d.index}.", "T_m0 [°C]": num(degC(d.T_m0), 1), "t_bekleme [s]": num(d.t_wait, 1),
                 "s_jel [mm]": num(mm(d.s_jel), 3), "h (ort.) [mm]": num(mm(d.h), 3),
                 "s_toplam [mm]": num(mm(d.s_toplam), 3), "s_kür [mm]": num(mm(d.s_kur), 3)})
st.dataframe(rows, hide_index=True)
st.caption(f"ε = {num(p['eps'], 3)}" + (f", φ = {num(p.get('phi', 1.0), 2)} (organosol)" if s.material_type == "Organosol" else ""))

# --- D11 ------------------------------------------------------------------------------
st.header("D11 – Toplam cidar ve hedef")
st.latex(r"w = \frac{OD - ID}{2} = s_{\text{iç}} + d_{tel} + s_{\text{dış}}")
OD_calc = p["ID"] + 2 * res.w
c1, c2, c3, c4 = st.columns(4)
c1.metric("Hesaplanan w", f"{num(mm(res.w), 3)} mm")
c2.metric("Hedef w", f"{num(mm(res.w_target), 3)} ± {num(mm(res.w_tol), 3)} mm")
c3.metric("Sapma", f"{'+' if res.deviation >= 0 else ''}{num(mm(res.deviation), 3)} mm",
          help="Hesaplanan − hedef. Pozitif: cidar kalın; negatif: ince.")
c4.metric("Hesaplanan OD", f"{num(mm(OD_calc), 3)} mm", help=f"ID + 2w; hedef {num(mm(p['OD']), 2)} ± {num(mm(p['OD_tol']), 2)} mm")
if res.ok:
    st.success(f"## ✅ Uygun\nCidar hedef tolerans içinde (sapma {num(mm(res.deviation), 3)} mm).")
else:
    yon = "kalın" if res.deviation > 0 else "ince"
    st.error(f"## ❌ Uygun değil\nCidar hedeften {num(abs(mm(res.deviation)), 3)} mm {yon}. "
             "Hangi ayarın değişmesi gerektiğini **Ters tasarım** sayfası gösterecek "
             f"(genel yön: mandrel sıcaklığını, bekleme süresini veya çekme hızını "
             f"{'düşür' if yon == 'kalın' else 'artır'}).")

# Cidar bileşimi grafiği
phi = p.get("phi", 1.0) if s.material_type == "Organosol" else 1.0
show_fig(charts.wall_composition(res, p["eps"], phi, p.get("d_wire", 0.0)), "D11_cidar_bilesimi", height=330)
explain("Çubuk, tüp cidarını içten dışa katmanlarına ayırır: 1. daldırmanın jel ve film kısmı, yay teli "
        "ve 2. daldırmanın jel ve film kısmı. Yeşil bant şartnamedeki hedef aralıktır; çubuğun ucu bu "
        "bandın içindeyse tüp uygundur.")

assumptions([
    "Spiralli tüp iki daldırma olarak modellendi; 2. daldırmada katmanlar: mandrel, iç PVC katmanı ve "
    "tel halkası (ayrıntı: 4. Tel halkası sayfası).",
    "Kür çekmesi kalınlığa doğrudan (1 − ε) ile uygulandı (D9).",
])
