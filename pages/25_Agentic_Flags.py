"""Agentic feature-flag experiments — CPSO / TTFV / HITL impact (synthetic)."""

from pathlib import Path

import streamlit as st

from analytics.metrics import resolve_metric
from data.challenge_seed import FEATURE_FLAGS
from ui.explain import page_help
from ui.magazine import load_magazine_css, masthead, section_kicker
from ui.viz import feature_flag_impact
from ui.workspace_banner import require_workspace

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead("Experiment", "Agentic Flags", "Treatment vs control on cost, activation, and trust (dummy-seeded).")
page_help("experiments", show_card_glossary=True)
st.info("Dual-layer story: measurement → decision → flywheel. Flags instrument CPSO, TTFV, HITL on synthetic cohorts.", icon="ℹ️")

ws = require_workspace(st.session_state, page_label="Agentic Flags")

c1, c2, c3, c4 = st.columns(4)
c1.metric("CPSO", resolve_metric("cost_per_successful_outcome", ws)["display"])
c2.metric("TTFV", resolve_metric("time_to_first_value", ws)["display"])
c3.metric("HITL rate", resolve_metric("human_intervention_rate", ws)["display"])
c4.metric("Integration depth", resolve_metric("integration_depth_score", ws)["display"])

flag = st.selectbox("Feature flag", FEATURE_FLAGS)
fig = feature_flag_impact(ws, flag)
if fig is not None:
    section_kicker(f"Flag impact: {flag}")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Regenerate workspace to seed feature-flag assignments.")

section_kicker("All flags")
for f in FEATURE_FLAGS:
    fig_f = feature_flag_impact(ws, f)
    if fig_f is not None:
        st.plotly_chart(fig_f, use_container_width=True, key=f"flag_{f}")
