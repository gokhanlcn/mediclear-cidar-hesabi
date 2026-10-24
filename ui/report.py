"""Özet rapor: internetsiz açılan, kendi içinde tam tek bir HTML dosyası (tarayıcıdan PDF'e yazdırılabilir)."""

from __future__ import annotations

import datetime as _dt
import html

import pandas as pd
import plotly.graph_objects as go

from physics import params
from physics.model import ModelResult
from physics.params import Settings
from physics.symbols import PARAMS
from physics.units import from_si
from ui import charts
from ui.common import DISCLAIMER, num, style_fig

ASSUMPTIONS = [
    "Toplam kalınlık = jel katmanı (D3, ısı iletimi) + sürüklenen film (D7, D8); kürde (1 − ε) ile çeker (D9).",
    "Jelleşme gizli ısısı, banyodaki konveksiyon ve sıcaklığa bağlı özellik değişimi ihmal edildi.",
    "Jelleşme geri dönüşsüz kabul edildi; D3 Crank–Nicolson sonlu farklarla çözüldü.",
    "Film formülü otomatik seçilir: R > ℓ_c (levha) ise h = min(D7a, D7c), değilse D7b; model katsayıları "
    "(C_LLD, C_fib, C_grav, C_dur) kaynaklarıyla girdi tablosundadır.",
    "Film, jel yüzeyine (R_s + s_jel) sürüklenir; toplamda L boyunca ortalama film kalınlığı kullanılır.",
    "Spiralli tüp iki daldırma olarak modellendi; w = s_1 + d_tel + s_2. 2. daldırmada tel bölgesi, çelik tel "
    "ve oluklara dolan plastisolden oluşan halka olarak D3'e girer: φ = πd/(4p), (ρc)_eff karışım kuralı, "
    "k_eff Rayleigh bağıntısı, başlangıç sıcaklığı enerji dengesinden.",
    "D1 (toplu kütle) yalnızca dolu mandrelde, Bi < 0,1 iken geçerli; fırından banyoya transferde soğuma ihmal edildi.",
    "Tel halkası: tel ile matris arasında tam ısıl temas; oluklar daldırma anında T_b sıcaklığındaki plastisolle dolar; "
    "iç PVC katmanı plastisol ısıl özellikleriyle hesaplanır.",
]

CSS = """
@page { size: A4; margin: 10mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5px; color: #1d2330; margin: 0 auto;
       max-width: 1050px; padding: 14px; background: #fff; }
h1 { font-size: 19px; margin: 0 0 2px; } h2 { font-size: 13.5px; margin: 14px 0 6px; border-bottom: 2px solid #1F6FB2;
padding-bottom: 2px; color: #1F6FB2; }
.meta { color: #5b6475; margin-bottom: 8px; }
.note { background: #eaf2fb; border-left: 4px solid #1F6FB2; padding: 6px 9px; margin: 6px 0; }
.warn { background: #fff7db; border-left: 4px solid #e0a400; padding: 6px 9px; margin: 6px 0; }
.kpis { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0; }
.kpi { flex: 1 1 130px; border: 1px solid #d9dee8; border-radius: 6px; padding: 6px 9px; }
.kpi b { display: block; font-size: 16px; margin-top: 2px; }
.ok { color: #1e7a46; } .bad { color: #b3261e; }
table { border-collapse: collapse; width: 100%; margin: 4px 0; }
th, td { border: 1px solid #d9dee8; padding: 2px 5px; text-align: left; vertical-align: top; }
th { background: #f2f5fa; } td.n { text-align: right; white-space: nowrap; }
tr.nosrc td { background: #fff8de; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.cols { columns: 2; column-gap: 14px; }
.fig { border: 1px solid #e3e7ef; border-radius: 6px; break-inside: avoid; }
ul { margin: 4px 0 4px 16px; padding: 0; } li { margin: 1px 0; }
.footer { margin-top: 10px; color: #5b6475; font-size: 9.5px; }
@media screen and (max-width: 700px) { .grid { grid-template-columns: 1fr; } .cols { columns: 1; } }
@media print { .noprint { display: none; } body { padding: 0; } h2 { break-after: avoid; } }
"""


def _fmt(x, digits: int | None = None) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "–"
    if isinstance(x, str):
        return html.escape(x)
    return (f"{x:.{digits}f}" if digits is not None else f"{x:.6g}").replace(".", ",")


