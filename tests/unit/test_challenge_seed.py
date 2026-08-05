"""Tests for challenge seed data and metrics."""

from analytics.agentic_profile import get_preset
from analytics.metrics import resolve_metric
from core.workspace import build_workspace


def test_challenge_tables_present():
    ws = build_workspace(get_preset("assistant_heavy"), seed=42)
    assert not ws.catastrophic_events.empty
    assert not ws.jevons_elasticity.empty
    assert "context_util_pct" in ws.runs.columns
    assert "integration_depth_score" in ws.accounts.columns


def test_challenge_metrics_resolve():
    ws = build_workspace(get_preset("workspace_crm"), seed=7)
    for name in (
        "time_to_first_value",
        "unattributed_spend_percentage",
        "agentic_health_score",
        "catastrophic_event_rate",
    ):
        m = resolve_metric(name, ws)
        assert m["display"] != "—"
