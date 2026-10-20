import streamlit as st

from physics.units import from_si, to_si
from ui import charts, compute, state
from ui.common import assumptions, draft_banner, explain, num, show_fig

st.title("5. Toplam ve spiralli cidar (D9, D11)")
st.markdown("Jel katmanı ile sürüklenen filmin toplamı kürde biraz çeker (D9). Spiralli tüpte cidar iki "
            "daldırma ve aradaki yay telinden oluşur (D11). Sonuç şartnamedeki hedefle karşılaştırılır.")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
p = state.nominal_si()
mm = lambda x: from_si(x, "mm")  # noqa: E731
degC = lambda T: from_si(T, "°C")  # noqa: E731

# --- 2. daldırma ayarları (hesaptan önce) ---------------------------------------------
if s.spiral:
    with st.container(border=True):
        st.markdown("**Spiralli tüp: iki daldırma modeli**  \n"
                    "1. daldırma: çıplak mandrel → s_1. Ardından yay teli sarılır. "
                    "2. daldırma: plastisolle temas eden yüzey R + s_1 + d_tel; 1. kat ve tel bölgesi "
                    "plastisol özellikleriyle tek katı katman sayılır (tel ihmal edilir). "
                    "w = s_1 + d_tel + s_2.")
        d2 = compute.dip2_overrides()
        separate = st.checkbox("2. daldırma için ayrı T_m0 ve t_bekleme gir",
                               value=d2["T_m0_2"] is not None or d2["t_wait_2"] is not None,
                               help="İşaretli değilse 2. daldırma 1. daldırmayla aynı değerlerle yapılır.")
        if separate:
            T1 = compute.run(T_m0_2=None, t_wait_2=None).T_m0   # 1. daldırmanın T_m0'ı (D1 modunda da)
            c1, c2 = st.columns(2)
            T2 = c1.number_input("T_m0,2 – 2. daldırmada mandrel sıcaklığı [°C]", min_value=0.0, max_value=500.0,
                                 value=float(degC(d2["T_m0_2"] if d2["T_m0_2"] is not None else T1)), step=5.0)
            t2 = c2.number_input("t_bekleme,2 – 2. daldırmada bekleme süresi [s]", min_value=0.1, max_value=3600.0,
                                 value=float(d2["t_wait_2"] if d2["t_wait_2"] is not None else p["t_wait"]), step=1.0)
            if to_si(T2, "°C") <= p["T_g"]:
                st.warning("T_m0,2 ≤ T_g: 2. daldırmada jel oluşmaz, yalnızca film sürüklenir.")
            d2.update(T_m0_2=to_si(T2, "°C"), t_wait_2=t2)
        else:
            d2.update(T_m0_2=None, t_wait_2=None)
else:
    st.info("Spiral kapalı: tek daldırma hesaplanır, w = s_kür. Spirali Parametre girişi → Hesap ayarları'ndan açabilirsin.")

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
    "Spiralli tüp iki daldırma olarak modellendi; tel ısıl olarak ihmal edildi, 1. kat + tel bölgesi "
    "plastisol özellikleriyle tek katman sayıldı.",
    "Kür çekmesi kalınlığa doğrudan (1 − ε) ile uygulandı (D9).",
    "Tel, cidara çapı kadar (d_tel) eklendi; telin plastisole gömülmesi ve sarım aralığı hesaba katılmadı.",
] + (["2. daldırma T_m0 ve t_bekleme 1. daldırmayla aynı."] if res.dip2 is not None
     and compute.dip2_overrides()["T_m0_2"] is None else []))
