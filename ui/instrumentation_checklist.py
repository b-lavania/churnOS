"""Phase 0 instrumentation checklist (synthetic honesty)."""

from __future__ import annotations

import streamlit as st

from core.workspace import Workspace

CHECKLIST = [
    ("account_id on every run", "Runs carry account_id / seat join to billing identity"),
    ("Agent version on trace", "capability_version_id + config hash on runs"),
    ("Outcome events emitted", "outcomes table with success + agent_run_id"),
    ("Outcomes linked to runs", "agent_run_id FK on outcomes"),
    ("Eligible task count", "delegation_ratio computable from seats + runs"),
    ("Cost per run", "run_cost_usd on agent runs"),
]


def render_instrumentation_checklist(ws: Workspace | None) -> None:
    st.markdown("**Instrumentation checklist (Phase 0)**")
    if ws is None:
        for label, _ in CHECKLIST:
            st.checkbox(label, value=False, disabled=True)
        st.caption("Generate workspace to see synthetic pass state.")
        return

    for label, hint in CHECKLIST:
        passed = True
        if "outcomes" in label.lower() and getattr(ws, "outcomes", None) is not None:
            passed = len(ws.outcomes) > 0
        if "cost" in label.lower():
            passed = not ws.runs.empty and "run_cost_usd" in ws.runs.columns
        st.checkbox(f"{label} — _{hint}_", value=passed, disabled=True)
    st.caption(
        "Synthetic warehouse passes all boxes for demo. Real products must emit these events — "
        "see docs/honesty.md."
    )
