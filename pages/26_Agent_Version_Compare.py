"""Agent Version Comparison — SPRT + rollback / monitor / ship."""

from pathlib import Path

import streamlit as st

from analytics.agent_version_compare import compare_agent_versions
from analytics.decisions import emit_capability_records
from ontology.exception_taxonomy import ACTIONS
from ui.evidence_chrome import render_underpowered_callout
from ui.explain import page_help
from ui.magazine import load_magazine_css, masthead, section_kicker
from ui.workspace_banner import require_workspace

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead(
    "Decide",
    "Agent Version Comparison",
    "Should you roll back the latest agent version?",
)
page_help("experiments")

ws = require_workspace(st.session_state, page_label="Agent Version Comparison")
cmp = compare_agent_versions(ws)

section_kicker("Version comparison")
st.caption(f"Previous: `{cmp.get('previous_version', '—')}` · Current: `{cmp.get('current_version', '—')}`")

lights = {"red": "🔴", "green": "🟢", "yellow": "🟡", "grey": "⚪"}
tl = cmp.get("traffic_light", "yellow")
st.markdown(f"### {lights.get(tl, '🟡')} {cmp.get('recommendation', 'hold').upper()}")

if cmp.get("rows"):
    st.dataframe(cmp["rows"], use_container_width=True, hide_index=True)
else:
    st.info("Not enough version history on this seed.")

rec = cmp.get("recommendation", "hold")
st.markdown(f"**Recommendation:** `{rec}` — {cmp.get('reason', '')}")

sprt = cmp.get("sprt") or {}
with st.expander("Evidence vs peeking (sequential test)", expanded=False):
    if sprt:
        st.write(
            f"SPRT decision: **{sprt.get('decision')}** · LLR {sprt.get('llr')} "
            f"(bounds {sprt.get('boundary_lower')} to {sprt.get('boundary_upper')}) · "
            f"n={sprt.get('n_total')}"
        )
    if cmp.get("p_value") is not None:
        st.caption(f"Fixed-n two-proportion z-test p-value: {cmp['p_value']:.4f} (peeking inflates false positives)")
    if cmp.get("recommendation") == "hold":
        render_underpowered_callout(
            cmp.get("n_curr", 0) + cmp.get("n_prev", 0),
            60,
        )

with st.expander("Traffic allocation (Thompson sampling — teaching)", expanded=False):
    from analytics.bandits import thompson_allocation

    caps = ws.capabilities["capability_id"].tolist() if not ws.capabilities.empty else []
    if caps:
        cap_pick = st.selectbox("Capability", caps, key="bandit_cap")
        alloc = thompson_allocation(ws, cap_pick)
        if alloc.get("recommended_traffic"):
            st.write(alloc["recommended_traffic"])
            st.caption(alloc.get("message", ""))

section_kicker("Emit capability GDR from recommendation")
overlay = st.session_state.get("semantics_overlay")
if st.button("Emit version decision record"):
    recs = emit_capability_records(ws, ws.profile, semantics_overlay=overlay)
    if recs:
        top = dict(recs[0])
        action = rec if rec in ACTIONS else "hold"
        top["decision"] = dict(top["decision"])
        top["decision"]["recommended_action"] = action
        top["decision"]["final_action"] = action
        st.session_state.setdefault("growth_records", []).insert(0, top)
        st.success(f"GDR updated with version recommendation: {action}")
    else:
        st.warning("No capability GDRs to attach recommendation.")
