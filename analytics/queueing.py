"""HITL queueing — Erlang-C staffing implications."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from core.workspace import Workspace


def erlang_c(
    arrival_rate: float,
    service_rate: float,
    servers: int,
) -> dict[str, Any]:
    """
    M/M/c queue: P(wait), expected wait (hours).
    arrival_rate λ (approvals/hr), service_rate μ (approvals/hr per reviewer).
    """
    if servers < 1 or service_rate <= 0 or arrival_rate < 0:
        return {"p_wait": 0.0, "expected_wait_hr": 0.0, "utilization": 0.0}

    a = arrival_rate / service_rate
    rho = a / servers
    if rho >= 1:
        return {
            "p_wait": 1.0,
            "expected_wait_hr": float("inf"),
            "utilization": rho,
            "overloaded": True,
        }

    # Erlang-C formula
    sum_terms = sum(a**k / math.factorial(k) for k in range(servers))
    last = (a**servers / math.factorial(servers)) * (servers / (servers - a))
    p0 = 1.0 / (sum_terms + last)
    pw = last * p0

    ew = pw / (servers * service_rate - arrival_rate) if servers * service_rate > arrival_rate else float("inf")
    return {
        "p_wait": round(pw, 4),
        "expected_wait_hr": round(ew, 3),
        "utilization": round(rho, 3),
        "overloaded": False,
    }


def hitl_queue_from_workspace(
    workspace: Workspace,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Estimate HITL queue from approvals table + profile capacity."""
    profile = profile or workspace.profile
    cap = profile.get("hitl_capacity", {})
    reviewers = int(cap.get("reviewers", 3))
    sla_hours = float(cap.get("sla_hours", 4.0))
    service_rate = float(cap.get("approvals_per_reviewer_per_hour", 2.0))

    approvals = getattr(workspace, "approvals", pd.DataFrame())
    if approvals.empty:
        arrival_rate = 1.5
    else:
        arrival_rate = max(0.1, len(approvals) / (30 * 8))

    result = erlang_c(arrival_rate, service_rate, reviewers)
    result["p_wait_exceeds_sla"] = (
        1.0 if result.get("expected_wait_hr", 0) > sla_hours else result["p_wait"]
    )
    result["reviewers"] = reviewers
    result["sla_hours"] = sla_hours
    result["arrival_rate"] = round(arrival_rate, 2)
    return result
