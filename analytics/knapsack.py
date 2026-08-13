"""Intervention knapsack — maximize expected $ saved under HITL capacity."""

from __future__ import annotations

from typing import Any


def _expected_savings(record: dict[str, Any]) -> float:
    econ = record.get("economics", {})
    cost = float(econ.get("primary_metric_usd", 0))
    risk = float(record.get("p_churn_30d") or record.get("risk_score") or 0.1)
    harm = 0.0
    for exc in record.get("exceptions", []):
        ev = exc.get("evidence") or {}
        harm = max(harm, float((ev.get("posterior") or {}).get("mean", 0)))
    return cost * (risk + harm)


def select_interventions_gdr(
    records: list[dict[str, Any]],
    hitl_capacity: int,
    *,
    review_cost: float = 0.0,
) -> dict[str, Any]:
    """
    0-1 knapsack: pick up to `hitl_capacity` records maximizing net expected savings.
    Each record costs 1 review slot (+ optional review_cost).
    """
    capacity = max(0, int(hitl_capacity))
    if capacity == 0 or not records:
        return {"selected": [], "total_savings_usd": 0.0, "capacity": capacity}

    items = []
    for i, rec in enumerate(records):
        benefit = _expected_savings(rec) - review_cost
        if benefit <= 0:
            continue
        items.append((i, int(benefit), 1))

    if not items:
        return {"selected": [], "total_savings_usd": 0.0, "capacity": capacity}

    n = len(items)
    cap = capacity
    dp = [[0] * (cap + 1) for _ in range(n + 1)]
    keep = [[False] * (cap + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        idx, val, wt = items[i - 1]
        for w in range(cap + 1):
            dp[i][w] = dp[i - 1][w]
            if wt <= w and dp[i - 1][w - wt] + val > dp[i][w]:
                dp[i][w] = dp[i - 1][w - wt] + val
                keep[i][w] = True

    selected_idx: list[int] = []
    w = cap
    for i in range(n, 0, -1):
        if keep[i][w]:
            selected_idx.append(items[i - 1][0])
            w -= items[i - 1][2]

    selected = [records[i] for i in selected_idx]
    total = sum(_expected_savings(r) for r in selected) - review_cost * len(selected)
    return {
        "selected": selected,
        "selected_ids": [r.get("record_id") for r in selected],
        "total_savings_usd": round(total, 2),
        "capacity": capacity,
        "n_candidates": len(records),
    }


def hitl_review_slots(workspace, profile: dict[str, Any] | None = None) -> int:
    """Derive weekly review slots from Erlang-C staffing (teaching heuristic)."""
    from analytics.queueing import hitl_queue_from_workspace

    profile = profile or workspace.profile
    q = hitl_queue_from_workspace(workspace, profile)
    reviewers = int(q.get("reviewers", 3))
    sla = float(q.get("sla_hours", 4.0))
    service = float(profile.get("hitl_capacity", {}).get("approvals_per_reviewer_per_hour", 2.0))
    slots = int(reviewers * service * sla * 5 / 8)
    return max(1, min(slots, 10))
