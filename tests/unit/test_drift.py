"""Tests for distributional drift."""

import numpy as np
import pytest

from analytics.agentic_profile import get_preset
from analytics.drift import cusum_change_point, js_divergence, kl_divergence, window_drift
from core.workspace import build_workspace


def test_kl_js_identical():
    p = np.array([0.5, 0.5])
    assert kl_divergence(p, p) == 0.0
    assert js_divergence(p, p) == 0.0


def test_window_drift_different():
    d = window_drift(np.array([0.9, 0.1]), np.array([0.1, 0.9]))
    assert d["js"] > 0.1


def test_cusum_finds_shift():
    series = [0.5] * 10 + [0.9] * 10
    cp = cusum_change_point(series, threshold=0.03)
    assert cp is not None
    assert 8 <= cp <= 12


@pytest.mark.slow
def test_outcome_drift_on_workspace():
    from analytics.drift import outcome_distribution_drift

    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=80)
    od = outcome_distribution_drift(ws)
    assert "js" in od
    assert "kl" in od
