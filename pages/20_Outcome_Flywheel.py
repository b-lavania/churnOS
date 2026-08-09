"""Outcome Flywheel — close the loop on GDR decisions."""

from pathlib import Path

import streamlit as st

from analytics.decisions import flywheel_evaluation, propose_action, write_outcome
from analytics.metrics import resolve_metric
from core.workspace import ensure_growth_records
from ontology.semantics import load_semantics
from ontology.store import append_record
from ui.decision_card import render_decision_card
from ui.explain import page_help
from ui.loop_chrome import render_loop_stepper
from ui.magazine import load_magazine_css, masthead, section_kicker
from ui.viz import flywheel_comparison_chart
from ui.workspace_banner import require_workspace

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead("Learn", "Outcome Flywheel", "Decisions awaiting outcome → write-back → intervention effectiveness.")
page_help("flywheel", show_card_glossary=True)
render_loop_stepper(st.session_state, highlight="flywheel")

ws = require_workspace(st.session_state, page_label="Outcome Flywheel")
records = ensure_growth_records(st.session_state, ws)

awaiting = [r for r in records if not r.get("outcome")]
section_kicker("Decisions awaiting outcome")
st.caption(f"**{len(awaiting)}** of {len(records)} records need outcome write-back.")

if awaiting:
    for i, rec in enumerate(awaiting[:5]):
        render_decision_card(rec, key_prefix=f"await_{i}", show_override=False, expanded=(i == 0))
    if st.button("Simulate 14d outcome for top 8 awaiting", type="primary"):
        updated_all = list(st.session_state.get("growth_records", records))
        id_to_idx = {r["record_id"]: i for i, r in enumerate(updated_all)}
        for rec in awaiting[:8]:
            out = write_outcome(rec, ws, horizon_days=14)
            append_record(out)
            if rec["record_id"] in id_to_idx:
                updated_all[id_to_idx[rec["record_id"]]] = out
        st.session_state["growth_records"] = updated_all
        st.success("Outcomes written.")
        st.rerun()
else:
    st.success("All records have outcomes — regenerate or override on Radar for new decisions.")

section_kicker("Followed vs overridden")
summary = flywheel_evaluation(records)
fig = flywheel_comparison_chart(summary)
if fig is not None:
    st.plotly_chart(fig, use_container_width=True)
causal = summary.get("causal_impact") or {}
if causal.get("effect_pp") is not None:
    from ui.evidence_chrome import render_claim_badge

    st.markdown("#### Incrementality (teaching)")
    render_claim_badge(causal.get("claim_type", "simulated"))
    st.info(causal.get("message", ""))
    if causal.get("ci95"):
        st.caption(f"95% band: {causal['ci95'][0]:+.1%} to {causal['ci95'][1]:+.1%}")
if summary.get("n"):
    st.table({
        "cohort": ["Followed recommendation", "Overridden"],
        "count": [summary["followed"]["count"], summary["overridden"]["count"]],
        "retention Δ 14d": [summary["followed"]["retention_delta_14d"], summary["overridden"]["retention_delta_14d"]],
        "delegation": [summary["followed"]["delegation_rate"], summary["overridden"]["delegation_rate"]],
        "churn rate": [summary["followed"]["churn_rate"], summary["overridden"]["churn_rate"]],
    })

with st.expander("Charts & agent stub", expanded=False):
    from ui.viz import coordination_overhead_chart, retention_feature_importance, success_vs_complexity

    c1, c2, c3 = st.columns(3)
    c1.metric("Verified success rate", resolve_metric("verified_outcome_success_rate", ws)["display"])
    c2.metric("Coordination overhead", resolve_metric("coordination_overhead", ws)["display"])
    c3.metric("Outcome drift WoW", resolve_metric("outcome_success_drift", ws)["display"])
    fig_sc = success_vs_complexity(ws)
    if fig_sc is not None:
        st.plotly_chart(fig_sc, use_container_width=True)
    if records:
        sem = load_semantics(ws.profile.get("ontology_vertical", "capability_lifecycle"))
        action, rationale = propose_action(records[0], sem)
        st.caption(f"Agent stub: **{action}** — {rationale}")

section_kicker("Records with outcomes")
for i, rec in enumerate(st.session_state.get("growth_records", records)[:5]):
    if rec.get("outcome"):
        render_decision_card(rec, key_prefix=f"out_{i}", show_override=False)

st.caption("Return to **Radar** from the sidebar after writing outcomes.")
