"""Model çağrıları: arayüz ile physics/ arasındaki tek köprü (önbellekli)."""

from __future__ import annotations

from dataclasses import astuple, fields

import streamlit as st

from physics.model import ModelError, ModelResult, Options, run_model
from ui import state

QUALITY_LABELS = {"normal": "Normal (önerilen)", "hassas": "Hassas (yavaş)", "hızlı": "Hızlı (kaba ağ)"}


def dip2_overrides() -> dict:
    """2. daldırma için ayrı girilen T_m0 [K] ve t_bekleme [s]; None → 1. ile aynı."""
    return st.session_state.setdefault("dip2", {"T_m0_2": None, "t_wait_2": None})


def options(**override) -> Options:
    s = state.settings()
    d2 = dip2_overrides()
    opt = Options(spiral=s.spiral, T_m0_mode=s.T_m0_mode,
                  quality=st.session_state.get("quality", "normal"),
                  T_m0_2=d2["T_m0_2"], t_wait_2=d2["t_wait_2"])
    for k, v in override.items():
        setattr(opt, k, v)
    return opt


@st.cache_data(show_spinner="Hesaplanıyor…", max_entries=24)
def _cached_run(p_items: tuple, opt_items: tuple) -> ModelResult:
    opt = Options(**{f.name: v for f, v in zip(fields(Options), opt_items)})
    return run_model(dict(p_items), opt)


def run(p: dict | None = None, **override) -> ModelResult:
    """Nominal değerlerle modeli çalıştırır; ModelError'u sade mesajla gösterip sayfayı durdurur."""
    p = p if p is not None else state.nominal_si()
    try:
        return _cached_run(tuple(sorted(p.items())), astuple(options(**override)))
    except ModelError as exc:
        st.error(f"Hesap yapılamadı: {exc}")
        st.stop()


def quality_selector() -> None:
    """Sayfa başında D3 hesap hassasiyeti seçimi."""
    keys = list(QUALITY_LABELS)
    cur = st.session_state.get("quality", "normal")
    st.session_state["quality"] = st.radio(
        "D3 hesap hassasiyeti", keys, index=keys.index(cur), horizontal=True,
        format_func=QUALITY_LABELS.get,
        help="Isı iletimi ağının inceliği. Normal çoğu iş için yeterli; Hassas sonucu doğrulamak için.")
