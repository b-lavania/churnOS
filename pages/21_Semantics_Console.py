"""Semantics Console — agent-readable product language + governing rules."""

from pathlib import Path

import streamlit as st
import yaml

from ontology.semantics import load_all_semantics
from ui.explain import page_help
from ui.magazine import load_magazine_css, masthead, section_kicker

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead(
    "Ontology",
    "Semantics Console",
    "Field gloss and governing rules — edit YAML, change decisions.",
)
page_help("semantics")

st.markdown(
    '<p class="mag-deck">Verdict rules, action maps, and classification thresholds live in '
    "<code>ontology/&lt;vertical&gt;/semantics.yaml</code>. The decision engine reads these at "
    "emit time — no code change required to retune policy.</p>",
    unsafe_allow_html=True,
)

all_sem = load_all_semantics()
for vertical, sem in all_sem.items():
    section_kicker(vertical)

    decision = sem.get("decision", {})
    if decision:
        st.markdown("**Governing rules (sample values)**")
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Verdict rules (first match wins)")
            st.code(
                yaml.dump(decision.get("verdict_rules", []), default_flow_style=False),
                language="yaml",
            )
        with col2:
            st.caption("Action map")
            st.code(
                yaml.dump(decision.get("action_map", {}), default_flow_style=False),
                language="yaml",
            )
        if "classification" in sem:
            with st.expander("Classification thresholds"):
                st.code(
                    yaml.dump(sem["classification"], default_flow_style=False),
                    language="yaml",
                )

    with st.expander("Full semantics YAML"):
        st.code(yaml.dump(sem, default_flow_style=False), language="yaml")
