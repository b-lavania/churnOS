"""Canvas runtime loop stepper — Profile → Warehouse → Classify → Rules → GDR → Radar → Flywheel."""

from __future__ import annotations

from typing import Any

import streamlit as st

from core.workspace import get_workspace_from_session

LOOP_STEPS: list[tuple[str, str]] = [
    ("profile", "Profile"),
    ("warehouse", "Warehouse"),
    ("classify", "Classify"),
    ("rules", "YAML rules"),
    ("gdr", "GDR"),
    ("radar", "Radar"),
    ("flywheel", "Flywheel"),
]


def _step_states(session_state: Any) -> dict[str, str]:
    """Return per-step status: done | current | blocked."""
    ws = get_workspace_from_session(session_state)
    records = session_state.get("growth_records") or []
    has_outcome = any(r.get("outcome") for r in records)

    states: dict[str, str] = {}
    if ws is None:
        states["profile"] = "current" if not session_state.get("agentic_profile") else "done"
        for sid, _ in LOOP_STEPS[1:]:
            states[sid] = "blocked"
        if session_state.get("agentic_profile"):
            states["profile"] = "done"
            states["warehouse"] = "current"
        return states

    states["profile"] = "done"
    states["warehouse"] = "done"
    if not records:
        states["classify"] = "current"
        states["rules"] = "blocked"
        states["gdr"] = "blocked"
        states["radar"] = "blocked"
        states["flywheel"] = "blocked"
        return states

    states["classify"] = "done"
    states["rules"] = "done"
    states["gdr"] = "done"
    states["radar"] = "current"
    states["flywheel"] = "done" if has_outcome else "blocked"
    return states


def render_loop_stepper(session_state: Any, *, highlight: str | None = None) -> None:
    """Sidebar loop progress strip."""
    states = _step_states(session_state)
    if highlight:
        for sid, _ in LOOP_STEPS:
            if sid == highlight:
                states[sid] = "current"
            elif states.get(sid) == "current" and sid != highlight:
                states[sid] = "done"

    parts: list[str] = []
    for i, (sid, label) in enumerate(LOOP_STEPS):
        status = states.get(sid, "blocked")
        cls = f"mag-loop-step mag-loop-step--{status}"
        parts.append(f'<span class="{cls}" title="{label}">{label}</span>')
        if i < len(LOOP_STEPS) - 1:
            flyback = ' mag-loop-arrow--flyback' if sid == "flywheel" else ""
            parts.append(f'<span class="mag-loop-arrow{flyback}">→</span>')

    st.markdown(
        f'<div class="mag-loop-stepper" aria-label="Runtime loop">{" ".join(parts)}</div>',
        unsafe_allow_html=True,
    )
