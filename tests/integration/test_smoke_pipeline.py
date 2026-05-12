"""Small smoke tests that traverse generator + analytic modules deterministically."""

import pytest

pytestmark = pytest.mark.integration


def test_bundle_contains_product_streams():
    from data.generator import generate_all_data

    data = generate_all_data(seed=7)
    for key in ("customers", "transactions", "funnel", "product_events", "marketing"):
        assert key in data
        assert data[key] is not None


def test_churn_and_funnel_summaries_resolve():
    from analytics.churn import compute_churn_rate
    from analytics.conversion import funnel_summary
    from data.generator import generate_all_data

    blob = generate_all_data(seed=9)
    assert not compute_churn_rate(blob["customers"]).empty

    funnel = funnel_summary(blob["funnel"])
    assert funnel["sessions"].iloc[0] > 2000


def test_product_metrics_integration():
    from analytics.product_metrics import activation_and_ttf_metrics, sessionize_product_events
    from data.generator import generate_all_data

    d = generate_all_data(seed=4)
    act = activation_and_ttf_metrics(d["customers"], d["transactions"])
    assert act["n_customers"] == len(d["customers"])
    assert not sessionize_product_events(d["product_events"]).empty
