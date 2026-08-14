"""Tests for marketplace GDR emit."""

import pytest

from analytics.agentic_profile import get_preset
from analytics.decisions import classify_marketplace, emit_marketplace_records
from core.workspace import build_workspace


@pytest.mark.slow
def test_emit_marketplace_workflow_records():
    profile = get_preset("marketplace_agentic")
    profile["priors"]["math_mode"] = "rigorous"
    ws = build_workspace(profile, seed=42, n_sessions=120)
    raw = classify_marketplace(ws, profile)
    assert len(raw) > 0
    records = emit_marketplace_records(ws, profile, entity_type="workflow")
    assert records
    assert records[0]["vertical"] == "marketplace_commerce"
    assert records[0]["economics"]["primary_metric_label"] == "platform_margin_at_risk_usd"
    costs = [r["economics"]["primary_metric_usd"] for r in records]
    assert costs == sorted(costs, reverse=True)


@pytest.mark.slow
def test_emit_marketplace_seller_records():
    profile = get_preset("marketplace_agentic")
    ws = build_workspace(profile, seed=42, n_sessions=120)
    records = emit_marketplace_records(ws, profile, entity_type="seller")
    for rec in records:
        assert rec["subject"]["entity_type"] == "seller"
