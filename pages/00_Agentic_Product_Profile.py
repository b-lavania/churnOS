"""Agentic Product Profile — ontology switch + workspace bootstrap."""

from pathlib import Path

import streamlit as st

from analytics.agentic_profile import PRESETS, get_preset, list_presets
from analytics.metrics import resolve_metric
from core.workspace import build_workspace, sync_workspace_to_session
from ui.explain import page_help
from ui.magazine import load_magazine_css, masthead, section_kicker

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead(
    "Configuration",
    "Agentic Product Profile",
    "Choose a product shape. This switches ontology semantics and synthetic warehouse priors.",
)
page_help("profile", show_notice=True)

st.info(
    "**Required before any chart works:** pick a preset and click **Generate workspace**. "
    "The first build takes about **30–90 seconds** — wait for the spinner to finish. "
    "Session state clears on browser refresh — regenerate if DECISIONS pages look empty.",
    icon="ℹ️",
)

preset_id = st.selectbox(
    "Profile preset",
    list_presets(),
    format_func=lambda k: PRESETS[k]["label"],
    index=list_presets().index(st.session_state.get("agentic_profile", {}).get("preset_id", "assistant_heavy"))
    if st.session_state.get("agentic_profile", {}).get("preset_id") in list_presets()
    else 0,
)

profile = get_preset(preset_id)
st.markdown(f"**{profile['description']}**")
section_kicker("Ontology")
st.write(
    f"Vertical: `{profile['ontology_vertical']}` · Version: `{profile['ontology_version']}` · "
    f"Billing: `{profile.get('billing_model', 'b2b_subscription')}` · Model: `{profile.get('default_model', '—')}`"
)

seed = st.number_input("Workspace seed", min_value=1, max_value=99999, value=int(st.session_state.get("workspace_seed", 42)))
data_source = st.selectbox("Data source", ["synthetic", "otel"], index=0)

if st.button("Generate workspace", type="primary"):
    try:
        with st.spinner(
            "Building synthetic warehouse (typically 30–90 seconds). "
            "Charts stay empty until this finishes — do not refresh."
        ):
            ws = build_workspace(
                profile,
                seed=int(seed),
                data_source=data_source,
                n_sessions=5_000,
            )
        sync_workspace_to_session(st.session_state, ws)
        st.session_state["growth_records"] = []
        st.success(
            f"Workspace built — {len(ws.seats)} seats, {len(ws.capabilities)} capabilities, "
            f"{len(getattr(ws, 'accounts', ws.workspaces))} accounts. "
            "Open **Radar** or any DECISIONS page."
        )
    except Exception as exc:
        st.error(f"Workspace build failed: {exc}")
        st.exception(exc)

ws = st.session_state.get("workspace")
if ws is not None:
    from core.workspace import get_workspace_from_session
    workspace = get_workspace_from_session(st.session_state)
    if workspace:
        section_kicker("Warehouse summary")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Seats", len(workspace.seats))
        c2.metric("Accounts", len(getattr(workspace, "accounts", workspace.workspaces)))
        c3.metric("Outcomes", len(getattr(workspace, "outcomes", [])))
        c4.metric("Runs", len(workspace.runs))
        c5.metric("Data version", workspace.meta.get("data_version", "—"))
        c6, c7 = st.columns(2)
        c6.metric("Verified activation ≤14d", resolve_metric("activation_verified_14d", workspace)["display"])
        c7.metric("Delegation ratio", resolve_metric("delegation_ratio", workspace)["display"])
