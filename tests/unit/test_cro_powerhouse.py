"""
Unit tests for Bayesian A/B test, revenue impact, experiment ROI,
conversion-to-LTV bridge, segment revenue gap, forecast, and program metrics.
"""

import pytest
import numpy as np
import pandas as pd
from analytics.conversion import (
    bayesian_ab_test, revenue_at_stake, experiment_roi,
    conversion_to_ltv_impact, segment_revenue_gap,
    forecast_cro_revenue, program_metrics,
)
from data.generator import generate_funnel_events


class TestBayesianABTest:
    def test_clear_winner(self):
        result = bayesian_ab_test(
            control_visitors=10000, control_conversions=300,
            variant_visitors=10000, variant_conversions=360,
        )
        assert result["prob_b_better"] > 0.95
        assert result["expected_lift_pct"] > 0
        assert result["credible_interval"][0] > 0
        assert "Strong evidence" in result["interpretation"]

    def test_no_difference(self):
        result = bayesian_ab_test(
            control_visitors=10000, control_conversions=300,
            variant_visitors=10000, variant_conversions=300,
        )
        assert 0.3 < result["prob_b_better"] < 0.7
        assert "Inconclusive" in result["interpretation"]

    def test_variant_worse(self):
        result = bayesian_ab_test(
            control_visitors=10000, control_conversions=400,
            variant_visitors=10000, variant_conversions=300,
        )
        assert result["prob_b_better"] < 0.05
        assert result["expected_lift_pct"] < 0

    def test_small_sample_uncertainty(self):
        result = bayesian_ab_test(
            control_visitors=500, control_conversions=15,
            variant_visitors=500, variant_conversions=20,
        )
        assert result["prob_b_better"] > 0.5
        assert abs(result["credible_interval"][1] - result["credible_interval"][0]) > 5

    def test_expected_loss_non_negative(self):
        result = bayesian_ab_test(
            control_visitors=10000, control_conversions=300,
            variant_visitors=10000, variant_conversions=350,
        )
        assert result["expected_loss_pct"] >= 0

    def test_posterior_means_reasonable(self):
        result = bayesian_ab_test(
            control_visitors=10000, control_conversions=300,
            variant_visitors=10000, variant_conversions=350,
        )
        assert 2.5 < result["control_posterior_mean"] < 3.5
        assert 3.0 < result["variant_posterior_mean"] < 4.0


class TestRevenueAtStake:
    def test_returns_dataframe(self):
        df = generate_funnel_events(n_sessions=10000)
        result = revenue_at_stake(df, aov=50.0, gross_margin_pct=40.0)
        assert isinstance(result, pd.DataFrame)
        assert "step" in result.columns
        assert "revenue_at_stake" in result.columns

    def test_visit_has_zero_loss(self):
        df = generate_funnel_events(n_sessions=10000)
        result = revenue_at_stake(df, aov=50.0, gross_margin_pct=40.0)
        visit_row = result[result["step"] == "Visit"]
        assert len(visit_row) > 0
        assert visit_row["revenue_at_stake"].iloc[0] == 0

    def test_purchase_has_max_loss(self):
        df = generate_funnel_events(n_sessions=10000)
        result = revenue_at_stake(df, aov=50.0, gross_margin_pct=40.0)
        purchase_row = result[result["step"] == "Purchase"]
        assert len(purchase_row) > 0
        assert purchase_row["revenue_at_stake"].iloc[0] == result["revenue_at_stake"].max()


class TestExperimentROI:
    def test_positive_roi_large_lift(self):
        result = experiment_roi(
            baseline_cvr=0.03, expected_lift_pct=20.0,
            sample_size_per_variant=5000, daily_traffic=2000,
            aov=50.0, gross_margin_pct=40.0,
        )
        assert result["net_roi_12mo"] > 0
        assert "positive ROI" in result["recommendation"]

    def test_negative_roi_small_lift(self):
        result = experiment_roi(
            baseline_cvr=0.03, expected_lift_pct=1.0,
            sample_size_per_variant=50000, daily_traffic=500,
            aov=10.0, gross_margin_pct=20.0,
        )
        assert result["net_roi_3mo"] <= 0

    def test_opportunity_cost_positive(self):
        result = experiment_roi(
            baseline_cvr=0.03, expected_lift_pct=10.0,
            sample_size_per_variant=5000, daily_traffic=2000,
            aov=50.0, gross_margin_pct=40.0,
        )
        assert result["test_opportunity_cost"] > 0


