"""
Journey chrome: breadcrumbs, related pages, workspace data contract.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from core.workspace import Workspace, get_workspace_from_session


JOURNEY_PAGES: dict[str, dict[str, Any]] = {
    "executive": {
        "phase": "Impact",
        "title": "Executive Summary",
        "related": ["business_model", "lifecycle", "experimentation"],
    },
    "business_model": {
        "phase": "Setup",
        "title": "Business Model",
        "related": ["executive", "experimentation"],
    },
    "lifecycle": {
        "phase": "Observe",
        "title": "Lifecycle & NSM Proxies",
        "tables": ["customers", "transactions", "product_events"],
        "related": ["experimentation", "retention", "ecommerce"],
    },
    "experimentation": {
        "phase": "Experiment",
        "title": "Experimentation Hub",
        "tables": ["funnel", "experiment_assignments", "experiment_outcomes"],
        "related": ["lifecycle", "cro_program", "leakage", "unit_economics"],
    },
    "retention": {
        "phase": "Observe",
        "title": "Retention & Churn",
        "tables": ["customers", "transactions"],
        "related": ["lifecycle", "unit_economics"],
    },
    "leakage": {
        "phase": "Observe",
        "title": "Revenue Leakage",
        "tables": ["funnel"],
        "related": ["experimentation"],
    },
    "cro_program": {
        "phase": "Experiment",
        "title": "CRO Program",
        "related": ["experimentation"],
    },
    "ecommerce": {
        "phase": "Observe",
        "title": "E-Commerce Analytics",
        "tables": ["transactions"],
        "related": ["lifecycle"],
    },
    "mmm": {
        "phase": "Impact",
        "title": "Attribution & MMM",
        "tables": ["marketing"],
        "related": ["executive"],
    },
}


def render_journey_header(page_key: str) -> Workspace | None:
    """Render breadcrumb + data contract; return workspace if loaded."""
    spec = JOURNEY_PAGES.get(page_key, {"phase": "churnOS", "title": page_key, "related": []})
    phase = spec.get("phase", "")
    title = spec.get("title", page_key)

    st.markdown(
        f'<p style="font-family: JetBrains Mono; font-size: 0.7rem; color: #00f2ff; '
        f'letter-spacing: 0.12em; margin-bottom: 0.25rem;">{phase} › {title}</p>',
        unsafe_allow_html=True,
    )

    ws = get_workspace_from_session(st.session_state)
    related = spec.get("related", [])
    if related:
        labels = [JOURNEY_PAGES.get(k, {}).get("title", k) for k in related]
        st.caption("Related: " + " · ".join(labels))

    with st.expander("Data contract (workspace)", expanded=False):
        if ws is None:
            st.warning("No workspace loaded. Run **Business Model** first or resync below.")
        else:
            st.write(f"**Seed:** `{ws.seed}` · **Built:** {ws.built_at}")
            tables = spec.get("tables", ["customers", "transactions", "funnel", "product_events"])
            for t in tables:
                df = getattr(ws, t, None)
                if df is not None and hasattr(df, "__len__"):
                    st.write(f"- `{t}`: {len(df):,} rows")

    return ws


def require_workspace(page_key: str) -> Workspace | None:
    """Render header and stop page if workspace missing (after model check)."""
    ws = render_journey_header(page_key)
    if ws is None and "model" in st.session_state:
        if st.button("Build workspace from current model", type="primary", key=f"build_ws_{page_key}"):
            from core.workspace import build_workspace

            cfg = st.session_state.get("model_config", {})
            seed = int(st.session_state.get("workspace_seed", 42))
            ws_new = build_workspace(cfg, seed=seed)
            from core.workspace import sync_workspace_to_session

            sync_workspace_to_session(st.session_state, ws_new)
            st.rerun()
    return get_workspace_from_session(st.session_state)
