"""
churnOS — Decision-grade analytics for agentic software systems.
Navigation: START → DECIDE → LEARN (+ Reference / Legacy expanders).
"""

import streamlit as st
from pathlib import Path

from core.workspace import get_workspace_from_session
from ui.decision_card import render_decision_card
from ui.explain import how_it_works, measurement_honesty
from ui.magazine import load_magazine_css, masthead, section_kicker
from ui.viz import agentic_health_composite, portfolio_tornado
from ui.workspace_banner import (
    empty_workspace_panel,
    render_sidebar_brand_and_status,
    render_sidebar_secondary_nav,
)

st.set_page_config(page_title="churnOS", layout="wide", initial_sidebar_state="expanded")

css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

def capability_risk_radar():
    from ui.explain import page_help

    load_magazine_css()
    masthead(
        "Capability Risk Radar",
        "What to ship, throttle, or kill",
        "Ranked GrowthDecisionRecords priced by cost of leaving live.",
    )
    page_help("radar", show_card_glossary=True)
    how_it_works(expanded=False)
    measurement_honesty()

    ws = get_workspace_from_session(st.session_state)
    if ws is None:
        empty_workspace_panel(page_label="Radar")
        st.caption("New here? The loop is Profile → Generate → Radar.")
        return

    from analytics.decisions import emit_account_records, emit_capability_records
    from analytics.metrics import resolve_metric

    section_kicker("Agentic Health")
    health_fig = agentic_health_composite(ws)
    if health_fig is not None:
        st.plotly_chart(health_fig, use_container_width=True)
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Health score", resolve_metric("agentic_health_score", ws)["display"])
    h2.metric("CPSO", resolve_metric("cost_per_successful_outcome", ws)["display"])
    h3.metric("TTFV", resolve_metric("time_to_first_value", ws)["display"])
    h4.metric("Unattributed spend", resolve_metric("unattributed_spend_percentage", ws)["display"])

    acc_records = emit_account_records(ws, ws.profile)
    cap_records = emit_capability_records(ws, ws.profile)
    st.session_state["growth_records"] = acc_records + cap_records

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Account GDRs", len(acc_records))
    c2.metric("Capability GDRs", len(cap_records))
    c3.metric("Seats", len(ws.seats))
    c4.metric("Profile", ws.profile.get("preset_id", "—"))

    def _apply_override(rec, action, reason):
        from analytics.decisions import apply_override
        from ontology.store import append_record

        records = st.session_state.get("growth_records") or []
        idx = next(
            (i for i, r in enumerate(records) if r["record_id"] == rec["record_id"]),
            None,
        )
        updated = apply_override(rec, action, reason)
        if idx is not None:
            records[idx] = updated
            st.session_state["growth_records"] = records
        append_record(updated)

    tab_accounts, tab_caps = st.tabs(["Accounts at risk", "Capabilities to act on"])

    with tab_accounts:
        fig = portfolio_tornado(acc_records)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Top {min(8, len(acc_records))} of {len(acc_records)} account decisions — expand a row to act.")
        if not acc_records:
            st.info("No account GDRs for this seed — try regenerating or another preset.")
        for i, rec in enumerate(acc_records[:8]):
            render_decision_card(
                rec,
                key_prefix=f"radar_acc_{i}",
                on_override=_apply_override,
                expanded=(i == 0),
            )

    with tab_caps:
        fig = portfolio_tornado(cap_records)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Top {min(8, len(cap_records))} of {len(cap_records)} capability decisions — expand a row to act.")
        if not cap_records:
            st.info("No capability GDRs for this seed.")
        for i, rec in enumerate(cap_records[:8]):
            render_decision_card(
                rec,
                key_prefix=f"radar_cap_{i}",
                on_override=_apply_override,
                expanded=(i == 0),
            )


_REFERENCE_PAGES = [
    st.Page("pages/7_Concepts.py", title="Concepts", url_path="concepts", visibility="hidden"),
    st.Page("pages/6_README.py", title="Architecture", url_path="architecture", visibility="hidden"),
    st.Page("pages/21_Semantics_Console.py", title="Semantics", url_path="semantics", visibility="hidden"),
    st.Page("pages/22_Taxonomy_Browser.py", title="Taxonomy", url_path="taxonomy", visibility="hidden"),
    st.Page("pages/23_Record_Inspector.py", title="Record Inspector", url_path="records", visibility="hidden"),
]

_LEGACY_PAGES = [
    st.Page("pages/99_Legacy_Index.py", title="Legacy (reference)", url_path="legacy", visibility="hidden"),
    st.Page("pages/0_Business_Model.py", title="Business Model", url_path="legacy_business_model", visibility="hidden"),
    st.Page("pages/1_Retention_Churn.py", title="Retention & Churn", url_path="legacy_retention", visibility="hidden"),
    st.Page("pages/2_Unit_Economics.py", title="Unit Economics", url_path="legacy_unit_economics", visibility="hidden"),
    st.Page("pages/11_Product_Lifecycle.py", title="Lifecycle & NSM", url_path="legacy_lifecycle", visibility="hidden"),
    st.Page("pages/4_Marketplace.py", title="Pricing Analytics", url_path="legacy_pricing", visibility="hidden"),
    st.Page("pages/5_Marketplace_Analytics.py", title="Seller Analytics", url_path="legacy_sellers", visibility="hidden"),
    st.Page("pages/8_ECommerce_Analytics.py", title="RFM & Inventory", url_path="legacy_rfm", visibility="hidden"),
    st.Page("pages/9_Marketplace_Liquidity.py", title="Marketplace Liquidity", url_path="legacy_liquidity", visibility="hidden"),
    st.Page("pages/10_Attribution_MMM.py", title="Attribution & MMM", url_path="legacy_mmm", visibility="hidden"),
    st.Page("pages/12_CRO_Program.py", title="CRO Program", url_path="legacy_cro", visibility="hidden"),
    st.Page("pages/13_Revenue_Leakage.py", title="Revenue Leakage", url_path="legacy_leakage", visibility="hidden"),
    st.Page("pages/14_Conversion_Forecast.py", title="Conversion Forecast", url_path="legacy_forecast", visibility="hidden"),
]

nav_structure = {
    "START": [
        st.Page(
            "pages/00_Agentic_Product_Profile.py",
            title="Product Profile",
            url_path="profile",
            default=True,
        ),
    ],
    "DECIDE": [
        st.Page(capability_risk_radar, title="Radar", url_path="radar"),
        st.Page("pages/15_Activation_Habit.py", title="Activation & Habit", url_path="activation"),
        st.Page("pages/16_Trust_Approval.py", title="Trust & Approval", url_path="trust"),
        st.Page("pages/17_Run_Economics.py", title="Run Economics", url_path="run_economics"),
        st.Page("pages/18_Connector_Blast_Radius.py", title="Connectors", url_path="connectors"),
    ],
    "LEARN": [
        st.Page("pages/3_Conversion.py", title="Experiments", url_path="experiments"),
        st.Page("pages/25_Agentic_Flags.py", title="Agentic Flags", url_path="agentic_flags"),
        st.Page("pages/20_Outcome_Flywheel.py", title="Outcome Flywheel", url_path="flywheel"),
        *_REFERENCE_PAGES,
        *_LEGACY_PAGES,
    ],
}

pg = st.navigation(nav_structure, expanded=True)
render_sidebar_brand_and_status(st.session_state)
render_sidebar_secondary_nav()
pg.run()
