"""Tests for SPRT and version compare."""

import pytest

from analytics.agent_version_compare import compare_agent_versions
from analytics.inference.sprt import sprt_two_proportion
from analytics.agentic_profile import get_preset
from core.workspace import build_workspace


def test_sprt_rollback_on_bad_variant():
    # control 80/100, variant 50/100
    r = sprt_two_proportion(80, 100, 50, 100, p0=0.8, p1=0.6)
    assert r["decision"] in ("rollback", "continue", "ship")


@pytest.mark.slow
def test_compare_agent_versions_has_sprt():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=80)
    cmp = compare_agent_versions(ws)
    assert "sprt" in cmp
    assert "traffic_light" in cmp
