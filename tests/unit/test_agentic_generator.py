"""Agentic warehouse generator invariants."""

import pytest
from analytics.agentic_profile import get_preset
from data.agentic_generator import generate_agentic_warehouse, EVENT_TYPES


def test_generator_produces_all_tables():
    profile = get_preset("assistant_heavy")
    tables = generate_agentic_warehouse(profile, seed=42)
    expected = {
        "workspaces", "seats", "agents", "capabilities", "capability_versions",
        "runs", "approvals", "connector_events", "product_events", "retention_marks",
        "experiment_assignments", "experiment_exposures", "experiment_outcomes",
    }
    assert expected <= set(tables.keys())


def test_run_capability_fk():
    profile = get_preset("workspace_crm")
    tables = generate_agentic_warehouse(profile, seed=99)
    cap_ids = set(tables["capabilities"]["capability_id"])
    assert tables["runs"]["capability_id"].isin(cap_ids).all()


def test_event_contract_subset():
    profile = get_preset("ops_mission")
    events = generate_agentic_warehouse(profile, seed=1)["product_events"]
    names = set(events["event_name"].unique())
    assert names <= set(EVENT_TYPES)
