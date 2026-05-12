"""Unit coverage for synthetic product analytics helpers."""

import pandas as pd

from analytics.product_metrics import (
    activation_and_ttf_metrics,
    cohort_event_adoption,
    cohort_signups_by_month,
    conversion_lift_orders_margin,
    inter_purchase_gap_distribution,
    purchase_dau_over_wau_proxy,
    sessionize_product_events,
    signup_momentum_latest_vs_prior_month,
)
from data.generator import generate_all_data


def test_cohort_signups_sorted():
    data = generate_all_data(seed=7)
    out = cohort_signups_by_month(data["customers"])
    assert not out.empty
    assert out["cohort_month"].tolist() == sorted(out["cohort_month"].tolist())


def test_activation_keys_and_percent():
    cust = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "signup_date": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
        }
    )
    tx = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-02-03")],
            "net_revenue": [42.0, 20.0],
        }
    )
    res = activation_and_ttf_metrics(cust, tx)
    assert res["pct_first_order_within_7d"] == 100.0
    assert res["median_days_to_first_purchase"] == 1.5


def test_conversion_lift_positive_gain():
    res = conversion_lift_orders_margin(
        baseline_cvr_pct=2.5,
        relative_lift_pct=10.0,
        baseline_sessions=10_000,
        margin_per_incremental_buyer_monthly=40.0,
        buyer_clv_24=200.0,
    )
    assert res["estimated_monthly_margin_gain_usd"] > 0
    assert isinstance(res["ratio_metric_notes"], str)


def test_sessionize_splits_on_gap():
    df = pd.DataFrame(
        {
            "customer_id": ["a", "a", "a"],
            "event_ts": pd.to_datetime(["2024-06-01 10:00", "2024-06-01 10:05", "2024-06-01 12:05"]),
            "event_name": ["x", "x", "x"],
        }
    )
    out = sessionize_product_events(df, gap_minutes=30)
    assert out["session_id"].nunique() == 2


def test_full_synthetic_pipeline_smoke_metrics():
    data = generate_all_data(seed=101)
    act = activation_and_ttf_metrics(data["customers"], data["transactions"])
    assert act["n_customers"] > 100
    assert purchase_dau_over_wau_proxy(data["transactions"])["mean_ratio"] is not None
    assert inter_purchase_gap_distribution(data["transactions"])["n_gaps"] > 0
    signup_momentum_latest_vs_prior_month(cohort_signups_by_month(data["customers"]))


def test_product_event_adoption_table():
    data = generate_all_data(seed=3)
    tbl = cohort_event_adoption(data["customers"], data["product_events"], event_name="subscribe_toggle")
    assert "signup_cohort_month" in tbl.columns
