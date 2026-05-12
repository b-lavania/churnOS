"""
Page 13: Revenue Leakage Analyzer
===================================
Segment-level revenue loss quantification — device, channel, geo, visitor type.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

PLOTLY_THEME = {
    "layout": {
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "JetBrains Mono", "color": "#94a3b8", "size": 11},
        "xaxis": {"gridcolor": "rgba(255,255,255,0.05)", "zeroline": False, "linecolor": "rgba(255,255,255,0.1)"},
        "yaxis": {"gridcolor": "rgba(255,255,255,0.05)", "zeroline": False, "linecolor": "rgba(255,255,255,0.1)"},
        "margin": {"t": 40, "b": 40, "l": 40, "r": 20},
    }
}

st.markdown('<div class="terminal-header">DEEP DIVE // REVENUE LEAKAGE ANALYSIS</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Revenue Leakage</h1>', unsafe_allow_html=True)

with st.expander("Concept Playbook: How to use this page"):
    st.markdown('''
    **Overview:** Quantify exactly how much revenue each segment is leaving on the table vs the best-performing segment.
    **How to use:** Select a dimension (device, source, region, visitor type) to see the revenue gap per segment. Prioritize fixes by dollar impact, not just CVR.
    ''')

if "model" not in st.session_state:
    st.warning("No model defined. Go to **Business Model** to configure your business first.")
    st.stop()

s = st.session_state["model_summary"]
config = st.session_state["model_config"]

from data.generator import generate_funnel_events
from analytics.conversion import segment_revenue_gap

if "leakage_funnel" not in st.session_state:
    st.session_state["leakage_funnel"] = generate_funnel_events(n_sessions=30000)

funnel_df = st.session_state["leakage_funnel"]

dimension = st.selectbox("Segment By", ["device", "source", "region", "visitor_type"], key="leak_dim")

gap_df = segment_revenue_gap(
    funnel_df,
    segment_by=dimension,
    aov=s["aov"],
    gross_margin_pct=s["gross_margin_pct"],
)

total_gap = gap_df["revenue_gap"].sum()
st.markdown(f"<h3 style='color: #f43f5e;'>Total Revenue Gap: ${total_gap:,.2f}/mo</h3>", unsafe_allow_html=True)
st.caption("If all segments matched the best-performing segment's CVR.")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=gap_df["segment"], y=gap_df["current_revenue"],
    name="Current Revenue", marker_color="#94a3b8",
))
fig.add_trace(go.Bar(
    x=gap_df["segment"], y=gap_df["revenue_gap"],
    name="Revenue Gap", marker_color="#f43f5e",
    base=gap_df["current_revenue"],
))
fig.update_layout(**PLOTLY_THEME["layout"], barmode="stack")
fig.update_yaxes(title="MONTHLY REVENUE ($)")
st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="terminal-header">SEGMENT DETAIL</div>', unsafe_allow_html=True)
st.dataframe(gap_df, use_container_width=True, hide_index=True)

worst = gap_df.iloc[-1] if len(gap_df) > 0 else None
if worst is not None and worst["revenue_gap"] > 0:
    st.warning(
        f"Biggest opportunity: **{worst['segment']}** — closing its {worst['gap_pct_of_current']:.0f}% revenue gap "
        f"would add **${worst['revenue_gap']:,.2f}/mo** in incremental margin."
    )
