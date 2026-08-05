"""Ground-truth tests for methodology metrics."""

from analytics.agentic_profile import get_preset
from analytics.metrics import resolve_metric
from core.workspace import build_workspace


def test_delegation_ratio_bounded():
    ws = build_workspace(get_preset("workspace_crm"), seed=3)
    m = resolve_metric("delegation_ratio", ws)
    assert m["value"] is not None
    assert 0 <= m["value"] <= 100


def test_cost_per_successful_outcome_positive():
    ws = build_workspace(get_preset("assistant_heavy"), seed=42)
    m = resolve_metric("cost_per_successful_outcome", ws)
    assert m["value"] >= 0


def test_emit_account_records():
    from analytics.decisions import emit_account_records

    ws = build_workspace(get_preset("assistant_heavy"), seed=42)
    records = emit_account_records(ws, ws.profile)
    assert isinstance(records, list)
    for r in records:
        assert r["subject"]["entity_type"] == "account"
        assert "account_id" in r["subject"]
