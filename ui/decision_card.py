"""Magazine-style Decision Card component."""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from ontology.exception_taxonomy import ACTIONS, CATEGORIES
from ui.explain import ACTION_GLOSS, VERDICT_GLOSS
from ui.magazine import load_magazine_css


def _evidence_line(record: dict[str, Any]) -> str:
    """Human-readable evidence hint from exception impacts / counts."""
    excs = record.get("exceptions", [])
    n = len(excs)
    cats = ", ".join(sorted({e.get("category", "") for e in excs if e.get("category")})[:3])
    verdict = record.get("decision", {}).get("verdict", "")
    gloss = VERDICT_GLOSS.get(verdict, "")
    parts = [f"{n} exception(s)"]
    if cats:
        parts.append(cats)
    if gloss:
        return f"{' · '.join(parts)} — {gloss}"
    return " · ".join(parts)


def render_decision_card(
    record: dict[str, Any],
    *,
    key_prefix: str = "card",
    on_override: Callable[[dict, str, str], None] | None = None,
    show_override: bool = True,
    expanded: bool = False,
) -> None:
    """Render one GDR as a single expandable row — not a stack of section headers."""
    load_magazine_css()
    decision = record.get("decision", {})
    economics = record.get("economics", {})
    subject = record.get("subject", {})
    verdict = decision.get("verdict", "unknown")
    cost = economics.get("primary_metric_usd", 0)
    entity_type = subject.get("entity_type", "capability")
    cap_id = subject.get("capability_id", "—")
    acc_id = subject.get("account_id", "—")
    cap_ver = subject.get("capability_version", "—")
    rec_action = decision.get("recommended_action", "hold")
    excs = record.get("exceptions", [])

    if entity_type == "account":
        title = acc_id
        meta_line = f"Account · {record.get('vertical', '')}"
    else:
        title = cap_id
        meta_line = f"Version {cap_ver} · Capability · {record.get('vertical', '')}"

    summary = (
        f"{title}  ·  {verdict}  ·  ${cost:,.0f}  ·  "
        f"{rec_action}  ·  {len(excs)} exceptions"
    )
    with st.expander(summary, expanded=expanded):
        st.markdown(
            f"""
            <article class="mag-decision-card mag-decision-card--compact">
                <p class="mag-kicker">{entity_type.upper()} · {verdict.upper()}</p>
                <h2 class="mag-card-title">{title}</h2>
                <p class="mag-card-meta">{meta_line}</p>
                <p class="mag-evidence">{_evidence_line(record)}</p>
                <p class="mag-card-deck">{decision.get('rationale', '')}</p>
                <p class="mag-card-cost">${cost:,.0f}</p>
                <p class="mag-card-cost-label">Cost of leaving live
                  <span style="font-weight:400; text-transform:none; letter-spacing:0;">
                  — teaching estimate if you do nothing</span>
                </p>
            </article>
            """,
            unsafe_allow_html=True,
        )

        if excs:
            chips = []
            total_impact = sum(e.get("impact", {}).get("cost_usd", 0) for e in excs) or 1
            for exc in excs[:6]:
                cat = exc.get("category", "")
                impact = exc.get("impact", {}).get("cost_usd", 0)
                pct = min(100, int(impact / total_impact * 100))
                chips.append(f"`{cat}` {pct}%")
            st.caption("Evidence · " + (" · ".join(chips) if chips else "none"))

            viz = record.get("viz")
            if viz:
                with st.expander("Visual receipt", expanded=False):
                    st.json(viz)

            st.markdown("**Exceptions** (highest $ impact first)")
            for exc in excs[:5]:
                impact = exc.get("impact", {}).get("cost_usd", 0)
                cat = exc.get("category", "")
                hint = CATEGORIES.get(cat, {}).get("playbook_hint", "")
                st.markdown(
                    f"- **`{cat}`** — {exc.get('title', '')} "
                    f"(${impact:,.0f})"
                    + (f"  \n  _{hint}_" if hint else "")
                )

        if show_override and on_override:
            st.caption(
                f"Recommended: **{rec_action}** — "
                f"{ACTION_GLOSS.get(rec_action, 'Engine suggestion')}"
            )
            final = st.selectbox(
                "Final action",
                ACTIONS,
                index=ACTIONS.index(decision.get("final_action", rec_action))
                if decision.get("final_action") in ACTIONS
                else (ACTIONS.index(rec_action) if rec_action in ACTIONS else 0),
                format_func=lambda a: f"{a} — {ACTION_GLOSS.get(a, '')}",
                key=f"{key_prefix}_action_{record['record_id']}",
            )
            reason = ""
            if final != rec_action:
                reason = st.text_input(
                    "Override reason (required when you disagree)",
                    key=f"{key_prefix}_reason_{record['record_id']}",
                    help="Logged on the record without re-running classification.",
                )
            if st.button("Apply decision", key=f"{key_prefix}_apply_{record['record_id']}"):
                if final != rec_action and not reason.strip():
                    st.error("Override reason required when final ≠ recommended.")
                else:
                    on_override(record, final, reason or "")
                    st.success("Decision recorded (session + JSONL store).")

        outcome = record.get("outcome")
        if outcome:
            st.caption(
                f"Outcome — Retention Δ (14d): {outcome.get('retention_delta_14d')} · "
                f"Churn happened: {outcome.get('churn_happened')}"
            )
