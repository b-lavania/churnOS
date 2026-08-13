"""Bootstrap CM-NRR and conformal CPSO for stochastic economics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.workspace import Workspace


def _seat_cpso(runs: pd.DataFrame, seats: pd.DataFrame) -> np.ndarray:
    if runs.empty or seats.empty:
        return np.array([0.0])
    merged = runs.merge(seats[["seat_id", "seat_arpu_monthly"]], on="seat_id", how="left")
    costs = []
    for seat_id, grp in merged.groupby("seat_id"):
        cost = float(grp["run_cost_usd"].sum()) if "run_cost_usd" in grp.columns else 0.0
        n_ok = max(1, int(grp["success"].sum()) if "success" in grp.columns else 1)
        costs.append(cost / n_ok)
    return np.array(costs) if costs else np.array([0.0])


def bootstrap_cm_nrr(
    workspace: Workspace,
    *,
    n_boot: int = 500,
    seed: int = 42,
) -> dict[str, Any]:
    """Bootstrap P(CM_NRR < 1.0) from seat margins."""
    rng = np.random.default_rng(seed)
    seats = workspace.seats
    runs = workspace.runs
    subs = getattr(workspace, "subscriptions", pd.DataFrame())

    if seats.empty:
        return {"p_cm_nrr_below_1": 0.0, "cm_nrr_mean": 1.0, "cm_nrr_ci90": [0.9, 1.1]}

    arpu = seats["seat_arpu_monthly"].values if "seat_arpu_monthly" in seats.columns else np.full(len(seats), 50.0)
    cpso_vals = _seat_cpso(runs, seats)
    margin_ratio = np.clip(arpu.mean() / max(cpso_vals.mean(), 1.0), 0.5, 2.0)

    expansion = 1.05
    if not subs.empty and "mrr_usd" in subs.columns:
        expansion = float(subs["mrr_usd"].sum() / max(subs["mrr_usd"].iloc[0], 1))

    samples = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(cpso_vals), size=len(cpso_vals))
        boot_cpso = cpso_vals[idx].mean()
        boot_nrr = margin_ratio * expansion * (1 - rng.normal(0, 0.02))
        cm_nrr = boot_nrr / max(boot_cpso / max(arpu.mean(), 1), 0.5)
        samples.append(cm_nrr)

    arr = np.array(samples)
    lo, hi = np.percentile(arr, [5, 95])
    return {
        "p_cm_nrr_below_1": float((arr < 1.0).mean()),
        "cm_nrr_mean": float(arr.mean()),
        "cm_nrr_ci90": [round(float(lo), 3), round(float(hi), 3)],
        "n_boot": n_boot,
    }


def conformal_cpso_band(
    workspace: Workspace,
    *,
    alpha: float = 0.10,
) -> dict[str, Any]:
    """Split-conformal 90% band on CPSO from seat-level costs."""
    seats = workspace.seats
    runs = workspace.runs
    cpso_vals = _seat_cpso(runs, seats)
    if len(cpso_vals) < 5:
        mean = float(cpso_vals.mean())
        return {"cpso_mean": mean, "cpso_ci90": [mean * 0.8, mean * 1.2]}

    n = len(cpso_vals)
    split = n // 2
    cal = cpso_vals[:split]
    test = cpso_vals[split:]
    q = np.quantile(np.abs(test - cal.mean()), 1 - alpha)
    mean = float(cpso_vals.mean())
    return {
        "cpso_mean": round(mean, 2),
        "cpso_ci90": [round(max(0, mean - q), 2), round(mean + q, 2)],
    }


def _account_churn_labels(workspace: Workspace) -> tuple[list[str], np.ndarray]:
    seats = workspace.seats
    if seats.empty:
        return [], np.array([])
    acc_col = "workspace_id" if "workspace_id" in seats.columns else "account_id"
    labels = []
    y = []
    for acc_id, grp in seats.groupby(acc_col):
        labels.append(str(acc_id))
        churned = bool(grp["is_churned"].any()) if "is_churned" in grp.columns else False
        y.append(int(churned))
    return labels, np.array(y, dtype=float)


def conformal_churn_risk_band(
    workspace: Workspace,
    account_id: str,
    *,
    alpha: float = 0.10,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Split-conformal band on P(churn_30d) across accounts."""
    from analytics.survival import predict_churn_30d

    profile = profile or workspace.profile
    labels, y = _account_churn_labels(workspace)
    if len(labels) < 6:
        pred = predict_churn_30d(workspace, account_id, profile)
        p = pred["p_churn_30d"]
        w = 0.1
        return {"point": p, "ci90": [max(0, p - w), min(1, p + w)], "method": "fallback"}

    scores = np.array([
        predict_churn_30d(workspace, acc, profile)["p_churn_30d"] for acc in labels
    ])
    n = len(scores)
    split = n // 2
    cal_scores, cal_y = scores[:split], y[:split]
    test_scores, test_y = scores[split:], y[split:]
    residuals = np.abs(test_y - cal_scores[: len(test_y)])
    if len(residuals) == 0:
        q = 0.1
    else:
        q = float(np.quantile(residuals, 1 - alpha))
    point = predict_churn_30d(workspace, account_id, profile)["p_churn_30d"]
    return {
        "point": round(point, 4),
        "ci90": [round(max(0.0, point - q), 4), round(min(1.0, point + q), 4)],
        "method": "split_conformal",
        "alpha": alpha,
    }


def conformal_cost_of_leaving_band(
    workspace: Workspace,
    account_id: str,
    *,
    alpha: float = 0.10,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Conformal band on survival-priced cost_of_leaving across accounts."""
    from analytics.survival import survival_priced_cost

    profile = profile or workspace.profile
    seats = workspace.seats
    if seats.empty:
        return {"point_usd": 0.0, "ci90_usd": [0.0, 0.0]}

    acc_col = "workspace_id" if "workspace_id" in seats.columns else "account_id"
    accounts = seats[acc_col].astype(str).unique().tolist()
    costs = np.array([
        survival_priced_cost(workspace, acc)["mean_usd"] for acc in accounts
    ])
    if len(costs) < 6:
        point = survival_priced_cost(workspace, account_id)["mean_usd"]
        w = point * 0.25
        return {"point_usd": point, "ci90_usd": [max(0, point - w), point + w]}

    n = len(costs)
    split = n // 2
    cal, test = costs[:split], costs[split:]
    q = float(np.quantile(np.abs(test - cal.mean()), 1 - alpha))
    point = survival_priced_cost(workspace, account_id)["mean_usd"]
    return {
        "point_usd": round(point, 2),
        "ci90_usd": [round(max(0, point - q), 2), round(point + q, 2)],
        "method": "split_conformal",
    }
