"""
Page 12: CRO Program Dashboard (legacy route → Experimentation Hub program tab).
"""

import streamlit as st
from pathlib import Path

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.markdown('<div class="terminal-header">PROGRAM // CRO (LEGACY ROUTE)</div>', unsafe_allow_html=True)
st.info(
    "The program registry and velocity metrics now live in **Experimentation Hub → Program** "
    "on the shared analytics workspace. This page mirrors the registry for bookmark compatibility."
)

if "model" not in st.session_state:
    st.warning("Configure **Business Model** first.")
    st.stop()

from ui.journey import require_workspace
from analytics.conversion import program_metrics
import pandas as pd

ws = require_workspace("cro_program")
if ws is None:
    st.stop()

if "cro_experiments" not in st.session_state:
    st.session_state["cro_experiments"] = []

experiments = st.session_state["cro_experiments"]
metrics = program_metrics(experiments)

c1, c2, c3, c4 = st.columns(4)
c1.metric("TOTAL", metrics["total_experiments"])
c2.metric("ACTIVE", metrics["active"])
c3.metric("WIN RATE", f"{metrics['win_rate_pct']:.1f}%")
c4.metric("CUMULATIVE $/MO", f"${metrics['cumulative_monthly_revenue_impact']:,.2f}")

if experiments:
    st.dataframe(pd.DataFrame(experiments), hide_index=True, use_container_width=True)
else:
    st.caption("Run **Experimentation Hub → Results** and save a workspace test to populate the registry.")
