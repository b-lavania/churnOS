"""
Page 4: Pricing Analytics
==========================
Marketplace economics and elasticity synthesis.
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

st.markdown('<div class="terminal-header">ANALYTICS UNIT // PRICING ECONOMY</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Pricing Analytics</h1>', unsafe_allow_html=True)

# ── Data Load ──
if "app_data" not in st.session_state:
    from data.generator import generate_all_data
    st.session_state["app_data"] = generate_all_data()

data = st.session_state["app_data"]
marketplace = data["marketplace"]

from analytics.pricing import take_rate_analysis, price_elasticity_sim, commission_tier_model

# ── Simulation Controls ──
col_a, col_b, col_c, col_d, col_e = st.columns(5)
with col_a:
    new_sel = st.number_input("N SELLERS", 50, 5000, 500, step=50)
with col_b:
    new_take = st.slider("TAKE RATE MULTIP", 0.5, 2.0, 1.0, 0.1)
with col_c:
    new_split = st.slider("BUYER FEE SPLIT", 0.0, 1.0, 0.40, 0.05)
with col_d:
    new_fixed = st.slider("FIXED FEE ($)", 0.0, 2.0, 0.0, 0.1)
with col_e:
    st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True)
    if st.button("Calculate", type="primary", key="regen_price"):
        # Use optional advanced params (if provided in the expander below)
        from data.generator import generate_marketplace_pricing
        # Build optional parameters collected in the advanced expander
        params = {}
        if "adv_categories" in st.session_state:
            params["categories"] = st.session_state["adv_categories"]
        if "adv_tiers" in st.session_state:
            params["tiers"] = st.session_state["adv_tiers"]
        if "adv_tier_rates" in st.session_state:
            params["tier_rates"] = st.session_state["adv_tier_rates"]
        if "adv_tier_weights" in st.session_state:
            params["tier_weights"] = st.session_state["adv_tier_weights"]
        if "adv_gmv_mu" in st.session_state:
            params["gmv_mu"] = st.session_state["adv_gmv_mu"]
            params["gmv_sigma"] = st.session_state.get("adv_gmv_sigma", 1.2)
        if "adv_aov_mu" in st.session_state:
            params["aov_mu"] = st.session_state["adv_aov_mu"]
            params["aov_sigma"] = st.session_state.get("adv_aov_sigma", 0.8)
        if "adv_listings_min" in st.session_state:
            params["listings_min"] = st.session_state["adv_listings_min"]
            params["listings_max"] = st.session_state.get("adv_listings_max", 500)

        st.session_state["app_data"]["marketplace"] = generate_marketplace_pricing(
            n_sellers=new_sel,
            take_rate_multiplier=new_take,
            buyer_fee_split=new_split,
            fixed_fee=new_fixed,
            **params,
        )
        st.rerun()

# Advanced parameters for marketplace generation
with st.expander("Advanced Marketplace Parameters", expanded=False):
    # Text inputs parsed into lists/dicts and stored in session_state so the Calculate button can consume them
    cats = st.text_area("Categories (comma-separated)", value=",").strip()
    if cats:
        cat_list = [c.strip() for c in cats.split(",") if c.strip()]
    else:
        cat_list = None
    st.session_state["adv_categories"] = cat_list

    tiers = st.text_input("Tiers (comma-separated)", value="Starter,Growth,Pro,Enterprise")
    tier_list = [t.strip() for t in tiers.split(",") if t.strip()]
    st.session_state["adv_tiers"] = tier_list

    tier_weights = st.text_input("Tier weights (comma-separated, sum to 1)", value="0.40,0.30,0.20,0.10")
    try:
        tw = [float(x.strip()) for x in tier_weights.split(",") if x.strip()]
    except Exception:
        tw = None
    st.session_state["adv_tier_weights"] = tw

    tier_rates_text = st.text_area("Tier rate ranges (JSON)", value='{"Starter": [0.15, 0.20], "Growth": [0.12,0.17], "Pro": [0.08,0.14], "Enterprise": [0.05,0.10]}')
    try:
        import json

        tr = json.loads(tier_rates_text)
    except Exception:
        tr = None
    st.session_state["adv_tier_rates"] = tr

    gmv_mu = st.number_input("GMV lognormal mu", value=10.0)
    gmv_sigma = st.number_input("GMV lognormal sigma", value=1.2)
    st.session_state["adv_gmv_mu"] = gmv_mu
    st.session_state["adv_gmv_sigma"] = gmv_sigma

    aov_mu = st.number_input("AOV lognormal mu", value=3.5)
    aov_sigma = st.number_input("AOV lognormal sigma", value=0.8)
    st.session_state["adv_aov_mu"] = aov_mu
    st.session_state["adv_aov_sigma"] = aov_sigma

    listings_min = st.number_input("Listings min", value=5)
    listings_max = st.number_input("Listings max", value=500)
    st.session_state["adv_listings_min"] = listings_min
    st.session_state["adv_listings_max"] = listings_max

# ── KPI Row ──
c1, c2, c3, c4 = st.columns(4)
gmv = marketplace["monthly_gmv"].sum()
net = marketplace["net_revenue"].sum()
c1.metric("GMV TOTAL", f"${gmv:,.0f}")
c2.metric("NET REVENUE", f"${net:,.0f}")
c3.metric("EFF TAKE RATE", f"{(net/gmv*100):.2f}%")
c4.metric("AVG ORDER VAL", f"${marketplace['avg_order_value'].mean():,.2f}")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["[ 01 ] TAKE RATE MAP", "[ 02 ] ELASTICITY SIM", "[ 03 ] TIER BREAKDOWN"])

with tab1:
    st.markdown('<div class="terminal-header">CATEGORY TAKE RATE MATRIX</div>', unsafe_allow_html=True)
    tr = take_rate_analysis(marketplace)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tr["category"], y=tr["total_gmv"], name="GMV", marker_color="#00f2ff"))
    fig.add_trace(go.Bar(x=tr["category"], y=tr["total_net_revenue"], name="NET", marker_color="#8a2be2"))
    fig.update_layout(**PLOTLY_THEME["layout"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown('<div class="terminal-header">PRICE ELASTICITY SYNTHESIS</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    el = col1.slider("ELASTICITY COEFF", -3.0, -0.1, -1.5)
    sim = price_elasticity_sim(50.0, el)
    fig2 = px.line(sim, x="price", y="revenue", color_discrete_sequence=["#00f2ff"], labels={"price": "PRICE", "revenue": "REVENUE"})
    fig2.update_layout(**PLOTLY_THEME["layout"])
    st.plotly_chart(fig2, use_container_width=True)
    st.info(f"// OPTIMAL REVENUE THRESHOLD: ${sim.iloc[sim['revenue'].idxmax()]['price']:.2f}")

with tab3:
    st.markdown('<div class="terminal-header">COMMISSION TIER SHARE</div>', unsafe_allow_html=True)
    tier_data = commission_tier_model(marketplace)
    fig3 = px.pie(tier_data, values="total_net_revenue", names="commission_tier", hole=0.7, color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6"], labels={"commission_tier": "COMMISSION TIER", "total_net_revenue": "NET REVENUE"})
    fig3.update_layout(**PLOTLY_THEME["layout"])
    st.plotly_chart(fig3, use_container_width=True)

