"""Account risk scoring — heuristic v0 or rigorous hazard mode."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics.evidence import is_rigorous_mode, pack_evidence
from analytics.survival import predict_churn_30d, survival_priced_cost
from analytics.stochastic_economics import conformal_churn_risk_band, conformal_cost_of_leaving_band
from core.workspace import Workspace

WEIGHTS = {
    "delegation_decline": 0.35,
    "days_since_success": 0.25,
    "autonomy_decline": 0.20,
    "margin_breach": 0.10,
    "payment_flag": 0.10,
}


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def account_risk_components(workspace: Workspace, account_id: str) -> dict[str, float]:
    """Per-account risk components normalized 0–1."""
    seats = workspace.seats
    if "workspace_id" in seats.columns:
        acc_seats = seats[seats["workspace_id"] == account_id]
    elif "account_id" in seats.columns:
        acc_seats = seats[seats["account_id"] == account_id]
    else:
        acc_seats = seats.iloc[0:0]

    runs = workspace.runs
    if acc_seats.empty:
        return {k: 0.0 for k in WEIGHTS}

    seat_ids = acc_seats["seat_id"].unique()
    acc_runs = runs[runs["seat_id"].isin(seat_ids)] if not runs.empty else runs

    delegation = 0.5
    if "weekly_delegation" in acc_seats.columns and "is_activated" in acc_seats.columns:
        active = acc_seats[acc_seats["is_activated"]]
        delegation = float(active["weekly_delegation"].mean()) if len(active) else 0.0
    delegation_decline = _clamp01(1.0 - delegation)

    days_since_success = 0.0
    if not getattr(workspace, "outcomes", pd.DataFrame()).empty:
        outs = workspace.outcomes
        if "account_id" in outs.columns:
            acc_out = outs[(outs["account_id"] == account_id) & (outs.get("success", outs.get("outcome_status", pd.Series())) == True)]  # noqa: E712
        else:
            acc_out = outs[outs["seat_id"].isin(seat_ids)] if "seat_id" in outs.columns else outs.iloc[0:0]
        if not acc_out.empty and "occurred_at" in acc_out.columns:
            last = pd.to_datetime(acc_out["occurred_at"]).max()
            days = (pd.Timestamp.utcnow() - last).days
            days_since_success = _clamp01(days / 14.0)

    autonomy_ratio = 0.7
    if not acc_runs.empty and "success" in acc_runs.columns:
        hitl = acc_runs.get("hitl_triggered", pd.Series([False] * len(acc_runs)))
        ok = acc_runs["success"].astype(bool) & ~hitl.astype(bool)
        autonomy_ratio = float(ok.mean()) if len(acc_runs) else 0.7
    autonomy_decline = _clamp01(1.0 - autonomy_ratio)

    arpu = float(acc_seats["seat_arpu_monthly"].mean()) if "seat_arpu_monthly" in acc_seats.columns else 50.0
    run_cost = float(acc_runs["run_cost_usd"].sum()) if not acc_runs.empty and "run_cost_usd" in acc_runs.columns else 0.0
    n_success = 1
    if not getattr(workspace, "outcomes", pd.DataFrame()).empty:
        o = workspace.outcomes
        if "account_id" in o.columns:
            n_success = max(1, len(o[(o["account_id"] == account_id) & (o.get("success", True))]))
    cpso = run_cost / n_success
    margin_breach = 1.0 if arpu > 0 and cpso > arpu * 0.5 else 0.0

    payment_flag = 0.0
    if not getattr(workspace, "subscriptions", pd.DataFrame()).empty:
        subs = workspace.subscriptions
        if "account_id" in subs.columns and "payment_failed" in subs.columns:
            if subs[(subs["account_id"] == account_id) & subs["payment_failed"]].shape[0] > 0:
                payment_flag = 1.0

    return {
        "delegation_decline": delegation_decline,
        "days_since_success": days_since_success,
        "autonomy_decline": autonomy_decline,
        "margin_breach": margin_breach,
        "payment_flag": payment_flag,
    }


def account_risk_score_heuristic(workspace: Workspace, account_id: str) -> float:
    comp = account_risk_components(workspace, account_id)
    return round(sum(WEIGHTS[k] * comp[k] for k in WEIGHTS), 3)


def account_risk_score(workspace: Workspace, account_id: str, profile: dict[str, Any] | None = None) -> float:
    profile = profile or workspace.profile
    if is_rigorous_mode(profile):
        pred = predict_churn_30d(workspace, account_id, profile)
        return pred["p_churn_30d"]
    return account_risk_score_heuristic(workspace, account_id)


def account_risk_detail(
    workspace: Workspace,
    account_id: str,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full risk payload for UI and GDR enrichment."""
    profile = profile or workspace.profile
    if is_rigorous_mode(profile):
        pred = predict_churn_30d(workspace, account_id, profile)
        cost = survival_priced_cost(workspace, account_id)
        risk_band = conformal_churn_risk_band(workspace, account_id, profile=profile)
        cost_band = conformal_cost_of_leaving_band(workspace, account_id, profile=profile)
        ci = risk_band.get("ci90", pred["ci95"])
        cost_ci = cost_band.get("ci90_usd", cost["ci95_usd"])
        evidence = pack_evidence(
            model_id=pred["model_id"],
            claim_type="simulated",
            estimand="p_churn_30d",
            posterior_mean=pred["p_churn_30d"],
            ci95=ci,
            n=pred["n_runs"],
        )
        return {
            "risk_score": pred["p_churn_30d"],
            "p_churn_30d": pred["p_churn_30d"],
            "ci95": ci,
            "baseline_p": pred["baseline_p"],
            "cost_mean_usd": cost_band.get("point_usd", cost["mean_usd"]),
            "cost_ci95_usd": cost_ci,
            "evidence": evidence,
            "attributions": pred.get("attributions", []),
            "calibration": pred.get("calibration"),
            "mode": "rigorous",
        }
    score = account_risk_score_heuristic(workspace, account_id)
    return {"risk_score": score, "mode": "heuristic"}