def _table(df: pd.DataFrame, num_cols: set[str] = frozenset(), row_class=None) -> str:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    rows = []
    for i, r in df.iterrows():
        cls = f' class="{row_class(i, r)}"' if row_class else ""
        cells = "".join(f'<td class="n">{_fmt(r[c])}</td>' if c in num_cols else f"<td>{_fmt(r[c])}</td>"
                        for c in df.columns)
        rows.append(f"<tr{cls}>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _fig_html(fig: go.Figure, first: bool, height: int = 300) -> str:
    style_fig(fig, height)
    fig.update_layout(title_font_size=13, font_size=10, margin=dict(t=40))
    return '<div class="fig">' + fig.to_html(full_html=False, include_plotlyjs=True if first else False,
                                             config={"displaylogo": False, "responsive": True}) + "</div>"


def build_report(df: pd.DataFrame, s: Settings, res: ModelResult, p: dict,
                 numara: pd.DataFrame | None = None, ters: dict | None = None) -> str:
    mm = lambda x: from_si(x, "mm")  # noqa: E731
    v = params.validate(df, s)
    now = _dt.datetime.now().strftime("%d.%m.%Y %H:%M")
    parts = [f"<h1>MediClear – Daldırma Cidar Kalınlığı Hesabı: Özet Rapor</h1>"
             f"<div class='meta'>Oluşturma: {now} · Denklemler: cidar_kalinligi_hesabi.md (D1–D11) ve tel halkası "
             "modeli (İstasyon Bazında Minimum Süre Hesabı Rev. 2, Bölüm 2.5)</div>",
             f"<div class='note'>{html.escape(DISCLAIMER)}</div>",
             "<div class='warn'><b>Doğrulama durumu:</b> Sonuçlar teorik denklemler ve veri sayfası değerleriyle "
             "hesaplanmıştır; model henüz deneyle doğrulanmamıştır. Doğrulama yöntemi: deneme daldırmasında "
             "daldırma öncesi–sonrası tartım ile ortalama kalınlığın bulunup modelle karşılaştırılması (D10).</div>"]
    if v.missing_source:
        syms = ", ".join(PARAMS[k].sym for k in v.missing_source)
        parts.append(f"<div class='warn'><b>Taslak:</b> kaynağı belirtilmemiş değerler kullanıldı ({html.escape(syms)}). "
                     "Bu değerler kaynakla teyit edilmeden rapor kesin sonuç olarak kullanılmamalıdır.</div>")

    # --- Ayarlar ve ana sonuç ---------------------------------------------------------
    mode = "D1 (ön ısıtma) + taşıma soğuması" if s.T_m0_mode == "D1" else "doğrudan girildi"
    parts.append("<h2>1. Ayarlar ve ana sonuç</h2>"
                 f"<div>Malzeme: <b>{s.material_type}</b> · Mandrel: <b>{html.escape(s.mandrel_material)}</b> · "
                 f"Spiral: <b>{'evet (iki daldırma)' if s.spiral else 'hayır (tek daldırma)'}</b> · "
                 f"T_m0: <b>{mode}</b> · Film formülü: <b>otomatik (levha: min(D7a, D7c); fiber: D7b)</b></div>")
    status = "<b class='ok'>✔ Uygun</b>" if res.ok else "<b class='bad'>✘ Uygun değil</b>"
    parts.append("<div class='kpis'>"
                 f"<div class='kpi'>Hesaplanan cidar w<b>{num(mm(res.w), 3)} mm</b></div>"
                 f"<div class='kpi'>Hedef w<b>{num(mm(res.w_target), 3)} ± {num(mm(res.w_tol), 3)} mm</b></div>"
                 f"<div class='kpi'>Sapma<b>{num(mm(res.deviation), 3)} mm</b></div>"
                 f"<div class='kpi'>Hesaplanan OD<b>{num(mm(p['ID'] + 2 * res.w), 3)} mm</b></div>"
                 f"<div class='kpi'>Durum{status}</div></div>")
    dips = [res.dip1] + ([res.dip2] if res.dip2 else [])
    rows = [{"Daldırma": f"{d.index}.", "T_m0 [°C]": from_si(d.T_m0, "°C"), "t_bekleme [s]": d.t_wait,
             "U [mm/s]": d.U * 1e3,
             "s_max (D2) [mm]": mm(d.s_max), "s_jel (D3) [mm]": mm(d.s_jel), "C (D4)": d.C,
             "D7 formülü": d.film.formula,
             "h_0 [mm]": mm(d.h0), "h ort. (D8) [mm]": mm(d.h), "s_kür (D9) [mm]": mm(d.s_kur)} for d in dips]
    dd = pd.DataFrame(rows).round(4)
    parts.append(_table(dd, num_cols=set(dd.columns) - {"Daldırma", "D7 formülü"}))

    wr = res.wire
    if wr is not None:
        T = lambda x: from_si(x, "°C")  # noqa: E731
        wt = pd.DataFrame([
            {"Büyüklük": "Tel hacim oranı φ = πd/(4p)", "Değer": wr.phi, "Birim": "–"},
            {"Büyüklük": "Halkanın ısı kapasitesi (ρc)_eff (karışım kuralı)", "Değer": wr.rhoc_eff, "Birim": "J/(m³·K)"},
            {"Büyüklük": "Halkanın radyal iletkenliği k_eff (Rayleigh)", "Değer": wr.k_eff, "Birim": "W/(m·K)"},
            {"Büyüklük": "Halkanın başlangıç sıcaklığı T_halka (enerji dengesi)", "Değer": T(wr.T_ring), "Birim": "°C"},
            {"Büyüklük": "Oluk plastisolü V'' = (1 − φ)d", "Değer": wr.V_groove * 1e3, "Birim": "mm³/mm²"},
            {"Büyüklük": "Temas sıcaklığı: mandrel – plastisol (1. daldırma)", "Değer": T(wr.T_c_dip1), "Birim": "°C"},
            {"Büyüklük": "Temas sıcaklığı: iç PVC – plastisol (2. daldırma)", "Değer": T(wr.T_c_layer), "Birim": "°C"},
            {"Büyüklük": "Temas sıcaklığı: tel – plastisol (2. daldırma)", "Değer": T(wr.T_c_wire), "Birim": "°C"},
            {"Büyüklük": "Tel çevresinde en kalın jel halkası δ_tel", "Değer": mm(wr.delta_wire), "Birim": "mm"},
        ])
        parts.append("<h3 style='font-size:12px;margin:10px 0 4px'>Tel halkası (2. daldırma)</h3>")
        parts.append(_table(wt, num_cols={"Değer"}))

    if numara is not None and not numara.empty:
        parts.append("<h2>2. Numara bazında hedefler ve sonuçlar</h2>")
        parts.append(_table(numara, num_cols={c for c in numara.columns if "[" in c}))

    # --- Grafikler ----------------------------------------------------------------------
    figs = [charts.gel_growth(res.dip1),
            charts.wall_composition(res, p["eps"], p.get("phi", 1.0) if s.material_type == "Organosol" else 1.0,
                                    p.get("d_wire", 0.0))]
    if ters is not None:
        figs.append(charts.design_map(ters["dm"], ters.get("title", "Ters tasarım haritası"),
                                      nominal=tuple(res.T_m0 if k == "T_m0" else p.get(k)
                                                    for k in (ters["dm"].x_key, ters["dm"].y_key))))
    parts.append(f"<h2>{3 if numara is not None and not numara.empty else 2}. Ana grafikler</h2><div class='grid'>")
    parts += [_fig_html(f, i == 0) for i, f in enumerate(figs)]
    parts.append("</div>")

    # --- Girdiler ------------------------------------------------------------------------
    keys = set(params.active_keys(s)) | {"T_fuz"}
    t = df[df.Kod.isin(keys)][["Kod", "Sembol", "Parametre", "Birim", params.VALUE_COL, "Kaynak", "Not"]]
    missing = set(v.missing_source)
    parts.append("<h2>Girdiler ve kaynaklar</h2>")
    parts.append(_table(t.drop(columns="Kod").reset_index(drop=True), num_cols={params.VALUE_COL},
                        row_class=lambda i, r: "nosrc" if t.iloc[i].Kod in missing else ""))
    parts.append("<h2>Model varsayımları</h2><ul class='cols'>"
                 + "".join(f"<li>{html.escape(a)}</li>" for a in ASSUMPTIONS) + "</ul>")
    parts.append("<div class='footer'>Bu rapor MediClear cidar kalınlığı hesap programıyla üretilmiştir. "
                 "Sarı satırlar kaynağı boş değerlerdir. PDF için tarayıcıda Yazdır → PDF olarak kaydet.</div>")
    return ("<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>MediClear Özet Rapor</title><style>{CSS}</style></head><body>"
            + "".join(parts) + "</body></html>")
