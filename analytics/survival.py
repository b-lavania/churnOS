"""
Survival and hazard models for account-level retention (agentic core).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from analytics.panels import account_week_panel
from core.workspace import Workspace


def _account_features(workspace: Workspace, account_id: str) -> dict[str, float]:
    """Aggregate features for hazard model."""
    seats = workspace.seats
    acc_col = "workspace_id" if "workspace_id" in seats.columns else "account_id"
    if acc_col == "workspace_id":
        acc_seats = seats[seats["workspace_id"] == account_id]
    else:
        acc_seats = seats[seats.get("account_id", seats["seat_id"]) == account_id]

    if acc_seats.empty:
        return {"delegation": 0.5, "autonomy": 0.7, "cpso_ratio": 0.0, "activated": 0.0}

    seat_ids = acc_seats["seat_id"].unique()
    runs = workspace.runs
    acc_runs = runs[runs["seat_id"].isin(seat_ids)] if not runs.empty else runs

    delegation = 0.5
    if "weekly_delegation" in acc_seats.columns and "is_activated" in acc_seats.columns:
        active = acc_seats[acc_seats["is_activated"]]
        delegation = float(active["weekly_delegation"].mean()) if len(active) else 0.5

    autonomy = 0.7
    if not acc_runs.empty and "success" in acc_runs.columns:
        hitl = acc_runs.get("hitl_triggered", pd.Series([False] * len(acc_runs)))
        autonomy = float((acc_runs["success"].astype(bool) & ~hitl.astype(bool)).mean())

    arpu = float(acc_seats["seat_arpu_monthly"].mean()) if "seat_arpu_monthly" in acc_seats.columns else 50.0
    cost = float(acc_runs["run_cost_usd"].sum()) if not acc_runs.empty and "run_cost_usd" in acc_runs.columns else 0.0
    n_ok = max(1, int(acc_runs["success"].sum()) if not acc_runs.empty and "success" in acc_runs.columns else 1)
    cpso_ratio = min(1.0, (cost / n_ok) / max(arpu, 1.0))

    activated = float(acc_seats["is_activated"].mean()) if "is_activated" in acc_seats.columns else 0.5

    return {
        "delegation": delegation,
        "autonomy": autonomy,
        "cpso_ratio": cpso_ratio,
        "activated": activated,
    }


def discrete_time_hazard_score(features: dict[str, float]) -> float:
    """
    Logistic hazard score in [0,1] — higher = more churn risk.
    Calibrated teaching model; replace with fitted Cox in production.
    """
    logit = (
        -1.2
        + 1.8 * (1.0 - features["delegation"])
        + 1.2 * (1.0 - features["autonomy"])
        + 0.9 * features["cpso_ratio"]
        + 0.6 * (1.0 - features["activated"])
    )
    return float(1.0 / (1.0 + np.exp(-logit)))


def predict_churn_30d(
    workspace: Workspace,
    account_id: str,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return P(churn in 30d) with approximate CI from feature uncertainty."""
    feats = _account_features(workspace, account_id)
    p = discrete_time_hazard_score(feats)
    panel = account_week_panel(workspace)
    acc_weeks = panel[panel["account_id"] == account_id] if not panel.empty else panel
    n_runs = int(acc_weeks["n_runs"].sum()) if not acc_weeks.empty else 0
    width = max(0.03, 0.15 / (1 + n_runs / 20))
    model_id = "discrete_hazard_v1"

    if profile is not None:
        from analytics.evidence import is_rigorous_mode

        if is_rigorous_mode(profile):
            cox_h = _cox_account_hazard(workspace, account_id)
            if cox_h is not None:
                p = round(0.6 * p + 0.4 * cox_h, 4)
                model_id = "cox_ph_v1"
                width = max(width, 0.05)

    lo = max(0.0, p - width)
    hi = min(1.0, p + width)
    baseline = 0.09
    return {
        "p_churn_30d": round(p, 4),
        "ci95": [round(lo, 4), round(hi, 4)],
        "baseline_p": baseline,
        "features": feats,
        "n_runs": n_runs,
        "model_id": model_id,
    }


