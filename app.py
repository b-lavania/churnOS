"""
Home: Churn Analysis & Marketplace Analytics
=============================================
Main dashboard and knowledge base for ecommerce & marketplace operators.
"""

import streamlit as st
from pathlib import Path

# Data schema version - bump when changing expected columns
DATA_VERSION = "1.1"

# ── Page Configuration ──
st.set_page_config(
    page_title="CHURN OS",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Custom CSS ──
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Sidebar Branding (above navigation) ──
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 1rem 0;">
            <div class="terminal-header">SYSTEM STATUS: ACTIVE</div>
            <h2 style="margin: 0; font-family: 'Outfit';">CHURN OS</h2>
            <p style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #00f2ff; opacity: 0.8;">
                REVENUE INTELLIGENCE UNIT
            </p>
        </div>
        <hr style="border-color: rgba(255,255,255,0.08); margin: 0.5rem 0 1.5rem;">
        """,
        unsafe_allow_html=True,
    )

def home_page():
    # ── Cache data generation with version key ──
    @st.cache_data(show_spinner="INIT SYSTEM DATA...", ttl=3600)
    def load_data(version: str = DATA_VERSION):
        from data.generator import generate_all_data
        return generate_all_data()

    data = load_data()
    st.session_state["app_data"] = data

    # ── Header ──
    st.markdown('<div class="terminal-header">HOME // CORE DASHBOARD // OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="gradient-text" style="font-size:3rem; margin-bottom:0.5rem;">Churn & Marketplace Analytics</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="max-width: 800px; margin-bottom: 2rem;">'
        'High-resolution intelligence for high-growth commerce. '
        'Real-time synthesis of churn propensity, retention cohorts, and price elasticity.'
        '</p>',
        unsafe_allow_html=True,
    )

    # ── Quick Stats Grid ──
    # Wrap metrics in a techno-card container for better aesthetics
    st.markdown('<div class="techno-card">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("TOTAL CUSTOMERS", f"{len(data['customers']):,}")
    with col2:
        st.metric("TOTAL TXN VOLUME", f"{len(data['transactions']):,}")
    with col3:
        st.metric("SESSION COUNT", f"{len(data['funnel']['session_id'].unique()):,}")
    with col4:
        st.metric("ACTIVE SELLERS", f"{len(data['marketplace']):,}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Exploration Modules ──
    st.markdown('<div class="terminal-header" style="margin-top:2rem;">ANALYTICS MODULES</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    modules = [
        ("Churn Analysis", "Deep-dive into churn drivers and survival curves. Identify high-risk cohorts before they attrit.", "#00f2ff"),
        ("Retention", "Multi-dimensional cohort analysis and CLV projections. Flatten the retention curve.", "#8a2be2"),
        ("Conversion", "Funnel breakdown and A/B test benchmarking. Optimize the path to purchase.", "#ff9d00"),
        ("Pricing", "Elasticity modeling and marketplace fee logic. Maximize take-rate and GMV efficiency.", "#14b8a6"),
    ]

    for col, (title, desc, color) in zip([c1, c2, c3, c4], modules):
        with col:
            st.markdown(
                f'''
                <div class="techno-card" style="border-top: 2px solid {color}; height: 220px;">
                    <h4 style="color: {color}; margin-top: 0;">{title}</h4>
                    <p style="font-size: 0.85rem; line-height: 1.4; color: #94a3b8;">{desc}</p>
                    <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: {color}; margin-top: 1rem;">
                        MODULE STABLE // VERSION 1.0
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

    # ── Knowledge Base ──
    st.markdown('<div class="terminal-header" style="margin-top:2rem;">KNOWLEDGE REPOSITORY // STRATEGIC PLAYBOOKS</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="gradient-text">Knowledge Base</h2>', unsafe_allow_html=True)

    _kb_sections = [
        ("CHURN INTEL", "Understand churn drivers and survival dynamics.", '''
**LOGO CHURN**
Formula: `Churned / Total`
Benchmark: `< 5% (SaaS)`, `20-30% (Ecommerce)`

**REVENUE CHURN**
Formula: `(Lost MRR - Expansion) / Total MRR`
Benchmark: `< 2% monthly`
        '''),
        ("RETENTION DYNAMICS", "Cohort analysis and CLV optimization.", '''
**DAY-N RETENTION**
D1, D7, D30 are critical indicators of product-market fit.
Benchmark: `D1: 40%+, D30: 10%+`

**CLV:CAC RATIO**
The efficiency of acquisition.
Benchmark: `> 3.0x`
        '''),
        ("CONVERSION SCIENCE", "Funnel resolution and A/B test rigor.", '''
**ECOMMERCE FUNNEL**
`Visit -> View -> Cart -> Checkout -> Pay`
Average CVR Benchmark: `2.0 - 4.0%`
        '''),
        ("PRICING ENGINE", "Elasticity and marketplace economics.", '''
**PRICE ELASTICITY**
`% Change in Quantity / % Change in Price`
Optimal revenue is achieved where `|e| = 1.0`
        ''')
    ]

    for _title, _subtitle, _content in _kb_sections:
        with st.expander(f"// {_title} // {_subtitle}"):
            st.markdown(_content)

    # ── Footer Info ──
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem; font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #475569;">
            // PLATFORM STATUS: NOMINAL // DATA ENCRYPTION: ENABLED // SEED 42 LOADED // ACCESS LEVEL: RESTRICTED
        </div>
        """,
        unsafe_allow_html=True,
    )

pg = st.navigation([
    st.Page(home_page, title="Home"),
    st.Page("pages/1_Churn_Analysis.py", title="Churn Analysis"),
    st.Page("pages/2_Retention.py", title="Retention"),
    st.Page("pages/3_Conversion_Optimization.py", title="Conversion Optimization"),
    st.Page("pages/4_Pricing_Analytics.py", title="Pricing Analytics"),
    st.Page("pages/5_Marketplace.py", title="Marketplace"),
    st.Page("pages/6_README.py", title="README"),
])

pg.run()
