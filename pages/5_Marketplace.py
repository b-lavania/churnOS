"""
Page 5: Marketplace Analytics
===============================
Interactive marketplace metrics with scenario simulation.
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

st.markdown('<div class="terminal-header">ANALYTICS UNIT // MARKETPLACE INTELLIGENCE</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Marketplace Metrics</h1>', unsafe_allow_html=True)

# ── Data Load ──
if "app_data" not in st.session_state:
    from data.generator import generate_all_data
    st.session_state["app_data"] = generate_all_data()

data = st.session_state["app_data"]
marketplace = data["marketplace"]
buyers = data["buyers"]
transactions = data["transactions"]

# ── Imports ──
from analytics.marketplace import (
    calculate_overall_metrics,
    calculate_seller_metrics,
    calculate_buyer_metrics,
    simulate_scenario,
    get_seller_tier_distribution,
    get_buyer_segment_distribution,
    get_category_performance,
)

overall = calculate_overall_metrics(marketplace, buyers, transactions)
seller_metrics = calculate_seller_metrics(marketplace)
buyer_metrics = calculate_buyer_metrics(buyers)

# ── Interactive Scenario Simulator ──
st.markdown('<div class="terminal-header">SCENARIO SIMULATOR</div>', unsafe_allow_html=True)

sim_col1, sim_col2, sim_col3, sim_col4 = st.columns(4)
with sim_col1:
    take_rate_mult = st.slider("Take Rate Multiplier", 0.5, 2.0, 1.0, 0.1, key="tr_mult")
with sim_col2:
    cac_mult = st.slider("CAC Multiplier", 0.5, 2.0, 1.0, 0.1, key="cac_mult")
with sim_col3:
    seller_growth = st.slider("Seller Growth %", -20, 50, 0, 5, key="sell_growth") / 100
with sim_col4:
    buyer_growth = st.slider("Buyer Growth %", -20, 50, 0, 5, key="buy_growth") / 100

# Calculate scenario
scenario = simulate_scenario(
    marketplace, buyers,
    take_rate_multiplier=take_rate_mult,
    cac_multiplier=cac_mult,
    new_seller_growth=seller_growth,
    new_buyer_growth=buyer_growth
)

# Show scenario deltas
st.markdown("#### Projected Impact")
delta_cols = st.columns(5)
with delta_cols[0]:
    delta_rev = scenario["revenue_delta"]
    st.metric("Revenue Change", f"${scenario['revenue']:,.0f}", f"${delta_rev:+,.0f}")
with delta_cols[1]:
    st.metric("Projected Sellers", f"{scenario['projected_sellers']:,}", f"{scenario['projected_sellers'] - len(marketplace):+d}")
with delta_cols[2]:
    st.metric("Projected Buyers", f"{scenario['projected_buyers']:,}", f"{scenario['projected_buyers'] - len(buyers):+d}")
with delta_cols[3]:
    st.metric("New Take Rate", f"{scenario['take_rate_avg']*100:.1f}%")
with delta_cols[4]:
    st.metric("CAC % of Revenue", f"{scenario['cac_pct_revenue']:.1f}%")

st.markdown("---")

# ── Sidebar Filters ──
with st.sidebar:
    st.markdown('<div class="terminal-header">FILTERS</div>', unsafe_allow_html=True)
    
    # Category filter with select/deselect all
    all_categories = marketplace["category"].unique().tolist()
    sel_categories = st.multiselect("Categories", all_categories, default=all_categories, key="mp_cat")
    
    # Tier filter
    all_tiers = marketplace["commission_tier"].unique().tolist()
    sel_tiers = st.multiselect("Seller Tiers", all_tiers, default=all_tiers, key="mp_tier")
    
    # Buyer segment filter
    all_segments = buyers["segment"].unique().tolist()
    sel_segments = st.multiselect("Buyer Segments", all_segments, default=all_segments, key="mp_seg")
    
    st.markdown("---")
    
    # Export button
    if st.button("Export Data (CSV)", type="secondary"):
        csv_mp = marketplace.to_csv(index=False)
        st.download_button("Download Marketplace CSV", csv_mp, "marketplace_data.csv", "text/csv")

# Apply filters
filtered_mp = marketplace[
    (marketplace["category"].isin(sel_categories)) &
    (marketplace["commission_tier"].isin(sel_tiers))
]
filtered_buyers = buyers[buyers["segment"].isin(sel_segments)]

# Recalculate metrics based on filters
overall = calculate_overall_metrics(filtered_mp, filtered_buyers, transactions)
seller_metrics = calculate_seller_metrics(filtered_mp)
buyer_metrics = calculate_buyer_metrics(filtered_buyers)

# ── Section A: Overall Marketplace Metrics ──
with st.expander("A. OVERALL MARKETPLACE METRICS", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Gross Merchandise Volume (GMV)", f"${overall['gmv']:,.0f}")
        st.metric("# of Transactions", f"{overall['total_transactions']:,}")
        st.metric("Average Order Value (AOV)", f"${overall['aov']:.2f}")
    with col2:
        st.metric("GMV Growth Rate, M-o-M", "8.5%", "+1.2%")
        st.metric("GMV Growth Rate, Y-o-Y", "42.3%", "+5.1%")
        st.metric("Take Rate (%)", f"{overall['avg_take_rate']*100:.1f}%")
    with col3:
        st.metric("Total Revenue ($)", f"${overall['total_revenue']:,.0f}")
        st.metric("Revenue from Transaction Fees", f"${overall['transaction_fee_revenue']:,.0f}")
        st.metric("Revenue from Fixed Fees", f"${overall['fixed_fee_revenue']:,.0f}")
    with col4:
        delta_sellers = len(filtered_mp) - len(marketplace) if len(filtered_mp) != len(marketplace) else ""
        st.metric("Buyer-to-Seller Ratio", f"{overall['buyer_to_seller_ratio']:.1f}:1")
        st.metric("Total CAC as % of Revenue", f"{overall['total_cac_pct_revenue']:.1f}%")
        st.metric("Active Sellers", f"{overall['num_sellers']:,}", delta_sellers)

st.markdown("---")

# ── Section B: Seller / Supplier Metrics ──
with st.expander("B. SELLER / SUPPLIER METRICS", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total # of Sellers", f"{seller_metrics['total_sellers']:,}")
        st.metric("# of New Sellers", f"{int(seller_metrics['total_sellers'] * 0.08):,}")
        st.metric("Seller Growth Rate, M-o-M", "6.2%", "+0.8%")
        st.metric("Seller Growth Rate, Y-o-Y", "38.5%", "+2.3%")
    with col2:
        st.metric("Sellers Active after 1 Month", f"{seller_metrics['retention_1m_pct']:.1f}%")
        st.metric("Sellers Active after 1 Year", f"{seller_metrics['retention_1y_pct']:.1f}%")
        st.metric("Avg Revenue per Seller", f"${seller_metrics['avg_revenue_per_seller']:,.0f}")
        st.metric("Top 20% Sellers Revenue", f"{seller_metrics['top_20_pct_revenue']:.1f}%")
    with col3:
        st.metric("Seller NPS", "7.2")
        st.metric("Seller CAC (Blended)", f"${seller_metrics['avg_seller_cac']:.0f}")
        st.metric("Seller CAC (Paid)", f"${seller_metrics['avg_seller_cac_paid']:.0f}")
        st.metric("% Paid Acquisition", f"{seller_metrics['pct_paid_acquisition']:.1f}%")
    with col4:
        st.metric("Total # of Listings", f"{seller_metrics['total_listings']:,}")
        st.metric("# of New Listings", f"{int(seller_metrics['total_listings'] * 0.12):,}")
        st.metric("Listings Growth Rate", "9.8%", "+1.5%")
        st.metric("Avg Listing Price", f"${seller_metrics['avg_listing_price']:.2f}")
        st.metric("Sell-Through Rate", f"{seller_metrics['sell_through_rate']:.1f}%")
    
    # Interactive Seller Tier Chart
    tier_dist = get_seller_tier_distribution(filtered_mp)
    fig1 = px.bar(
        tier_dist, 
        x="commission_tier", 
        y="count",
        color="commission_tier",
        color_discrete_sequence=["#00f2ff", "#8a2be2", "#ff9d00", "#14b8a6"],
        labels={"commission_tier": "TIER", "count": "# OF SELLERS"}
    )
    fig1.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)
    
    if st.checkbox("Show Seller Tier Details Table"):
        st.dataframe(tier_dist, use_container_width=True)

st.markdown("---")

# ── Section C: Buyer Metrics ──
with st.expander("C. BUYER METRICS", expanded=True):
    delta_buyers = len(filtered_buyers) - len(buyers) if len(filtered_buyers) != len(buyers) else ""
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total # of Buyers", f"{buyer_metrics['total_buyers']:,}", delta_buyers)
        st.metric("# of New Buyers", f"{buyer_metrics['new_buyers']:,}")
        st.metric("Buyer Growth Rate, M-o-M", f"{buyer_metrics['buyer_growth_mom']:.1f}%")
        st.metric("Buyer Growth Rate, Y-o-Y", f"{buyer_metrics['buyer_growth_yoy']:.1f}%")
    with col2:
        st.metric("Repeat Buyer %", f"{buyer_metrics['repeat_buyer_pct']:.1f}%")
        st.metric("GMV from Repeat Buyers", f"{buyer_metrics['gmv_from_repeat_pct']:.1f}%")
        st.metric("Category Diversity %", f"{buyer_metrics['avg_category_diversity']:.1f}%")
        st.metric("Avg Purchase per Buyer", f"${buyer_metrics['avg_purchase_per_buyer']:.2f}")
        st.metric("Avg # of Orders per Buyer", f"{buyer_metrics['avg_orders_per_buyer']:.1f}")
    with col3:
        st.metric("Top 20% Buyers Revenue", f"{buyer_metrics['top_20_pct_revenue']:.1f}%")
        st.metric("Buyer NPS", f"{buyer_metrics['avg_nps']:.1f}")
        st.metric("Buyer CAC (Blended)", f"${buyer_metrics['avg_buyer_cac']:.2f}")
        st.metric("Buyer CAC (Paid)", f"${buyer_metrics['avg_buyer_cac_paid']:.2f}")
        st.metric("% Paid Acquisition", f"{buyer_metrics['pct_paid_acquisition']:.1f}%")
    
    # Charts row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        segment_dist = get_buyer_segment_distribution(filtered_buyers)
        fig2 = px.pie(
            segment_dist,
            values="count",
            names="segment",
            color="segment",
            color_discrete_map={
                "Budget": "#00f2ff",
                "Mid-Range": "#8a2be2",
                "Premium": "#ff9d00",
                "Enterprise": "#14b8a6"
            },
            labels={"segment": "SEGMENT", "count": "BUYERS"}
        )
        fig2.update_layout(**PLOTLY_THEME["layout"])
        st.plotly_chart(fig2, use_container_width=True)
    
    with chart_col2:
        cat_perf = get_category_performance(filtered_mp)
        fig3 = px.bar(
            cat_perf,
            x="category",
            y="total_gmv",
            color="category",
            color_discrete_sequence=px.colors.sequential.Plasma,
            labels={"category": "CATEGORY", "total_gmv": "GMV ($)"}
        )
        fig3.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

# ── Data Explorer ──
with st.expander("DATA EXPLORER (Raw Data Tables)", expanded=False):
    tab1, tab2, tab3 = st.tabs(["Sellers", "Buyers", "Category Performance"])
    
    with tab1:
        st.dataframe(filtered_mp, use_container_width=True)
    with tab2:
        st.dataframe(filtered_buyers, use_container_width=True)
    with tab3:
        st.dataframe(cat_perf, use_container_width=True)
