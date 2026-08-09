"""In-app explainers — how churnOS works and what numbers mean."""

from __future__ import annotations

import streamlit as st

from ui.magazine import load_magazine_css, section_kicker

# Surface-specific one-liners for DECISIONS pages
SURFACE_EXPLAINERS: dict[str, dict[str, str]] = {
    "radar": {
        "title": "What this screen is",
        "body": (
            "The weekly meeting, rendered. Each card is a **GrowthDecisionRecord** for one "
            "capability (skill, automation, agent tool): what’s wrong, what it may cost to "
            "leave live, and what to do. Numbers come from the synthetic workspace — not "
            "production agents — until you connect real event data."
        ),
    },
    "profile": {
        "title": "What this screen is",
        "body": (
            "Pick a product shape — personal assistant, CRM workspace, ops missions, "
            "or metered agent API. That choice switches ontology semantics and the "
            "**fake** rates used to generate seats, runs, approvals, and churn. "
            "Press **Generate workspace** before any other screen has data."
        ),
    },
    "activation": {
        "title": "What this measures",
        "body": (
            "**Activation** = share of seats that got a first trusted successful run. "
            "**Weekly delegation habit** (your OEC) = among activated seats, share that "
            "keep running successfully each week. Cards here filter for activation leaks "
            "and habit collapse only."
        ),
    },
    "trust": {
        "title": "What this measures",
        "body": (
            "**Trust incidents** = runs flagged as scary/wrong (`trust_flag`). "
            "**Dismiss rate** = humans rejecting agent proposals — high dismiss often means "
            "approval fatigue or low trust. Cards filter for `trust_break` and `approval_fatigue`."
        ),
    },
    "run_economics": {
        "title": "What this measures",
        "body": (
            "**$/successful run** vs **seat ARPU** — if run cost eats willingness to pay, "
            "the capability is uneconomic even if users like it. Cards filter for "
            "`run_cost_blowout` and CAC/LTV-style contradictions."
        ),
    },
    "connector": {
        "title": "What this measures",
        "body": (
            "Tool/integration failures (Gmail, HubSpot, MCP, etc.) that block jobs-to-be-done. "
            "Blast radius = how many capabilities depend on a fragile connector. "
            "Cards filter for `connector_fragility`."
        ),
    },
    "flywheel": {
        "title": "What this measures",
        "body": (
            "After you decide (ship / hold / throttle…), write back **retention Δ** and "
            "**churn happened** onto the record. Today this is a **simulated** 14-day "
            "write-back on synthetic seats — it demos the closed loop, not real causality."
        ),
    },
    "semantics": {
        "title": "What this is",
        "body": (
            "Agent-readable glossary **and** governing rules (`semantics.yaml`): "
            "verdict rules, action maps, and classification thresholds. "
            "Edit sample values in YAML → regenerate workspace → Radar decisions change. "
            "Not a dashboard — the policy layer agents and humans share."
        ),
    },
    "taxonomy": {
        "title": "What this is",
        "body": (
            "Exception categories (activation leak, trust break, …), owners, and playbook "
            "hints. Taxonomy first, then semantics, then schema — the ontology recipe."
        ),
    },
    "inspector": {
        "title": "What this is",
        "body": (
            "Raw `GrowthDecisionRecord` inspection: validate against schema, override "
            "actions, see JSONL persistence. Audit surface for the decision object."
        ),
    },
    "concepts": {
        "title": "What this is",
        "body": (
            "Human-facing playbook compiled from ontology semantics + the governed metric "
            "lexicon. Same meanings as agents get — not a separate encyclopedia."
        ),
    },
}

VERDICT_GLOSS = {
    "healthy": "No ranked exceptions above threshold — safe to keep shipping.",
    "leaking": "Activation or habit problems — value unfinished for many seats.",
    "destructive": "Usage correlates with churn / trust damage — throttle or rollback.",
    "uneconomic": "Run cost or growth economics break policy even if UX looks fine.",
    "underpowered": "Signal exists but not decision-grade yet — hold and gather evidence.",
    "needs_review": "Low confidence — a human should confirm before acting.",
}

ACTION_GLOSS = {
    "ship": "Promote / raise traffic.",
    "hold": "Freeze rollout; gather evidence.",
    "throttle": "Cap % traffic, rate, or tool budget.",
    "shadow": "Run offline / no user-visible side effects.",
    "rollback": "Revert to last known-good version.",
    "kill": "Remove from the product surface.",
    "experiment": "Force a governed test before further ship.",
    "revise": "Change prompt/tool/policy; re-enter eval.",
}

