"""Tests for marketplace_agentic generator and workspace wiring."""

import pytest

from analytics.agentic_profile import get_preset
from core.workspace import build_workspace


@pytest.mark.slow
def test_agent_transactions_generated_for_marketplace_preset():
    profile = get_preset("marketplace_agentic")
    ws = build_workspace(profile, seed=42, n_sessions=120)
    txn = ws.agent_transactions
    assert not txn.empty
    assert len(txn) >= 80
    assert "gmv_usd" in txn.columns
    assert "agent_inference_cost_usd" in txn.columns


@pytest.mark.slow
def test_agent_transactions_fk_integrity():
    profile = get_preset("marketplace_agentic")
    ws = build_workspace(profile, seed=7, n_sessions=120)
    txn = ws.agent_transactions
    assisted = txn[txn["agent_run_id"].notna()]
    if not assisted.empty:
        run_ids = set(ws.runs["run_id"])
        assert assisted["agent_run_id"].isin(run_ids).all()


@pytest.mark.slow
def test_planted_negative_margin_workflow():
    from data.ground_truth import get as get_ground_truth

    profile = get_preset("marketplace_agentic")
    ws = build_workspace(profile, seed=42, n_sessions=120)
    gt = get_ground_truth(ws.seed)
    assert gt is not None
    assert gt.planted_negative_margin_workflows
    txn = ws.agent_transactions
    for cap_id in gt.planted_negative_margin_workflows:
        sub = txn[(txn["capability_id"] == cap_id) & (txn["agent_assist_type"] != "none")]
        if not sub.empty:
            net = sub["platform_revenue_usd"].sum() - sub["agent_inference_cost_usd"].sum()
            assert net < 0
