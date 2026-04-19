"""
churnOS — Causal Business Intelligence for Retention & Growth
==============================================================
Main entry point. Defines the navigation and the Executive Summary (home page).
"""

import streamlit as st
from pathlib import Path

# ── Page Configuration ──
st.set_page_config(
    page_title="churnOS",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Custom CSS ──
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Sidebar Branding ──
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 1rem 0;">
            <div class="terminal-header">SYSTEM STATUS: ACTIVE</div>
            <h2 style="margin: 0; font-family: 'Outfit';">churnOS</h2>
            <p style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #00f2ff; opacity: 0.8;">
                CAUSAL BUSINESS INTELLIGENCE
            </p>
        </div>
        <hr style="border-color: rgba(255,255,255,0.08); margin: 0.5rem 0 1.5rem;">
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
#  Executive Summary — the Home Page
# ──────────────────────────────────────────────

def executive_summary():
    """Home page: health score, key metrics, waterfall, and sensitivity heatmap."""
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    import numpy as np

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

    st.markdown('<div class="terminal-header">HOME // EXECUTIVE SUMMARY</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="gradient-text" style="font-size:3rem; margin-bottom:0.5rem;">Executive Summary</h1>', unsafe_allow_html=True)

    # ── Check for model ──
    if "model" not in st.session_state:
        st.markdown(
            """
            <div class="techno-card" style="border-top: 2px solid #ff9d00; text-align: center; padding: 3rem;">
                <h3 style="color: #ff9d00; margin-bottom: 1rem;">No Business Model Defined</h3>
                <p style="font-size: 0.95rem;">
                    Navigate to <strong>Business Model</strong> in the sidebar to define your business
                    parameters. churnOS will then compute your full causal chain.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    model = st.session_state["model"]
    s = st.session_state["model_summary"]
    config = st.session_state["model_config"]

    # ── Health Score + Key Metrics ──
    health = s["health_score"]
    health_color = "#14b8a6" if health >= 70 else "#ff9d00" if health >= 40 else "#f43f5e"

    st.markdown(
        f"""
        <div class="techno-card" style="border-top: 3px solid {health_color}; text-align: center; padding: 1.5rem 1rem 0.5rem;">
            <div class="terminal-header" style="border: none; text-align: center;">BUSINESS HEALTH INDEX</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 5rem; font-weight: 800; color: {health_color}; line-height: 1;">
                {health}
            </div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: #94a3b8; margin-top: 0.3rem;">
                / 100 — {config['business_type'].upper()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Key metric cards
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("CLV (24mo)", f"${s['clv_24']:,.2f}")
    m2.metric("BLENDED CAC", f"${s['cac']:,.2f}")
    m3.metric("LTV : CAC", f"{s['ltv_cac']}x")
    payback_label = f"Month {s['payback_month']}" if s['payback_month'] else "Never"
    m4.metric("PAYBACK", payback_label)
    m5.metric("MONTHLY CHURN", f"{s['monthly_churn_eff']}%")
    m6.metric("GROSS MARGIN", f"{s['gross_margin_pct']}%")

    # ── Two-column layout: Waterfall + Cohort Survival ──
    col_left, col_right = st.columns(2)

    # Waterfall chart
    with col_left:
        st.markdown('<div class="terminal-header">REVENUE WATERFALL // PER ORDER</div>', unsafe_allow_html=True)
        waterfall = model.compute_waterfall()

        colors = []
        for _, row in waterfall.iterrows():
            if row["type"] == "absolute":
                colors.append("#00f2ff")
            elif row["type"] == "total":
                colors.append("#14b8a6" if row["amount"] >= 0 else "#f43f5e")
            else:
                colors.append("#f43f5e" if row["amount"] < 0 else "#14b8a6")

        fig_wf = go.Figure(go.Waterfall(
            orientation="v",
            measure=waterfall["type"].tolist(),
            x=waterfall["label"].tolist(),
            y=waterfall["amount"].tolist(),
            connector={"line": {"color": "rgba(255,255,255,0.1)"}},
            decreasing={"marker": {"color": "#f43f5e"}},
            increasing={"marker": {"color": "#14b8a6"}},
            totals={"marker": {"color": "#8a2be2"}},
            textposition="outside",
            text=[f"${abs(v):.2f}" for v in waterfall["amount"]],
        ))
        fig_wf.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
        fig_wf.update_yaxes(title="$ PER ORDER")
        st.plotly_chart(fig_wf, use_container_width=True)

    # Cohort survival curve
    with col_right:
        st.markdown('<div class="terminal-header">COHORT SURVIVAL // 24 MONTH PROJECTION</div>', unsafe_allow_html=True)
        cohort = model.simulate_cohort(n_months=24)

        fig_surv = go.Figure()
        fig_surv.add_trace(go.Scatter(
            x=cohort["month"], y=cohort["active_pct"],
            mode="lines+markers",
            name="Active %",
            line=dict(color="#00f2ff", width=3),
            marker=dict(size=4),
            fill="tozeroy",
            fillcolor="rgba(0, 242, 255, 0.05)",
        ))
        # Add CAC payback line
        if s["payback_month"]:
            fig_surv.add_vline(
                x=s["payback_month"], line_dash="dash",
                line_color="#ff9d00", annotation_text=f"Payback M{s['payback_month']}",
                annotation_font_color="#ff9d00",
            )
        fig_surv.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
        fig_surv.update_xaxes(title="MONTH")
        fig_surv.update_yaxes(title="ACTIVE %", range=[0, 105])
        st.plotly_chart(fig_surv, use_container_width=True)

    # ── Sensitivity Analysis Heatmap ──
    st.markdown('<div class="terminal-header" style="margin-top: 1rem;">SENSITIVITY ANALYSIS // WHAT MATTERS MOST</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.85rem; max-width: 700px; margin-bottom: 1rem;">'
        'Each input is perturbed ±10%. The bars show how much that changes your CLV. '
        'Longer bars = higher leverage. Focus your optimization efforts here.'
        '</p>',
        unsafe_allow_html=True,
    )

    sensitivity = model.compute_sensitivity(output_metric="clv_24", delta_pct=0.10)
    # Top 8 most impactful
    top_sens = sensitivity.head(8)

    fig_sens = go.Figure()
    # Show as tornado: low_output and high_output around base
    base_clv = top_sens["base_output"].iloc[0]
    for _, row in top_sens.iterrows():
        fig_sens.add_trace(go.Bar(
            y=[row["input_name"]],
            x=[row["high_output"] - base_clv],
            name="+10%",
            orientation="h",
            marker_color="#14b8a6",
            showlegend=False,
            text=f"${row['high_output']:.2f}",
            textposition="outside",
        ))
        fig_sens.add_trace(go.Bar(
            y=[row["input_name"]],
            x=[row["low_output"] - base_clv],
            name="-10%",
            orientation="h",
            marker_color="#f43f5e",
            showlegend=False,
            text=f"${row['low_output']:.2f}",
            textposition="outside",
        ))

    fig_sens.update_layout(
        **PLOTLY_THEME["layout"],
        barmode="overlay",
        height=max(350, len(top_sens) * 50),
    )
    fig_sens.update_xaxes(title="CLV CHANGE FROM BASELINE ($)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)")
    fig_sens.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_sens, use_container_width=True)

    # ── Segment Comparison ──
    st.markdown('<div class="terminal-header" style="margin-top: 1rem;">SEGMENT BREAKDOWN // BY-SEGMENT ECONOMICS</div>', unsafe_allow_html=True)
    seg_cohort = model.simulate_cohort_by_segment(n_months=24)

    # Survival by segment
    seg_col1, seg_col2 = st.columns(2)
    with seg_col1:
        fig_seg = go.Figure()
        seg_colors = {"Budget": "#f43f5e", "Mid-Range": "#ff9d00", "Premium": "#8a2be2", "Enterprise": "#14b8a6"}
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

    # CLV by segment at M24
    with seg_col2:
        seg_24 = seg_cohort[seg_cohort["month"] == 24][["segment", "ltv_to_date", "active_pct"]].copy()
        seg_24.columns = ["Segment", "CLV (24mo)", "Retention %"]
        fig_clv_seg = px.bar(
            seg_24, x="Segment", y="CLV (24mo)",
            color="Segment",
            color_discrete_map=seg_colors,
            text_auto=".2f",
        )
        fig_clv_seg.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
        fig_clv_seg.update_yaxes(title="CLV ($)")
        st.plotly_chart(fig_clv_seg, use_container_width=True)

    # ── Footer ──
    st.markdown("---")
    unit_econ_cols = st.columns(4)
    unit_econ_cols[0].metric("NET REV / ORDER", f"${s['net_revenue_per_order']:,.2f}")
    unit_econ_cols[1].metric("MARGIN / ACTIVE / MO", f"${s['margin_per_active_monthly']:,.2f}")
    unit_econ_cols[2].metric("AOV", f"${s['aov']:,.2f}")
    unit_econ_cols[3].metric("PURCHASE FREQ", f"{s['purchase_frequency']}x / mo")


# ──────────────────────────────────────────────
#  Navigation
# ──────────────────────────────────────────────

# Build page list — conditionally include marketplace/conversion
pages = [
    st.Page("pages/0_Business_Model.py", title="Business Model"),
    st.Page(executive_summary, title="Executive Summary"),
    st.Page("pages/1_Retention_Churn.py", title="Retention & Churn"),
    st.Page("pages/2_Unit_Economics.py", title="Unit Economics"),
    st.Page("pages/3_Conversion.py", title="Conversion & Funnel"),
    st.Page("pages/4_Marketplace.py", title="Marketplace"),
    st.Page("pages/5_Marketplace_Analytics.py", title="Marketplace Analytics"),
]

pg = st.navigation(pages)
pg.run()
