"""Sayfalarda ve raporda ortak kullanılan grafikler (yalnızca go.Figure üretir, Streamlit'e bağlı değil)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from physics import gel, montecarlo
from physics.model import DipResult, ModelResult
from physics.symbols import PARAMS
from physics.units import from_si
from ui.common import COLORS, num

FILM_LABEL = "D7 formül seçimi (geçiş bölgesi)"


def _mm(x):
    return from_si(x, "mm")


def param_label(k: str) -> str:
    return FILM_LABEL if k == montecarlo.FILM_U else f"{PARAMS[k].sym} – {PARAMS[k].name}"


def gel_growth(dip: DipResult) -> go.Figure:
    g = dip.gel_result
    fig = go.Figure()
    fig.add_scatter(x=g.t, y=_mm(g.s_gel), name="s_jel(t) – D3 (geri dönüşsüz)",
                    line=dict(color=COLORS["line"], width=3))
    if np.any(g.s_raw < g.s_gel - 1e-12):
        fig.add_scatter(x=g.t, y=_mm(g.s_raw), name="Anlık T_g izotermi",
                        line=dict(color=COLORS["line"], dash="dot"))
    fig.add_scatter(x=g.t, y=_mm(gel.diffusion_estimate(dip.C, g.alpha_p, g.t)),
                    name=f"D4: C·√(α_p·t), C = {num(dip.C, 3)}",
                    line=dict(color=COLORS["plastisol"], dash="dash"))
    fig.add_hline(y=_mm(dip.s_max), line=dict(color=COLORS["accent"], dash="dash"),
                  annotation_text="D2 enerji tavanı s_max", annotation_position="top left")
    fig.update_layout(title=f"Jel kalınlığının zamanla artışı ({dip.index}. daldırma)",
                      xaxis_title="Banyoda geçen süre t [s]", yaxis_title="Jel kalınlığı [mm]",
                      yaxis_rangemode="tozero")
    return fig


def wall_composition(res: ModelResult, eps: float, phi: float, d_wire: float) -> go.Figure:
    d1, k = res.dip1, 1 - eps
    parts = [("1. daldırma – jel", k * d1.s_jel, COLORS["line"]),
             ("1. daldırma – film", k * phi * d1.h, "#7FB3E0")]
    if res.dip2 is not None:
        d2 = res.dip2
        parts += [("Yay teli", d_wire, COLORS["mandrel"]),
                  ("2. daldırma – jel", k * d2.s_jel, COLORS["plastisol"]),
                  ("2. daldırma – film", k * phi * d2.h, "#F3CD8C")]
    fig = go.Figure()
    for name, val, color in parts:
        fig.add_bar(y=["Hesaplanan"], x=[_mm(val)], name=f"{name}: {num(_mm(val), 3)} mm",
                    orientation="h", marker_color=color)
    fig.add_vrect(x0=_mm(res.w_target - res.w_tol), x1=_mm(res.w_target + res.w_tol),
                  fillcolor=COLORS["band"], line_width=0, annotation_text="hedef ± tolerans",
                  annotation_position="top left")
    fig.add_vline(x=_mm(res.w_target), line=dict(color=COLORS["ok"], dash="dash"))
    fig.update_layout(barmode="stack", title="Cidar kalınlığının bileşimi (kür sonrası)",
                      xaxis_title="Kalınlık [mm] (içten dışa)",
                      legend=dict(orientation="h", y=-0.35, traceorder="normal"), margin=dict(b=120))
    return fig


def mc_histogram(y, pct: dict, target: tuple[float, float] | None, title: str) -> go.Figure:
    y = np.asarray(y)
    fig = go.Figure()
    fig.add_histogram(x=_mm(y), nbinsx=min(60, max(15, y.size // 10)), marker_color=COLORS["line"],
                      opacity=0.85, name="Denemeler")
    if target is not None:
        w_t, w_tol = target
        fig.add_vrect(x0=_mm(w_t - w_tol), x1=_mm(w_t + w_tol), fillcolor="rgba(46,139,87,0.35)",
                      line_width=0, annotation_text="hedef", annotation_position="bottom left",
                      annotation_font_color=COLORS["ok"])
    for i, (k, dash) in enumerate((("P5", "dash"), ("medyan", "solid"), ("P95", "dash"))):
        fig.add_vline(x=_mm(pct[k]), line=dict(color=COLORS["accent"], dash=dash, width=2))
        fig.add_annotation(x=_mm(pct[k]), y=1.0 - 0.07 * i, yref="paper", text=f"{k}: {num(_mm(pct[k]), 3)}",
                           showarrow=False, xanchor="left", yanchor="top", xshift=4,
                           bgcolor="rgba(255,255,255,0.8)", font=dict(color=COLORS["accent"]))
    fig.update_layout(title=title, xaxis_title="Kalınlık [mm]", yaxis_title="Deneme sayısı",
                      showlegend=False, bargap=0.05)
    return fig


def tornado(sens: pd.Series, n_ok: int, top_n: int = 12) -> go.Figure:
    top = sens.head(top_n)[::-1]
    fig = go.Figure(go.Bar(x=top.values, y=[param_label(k) for k in top.index], orientation="h",
                           marker_color=[COLORS["accent"] if x > 0 else COLORS["line"] for x in top.values],
                           text=[num(x, 2) for x in top.values], textposition="outside"))
    noise = 2 / n_ok ** 0.5      # rastgele örneklemede bu düzeyin altındaki korelasyon anlamsız
    fig.add_vrect(x0=-noise, x1=noise, fillcolor="rgba(128,128,128,0.18)", line_width=0,
                  annotation_text="gürültü seviyesi", annotation_position="top left")
    fig.update_layout(title="Duyarlılık – Spearman korelasyonu (tornado)",
                      xaxis_title="Korelasyon katsayısı", xaxis_range=[-1.1, 1.1], showlegend=False,
                      margin=dict(l=260))
    return fig


def tornado_height(sens: pd.Series, top_n: int = 12) -> int:
    return 120 + 32 * min(top_n, len(sens))


def design_map(dm, title: str, nominal: tuple[float, float] | None = None) -> go.Figure:
    """dm: inverse.DesignMap. nominal: (t_bekleme [s], T_m0 [K]) işaretlenecek nokta."""
    W = _mm(dm.w)
    lo, hi = _mm(dm.w_target - dm.w_tol), _mm(dm.w_target + dm.w_tol)
    x, y = dm.t_wait, from_si(dm.T_m0, "°C")
    fig = go.Figure()
    fig.add_contour(x=x, y=y, z=W, colorscale="Viridis", colorbar=dict(title="w [mm]"),
                    contours=dict(showlabels=True, labelfont=dict(color="white")), name="w",
                    hovertemplate="t_bekleme = %{x:.1f} s<br>T_m0 = %{y:.0f} °C<br>w = %{z:.3f} mm<extra></extra>")
    fig.add_contour(x=x, y=y, z=W, showscale=False, hoverinfo="skip", name="Hedef bandı",
                    # Plotly koşulu SAĞLAMAYAN bölgeyi boyar: "][" (bandın dışı) → bandın içi boyanır
                    contours=dict(type="constraint", operation="][", value=[lo, hi]),
                    fillcolor="rgba(255,60,60,0.6)", line=dict(color="red", width=2))
    if nominal is not None:
        t_n, T_n = nominal[0], from_si(nominal[1], "°C")
        if x.min() <= t_n <= x.max() and y.min() <= T_n <= y.max():
            fig.add_scatter(x=[t_n], y=[T_n], mode="markers", name="Şu anki ayar",
                            marker=dict(size=14, color="white", symbol="x", line=dict(width=2, color="black")))
    fig.update_layout(title=title, xaxis_title="Bekleme süresi t_bekleme [s]",
                      yaxis_title="Mandrel sıcaklığı T_m0 [°C]")
    return fig
