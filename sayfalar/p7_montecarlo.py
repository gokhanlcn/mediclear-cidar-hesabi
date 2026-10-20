import io
import time
from dataclasses import astuple

import pandas as pd
import streamlit as st

from physics import montecarlo, params
from physics.model import run_model
from physics.symbols import PARAMS
from physics.units import from_si
from ui import charts, compute, state
from ui.charts import FILM_LABEL, param_label as sym
from ui.common import draft_banner, explain, num, show_fig

st.title("7. Belirsizlik – Monte Carlo (D12)")
st.markdown("Veri sayfası değerleri tam bilinmediği için sonuç tek bir sayı değil, bir **aralıktır**. "
            "Program her parametreyi Min–Max aralığından rastgele seçip hesabı N kez tekrarlar; böylece "
            "kalınlığın hangi aralıkta çıkacağını ve hedefi tutturma olasılığını bulur.")
st.latex(r"s_{P5} \le s_{toplam} \le s_{P95}")

v = state.require_ready()
s = state.settings()
draft_banner(v, s)
mm = lambda x: from_si(x, "mm")  # noqa: E731

OUTPUTS = {"w": "Toplam cidar w (kür sonrası)", "s_toplam": "1. daldırma s_toplam (kür öncesi)"}



# --- Ayarlar --------------------------------------------------------------------------
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    N = c1.number_input("Deneme sayısı N", min_value=20, max_value=5000, value=200, step=50,
                        help="Ne kadar büyükse sonuç o kadar kararlı, ama süre uzar. 200 hızlı bir "
                             "ön bakış, 1000 rapor için önerilir.")
    dist_label = c2.radio("Dağılım", ["Üçgen (min, nominal, max)", "Düzgün (min–max)"],
                          help="Üçgen: nominale yakın değerler daha sık seçilir. Düzgün: aralıktaki her "
                               "değer eşit olasılıklı (.md'deki tanım).")
    speed = c3.radio("Hız / doğruluk", ["Hızlı (kaba ağ)", "Normal (ince ağ)"],
                     help="Hızlı modda D3 daha kaba bir ağla çözülür; sonuç normal moddan genellikle "
                          "%1–2 farklıdır.")
    c1, c2 = st.columns(2)
    out_key = c1.selectbox("İncelenecek sonuç", list(OUTPUTS), format_func=OUTPUTS.get,
                           index=0 if s.spiral else 1, disabled=not s.spiral)
    seed = c2.number_input("Rastgele tohum", min_value=0, value=1, step=1,
                           help="Aynı tohum aynı sonucu verir; sonuçları tekrarlanabilir yapar.")

dist = "düzgün" if dist_label.startswith("Düzgün") else "üçgen"
quality = "hızlı" if speed.startswith("Hızlı") else "normal"
if not s.spiral:
    out_key = "w"      # spiral yoksa w = s_kür
opt = compute.options(quality=quality)
ranges = state.ranges_si()
varying = [k for k in params.model_keys(s) if k in ranges and ranges[k][2] > ranges[k][0]]
# sonucu etkilemeyen parametreler sabit tutulur (gereksiz rastgelelik ve sahte korelasyon olmasın)
ranges = {k: (r if k in varying else (r[1], r[1], r[1])) for k, r in ranges.items()}

# süre tahmini
t0 = time.perf_counter()
run_model(state.nominal_si(), compute.options(quality=quality, keep_details=False))
per_run = time.perf_counter() - t0
st.caption(f"Belirsiz kabul edilen {len(varying)} parametre var (Min < Max). Tahmini süre: "
           f"yaklaşık {num(per_run * N, 0)} s.")
if not varying:
    st.warning("Hiçbir parametrenin Min ve Max değeri farklı değil; Monte Carlo anlamsız olur. "
               "Parametre girişinde Min/Max gir ya da ±%10 uygula.")

sig = (tuple(sorted(ranges.items())), int(N), dist, int(seed), astuple(opt))
stored = st.session_state.get("mc")

