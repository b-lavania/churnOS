"""Decision-surface chart helpers — visual receipts for DECISIONS pages."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ui.magazine import apply_plotly_theme

# Blavania chart palette
_CHART_TEAL = "#0a5a46"
_CHART_AMBER = "#ba7517"
_CHART_BLUE = "#185fa5"
_CHART_INK_MID = "#3a3f45"
_CHART_INK_SOFT = "#5c6370"
_CHART_INK = "#0f1112"


def activation_habit_cohort(seats: pd.DataFrame) -> go.Figure | None:
    """Activation + weekly delegation rates by signup month."""
    if seats.empty or "signup_date" not in seats.columns:
        return None
    df = seats.copy()
    df["signup_month"] = pd.to_datetime(df["signup_date"]).dt.to_period("M").astype(str)
    by = (
        df.groupby("signup_month", as_index=False)
        .agg(
            activation=("is_activated", "mean"),
            habit=("weekly_delegation", "mean"),
        )
        .sort_values("signup_month")
    )
    if by.empty:
        return None
    long = by.melt(
        id_vars="signup_month",
        value_vars=["activation", "habit"],
        var_name="metric",
        value_name="rate",
    )
    long["rate_pct"] = long["rate"] * 100
    long["metric"] = long["metric"].map(
        {"activation": "Activation", "habit": "Weekly delegation"}
    )
    fig = px.line(
        long,
        x="signup_month",
        y="rate_pct",
        color="metric",
        markers=True,
        labels={"signup_month": "Signup cohort", "rate_pct": "%", "metric": ""},
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=320, legend=dict(orientation="h", yanchor="bottom", y=1.02))
    fig.update_yaxes(range=[0, 105])
    return fig


def activation_by_capability(runs: pd.DataFrame, capabilities: pd.DataFrame) -> go.Figure | None:
    """Success rate and run volume by capability — activation leak signal."""
    if runs.empty:
        return None
    agg = (
        runs.groupby("capability_id", as_index=False)
        .agg(runs=("run_id", "count"), success_rate=("success", "mean"))
        .sort_values("runs", ascending=False)
        .head(12)
    )
    if "name" in capabilities.columns:
        names = capabilities.set_index("capability_id")["name"]
        agg["label"] = agg["capability_id"].map(lambda c: names[c] if c in names.index else c)
    else:
        agg["label"] = agg["capability_id"]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=agg["label"],
            y=agg["success_rate"] * 100,
            name="Success %",
            marker_color=_CHART_TEAL,
            yaxis="y",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=agg["label"],
            y=agg["runs"],
            name="Run count",
            mode="lines+markers",
            marker=dict(color=_CHART_AMBER, size=7),
            line=dict(color=_CHART_AMBER, width=2),
            yaxis="y2",
        )
    )
    apply_plotly_theme(fig)
    fig.update_layout(
        height=340,
        yaxis=dict(title="Success %", range=[0, 105]),
        yaxis2=dict(title="Runs", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(tickangle=-35),
        barmode="group",
    )
    return fig


def trust_approval_timeline(runs: pd.DataFrame, approvals: pd.DataFrame) -> go.Figure | None:
    """Monthly trust-incident rate and dismiss rate."""
    if runs.empty:
        return None
    r = runs.copy()
    r["month"] = pd.to_datetime(r["started_at"]).dt.to_period("M").astype(str)
    trust = r.groupby("month", as_index=False).agg(trust_rate=("trust_incident", "mean"))
    trust["trust_pct"] = trust["trust_rate"] * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trust["month"],
            y=trust["trust_pct"],
            name="Trust incidents %",
            mode="lines+markers",
            line=dict(color=_CHART_INK_MID, width=2),
            marker=dict(size=6),
        )
    )
    if not approvals.empty and "decided_at" in approvals.columns:
        a = approvals.copy()
        a["month"] = pd.to_datetime(a["decided_at"]).dt.to_period("M").astype(str)
        a["is_dismiss"] = a["decision"] == "dismiss"
        dismiss = a.groupby("month", as_index=False).agg(dismiss_rate=("is_dismiss", "mean"))
        dismiss["dismiss_pct"] = dismiss["dismiss_rate"] * 100
        fig.add_trace(
            go.Scatter(
                x=dismiss["month"],
                y=dismiss["dismiss_pct"],
                name="Dismiss rate %",
                mode="lines+markers",
                line=dict(color=_CHART_AMBER, width=2, dash="dot"),
                marker=dict(size=6),
            )
        )
    apply_plotly_theme(fig)
    fig.update_layout(
        height=320,
        yaxis_title="%",
        xaxis_title="Month",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def trust_by_capability(runs: pd.DataFrame, capabilities: pd.DataFrame) -> go.Figure | None:
    """Trust incident rate by capability (top offenders)."""
    if runs.empty:
        return None
    agg = (
        runs.groupby("capability_id", as_index=False)
        .agg(trust_rate=("trust_incident", "mean"), runs=("run_id", "count"))
        .query("runs >= 5")
        .sort_values("trust_rate", ascending=False)
        .head(10)
    )
    if agg.empty:
        return None
    if "name" in capabilities.columns:
        names = capabilities.set_index("capability_id")["name"]
        agg["label"] = agg["capability_id"].map(lambda c: names[c] if c in names.index else c)
    else:
        agg["label"] = agg["capability_id"]
    fig = px.bar(
        agg,
        x="label",
        y=agg["trust_rate"] * 100,
        labels={"label": "Capability", "y": "Trust incident %"},
        color_discrete_sequence=[_CHART_INK_MID],
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=300, showlegend=False, xaxis=dict(tickangle=-35))
    fig.update_yaxes(title="Trust incident %")
    return fig


def run_cost_by_capability(
    runs: pd.DataFrame,
    capabilities: pd.DataFrame,
    seat_arpu: float,
) -> go.Figure | None:
    """Mean $/successful run by capability with ARPU reference band."""
    success = runs[runs["success"]] if not runs.empty else runs
    if success.empty:
        return None
    agg = (
        success.groupby("capability_id", as_index=False)
        .agg(cost=("run_cost_usd", "mean"), runs=("run_id", "count"))
        .sort_values("cost", ascending=False)
        .head(12)
    )
    if "name" in capabilities.columns:
        names = capabilities.set_index("capability_id")["name"]
        agg["label"] = agg["capability_id"].map(lambda c: names[c] if c in names.index else c)
    else:
        agg["label"] = agg["capability_id"]

    # Rough monthly run load proxy: show cost as share of ARPU if ~20 successful runs/mo
    implied_monthly = agg["cost"] * 20
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=agg["label"],
            y=agg["cost"],
            name="$ / successful run",
            marker_color=_CHART_TEAL,
        )
    )
    if seat_arpu and seat_arpu > 0:
        fig.add_hline(
            y=seat_arpu / 40,
            line_dash="dash",
            line_color=_CHART_AMBER,
            annotation_text="≈ ARPU / 40 runs",
            annotation_position="top right",
        )
    apply_plotly_theme(fig)
    fig.update_layout(
        height=340,
        yaxis_title="USD",
        xaxis=dict(tickangle=-35),
        showlegend=False,
    )
    # Store for caption use via fig.layout.meta if needed
    fig.layout.meta = {"implied_monthly_max": float(implied_monthly.max()) if len(implied_monthly) else 0}
    return fig


def connector_fail_rates(connector_events: pd.DataFrame) -> go.Figure | None:
    """Failure rate by connector."""
    if connector_events.empty:
        return None
    by = (
        connector_events.groupby("connector_id", as_index=False)
        .agg(calls=("connector_event_id", "count"), fail_rate=("success", lambda s: 1 - s.mean()))
        .sort_values("fail_rate", ascending=False)
    )
    fig = go.Figure(
        go.Bar(
            x=by["connector_id"],
            y=by["fail_rate"] * 100,
            marker_color=_CHART_AMBER,
            customdata=by["calls"],
            hovertemplate="%{x}<br>Fail %{y:.1f}%<br>Calls %{customdata}<extra></extra>",
        )
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=300, yaxis_title="Failure %", xaxis_title="Connector")
    return fig


def loop_histogram(runs: pd.DataFrame, max_loops_threshold: float = 8) -> go.Figure | None:
    """Distribution of loop_count with exhaustion threshold line."""
    if runs.empty or "loop_count" not in runs.columns:
        return None
    fig = go.Figure(
        go.Histogram(
            x=runs["loop_count"],
            nbinsx=min(24, int(runs["loop_count"].max()) + 1),
            marker_color=_CHART_TEAL,
            name="Runs",
        )
    )
    fig.add_vline(
        x=max_loops_threshold,
        line_dash="dash",
        line_color=_CHART_AMBER,
        annotation_text=f"max_loops={int(max_loops_threshold)}",
        annotation_position="top right",
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=300, xaxis_title="Loop count", yaxis_title="Runs", bargap=0.05)
    return fig


def cost_waterfall_sample(runs: pd.DataFrame) -> go.Figure | None:
    """Mean gross → cache credit → net cost waterfall across runs."""
    if runs.empty or "gross_cost_usd" not in runs.columns:
        return None
    gross = float(runs["gross_cost_usd"].mean())
    credit = float(runs["cache_credit_usd"].mean()) if "cache_credit_usd" in runs.columns else 0.0
    net = float(runs["run_cost_usd"].mean())
    fig = go.Figure(
        go.Waterfall(
            name="Cost",
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Gross token cost", "Cache credit", "Net run cost"],
            y=[gross, -credit, net],
            connector={"line": {"color": _CHART_INK_SOFT}},
            decreasing={"marker": {"color": _CHART_TEAL}},
            increasing={"marker": {"color": _CHART_AMBER}},
            totals={"marker": {"color": _CHART_INK_MID}},
        )
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=300, yaxis_title="USD", showlegend=False)
    return fig


def connector_blast_radius(
    connector_events: pd.DataFrame,
    runs: pd.DataFrame,
    capabilities: pd.DataFrame | None = None,
    graph: pd.DataFrame | None = None,
) -> go.Figure | None:
    """How many capabilities each connector touches (blast radius)."""
    if graph is not None and not graph.empty:
        radius = (
            graph.groupby("connector_id", as_index=False)
            .agg(
                capabilities=("capability_id", "nunique"),
                fails=("fail_count", "sum"),
                calls=("call_count", "sum"),
            )
        )
        radius["fail_rate"] = radius["fails"] / radius["calls"].clip(lower=1)
    else:
        if connector_events.empty or runs.empty:
            return None
        merged = connector_events.merge(
            runs[["run_id", "capability_id"]],
            on="run_id",
            how="left",
        )
        radius = (
            merged.groupby("connector_id", as_index=False)
            .agg(
                capabilities=("capability_id", "nunique"),
                fail_rate=("success", lambda s: 1 - s.mean()),
            )
        )
    radius = radius.sort_values("capabilities", ascending=False)
    fig = go.Figure(
        go.Scatter(
            x=radius["capabilities"],
            y=radius["fail_rate"] * 100,
            mode="markers+text",
            text=radius["connector_id"],
            textposition="top center",
            marker=dict(
                size=12 + radius["capabilities"] * 2,
                color=radius["fail_rate"] * 100,
                colorscale=[[0, _CHART_TEAL], [1, _CHART_AMBER]],
                showscale=False,
                line=dict(width=1, color=_CHART_INK),
            ),
            hovertemplate=(
                "%{text}<br>Capabilities: %{x}"
                "<br>Fail rate: %{y:.1f}%<extra></extra>"
            ),
        )
    )
    apply_plotly_theme(fig)
    fig.update_layout(
        height=340,
        xaxis_title="Capabilities touched (blast radius)",
        yaxis_title="Failure %",
    )
    return fig


def delegation_ratio_timeseries(seats: pd.DataFrame) -> go.Figure | None:
    """Weekly delegation ratio by signup cohort month."""
    if seats.empty or "signup_date" not in seats.columns:
        return None
    df = seats.copy()
    df["signup_month"] = pd.to_datetime(df["signup_date"]).dt.to_period("M").astype(str)
    active = df[df["is_activated"]]
    if active.empty:
        return None
    by = (
        active.groupby("signup_month", as_index=False)
        .agg(delegation=("weekly_delegation", "mean"))
        .sort_values("signup_month")
    )
    by["delegation_pct"] = by["delegation"] * 100
    fig = px.line(
        by, x="signup_month", y="delegation_pct", markers=True,
        labels={"signup_month": "Cohort", "delegation_pct": "Delegation %"},
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=300, showlegend=False)
    fig.update_yaxes(range=[0, 105])
    return fig


def days_to_verified_outcome_cohort(outcomes: pd.DataFrame) -> go.Figure | None:
    """Days-to-first-verified-outcome distribution."""
    if outcomes.empty or "days_since_signup" not in outcomes.columns:
        return None
    verified = outcomes[outcomes["verified"]]
    if verified.empty:
        return None
    first = verified.groupby("account_id")["days_since_signup"].min().reset_index()
    fig = px.histogram(
        first, x="days_since_signup", nbins=20,
        labels={"days_since_signup": "Days to first verified outcome"},
        color_discrete_sequence=[_CHART_TEAL],
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=300, showlegend=False)
    fig.add_vline(x=14, line_dash="dash", line_color=_CHART_AMBER, annotation_text="14d")
    return fig


def autonomy_ratio_strip(runs: pd.DataFrame, approvals: pd.DataFrame) -> go.Figure | None:
    """HITL vs agent-resolved share."""
    if runs.empty:
        return None
    hitl = len(approvals) if not approvals.empty else 0
    agent = len(runs)
    fig = go.Figure(
        go.Bar(
            x=["Agent-resolved", "HITL approvals"],
            y=[agent, hitl],
            marker_color=[_CHART_TEAL, _CHART_AMBER],
        )
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=260, yaxis_title="Count", showlegend=False)
    return fig


def cm_nrr_teaching_chart(
    subscriptions: pd.DataFrame,
    usage_events: pd.DataFrame,
    runs: pd.DataFrame,
) -> go.Figure | None:
    """Teaching CM-NRR: MRR vs COGS."""
    if subscriptions.empty:
        return None
    mrr = float(subscriptions["mrr_usd"].sum())
    cogs = float(usage_events["cost_usd"].sum()) if not usage_events.empty else float(runs["run_cost_usd"].sum())
    margin = mrr - cogs
    fig = go.Figure(
        go.Bar(
            x=["MRR", "Run COGS", "Contribution margin"],
            y=[mrr, cogs, margin],
            marker_color=[_CHART_BLUE, _CHART_AMBER, _CHART_TEAL],
        )
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=300, yaxis_title="USD", showlegend=False)
    return fig


def portfolio_tornado(records: list) -> go.Figure | None:
    """Tornado chart of cost of leaving live by subject."""
    if not records:
        return None
    rows = []
    for r in records[:15]:
        subj = r.get("subject", {})
        et = subj.get("entity_type", "capability")
        label = subj.get("account_id") or subj.get("capability_id", "—")
        rows.append({
            "label": f"{et[:3].upper()} · {label}",
            "cost": r.get("economics", {}).get("primary_metric_usd", 0),
        })
    df = pd.DataFrame(rows).sort_values("cost", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=df["cost"],
            y=df["label"],
            orientation="h",
            marker_color=_CHART_AMBER,
        )
    )
    apply_plotly_theme(fig)
    fig.update_layout(
        height=max(280, len(df) * 28),
        xaxis_title="Cost of leaving live (USD)",
        showlegend=False,
    )
    return fig


def flywheel_comparison_chart(summary: dict) -> go.Figure | None:
    """Followed vs overridden outcome deltas."""
    if summary.get("n", 0) == 0:
        return None
    followed = summary.get("followed", {})
    overridden = summary.get("overridden", {})
    metrics = ["retention Δ", "delegation", "churn rate"]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Followed",
            x=metrics,
            y=[
                followed.get("retention_delta_14d", 0),
                followed.get("delegation_rate", 0),
                followed.get("churn_rate", 0),
            ],
            marker_color=_CHART_TEAL,
        )
    )
    fig.add_trace(
        go.Bar(
            name="Overridden",
            x=metrics,
            y=[
                overridden.get("retention_delta_14d", 0),
                overridden.get("delegation_rate", 0),
                overridden.get("churn_rate", 0),
            ],
            marker_color=_CHART_AMBER,
        )
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=320, barmode="group", legend=dict(orientation="h"))
    return fig
