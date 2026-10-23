"""Oturum durumu: parametre tablosu ve ayarlar tüm sayfalarda ortak."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from physics import params
from physics.params import Settings, Validation


def init() -> None:
    ss = st.session_state
    # Program açılışta MediClear proje verileriyle (veriler.md) başlar
    ss.setdefault("params_df", params.project_table())
    ss.setdefault("settings", params.project_settings())
    ss.setdefault("table_ver", 0)
    pending = ss.pop("pending_settings", None)
    if pending is not None:          # dosyadan yüklenen ayarlar (widget'lardan önce uygulanır)
        ss["settings"] = pending
        ss["draft_toggle"] = pending.draft
    ss.setdefault("draft_toggle", ss["settings"].draft)


def df() -> pd.DataFrame:
    return st.session_state["params_df"]


def settings() -> Settings:
    return st.session_state["settings"]


def set_df(new_df: pd.DataFrame, remount: bool = True) -> None:
    """Tabloyu değiştirir; remount=True ise düzenleyiciler yeni veriyle yeniden çizilir."""
    st.session_state["params_df"] = new_df.reset_index(drop=True)
    if remount:
        st.session_state["table_ver"] += 1


def validation() -> Validation:
    return params.validate(df(), settings())


def values_si() -> dict[str, float]:
    return params.values_si(df())


def require_ready() -> Validation:
    """Hesap sayfalarının başında: veri eksik/hatalıysa sade bir mesajla sayfayı durdurur."""
    v = validation()
    s = settings()
    if v.errors:
        st.error(f"Parametre tablosunda {len(v.errors)} hata var; hesap yapılamıyor. "
                 "**0. Veri girişi** sayfasına dönüp kırmızı (🔴) satırları düzelt.")
        with st.expander("Hataları göster"):
            for i in v.errors:
                st.markdown(f"- {i.message}")
        st.page_link("sayfalar/p1_parametre.py", label="Veri girişine git", icon="📝")
        st.stop()
    if v.missing_source and not s.draft:
        st.warning(f"{len(v.missing_source)} parametrenin kaynağı boş. .md'deki kurala göre "
                   "kaynağı olmayan değer hesaba girmez. Kaynak sütununu doldur ya da sol menüden "
                   "**Taslak mod**'u aç.")
        st.page_link("sayfalar/p1_parametre.py", label="Veri girişine git", icon="📝")
        st.stop()
    return v
