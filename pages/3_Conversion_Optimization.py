"""
Page 3: Conversion Optimization
================================
Funnel resolution and experimental benchmarking.
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

st.markdown('<div class="terminal-header">ANALYTICS UNIT // CONVERSION FUNNEL</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Conversion Optimization</h1>', unsafe_allow_html=True)

# ── Data Load ──
if "app_data" not in st.session_state:
    from data.generator import generate_all_data
    st.session_state["app_data"] = generate_all_data()

data = st.session_state["app_data"]
funnel_df = data["funnel"]

from analytics.conversion import funnel_summary, segment_conversion, ab_test_significance

# ── Simulation Controls ──
col_a, col_b, col_c, col_d, col_e = st.columns(5)
with col_a:
    new_sess = st.number_input("N SESSIONS", 5000, 100000, 30000, step=5000)
with col_b:
    new_dropoff = st.slider("CHECKOUT DROPOFF", 0.5, 2.0, 1.0, 0.1)
with col_c:
    new_mobile = st.slider("MOBILE SHARE", 0.1, 0.9, 0.48, 0.05)
with col_d:
    st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True)
    new_fs = st.toggle("FREE SHIPPING", value=False)
with col_e:
    st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True)
    if st.button("Calculate", type="primary", key="regen_conv"):
        from data.generator import generate_funnel_events
        st.session_state["app_data"]["funnel"] = generate_funnel_events(
            n_sessions=new_sess, 
            checkout_dropoff_modifier=new_dropoff, 
            mobile_share=new_mobile,
            free_shipping=new_fs
        )
        st.rerun()

# ── Sidebar ──
with st.sidebar:
    st.markdown('<div class="terminal-header">FILTERS</div>', unsafe_allow_html=True)
    sel_dev = st.multiselect("Device", funnel_df["device"].unique().tolist(), default=funnel_df["device"].unique().tolist(), key="conv_dev_2")

filtered = funnel_df[funnel_df["device"].isin(sel_dev)]
summary = funnel_summary(filtered)

# ── KPI Row ──
c1, c2, c3, c4 = st.columns(4)
total_s = summary.loc[summary["step"]=="Visit", "sessions"].iloc[0]
total_p = summary.loc[summary["step"]=="Purchase", "sessions"].iloc[0]
c1.metric("SESSION TOTAL", f"{total_s:,}")
c2.metric("PURCHASE COUNT", f"{total_p:,}")
c3.metric("OVERALL CVR", f"{(total_p/total_s*100):.2f}%")
c4.metric("CART ADD RATE", f"{summary.loc[summary['step']=='Add to Cart', 'conversion_rate'].iloc[0]}%")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["[ 01 ] FUNNEL VISUAL", "[ 02 ] SEGMENT MAP", "[ 03 ] AB TEST ENGINE"])

with tab1:
    st.markdown('<div class="terminal-header">VISUAL FUNNEL BREAKDOWN</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Funnel(y=summary["step"], x=summary["sessions"], textinfo="value+percent initial",
        marker=dict(color=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6", "#f43f5e"])))
    fig.update_layout(**PLOTLY_THEME["layout"])
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown('<div class="terminal-header">CVR BY DEVICE CLASS</div>', unsafe_allow_html=True)
    dev_conv = segment_conversion(filtered, by="device")
    fig2 = px.bar(dev_conv, x="device", y="conversion_rate", color="device", color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00"], labels={"device": "DEVICE", "conversion_rate": "CONVERSION RATE"})
    fig2.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.markdown('<div class="terminal-header">STATISTICAL SIGNIFICANCE CALC</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        cv = st.number_input("CTRL VISITORS", 1000, 100000, 10000, key="ab_cv_2")
        cc = st.number_input("CTRL CONV", 100, 10000, 350, key="ab_cc_2")
    with col_b:
        vv = st.number_input("VAR VISITORS", 1000, 100000, 10000, key="ab_vv_2")
        vc = st.number_input("VAR CONV", 100, 10000, 420, key="ab_vc_2")
    if st.button("RUN SIGNIFICANCE TEST", type="primary"):
        res = ab_test_significance(cv, cc, vv, vc)
        st.write(f"// LIFT: {res['lift_pct']:+.2f}% // P VALUE: {res['p_value']:.4f}")
        if res["is_significant"]: st.success("SIGNIFICANT SUCCESS")
        else: st.warning("NO SIGNIFICANT DIFF")

