"""Tests for empirical Bayes harm shrinkage."""

import pytest

from analytics.agentic_profile import get_preset
from analytics.inference.empirical_bayes import capability_harm_eb, capability_harm_eb_one, shrink_rate
from core.workspace import build_workspace


def test_shrink_rate_moves_toward_prior():
    prior = shrink_rate(1, 3, alpha0=1.0, beta0=9.0)
    assert prior < 1 / 3
    assert prior > 0.05


@pytest.mark.slow
def test_capability_harm_eb_dataframe():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=80)
    df = capability_harm_eb(ws)
    if not df.empty:
        assert "raw" in df.columns
        assert "shrunk" in df.columns
        row = capability_harm_eb_one(ws, df.iloc[0]["capability_id"])
        assert "shrunk_rate" in row
