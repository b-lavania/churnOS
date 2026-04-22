import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from data.generator import generate_all_data
from analytics.marketplace import calculate_liquidity_metrics, supply_side_cohorts, cross_side_network_effects

st.set_page_config(page_title="Marketplace Liquidity", layout="wide")

# Load CSS
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.markdown('<div class="terminal-header">MARKETPLACE // LIQUIDITY</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Liquidity & Network Effects</h1>', unsafe_allow_html=True)

with st.expander("Concept Playbook: How to use this page"):
    st.markdown('''
    **Overview:** This page provides causal insights into your metrics.
    **How to use:** Adjust the inputs in the sidebar or main area to simulate different business scenarios. 
    Pay attention to the outputs with tooltips for detailed definitions. All metrics are connected to the central causal model.
    ''')


# Generate Data
@st.cache_data
def load_data():
    return generate_all_data()

data = load_data()
buyers = data['buyers']
sellers = data['marketplace']
transactions = data['transactions']

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Liquidity Metrics", "Supply-Side Cohorts", "Network Effects Simulator"])

with tab1:
    st.subheader("Two-Sided Liquidity")
    liq = calculate_liquidity_metrics(buyers, sellers, transactions)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Search-to-Fill Rate", f"{liq.get('search_to_fill_rate', 0):.2f}%")
    col2.metric("Avg Time to First Sale", f"{liq.get('avg_time_to_first_sale_days', 0):.1f} days")
    col3.metric("Buyer-to-Seller Ratio", f"{liq.get('buyer_to_seller_ratio', 0):.2f}:1")

with tab2:
    st.subheader("Supply-Side Survival Curves")
    cohorts = supply_side_cohorts(sellers)
    if not cohorts.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cohorts["month"], y=cohorts["active_pct"],
            mode="lines+markers",
            name="Active %",
            line=dict(color="#00f2ff", width=3),
            fill="tozeroy",
            fillcolor="rgba(0, 242, 255, 0.05)",
        ))
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"))
        fig.update_xaxes(title="Months Since Signup")
        fig.update_yaxes(title="Retention %", range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No cohort data available.")

with tab3:
    st.subheader("Cross-Side Network Effects")
    st.write("Simulate how acquiring new sellers impacts buyer conversion.")
    
    growth_slider = st.slider("Simulated Seller Growth", min_value=0.0, max_value=2.0, value=0.5, step=0.1, help="Adjust this parameter to see its impact on the model.")
    
    nw = cross_side_network_effects(buyers, sellers, simulated_seller_growth=growth_slider)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Projected Sellers", f"{nw.get('projected_sellers', 0):,}")
    col2.metric("New Buyer Conversion", f"{nw.get('projected_conversion_pct', 0):.2f}%", f"+{nw.get('gmv_lift_pct', 0):.1f}% lift")
    col3.metric("Projected GMV", f"${nw.get('projected_gmv', 0):,.2f}")
