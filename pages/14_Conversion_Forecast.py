"""
Page 14: Conversion Revenue Forecaster
========================================
Monte Carlo revenue forecast from a CRO improvement roadmap.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
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

st.markdown('<div class="terminal-header">FORECAST // CRO REVENUE PROJECTION</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Conversion Revenue Forecast</h1>', unsafe_allow_html=True)

with st.expander("Concept Playbook: How to use this page"):
    st.markdown('''
    **Overview:** Project the revenue impact of your CRO roadmap using Monte Carlo simulation.
    **How to use:** Define planned improvements with expected lift, uncertainty, and deployment month. The forecaster simulates 1,000 scenarios and shows median revenue with 80% confidence bands.
    ''')

if "model" not in st.session_state:
    st.warning("No model defined. Go to **Business Model** to configure your business first.")
    st.stop()

s = st.session_state["model_summary"]
config = st.session_state["model_config"]

from analytics.conversion import forecast_cro_revenue

st.markdown('<div class="terminal-header">BASELINE PARAMETERS</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    baseline_cvr = st.number_input("BASELINE CVR (%)", 0.1, 100.0, 3.0, step=0.1, key="fc_base_cvr")
with c2:
    monthly_sessions = st.number_input("MONTHLY SESSIONS", 1000, 10000000, 30000, step=1000, key="fc_sess")
with c3:
    churn_rate = st.number_input("MONTHLY CHURN (%)", 0.5, 40.0, config.get("monthly_churn_rate", 0.08) * 100, step=0.5, key="fc_churn") / 100
with c4:
    n_months = st.slider("FORECAST HORIZON (mo)", 3, 24, 12, key="fc_horizon")

st.markdown('<div class="terminal-header">PLANNED IMPROVEMENTS</div>', unsafe_allow_html=True)
st.caption("Define your CRO roadmap. Each improvement has an expected lift, uncertainty (std dev), and deployment month.")

if "fc_improvements" not in st.session_state:
    st.session_state["fc_improvements"] = [
        {"name": "Checkout Optimization", "cvr_lift_pct": 12.0, "cvr_lift_std": 4.0, "deploy_month": 2},
        {"name": "Mobile CTA Redesign", "cvr_lift_pct": 8.0, "cvr_lift_std": 3.0, "deploy_month": 4},
        {"name": "PDP Image Gallery", "cvr_lift_pct": 5.0, "cvr_lift_std": 2.0, "deploy_month": 6},
    ]

improvements = st.session_state["fc_improvements"]

for i, imp in enumerate(improvements):
    with st.expander(f"{imp['name']}", expanded=(i == 0)):
        c1, c2, c3 = st.columns(3)
        with c1:
            imp["cvr_lift_pct"] = st.number_input(
                "Expected Lift (%)", 0.1, 100.0, imp["cvr_lift_pct"], step=0.5,
                key=f"fc_lift_{i}"
            )
        with c2:
            imp["cvr_lift_std"] = st.number_input(
                "Uncertainty (std %)", 0.1, 50.0, imp["cvr_lift_std"], step=0.5,
                key=f"fc_std_{i}"
            )
        with c3:
            imp["deploy_month"] = st.number_input(
                "Deploy Month", 1, n_months, imp["deploy_month"], step=1,
                key=f"fc_deploy_{i}"
            )

if st.button("Add Improvement", key="fc_add"):
    st.session_state["fc_improvements"].append({
        "name": f"Improvement {len(improvements) + 1}",
        "cvr_lift_pct": 5.0,
        "cvr_lift_std": 2.0,
        "deploy_month": len(improvements) + 1,
    })
    st.rerun()

if st.button("Run Forecast", type="primary", key="fc_run"):
    with st.spinner("Running 1,000 Monte Carlo simulations..."):
        forecast = forecast_cro_revenue(
            baseline_cvr=baseline_cvr,
            planned_improvements=improvements,
            monthly_sessions=monthly_sessions,
            aov=s["aov"],
            gross_margin_pct=s["gross_margin_pct"],
            monthly_churn_rate=churn_rate,
            n_months=n_months,
        )

    st.markdown(f"<h3 style='color: #14b8a6;'>Total Incremental Revenue: ${forecast['total_incremental_revenue']:,.2f}</h3>", unsafe_allow_html=True)

    monthly = forecast["monthly_forecast"]
    months = [m["month"] for m in monthly]
    medians = [m["median_revenue"] for m in monthly]
    lowers = [m["ci_lower"] for m in monthly]
    uppers = [m["ci_upper"] for m in monthly]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=uppers,
        mode="lines", line=dict(width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=months, y=lowers,
        mode="lines", fill="tonexty",
        fillcolor="rgba(0, 242, 255, 0.1)",
        line=dict(width=0),
        name="80% Confidence",
    ))
    fig.add_trace(go.Scatter(
        x=months, y=medians,
        mode="lines+markers",
        line=dict(color="#00f2ff", width=3),
        marker=dict(size=6),
        name="Median Revenue",
    ))
    fig.update_layout(**PLOTLY_THEME["layout"])
    fig.update_xaxes(title="MONTH", tickvals=months)
    fig.update_yaxes(title="INCREMENTAL MONTHLY REVENUE ($)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="terminal-header">IMPROVEMENT CONTRIBUTIONS</div>', unsafe_allow_html=True)
    contribs = forecast["improvement_contributions"]
    contrib_df = pd.DataFrame({
        "Improvement": list(contribs.keys()),
        "Expected Contribution ($)": list(contribs.values()),
    }).sort_values("Expected Contribution ($)", ascending=False)
    st.dataframe(contrib_df, use_container_width=True, hide_index=True)
