"""Contextual bandits — YAML-governed Thompson sampling with regret teaching."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.workspace import Workspace

DEFAULT_POLICY = {
    "exploration_rate": 0.1,
    "prior_alpha": 1.0,
    "prior_beta": 1.0,
    "min_traffic_floor": 0.15,
    "algorithm": "thompson",
}


def bandit_policy_from_semantics(semantics_overlay: dict[str, Any] | None) -> dict[str, Any]:
    """Read bandit policy block from semantics overlay."""
    overlay = semantics_overlay or {}
    policy = dict(DEFAULT_POLICY)
    policy.update(overlay.get("bandit", {}))
    return policy


def cumulative_regret(
    rewards_by_arm: dict[str, list[float]],
    optimal_arm: str,
) -> dict[str, Any]:
    """Cumulative regret vs known optimal arm (teaching simulation)."""
    arms = list(rewards_by_arm.keys())
    if not arms or optimal_arm not in rewards_by_arm:
        return {"rounds": [], "total_regret": 0.0}

    max_len = max(len(rewards_by_arm[a]) for a in arms)
    optimal_rewards = rewards_by_arm[optimal_arm]
    chosen_rewards = []
    for t in range(max_len):
        best_arm = max(arms, key=lambda a: rewards_by_arm[a][t] if t < len(rewards_by_arm[a]) else -1)
        r = rewards_by_arm[best_arm][t] if t < len(rewards_by_arm[best_arm]) else 0.0
        chosen_rewards.append(r)

    cum_regret = []
    total = 0.0
    for t in range(max_len):
        opt_r = optimal_rewards[t] if t < len(optimal_rewards) else 0.0
        total += opt_r - chosen_rewards[t]
        cum_regret.append(round(total, 4))

    return {
        "rounds": list(range(1, len(cum_regret) + 1)),
        "cumulative_regret": cum_regret,
        "total_regret": round(total, 4),
        "optimal_arm": optimal_arm,
    }


def simulate_bandit_regret(
    true_rates: dict[str, float],
    *,
    n_rounds: int = 200,
    policy: dict[str, Any] | None = None,
    seed: int = 42,
) -> dict[str, Any]:
    """Simulate Thompson allocation regret against planted Bernoulli rates."""
    policy = policy or DEFAULT_POLICY
    rng = np.random.default_rng(seed)
    arms = list(true_rates.keys())
    optimal = max(arms, key=lambda a: true_rates[a])
    alpha = float(policy.get("prior_alpha", 1))
    beta = float(policy.get("prior_beta", 1))
    floor = float(policy.get("min_traffic_floor", 0.15))
    explore = float(policy.get("exploration_rate", 0.1))

    succ = {a: 0 for a in arms}
    fail = {a: 0 for a in arms}
    rewards_by_arm: dict[str, list[float]] = {a: [] for a in arms}
    chosen: list[str] = []

    for _ in range(n_rounds):
        samples = {}
        for a in arms:
            draw = rng.beta(succ[a] + alpha, fail[a] + beta)
            samples[a] = draw
        pick = max(samples, key=samples.get)
        if rng.random() < explore:
            pick = rng.choice(arms)
        win = rng.random() < true_rates[pick]
        if win:
            succ[pick] += 1
        else:
            fail[pick] += 1
        rewards_by_arm[pick].append(1.0 if win else 0.0)
        chosen.append(pick)

    traffic = {a: chosen.count(a) / n_rounds for a in arms}
    for a in arms:
        traffic[a] = max(traffic[a], floor if a != optimal else traffic[a])
    total = sum(traffic.values()) or 1
    traffic = {a: round(v / total, 3) for a, v in traffic.items()}

    regret = cumulative_regret(rewards_by_arm, optimal)
    return {
        "arms": arms,
        "true_rates": true_rates,
        "recommended_traffic": traffic,
        "regret": regret,
        "policy": policy,
        "message": f"Policy favors {max(traffic, key=traffic.get)}; cumulative regret {regret['total_regret']:.1f}.",
    }


def thompson_allocation(
    workspace: Workspace,
    capability_id: str,
    *,
    n_draws: int = 1000,
    seed: int = 42,
    semantics_overlay: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    2-arm Beta-Bernoulli Thompson on success×cost reward.
    When semantics overlay includes bandit policy, apply exploration floor + regret sim.
    """
    policy = bandit_policy_from_semantics(semantics_overlay)
    rng = np.random.default_rng(seed)
    runs = workspace.runs
    if runs.empty or "capability_id" not in runs.columns:
        return {"arms": [], "recommended_traffic": {}, "policy": policy}

    cap_runs = runs[runs["capability_id"] == capability_id]
    if "capability_version" not in cap_runs.columns:
        return {"arms": [], "recommended_traffic": {}, "policy": policy}

    versions = cap_runs["capability_version"].value_counts().head(2).index.tolist()
    if len(versions) < 2:
        return {
            "arms": versions,
            "recommended_traffic": {versions[0]: 1.0} if versions else {},
            "policy": policy,
        }

    alpha = float(policy.get("prior_alpha", 1))
    beta = float(policy.get("prior_beta", 1))
    floor = float(policy.get("min_traffic_floor", 0.15))
    explore = float(policy.get("exploration_rate", 0.1))

    wins = {v: 0 for v in versions}
    true_rates: dict[str, float] = {}
    for v in versions:
        sub = cap_runs[cap_runs["capability_version"] == v]
        succ = int(sub["success"].sum()) if "success" in sub.columns else 0
        true_rates[v] = succ / max(1, len(sub))

    for _ in range(n_draws):
        samples = []
        for v in versions:
            sub = cap_runs[cap_runs["capability_version"] == v]
            succ = int(sub["success"].sum()) if "success" in sub.columns else 0
            fail = max(1, len(sub) - succ)
            cost = float(sub["run_cost_usd"].mean()) if "run_cost_usd" in sub.columns else 1.0
            draw = rng.beta(succ + alpha, fail + beta)
            reward = draw / max(cost, 0.01)
            samples.append((v, reward))
        best = max(samples, key=lambda x: x[1])[0]
        if rng.random() < explore:
            best = rng.choice(versions)
        wins[best] += 1

    total = sum(wins.values()) or 1
    traffic = {v: round(wins[v] / total, 3) for v in versions}
    for v in versions:
        traffic[v] = max(traffic[v], floor)

    t_total = sum(traffic.values()) or 1
    traffic = {k: round(v / t_total, 3) for k, v in traffic.items()}

    regret_sim = simulate_bandit_regret(true_rates, n_rounds=min(200, n_draws), policy=policy, seed=seed)

    return {
        "arms": versions,
        "recommended_traffic": traffic,
        "n_draws": n_draws,
        "policy": policy,
        "regret": regret_sim.get("regret"),
        "message": (
            f"YAML policy ({policy.get('algorithm', 'thompson')}) favors "
            f"{max(traffic, key=traffic.get)} at {max(traffic.values()):.0%}."
        ),
    }
