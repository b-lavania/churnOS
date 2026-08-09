"""Semantics Console — policy playground + governing rules."""

from pathlib import Path

import streamlit as st
import yaml

from analytics.account_risk import enrich_account_records
from analytics.decisions import emit_account_records, emit_capability_records
from analytics.evidence import is_rigorous_mode
from core.workspace import get_workspace_from_session
from ontology.semantics import load_semantics
from ui.explain import page_help
from ui.loop_chrome import render_loop_stepper
from ui.magazine import load_magazine_css, masthead, section_kicker
from ui.workspace_banner import require_workspace

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead(
    "Ontology",
    "Semantics Console",
    "Edit policy in-session → reclassify → Radar updates.",
)
page_help("semantics")
render_loop_stepper(st.session_state, highlight="rules")

ws = get_workspace_from_session(st.session_state)
vertical = ws.profile.get("ontology_vertical", "capability_lifecycle") if ws else "capability_lifecycle"
base_sem = load_semantics(vertical)

section_kicker("Policy playground (session overlay)")
st.caption("Changes apply to this session only — not written to disk.")

destructive_action = st.selectbox(
    "destructive → recommended_action",
    ["rollback", "throttle", "shadow", "kill", "hold"],
    index=0,
)
harm_min = st.slider(
    "capability_harm harm_score_min",
    0.02, 0.20,
    float(base_sem.get("classification", {}).get("thresholds", {}).get("capability_harm", {}).get("harm_score_min", 0.08)),
    0.01,
)

show_rigorous = st.checkbox(
    "Rigorous posterior thresholds",
    value=ws is not None and is_rigorous_mode(ws.profile),
)
p_churn_min = 0.5
p_uplift_min = 0.8
if show_rigorous:
    p_churn_min = st.slider("P(churn_30d) destructive threshold", 0.1, 0.9, 0.5, 0.05)
    p_uplift_min = st.slider("P(uplift harm) destructive threshold (causal only)", 0.5, 0.99, 0.8, 0.05)

overlay = {
    "decision": {
        "action_map": {
            "destructive": {"recommended_action": destructive_action},
        },
    },
    "classification": {
        "thresholds": {
            "capability_harm": {"harm_score_min": harm_min},
        },
    },
}
if show_rigorous:
    overlay["classification"]["posterior_thresholds"] = {
        "p_churn_30d_min": p_churn_min,
        "p_uplift_churn_min": p_uplift_min,
    }

if st.button("Apply overlay & reclassify", type="primary"):
    st.session_state["semantics_overlay"] = overlay
    if ws:
        profile_heur = dict(ws.profile)
        profile_heur.setdefault("priors", {})["math_mode"] = "heuristic"
        profile_rig = dict(ws.profile)
        profile_rig.setdefault("priors", {})["math_mode"] = "rigorous"

        before_cap = emit_capability_records(ws, profile_heur, semantics_overlay=overlay)
        after_cap = emit_capability_records(ws, profile_rig, semantics_overlay=overlay)
        changed_cap = sum(
            1 for b, a in zip(before_cap, after_cap)
            if b.get("decision", {}).get("verdict") != a.get("decision", {}).get("verdict")
            or b.get("decision", {}).get("recommended_action") != a.get("decision", {}).get("recommended_action")
        )

        before_acc = enrich_account_records(emit_account_records(ws, profile_heur, semantics_overlay=overlay), ws)
        after_acc = enrich_account_records(emit_account_records(ws, profile_rig, semantics_overlay=overlay), ws)

        st.session_state["growth_records"] = []
        st.success(f"Overlay applied. {changed_cap} capability GDR(s) changed verdict/action. Open Radar.")

        section_kicker("Heuristic vs rigorous (sample)")
        rows = []
        for b, a in zip(before_cap[:8], after_cap[:8]):
            exc_b = b.get("exceptions", [{}])[0] if b.get("exceptions") else {}
            rows.append({
                "Entity": b.get("subject", {}).get("capability_id", "—"),
                "Heuristic verdict": b.get("decision", {}).get("verdict"),
                "Rigorous verdict": a.get("decision", {}).get("verdict"),
                "Heuristic action": b.get("decision", {}).get("recommended_action"),
                "Rigorous action": a.get("decision", {}).get("recommended_action"),
                "Claim": (exc_b.get("evidence") or {}).get("claim_type", "—"),
            })
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        if before_acc and after_acc:
            st.caption("Account sample (first record)")
            st.write(
                f"Heuristic risk: {before_acc[0].get('risk_score')} → "
                f"Rigorous P(churn_30d): {after_acc[0].get('p_churn_30d')}"
            )
    else:
        st.success("Overlay saved — generate workspace then open Radar.")

if st.session_state.get("semantics_overlay"):
    with st.expander("Active session overlay"):
        st.code(yaml.dump(st.session_state["semantics_overlay"], default_flow_style=False), language="yaml")
    if st.button("Clear overlay"):
        st.session_state.pop("semantics_overlay", None)
        st.session_state["growth_records"] = []
        st.rerun()

section_kicker(f"Base semantics — {vertical}")
decision = base_sem.get("decision", {})
if decision:
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Verdict rules")
        st.code(yaml.dump(decision.get("verdict_rules", []), default_flow_style=False), language="yaml")
    with col2:
        st.caption("Action map")
        st.code(yaml.dump(decision.get("action_map", {}), default_flow_style=False), language="yaml")
