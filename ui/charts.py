"""Sayfalarda ve raporda ortak kullanılan grafikler (yalnızca go.Figure üretir, Streamlit'e bağlı değil)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from physics import gel
from physics.model import DipResult, ModelResult
from physics.units import from_si
from ui.common import COLORS, num

def _mm(x):
    return from_si(x, "mm")


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
