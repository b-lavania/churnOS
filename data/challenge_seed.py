"""
Dummy seed data for agenticchallenges.md metrics (teaching / synthetic only).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

STEP_KINDS = ["plan", "tool", "verify", "retry"]
CHURN_REASONS = [
    "rebuild_in_house",
    "competitor",
    "tourist",
    "price",
    "value_failure",
    "champion_departure",
    "product_gap",
    "other",
]
ACTIVATION_PATHS = ["guided_first_win", "self_serve", "design_partner", "power_user"]
FEATURE_FLAGS = [
    "max_retries_limit",
    "guided_first_win_flow",
    "agent_model_router_v2",
    "cost_observability_v1",
    "human_in_the_loop_first_30_days",
]


def enrich_challenge_data(
    agentic: dict[str, pd.DataFrame],
    profile: dict[str, Any],
    *,
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """Add columns and tables required for the 25 agentic challenge findings."""
    rng = np.random.default_rng(seed)
    runs = agentic["runs"].copy()
    seats = agentic["seats"].copy()
    accounts = agentic.get("accounts", pd.DataFrame()).copy()
    spans = agentic.get("spans", pd.DataFrame()).copy()
    usage_events = agentic.get("usage_events", pd.DataFrame()).copy()
    outcomes = agentic.get("outcomes", pd.DataFrame()).copy()

    if not runs.empty:
        n = len(runs)
        runs["context_util_pct"] = np.clip(rng.beta(2, 2, size=n) * 100, 5, 98)
        runs["retry_count"] = np.maximum(0, runs["loop_count"].astype(int) - 1)
        runs["attribution_complete"] = rng.random(n) > 0.18
        runs["human_intervened"] = rng.random(n) < 0.22
        runs["coordination_token_share"] = np.clip(rng.beta(1.5, 4, size=n), 0.05, 0.65)
        runs["step_kind"] = rng.choice(STEP_KINDS, size=n)
        runs["user_goal_id"] = [f"GOAL-{i // 3:05d}" for i in range(n)]

    if not seats.empty:
        n_seats = len(seats)
        seats["first_paid_at"] = seats["signup_date"] + pd.to_timedelta(
            rng.integers(0, 14, size=n_seats), unit="D"
        )
        seats["churn_reason"] = "other"
        churned_mask = seats["is_churned"]
        if churned_mask.any():
            seats.loc[churned_mask, "churn_reason"] = rng.choice(
                CHURN_REASONS, size=int(churned_mask.sum())
            )
        seats["exported_before_churn"] = False
        if churned_mask.any():
            seats.loc[churned_mask, "exported_before_churn"] = rng.random(int(churned_mask.sum())) < 0.35

    if not accounts.empty:
        n_acc = len(accounts)
        accounts["first_paid_at"] = accounts["created_at"] + pd.to_timedelta(
            rng.integers(1, 21, size=n_acc), unit="D"
        )
        accounts["first_win_defined"] = rng.random(n_acc) > 0.25
        accounts["memory_days"] = rng.integers(7, 180, size=n_acc)
        accounts["custom_workflow_count"] = rng.integers(0, 8, size=n_acc)
        accounts["integration_depth_score"] = np.clip(
            0.3 * accounts["custom_workflow_count"]
            + 0.3 * (accounts["memory_days"] / 180)
            + rng.uniform(0, 0.4, size=n_acc),
            0,
            1,
        ) * 100
        accounts["activation_path"] = rng.choice(ACTIVATION_PATHS, size=n_acc)
        accounts["nps_before"] = rng.integers(20, 80, size=n_acc)
        accounts["nps_after_failure"] = accounts["nps_before"] - rng.integers(5, 35, size=n_acc)
        accounts["is_paying"] = True

    if not spans.empty and not runs.empty:
        run_costs = runs.set_index("run_id")["run_cost_usd"]
        span_counts = spans.groupby("agent_run_id")["span_id"].transform("count").clip(lower=1)
        spans["cost_usd"] = spans["agent_run_id"].map(run_costs).fillna(0) / span_counts
        base_times = runs.set_index("run_id")["started_at"]
        spans["started_at"] = (
            spans["agent_run_id"].map(base_times).fillna(pd.Timestamp("2024-06-01"))
            + pd.to_timedelta(spans["loop_iteration"].astype(int) * 2, unit="min")
        )

    if not usage_events.empty:
        usage_events["attribution_complete"] = rng.random(len(usage_events)) > 0.15

    catastrophic_rows = []
    if not runs.empty:
        n_cat = max(3, len(runs) // 200)
        cat_runs = runs.sample(n=min(n_cat, len(runs)), random_state=seed)
        for i, (_, run) in enumerate(cat_runs.iterrows()):
            catastrophic_rows.append({
                "event_id": f"CAT-{i:04d}",
                "run_id": run["run_id"],
                "seat_id": run["seat_id"],
                "occurred_at": run["started_at"],
                "severity": rng.choice(["high", "critical"], p=[0.6, 0.4]),
                "description": rng.choice([
                    "Agent deleted production records",
                    "Incorrect customer email sent",
                    "Compliance policy violation",
                ]),
                "churn_within_14d": bool(rng.random() < 0.4),
            })
    catastrophic_events = pd.DataFrame(catastrophic_rows) if catastrophic_rows else pd.DataFrame(
        columns=["event_id", "run_id", "seat_id", "occurred_at", "severity", "description", "churn_within_14d"]
    )

    routing_rows = []
    models = ["gpt-4o", "gpt-4o-mini", "claude-3.5", "gemini-pro"]
    for i, model in enumerate(models):
        routing_rows.append({
            "rule_id": f"ROUTE-{i:03d}",
            "model_id": model,
            "last_reviewed_at": pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(30, 200))),
            "static_age_days": int(rng.integers(45, 180)),
        })
    routing_decisions = pd.DataFrame(routing_rows)

    spend_rows = []
    if not runs.empty:
        cohorts = ["enterprise", "pro", "starter"]
        for step in STEP_KINDS:
            for model in models[:3]:
                for cohort in cohorts:
                    spend_rows.append({
                        "step_kind": step,
                        "model_id": model,
                        "cohort": cohort,
                        "spend_usd": float(rng.uniform(50, 2500)),
                    })
    spend_by_step = pd.DataFrame(spend_rows) if spend_rows else pd.DataFrame(
        columns=["step_kind", "model_id", "cohort", "spend_usd"]
    )

    jevons_rows = []
    for week in range(12):
        price = 0.002 * (0.92 ** week)
        volume = 1_000_000 * (1.08 ** week)
        jevons_rows.append({"week": f"W{week}", "unit_price": price, "token_volume": volume, "total_spend": price * volume})
    jevons_elasticity = pd.DataFrame(jevons_rows)

    flag_rows = []
    if not seats.empty:
        for flag in FEATURE_FLAGS:
            for seat_id in seats["seat_id"].sample(frac=0.4, random_state=seed + hash(flag) % 1000):
                flag_rows.append({
                    "seat_id": seat_id,
                    "flag_id": flag,
                    "variant": rng.choice(["control", "treatment"]),
                    "assigned_at": pd.Timestamp("2024-06-01"),
                })
    feature_flag_assignments = pd.DataFrame(flag_rows) if flag_rows else pd.DataFrame(
        columns=["seat_id", "flag_id", "variant", "assigned_at"]
    )

    retention_features = pd.DataFrame([
        {"feature": "first_success_7d", "importance": 0.28},
        {"feature": "integration_depth", "importance": 0.22},
        {"feature": "low_retry_rate", "importance": 0.18},
        {"feature": "human_review_accept", "importance": 0.14},
        {"feature": "weekly_logins", "importance": 0.06},
        {"feature": "feature_clicks", "importance": 0.04},
    ])

    agentic["runs"] = runs
    agentic["seats"] = seats
    agentic["accounts"] = accounts
    agentic["spans"] = spans
    agentic["usage_events"] = usage_events
    agentic["outcomes"] = outcomes
    agentic["catastrophic_events"] = catastrophic_events
    agentic["routing_decisions"] = routing_decisions
    agentic["spend_by_step"] = spend_by_step
    agentic["jevons_elasticity"] = jevons_elasticity
    agentic["feature_flag_assignments"] = feature_flag_assignments
    agentic["retention_features"] = retention_features
    agentic["challenge_meta"] = {
        "time_to_first_production_agent_days": int(profile.get("time_to_first_production_agent_days", 127)),
    }
    return agentic
