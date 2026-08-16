"""Tests for challenge seed data and metrics."""

from analytics.agentic_profile import get_preset
from analytics.decisions import emit_capability_records
from analytics.metrics import resolve_metric
from core.workspace import build_workspace


def test_challenge_tables_present():
    ws = build_workspace(get_preset("assistant_heavy"), seed=42, n_sessions=500)
    assert not ws.catastrophic_events.empty
    assert not ws.jevons_elasticity.empty
    assert "context_util_pct" in ws.runs.columns
    assert "integration_depth_score" in ws.accounts.columns
    assert not ws.feature_flag_assignments.empty


def test_challenge_metrics_resolve():
    ws = build_workspace(get_preset("workspace_crm"), seed=7, n_sessions=500)
    for name in (
        "time_to_first_value",
        "unattributed_spend_percentage",
        "agentic_health_score",
        "catastrophic_event_rate",
        "paying_but_dormant_rate",
        "coordination_overhead",
        "high_ltv_activation_path_share",
    ):
        m = resolve_metric(name, ws)
        assert m["display"] != "—"


def test_gdr_viz_receipts_attached():
    ws = build_workspace(get_preset("assistant_heavy"), seed=42, n_sessions=500)
    records = emit_capability_records(ws, ws.profile)
    assert records
    with_viz = [r for r in records if r.get("viz")]
    assert with_viz, "expected at least one GDR with viz receipt"
