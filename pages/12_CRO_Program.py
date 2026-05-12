"""
Page 12: CRO Program Dashboard
================================
Experiment registry, cumulative revenue impact, program velocity, and win/loss analytics.
"""

import streamlit as st
import plotly.express as px
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

st.markdown('<div class="terminal-header">PROGRAM // CRO COMMAND CENTER</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">CRO Program Dashboard</h1>', unsafe_allow_html=True)

with st.expander("Concept Playbook: How to use this page"):
    st.markdown('''
    **Overview:** Track your entire CRO program in one place — active experiments, cumulative revenue impact, and program health.
    **How to use:** Add experiments below. The dashboard auto-computes program KPIs. Use the registry to manage your test backlog.
    ''')

if "model" not in st.session_state:
    st.warning("No model defined. Go to **Business Model** to configure your business first.")
    st.stop()

s = st.session_state["model_summary"]
config = st.session_state["model_config"]

from analytics.conversion import program_metrics

# ── Experiment Registry ──
if "cro_experiments" not in st.session_state:
    st.session_state["cro_experiments"] = [
        {
            "id": "EXP-001",
            "name": "Checkout Flow Redesign",
            "hypothesis": "Single-page checkout reduces drop-off vs 3-step flow",
            "status": "completed",
            "winner": "variant",
            "lift_pct": 12.5,
            "monthly_revenue_impact": 4250.00,
            "duration_days": 21,
            "start_date": "2025-01-15",
            "end_date": "2025-02-05",
        },
        {
            "id": "EXP-002",
            "name": "Hero CTA Copy Test",
            "hypothesis": "Benefit-driven CTA outperforms action-driven CTA",
            "status": "completed",
            "winner": "control",
            "lift_pct": -3.2,
            "monthly_revenue_impact": 0,
            "duration_days": 14,
            "start_date": "2025-02-01",
            "end_date": "2025-02-15",
        },
        {
            "id": "EXP-003",
            "name": "Mobile Nav Simplification",
            "hypothesis": "Hamburger menu with fewer items increases mobile CVR",
            "status": "active",
            "winner": None,
            "lift_pct": None,
            "monthly_revenue_impact": None,
            "duration_days": None,
            "start_date": "2025-03-01",
            "end_date": None,
        },
        {
            "id": "EXP-004",
            "name": "PDP Image Gallery Test",
            "hypothesis": "Full-width gallery increases add-to-cart rate",
            "status": "planned",
            "winner": None,
            "lift_pct": None,
            "monthly_revenue_impact": None,
            "duration_days": None,
            "start_date": None,
            "end_date": None,
        },
    ]

experiments = st.session_state["cro_experiments"]
metrics = program_metrics(experiments)

# ── Program KPIs ──
st.markdown('<div class="terminal-header">PROGRAM HEALTH</div>', unsafe_allow_html=True)
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("TOTAL TESTS", metrics["total_experiments"])
k2.metric("ACTIVE", metrics["active"])
k3.metric("COMPLETED", metrics["completed"])
k4.metric("WIN RATE", f"{metrics['win_rate_pct']:.1f}%")
k5.metric("AVG LIFT", f"{metrics['avg_lift_pct']:+.2f}%")
k6.metric("CUMULATIVE REVENUE", f"${metrics['cumulative_monthly_revenue_impact']:,.2f}/mo")

# ── Cumulative Revenue Impact ──
st.markdown('<div class="terminal-header" style="margin-top: 1.5rem;">CUMULATIVE REVENUE IMPACT</div>', unsafe_allow_html=True)
won_experiments = [e for e in experiments if e.get("winner") == "variant" and e.get("monthly_revenue_impact", 0) > 0]
if won_experiments:
    won_df = pd.DataFrame(won_experiments)
    won_df["cumulative"] = won_df["monthly_revenue_impact"].cumsum()
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Bar(
        x=won_df["name"], y=won_df["monthly_revenue_impact"],
        name="Per Test", marker_color="#14b8a6",
        text=[f"${v:,.0f}" for v in won_df["monthly_revenue_impact"]],
        textposition="outside",
    ))
    fig_cum.add_trace(go.Scatter(
        x=won_df["name"], y=won_df["cumulative"],
        name="Cumulative", mode="lines+markers",
        line=dict(color="#00f2ff", width=3),
        marker=dict(size=8),
    ))
    fig_cum.update_layout(**PLOTLY_THEME["layout"], showlegend=True)
    fig_cum.update_yaxes(title="MONTHLY REVENUE ($)")
    st.plotly_chart(fig_cum, use_container_width=True)