FIELD_GLOSS = [
    ("Verdict", "Engine’s state call on this capability (see glossary below)."),
    ("Capability ID", "The shippable unit: skill, automation, agent, or tool policy."),
    ("Cost of leaving live", "Teaching estimate of $ at risk if you do nothing this window."),
    ("Exceptions", "Ranked reasons — activation leak, trust break, cost blowout, etc."),
    ("Recommended / Final", "What the engine suggests vs what you chose (override)."),
    ("Outcome", "Later write-back: retention Δ and whether churn happened (simulated today)."),
]


def synthetic_notice() -> None:
    """Persistent honesty banner: demo warehouse, not production."""
    load_magazine_css()
    st.markdown(
        """
        <div class="mag-notice">
            <span class="mag-notice-kicker">Synthetic demo</span>
            <span class="mag-notice-body">
                Numbers come from an authored warehouse (profile priors), not live product
                telemetry. Use this to learn the decision loop — not to certify production forecasts.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def surface_explainer(surface_key: str, *, expanded: bool = False) -> None:
    """Short ‘what this screen is / measures’ expander."""
    spec = SURFACE_EXPLAINERS.get(surface_key)
    if not spec:
        return
    with st.expander(spec["title"], expanded=expanded):
        st.markdown(spec["body"])


def how_it_works(*, expanded: bool = True) -> None:
    """Full product loop — primarily on Radar home."""
    with st.expander("How churnOS works (read this first)", expanded=expanded):
        st.markdown(
            """
**One loop**

1. **Agentic Product Profile** — pick product shape → sets ontology + fake rates  
2. **Generate workspace** — seats, capabilities, runs, approvals, connectors, churn marks  
3. **Decision engine** — finds exceptions per capability, prices *cost of leaving live*  
4. **This Radar** — ranked Decision Cards → you override ship / hold / throttle…  
5. **Outcome Flywheel** — write retention Δ / churn back onto the record (simulated)

**What is real vs demo**

| Real (the IP) | Demo today |
| --- | --- |
| Decision object, taxonomy, semantics | Synthetic seats & runs |
| Exception categories & playbooks | Authored correlation structure |
| Override → outcome flywheel pattern | Fake 14d retention / churn labels |

**Sidebar map**

- **START** — Product Profile (pick preset → generate workspace)  
- **DECIDE** — Radar + filtered decision surfaces (activation, trust, cost, connectors)  
- **LEARN** — Experiments + Outcome Flywheel (close the loop)  
- **Reference** (collapsed) — Concepts, Architecture, Semantics, Taxonomy, Record Inspector  
- **Legacy** (collapsed) — Pre-agentic ecomm / marketplace modules
            """
        )


def decision_card_glossary(*, expanded: bool = False) -> None:
    """Plain-English meanings for card fields, verdicts, actions."""
    with st.expander("How to read a Decision Card", expanded=expanded):
        section_kicker("Card fields")
        for name, meaning in FIELD_GLOSS:
            st.markdown(f"**{name}** — {meaning}")
        section_kicker("Verdicts")
        for k, v in VERDICT_GLOSS.items():
            st.markdown(f"**`{k}`** — {v}")
        section_kicker("Actions")
        for k, v in ACTION_GLOSS.items():
            st.markdown(f"**`{k}`** — {v}")
        st.caption(
            "`capability_harm` is associational unless an experiment is attached — "
            "not automatic causal proof. **`p_churn_30d`** is calibrated 30-day churn "
            "probability (rigorous math_mode). **`uplift_pp`** is treatment effect when experiment_id present."
        )


def measurement_honesty() -> None:
    """Compact table: helps think vs measures production."""
    with st.expander("Does this measure what’s really going on?"):
        st.markdown(
            """
**Yes, as a model of what agentic products should measure**

- First trusted successful run (activation)  
- Weekly delegation habit (north-star / OEC)  
- Approval fatigue & trust incidents  
- $/successful run vs seat ARPU  
- Connector failures blocking jobs  

**No, as live instrumentation (yet)**

- No Lindy / Dench / Invice / your-product ingest  
- Harm scores are teaching correlations, not causal proof  
- Seat Retention / Unit Economics pages are still partly the old purchase story  
- Outcome write-back is simulated for the portfolio demo  

The durable idea: ranked, dollar-weighted judgments with human override and outcome feedback — not another vanity dashboard.
            """
        )


def page_help(surface_key: str, *, show_notice: bool = True, show_card_glossary: bool = False) -> None:
    """Standard chrome: notice + surface explainer (+ optional card glossary)."""
    if show_notice:
        synthetic_notice()
    surface_explainer(surface_key, expanded=False)
    if show_card_glossary:
        decision_card_glossary(expanded=False)
