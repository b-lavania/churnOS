"""
Page 4: Marketplace
=====================
Marketplace-specific deep dive — seller/buyer economics, take rate analysis,
and liquidity metrics. Connected to the causal model.
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

st.markdown('<div class="terminal-header">DEEP DIVE // MARKETPLACE ECONOMICS</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Marketplace</h1>', unsafe_allow_html=True)

if "model" not in st.session_state:
    st.warning("No model defined. Go to **Business Model** to configure your business first.")
    st.stop()

model = st.session_state["model"]
s = st.session_state["model_summary"]
config = st.session_state["model_config"]

# ── Generate marketplace data ──
from data.generator import generate_marketplace_pricing, generate_buyers
from analytics.pricing import take_rate_analysis, price_elasticity_sim, commission_tier_model

# Use model config to generate consistent data
take_rate_val = config.get("take_rate", 0.15)
buyer_fee_val = config.get("buyer_fee_split", 0.40)
fixed_fee_val = config.get("fixed_fee_per_txn", 0.0)
n_sellers_val = config.get("n_sellers", 500)

if "mp_data" not in st.session_state:
    st.session_state["mp_data"] = generate_marketplace_pricing(
        n_sellers=n_sellers_val,
        take_rate_multiplier=take_rate_val / 0.15 if take_rate_val != 0 else 1.0,
        buyer_fee_split=buyer_fee_val,
        fixed_fee=fixed_fee_val,
    )
    st.session_state["buyer_data"] = generate_buyers()

marketplace = st.session_state["mp_data"]
buyers = st.session_state["buyer_data"]

# ── KPI Row ──
gmv = marketplace["monthly_gmv"].sum()
net_rev = marketplace["net_revenue"].sum()
eff_take = (net_rev / gmv * 100) if gmv > 0 else 0
b2s_ratio = len(buyers) / len(marketplace) if len(marketplace) > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("GMV", f"${gmv:,.0f}")
k2.metric("PLATFORM REVENUE", f"${net_rev:,.0f}")
k3.metric("EFF TAKE RATE", f"{eff_take:.1f}%")
k4.metric("BUYER:SELLER", f"{b2s_ratio:.1f}:1")
k5.metric("ACTIVE SELLERS", f"{len(marketplace):,}")

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs([
    "[ 01 ] TAKE RATE",
    "[ 02 ] ELASTICITY",
    "[ 03 ] TIER ECONOMICS",
    "[ 04 ] LIQUIDITY",
])

with tab1:
    st.markdown('<div class="terminal-header">TAKE RATE BY CATEGORY</div>', unsafe_allow_html=True)
    tr = take_rate_analysis(marketplace)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=tr["category"], y=tr["total_gmv"], name="GMV", marker_color="#00f2ff"))
    fig.add_trace(go.Bar(x=tr["category"], y=tr["total_net_revenue"], name="REVENUE", marker_color="#8a2be2"))
    fig.update_layout(**PLOTLY_THEME["layout"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    # Effective take rate by category
    fig_tr = px.bar(
        tr, x="category", y="effective_take_rate",
        color="effective_take_rate",
        color_continuous_scale=["#00f2ff", "#8a2be2"],
        labels={"category": "CATEGORY", "effective_take_rate": "EFFECTIVE TAKE RATE %"},
    )
    fig_tr.update_layout(**PLOTLY_THEME["layout"], coloraxis_showscale=False)
    st.plotly_chart(fig_tr, use_container_width=True)

with tab2:
    st.markdown('<div class="terminal-header">PRICE ELASTICITY SIMULATION</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.82rem; color: #94a3b8;">'
        'Model demand response to price changes. The optimal revenue point is where |elasticity| = 1.'
        '</p>',
        unsafe_allow_html=True,
    )

    el_col1, el_col2 = st.columns(2)
    with el_col1:
        base_price = st.number_input("BASE PRICE ($)", 5.0, 500.0, 50.0, step=5.0, key="mp_base_price")
    with el_col2:
        elasticity = st.slider("ELASTICITY COEFFICIENT", -3.0, -0.1, -1.5, step=0.1, key="mp_elasticity")

    sim = price_elasticity_sim(base_price, elasticity)
    optimal_idx = sim["revenue"].idxmax()
    optimal_price = sim.loc[optimal_idx, "price"]

    fig_el = go.Figure()
    fig_el.add_trace(go.Scatter(
        x=sim["price"], y=sim["revenue"],
        name="REVENUE",
        line=dict(color="#00f2ff", width=3),
        fill="tozeroy",
        fillcolor="rgba(0, 242, 255, 0.05)",
    ))
    fig_el.add_trace(go.Scatter(
        x=sim["price"], y=sim["demand"] * base_price / 20,  # scale for dual axis
        name="DEMAND (scaled)",
        line=dict(color="#8a2be2", width=2, dash="dash"),
    ))
    fig_el.add_vline(x=optimal_price, line_dash="dot", line_color="#14b8a6",
                     annotation_text=f"Optimal: ${optimal_price:.2f}",
                     annotation_font_color="#14b8a6")
    fig_el.update_layout(**PLOTLY_THEME["layout"])
    fig_el.update_xaxes(title="PRICE ($)")
    fig_el.update_yaxes(title="REVENUE ($)")
    st.plotly_chart(fig_el, use_container_width=True)

with tab3:
    st.markdown('<div class="terminal-header">COMMISSION TIER BREAKDOWN</div>', unsafe_allow_html=True)
    tier_data = commission_tier_model(marketplace)

    fig_tier_rev = px.bar(
        tier_data, x="commission_tier", y="total_net_revenue",
        color="commission_tier",
        color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6"],
        text="revenue_share",
    )
    fig_tier_rev.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
    fig_tier_rev.update_yaxes(title="NET REVENUE ($)")
    st.plotly_chart(fig_tier_rev, use_container_width=True)

    # Tier details table
    st.markdown('<div class="terminal-header">TIER DETAILS</div>', unsafe_allow_html=True)
    display_tiers = tier_data[["commission_tier", "num_sellers", "total_gmv", "total_net_revenue", "effective_take_rate", "gmv_share", "revenue_share"]].copy()
    display_tiers.columns = ["Tier", "Sellers", "GMV ($)", "Revenue ($)", "Eff. Take Rate %", "GMV Share %", "Rev Share %"]
    st.dataframe(display_tiers, use_container_width=True, hide_index=True)

with tab4:
    st.markdown('<div class="terminal-header">MARKETPLACE LIQUIDITY ANALYSIS</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 1rem;">'
        'Liquidity = the ability of buyers to find what they want and sellers to make sales. '
        'Higher buyer:seller ratios generally improve seller economics but may reduce buyer choice.'
        '</p>',
        unsafe_allow_html=True,
    )

    # Simulate different buyer:seller ratios
    ratios_sim = np.linspace(2, 40, 20)
    liq_data = []
    for ratio in ratios_sim:
        projected_buyers = int(len(marketplace) * ratio)
        projected_gmv_per_seller = gmv / len(marketplace) * (1 + np.log(ratio) / np.log(20))
        projected_total_gmv = projected_gmv_per_seller * len(marketplace)
        liq_data.append({
            "buyer_seller_ratio": round(ratio, 1),
            "projected_gmv": round(projected_total_gmv),
            "gmv_per_seller": round(projected_gmv_per_seller),
        })
    liq_df = pd.DataFrame(liq_data)

    fig_liq = go.Figure()
    fig_liq.add_trace(go.Scatter(
        x=liq_df["buyer_seller_ratio"],
        y=liq_df["projected_gmv"],
        name="TOTAL GMV",
        line=dict(color="#00f2ff", width=3),
        fill="tozeroy",
        fillcolor="rgba(0, 242, 255, 0.05)",
    ))
    fig_liq.add_vline(x=b2s_ratio, line_dash="dash", line_color="#ff9d00",
                      annotation_text=f"Current: {b2s_ratio:.1f}:1",
                      annotation_font_color="#ff9d00")
    fig_liq.update_layout(**PLOTLY_THEME["layout"])
    fig_liq.update_xaxes(title="BUYER : SELLER RATIO")
    fig_liq.update_yaxes(title="PROJECTED GMV ($)")
    st.plotly_chart(fig_liq, use_container_width=True)

    # Seller concentration
    st.markdown('<div class="terminal-header">SELLER CONCENTRATION // PARETO ANALYSIS</div>', unsafe_allow_html=True)
    sorted_sellers = marketplace.sort_values("monthly_gmv", ascending=False).reset_index(drop=True)
    sorted_sellers["cumulative_pct"] = (sorted_sellers["monthly_gmv"].cumsum() / gmv * 100).round(1)
    sorted_sellers["seller_rank_pct"] = ((sorted_sellers.index + 1) / len(sorted_sellers) * 100).round(1)

    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Scatter(
        x=sorted_sellers["seller_rank_pct"],
        y=sorted_sellers["cumulative_pct"],
        line=dict(color="#8a2be2", width=3),
        fill="tozeroy",
        fillcolor="rgba(138, 43, 226, 0.08)",
    ))
    fig_pareto.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                         line=dict(color="rgba(255,255,255,0.2)", dash="dash"))
    fig_pareto.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
    fig_pareto.update_xaxes(title="SELLER RANK PERCENTILE (%)")
    fig_pareto.update_yaxes(title="CUMULATIVE GMV (%)")
    st.plotly_chart(fig_pareto, use_container_width=True)

    # Top 20% stat
    top_20_gmv = sorted_sellers.head(int(len(sorted_sellers) * 0.2))["monthly_gmv"].sum()
    top_20_pct = top_20_gmv / gmv * 100
    st.info(f"Top 20% of sellers generate **{top_20_pct:.1f}%** of GMV — {'high' if top_20_pct > 80 else 'moderate'} concentration.")
