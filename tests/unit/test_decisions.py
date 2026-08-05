"""Tests for decision emitter."""

from analytics.agentic_profile import get_preset
from analytics.decisions import apply_override, emit_records, rank_exceptions, write_outcome
from core.workspace import build_workspace


def test_emit_records_ranked_by_cost():
    ws = build_workspace(get_preset("assistant_heavy"), seed=42, n_sessions=500)
    records = emit_records(ws, ws.profile)
    assert len(records) > 0
    costs = [r["economics"]["primary_metric_usd"] for r in records]
    assert costs == sorted(costs, reverse=True)


def test_override_without_reclassify():
    ws = build_workspace(get_preset("ops_mission"), seed=7, n_sessions=500)
    rec = emit_records(ws, ws.profile)[0]
    original_exceptions = rec["exceptions"]
    updated = apply_override(rec, "hold", "Testing override", decided_by="tester")
    assert updated["decision"]["final_action"] == "hold"
    assert updated["exceptions"] == original_exceptions


def test_write_outcome_fields():
    ws = build_workspace(get_preset("workspace_crm"), seed=3, n_sessions=500)
    rec = emit_records(ws, ws.profile, entity_type="capability")[0]
    out = write_outcome(rec, ws, horizon_days=14)
    assert "outcome" in out
    assert "churn_happened" in out["outcome"]
    assert "followed_recommendation" in out["outcome"]
