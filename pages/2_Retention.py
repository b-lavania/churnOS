"""
Page 2: Retention Analytics
===========================
Multi-dimensional retention cohorts and CLV synthesis.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from pathlib import Path

# ── Load CSS ──
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Plotly Theme Override ──
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

st.markdown('<div class="terminal-header">ANALYTICS UNIT // RETENTION MATRIX</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Retention Analytics</h1>', unsafe_allow_html=True)

# ── Data Load ──
if "app_data" not in st.session_state:
    from data.generator import generate_all_data
    st.session_state["app_data"] = generate_all_data()

data = st.session_state["app_data"]
customers = data["customers"]
transactions = data["transactions"]

# ── Simulation Controls ──
col1, col2, col3 = st.columns(3)
new_avg = col1.number_input("AVG TXNS PER CUSTOMER", 1, 50, 12, step=1)
new_aov = col2.slider("AOV MULTIPLIER", 0.5, 3.0, 1.0, 0.1)
new_disc = col3.slider("DISCOUNT FREQUENCY", 0.0, 1.0, 0.25, 0.05)

col4, col5, col6, col7 = st.columns(4)
new_refund = col4.slider("REFUND RATE", 0.0, 0.5, 0.05, 0.01)
new_cogs = col5.slider("COGS %", 0.0, 0.8, 0.40, 0.05)
new_cac = col6.number_input("BLENDED CAC ($)", 1, 500, 45, step=5)
with col7:
    st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True) # visual alignment
    if st.button("Calculate", type="primary", key="regen_ret"):
        from data.generator import generate_transactions
        st.session_state["app_data"]["transactions"] = generate_transactions(
            st.session_state["app_data"]["customers"], 
            avg_per_customer=new_avg, 
            aov_multiplier=new_aov, 
            discount_freq=new_disc,
            refund_rate=new_refund,
            cogs_pct=new_cogs
        )
        st.rerun()

# ── Sidebar ──
with st.sidebar:
    st.markdown('<div class="terminal-header">FILTERS</div>', unsafe_allow_html=True)
    sel_ch = st.multiselect("Channel", customers["acquisition_channel"].unique().tolist(), default=customers["acquisition_channel"].unique().tolist(), key="ret_ch_2")

filtered_cust = customers[customers["acquisition_channel"].isin(sel_ch)]
filtered_txns = transactions[transactions["customer_id"].isin(filtered_cust["customer_id"])]

from analytics.retention import cohort_retention_matrix, clv_estimate, retention_curve, day_n_retention

# ── KPI Row ──
day_n = day_n_retention(filtered_cust, filtered_txns, days=[1, 7, 30, 90])
cols = st.columns(len(day_n) + 1)
for col, (_, row) in zip(cols[:-1], day_n.iterrows()):
    col.metric(f"{row['day'].upper()} RETENTION", f"{row['retention_pct']}%")

clv_df = clv_estimate(filtered_cust, filtered_txns)
avg_clv = clv_df["clv"].mean() if len(clv_df) > 0 else 0
ltv_cac = round(avg_clv / new_cac, 1) if new_cac > 0 else 0.0
cols[-1].metric("LTV:CAC RATIO", f"{ltv_cac}x")

# ── Graphs ──
st.markdown('<div class="terminal-header">RETENTION COHORT HEATMAP</div>', unsafe_allow_html=True)
matrix = cohort_retention_matrix(filtered_txns, filtered_cust).tail(15)
fig = go.Figure(data=go.Heatmap(
    z=matrix.values, x=matrix.columns.tolist(), y=matrix.index.tolist(),
    colorscale=[[0, "#05050a"], [0.5, "#8a2be2"], [1, "#00f2ff"]],
    text=matrix.values, texttemplate="%{text:.0f}%",
))
fig.update_layout(**PLOTLY_THEME["layout"])
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="terminal-header">CLV DISTRIBUTION HISTOGRAM</div>', unsafe_allow_html=True)
clv_df = clv_estimate(filtered_cust, filtered_txns)
fig2 = px.histogram(clv_df, x="clv", color="segment", nbins=50, color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6"], labels={"clv": "CUSTOMER LIFETIME VALUE", "segment": "SEGMENT"})
fig2.update_layout(**PLOTLY_THEME["layout"], barmode="overlay")
st.plotly_chart(fig2, use_container_width=True)
st.markdown('<div class="terminal-header">BOX MODEL SEGMENT ANALYSIS</div>', unsafe_allow_html=True)
fig3 = px.box(clv_df, x="segment", y="clv", color="segment", color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6"], labels={"segment": "SEGMENT", "clv": "CLV"})
fig3.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

st.markdown('<div class="terminal-header">RETENTION CURVES BY CHANNEL</div>', unsafe_allow_html=True)
curves = retention_curve(filtered_cust, filtered_txns, by="acquisition_channel")
fig4 = px.line(curves, x="month", y="retention_pct", color="acquisition_channel", markers=True, color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6", "#f43f5e"], labels={"month": "MONTH", "retention_pct": "RETENTION %", "acquisition_channel": "ACQUISITION CHANNEL"})
fig4.update_layout(**PLOTLY_THEME["layout"], yaxis_range=[0, 105])
st.plotly_chart(fig4, use_container_width=True)

