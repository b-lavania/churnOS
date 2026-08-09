"""Tests for planted ground truth."""

import pytest

from data.ground_truth import GroundTruth, register, get, clear
from analytics.agentic_profile import get_preset
from core.workspace import build_workspace


def test_register_and_get():
    clear()
    register(GroundTruth(seed=99, population_churn_rate=0.1))
    gt = get(99)
    assert gt is not None
    assert gt.population_churn_rate == 0.1


@pytest.mark.slow
def test_agentic_generator_plants_ground_truth():
    clear()
    profile = get_preset("assistant_heavy")
    build_workspace(profile, seed=7, n_sessions=80)
    gt = get(7)
    assert gt is not None
    assert gt.experiment_id == "EXP-CAP-VERSION-001"
    assert len(gt.account_hazard_multipliers) > 0
