import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from data.generator import generate_all_data
from analytics.ecommerce import calculate_rfm_segments, inventory_volatility_impact, discount_cannibalization_analysis

st.set_page_config(page_title="E-Commerce Deep Dive", layout="wide")

# Load CSS
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.markdown('<div class="terminal-header">ECOMMERCE // DEEP DIVE</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">E-Commerce Analytics</h1>', unsafe_allow_html=True)

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
transactions = data['transactions']

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["RFM Segmentation", "Inventory Simulator", "Discount Cannibalization"])

with tab1:
    st.subheader("RFM Lifecycle Segmentation")
    rfm = calculate_rfm_segments(transactions)
    if not rfm.empty:
        segment_counts = rfm['Segment'].value_counts().reset_index()
        segment_counts.columns = ['Segment', 'Count']
        
        fig = px.pie(segment_counts, names='Segment', values='Count', hole=0.4, title="Customer Segments", color_discrete_sequence=px.colors.sequential.Teal)
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"))
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(rfm.head())
    else:
        st.write("No transaction data available.")

with tab2:
    st.subheader("Inventory Volatility & COGS Impact")
    inv_impact = inventory_volatility_impact(transactions)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Stockout Events", f"{inv_impact.get('stockout_count', 0):,}")
    col2.metric("Est. Lost Revenue", f"${inv_impact.get('lost_revenue_est', 0):,.2f}")
    col3.metric("Margin Compression", f"{inv_impact.get('margin_compression_pct', 0):.2f}%")

with tab3:
    st.subheader("Promo Cannibalization Analyzer")
    discount_impact = discount_cannibalization_analysis(transactions)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Incremental Events", f"{discount_impact.get('incremental_events', 0):,}")
    col2.metric("Cannibalized Events", f"{discount_impact.get('cannibalized_events', 0):,}")
    col3.metric("Net Promo Value", f"${discount_impact.get('net_promo_value', 0):,.2f}")
