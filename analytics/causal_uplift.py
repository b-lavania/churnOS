"""Experiment-gated uplift estimation for capability harm claims."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.workspace import Workspace


def _simple_uplift(ctrl_runs: pd.DataFrame, var_runs: pd.DataFrame) -> dict[str, Any]:
    p_ctrl = float(ctrl_runs["success"].mean())
    p_var = float(var_runs["success"].mean())
    uplift = p_var - p_ctrl
    return {
        "uplift_pp": round(uplift, 4),
        "control_rate": round(p_ctrl, 4),
        "variant_rate": round(p_var, 4),
        "model_id": "uplift_diff_v0",
    }


def _tlearner_uplift(
    ctrl_runs: pd.DataFrame,
    var_runs: pd.DataFrame,
) -> dict[str, Any] | None:
    """GradientBoosting T-learner when n >= 200 runs."""
    n_total = len(ctrl_runs) + len(var_runs)
    if n_total < 200:
        return None

    try:
        from sklearn.ensemble import GradientBoostingClassifier
    except ImportError:
        return None

    def _features(df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "cost": df["run_cost_usd"].fillna(0) if "run_cost_usd" in df.columns else 0,
            "loops": df["loop_count"].fillna(1) if "loop_count" in df.columns else 1,
            "latency": (df["latency_ms"].fillna(500) / 1000.0) if "latency_ms" in df.columns else 0.5,
        })

    X0 = _features(ctrl_runs)
    X1 = _features(var_runs)
    y0 = ctrl_runs["success"].astype(int).values
    y1 = var_runs["success"].astype(int).values

    m0 = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
    m1 = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=43)
    m0.fit(X0, y0)
    m1.fit(X1, y1)

    X_all = pd.concat([X0, X1], ignore_index=True)
    uplift = float((m1.predict_proba(X_all)[:, 1] - m0.predict_proba(X_all)[:, 1]).mean())
    return {
        "uplift_pp": round(uplift, 4),
        "control_rate": round(float(y0.mean()), 4),
        "variant_rate": round(float(y1.mean()), 4),
        "model_id": "uplift_tlearner_gbm_v1",
    }


def estimate_uplift(
    workspace: Workspace,
    *,
    experiment_id: str | None = None,
) -> dict[str, Any]:
    """
    T-learner style uplift on experiment assignments when powered.
    Falls back to simple diff when n < 200.
    """
    exp_id = experiment_id or workspace.default_experiment_id
    assigns = workspace.experiment_assignments
    runs = workspace.runs

    if assigns.empty or runs.empty or "variant" not in assigns.columns:
        return {
            "uplift_pp": None,
            "claim_type": "associational",
            "message": "No experiment assignments — uplift unavailable.",
        }

    sub = assigns[assigns["experiment_id"] == exp_id] if "experiment_id" in assigns.columns else assigns
    if sub.empty:
        return {"uplift_pp": None, "claim_type": "associational", "message": "Experiment not found."}

    ctrl_seats = set(sub.loc[sub["variant"] == "control", "seat_id"])
    var_seats = set(sub.loc[sub["variant"] == "variant", "seat_id"])
    ctrl_runs = runs[runs["seat_id"].isin(ctrl_seats)]
    var_runs = runs[runs["seat_id"].isin(var_seats)]

    if len(ctrl_runs) < 5 or len(var_runs) < 5:
        return {
            "uplift_pp": None,
            "claim_type": "causal" if experiment_id else "associational",
            "experiment_id": exp_id,
            "message": "Underpowered for uplift.",
        }

    result = _tlearner_uplift(ctrl_runs, var_runs) or _simple_uplift(ctrl_runs, var_runs)
    uplift = result["uplift_pp"]

    return {
        **result,
        "claim_type": "causal",
        "experiment_id": exp_id,
        "n_control": len(ctrl_runs),
        "n_variant": len(var_runs),
        "message": f"Treatment uplift on success: {uplift:+.1%}pp ({result['model_id']}).",
    }
