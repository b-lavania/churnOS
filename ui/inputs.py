"""
Shared UI input components for the churnOS app (prototype).

Functions provided:
- global_filters(...): renders sidebar filters based on available dataframes
- churn_simulation_controls(...): renders the churn page top-row controls
- preset_manager(...): minimal preset save/load UI (file-backed)

This is intentionally lightweight — intended as a single place to centralize
common inputs and keys for the app.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_DIR = ROOT / ".settings"
PRESET_FILE = SETTINGS_DIR / "presets.json"


def _ensure_settings_dir() -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def global_filters(
    customers=None,
    transactions=None,
    marketplace=None,
    funnel=None,
    buyers=None,
    key_prefix: str = "global",
) -> Dict[str, Any]:
    """Render sidebar filters derived from provided dataframes.

    Returns a dict containing the selections (keys vary depending on
    which dataframes were supplied).
    """
    with st.sidebar:
        st.markdown('<div class="terminal-header">FILTERS</div>', unsafe_allow_html=True)
        selections: Dict[str, Any] = {}

        if customers is not None and "segment" in customers.columns:
            segs = customers["segment"].unique().tolist()
            selections["segments"] = st.multiselect("Segment", segs, default=segs, key=f"{key_prefix}_segments")

        if customers is not None and "acquisition_channel" in customers.columns:
            channels = customers["acquisition_channel"].unique().tolist()
            selections["channels"] = st.multiselect("Channel", channels, default=channels, key=f"{key_prefix}_channels")

        if funnel is not None and "device" in funnel.columns:
            devices = funnel["device"].unique().tolist()
            selections["devices"] = st.multiselect("Device", devices, default=devices, key=f"{key_prefix}_devices")

        if marketplace is not None and "category" in marketplace.columns:
            categories = marketplace["category"].unique().tolist()
            selections["categories"] = st.multiselect("Categories", categories, default=categories, key=f"{key_prefix}_categories")

        if marketplace is not None and "commission_tier" in marketplace.columns:
            tiers = marketplace["commission_tier"].unique().tolist()
            selections["tiers"] = st.multiselect("Seller Tiers", tiers, default=tiers, key=f"{key_prefix}_tiers")

        if buyers is not None and "segment" in buyers.columns:
            buyer_segments = buyers["segment"].unique().tolist()
            selections["buyer_segments"] = st.multiselect("Buyer Segments", buyer_segments, default=buyer_segments, key=f"{key_prefix}_buyer_segments")

        return selections


def churn_simulation_controls(defaults: Optional[Dict[str, Any]] = None, key_prefix: str = "churn") -> Dict[str, Any]:
    """Render the top-row simulation controls used on the churn page.

    Returns a dict of values and a boolean `calculate` indicating whether
    the user pressed the Calculate button.
    """
    defaults = defaults or {}
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        n = st.number_input("TOTAL CUSTOMERS", 500, 50000, int(defaults.get("n", 5000)), step=500, key=f"{key_prefix}_n")
    with col_b:
        churn_mult = st.slider("BASE CHURN MULTIPLIER", 0.1, 3.0, float(defaults.get("churn_mult", 1.0)), 0.1, key=f"{key_prefix}_churn_mult")
    with col_c:
        prem_mix = st.slider("PREMIUM SEGMENT MIX", -0.5, 0.5, float(defaults.get("prem_mix", 0.0)), 0.05, key=f"{key_prefix}_prem_mix")
    with col_d:
        sub_ratio = st.slider("SUBSCRIBE & SAVE %", 0.0, 1.0, float(defaults.get("sub_ratio", 0.0)), 0.05, key=f"{key_prefix}_sub_ratio")
    with col_e:
        st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True)
        calculate = st.button("Calculate", type="primary", key=f"{key_prefix}_calculate")

    return {"n": n, "churn_mult": churn_mult, "prem_mix": prem_mix, "sub_ratio": sub_ratio, "calculate": calculate}


def preset_manager(key_prefix: str = "presets") -> None:
    """Minimal preset save/load UI backed by a JSON file under `.settings/`.

    This is a light-weight helper for prototyping presets; it writes the
    picks to `.settings/presets.json` and exposes a basic save/load UI.
    """
    _ensure_settings_dir()
    # load existing presets (safe fallback)
    try:
        if PRESET_FILE.exists():
            presets = json.loads(PRESET_FILE.read_text(encoding="utf-8"))
        else:
            presets = {}
    except Exception:
        presets = {}

    cols = st.columns([3, 1, 1])
    with cols[0]:
        name = st.text_input("Preset name", key=f"{key_prefix}_name")
    with cols[1]:
        if st.button("Save preset", key=f"{key_prefix}_save"):
            if name:
                payload = st.session_state.get(f"{key_prefix}_current", {})
                presets[name] = payload
                PRESET_FILE.write_text(json.dumps(presets, indent=2), encoding="utf-8")
                st.success("Preset saved")
    with cols[2]:
        choice = st.selectbox("Load", options=[""] + list(presets.keys()), key=f"{key_prefix}_load")
        if choice:
            st.session_state[f"{key_prefix}_loaded"] = presets.get(choice)
            st.experimental_rerun()
