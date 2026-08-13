"""Tests for pareto module."""

from analytics.agentic_profile import get_preset
from analytics.pareto import is_dominated, pareto_frontier_indices, rank_capability_records
from analytics.decisions import emit_capability_records
from core.workspace import build_workspace


def test_is_dominated():
    a = (0.5, 10.0, 0.5)
    b = (0.8, 5.0, 0.9)
    assert is_dominated(a, b)
    assert not is_dominated(b, a)


def test_pareto_frontier_indices():
    tuples = [(0.9, 5.0, 0.8), (0.5, 10.0, 0.5), (0.85, 6.0, 0.75)]
    frontier = pareto_frontier_indices(tuples)
    assert 0 in frontier


def test_rank_capability_records_pareto_mode():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=80)
    recs = emit_capability_records(ws, profile)
    ranked = rank_capability_records(recs, ws, mode="pareto")
    assert len(ranked) == len(recs)
    assert any(r.get("pareto_frontier") for r in ranked if r.get("subject", {}).get("entity_type") == "capability")
