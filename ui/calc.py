"""Hesap adımlarını 'formül → değerler yerine konmuş hali → sonuç' biçiminde gösterir."""

from __future__ import annotations

import math

import streamlit as st


def L(x: float, digits: int = 4) -> str:
    """Sayıyı LaTeX için Türkçe ondalık virgülle yazar (çok büyük/küçükse ×10ⁿ)."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return r"\text{–}"
    if x == 0:
        return "0"
    exp = math.floor(math.log10(abs(x)))
    if -3 <= exp < 5:
        s = f"{x:.{max(digits - 1 - exp, 0)}f}" if exp < digits else f"{x:.0f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s.replace(".", "{,}")
    mant = x / 10**exp
    m = f"{mant:.{digits - 1}f}".rstrip("0").rstrip(".").replace(".", "{,}")
    return rf"{m} \times 10^{{{exp}}}"


def step(title: str, formula: str, substituted: str | None, result: str, note: str | None = None) -> None:
    r"""Bir hesap adımı kutusu.

    formula:      sembolik denklem (LaTeX)
    substituted:  değerlerin yerine konmuş hali (LaTeX, '=' olmadan); None ise gösterilmez
    result:       sonuç (LaTeX, ör. r'0{,}118' veya r'51{,}3\;°C')
    """
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.latex(formula)
        if substituted:
            st.latex(rf"= {substituted}")
        st.latex(rf"= \mathbf{{{result}}}")
        if note:
            st.caption(note)