if st.button("▶️ Monte Carlo'yu çalıştır", type="primary", disabled=not varying):
    bar = st.progress(0.0, text="Başlıyor…")
    step = max(1, N // 100)

    def progress(i, n):
        if i % step == 0 or i == n:
            bar.progress(i / n, text=f"{i} / {n} deneme")

    mc = montecarlo.run_monte_carlo(ranges, int(N), opt, dist=dist, seed=int(seed), progress=progress)
    bar.empty()
    st.session_state["mc"] = stored = {"sig": sig, "res": mc, "out_key": out_key}

if stored is None:
    st.info("Ayarları seçip **Monte Carlo'yu çalıştır** düğmesine bas.")
    st.stop()
if stored["sig"] != sig:
    st.warning("Girdiler veya ayarlar son çalıştırmadan sonra değişti; aşağıdaki sonuçlar eski. "
               "Güncellemek için yeniden çalıştır.")

mc = stored["res"]
if mc.n_ok == 0:
    st.error("Hiçbir deneme hesaplanamadı. Aralıkların fiziksel olarak tutarlı olduğunu kontrol et "
             "(ör. T_g'nin alt sınırı T_b'nin üst sınırından büyük olmalı).")
    st.stop()
if mc.failures:
    with st.expander(f"⚠️ {sum(mc.failures.values())} deneme hesaplanamadı ve atlandı"):
        for msg, cnt in mc.failures.most_common():
            st.markdown(f"- **{cnt}×** {msg}")

y = mc.outputs[out_key].to_numpy()
pct = montecarlo.percentiles(y)
nominal_res = compute.run()
w_t, w_tol = nominal_res.w_target, nominal_res.w_tol
prob = montecarlo.hit_probability(y, w_t, w_tol) if out_key == "w" else None

st.header("Sonuç aralığı")
c1, c2, c3, c4 = st.columns(4)
c1.metric("P5", f"{num(mm(pct['P5']), 3)} mm", help="Denemelerin %5'i bu değerin altında.")
c2.metric("Medyan", f"{num(mm(pct['medyan']), 3)} mm")
c3.metric("P95", f"{num(mm(pct['P95']), 3)} mm", help="Denemelerin %95'i bu değerin altında.")
if prob is not None:
    c4.metric("Hedefi tutturma olasılığı", f"%{num(100 * prob, 0)}",
              help=f"w'nin {num(mm(w_t), 3)} ± {num(mm(w_tol), 3)} mm içinde kaldığı denemelerin oranı.")
st.caption(f"{mc.n_ok} başarılı deneme · dağılım: {dist} · hız: {quality}")

show_fig(charts.mc_histogram(y, pct, (w_t, w_tol) if out_key == "w" else None,
                             f"{OUTPUTS[out_key]} dağılımı"), f"D12_histogram_{out_key}")
explain("Her çubuk, kalınlığın o aralıkta çıktığı deneme sayısıdır. Kırmızı çizgiler P5, medyan ve P95'i "
        "gösterir: denemelerin %90'ı iki kesikli çizgi arasında kalır. Yeşil bant hedef aralıktır; "
        "çubukların ne kadarı bandın içindeyse hedefi tutturma olasılığı o kadar yüksektir.")

# --- Duyarlılık -----------------------------------------------------------------------
st.header("Duyarlılık – sonucu en çok ne etkiliyor?")
keys = [k for k in varying if k in mc.samples.columns]
if montecarlo.FILM_U in mc.samples.columns and nominal_res.dip1.film.transition:
    keys.append(montecarlo.FILM_U)
sens = montecarlo.sensitivity(mc.samples, y, keys)
stored.update(keys=keys, out_key=out_key)        # rapor sayfası için
if sens.empty:
    st.info("Duyarlılık hesaplanamadı (değişen parametre yok).")
else:
    show_fig(charts.tornado(sens, mc.n_ok), f"D12_tornado_{out_key}", height=charts.tornado_height(sens))
    names = ", ".join(PARAMS[k].sym if k in PARAMS else "D7 formül seçimi" for k in sens.index[:3])
    st.markdown(f"**Sonucu en çok bu parametreler etkiliyor: {names}.** Bu parametrelerin değerini "
                "daha iyi bir kaynakla daraltmak, sonuç aralığını en çok küçültür.")
    explain("Her çubuk bir parametrenin sonuçla ne kadar ilişkili olduğunu gösterir (−1 ile +1 arası). "
            "Kırmızı (pozitif): parametre artınca kalınlık artar. Mavi (negatif): parametre artınca "
            "kalınlık azalır. Gri bant içinde kalan çubuklar rastlantısal olabilir; bu parametreler "
            "sonucu pek etkilemez. Gri bant N büyüdükçe daralır.")

# --- İndir ----------------------------------------------------------------------------
st.header("Verileri indir")
table = mc.samples.copy()
for k in table.columns:
    if k in PARAMS:
        table[k] = from_si(table[k].to_numpy(), PARAMS[k].unit)
table = table.rename(columns={k: (f"{PARAMS[k].sym} [{PARAMS[k].unit}]" if k in PARAMS else FILM_LABEL)
                              for k in table.columns})
outs = mc.outputs.copy()
for k in outs.columns:
    if k == "T_m0":
        outs[k] = from_si(outs[k].to_numpy(), "°C")
    elif k != "ok":
        outs[k] = mm(outs[k].to_numpy())
outs = outs.rename(columns=lambda k: "T_m0 [°C]" if k == "T_m0" else ("uygun (1/0)" if k == "ok" else f"{k} [mm]"))
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as xw:
    pd.concat([table, outs], axis=1).to_excel(xw, sheet_name="Denemeler", index=False)
    pd.DataFrame({"Değer": ["P5", "Medyan", "P95"] + (["Hedefi tutturma olasılığı"] if prob is not None else []),
                  "Sonuç": [mm(pct["P5"]), mm(pct["medyan"]), mm(pct["P95"])] + ([prob] if prob is not None else [])}
                 ).to_excel(xw, sheet_name="Özet", index=False)
    if not sens.empty:
        pd.DataFrame({"Parametre": [sym(k) for k in sens.index], "Spearman": sens.values}).to_excel(
            xw, sheet_name="Duyarlılık", index=False)
st.download_button("💾 Monte Carlo sonuçlarını Excel olarak indir", buf.getvalue(),
                   file_name="mediclear_monte_carlo.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
