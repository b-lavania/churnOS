"""P1 generator / OTEL / taxonomy extensions."""

from analytics.agentic_profile import get_preset, list_presets
from core.workspace import build_workspace
from data.agentic_generator import generate_agentic_warehouse
from data.otel_mock_generator import generate_otel_traces, load_otel_traces
from ontology.exception_taxonomy import all_categories


def test_runs_have_loop_and_token_columns():
    tables = generate_agentic_warehouse(get_preset("assistant_heavy"), seed=42)
    runs = tables["runs"]
    for col in ("loop_count", "steps_to_completion", "tokens_in", "tokens_out", "model_id"):
        assert col in runs.columns
    assert (runs["loop_count"] >= 1).all()
    # Failures should tend toward higher loops than successes (bimodal)
    ok = runs.loc[runs["success"], "loop_count"].mean()
    fail = runs.loc[~runs["success"], "loop_count"].mean()
    assert fail > ok


def test_connector_outcome_confirmed():
    tables = generate_agentic_warehouse(get_preset("ops_mission"), seed=3)
    ce = tables["connector_events"]
    assert "outcome_confirmed" in ce.columns
    assert ce["outcome_confirmed"].dtype == bool or ce["outcome_confirmed"].isin([True, False]).all()


def test_workspace_graph_and_eval():
    ws = build_workspace(get_preset("workspace_crm"), seed=11, n_sessions=500)
    assert not ws.connector_capability_graph.empty
    assert {"connector_id", "capability_id", "call_count", "fail_count"} <= set(
        ws.connector_capability_graph.columns
    )
    assert not ws.eval_results.empty
    assert "gross_cost_usd" in ws.runs.columns


def test_otel_mock_jsonl(tmp_path):
    out = generate_otel_traces(get_preset("assistant_heavy"), num_traces=5, output_path=tmp_path / "t.jsonl")
    rows = load_otel_traces(out)
    assert len(rows) >= 5
    assert all("parent_span_id" in r and "scrubbed" in r for r in rows)
    # At least one multi-span trace with a parent link
    assert any(r["parent_span_id"] is not None for r in rows)


def test_new_taxonomy_categories():
    cats = set(all_categories())
    for key in ("loop_exhaustion", "quality_drift", "eval_regression", "outcome_confirmation_gap"):
        assert key in cats


def test_api_metered_preset():
    assert "api_metered" in list_presets()
    p = get_preset("api_metered")
    assert p["billing_model"] == "usage_based"
