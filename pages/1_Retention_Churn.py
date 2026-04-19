"""
Page 1: Retention & Churn
==========================
Deep-dive into the shape of your retention curve and what bends it.
Reads from the shared causal model instead of regenerating data.
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

st.markdown('<div class="terminal-header">DEEP DIVE // RETENTION & CHURN</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Retention & Churn</h1>', unsafe_allow_html=True)

# ── Check for model ──
if "model" not in st.session_state:
    st.warning("No model defined. Go to **Business Model** to configure your business first.")
    st.stop()

model = st.session_state["model"]
s = st.session_state["model_summary"]
config = st.session_state["model_config"]

# ── KPI Row ──
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("MONTHLY CHURN", f"{s['monthly_churn_eff']}%")
k2.metric("ANNUAL CHURN", f"{s['annual_churn']}%")
k3.metric("M1 RETENTION", f"{s['m1_retention']}%")
k4.metric("CLV (24mo)", f"${s['clv_24']:,.2f}")
k5.metric("LTV : CAC", f"{s['ltv_cac']}x")

# ── What-If Scenario Bar ──
st.markdown('<div class="terminal-header" style="margin-top: 1.5rem;">WHAT-IF SCENARIO // CHANGE ONE VARIABLE</div>', unsafe_allow_html=True)
st.markdown(
    '<p style="font-size: 0.82rem; margin-bottom: 0.8rem; color: #94a3b8;">'
    'Adjust a single lever and see how it impacts CLV and retention. '
    'The model re-propagates the full causal chain in real-time.'
    '</p>',
    unsafe_allow_html=True,
)

wi_col1, wi_col2, wi_col3 = st.columns(3)
with wi_col1:
    wi_churn = st.slider(
        "Monthly Churn Rate (%)",
        0.5, 40.0,
        float(config["monthly_churn_rate"] * 100),
        step=0.5,
        key="wi_churn",
    )
with wi_col2:
    wi_sub = st.slider(
        "Subscribe & Save (%)",
        0, 100,
        int(config["subscribe_save_pct"] * 100),
        step=5,
        key="wi_sub",
    )
with wi_col3:
    wi_reactivation = st.slider(
        "Reactivation Rate (%)",
        0.0, 20.0,
        float(config["reactivation_rate"] * 100),
        step=0.5,
        key="wi_react",
    )

# Build what-if model
from analytics.causal_model import BusinessModel
wi_config = dict(config)
wi_config["monthly_churn_rate"] = wi_churn / 100.0
wi_config["subscribe_save_pct"] = wi_sub / 100.0
wi_config["reactivation_rate"] = wi_reactivation / 100.0
wi_model = BusinessModel(wi_config)
wi_summary = wi_model.compute_summary()

# Show deltas
d1, d2, d3, d4 = st.columns(4)
clv_delta = wi_summary["clv_24"] - s["clv_24"]
d1.metric("CLV (24mo) — Scenario", f"${wi_summary['clv_24']:,.2f}", f"${clv_delta:+,.2f}")
ltv_cac_delta = wi_summary["ltv_cac"] - s["ltv_cac"]
d2.metric("LTV:CAC — Scenario", f"{wi_summary['ltv_cac']}x", f"{ltv_cac_delta:+.2f}x")
payback_label = f"M{wi_summary['payback_month']}" if wi_summary['payback_month'] else "Never"
d3.metric("Payback — Scenario", payback_label)
health_delta = wi_summary["health_score"] - s["health_score"]
d4.metric("Health — Scenario", f"{wi_summary['health_score']}/100", f"{health_delta:+d}")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["[ 01 ] SURVIVAL CURVES", "[ 02 ] SEGMENT COMPARISON", "[ 03 ] CHURN SENSITIVITY"])

with tab1:
    st.markdown('<div class="terminal-header">COHORT SURVIVAL // BASE vs SCENARIO</div>', unsafe_allow_html=True)
    base_cohort = model.simulate_cohort(n_months=24)
    wi_cohort = wi_model.simulate_cohort(n_months=24)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=base_cohort["month"], y=base_cohort["active_pct"],
        name="BASELINE",
        line=dict(color="#00f2ff", width=3),
        fill="tozeroy",
        fillcolor="rgba(0, 242, 255, 0.05)",
    ))
    fig.add_trace(go.Scatter(
        x=wi_cohort["month"], y=wi_cohort["active_pct"],
        name="SCENARIO",
        line=dict(color="#8a2be2", width=3, dash="dash"),
        fill="tozeroy",
        fillcolor="rgba(138, 43, 226, 0.05)",
    ))
    fig.update_layout(**PLOTLY_THEME["layout"])
    fig.update_xaxes(title="MONTH")
    fig.update_yaxes(title="ACTIVE CUSTOMERS %", range=[0, 105])
    st.plotly_chart(fig, use_container_width=True)

    # Cumulative margin comparison
    st.markdown('<div class="terminal-header">CUMULATIVE MARGIN PER USER // BASE vs SCENARIO</div>', unsafe_allow_html=True)
    fig_margin = go.Figure()
    n_base = config["cohort_size"]
    fig_margin.add_trace(go.Scatter(
        x=base_cohort["month"],
        y=base_cohort["ltv_to_date"],
        name="BASELINE CLV",
        line=dict(color="#00f2ff", width=2),
    ))
    fig_margin.add_trace(go.Scatter(
        x=wi_cohort["month"],
        y=wi_cohort["ltv_to_date"],
        name="SCENARIO CLV",
        line=dict(color="#8a2be2", width=2, dash="dash"),
    ))
    # CAC line
    fig_margin.add_hline(
        y=s["cac"], line_dash="dot", line_color="#ff9d00",
        annotation_text=f"CAC ${s['cac']:.2f}",
        annotation_font_color="#ff9d00",
    )
    fig_margin.update_layout(**PLOTLY_THEME["layout"])
    fig_margin.update_xaxes(title="MONTH")
    fig_margin.update_yaxes(title="CUMULATIVE CLV ($)")
    st.plotly_chart(fig_margin, use_container_width=True)

with tab2:
    st.markdown('<div class="terminal-header">SEGMENT SURVIVAL CURVES</div>', unsafe_allow_html=True)
    seg_cohort = model.simulate_cohort_by_segment(n_months=24)
    seg_colors = {"Budget": "#f43f5e", "Mid-Range": "#ff9d00", "Premium": "#8a2be2", "Enterprise": "#14b8a6"}

    fig_seg = go.Figure()
    for seg_name in seg_cohort["segment"].unique():
        seg_data = seg_cohort[seg_cohort["segment"] == seg_name]
        fig_seg.add_trace(go.Scatter(
            x=seg_data["month"], y=seg_data["active_pct"],
            name=seg_name.upper(),
            line=dict(color=seg_colors.get(seg_name, "#00f2ff"), width=2),
        ))
    fig_seg.update_layout(**PLOTLY_THEME["layout"])
    fig_seg.update_xaxes(title="MONTH")
    fig_seg.update_yaxes(title="RETENTION %", range=[0, 105])
    st.plotly_chart(fig_seg, use_container_width=True)

    # Churn decomposition: logo vs revenue
    st.markdown('<div class="terminal-header">CHURN DECOMPOSITION // LOGO vs REVENUE</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.82rem; color: #94a3b8;">'
        '"Logo churn" counts customers lost. "Revenue churn" weights by spend. '
        'When high-value segments churn less, revenue churn < logo churn — a good sign.'
        '</p>',
        unsafe_allow_html=True,
    )
    # Compute segment-level M12 data
    seg_m12 = seg_cohort[seg_cohort["month"] == 12][["segment", "active_pct", "active"]].copy()
    seg_m0 = seg_cohort[seg_cohort["month"] == 0][["segment", "active"]].copy()
    seg_m0.columns = ["segment", "initial"]
    decomp = seg_m12.merge(seg_m0, on="segment")
    decomp["churned"] = decomp["initial"] - decomp["active"]
    decomp["logo_churn_pct"] = ((decomp["churned"] / decomp["initial"]) * 100).round(1)

    fig_decomp = px.bar(
        decomp, x="segment", y=["active", "churned"],
        color_discrete_sequence=["#14b8a6", "#f43f5e"],
        labels={"value": "CUSTOMERS", "segment": "SEGMENT"},
        barmode="stack",
    )
    fig_decomp.update_layout(**PLOTLY_THEME["layout"])
    st.plotly_chart(fig_decomp, use_container_width=True)

with tab3:
    st.markdown('<div class="terminal-header">CHURN SENSITIVITY // IMPACT ON CLV</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.82rem; color: #94a3b8;">'
        'Which variables have the most leverage over your CLV? '
        'Inputs are perturbed ±10% and the resulting CLV change is shown.'
        '</p>',
        unsafe_allow_html=True,
    )

    # Filter sensitivity to retention-related inputs
    sens = model.compute_sensitivity("clv_24", delta_pct=0.10)
    retention_keys = [
        "monthly_churn_rate", "subscribe_save_pct", "reactivation_rate",
        "aov", "purchase_frequency", "refund_rate",
    ]
    retention_sens = sens[sens["input_key"].isin(retention_keys)].copy()

    fig_tornado = go.Figure()
    base_clv = retention_sens["base_output"].iloc[0] if len(retention_sens) > 0 else 0
    for _, row in retention_sens.iterrows():
        fig_tornado.add_trace(go.Bar(
            y=[row["input_name"]],
            x=[row["high_output"] - base_clv],
            orientation="h",
            marker_color="#14b8a6",
            showlegend=False,
            text=f"${row['high_output']:.2f}",
            textposition="outside",
        ))
        fig_tornado.add_trace(go.Bar(
            y=[row["input_name"]],
            x=[row["low_output"] - base_clv],
            orientation="h",
            marker_color="#f43f5e",
            showlegend=False,
            text=f"${row['low_output']:.2f}",
            textposition="outside",
        ))
    fig_tornado.update_layout(
        **PLOTLY_THEME["layout"],
        barmode="overlay",
        height=max(300, len(retention_sens) * 55),
    )
    fig_tornado.update_xaxes(title="CLV CHANGE ($)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)")
    fig_tornado.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_tornado, use_container_width=True)

    # Elasticity table
    st.markdown('<div class="terminal-header">ELASTICITY TABLE</div>', unsafe_allow_html=True)
    display_sens = retention_sens[["input_name", "base_value", "low_output", "high_output", "swing", "elasticity"]].copy()
    display_sens.columns = ["Variable", "Current Value", "CLV at -10%", "CLV at +10%", "Total Swing ($)", "Elasticity"]
    st.dataframe(display_sens, use_container_width=True, hide_index=True)
