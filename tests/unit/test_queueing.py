"""Tests for queueing module."""

from analytics.agentic_profile import get_preset
from analytics.queueing import erlang_c, hitl_queue_from_workspace
from core.workspace import build_workspace


def test_erlang_c_underloaded():
    r = erlang_c(arrival_rate=1.0, service_rate=2.0, servers=2)
    assert r["p_wait"] < 0.5
    assert r["utilization"] < 1.0
    assert not r.get("overloaded")


def test_erlang_c_overloaded():
    r = erlang_c(arrival_rate=10.0, service_rate=2.0, servers=2)
    assert r.get("overloaded") is True


def test_hitl_queue_from_workspace():
    profile = get_preset("assistant_heavy")
    ws = build_workspace(profile, seed=42, n_sessions=60)
    q = hitl_queue_from_workspace(ws, profile)
    assert "p_wait" in q
    assert q["reviewers"] >= 1
