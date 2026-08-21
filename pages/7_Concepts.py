"""Concepts & Playbook — rendered from ontology semantics + lexicon."""

from pathlib import Path

import streamlit as st
import yaml

from ontology.exception_taxonomy import CATEGORIES
from ontology.semantics import load_all_semantics
from ui.explain import competitive_faq, page_help, tool_stack_explainer
from ui.magazine import load_magazine_css, masthead, section_kicker

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead(
    "Reference",
    "Concepts & Playbook",
    "Agent-readable product language from semantics.yaml and governed metrics.",
)
page_help("concepts")
tool_stack_explainer(expanded=False)
competitive_faq(expanded=False)

lexicon_path = Path(__file__).parent.parent / "metrics" / "lexicon.yaml"
lexicon = yaml.safe_load(lexicon_path.read_text()) if lexicon_path.exists() else {"metrics": {}}

section_kicker("Ontology semantics")
for vertical, sem in load_all_semantics().items():
    with st.expander(vertical):
        verdicts = sem.get("decision.verdict", {})
        for k, v in verdicts.items():
            st.markdown(f"**{k}** — {v}")
        action_map = sem.get("decision", {}).get("action_map", {})
        if action_map:
            st.markdown("---")
            st.caption("Governing action map (from semantics.yaml)")
            for verdict, spec in action_map.items():
                st.markdown(
                    f"**{verdict}** → `{spec.get('recommended_action')}` "
                    f"{'(review)' if spec.get('requires_review') else ''}"
                )

section_kicker("Exception taxonomy")
for key, meta in CATEGORIES.items():
    st.markdown(f"**{key}** ({meta['owner_role']}) — {meta['playbook_hint']}")

section_kicker("Governed metrics (lexicon)")
for key, m in lexicon.get("metrics", {}).items():
    st.markdown(f"**{m.get('label', key)}** — {m.get('caveats', '')}")
