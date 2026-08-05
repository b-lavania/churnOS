"""Legacy suite index — single sidebar entry for reference pages."""

from pathlib import Path

import streamlit as st

from ui.legacy_banner import render_legacy_banner
from ui.magazine import load_magazine_css, masthead, section_kicker

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
render_legacy_banner()
masthead(
    "Legacy",
    "Reference modules",
    "Pre-agentic ecomm / marketplace / CRO surfaces. Not part of the decision-grade story.",
)

section_kicker("Open a module")
st.caption("These pages stay registered for deep links; the sidebar only lists this index.")

LEGACY_LINKS = [
    ("pages/0_Business_Model.py", "Business Model"),
    ("pages/1_Retention_Churn.py", "Retention & Churn"),
    ("pages/2_Unit_Economics.py", "Unit Economics"),
    ("pages/11_Product_Lifecycle.py", "Lifecycle & NSM"),
    ("pages/4_Marketplace.py", "Pricing Analytics"),
    ("pages/5_Marketplace_Analytics.py", "Seller Analytics"),
    ("pages/8_ECommerce_Analytics.py", "RFM & Inventory"),
    ("pages/9_Marketplace_Liquidity.py", "Marketplace Liquidity"),
    ("pages/10_Attribution_MMM.py", "Attribution & MMM"),
    ("pages/12_CRO_Program.py", "CRO Program"),
    ("pages/13_Revenue_Leakage.py", "Revenue Leakage"),
    ("pages/14_Conversion_Forecast.py", "Conversion Forecast"),
]

for path, label in LEGACY_LINKS:
    st.page_link(path, label=label, use_container_width=True)
