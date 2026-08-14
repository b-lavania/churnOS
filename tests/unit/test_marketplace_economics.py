"""Tests for marketplace economics module."""

import pytest

from analytics.agentic_profile import get_preset
from analytics.marketplace_economics import (
    agent_gmv_attribution,
    platform_margin_after_inference,
)
from core.workspace import build_workspace


@pytest.mark.slow
def test_platform_margin_negative_on_planted_workflow():
    from data.ground_truth import get as get_ground_truth

    profile = get_preset("marketplace_agentic")
    ws = build_workspace(profile, seed=42, n_sessions=120)
    gt = get_ground_truth(ws.seed)
    m = platform_margin_after_inference(ws)
    assert m["n"] > 0
    if gt and gt.planted_negative_margin_workflows:
        txn = ws.agent_transactions
        for cap_id in gt.planted_negative_margin_workflows:
            sub = txn[(txn["capability_id"] == cap_id) & (txn["agent_assist_type"] != "none")]
            if not sub.empty:
                margin = sub["platform_revenue_usd"].sum() - sub["agent_inference_cost_usd"].sum()
                assert margin < 0


@pytest.mark.slow
def test_gmv_attribution_sums():
    profile = get_preset("marketplace_agentic")
    ws = build_workspace(profile, seed=3, n_sessions=120)
    attr = agent_gmv_attribution(ws)
    txn = ws.agent_transactions
    assisted = txn[txn["agent_assist_type"] != "none"]
    if not assisted.empty and not attr.empty:
        assert abs(attr["gmv_usd"].sum() - assisted["gmv_usd"].sum()) < 1e-3
