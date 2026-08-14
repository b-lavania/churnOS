"""Tests for token-cost VaR/CVaR."""

import pandas as pd
import pytest

from analytics.agentic_profile import get_preset
from analytics.token_risk import daily_spend_series, pricing_shock_simulation, token_cost_var
from core.workspace import build_workspace


def test_token_cost_var_on_series():
    daily = pd.Series([10.0, 12.0, 8.0, 15.0, 11.0])
    out = token_cost_var(daily, n_boot=100, seed=1)
    assert out["var"] >= 0
    assert out["cvar"] <= out["var"]


@pytest.mark.slow
def test_daily_spend_and_shock():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=80)
    daily = daily_spend_series(ws)
    if not daily.empty:
        base = token_cost_var(daily, n_boot=50)
        shocked = pricing_shock_simulation(ws, shock_pct=0.5)
        assert shocked["mean_daily"] >= base["mean"]
