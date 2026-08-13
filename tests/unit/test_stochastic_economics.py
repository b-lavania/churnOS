"""Tests for stochastic economics module."""

import pytest

from analytics.agentic_profile import get_preset
from analytics.stochastic_economics import (
    bootstrap_cm_nrr,
    conformal_churn_risk_band,
    conformal_cost_of_leaving_band,
    conformal_cpso_band,
)
from core.workspace import build_workspace


@pytest.mark.slow
def test_bootstrap_cm_nrr():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=80)
    out = bootstrap_cm_nrr(ws, n_boot=50)
    assert 0 <= out["p_cm_nrr_below_1"] <= 1
    assert out["cm_nrr_ci90"][0] <= out["cm_nrr_mean"] <= out["cm_nrr_ci90"][1]


@pytest.mark.slow
def test_conformal_cpso_band():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=80)
    band = conformal_cpso_band(ws)
    assert band["cpso_ci90"][0] <= band["cpso_mean"] <= band["cpso_ci90"][1]


@pytest.mark.slow
def test_conformal_churn_risk_band():
    profile = get_preset("assistant_heavy")
    profile["priors"]["math_mode"] = "rigorous"
    ws = build_workspace(profile, seed=42, n_sessions=80)
    acc = ws.workspaces["workspace_id"].iloc[0]
    band = conformal_churn_risk_band(ws, acc, profile=profile)
    assert band["ci90"][0] <= band["point"] <= band["ci90"][1]


@pytest.mark.slow
def test_conformal_cost_band():
    profile = get_preset("assistant_heavy")
    profile["priors"]["math_mode"] = "rigorous"
    ws = build_workspace(profile, seed=42, n_sessions=80)
    acc = ws.workspaces["workspace_id"].iloc[0]
    band = conformal_cost_of_leaving_band(ws, acc, profile=profile)
    assert band["ci90_usd"][0] <= band["point_usd"] <= band["ci90_usd"][1]
