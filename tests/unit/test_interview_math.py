"""Tests for decision curves, knapsack, and calibration."""

import numpy as np
import pytest

from analytics.agentic_profile import get_preset
from analytics.decision_curves import net_benefit_curve, operating_point_from_semantics, optimal_threshold
from analytics.decisions import emit_account_records
from analytics.knapsack import select_interventions_gdr
from analytics.survival import calibration_metrics, fit_discrete_hazard_mle
from core.workspace import build_workspace
from data.ground_truth import get as get_ground_truth


def test_net_benefit_peaks_at_sensible_threshold():
    y_true = [1, 1, 0, 0, 0, 0, 1, 0]
    y_score = [0.9, 0.8, 0.7, 0.2, 0.1, 0.15, 0.85, 0.05]
    curve = net_benefit_curve(y_true, y_score, cost_fp=1.0, cost_fn=5.0)
    best = optimal_threshold(curve)
    assert best is not None
    assert 0.5 <= best["threshold"] <= 0.95


def test_operating_point_from_semantics():
    op = operating_point_from_semantics({
        "classification": {"posterior_thresholds": {"p_churn_30d_min": 0.35}},
    })
    assert op["p_churn_30d_min"] == 0.35


def test_knapsack_selects_highest_value():
    records = [
        {"record_id": "a", "economics": {"primary_metric_usd": 100}, "p_churn_30d": 0.8, "exceptions": []},
        {"record_id": "b", "economics": {"primary_metric_usd": 50}, "p_churn_30d": 0.2, "exceptions": []},
        {"record_id": "c", "economics": {"primary_metric_usd": 200}, "p_churn_30d": 0.9, "exceptions": []},
    ]
    out = select_interventions_gdr(records, hitl_capacity=2)
    ids = out["selected_ids"]
    assert "c" in ids
    assert len(ids) == 2


def test_calibration_metrics_perfect():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.0, 0.0, 1.0, 1.0])
    m = calibration_metrics(y, p)
    assert m["brier"] == 0.0
    assert m["ece"] == 0.0


@pytest.mark.slow
def test_fit_discrete_hazard_mle_runs():
    profile = get_preset("assistant_heavy")
    profile["priors"]["math_mode"] = "rigorous"
    ws = build_workspace(profile, seed=42, n_sessions=100)
    fit = fit_discrete_hazard_mle(ws)
    assert "fitted" in fit
    gt = get_ground_truth(ws.seed)
    if gt and fit.get("fitted"):
        assert fit.get("n_accounts", 0) > 0
