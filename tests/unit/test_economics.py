"""Unit tests for token economics + dual billing."""

from analytics.agentic_profile import get_preset
from analytics.economics import calculate_run_cost, load_pricing_oracle, seat_margins
from data.agentic_generator import generate_agentic_warehouse


def test_oracle_has_models():
    oracle = load_pricing_oracle()
    assert "gpt-4o" in oracle["models"]
    assert oracle["models"]["gpt-4o"]["input_cost_per_1k"] > 0


def test_calculate_run_cost_positive_and_cached():
    profile = get_preset("assistant_heavy")
    tables = generate_agentic_warehouse(profile, seed=42)
    priced = calculate_run_cost(tables["runs"], profile)
    assert "run_cost_usd" in priced.columns
    assert "cache_credit_usd" in priced.columns
    assert (priced["run_cost_usd"] >= 0).all()
    assert (priced["gross_cost_usd"] >= priced["run_cost_usd"] - 1e-9).all()


def test_usage_based_margins_differ_from_subscription():
    profile = get_preset("assistant_heavy")
    tables = generate_agentic_warehouse(profile, seed=7)
    priced = calculate_run_cost(tables["runs"], profile)
    sub = dict(profile)
    sub["billing_model"] = "b2b_subscription"
    usage = dict(profile)
    usage["billing_model"] = "usage_based"
    m_sub = seat_margins(priced, tables["seats"], sub)
    m_usage = seat_margins(priced, tables["seats"], usage)
    assert not m_sub["revenue_usd"].equals(m_usage["revenue_usd"])
