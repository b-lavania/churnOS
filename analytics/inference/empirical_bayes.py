"""Empirical Bayes shrinkage for capability harm rates."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.workspace import Workspace


def fit_beta_mom(rates: np.ndarray, ns: np.ndarray) -> tuple[float, float]:
    """Method-of-moments Beta prior from per-unit rates."""
    rates = np.asarray(rates, dtype=float)
    ns = np.asarray(ns, dtype=float)
    mask = ns > 0
    if mask.sum() < 2:
        return 1.0, 9.0
    r = rates[mask]
    v = np.var(r)
    m = np.mean(r)
    if v <= 1e-8 or m <= 0 or m >= 1:
        return 1.0, 9.0
    common = m * (1 - m) / v - 1
    alpha0 = max(0.5, m * common)
    beta0 = max(0.5, (1 - m) * common)
    return float(alpha0), float(beta0)


def shrink_rate(successes: int, trials: int, alpha0: float, beta0: float) -> float:
    return (alpha0 + successes) / (alpha0 + beta0 + trials)


def capability_harm_eb(ws: Workspace) -> pd.DataFrame:
    from analytics.decisions import _capability_stats

    caps = _capability_stats(ws)
    if caps.empty:
        return pd.DataFrame(columns=["capability_id", "raw", "shrunk", "n"])
    caps = caps.copy()
    caps["n"] = caps["run_count"].clip(lower=1).astype(int)
    caps["successes"] = (caps["harm_score"] * caps["n"]).round().astype(int)
    alpha0, beta0 = fit_beta_mom(caps["harm_score"].values, caps["n"].values)
    rows = []
    for _, row in caps.iterrows():
        n = int(row["n"])
        s = int(min(n, max(0, row["successes"])))
        raw = float(row["harm_score"])
        shrunk = shrink_rate(s, n, alpha0, beta0)
        rows.append({
            "capability_id": row["capability_id"],
            "raw": round(raw, 4),
            "shrunk": round(shrunk, 4),
            "n": n,
            "alpha0": round(alpha0, 3),
            "beta0": round(beta0, 3),
        })
    return pd.DataFrame(rows)


def capability_harm_eb_one(ws: Workspace, capability_id: str) -> dict[str, Any]:
    """Shrunk harm rate for a single capability (used by classify)."""
    df = capability_harm_eb(ws)
    row = df[df["capability_id"] == capability_id]
    if row.empty:
        return {"shrunk_rate": 0.0, "raw_rate": 0.0, "n": 0, "alpha0": 1.0, "beta0": 9.0}
    r = row.iloc[0]
    return {
        "shrunk_rate": float(r["shrunk"]),
        "raw_rate": float(r["raw"]),
        "n": int(r["n"]),
        "alpha0": float(r.get("alpha0", 1.0)),
        "beta0": float(r.get("beta0", 9.0)),
    }


def global_prior(ws: Workspace) -> dict[str, float]:
    df = capability_harm_eb(ws)
    if df.empty:
        return {"alpha0": 1.0, "beta0": 9.0, "mean": 0.1}
    a, b = fit_beta_mom(df["raw"].values, df["n"].values)
    return {"alpha0": a, "beta0": b, "mean": round(a / (a + b), 4)}