else:
    st.info("No winning experiments with revenue impact yet. Ship a winner to see cumulative impact.")

# ── Win/Loss Distribution ──
st.markdown('<div class="terminal-header" style="margin-top: 1.5rem;">WIN / LOSS DISTRIBUTION</div>', unsafe_allow_html=True)
completed = [e for e in experiments if e.get("status") == "completed"]
if completed:
    outcomes = []
    for e in completed:
        if e.get("winner") == "variant":
            outcomes.append("Win" if (e.get("lift_pct") or 0) > 0 else "Loss")
        else:
            outcomes.append("Loss")
    outcome_counts = pd.Series(outcomes).value_counts()
    fig_pie = px.pie(
        values=outcome_counts.values,
        names=outcome_counts.index,
        color=outcome_counts.index,
        color_discrete_map={"Win": "#14b8a6", "Loss": "#f43f5e"},
    )
    fig_pie.update_layout(**PLOTLY_THEME["layout"])
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Experiment Registry Table ──
st.markdown('<div class="terminal-header" style="margin-top: 1.5rem;">EXPERIMENT REGISTRY</div>', unsafe_allow_html=True)
registry_data = []
for e in experiments:
    registry_data.append({
        "ID": e["id"],
        "Name": e["name"],
        "Status": e["status"].upper(),
        "Winner": e.get("winner", "—").title() if e.get("winner") else "—",
        "Lift %": f"{e['lift_pct']:+.1f}%" if e.get("lift_pct") is not None else "—",
        "Revenue/mo": f"${e['monthly_revenue_impact']:,.0f}" if e.get("monthly_revenue_impact") else "—",
        "Duration": f"{e['duration_days']}d" if e.get("duration_days") else "—",
    })
registry_df = pd.DataFrame(registry_data)
st.dataframe(registry_df, use_container_width=True, hide_index=True)

# ── Add Experiment ──
st.markdown('<div class="terminal-header" style="margin-top: 1.5rem;">ADD EXPERIMENT</div>', unsafe_allow_html=True)
with st.form("add_experiment"):
    ac1, ac2 = st.columns(2)
    with ac1:
        new_name = st.text_input("Experiment Name", placeholder="e.g. Pricing Page A/B Test")
        new_hypothesis = st.text_input("Hypothesis", placeholder="e.g. Showing annual pricing first increases conversion")
    with ac2:
        new_status = st.selectbox("Status", ["planned", "active", "completed"])
        new_winner = st.selectbox("Winner (if completed)", ["—", "variant", "control"])
    new_lift = st.number_input("Observed Lift % (if completed)", -100.0, 500.0, 0.0, step=0.1)
    new_revenue = st.number_input("Monthly Revenue Impact $ (if winner)", 0.0, 1000000.0, 0.0, step=100.0)
    new_duration = st.number_input("Duration (days)", 1, 365, 14)

    if st.form_submit_button("Add Experiment", type="primary"):
        if new_name:
            new_id = f"EXP-{len(experiments) + 1:03d}"
            st.session_state["cro_experiments"].append({
                "id": new_id,
                "name": new_name,
                "hypothesis": new_hypothesis,
                "status": new_status,
                "winner": None if new_winner == "—" else new_winner,
                "lift_pct": new_lift if new_status == "completed" else None,
                "monthly_revenue_impact": new_revenue if new_winner == "variant" else 0,
                "duration_days": new_duration if new_status == "completed" else None,
                "start_date": "2025-04-01",
                "end_date": "2025-04-15" if new_status == "completed" else None,
            })
            st.rerun()
        else:
            st.error("Experiment name is required.")

st.caption(f"Avg time to decision: {metrics['avg_time_to_decision_days']:.1f} days | Tests completed: {metrics['completed']}")
