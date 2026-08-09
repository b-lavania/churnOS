"""Pareto-optimal ranking for capability guardrail tuples."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.workspace import Workspace


def capability_guardrail_tuple(
    workspace: Workspace,
    capability_id: str,
) -> tuple[float, float, float]:
    """
    Return (success_rate, cpso, trust_rate) for Pareto dominance.
    Higher success/trust is better; lower CPSO is better.
    """
    runs = workspace.runs
    caps = workspace.capabilities
    if runs.empty:
        return (0.0, 999.0, 0.0)

    cap_runs = runs[runs["capability_id"] == capability_id] if "capability_id" in runs.columns else runs.iloc[0:0]
    if cap_runs.empty:
        return (0.0, 999.0, 0.0)

    success_rate = float(cap_runs["success"].mean()) if "success" in cap_runs.columns else 0.0
    cost = float(cap_runs["run_cost_usd"].sum()) if "run_cost_usd" in cap_runs.columns else 0.0
    n_ok = max(1, int(cap_runs["success"].sum()) if "success" in cap_runs.columns else 1)
    cpso = cost / n_ok

    trust_rate = 0.7
    if "hitl_triggered" in cap_runs.columns:
        hitl = cap_runs["hitl_triggered"].astype(bool)
        trust_rate = float((cap_runs["success"].astype(bool) & ~hitl).mean())

    return (success_rate, cpso, trust_rate)


def is_dominated(a: tuple[float, float, float], b: tuple[float, float, float]) -> bool:
    """True if a is dominated by b (b better on all objectives)."""
    sr_a, cpso_a, trust_a = a
    sr_b, cpso_b, trust_b = b
    better_or_equal = sr_b >= sr_a and cpso_b <= cpso_a and trust_b >= trust_a
    strictly_better = sr_b > sr_a or cpso_b < cpso_a or trust_b > trust_a
    return better_or_equal and strictly_better


def pareto_frontier_indices(tuples: list[tuple[float, float, float]]) -> list[int]:
    """Indices of non-dominated tuples."""
    n = len(tuples)
    frontier = []
    for i, ti in enumerate(tuples):
        dominated = any(is_dominated(ti, tuples[j]) for j in range(n) if j != i)
        if not dominated:
            frontier.append(i)
    return frontier


def rank_capability_records(
    records: list[dict[str, Any]],
    workspace: Workspace,
    *,
    mode: str = "cost",
) -> list[dict[str, Any]]:
    """Re-rank capability GDRs by cost or Pareto frontier."""
    cap_recs = [r for r in records if r.get("subject", {}).get("entity_type") == "capability"]
    other = [r for r in records if r.get("subject", {}).get("entity_type") != "capability"]

    if not cap_recs:
        return records

    tuples = []
    for rec in cap_recs:
        cap_id = rec.get("subject", {}).get("capability_id", "")
        tuples.append(capability_guardrail_tuple(workspace, cap_id))

    frontier = set(pareto_frontier_indices(tuples))

    enriched = []
    for i, rec in enumerate(cap_recs):
        updated = dict(rec)
        on_frontier = i in frontier
        updated["pareto_frontier"] = on_frontier
        if not on_frontier:
            updated["pareto_caption"] = "Dominated on success×cost×trust"
        harm_mean = 0.0
        for exc in rec.get("exceptions", []):
            ev = exc.get("evidence") or {}
            harm_mean = max(harm_mean, (ev.get("posterior") or {}).get("mean", 0))
        cost = rec.get("economics", {}).get("primary_metric_usd", 0)
        updated["_sort_key"] = (
            0 if on_frontier else 1,
            -(cost * (1 + harm_mean)) if mode == "pareto" else -cost,
        )
        enriched.append(updated)

    enriched.sort(key=lambda r: r["_sort_key"])
    for r in enriched:
        r.pop("_sort_key", None)
    return other + enriched
