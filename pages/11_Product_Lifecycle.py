"""
Product lifecycle scorecard: acquisition → activation → monetization proxies.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

from analytics.product_metrics import (
    activation_and_ttf_metrics,
    cohort_event_adoption,
    cohort_signups_by_month,
    inter_purchase_gap_distribution,
    purchase_dau_over_wau_proxy,
    refund_exposure_rates,
    sessionize_product_events,
    signup_momentum_latest_vs_prior_month,
)
from analytics.retention import cohort_retention_matrix
from ui.journey import require_workspace
from analytics.journeys import event_funnel, DEFAULT_JOURNEY_STEPS

st.set_page_config(page_title="Product Lifecycle", layout="wide")

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

PLOTLY_THEME = {
    "layout": {
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "JetBrains Mono", "color": "#94a3b8", "size": 11},
        "xaxis": {"gridcolor": "rgba(255,255,255,0.05)", "zeroline": False, "linecolor": "rgba(255,255,255,0.1)"},
        "yaxis": {"gridcolor": "rgba(255,255,255,0.05)", "zeroline": False, "linecolor": "rgba(255,255,255,0.1)"},
        "margin": {"t": 40, "b": 40, "l": 40, "r": 20},
    }
}

st.markdown('<div class="terminal-header">PRODUCT // LIFECYCLE & NSM PROXIES</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Product Analytics Scorecard</h1>', unsafe_allow_html=True)

if "model" not in st.session_state:
    st.warning("No model defined. Go to **Business Model** to configure your business first.")
    st.stop()

ws = require_workspace("lifecycle")
if ws is None:
    st.stop()

s = st.session_state["model_summary"]
config = st.session_state["model_config"]

with st.expander("Metric definitions (read me first)"):
    st.markdown(
        """
        **North Star proxies** here combine signup cohorts, purchase-qualified activation windows, and behavioural events.
        They are deliberately honest: purchase cadence proxies are **not authenticated product DAU** without client telemetry.
        """
    )
    st.markdown(
        """
        - **Acquisition:** signup counts by calendar cohort month (`customers`).
        - **Activation:** share of cohort whose first qualifying order (`net_revenue > 0`) lands inside `{7,14,28}` days of signup.
        - **Retention triangle:** transactional presence reuse of `cohort_retention_matrix`.
        - **Monetisation + guardrails:** order density, refunds, discounted mix, causal summary from `Business Model`.
        - **Stickiness analogue:** intra-week purchaser concentration—a purchase-based DAU/WAU substitute.
        """
    )


cust = ws.customers
tx = ws.transactions
events = ws.product_events

cohort_signups = cohort_signups_by_month(cust)
act = activation_and_ttf_metrics(cust, tx)
stick = purchase_dau_over_wau_proxy(tx)
gaps = inter_purchase_gap_distribution(tx)
refunds = refund_exposure_rates(tx)
mom = signup_momentum_latest_vs_prior_month(cohort_signups)

ret_matrix = cohort_retention_matrix(tx, cust)
gap_min = st.sidebar.slider(
    "Behavioural session idle gap (minutes)",
    min_value=5,
    max_value=180,
    value=30,
    step=5,
    key="sess_gap_help",
)

sess_events = sessionize_product_events(events, gap_minutes=int(gap_min))

tab_score, tab_journeys, tab_inst, tab_model = st.tabs(
    ["[01] Scorecard", "[02] Journeys", "[03] Instrumentation", "[04] Causal tie-in"]
)

with tab_score:
    st.markdown('<div class="terminal-header">ACQUISITION // MONTHLY SIGNUPS</div>', unsafe_allow_html=True)
    cc1, cc2, cc3 = st.columns(3)
    dv = mom.get("delta_pct")
    cc1.metric("Latest vs prior cohort MoM Δ", "—" if dv is None or pd.isna(dv) else f"{dv:+.2f}%")
    cc2.metric("Latest month", str(mom.get("latest_month") or "—"))
    cc3.metric("Prior month", str(mom.get("prior_month") or "—"))

    fig_c = px.bar(cohort_signups, x="cohort_month", y="signups", color_discrete_sequence=["#00f2ff"])
    fig_c.update_layout(**PLOTLY_THEME["layout"])
    fig_c.update_xaxes(title="Signup cohort")
    fig_c.update_yaxes(title="Customers signed")
    fig_c.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_c, use_container_width=True)

    st.markdown('<div class="terminal-header">ACTIVATION // QUALIFIED FIRST PURCHASE</div>', unsafe_allow_html=True)
    aa1, aa2, aa3, aa4 = st.columns(4)
    aa1.metric("Median days → 1st order", str(act["median_days_to_first_purchase"] or "—"))
    aa2.metric("Median days → 2nd order", str(act["median_days_to_second_order_from_signup"] or "—"))
    aa3.metric("Activated ≤7d", f"{act.get('pct_first_order_within_7d', 0)}%")
    aa4.metric("Activated ≤28d", f"{act.get('pct_first_order_within_28d', 0)}%")

    st.markdown('<div class="terminal-header">RETENTION // TRANSACTION COHORT HEATMAP</div>', unsafe_allow_html=True)
    hm = ret_matrix.astype(float).T
    heat = px.imshow(
        hm,
        labels=dict(x="Signup cohort month", y="Months since signup", color="Retention %"),
        aspect="auto",
        color_continuous_scale=["#020617", "#14b8a6", "#ffe29d"],
        zmin=0,
        zmax=100,
    )
    heat.update_layout(**PLOTLY_THEME["layout"])
    heat.update_layout(yaxis=dict(autorange="reversed"))
    heat.update_xaxes(side="bottom", tickangle=-45)
    st.plotly_chart(heat, use_container_width=True)

    st.caption(
        "Triangle counts unique purchasing customers within each signup cohort × elapsed month—not subscription invoice churn."
    )

    st.markdown('<div class="terminal-header">MONETISATION GUARDRAILS</div>', unsafe_allow_html=True)
    monet = act.get("monetization") or {}

    mq1, mq2, mq3, mq4, mq5 = st.columns(5)
    mq1.metric("Orders / buyer", f"{monet.get('orders_per_buyer', 0):.3f}")
    mq2.metric("Pct discounted orders", f"{monet.get('pct_orders_discounted', 0):.2f}%")

    rr = refunds.get("refund_rate_all_orders_pct")
    if rr is None or (isinstance(rr, float) and pd.isna(rr)):
        mq3.metric("Refund rate", "—")
    else:
        mq3.metric("Refund rate", f"{rr}%")
    mq4.metric(
        "Margin ÷ revenue",
        f"{monet['margin_over_revenue_pct']}%"
        if monet.get("margin_over_revenue_pct") is not None
        else "—",
    )
    mq5.metric("Pct never ordered", f"{act.get('pct_never_ordered', 0)}%")

    st.markdown('<div class="terminal-header">PURCHASE STICKINESS ANALOGUE</div>', unsafe_allow_html=True)
    mr = stick.get("mean_ratio")
    st.write(
        f"**Analogue ratio** `{mr}` across `{stick.get('weeks_observed', 0)}` ISO-weeks observed — "
        f"{stick.get('definition', '')}."
    )
    st.write(
        f"**Inter-purchase gap** • median `{gaps.get('median_gap_days')}` days • "
        f"IQR `{gaps.get('q25_gap_days')}`–`{gaps.get('q75_gap_days')}` • `{gaps.get('n_gaps')}` transitions."
    )

with tab_journeys:
    st.markdown('<div class="terminal-header">EVENT-FIRST FUNNEL (RETROACTIVE)</div>', unsafe_allow_html=True)
    steps_raw = st.text_input(
        "Ordered event steps (comma-separated)",
        value=", ".join(DEFAULT_JOURNEY_STEPS),
        key="journey_steps",
    )
    steps = [s.strip() for s in steps_raw.split(",") if s.strip()]
    jdf = event_funnel(events, steps)
    if not jdf.empty:
        fig_j = px.bar(jdf, x="step", y="users", color="users", color_continuous_sequence=["#00f2ff"])
        fig_j.update_layout(**PLOTLY_THEME["layout"], showlegend=False)
        st.plotly_chart(fig_j, use_container_width=True)
        st.dataframe(jdf, hide_index=True, use_container_width=True)

with tab_inst:
    st.markdown('<div class="terminal-header">SESSIONIZATION + FEATURE FLAGS</div>', unsafe_allow_html=True)
    sess_sizes = sess_events.groupby("session_id").size()
    ix1, ix2 = st.columns(2)
    ix1.metric("Synthetic product events generated", f"{len(events):,}")
    ix2.metric("Avg events / behavioural session", f"{sess_sizes.mean():.2f}" if not sess_sizes.empty else "0")

    adop = cohort_event_adoption(cust, events, event_name="subscribe_toggle")
    adop_fig = px.line(
        adop,
        x="signup_cohort_month",
        y="pct_activated_within_window",
        markers=True,
        color_discrete_sequence=["#ff9d00"],
    )
    adop_fig.update_layout(**PLOTLY_THEME["layout"])
    adop_fig.update_yaxes(range=[0, 105])
    adop_fig.update_xaxes(title="Signup cohort month", tickangle=-45)
    adop_fig.update_yaxes(title="Pct with subscribe_toggle in first 30d")
    st.plotly_chart(adop_fig, use_container_width=True)

    sel_event = st.selectbox(
        "Adoption cohort view",
        options=["subscribe_toggle", "apply_promo", "browse_for_you_scroll", "purchase_complete"],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    alt = cohort_event_adoption(cust, events, event_name=sel_event)
    mini = px.bar(alt.tail(12), x="signup_cohort_month", y="pct_activated_within_window")
    mini.update_layout(**PLOTLY_THEME["layout"])
    mini.update_yaxes(range=[0, 105])
    st.plotly_chart(mini, use_container_width=True)

    st.dataframe(sess_events.head(200), hide_index=True, use_container_width=True)

with tab_model:
    st.markdown('<div class="terminal-header">BRIDGE BACK TO EXECUTIVE SUMMARY</div>', unsafe_allow_html=True)
    pm_pb = s.get("payback_month")
    if pm_pb is None or (isinstance(pm_pb, float) and pd.isna(pm_pb)) or pm_pb == "":
        payback_readable = "Never"
    else:
        payback_readable = f"Month {int(pm_pb)}"
    st.info(
        f"Health `{s['health_score']}`, LTV:CAC `{s['ltv_cac']}×`, "
        f"Monthly churn `{s['monthly_churn_eff']}%`, Payback `{payback_readable}`."
    )

    st.write(f"*{str(config.get('business_type')).upper()}* configuration informs how tolerant GTM teams can be to activation lag.")

    st.markdown(
        "Use **Conversion & Funnel** for experiment uplift → monetisation math and guardrail narration (discount/refund interplay)."
    )
