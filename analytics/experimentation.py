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
from analytics.metrics import resolve_metric, load_lexicon
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
    if "visitors" in outcomes.columns:
        return {
            "control_visitors": int(ctrl["visitors"]),
            "control_conversions": int(ctrl["conversions"]),
            "variant_visitors": int(var["visitors"]),
            "variant_conversions": int(var["conversions"]),
        }
    return {
        "control_visitors": int(ctrl.get("exposed_seats", 0)),
        "control_conversions": int(ctrl.get("successful_runs", 0)),
        "variant_visitors": int(var.get("exposed_seats", 0)),
        "variant_conversions": int(var.get("successful_runs", 0)),
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
    """Plan sample size / duration using workspace baseline rate."""
    if "weekly_delegation_habit" in load_lexicon().get("metrics", {}):
        cvr_metric = resolve_metric("weekly_delegation_habit", workspace)
        baseline = float(cvr_metric["value"] or 40.0) / 100.0
        visits = len(workspace.seats)
    else:
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


def agentic_sample_size(
    baseline: float,
    mde_absolute: float,
    *,
    unit: str = "run",
    power: float = 0.80,
    alpha: float = 0.05,
    icc: float = 0.0,
    runs_per_unit: int = 1,
) -> dict[str, Any]:
    """
    Cluster-aware sample size for agentic experiments.

    When unit is seat/account with ICC > 0, applies design effect DE = 1 + (m-1)*rho.
    """
    if baseline <= 0 or baseline >= 1 or mde_absolute <= 0:
        raise ValueError("baseline must be in (0,1) and mde_absolute > 0")

    mde_relative = mde_absolute / baseline
    ss = calculate_sample_size(baseline, mde_relative, power=power, alpha=alpha)
    n_per_arm = ss["sample_size_per_variant"]
    de = 1.0 + max(0.0, icc) * max(1, runs_per_unit - 1)
    clustered_n = int(np.ceil(n_per_arm * de))

    web_comparison = calculate_sample_size(0.02, 0.05, power=power, alpha=alpha)

    return {
        "unit": unit,
        "baseline": baseline,
        "mde_absolute": mde_absolute,
        "mde_relative": round(mde_relative, 4),
        "sample_size_per_arm_naive": n_per_arm,
        "sample_size_per_arm_clustered": clustered_n,
        "design_effect": round(de, 3),
        "icc": icc,
        "runs_per_unit": runs_per_unit,
        "web_cvr_analogy_n_per_arm": web_comparison["sample_size_per_variant"],
        "message": (
            f"At {baseline:.0%} baseline, detecting {mde_absolute:.1%}pp needs "
            f"~{clustered_n} {unit}s/arm (ICC={icc})."
        ),
    }


def cuped_adjust(
    control_outcomes: np.ndarray,
    variant_outcomes: np.ndarray,
    control_covariate: np.ndarray,
    variant_covariate: np.ndarray,
) -> dict[str, Any]:
    """CUPED variance reduction on pre-period covariate."""
    if len(control_outcomes) < 2 or len(variant_outcomes) < 2:
        return {"adjusted_lift": None, "variance_reduction_pct": 0.0}

    pooled_x = np.concatenate([control_covariate, variant_covariate])
    pooled_y = np.concatenate([control_outcomes, variant_outcomes])
    if np.std(pooled_x) < 1e-9:
        return {"adjusted_lift": None, "variance_reduction_pct": 0.0}

    theta = float(np.cov(pooled_y, pooled_x)[0, 1] / np.var(pooled_x))
    adj_c = control_outcomes - theta * (control_covariate - pooled_x.mean())
    adj_v = variant_outcomes - theta * (variant_covariate - pooled_x.mean())
    raw_lift = variant_outcomes.mean() - control_outcomes.mean()
    adj_lift = adj_v.mean() - adj_c.mean()
    raw_var = np.var(control_outcomes) / len(control_outcomes) + np.var(variant_outcomes) / len(variant_outcomes)
    adj_var = np.var(adj_c) / len(adj_c) + np.var(adj_v) / len(adj_v)
    vr = max(0.0, (1 - adj_var / raw_var) * 100) if raw_var > 0 else 0.0
    return {
        "raw_lift": round(float(raw_lift), 4),
        "adjusted_lift": round(float(adj_lift), 4),
        "variance_reduction_pct": round(vr, 1),
        "theta": round(theta, 4),
    }


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """Return which hypotheses are significant under BH FDR control."""
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    significant = [False] * m
    max_k = -1
    for rank, (orig_i, p) in enumerate(indexed, start=1):
        if p <= alpha * rank / m:
            max_k = rank
    if max_k >= 0:
        for rank, (orig_i, _) in enumerate(indexed[:max_k], start=1):
            significant[orig_i] = True
    return significant

