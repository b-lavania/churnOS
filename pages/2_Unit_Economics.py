"""
Page 2: Unit Economics
========================
Is each customer profitable, and when?
Payback curves, CLV distribution, marginal P&L, CAC ceiling.
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

st.markdown('<div class="terminal-header">DEEP DIVE // UNIT ECONOMICS</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Unit Economics</h1>', unsafe_allow_html=True)

if "model" not in st.session_state:
    st.warning("No model defined. Go to **Business Model** to configure your business first.")
    st.stop()

model = st.session_state["model"]
s = st.session_state["model_summary"]
config = st.session_state["model_config"]

from analytics.causal_model import BusinessModel

# ── KPI Row ──
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("NET REV / ORDER", f"${s['net_revenue_per_order']:,.2f}")
k2.metric("MARGIN / USER / MO", f"${s['margin_per_active_monthly']:,.2f}")
k3.metric("GROSS MARGIN %", f"{s['gross_margin_pct']}%")
payback_str = f"Month {s['payback_month']}" if s['payback_month'] else "Never"
k4.metric("PAYBACK MONTH", payback_str)
k5.metric("CLV (24mo)", f"${s['clv_24']:,.2f}")
cac_ceil = model.cac_ceiling(target_ltv_cac=3.0, horizon_months=24)
k6.metric("CAC CEILING (3x)", f"${cac_ceil:,.2f}")

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs([
    "[ 01 ] PAYBACK CURVE",
    "[ 02 ] P&L WATERFALL",
    "[ 03 ] SEGMENT CLV",
    "[ 04 ] CAC CEILING",
])

with tab1:
    st.markdown('<div class="terminal-header">PAYBACK CURVE // WHEN DOES THE CUSTOMER PAY FOR ITSELF?</div>', unsafe_allow_html=True)
    cohort = model.simulate_cohort(n_months=36)

    fig_pb = go.Figure()
    # CLV accumulation line
    fig_pb.add_trace(go.Scatter(
        x=cohort["month"], y=cohort["ltv_to_date"],
        name="CUMULATIVE CLV",
        line=dict(color="#00f2ff", width=3),
        fill="tozeroy",
        fillcolor="rgba(0, 242, 255, 0.08)",
    ))
    # CAC line
    fig_pb.add_hline(
        y=s["cac"], line_dash="dot", line_color="#f43f5e",
        annotation_text=f"CAC = ${s['cac']:.2f}",
        annotation_font_color="#f43f5e",
    )
    # Breakeven marker
    if s["payback_month"]:
        fig_pb.add_vline(
            x=s["payback_month"], line_dash="dash", line_color="#14b8a6",
            annotation_text=f"Break-even at M{s['payback_month']}",
            annotation_font_color="#14b8a6",
        )
        # Shade the payback period
        fig_pb.add_vrect(
            x0=0, x1=s["payback_month"],
            fillcolor="rgba(244, 63, 94, 0.05)",
            line_width=0,
            annotation_text="CAC RECOVERY",
            annotation_font_color="#f43f5e",
            annotation_position="top left",
        )
    fig_pb.update_layout(**PLOTLY_THEME["layout"], showlegend=True)
    fig_pb.update_xaxes(title="MONTH")
    fig_pb.update_yaxes(title="CUMULATIVE CLV ($)")
    st.plotly_chart(fig_pb, use_container_width=True)

    # LTV:CAC ratio over time
    st.markdown('<div class="terminal-header">LTV:CAC RATIO OVER TIME</div>', unsafe_allow_html=True)
    fig_ratio = go.Figure()
    fig_ratio.add_trace(go.Scatter(
        x=cohort["month"], y=cohort["ltv_cac_ratio"],
        line=dict(color="#8a2be2", width=3),
        fill="tozeroy",
        fillcolor="rgba(138, 43, 226, 0.08)",
    ))
    fig_ratio.add_hline(y=3.0, line_dash="dash", line_color="#14b8a6",
                        annotation_text="3x TARGET", annotation_font_color="#14b8a6")
    fig_ratio.add_hline(y=1.0, line_dash="dot", line_color="#f43f5e",
                        annotation_text="BREAK-EVEN", annotation_font_color="#f43f5e")
    fig_ratio.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
    fig_ratio.update_xaxes(title="MONTH")
    fig_ratio.update_yaxes(title="LTV : CAC RATIO")
    st.plotly_chart(fig_ratio, use_container_width=True)

with tab2:
    st.markdown('<div class="terminal-header">MARGINAL UNIT ECONOMICS // PER-ORDER P&L</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.82rem; color: #94a3b8;">'
        'Revenue decomposition per order. Every dollar that enters gets allocated across costs.'
        '</p>',
        unsafe_allow_html=True,
    )

    waterfall = model.compute_waterfall()
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
    fig_wf.update_layout(**PLOTLY_THEME["layout"], showlegend=False, height=500)
    fig_wf.update_yaxes(title="$ PER ORDER")
    st.plotly_chart(fig_wf, use_container_width=True)

    # Detailed P&L table
    st.markdown('<div class="terminal-header">DETAILED P&L TABLE</div>', unsafe_allow_html=True)
    aov = config["aov"]
    pnl_data = {
        "Line Item": [
            "Gross Revenue (AOV)",
            "  COGS",
            "  Shipping",
            "  Refund Loss",
            "  Discount Loss",
            "Net Revenue per Order",
            "Monthly Margin per Active User",
            "CAC (Blended)",
        ],
        "$ Amount": [
            f"${aov:.2f}",
            f"-${aov * config['cogs_pct']:.2f}",
            f"-${config['shipping_cost']:.2f}",
            f"-${aov * config['refund_rate']:.2f}",
            f"-${aov * config['discount_frequency'] * config['discount_depth']:.2f}",
            f"${s['net_revenue_per_order']:.2f}",
            f"${s['margin_per_active_monthly']:.2f}",
            f"${s['cac']:.2f}",
        ],
        "% of AOV": [
            "100%",
            f"{config['cogs_pct'] * 100:.0f}%",
            f"{config['shipping_cost'] / aov * 100:.1f}%" if aov > 0 else "0%",
            f"{config['refund_rate'] * 100:.0f}%",
            f"{config['discount_frequency'] * config['discount_depth'] * 100:.1f}%",
            f"{s['gross_margin_pct']:.1f}%",
            "—",
            "—",
        ],
    }
    st.dataframe(pd.DataFrame(pnl_data), use_container_width=True, hide_index=True)

with tab3:
    st.markdown('<div class="terminal-header">CLV BY SEGMENT // 24 MONTH HORIZON</div>', unsafe_allow_html=True)
    seg_cohort = model.simulate_cohort_by_segment(n_months=24)
    seg_colors = {"Budget": "#f43f5e", "Mid-Range": "#ff9d00", "Premium": "#8a2be2", "Enterprise": "#14b8a6"}

    # CLV accumulation by segment
    fig_seg_clv = go.Figure()
    for seg_name in seg_cohort["segment"].unique():
        seg_data = seg_cohort[seg_cohort["segment"] == seg_name]
        fig_seg_clv.add_trace(go.Scatter(
            x=seg_data["month"], y=seg_data["ltv_to_date"],
            name=seg_name.upper(),
            line=dict(color=seg_colors.get(seg_name, "#00f2ff"), width=2),
        ))
    fig_seg_clv.add_hline(y=s["cac"], line_dash="dot", line_color="#ff9d00",
                          annotation_text=f"CAC ${s['cac']:.2f}",
                          annotation_font_color="#ff9d00")
    fig_seg_clv.update_layout(**PLOTLY_THEME["layout"])
    fig_seg_clv.update_xaxes(title="MONTH")
    fig_seg_clv.update_yaxes(title="CUMULATIVE CLV ($)")
    st.plotly_chart(fig_seg_clv, use_container_width=True)

    # Summary table
    seg_24 = seg_cohort[seg_cohort["month"] == 24].copy()
    seg_24["ltv_cac"] = (seg_24["ltv_to_date"] / s["cac"]).round(2) if s["cac"] > 0 else 0
    seg_summary = seg_24[["segment", "active_pct", "ltv_to_date", "ltv_cac"]].copy()
    seg_summary.columns = ["Segment", "M24 Retention %", "CLV ($)", "LTV:CAC"]
    st.dataframe(seg_summary, use_container_width=True, hide_index=True)

with tab4:
    st.markdown('<div class="terminal-header">CAC CEILING CALCULATOR</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 1rem;">'
        'Given your current retention curve and monetization, what is the maximum CAC you can afford '
        'while maintaining a target LTV:CAC ratio?'
        '</p>',
        unsafe_allow_html=True,
    )

    target_col, horizon_col, _ = st.columns([1, 1, 2])
    with target_col:
        target_ratio = st.number_input("Target LTV:CAC Ratio", 1.0, 10.0, 3.0, step=0.5, key="cac_target")
    with horizon_col:
        horizon = st.number_input("Horizon (months)", 6, 60, 24, step=6, key="cac_horizon")

    # Compute ceiling across different ratios
    ratios = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    horizons = [12, 18, 24, 36]

    ceiling_data = []
    for h in horizons:
        row = {"Horizon": f"{h} months"}
        for r in ratios:
            c = model.cac_ceiling(target_ltv_cac=r, horizon_months=h)
            row[f"{r:.1f}x"] = f"${c:,.2f}"
        ceiling_data.append(row)

    st.dataframe(pd.DataFrame(ceiling_data), use_container_width=True, hide_index=True)

    # Visual: CAC headroom
    st.markdown('<div class="terminal-header">CAC HEADROOM ANALYSIS</div>', unsafe_allow_html=True)
    selected_ceiling = model.cac_ceiling(target_ltv_cac=target_ratio, horizon_months=int(horizon))
    current_cac = s["cac"]
    headroom = selected_ceiling - current_cac

    fig_headroom = go.Figure()
    fig_headroom.add_trace(go.Bar(
        x=["Current CAC", "CAC Ceiling", "Headroom"],
        y=[current_cac, selected_ceiling, max(0, headroom)],
        marker_color=["#00f2ff", "#8a2be2", "#14b8a6" if headroom > 0 else "#f43f5e"],
        text=[f"${current_cac:.2f}", f"${selected_ceiling:.2f}", f"${headroom:+.2f}"],
        textposition="outside",
    ))
    fig_headroom.update_layout(**PLOTLY_THEME["layout"], showlegend=False, height=400)
    fig_headroom.update_yaxes(title="$ AMOUNT")
    st.plotly_chart(fig_headroom, use_container_width=True)

    if headroom > 0:
        st.success(f"You have **${headroom:,.2f}** of CAC headroom at a {target_ratio}x target over {int(horizon)} months.")
    else:
        st.error(f"Your current CAC **exceeds** the ceiling by **${abs(headroom):,.2f}**. You need to either reduce CAC or improve retention/monetization.")
