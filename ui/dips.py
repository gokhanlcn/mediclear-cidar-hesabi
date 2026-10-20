"""Spiralli tüpte daldırma seçimi (sayfalar arası ortak)."""

import streamlit as st

from physics.model import DipResult, ModelResult


def select_dip(res: ModelResult, key: str) -> DipResult:
    if res.dip2 is None:
        return res.dip1
    choice = st.radio("Daldırma", ["1. daldırma (çıplak mandrel)", "2. daldırma (spiral üstü)"],
                      horizontal=True, key=key,
                      help="Spiralli tüp iki daldırmayla yapılır. 2. daldırmada mandrelin üstünde "
                           "1. kat ve tel vardır.")
    return res.dip1 if choice.startswith("1") else res.dip2
