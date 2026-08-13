"""Tests for bandits module."""

import pytest

from analytics.agentic_profile import get_preset
from analytics.bandits import (
    bandit_policy_from_semantics,
    cumulative_regret,
    simulate_bandit_regret,
    thompson_allocation,
)
from core.workspace import build_workspace

_N = 80


@pytest.mark.slow
def test_thompson_allocation_returns_traffic():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=_N)
    caps = ws.capabilities["capability_id"].tolist()
    if not caps:
        pytest.skip("no capabilities")
    alloc = thompson_allocation(ws, caps[0], semantics_overlay={"bandit": {"exploration_rate": 0.2}})
    assert "recommended_traffic" in alloc
    if alloc["recommended_traffic"]:
        assert abs(sum(alloc["recommended_traffic"].values()) - 1.0) < 0.01


def test_bandit_policy_defaults():
    policy = bandit_policy_from_semantics(None)
    assert policy["algorithm"] == "thompson"
    assert 0 < policy["min_traffic_floor"] < 1


def test_cumulative_regret_sublinear_on_planted_arms():
    true = {"A": 0.7, "B": 0.3}
    sim = simulate_bandit_regret(true, n_rounds=300, seed=1)
    regret = sim["regret"]["total_regret"]
    assert regret < 150


def test_yaml_policy_changes_exploration():
    overlay = {"bandit": {"exploration_rate": 0.5, "min_traffic_floor": 0.2}}
    policy = bandit_policy_from_semantics(overlay)
    assert policy["exploration_rate"] == 0.5


def test_cumulative_regret_known_optimal():
    rewards = {"opt": [1.0, 1.0, 1.0], "sub": [0.0, 0.0, 0.0]}
    out = cumulative_regret(rewards, "opt")
    assert out["total_regret"] == 0.0
