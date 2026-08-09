"""Property tests for Beta–Binomial posterior recovery."""

import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

from analytics.inference.binomial import beta_binomial_posterior
from analytics.agentic_profile import get_preset
from core.workspace import build_workspace
from data.ground_truth import get, clear


@given(p=st.floats(min_value=0.05, max_value=0.4))
@settings(max_examples=20, deadline=None)
def test_posterior_mean_near_true_rate(p):
    n = 500
    successes = int(n * p)
    post = beta_binomial_posterior(successes, n)
    assert abs(post["mean"] - p) < 0.05


@pytest.mark.slow
def test_ground_truth_recovery_default_seed():
    clear()
    profile = get_preset("assistant_heavy")
    profile["priors"]["math_mode"] = "heuristic"
    ws = build_workspace(profile, seed=42, n_sessions=200)
    gt = get(42)
    assert gt is not None
    churned = int(ws.seats["is_churned"].sum())
    n = len(ws.seats)
    post = beta_binomial_posterior(churned, n)
    assert abs(post["mean"] - gt.population_churn_rate) < 0.08