class TestConversionToLTVImpact:
    def test_improvement_adds_customers(self):
        result = conversion_to_ltv_impact(
            baseline_cvr=3.0, improved_cvr=3.5,
            monthly_sessions=30000, aov=50.0,
            gross_margin_pct=40.0, monthly_churn_rate=0.08,
        )
        assert result["additional_customers_per_month"] > 0
        assert result["incremental_ltv_24mo"] > 0

    def test_no_improvement_zero_impact(self):
        result = conversion_to_ltv_impact(
            baseline_cvr=3.0, improved_cvr=3.0,
            monthly_sessions=30000, aov=50.0,
            gross_margin_pct=40.0, monthly_churn_rate=0.08,
        )
        assert result["additional_customers_per_month"] == 0
        assert result["incremental_ltv_24mo"] == 0

    def test_retention_curve_decays(self):
        result = conversion_to_ltv_impact(
            baseline_cvr=3.0, improved_cvr=4.0,
            monthly_sessions=30000, aov=50.0,
            gross_margin_pct=40.0, monthly_churn_rate=0.08,
        )
        curve = result["monthly_retention_curve"]
        assert curve[0] > curve[-1]


class TestSegmentRevenueGap:
    def test_returns_dataframe(self):
        df = generate_funnel_events(n_sessions=10000)
        result = segment_revenue_gap(df, segment_by="device", aov=50.0, gross_margin_pct=40.0)
        assert isinstance(result, pd.DataFrame)
        assert "revenue_gap" in result.columns

    def test_best_segment_has_zero_gap(self):
        df = generate_funnel_events(n_sessions=10000)
        result = segment_revenue_gap(df, segment_by="device", aov=50.0, gross_margin_pct=40.0)
        assert result["revenue_gap"].iloc[-1] == 0


class TestForecastCRORevenue:
    def test_returns_forecast_structure(self):
        improvements = [
            {"name": "Test A", "cvr_lift_pct": 10.0, "cvr_lift_std": 3.0, "deploy_month": 2},
        ]
        result = forecast_cro_revenue(
            baseline_cvr=3.0, planned_improvements=improvements,
            monthly_sessions=30000, aov=50.0, gross_margin_pct=40.0,
            monthly_churn_rate=0.08, n_months=6,
        )
        assert "monthly_forecast" in result
        assert "total_incremental_revenue" in result
        assert "improvement_contributions" in result
        assert len(result["monthly_forecast"]) == 6

    def test_no_improvements_zero_revenue(self):
        result = forecast_cro_revenue(
            baseline_cvr=3.0, planned_improvements=[],
            monthly_sessions=30000, aov=50.0, gross_margin_pct=40.0,
            monthly_churn_rate=0.08, n_months=6,
        )
        assert result["total_incremental_revenue"] == 0

    def test_confidence_bands_ordered(self):
        improvements = [
            {"name": "Test A", "cvr_lift_pct": 10.0, "cvr_lift_std": 3.0, "deploy_month": 2},
        ]
        result = forecast_cro_revenue(
            baseline_cvr=3.0, planned_improvements=improvements,
            monthly_sessions=30000, aov=50.0, gross_margin_pct=40.0,
            monthly_churn_rate=0.08, n_months=6,
        )
        for m in result["monthly_forecast"]:
            assert m["ci_lower"] <= m["median_revenue"] <= m["ci_upper"]


class TestProgramMetrics:
    def test_all_planned(self):
        experiments = [
            {"status": "planned", "winner": None, "lift_pct": None, "monthly_revenue_impact": None, "duration_days": None},
            {"status": "planned", "winner": None, "lift_pct": None, "monthly_revenue_impact": None, "duration_days": None},
        ]
        result = program_metrics(experiments)
        assert result["total_experiments"] == 2
        assert result["completed"] == 0
        assert result["win_rate_pct"] == 0

    def test_mixed_program(self):
        experiments = [
            {"status": "completed", "winner": "variant", "lift_pct": 12.0, "monthly_revenue_impact": 5000, "duration_days": 14},
            {"status": "completed", "winner": "control", "lift_pct": -3.0, "monthly_revenue_impact": 0, "duration_days": 21},
            {"status": "active", "winner": None, "lift_pct": None, "monthly_revenue_impact": None, "duration_days": None},
        ]
        result = program_metrics(experiments)
        assert result["completed"] == 2
        assert result["active"] == 1
        assert result["win_rate_pct"] == 50.0
        assert result["avg_lift_pct"] == 12.0
        assert result["cumulative_monthly_revenue_impact"] == 5000
        assert result["avg_time_to_decision_days"] == 17.5
