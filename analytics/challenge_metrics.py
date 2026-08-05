"""Resolvers for agenticchallenges.md metrics (dummy-seeded warehouse)."""

from __future__ import annotations

import pandas as pd

from core.workspace import Workspace


def _naive_ts(value) -> pd.Timestamp:
    """Normalize to tz-naive UTC so synthetic (naive) and utcnow() (aware) can subtract."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        return ts.tz_convert("UTC").tz_localize(None)
    return ts


def power_user_margin_leakage(ws: Workspace) -> tuple[float, dict]:
    if ws.runs.empty or ws.seats.empty:
        return 0.0, {}
    seat_tokens = ws.runs.groupby("seat_id")["tokens_in"].sum().reset_index()
    seat_tokens = seat_tokens.merge(ws.seats[["seat_id", "seat_arpu_monthly"]], on="seat_id")
    top_n = max(1, int(len(seat_tokens) * 0.05))
    top = seat_tokens.nlargest(top_n, "tokens_in")
    revenue = top["seat_arpu_monthly"].sum() * 6
    cost = ws.runs[ws.runs["seat_id"].isin(top["seat_id"])]["run_cost_usd"].sum()
    margin = revenue - cost
    return float(margin), {"revenue": revenue, "cost": cost, "margin": margin}


def context_utilization_rate(ws: Workspace) -> float:
    if ws.runs.empty or "context_util_pct" not in ws.runs.columns:
        return 0.0
    return float(ws.runs["context_util_pct"].mean())


def retry_amplification_factor(ws: Workspace) -> float:
    if ws.runs.empty:
        return 0.0
    if "user_goal_id" in ws.runs.columns:
        goals = ws.runs.groupby("user_goal_id").size().mean()
        return float(goals) if goals else 1.0
    return float(ws.runs["loop_count"].mean())


def unattributed_spend_pct(ws: Workspace) -> float:
    ue = ws.usage_events
    if ue.empty:
        runs = ws.runs
        if runs.empty or "attribution_complete" not in runs.columns:
            return 0.0
        return float((~runs["attribution_complete"]).mean() * 100)
    col = "attribution_complete" if "attribution_complete" in ue.columns else None
    if col is None:
        return 18.0
    return float((~ue[col]).mean() * 100)


def static_decision_age_median(ws: Workspace) -> float:
    rd = getattr(ws, "routing_decisions", pd.DataFrame())
    if rd.empty or "static_age_days" not in rd.columns:
        return 0.0
    return float(rd["static_age_days"].median())


def time_to_first_production_agent(ws: Workspace) -> float:
    return float(ws.meta.get("time_to_first_production_agent_days", 127))


def time_to_first_value_median(ws: Workspace) -> float:
    seats = ws.seats
    outcomes = ws.outcomes
    if seats.empty or outcomes.empty or "first_paid_at" not in seats.columns:
        return 0.0
    verified = outcomes[outcomes["verified"]].copy()
    if verified.empty:
        return 14.0
    merged = verified.merge(seats[["seat_id", "first_paid_at"]], left_on="end_user_id", right_on="seat_id")
    if merged.empty:
        return 0.0
    merged["ttfv_days"] = (
        pd.to_datetime(merged["occurred_at"]) - pd.to_datetime(merged["first_paid_at"])
    ).dt.days
    return float(merged["ttfv_days"].median())


def paying_but_dormant_rate(ws: Workspace) -> float:
    accounts = ws.accounts
    outcomes = ws.outcomes
    if accounts.empty:
        return 0.0
    paying = accounts[accounts.get("is_paying", True)]
    if paying.empty:
        return 0.0
    dormant = 0
    for _, acc in paying.iterrows():
        acc_out = outcomes[
            (outcomes["account_id"] == acc["account_id"])
            & (outcomes["verified"])
        ] if not outcomes.empty else pd.DataFrame()
        if acc_out.empty:
            dormant += 1
        else:
            latest = _naive_ts(pd.to_datetime(acc_out["occurred_at"]).max())
            if (_naive_ts(pd.Timestamp.utcnow()) - latest).days > 14:
                dormant += 1
    return dormant / len(paying) * 100


def activation_conversion_paid_success(ws: Workspace, days: int = 14) -> float:
    accounts = ws.accounts
    outcomes = ws.outcomes
    if accounts.empty or outcomes.empty:
        return 0.0
    converted = 0
    for _, acc in accounts.iterrows():
        paid = _naive_ts(acc.get("first_paid_at", acc.get("created_at")))
        acc_out = outcomes[
            (outcomes["account_id"] == acc["account_id"]) & outcomes["verified"]
        ]
        if acc_out.empty:
            continue
        first = _naive_ts(pd.to_datetime(acc_out["occurred_at"]).min())
        if (first - paid).days <= days:
            converted += 1
    return converted / max(len(accounts), 1) * 100


def first_win_definition_coverage(ws: Workspace) -> float:
    acc = ws.accounts
    if acc.empty or "first_win_defined" not in acc.columns:
        return 0.0
    return float(acc["first_win_defined"].mean() * 100)


def integration_depth_mean(ws: Workspace) -> float:
    acc = ws.accounts
    if acc.empty or "integration_depth_score" not in acc.columns:
        return 0.0
    return float(acc["integration_depth_score"].mean())


def rebuild_competitor_churn_share(ws: Workspace) -> float:
    seats = ws.seats
    if seats.empty or "churn_reason" not in seats.columns:
        return 0.0
    churned = seats[seats["is_churned"]]
    if churned.empty:
        return 0.0
    tagged = churned[churned["churn_reason"].isin(["rebuild_in_house", "competitor"])]
    return len(tagged) / len(churned) * 100


def context_export_rate(ws: Workspace) -> float:
    seats = ws.seats
    if seats.empty or "exported_before_churn" not in seats.columns:
        return 0.0
    churned = seats[seats["is_churned"]]
    if churned.empty:
        return 0.0
    return float(churned["exported_before_churn"].mean() * 100)


def catastrophic_event_rate(ws: Workspace) -> float:
    cat = getattr(ws, "catastrophic_events", pd.DataFrame())
    if cat.empty or ws.runs.empty:
        return 0.0
    return len(cat) / len(ws.runs) * 1000


def human_intervention_rate(ws: Workspace) -> float:
    if ws.runs.empty or "human_intervened" not in ws.runs.columns:
        return 0.0
    return float(ws.runs["human_intervened"].mean() * 100)


def post_failure_trust_drop(ws: Workspace) -> float:
    acc = ws.accounts
    if acc.empty or "nps_before" not in acc.columns:
        return 0.0
    return float((acc["nps_after_failure"] - acc["nps_before"]).mean())


def verified_outcome_success_rate(ws: Workspace) -> float:
    outcomes = ws.outcomes
    if outcomes.empty:
        return 0.0
    return float(outcomes["verified"].mean() * 100) if "verified" in outcomes.columns else 0.0


def coordination_overhead_mean(ws: Workspace) -> float:
    if ws.runs.empty or "coordination_token_share" not in ws.runs.columns:
        return 0.0
    return float(ws.runs["coordination_token_share"].mean() * 100)


def high_ltv_path_share(ws: Workspace) -> float:
    acc = ws.accounts
    if acc.empty or "activation_path" not in acc.columns:
        return 0.0
    high = acc[acc["activation_path"].isin(["guided_first_win", "design_partner"])]
    return len(high) / len(acc) * 100


def agentic_health_score(ws: Workspace) -> tuple[float, str]:
    """Composite 0–100 with R/Y/G band."""
    from analytics.metrics import resolve_metric

    cpso = resolve_metric("cost_per_successful_outcome", ws).get("value") or 1.0
    ttfv = time_to_first_value_median(ws)
    depth = integration_depth_mean(ws)
    cat = catastrophic_event_rate(ws)
    score = 100.0
    score -= min(30, float(cpso) * 5)
    score -= min(25, ttfv * 1.5)
    score += min(20, depth * 0.2)
    score -= min(25, cat * 2)
    score = max(0, min(100, score))
    band = "green" if score >= 70 else ("yellow" if score >= 45 else "red")
    return score, band
