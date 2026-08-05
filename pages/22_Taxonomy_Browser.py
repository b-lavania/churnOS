"""Taxonomy browser."""

from pathlib import Path

import streamlit as st

from ontology.exception_taxonomy import CATEGORIES, VERDICTS, ACTIONS
from ui.explain import page_help
from ui.magazine import load_magazine_css, masthead, section_kicker

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead("Ontology", "Taxonomy Browser", "Exception categories, verdicts, and control-plane actions.")
page_help("taxonomy")

section_kicker("Exception categories")
for key, meta in CATEGORIES.items():
    with st.expander(key):
        st.write(f"**Owner:** {meta['owner_role']}")
        st.write(f"**Severity:** {meta['default_severity']}")
        st.write(meta["playbook_hint"])

section_kicker("Verdicts")
st.write(", ".join(VERDICTS))
section_kicker("Actions")
st.write(", ".join(ACTIONS))
