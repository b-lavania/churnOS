"""Tests for methodology warehouse entities."""

from analytics.agentic_profile import get_preset
from core.workspace import build_workspace


def test_methodology_tables_present():
    ws = build_workspace(get_preset("assistant_heavy"), seed=42)
    assert not ws.accounts.empty
    assert not ws.end_users.empty
    assert not ws.agent_runs.empty
    assert "account_id" in ws.accounts.columns
    assert len(ws.runs) == len(ws.agent_runs)


def test_otel_data_source():
    ws = build_workspace(get_preset("assistant_heavy"), seed=7, data_source="otel")
    assert ws.meta.get("data_source") == "otel"
    assert not ws.spans.empty
