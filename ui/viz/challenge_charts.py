"""Charts for agenticchallenges.md findings (dummy-seeded data)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.workspace import Workspace
from ui.magazine import apply_plotly_theme

_TEAL = "#0a5a46"
_AMBER = "#ba7517"
_BLUE = "#185fa5"
_RED = "#a32a2a"
_GREEN = "#0a5a46"


def cost_attribution_heatmap(ws: Workspace) -> go.Figure | None:
    df = getattr(ws, "spend_by_step", pd.DataFrame())
    if df.empty:
        return None
    pivot = df.pivot_table(index="step_kind", columns="cohort", values="spend_usd", aggfunc="sum").fillna(0)
    fig = px.imshow(pivot, labels=dict(x="Cohort", y="Step", color="Spend USD"), color_continuous_scale=[[0, _TEAL], [1, _AMBER]])
    apply_plotly_theme(fig)
    fig.update_layout(height=320, title="Cost attribution heatmap (synthetic)")
    return fig


def jevons_elasticity_chart(ws: Workspace) -> go.Figure | None:
    df = getattr(ws, "jevons_elasticity", pd.DataFrame())
    if df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["unit_price"], y=df["token_volume"], mode="lines+markers", name="Volume", line=dict(color=_TEAL)))
    fig.add_trace(go.Scatter(x=df["unit_price"], y=df["total_spend"], mode="lines+markers", name="Total $", yaxis="y2", line=dict(color=_AMBER)))
    apply_plotly_theme(fig)
    fig.update_layout(height=320, yaxis=dict(title="Token volume"), yaxis2=dict(title="Total spend", overlaying="y", side="right"), legend=dict(orientation="h"))
    return fig


def run_gantt_sample(ws: Workspace, max_spans: int = 40) -> go.Figure | None:
    spans = ws.spans
    if spans.empty or "started_at" not in spans.columns:
        return None
    sample = spans.dropna(subset=["started_at"]).head(max_spans).copy()
    if sample.empty:
        return None
    sample["label"] = sample["agent_run_id"] + " L" + sample["loop_iteration"].astype(str)
    sample["end"] = pd.to_datetime(sample["started_at"]) + pd.Timedelta(minutes=2)
    fig = px.timeline(
        sample, x_start="started_at", x_end="end", y="label", color="success",
        color_discrete_map={True: _TEAL, False: _AMBER},
    )
    apply_plotly_theme(fig)
    fig.update_layout(height=400, title="Agent run Gantt (sample session)", yaxis=dict(autorange="reversed"))
    return fig


def context_util_histogram(ws: Workspace) -> go.Figure | None:
    if ws.runs.empty or "context_util_pct" not in ws.runs.columns:
        return None
    fig = px.histogram(ws.runs, x="context_util_pct", nbins=25, color_discrete_sequence=[_BLUE])
    apply_plotly_theme(fig)
    fig.add_vline(x=80, line_dash="dash", line_color=_AMBER)
    fig.update_layout(height=280, xaxis_title="Context utilization %", showlegend=False)
    return fig


def retry_by_capability(ws: Workspace, capabilities: pd.DataFrame) -> go.Figure | None:
    if ws.runs.empty:
        return None
    agg = ws.runs.groupby("capability_id")["loop_count"].mean().reset_index(name="retry_factor")
    if "name" in capabilities.columns:
        names = capabilities.set_index("capability_id")["name"]
        agg["label"] = agg["capability_id"].map(lambda c: names.get(c, c))
    else:
        agg["label"] = agg["capability_id"]
    agg = agg.sort_values("retry_factor", ascending=False).head(10)
    fig = px.bar(agg, x="label", y="retry_factor", color_discrete_sequence=[_AMBER])
    apply_plotly_theme(fig)
    fig.update_layout(height=300, yaxis_title="Retry amplification", showlegend=False)
    return fig


def power_user_margin_table(ws: Workspace) -> pd.DataFrame:
    if ws.runs.empty or ws.seats.empty:
        return pd.DataFrame()
    seat_tokens = ws.runs.groupby("seat_id").agg(tokens=("tokens_in", "sum"), cost=("run_cost_usd", "sum")).reset_index()
    seat_tokens = seat_tokens.merge(ws.seats[["seat_id", "seat_arpu_monthly"]], on="seat_id")
    seat_tokens["margin"] = seat_tokens["seat_arpu_monthly"] * 6 - seat_tokens["cost"]
    return seat_tokens.nlargest(max(1, len(seat_tokens) // 20), "tokens")


def activation_funnel_revenue(ws: Workspace) -> go.Figure | None:
    n_accounts = len(ws.accounts) if not ws.accounts.empty else len(ws.workspaces)
    n_paid = len(ws.accounts[ws.accounts.get("is_paying", True)]) if not ws.accounts.empty else n_accounts
    verified_accs = set()
    if not ws.outcomes.empty:
        verified_accs = set(ws.outcomes[ws.outcomes["verified"]]["account_id"].unique())
    n_verified = len(verified_accs)
    fig = go.Figure(go.Funnel(
        y=["Sign-up", "First paid", "Verified outcome"],
        x=[n_accounts, n_paid, n_verified],
        textinfo="value+percent initial",
    ))
    apply_plotly_theme(fig)
    fig.update_layout(height=320, title="Activation funnel with revenue (synthetic)")
    return fig


def ttfv_payment_histogram(ws: Workspace) -> go.Figure | None:
    seats = ws.seats
    outcomes = ws.outcomes
    if seats.empty or outcomes.empty or "first_paid_at" not in seats.columns:
        return None
    verified = outcomes[outcomes["verified"]].merge(
        seats[["seat_id", "first_paid_at"]], left_on="end_user_id", right_on="seat_id"
    )
    if verified.empty:
        return None
    verified["ttfv_days"] = (pd.to_datetime(verified["occurred_at"]) - pd.to_datetime(verified["first_paid_at"])).dt.days
    fig = px.histogram(verified, x="ttfv_days", nbins=20, color_discrete_sequence=[_TEAL])
    apply_plotly_theme(fig)
    fig.update_layout(height=280, xaxis_title="Days from payment to verified outcome")
    return fig


def paying_dormant_table(ws: Workspace) -> pd.DataFrame:
    if ws.accounts.empty:
        return pd.DataFrame()
    rows = []
    for _, acc in ws.accounts.iterrows():
        acc_out = ws.outcomes[(ws.outcomes["account_id"] == acc["account_id"]) & ws.outcomes["verified"]] if not ws.outcomes.empty else pd.DataFrame()
        dormant = acc_out.empty
        rows.append({"account_id": acc["account_id"], "tier": acc.get("tier", "—"), "dormant_14d": dormant, "depth": acc.get("integration_depth_score", 0)})
    df = pd.DataFrame(rows)
    return df[df["dormant_14d"]].head(15)


def integration_depth_chart(ws: Workspace) -> go.Figure | None:
    acc = ws.accounts
    if acc.empty or "integration_depth_score" not in acc.columns:
        return None
    fig = px.bar(acc.sort_values("integration_depth_score", ascending=False).head(12), x="account_id", y="integration_depth_score", color="tier", color_discrete_sequence=[_TEAL, _BLUE, _AMBER])
    apply_plotly_theme(fig)
    fig.update_layout(height=320, yaxis_title="Depth score", showlegend=True)
    return fig


def churn_reason_stacked(ws: Workspace) -> go.Figure | None:
    seats = ws.seats
    if seats.empty or "churn_reason" not in seats.columns:
        return None
    churned = seats[seats["is_churned"]]
    if churned.empty:
        return None
    counts = churned["churn_reason"].value_counts().reset_index()
    counts.columns = ["reason", "count"]
    fig = px.bar(counts, x="reason", y="count", color="reason", color_discrete_sequence=px.colors.qualitative.Set2)
    apply_plotly_theme(fig)
    fig.update_layout(height=300, showlegend=False)
    return fig


def catastrophic_event_timeline(ws: Workspace) -> go.Figure | None:
    cat = getattr(ws, "catastrophic_events", pd.DataFrame())
    if cat.empty:
        return None
    fig = px.scatter(cat, x="occurred_at", y="severity", color="churn_within_14d", hover_data=["description"], color_discrete_map={True: _RED, False: _AMBER})
    apply_plotly_theme(fig)
    fig.update_layout(height=300, title="Catastrophic event log")
    return fig


def human_intervention_timeseries(ws: Workspace) -> go.Figure | None:
    if ws.runs.empty or "human_intervened" not in ws.runs.columns or "started_at" not in ws.runs.columns:
        return None
    df = ws.runs.copy()
    df["week"] = pd.to_datetime(df["started_at"]).dt.to_period("W").astype(str)
    weekly = df.groupby("week")["human_intervened"].mean().reset_index()
    weekly["rate_pct"] = weekly["human_intervened"] * 100
    fig = px.line(weekly, x="week", y="rate_pct", markers=True, color_discrete_sequence=[_AMBER])
    apply_plotly_theme(fig)
    fig.update_layout(height=280, yaxis_title="Human intervention %")
    return fig


def post_failure_trust_bars(ws: Workspace) -> go.Figure | None:
    acc = ws.accounts
    if acc.empty or "nps_before" not in acc.columns:
        return None
    sample = acc.head(12).copy()
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Before", x=sample["account_id"], y=sample["nps_before"], marker_color=_TEAL))
    fig.add_trace(go.Bar(name="After failure", x=sample["account_id"], y=sample["nps_after_failure"], marker_color=_RED))
    apply_plotly_theme(fig)
    fig.update_layout(height=300, barmode="group", legend=dict(orientation="h"))
    return fig


def success_vs_complexity(ws: Workspace) -> go.Figure | None:
    if ws.runs.empty:
        return None
    df = ws.runs.copy()
    if "coordination_token_share" not in df.columns:
        return None
    df["complexity"] = df["steps_to_completion"] if "steps_to_completion" in df.columns else df["loop_count"]
    fig = px.scatter(df, x="complexity", y="success", color="coordination_token_share", opacity=0.4, color_continuous_scale=[[0, _TEAL], [1, _AMBER]])
    apply_plotly_theme(fig)
    fig.update_layout(height=320, title="Verified success vs complexity (synthetic)")
    return fig


def coordination_overhead_chart(ws: Workspace) -> go.Figure | None:
    if ws.runs.empty or "coordination_token_share" not in ws.runs.columns:
        return None
    df = ws.runs.groupby("capability_id")["coordination_token_share"].mean().reset_index().head(10)
    df["pct"] = df["coordination_token_share"] * 100
    fig = px.bar(df, x="capability_id", y="pct", color_discrete_sequence=[_AMBER])
    apply_plotly_theme(fig)
    fig.update_layout(height=280, yaxis_title="Coordination overhead %")
    return fig


def retention_feature_importance(ws: Workspace) -> go.Figure | None:
    rf = getattr(ws, "retention_features", pd.DataFrame())
    if rf.empty:
        return None
    fig = px.bar(rf.sort_values("importance"), x="importance", y="feature", orientation="h", color_discrete_sequence=[_BLUE])
    apply_plotly_theme(fig)
    fig.update_layout(height=300, title="Predictive retention features (synthetic SHAP)")
    return fig


def activation_path_mix(ws: Workspace) -> go.Figure | None:
    acc = ws.accounts
    if acc.empty or "activation_path" not in acc.columns:
        return None
    counts = acc["activation_path"].value_counts().reset_index()
    counts.columns = ["path", "count"]
    fig = px.pie(counts, names="path", values="count", color_discrete_sequence=[_TEAL, _BLUE, _AMBER, "#6b4fa0"])
    apply_plotly_theme(fig)
    fig.update_layout(height=300)
    return fig


def agentic_health_composite(ws: Workspace) -> go.Figure | None:
    from analytics.challenge_metrics import agentic_health_score
    from analytics.metrics import resolve_metric

    score, band = agentic_health_score(ws)
    metrics = [
        ("CPSO", resolve_metric("cost_per_successful_outcome", ws)["display"]),
        ("TTFV", resolve_metric("time_to_first_value", ws)["display"]),
        ("Depth", resolve_metric("integration_depth_score", ws)["display"]),
        ("Catastrophic", resolve_metric("catastrophic_event_rate", ws)["display"]),
    ]
    colors = {"green": _GREEN, "yellow": _AMBER, "red": _RED}
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": f"Agentic Health ({band.upper()})"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": colors.get(band, _TEAL)}},
    ))
    apply_plotly_theme(fig)
    fig.update_layout(height=220, annotations=[dict(text="<br>".join(f"{k}: {v}" for k, v in metrics), x=0.5, y=-0.15, showarrow=False, font=dict(size=11))])
    return fig


def feature_flag_impact(ws: Workspace, flag_id: str) -> go.Figure | None:
    flags = getattr(ws, "feature_flag_assignments", pd.DataFrame())
    if flags.empty or ws.runs.empty:
        return None
    sub = flags[flags["flag_id"] == flag_id]
    if sub.empty:
        return None
    rows = []
    for variant in ("control", "treatment"):
        seat_ids = sub[sub["variant"] == variant]["seat_id"]
        runs = ws.runs[ws.runs["seat_id"].isin(seat_ids)]
        if runs.empty:
            continue
        cpso = runs["run_cost_usd"].sum() / max(len(runs[runs["success"]]), 1)
        hitl = runs["human_intervened"].mean() * 100 if "human_intervened" in runs.columns else 0
        rows.append({"variant": variant, "CPSO": cpso, "HITL %": hitl})
    if not rows:
        return None
    df = pd.DataFrame(rows)
    fig = go.Figure()
    for col, color in [("CPSO", _TEAL), ("HITL %", _AMBER)]:
        fig.add_trace(go.Bar(name=col, x=df["variant"], y=df[col], marker_color=color))
    apply_plotly_theme(fig)
    fig.update_layout(height=300, title=f"Flag: {flag_id}", barmode="group")
    return fig
