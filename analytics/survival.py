"""
Survival and hazard models for account-level retention (agentic core).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from analytics.panels import account_week_panel
from core.workspace import Workspace

FEATURE_COLS = ("delegation_ratio", "autonomy_ratio", "cpso", "activated")
_FIT_CACHE: dict[int, dict[str, Any]] = {}


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


def _hazard_training_frame(workspace: Workspace) -> pd.DataFrame:
    """Account-level rows for discrete-time hazard MLE."""
    panel = account_week_panel(workspace)
    if panel.empty:
        return pd.DataFrame(columns=[*FEATURE_COLS, "churned", "account_id"])

    agg = (
        panel.groupby("account_id", as_index=False)
        .agg(
            delegation_ratio=("delegation_ratio", "mean"),
            autonomy_ratio=("autonomy_ratio", "mean"),
            cpso=("cpso", "mean"),
            churned=("churned", "max"),
            n_runs=("n_runs", "sum"),
        )
    )
    seats = workspace.seats
    acc_col = "workspace_id" if "workspace_id" in seats.columns else "account_id"
    activated_map: dict[str, float] = {}
    if not seats.empty and "is_activated" in seats.columns:
        for acc_id, grp in seats.groupby(acc_col):
            activated_map[str(acc_id)] = float(grp["is_activated"].mean())
    agg["activated"] = agg["account_id"].astype(str).map(activated_map).fillna(0.5)
    return agg


def fit_discrete_hazard_mle(workspace: Workspace) -> dict[str, Any]:
    """
    Panel MLE via logistic regression on account-week aggregates.
    Cached per workspace seed for repeated Radar renders.
    """
    cache_key = int(getattr(workspace, "seed", 0) or 0)
    if cache_key in _FIT_CACHE:
        return _FIT_CACHE[cache_key]

    df = _hazard_training_frame(workspace)
    if len(df) < 8 or int(df["churned"].sum()) < 2:
        result = {"fitted": False, "model_id": "discrete_hazard_v1", "coefficients": {}}
        _FIT_CACHE[cache_key] = result
        return result

    from sklearn.linear_model import LogisticRegression

    x = df[list(FEATURE_COLS)].fillna(0.5).values
    y = df["churned"].astype(int).values
    clf = LogisticRegression(max_iter=500, random_state=42)
    clf.fit(x, y)
    y_pred = clf.predict_proba(x)[:, 1]
    cal = calibration_metrics(y, y_pred)
    result = {
        "fitted": True,
        "model_id": "discrete_hazard_mle_v1",
        "coefficients": dict(zip(FEATURE_COLS, clf.coef_[0].tolist())),
        "intercept": float(clf.intercept_[0]),
        "n_accounts": len(df),
        "n_events": int(y.sum()),
        "calibration": cal,
        "reliability": reliability_bins(y, y_pred),
        "_clf": clf,
    }
    _FIT_CACHE[cache_key] = result
    return result


def calibration_metrics(y_true: np.ndarray | list, y_pred: np.ndarray | list) -> dict[str, float]:
    """Brier score and expected calibration error."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.clip(np.asarray(y_pred, dtype=float), 1e-6, 1 - 1e-6)
    brier = float(np.mean((yp - yt) ** 2))
    n_bins = 10
    edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (yp >= lo) & (yp < hi if i < n_bins - 1 else yp <= hi)
        if not mask.any():
            continue
        ece += mask.mean() * abs(float(yp[mask].mean()) - float(yt[mask].mean()))
    return {"brier": round(brier, 4), "ece": round(float(ece), 4), "n": int(len(yt))}


def reliability_bins(
    y_true: np.ndarray | list,
    y_pred: np.ndarray | list,
    *,
    n_bins: int = 10,
) -> list[dict[str, float]]:
    """Reliability diagram bin centers for Math Lab."""
    yt = np.asarray(y_true, dtype=float)
    yp = np.clip(np.asarray(y_pred, dtype=float), 0, 1)
    edges = np.linspace(0, 1, n_bins + 1)
    bins: list[dict[str, float]] = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (yp >= lo) & (yp < hi if i < n_bins - 1 else yp <= hi)
        if not mask.any():
            continue
        bins.append({
            "bin_center": round(float((lo + hi) / 2), 3),
            "predicted_mean": round(float(yp[mask].mean()), 4),
            "observed_rate": round(float(yt[mask].mean()), 4),
            "count": int(mask.sum()),
        })
    return bins


