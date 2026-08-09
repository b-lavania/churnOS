"""
Panel builders for rigorous survival and experimentation analysis.
"""

from __future__ import annotations

import pandas as pd

from core.workspace import Workspace


def _account_id_col(seats: pd.DataFrame) -> str:
    if "account_id" in seats.columns:
        return "account_id"
    if "workspace_id" in seats.columns:
        return "workspace_id"
    return "seat_id"


def account_week_panel(workspace: Workspace) -> pd.DataFrame:
    """
    Account-week panel with churn, delegation, autonomy, CPSO, outcome success.
    """
    seats = workspace.seats
    runs = workspace.runs
    if seats.empty:
        return pd.DataFrame(
            columns=[
                "account_id", "week", "churned", "delegation_ratio",
                "autonomy_ratio", "cpso", "outcome_success_rate", "arpu", "n_runs",
            ]
        )

    acc_col = _account_id_col(seats)
    seats = seats.copy()
    if acc_col == "workspace_id":
        seats["account_id"] = seats["workspace_id"]
    else:
        seats["account_id"] = seats[acc_col]

    ref_end = pd.Timestamp("2025-12-31")
    if not runs.empty and "started_at" in runs.columns:
        ref_end = max(ref_end, pd.to_datetime(runs["started_at"]).max())

    rows: list[dict] = []
    for acc_id, acc_seats in seats.groupby("account_id"):
        seat_ids = acc_seats["seat_id"].unique()
        acc_runs = runs[runs["seat_id"].isin(seat_ids)] if not runs.empty else runs
        arpu = float(acc_seats["seat_arpu_monthly"].mean()) if "seat_arpu_monthly" in acc_seats.columns else 50.0
        churned = bool(acc_seats["is_churned"].any()) if "is_churned" in acc_seats.columns else False

        if acc_runs.empty:
            rows.append({
                "account_id": acc_id,
                "week": ref_end.floor("W"),
                "churned": int(churned),
                "delegation_ratio": 0.5,
                "autonomy_ratio": 0.7,
                "cpso": 0.0,
                "outcome_success_rate": 0.0,
                "arpu": arpu,
                "n_runs": 0,
            })
            continue

        acc_runs = acc_runs.copy()
        acc_runs["started_at"] = pd.to_datetime(acc_runs["started_at"])
        acc_runs["week"] = acc_runs["started_at"].dt.to_period("W").dt.start_time

        delegation = 0.5
        if "weekly_delegation" in acc_seats.columns and "is_activated" in acc_seats.columns:
            active = acc_seats[acc_seats["is_activated"]]
            delegation = float(active["weekly_delegation"].mean()) if len(active) else 0.5

        for week, grp in acc_runs.groupby("week"):
            n = len(grp)
            sr = float(grp["success"].mean()) if "success" in grp.columns else 0.0
            cost = float(grp["run_cost_usd"].sum()) if "run_cost_usd" in grp.columns else 0.0
            n_ok = max(1, int(grp["success"].sum()) if "success" in grp.columns else 1)
            hitl = grp.get("hitl_triggered", pd.Series([False] * len(grp)))
            autonomy = float((grp["success"].astype(bool) & ~hitl.astype(bool)).mean()) if n else 0.7
            rows.append({
                "account_id": acc_id,
                "week": week,
                "churned": int(churned),
                "delegation_ratio": delegation,
                "autonomy_ratio": autonomy,
                "cpso": cost / n_ok,
                "outcome_success_rate": sr,
                "arpu": arpu,
                "n_runs": n,
            })

    return pd.DataFrame(rows)


def capability_version_panel(workspace: Workspace) -> pd.DataFrame:
    """Per-version run aggregates for sequential / version compare."""
    runs = workspace.runs
    if runs.empty or "capability_version_id" not in runs.columns:
        return pd.DataFrame(
            columns=[
                "capability_version_id", "n_runs", "n_success", "success_rate",
                "mean_cost", "hitl_rate",
            ]
        )

    rows = []
    for ver_id, grp in runs.groupby("capability_version_id"):
        n = len(grp)
        s = int(grp["success"].sum()) if "success" in grp.columns else 0
        cost = float(grp["run_cost_usd"].mean()) if "run_cost_usd" in grp.columns else 0.0
        hitl = float(grp["hitl_triggered"].mean()) if "hitl_triggered" in grp.columns else 0.0
        rows.append({
            "capability_version_id": ver_id,
            "n_runs": n,
            "n_success": s,
            "success_rate": s / n if n else 0.0,
            "mean_cost": cost,
            "hitl_rate": hitl,
        })
    return pd.DataFrame(rows)
