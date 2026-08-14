"""Distributional drift — KL/JS divergence and change-point detection."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.workspace import Workspace


def _smooth(p: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    p = np.asarray(p, dtype=float) + eps
    return p / p.sum()


def kl_divergence(p: np.ndarray | list, q: np.ndarray | list) -> float:
    p = _smooth(p)
    q = _smooth(q)
    return float(np.sum(p * np.log(p / q)))


def js_divergence(p: np.ndarray | list, q: np.ndarray | list) -> float:
    p = _smooth(p)
    q = _smooth(q)
    m = 0.5 * (p + q)
    return float(0.5 * kl_divergence(p, m) + 0.5 * kl_divergence(q, m))


def outcome_mix(ws: Workspace, start: pd.Timestamp, end: pd.Timestamp) -> np.ndarray:
    runs = ws.runs
    if runs.empty or "started_at" not in runs.columns:
        return np.array([0.5, 0.5])
    df = runs.copy()
    df["started_at"] = pd.to_datetime(df["started_at"])
    mask = (df["started_at"] >= start) & (df["started_at"] < end)
    sub = df[mask]
    if sub.empty:
        return np.array([0.5, 0.5])
    succ = float(sub["success"].astype(bool).mean()) if "success" in sub.columns else 0.5
    return np.array([succ, 1 - succ])


def window_drift(baseline_pmf: np.ndarray, recent_pmf: np.ndarray) -> dict[str, float]:
    return {
        "kl": round(kl_divergence(baseline_pmf, recent_pmf), 4),
        "js": round(js_divergence(baseline_pmf, recent_pmf), 4),
    }


def outcome_distribution_drift(ws: Workspace, window_days: int = 14) -> dict[str, Any]:
    runs = ws.runs
    if runs.empty or "started_at" not in runs.columns:
        return {"kl": 0.0, "js": 0.0, "baseline": [0.5, 0.5], "recent": [0.5, 0.5]}
    end = pd.to_datetime(runs["started_at"]).max()
    recent_start = end - pd.Timedelta(days=window_days)
    baseline_start = recent_start - pd.Timedelta(days=window_days)
    baseline = outcome_mix(ws, baseline_start, recent_start)
    recent = outcome_mix(ws, recent_start, end + pd.Timedelta(days=1))
    drift = window_drift(baseline, recent)
    return {**drift, "baseline": baseline.tolist(), "recent": recent.tolist()}


def weekly_success_series(ws: Workspace) -> pd.DataFrame:
    runs = ws.runs
    if runs.empty:
        return pd.DataFrame(columns=["week", "success_rate"])
    df = runs.copy()
    df["started_at"] = pd.to_datetime(df["started_at"])
    df["week"] = df["started_at"].dt.to_period("W").dt.start_time
    weekly = df.groupby("week", as_index=False).agg(success_rate=("success", "mean"))
    return weekly


def cusum_change_point(series: np.ndarray | list, threshold: float = 0.05) -> int | None:
    arr = np.asarray(series, dtype=float)
    if len(arr) < 5:
        return None
    mean = arr.mean()
    cusum = np.cumsum(arr - mean)
    idx = int(np.argmax(np.abs(cusum)))
    if np.abs(cusum[idx]) < threshold * len(arr):
        return None
    return idx


def drift_summary(ws: Workspace) -> dict[str, Any]:
    od = outcome_distribution_drift(ws)
    weekly = weekly_success_series(ws)
    cp = None
    if not weekly.empty:
        cp = cusum_change_point(weekly["success_rate"].values)
    cp_week = str(weekly.iloc[cp]["week"].date()) if cp is not None and not weekly.empty else None
    return {**od, "change_point_index": cp, "change_point_week": cp_week, "weekly": weekly}