def _cox_account_hazard(workspace: Workspace, account_id: str) -> float | None:
    """Partial hazard score for one account when Cox fit succeeds."""
    try:
        from lifelines import CoxPHFitter
    except ImportError:
        return None

    panel = account_week_panel(workspace)
    if panel.empty or panel["account_id"].nunique() < 10:
        return None

    agg = (
        panel.groupby("account_id", as_index=False)
        .agg(
            delegation_ratio=("delegation_ratio", "mean"),
            autonomy_ratio=("autonomy_ratio", "mean"),
            cpso=("cpso", "mean"),
            churned=("churned", "max"),
            weeks=("week", "count"),
        )
    )
    agg = agg.rename(columns={"weeks": "duration"})
    agg["duration"] = agg["duration"].clip(lower=1)
    if agg["churned"].sum() < 2:
        return None

    feats = _account_features(workspace, account_id)
    row = pd.DataFrame([{
        "duration": 4,
        "churned": 0,
        "delegation_ratio": feats["delegation"],
        "autonomy_ratio": feats["autonomy"],
        "cpso": feats["cpso_ratio"],
    }])

    cph = CoxPHFitter()
    try:
        cph.fit(
            agg[["duration", "churned", "delegation_ratio", "autonomy_ratio", "cpso"]],
            duration_col="duration",
            event_col="churned",
        )
        ph = cph.predict_partial_hazard(row).iloc[0]
        return float(1.0 / (1.0 + np.exp(-np.log(max(ph, 1e-6)))))
    except Exception:
        return None


def cause_specific_incidence(workspace: Workspace) -> pd.DataFrame:
    """Cause-specific churn counts from taxonomy codes on seats."""
    seats = workspace.seats
    if seats.empty or "churn_reason" not in seats.columns:
        return pd.DataFrame(columns=["cause", "count", "hazard_rate"])

    churned = seats[seats.get("is_churned", False) == True]  # noqa: E712
    if churned.empty:
        return pd.DataFrame(columns=["cause", "count", "hazard_rate"])

    counts = churned["churn_reason"].value_counts().reset_index()
    counts.columns = ["cause", "count"]
    n_total = len(seats)
    counts["hazard_rate"] = counts["count"] / max(n_total, 1)
    return counts


def survival_priced_cost(
    workspace: Workspace,
    account_id: str,
    *,
    horizon_months: int = 6,
) -> dict[str, Any]:
    """
    Teaching formula: cost_of_leaving_live ≈ ∫ hazard(t) · margin(t) dt
    """
    pred = predict_churn_30d(workspace, account_id)
    p = pred["p_churn_30d"]
    seats = workspace.seats
    acc_col = "workspace_id" if "workspace_id" in seats.columns else "account_id"
    acc_seats = seats[seats[acc_col] == account_id] if acc_col in seats.columns else seats.iloc[0:0]
    arpu = float(acc_seats["seat_arpu_monthly"].mean()) if not acc_seats.empty else 50.0
    monthly_margin = arpu * 0.65  # teaching gross margin
    mean_cost = p * monthly_margin * horizon_months
    width = (pred["ci95"][1] - pred["ci95"][0]) * monthly_margin * horizon_months / 2
    return {
        "mean_usd": round(mean_cost, 2),
        "ci95_usd": [round(max(0, mean_cost - width), 2), round(mean_cost + width, 2)],
        "horizon_months": horizon_months,
        "p_churn_30d": p,
    }


def fit_cox_summary(workspace: Workspace) -> dict[str, Any] | None:
    """Optional Cox PH summary when lifelines + sufficient data."""
    try:
        from lifelines import CoxPHFitter
    except ImportError:
        return None

    panel = account_week_panel(workspace)
    if panel.empty or panel["account_id"].nunique() < 10:
        return None

    agg = (
        panel.groupby("account_id", as_index=False)
        .agg(
            delegation_ratio=("delegation_ratio", "mean"),
            autonomy_ratio=("autonomy_ratio", "mean"),
            cpso=("cpso", "mean"),
            churned=("churned", "max"),
            weeks=("week", "count"),
        )
    )
    agg = agg.rename(columns={"weeks": "duration"})
    agg["duration"] = agg["duration"].clip(lower=1)
    if agg["churned"].sum() < 2:
        return None

    cph = CoxPHFitter()
    try:
        cph.fit(
            agg[["duration", "churned", "delegation_ratio", "autonomy_ratio", "cpso"]],
            duration_col="duration",
            event_col="churned",
        )
        return {"summary": cph.summary.to_dict(), "concordance": float(cph.concordance_index_)}
    except Exception:
        return None
