"""Render Decision Card visual receipts from record['viz'] keys."""

from __future__ import annotations

from typing import Any

import streamlit as st

from core.workspace import Workspace
from ui.viz.challenge_charts import (
    activation_funnel_revenue,
    catastrophic_event_timeline,
    context_util_histogram,
    coordination_overhead_chart,
    cost_attribution_heatmap,
    cpso_trend_line,
    human_intervention_timeseries,
    integration_depth_chart,
    retention_feature_importance,
    success_vs_complexity,
    ttfv_payment_histogram,
)
from ui.viz.decisions_charts import (
    autonomy_ratio_strip,
    connector_blast_radius,
    delegation_ratio_timeseries,
    loop_histogram,
)


def attach_viz_receipt(record: dict[str, Any], workspace: Workspace) -> None:
    """Attach a chart key + headline metrics for the top exception category."""
    excs = record.get("exceptions", [])
    if not excs:
        return
    top_cat = excs[0].get("category", "")
    chart_map = {
        "run_cost_blowout": "cpso_trend",
        "margin_leakage": "power_user_margin",
        "loop_exhaustion": "loop_histogram",
        "connector_fragility": "connector_blast",
        "catastrophic_failure": "catastrophic_timeline",
        "activation_failure": "activation_funnel",
        "tourist": "ttfv_histogram",
        "habit_collapse": "delegation_timeseries",
        "trust_break": "hitl_timeseries",
        "approval_fatigue": "autonomy_strip",
        "capability_harm": "success_complexity",
        "value_failure": "coordination_overhead",
        "price": "cost_heatmap",
        "product_gap": "activation_funnel",
        "efficiency": "delegation_timeseries",
    }
    chart = chart_map.get(top_cat)
    if not chart:
        return
    from analytics.metrics import resolve_metric

    record["viz"] = {
        "chart": chart,
        "category": top_cat,
        "headline": {
            "cpso": resolve_metric("cost_per_successful_outcome", workspace)["display"],
            "ttfv": resolve_metric("time_to_first_value", workspace)["display"],
            "depth": resolve_metric("integration_depth_score", workspace)["display"],
        },
    }


def render_viz_receipt(viz: dict[str, Any], workspace: Workspace) -> None:
    """Render the teaching chart referenced on a GDR."""
    if not viz:
        return
    headline = viz.get("headline", {})
    if headline:
        st.caption(
            " · ".join(f"{k.upper()}: {v}" for k, v in headline.items())
        )
    chart = viz.get("chart")
    fig = None
    if chart == "cpso_trend":
        fig = cpso_trend_line(workspace)
    elif chart == "loop_histogram":
        fig = loop_histogram(workspace.runs, float(workspace.profile.get("max_loops_threshold", 8)))
    elif chart == "connector_blast":
        graph = getattr(workspace, "connector_capability_graph", None)
        fig = connector_blast_radius(
            workspace.connector_events,
            workspace.runs,
            workspace.capabilities,
            graph=graph if graph is not None and not graph.empty else None,
        )
    elif chart == "catastrophic_timeline":
        fig = catastrophic_event_timeline(workspace)
    elif chart == "activation_funnel":
        fig = activation_funnel_revenue(workspace)
    elif chart == "ttfv_histogram":
        fig = ttfv_payment_histogram(workspace)
    elif chart == "delegation_timeseries":
        fig = delegation_ratio_timeseries(workspace.seats)
    elif chart == "hitl_timeseries":
        fig = human_intervention_timeseries(workspace)
    elif chart == "autonomy_strip":
        fig = autonomy_ratio_strip(workspace.runs, workspace.approvals)
    elif chart == "success_complexity":
        fig = success_vs_complexity(workspace)
    elif chart == "coordination_overhead":
        fig = coordination_overhead_chart(workspace)
    elif chart == "cost_heatmap":
        fig = cost_attribution_heatmap(workspace)
    elif chart == "context_util":
        fig = context_util_histogram(workspace)
    elif chart == "integration_depth":
        fig = integration_depth_chart(workspace)
    elif chart == "retention_features":
        fig = retention_feature_importance(workspace)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
