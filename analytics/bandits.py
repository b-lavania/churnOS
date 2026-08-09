"""Contextual bandits — teaching Thompson sampling on capability versions."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.workspace import Workspace


def thompson_allocation(
    workspace: Workspace,
    capability_id: str,
    *,
    n_draws: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """
    2-arm Beta-Bernoulli Thompson on success×cost reward.
    Teaching only — not a production rollout engine.
    """
    rng = np.random.default_rng(seed)
    runs = workspace.runs
    if runs.empty or "capability_id" not in runs.columns:
        return {"arms": [], "recommended_traffic": {}}

    cap_runs = runs[runs["capability_id"] == capability_id]
    if "capability_version" not in cap_runs.columns:
        return {"arms": [], "recommended_traffic": {}}

    versions = cap_runs["capability_version"].value_counts().head(2).index.tolist()
    if len(versions) < 2:
        return {"arms": versions, "recommended_traffic": {versions[0]: 1.0} if versions else {}}

    arms = []
    wins = {v: 0 for v in versions}
    for _ in range(n_draws):
        samples = []
        for v in versions:
            sub = cap_runs[cap_runs["capability_version"] == v]
            succ = int(sub["success"].sum()) if "success" in sub.columns else 0
            fail = max(1, len(sub) - succ)
            cost = float(sub["run_cost_usd"].mean()) if "run_cost_usd" in sub.columns else 1.0
            draw = rng.beta(succ + 1, fail + 1)
            reward = draw / max(cost, 0.01)
            samples.append((v, reward))
        best = max(samples, key=lambda x: x[1])[0]
        wins[best] += 1

    total = sum(wins.values()) or 1
    traffic = {v: round(wins[v] / total, 3) for v in versions}
    return {
        "arms": versions,
        "recommended_traffic": traffic,
        "n_draws": n_draws,
        "message": f"Thompson sampling favors {max(traffic, key=traffic.get)} at {max(traffic.values()):.0%}.",
    }
