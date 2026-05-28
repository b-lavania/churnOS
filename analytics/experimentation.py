"""
Experiment lifecycle helpers: assignment hygiene, SRM, exposure-aware analysis.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from analytics.conversion import (
    ab_test_significance,
    bayesian_ab_test,
    calculate_sample_size,
    estimate_test_duration,
)
from analytics.metrics import resolve_metric
from analytics.product_metrics import refund_exposure_rates
from core.workspace import Workspace


def sample_ratio_mismatch_test(assignments: pd.DataFrame, expected_control_share: float = 0.5) -> dict[str, Any]:
    """
    Chi-square goodness-of-fit on assignment counts (standard pre-flight SRM screen).
    """
    counts = assignments["variant"].value_counts()
    control_n = int(counts.get("control", 0))
    variant_n = int(counts.get("variant", 0))
    total = control_n + variant_n
    if total == 0:
        return {
            "passed": False,
            "p_value": 1.0,
            "control_n": 0,
            "variant_n": 0,
            "expected_control_share": expected_control_share,
            "message": "No assignments to test.",
        }

    expected = np.array([expected_control_share, 1.0 - expected_control_share]) * total
    observed = np.array([control_n, variant_n], dtype=float)
    chi2, p_value = stats.chisquare(observed, expected)

    passed = p_value >= 0.01
    return {
        "passed": passed,
        "p_value": round(float(p_value), 6),
        "chi2": round(float(chi2), 4),
        "control_n": control_n,
        "variant_n": variant_n,
        "expected_control_share": expected_control_share,
        "message": (
            "Assignment balance looks acceptable."
            if passed
            else f"Possible sample ratio mismatch (p={p_value:.4f}). Review randomization."
        ),
    }


def outcomes_to_analysis_counts(outcomes: pd.DataFrame) -> dict[str, int]:
    """Map experiment_outcomes rows to ab_test_significance inputs."""
    ctrl = outcomes[outcomes["variant"] == "control"].iloc[0]
    var = outcomes[outcomes["variant"] == "variant"].iloc[0]
    return {
        "control_visitors": int(ctrl["visitors"]),
        "control_conversions": int(ctrl["conversions"]),
        "variant_visitors": int(var["visitors"]),
        "variant_conversions": int(var["conversions"]),
    }


def analyze_workspace_experiment(workspace: Workspace) -> dict[str, Any]:
    """Frequentist + Bayesian analysis on workspace experiment_outcomes."""
    counts = outcomes_to_analysis_counts(workspace.experiment_outcomes)
    freq = ab_test_significance(**counts)
    bayes = bayesian_ab_test(**counts)
    srm = sample_ratio_mismatch_test(workspace.experiment_assignments)
    guardrails = guardrail_snapshot(workspace)

    return {
        "counts": counts,
        "frequentist": freq,
        "bayesian": bayes,
        "srm": srm,
        "guardrails": guardrails,
        "experiment_id": workspace.default_experiment_id,
        "notes": (
            "Session-level counts after synthetic user→session linkage. "
            "Not a substitute for production exposure logging."
        ),
    }


def guardrail_snapshot(workspace: Workspace) -> dict[str, Any]:
    ref = refund_exposure_rates(workspace.transactions)
    disc = resolve_metric("orders_per_active_buyer", workspace)
    return {
        "refund_rate_orders_pct": ref.get("refund_rate_all_orders_pct"),
        "refund_rate_discounted_orders_pct": ref.get("refund_rate_discounted_orders_pct"),
        "orders_per_active_buyer": disc.get("value"),
        "thresholds": {"refund_rate_warn_pct": 8.0},
    }


def design_from_workspace(
    workspace: Workspace,
    *,
    mde_relative: float = 0.10,
    power: float = 0.80,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Plan sample size / duration using workspace funnel CVR."""
    cvr_metric = resolve_metric("session_to_purchase_cvr", workspace)
    baseline = float(cvr_metric["value"] or 3.0) / 100.0
    visits = int(cvr_metric["meta"].get("visits", 30_000))

    ss = calculate_sample_size(baseline, mde_relative, power=power, alpha=alpha)
    daily_traffic = max(100, visits // 30)
    dur = estimate_test_duration(ss["total_sample_size"], daily_traffic, baseline)

    return {
        "baseline_cvr": baseline,
        "sample_size": ss,
        "duration": dur,
        "daily_traffic_assumed": daily_traffic,
    }


def registry_entry_from_analysis(
    name: str,
    hypothesis: str,
    analysis: dict[str, Any],
    *,
    status: str = "completed",
) -> dict[str, Any]:
    """Build CRO registry row from a completed workspace analysis."""
    freq = analysis["frequentist"]
    counts = analysis["counts"]
    winner = "variant" if freq["is_significant"] and freq["lift_pct"] > 0 else "control"
    return {
        "id": f"EXP-{pd.Timestamp.utcnow().strftime('%H%M%S')}",
        "name": name,
        "hypothesis": hypothesis,
        "status": status,
        "winner": winner if status == "completed" else None,
        "lift_pct": freq["lift_pct"],
        "monthly_revenue_impact": None,
        "duration_days": 14,
        "start_date": pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        "end_date": pd.Timestamp.utcnow().strftime("%Y-%m-%d") if status == "completed" else None,
        "control_visitors": counts["control_visitors"],
        "variant_visitors": counts["variant_visitors"],
        "control_conversions": counts["control_conversions"],
        "variant_conversions": counts["variant_conversions"],
        "srm_p_value": analysis["srm"]["p_value"],
    }


def sequential_testing_warning(active_experiment_count: int) -> str | None:
    if active_experiment_count <= 1:
        return None
    return (
        f"{active_experiment_count} experiments marked active. "
        "Peeking and overlapping tests inflate false positives—see docs/methodology.md."
    )
