"""
Page 3: Conversion & Funnel
=============================
Funnel breakdown, A/B testing, and causal-model-connected conversion impact.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
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

st.markdown('<div class="terminal-header">DEEP DIVE // CONVERSION & FUNNEL</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Conversion & Funnel</h1>', unsafe_allow_html=True)

if "model" not in st.session_state:
    st.warning("No model defined. Go to **Business Model** to configure your business first.")
    st.stop()

model = st.session_state["model"]
s = st.session_state["model_summary"]
config = st.session_state["model_config"]

# ── Generate funnel data (using existing generator — kept for conversion analysis) ──
from data.generator import generate_funnel_events
from analytics.conversion import funnel_summary, segment_conversion, ab_test_significance

# Funnel simulation controls
st.markdown('<div class="terminal-header">FUNNEL SIMULATION</div>', unsafe_allow_html=True)
col_a, col_b, col_c, col_d, col_e = st.columns(5)
with col_a:
    new_sess = st.number_input("SESSIONS", 5000, 100000, 30000, step=5000, key="conv_sess")
with col_b:
    new_dropoff = st.slider("CHECKOUT DROPOFF", 0.5, 2.0, 1.0, 0.1, key="conv_dropoff")
with col_c:
    new_mobile = st.slider("MOBILE SHARE", 0.1, 0.9, 0.48, 0.05, key="conv_mobile")
with col_d:
    st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True)
    new_fs = st.toggle("FREE SHIPPING", value=False, key="conv_fs")
with col_e:
    st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True)
    regen = st.button("Calculate", type="primary", key="conv_regen")

# Cache or regenerate funnel data
if regen or "funnel_data" not in st.session_state:
    st.session_state["funnel_data"] = generate_funnel_events(
        n_sessions=new_sess,
        checkout_dropoff_modifier=new_dropoff,
        mobile_share=new_mobile,
        free_shipping=new_fs,
    )

funnel_df = st.session_state["funnel_data"]
summary = funnel_summary(funnel_df)

# ── KPIs ──
total_s = summary.loc[summary["step"] == "Visit", "sessions"].iloc[0]
total_p = summary.loc[summary["step"] == "Purchase", "sessions"].iloc[0]
cvr = total_p / total_s * 100 if total_s > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("SESSIONS", f"{total_s:,}")
c2.metric("PURCHASES", f"{total_p:,}")
c3.metric("OVERALL CVR", f"{cvr:.2f}%")
c4.metric("CART ADD RATE", f"{summary.loc[summary['step'] == 'Add to Cart', 'conversion_rate'].iloc[0]}%")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["[ 01 ] FUNNEL", "[ 02 ] SEGMENT MAP", "[ 03 ] CVR → CLV IMPACT"])

with tab1:
    st.markdown('<div class="terminal-header">VISUAL FUNNEL BREAKDOWN</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Funnel(
        y=summary["step"], x=summary["sessions"],
        textinfo="value+percent initial",
        marker=dict(color=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6", "#f43f5e"]),
    ))
    fig.update_layout(**PLOTLY_THEME["layout"])
    st.plotly_chart(fig, use_container_width=True)

    # Drop-off analysis
    st.markdown('<div class="terminal-header">DROP-OFF ANALYSIS</div>', unsafe_allow_html=True)
    dropoff = summary[summary["drop_off_pct"] > 0].copy()
    fig_drop = px.bar(
        dropoff, x="step", y="drop_off_pct",
        color="drop_off_pct",
        color_continuous_scale=["#14b8a6", "#ff9d00", "#f43f5e"],
        labels={"step": "FUNNEL STEP", "drop_off_pct": "DROP-OFF %"},
    )
    fig_drop.update_layout(**PLOTLY_THEME["layout"], coloraxis_showscale=False)
    st.plotly_chart(fig_drop, use_container_width=True)

with tab2:
    st.markdown('<div class="terminal-header">CVR BY DEVICE CLASS</div>', unsafe_allow_html=True)
    dev_conv = segment_conversion(funnel_df, by="device")
    fig2 = px.bar(
        dev_conv, x="device", y="conversion_rate",
        color="device",
        color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00"],
        labels={"device": "DEVICE", "conversion_rate": "CONVERSION RATE"},
    )
    fig2.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="terminal-header">CVR BY SOURCE</div>', unsafe_allow_html=True)
    src_conv = segment_conversion(funnel_df, by="source")
    fig3 = px.bar(
        src_conv, x="source", y="conversion_rate",
        color="source",
        color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6", "#f43f5e"],
        labels={"source": "SOURCE", "conversion_rate": "CONVERSION RATE"},
    )
    fig3.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.markdown('<div class="terminal-header">CONVERSION RATE → REVENUE IMPACT</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 1rem;">'
        'If you improve a funnel step, how does that impact total cohort revenue? '
        'This connects your funnel optimization directly to the causal business model.'
        '</p>',
        unsafe_allow_html=True,
    )

    step_to_improve = st.selectbox("Funnel Step to Improve", ["Product View", "Add to Cart", "Checkout", "Purchase"], key="conv_step")
    improvement_pct = st.slider("Improvement (%)", 1, 50, 10, step=1, key="conv_improve")

    # Calculate impact: improvement in this step means more purchases
    # which means more customers acquired from the same traffic
    baseline_cvr = cvr / 100.0
    step_data = summary[summary["step"] == step_to_improve]
    if len(step_data) > 0:
        step_rate = step_data["conversion_rate"].iloc[0] / 100.0
        improved_rate = step_rate * (1 + improvement_pct / 100.0)
        # Proportional impact on final CVR
        if step_rate > 0:
            cvr_ratio = improved_rate / step_rate
            new_cvr = baseline_cvr * cvr_ratio
        else:
            new_cvr = baseline_cvr

        additional_customers = int(new_sess * (new_cvr - baseline_cvr))
        additional_monthly_rev = additional_customers * s["margin_per_active_monthly"]
        additional_24mo_value = additional_customers * s["clv_24"]

        imp_cols = st.columns(4)
        imp_cols[0].metric("NEW CVR", f"{new_cvr * 100:.2f}%", f"+{(new_cvr - baseline_cvr) * 100:.2f}%")
        imp_cols[1].metric("ADDITIONAL CUSTOMERS", f"{additional_customers:,}")
        imp_cols[2].metric("MONTHLY MARGIN GAIN", f"${additional_monthly_rev:,.2f}")
        imp_cols[3].metric("24mo VALUE", f"${additional_24mo_value:,.2f}")

    # A/B test engine
    st.markdown('<div class="terminal-header" style="margin-top: 2rem;">A/B TEST SIGNIFICANCE CALCULATOR</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        cv = st.number_input("CONTROL VISITORS", 1000, 100000, 10000, key="ab_cv")
        cc = st.number_input("CONTROL CONVERSIONS", 10, 10000, 350, key="ab_cc")
    with col_b:
        vv = st.number_input("VARIANT VISITORS", 1000, 100000, 10000, key="ab_vv")
        vc = st.number_input("VARIANT CONVERSIONS", 10, 10000, 420, key="ab_vc")
    if st.button("RUN SIGNIFICANCE TEST", type="primary", key="ab_run"):
        res = ab_test_significance(cv, cc, vv, vc)
        res_cols = st.columns(3)
        res_cols[0].metric("LIFT", f"{res['lift_pct']:+.2f}%")
        res_cols[1].metric("P-VALUE", f"{res['p_value']:.4f}")
        if res["is_significant"]:
            res_cols[2].success("✓ STATISTICALLY SIGNIFICANT")
        else:
            res_cols[2].warning("✗ NOT SIGNIFICANT")
