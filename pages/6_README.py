"""
Page 6: README
===============
System documentation and architecture overview.
"""

import streamlit as st
from pathlib import Path

# ── Load CSS ──
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.markdown('<div class="terminal-header">SYSTEM DOCS // ARCHITECTURE V1.0</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">README</h1>', unsafe_allow_html=True)

with st.expander("Concept Playbook: How to use this page"):
    st.markdown('''
    **Overview:** This page provides causal insights into your metrics.
    **How to use:** Adjust the inputs in the sidebar or main area to simulate different business scenarios. 
    Pay attention to the outputs with tooltips for detailed definitions. All metrics are connected to the central causal model.
    ''')

st.markdown("---")

readme_path = Path(__file__).parent.parent / "README.md"
if readme_path.exists():
    st.markdown(readme_path.read_text())
else:
    st.error("// ERROR: README FILE NOT FOUND")