def isotonic_recalibrate(
    y_true: np.ndarray | list,
    y_pred: np.ndarray | list,
) -> dict[str, Any]:
    """Fit isotonic recalibration mapping raw scores → calibrated probs."""
    from sklearn.isotonic import IsotonicRegression

    yt = np.asarray(y_true, dtype=float)
    yp = np.clip(np.asarray(y_pred, dtype=float), 0, 1)
    if len(yt) < 5:
        return {"calibrated": False, "model": None}
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(yp, yt)
    return {"calibrated": True, "model": iso}


def _score_from_fit(features: dict[str, float], fit: dict[str, Any]) -> float | None:
    if not fit.get("fitted"):
        return None
    clf = fit.get("_clf")
    if clf is None:
        return None
    row = [[features.get(c.replace("_ratio", ""), features.get(c, 0.5)) for c in FEATURE_COLS]]
    # map feature names to keys in features dict
    vec = [
        features.get("delegation", features.get("delegation_ratio", 0.5)),
        features.get("autonomy", features.get("autonomy_ratio", 0.7)),
        features.get("cpso_ratio", features.get("cpso", 0.0)),
        features.get("activated", 0.5),
    ]
    return float(clf.predict_proba([vec])[0, 1])


def hazard_permutation_importance(
    workspace: Workspace,
    account_id: str,
    fit: dict[str, Any] | None = None,
    *,
    n_repeats: int = 8,
    seed: int = 42,
) -> list[dict[str, float]]:
    """Permutation importance on fitted hazard — lightweight SHAP substitute."""
    fit = fit or fit_discrete_hazard_mle(workspace)
    if not fit.get("fitted"):
        return []
    feats = _account_features(workspace, account_id)
    base = _score_from_fit(feats, fit)
    if base is None:
        return []

    rng = np.random.default_rng(seed)
    panel = _hazard_training_frame(workspace)
    importances: list[dict[str, float]] = []
    feat_keys = [
        ("delegation", "delegation"),
        ("autonomy", "autonomy"),
        ("cpso_ratio", "cpso_ratio"),
        ("activated", "activated"),
    ]
    for label, key in feat_keys:
        deltas = []
        for _ in range(n_repeats):
            perturbed = dict(feats)
            if not panel.empty and key in ("delegation", "autonomy", "cpso_ratio"):
                col = {"delegation": "delegation_ratio", "autonomy": "autonomy_ratio", "cpso_ratio": "cpso"}[key]
                perturbed[key] = float(rng.choice(panel[col].values))
            else:
                perturbed[key] = float(rng.uniform(0, 1))
            score = _score_from_fit(perturbed, fit)
            if score is not None:
                deltas.append(abs(score - base))
        importances.append({
            "feature": label,
            "importance": round(float(np.mean(deltas)) if deltas else 0.0, 4),
            "direction": "increases_risk" if feats.get(key, 0) < 0.5 else "decreases_risk",
        })
    importances.sort(key=lambda x: -x["importance"])
    return importances[:5]


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
    calibration: dict[str, Any] | None = None
    attributions: list[dict[str, float]] = []

    if profile is not None:
        from analytics.evidence import is_rigorous_mode

        if is_rigorous_mode(profile):
            fit = fit_discrete_hazard_mle(workspace)
            fitted_p = _score_from_fit(feats, fit)
            if fitted_p is not None:
                p = round(fitted_p, 4)
                model_id = fit.get("model_id", "discrete_hazard_mle_v1")
                calibration = fit.get("calibration")
            cox_h = _cox_account_hazard(workspace, account_id)
            if cox_h is not None:
                p = round(0.7 * p + 0.3 * cox_h, 4)
                model_id = f"{model_id}+cox"
            attributions = hazard_permutation_importance(workspace, account_id, fit)
            try:
                from analytics.stochastic_economics import conformal_churn_risk_band

                band = conformal_churn_risk_band(workspace, account_id, profile=profile)
                lo, hi = band["ci90"]
                width = (hi - lo) / 2
            except Exception:
                width = max(width, 0.05)
            lo = max(0.0, p - width)
            hi = min(1.0, p + width)
        else:
            lo = max(0.0, p - width)
            hi = min(1.0, p + width)
    else:
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
        "calibration": calibration,
        "attributions": attributions,
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
