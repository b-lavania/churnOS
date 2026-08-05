"""Record inspector — GrowthDecisionRecord JSON + validation."""

from pathlib import Path

import json
import streamlit as st

from core.workspace import ensure_growth_records, get_workspace_from_session
from ontology.store import read_records
from ontology.validate import validate_record
from ui.decision_card import render_decision_card
from ui.explain import page_help
from ui.magazine import load_magazine_css, masthead, section_kicker
from ui.workspace_banner import require_workspace

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead("Ontology", "Record Inspector", "Inspect, validate, and override GrowthDecisionRecords.")
page_help("inspector", show_card_glossary=True)

ws = require_workspace(st.session_state, page_label="Record Inspector")
records = ensure_growth_records(st.session_state, ws)
stored = read_records()

entity_filter = st.selectbox("Entity type", ["all", "account", "capability"])
filtered = records
if entity_filter != "all":
    filtered = [r for r in records if r.get("subject", {}).get("entity_type") == entity_filter]

def _apply_override(rec, action, reason):
    from analytics.decisions import apply_override
    from ontology.store import append_record
    idx = next(i for i, r in enumerate(st.session_state["growth_records"]) if r["record_id"] == rec["record_id"])
    updated = apply_override(rec, action, reason)
    st.session_state["growth_records"][idx] = updated
    append_record(updated)

section_kicker("Session records")
for i, rec in enumerate(filtered[:8]):
    errors = validate_record(rec, rec.get("vertical", "capability_lifecycle"))
    if errors:
        st.warning(f"Validation: {errors[:2]}")
    render_decision_card(rec, key_prefix=f"insp_{i}", on_override=_apply_override)

if stored:
    section_kicker("Persisted JSONL")
    st.json(stored[-3:])
