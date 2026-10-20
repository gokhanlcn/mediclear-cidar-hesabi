"""Sayfalarda ortak arayüz parçaları."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from physics.symbols import PARAMS

DISCLAIMER = ("Sonuçlar modele dayalı tahmindir; kesin değerler devreye almada ölçümle "
              "kalibre edilmelidir.")

PLOT_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "locale": "tr",
}

COLORS = {
    "mandrel": "#8C97A6",
    "plastisol": "#E8A33D",
    "line": "#1F6FB2",
    "accent": "#C0392B",
    "ok": "#2E8B57",
    "band": "rgba(46,139,87,0.18)",
}


def explain(text: str) -> None:
    """Her grafiğin altındaki sade açıklama kutusu."""
    with st.container(border=True):
        st.markdown(f"**Bu grafik ne gösteriyor?** {text}")


def assumptions(items: list[str], title: str = "Model varsayımları") -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.markdown("\n".join(f"- {i}" for i in items))


def draft_banner(v, s) -> None:
    if s.draft and v.missing_source:
        syms = ", ".join(PARAMS[k].sym for k in v.missing_source)
        st.warning(f"⚠️ Taslak mod: kaynaksız değer kullanıldı ({syms}). Sonuçlar rapora "
                   "konmadan önce kaynaklar tamamlanmalı.")


def num(x: float, digits: int = 3) -> str:
    """Türkçe ondalık virgülle sayı."""
    if x is None:
        return "–"
    return f"{x:.{digits}f}".replace(".", ",")


def style_fig(fig: go.Figure, height: int = 420) -> go.Figure:
    m = fig.layout.margin       # sayfanın verdiği kenar boşlukları korunur
    margin = {k: getattr(m, k) if getattr(m, k) is not None else d
              for k, d in dict(l=60, r=20, t=50, b=50).items()}
    fig.update_layout(template="plotly_white", height=height, separators=",.",
                      plot_bgcolor="white", paper_bgcolor="white", font=dict(color="#262730"),
                      margin=margin)
    if fig.layout.legend.y is None and fig.layout.showlegend is not False:
        # açıklama grafiğin altında, başlıkla çakışmasın
        fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.22, x=0),
                          margin=dict(b=max(margin["b"], 110)), height=height + 60)
    return fig


def show_fig(fig: go.Figure, filename: str, height: int = 420) -> None:
    cfg = dict(PLOT_CONFIG)
    cfg["toImageButtonOptions"] = {**cfg["toImageButtonOptions"], "filename": filename}
    # theme=None: renk skalaları ve PNG çıktısı ekranda görünenle aynı kalsın
    st.plotly_chart(style_fig(fig, height), config=cfg, theme=None)
