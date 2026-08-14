"""Token-cost VaR/CVaR and pricing shock simulation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from analytics.economics import calculate_run_cost, load_pricing_oracle
from core.workspace import Workspace


def daily_spend_series(ws: Workspace) -> pd.Series:
    runs = ws.runs
    if runs.empty or "run_cost_usd" not in runs.columns:
        return pd.Series(dtype=float)
    df = runs.copy()
    if "started_at" in df.columns:
        df["day"] = pd.to_datetime(df["started_at"]).dt.floor("D")
    else:
        df["day"] = pd.Timestamp("2025-01-01")
    return df.groupby("day")["run_cost_usd"].sum()


def token_cost_var(
    daily: pd.Series,
    *,
    alpha: float = 0.05,
    n_boot: int = 500,
    seed: int = 42,
) -> dict[str, float]:
    if daily.empty:
        return {"var": 0.0, "cvar": 0.0, "mean": 0.0}
    rng = np.random.default_rng(seed)
    vals = daily.values.astype(float)
    boots = [float(rng.choice(vals, size=len(vals), replace=True).sum()) for _ in range(n_boot)]
    arr = np.array(boots)
    var = float(np.quantile(arr, 1 - alpha))
    tail = arr[arr <= var]
    cvar = float(tail.mean()) if len(tail) else var
    return {"var": round(var, 2), "cvar": round(cvar, 2), "mean": round(float(arr.mean()), 2)}


def budget_breach_probability(daily: pd.Series, budget_usd: float, n_boot: int = 500, seed: int = 42) -> float:
    if daily.empty:
        return 0.0
    rng = np.random.default_rng(seed)
    vals = daily.values.astype(float)
    boots = [float(rng.choice(vals, size=len(vals), replace=True).sum()) for _ in range(n_boot)]
    return float((np.array(boots) > budget_usd).mean())


def pricing_shock_simulation(ws: Workspace, shock_pct: float = 0.0) -> dict[str, Any]:
    runs = ws.runs.copy()
    if runs.empty:
        return {"mean_daily": 0.0, "var": 0.0, "delta_mean": 0.0}
    profile = dict(ws.profile)
    oracle = load_pricing_oracle()
    models = oracle.get("models", {})
    for mid, m in models.items():
        m["input_cost_per_1k"] = float(m.get("input_cost_per_1k", 0.005)) * (1 + shock_pct)
        m["output_cost_per_1k"] = float(m.get("output_cost_per_1k", 0.015)) * (1 + shock_pct)
    oracle["models"] = models
    shocked = runs.copy()
    if "run_cost_usd" in shocked.columns:
        shocked["run_cost_usd"] = shocked["run_cost_usd"] * (1 + shock_pct)
    daily = shocked.groupby(pd.to_datetime(shocked.get("started_at", pd.Timestamp.now())).dt.floor("D"))["run_cost_usd"].sum()
    base_daily = daily_spend_series(ws)
    risk = token_cost_var(daily if not daily.empty else base_daily)
    base_mean = float(base_daily.sum() / max(1, len(base_daily))) if not base_daily.empty else 0.0
    return {
        "mean_daily": risk["mean"],
        "var": risk["var"],
        "cvar": risk["cvar"],
        "delta_mean": round(risk["mean"] - base_mean, 2),
        "shock_pct": shock_pct,
    }
