"""Workspace spine → metrics → experimentation analysis."""

import pytest

pytestmark = pytest.mark.integration


def test_build_workspace_experiment_pipeline():
    from analytics.agentic_profile import get_preset
    from core.workspace import build_workspace
    from analytics.metrics import resolve_metric
    from analytics.experimentation import analyze_workspace_experiment, design_from_workspace

    ws = build_workspace(get_preset("assistant_heavy"), seed=99)
    habit = resolve_metric("weekly_delegation_habit", ws)
    assert habit["value"] is not None

    plan = design_from_workspace(ws)
    assert plan["sample_size"]["sample_size_per_variant"] > 0

    analysis = analyze_workspace_experiment(ws)
    assert analysis["counts"]["control_visitors"] > 0
    assert "frequentist" in analysis
    assert "srm" in analysis
    assert 0 <= analysis["bayesian"]["prob_b_better"] <= 1


def test_metrics_consistent_across_resolvers():
    from analytics.agentic_profile import get_preset
    from core.workspace import build_workspace
    from analytics.metrics import resolve_metric

    ws = build_workspace(get_preset("workspace_crm"), seed=11)
    a = resolve_metric("weekly_delegation_habit", ws)
    b = resolve_metric("weekly_delegation_habit", ws)
    assert a["display"] == b["display"]