def primary_signal_from_exceptions(exceptions: list[dict[str, Any]]) -> str:
    if not exceptions:
        return "—"
    top = sorted(exceptions, key=lambda e: -(e.get("impact", {}).get("cost_usd", 0)))[0]
    return top.get("category", top.get("title", "—"))


def enrich_account_records(
    records: list[dict[str, Any]],
    workspace: Workspace,
) -> list[dict[str, Any]]:
    """Attach risk_score, survival detail, primary_signal; sort by risk×$."""
    profile = workspace.profile
    enriched = []
    for rec in records:
        acc_id = rec.get("subject", {}).get("account_id", "")
        detail = account_risk_detail(workspace, acc_id, profile) if acc_id else {"risk_score": 0.0}
        signal = primary_signal_from_exceptions(rec.get("exceptions", []))
        updated = dict(rec)
        updated["risk_score"] = detail.get("risk_score", 0.0)
        updated["primary_signal"] = signal
        if detail.get("p_churn_30d") is not None:
            updated["p_churn_30d"] = detail["p_churn_30d"]
            updated["p_churn_ci95"] = detail.get("ci95")
            updated["cost_ci95_usd"] = detail.get("cost_ci95_usd")
            updated["attributions"] = detail.get("attributions", [])
        if detail.get("evidence"):
            updated["evidence"] = detail["evidence"]
            econ = dict(updated.get("economics") or {})
            if detail.get("cost_mean_usd"):
                econ["primary_metric_usd"] = detail["cost_mean_usd"]
                econ["primary_metric_ci95_usd"] = detail.get("cost_ci95_usd")
            updated["economics"] = econ
        enriched.append(updated)
    enriched.sort(
        key=lambda r: (
            -r.get("risk_score", 0) * r.get("economics", {}).get("primary_metric_usd", 0),
            -r.get("economics", {}).get("primary_metric_usd", 0),
        )
    )
    return enriched
