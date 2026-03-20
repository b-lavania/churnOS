"""
Page 1: Churn Analysis
======================
High-resolution churn intelligence.
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

st.markdown('<div class="terminal-header">ANALYTICS UNIT // CHURN REPORT</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Churn Analysis</h1>', unsafe_allow_html=True)

# ── Data Load ──
if "app_data" not in st.session_state:
    from data.generator import generate_all_data
    st.session_state["app_data"] = generate_all_data()

data = st.session_state["app_data"]
customers = data["customers"]

# ── Simulation Controls ──
col_a, col_b, col_c, col_d, col_e = st.columns(5)
with col_a:
    new_n = st.number_input("TOTAL CUSTOMERS", 500, 50000, 5000, step=500)
with col_b:
    new_churn_mult = st.slider("BASE CHURN MULTIPLIER", 0.1, 3.0, 1.0, 0.1)
with col_c:
    new_prem_mix = st.slider("PREMIUM SEGMENT MIX", -0.5, 0.5, 0.0, 0.05)
with col_d:
    new_sub = st.slider("SUBSCRIBE & SAVE %", 0.0, 1.0, 0.0, 0.05)
with col_e:
    st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True) # visual alignment
    if st.button("Calculate", type="primary", key="regen_churn"):
        from data.generator import generate_customers, generate_transactions
        new_cust = generate_customers(n=new_n, churn_multiplier=new_churn_mult, premium_mix=new_prem_mix, subscribe_ratio=new_sub)
        st.session_state["app_data"]["customers"] = new_cust
        st.session_state["app_data"]["transactions"] = generate_transactions(new_cust)
        st.rerun()

# ── Sidebar Filter (Compact Mode) ──
with st.sidebar:
    st.markdown('<div class="terminal-header">FILTERS</div>', unsafe_allow_html=True)
    selected_segments = st.multiselect(
        "Segment", customers["segment"].unique().tolist(),
        default=customers["segment"].unique().tolist(),
        key="churn_seg_2"
    )

filtered = customers[customers["segment"].isin(selected_segments)]

# ── Analytics Logic ──
from analytics.churn import compute_churn_rate, compute_cohort_churn, revenue_vs_logo_churn, churn_drivers, survival_analysis

# ── KPI Row ──
overall = compute_churn_rate(filtered)
rev_logo = revenue_vs_logo_churn(filtered)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("OVERALL CHURN", f"{overall['churn_rate'].iloc[0]}%")
c2.metric("LOGO CHURN RATE", f"{rev_logo['logo_churn_rate']}%")
c3.metric("REVENUE CHURN", f"{rev_logo['revenue_churn_rate']}%")
c4.metric("CHURN VOL", f"{len(filtered[filtered['is_churned']]):,}")
sub_pct = round(filtered['is_subscriber'].mean() * 100, 1) if 'is_subscriber' in filtered else 0.0
c5.metric("SUBSCRIBERS", f"{sub_pct}%")

# ── Main Content ──
tab1, tab2, tab3 = st.tabs(["[ 01 ] COHORT DENSITY", "[ 02 ] DRIVER IMPORTANCE", "[ 03 ] SURVIVAL CURVES"])

with tab1:
    st.markdown('<div class="terminal-header">COHORT ATTRITION MAP</div>', unsafe_allow_html=True)
    cohort = compute_cohort_churn(filtered).tail(18)
    
    fig = px.bar(
        cohort, x="cohort", y="churn_rate",
        color="churn_rate",
        color_continuous_scale=["#00f2ff", "#8a2be2", "#ff9d00"],
        labels={"cohort": "COHORT PERIOD", "churn_rate": "CHURN %"},
    )
    fig.update_layout(**PLOTLY_THEME["layout"])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="terminal-header">SEGMENT CHURN BREAKDOWN</div>', unsafe_allow_html=True)
    seg_churn = compute_churn_rate(filtered, by="segment")
    fig2 = px.bar(
        seg_churn, x="segment", y="churn_rate",
        color="segment",
        color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6"],
        labels={"segment": "SEGMENT", "churn_rate": "CHURN %"},
    )
    fig2.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.markdown('<div class="terminal-header">FEATURE IMPORTANCE SCORES</div>', unsafe_allow_html=True)
    drivers = churn_drivers(filtered)
    fig3 = px.bar(
        drivers, x="importance", y="feature", orientation="h",
        color="importance",
        color_continuous_scale=["#00f2ff", "#8a2be2"],
        labels={"importance": "IMPORTANCE SCORE", "feature": "FEATURE"},
    )
    fig3.update_layout(**PLOTLY_THEME["layout"], coloraxis_showscale=False)
    fig3.update_yaxes(autorange="reversed")
    st.plotly_chart(fig3, use_container_width=True)
    st.info("// MODEL: RANDOM FOREST CLASSIFIER // CONFIDENCE: HIGH")

with tab3:
    st.markdown('<div class="terminal-header">KAPLAN MEIER SURVIVAL FUNCTION</div>', unsafe_allow_html=True)
    surv = survival_analysis(filtered)
    fig4 = go.Figure()
    colors = ["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6"]
    for i, (seg_name, kmf) in enumerate(surv["by_segment"].items()):
        tl = kmf.survival_function_
        fig4.add_trace(go.Scatter(
            x=tl.index, y=tl.iloc[:,0], name=seg_name.upper(),
            line=dict(color=colors[i % len(colors)], width=2)
        ))
    fig4.update_layout(**PLOTLY_THEME["layout"])
    fig4.update_xaxes(title="TENURE DAYS")
    fig4.update_yaxes(title="SURVIVAL PROBABILITY")
    st.plotly_chart(fig4, use_container_width=True)

