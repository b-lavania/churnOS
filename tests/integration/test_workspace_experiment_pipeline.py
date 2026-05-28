"""Workspace spine → metrics → experimentation analysis."""

import pytest

pytestmark = pytest.mark.integration


def test_build_workspace_experiment_pipeline():
    from core.workspace import build_workspace
    from analytics.metrics import resolve_metric
    from analytics.experimentation import analyze_workspace_experiment, design_from_workspace

    ws = build_workspace({"business_type": "ecommerce"}, seed=99)
    cvr = resolve_metric("session_to_purchase_cvr", ws)
    assert cvr["value"] is not None

    plan = design_from_workspace(ws)
    assert plan["sample_size"]["sample_size_per_variant"] > 0

    analysis = analyze_workspace_experiment(ws)
    assert analysis["counts"]["control_visitors"] > 0
    assert "frequentist" in analysis
    assert "srm" in analysis
    assert 0 <= analysis["bayesian"]["prob_b_better"] <= 1


def test_metrics_consistent_across_resolvers():
    from core.workspace import build_workspace
    from analytics.metrics import resolve_metric

    ws = build_workspace(seed=11)
    a = resolve_metric("session_to_purchase_cvr", ws)
    b = resolve_metric("session_to_purchase_cvr", ws)
    assert a["display"] == b["display"]
