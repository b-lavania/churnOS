"""Outcome Flywheel — GDR evaluation + opaque success metrics."""

from pathlib import Path

import streamlit as st

from analytics.decisions import flywheel_evaluation, propose_action, write_outcome
from analytics.metrics import resolve_metric
from core.workspace import ensure_growth_records
from ontology.semantics import load_semantics
from ontology.store import append_record
from ui.decision_card import render_decision_card
from ui.explain import page_help
from ui.magazine import load_magazine_css, masthead, section_kicker
from ui.viz import (
    coordination_overhead_chart,
    flywheel_comparison_chart,
    retention_feature_importance,
    success_vs_complexity,
)
from ui.workspace_banner import require_workspace

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead("Experiment", "Outcome Flywheel", "Followed vs overridden + non-deterministic success signals.")
page_help("flywheel", show_card_glossary=True)

ws = require_workspace(st.session_state, page_label="Outcome Flywheel")
records = ensure_growth_records(st.session_state, ws)

c1, c2, c3 = st.columns(3)
c1.metric("Verified success rate", resolve_metric("verified_outcome_success_rate", ws)["display"])
c2.metric("Coordination overhead", resolve_metric("coordination_overhead", ws)["display"])
c3.metric("Outcome drift WoW", resolve_metric("outcome_success_drift", ws)["display"])

section_kicker("Success vs complexity")
fig_sc = success_vs_complexity(ws)
if fig_sc is not None:
    st.plotly_chart(fig_sc, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    section_kicker("Coordination overhead")
    fig_co = coordination_overhead_chart(ws)
    if fig_co is not None:
        st.plotly_chart(fig_co, use_container_width=True)
with col2:
    section_kicker("Predictive retention features")
    fig_rf = retention_feature_importance(ws)
    if fig_rf is not None:
        st.plotly_chart(fig_rf, use_container_width=True)

section_kicker("Followed vs overridden (GDR flywheel)")
summary = flywheel_evaluation(records)
fig = flywheel_comparison_chart(summary)
if fig is not None:
    st.plotly_chart(fig, use_container_width=True)
elif not summary.get("n"):
    st.caption("Write outcomes below to populate followed vs overridden comparison.")

if summary.get("n"):
    st.table({
        "cohort": ["Followed recommendation", "Overridden"],
        "count": [summary["followed"]["count"], summary["overridden"]["count"]],
        "retention Δ 14d": [summary["followed"]["retention_delta_14d"], summary["overridden"]["retention_delta_14d"]],
        "delegation": [summary["followed"]["delegation_rate"], summary["overridden"]["delegation_rate"]],
        "churn rate": [summary["followed"]["churn_rate"], summary["overridden"]["churn_rate"]],
    })

if records:
    sem = load_semantics(ws.profile.get("ontology_vertical", "capability_lifecycle"))
    action, rationale = propose_action(records[0], sem)
    st.caption(f"Agent stub: **{action}** — {rationale}")

if st.button("Simulate 14d outcome write-back"):
    updated_all = list(st.session_state.get("growth_records", records))
    id_to_idx = {r["record_id"]: i for i, r in enumerate(updated_all)}
    for rec in records[:8]:
        out = write_outcome(rec, ws, horizon_days=14)
        append_record(out)
        if rec["record_id"] in id_to_idx:
            updated_all[id_to_idx[rec["record_id"]]] = out
    st.session_state["growth_records"] = updated_all
    st.success("Outcomes written.")
    st.rerun()

section_kicker("Records with outcomes")
for i, rec in enumerate(st.session_state.get("growth_records", records)[:5]):
    if rec.get("outcome"):
        render_decision_card(rec, key_prefix=f"out_{i}", show_override=False)
