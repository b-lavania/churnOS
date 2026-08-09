"""Tests for survival / hazard module."""

import pytest

from analytics.agentic_profile import get_preset
from analytics.account_risk import account_risk_detail, enrich_account_records
from analytics.survival import predict_churn_30d, survival_priced_cost
from core.workspace import build_workspace

_N = 80


@pytest.mark.slow
def test_predict_churn_30d_bounds():
    profile = get_preset("assistant_heavy")
    profile["priors"]["math_mode"] = "rigorous"
    ws = build_workspace(profile, seed=42, n_sessions=_N)
    acc_id = ws.workspaces["workspace_id"].iloc[0]
    pred = predict_churn_30d(ws, acc_id)
    assert 0 <= pred["p_churn_30d"] <= 1
    assert pred["ci95"][0] <= pred["p_churn_30d"] <= pred["ci95"][1]


@pytest.mark.slow
def test_rigorous_enrich_adds_evidence():
    profile = get_preset("assistant_heavy")
    profile["priors"]["math_mode"] = "rigorous"
    ws = build_workspace(profile, seed=42, n_sessions=_N)
    from analytics.decisions import emit_account_records

    recs = emit_account_records(ws, profile)
    enriched = enrich_account_records(recs[:3], ws)
    assert any(r.get("evidence") for r in enriched)
    assert any(r.get("p_churn_30d") is not None for r in enriched)


@pytest.mark.slow
def test_survival_priced_cost_positive():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=_N)
    acc_id = ws.workspaces["workspace_id"].iloc[0]
    cost = survival_priced_cost(ws, acc_id)
    assert cost["mean_usd"] >= 0
