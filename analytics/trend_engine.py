"""
Trailing-window trend engine for capability guardrail metrics.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_trends(
    runs_df: pd.DataFrame,
    *,
    date_col: str = "started_at",
    metric: str = "steps_to_completion",
    windows_days: tuple[int, ...] = (7, 14, 28),
) -> dict[str, dict[str, Any]]:
    """
    For each capability, estimate weekly slope of `metric` over the longest
    available trailing window. Returns direction + slope_per_week.
    """
    if runs_df.empty or metric not in runs_df.columns or date_col not in runs_df.columns:
        return {}

    df = runs_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    max_ts = df[date_col].max()
    out: dict[str, dict[str, Any]] = {}

    for cap_id, grp in df.groupby("capability_id"):
        slope = 0.0
        window_used = windows_days[-1]
        for w in sorted(windows_days, reverse=True):
            cut = max_ts - pd.Timedelta(days=w)
            window = grp[grp[date_col] >= cut].sort_values(date_col)
            if len(window) < 5:
                continue
            # Weekly bucket means → simple linear slope
            window = window.copy()
            window["week"] = window[date_col].dt.to_period("W").astype(str)
            weekly = window.groupby("week", as_index=False)[metric].mean()
            if len(weekly) < 2:
                continue
            x = np.arange(len(weekly), dtype=float)
            y = weekly[metric].to_numpy(dtype=float)
            slope = float(np.polyfit(x, y, 1)[0])
            window_used = w
            break

        direction = "flat"
        if slope > 0.05:
            direction = "worsening"
        elif slope < -0.05:
            direction = "improving"

        out[str(cap_id)] = {
            "metric": metric,
            "direction": direction,
            "slope_per_week": round(slope, 4),
            "window_days": window_used,
        }
    return out


def detect_change_point(
    series: pd.Series,
    *,
    min_segment: int = 5,
) -> dict[str, Any]:
    """
    Simple binary-segmentation change-point on a metric series.
    Returns index of break and before/after means.
    """
    y = series.dropna().to_numpy(dtype=float)
    n = len(y)
    if n < 2 * min_segment:
        return {"detected": False, "break_index": None, "before_mean": None, "after_mean": None}

    best_idx = None
    best_score = -np.inf
    for i in range(min_segment, n - min_segment + 1):
        before = y[:i].mean()
        after = y[i:].mean()
        score = abs(after - before) * min(i, n - i)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx is None:
        return {"detected": False, "break_index": None, "before_mean": None, "after_mean": None}

    return {
        "detected": True,
        "break_index": int(best_idx),
        "before_mean": round(float(y[:best_idx].mean()), 4),
        "after_mean": round(float(y[best_idx:].mean()), 4),
        "delta": round(float(y[best_idx:].mean() - y[:best_idx].mean()), 4),
    }


def compute_trends_with_changepoints(
    runs_df: pd.DataFrame,
    *,
    date_col: str = "started_at",
    metric: str = "steps_to_completion",
) -> dict[str, dict[str, Any]]:
    """Trends plus optional change-point on weekly success rate."""
    trends = compute_trends(runs_df, date_col=date_col, metric=metric)
    if runs_df.empty or "capability_id" not in runs_df.columns:
        return trends

    df = runs_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["week"] = df[date_col].dt.to_period("W").astype(str)

    for cap_id, grp in df.groupby("capability_id"):
        weekly = grp.groupby("week")["success"].mean() if "success" in grp.columns else pd.Series(dtype=float)
        if len(weekly) >= 6:
            cp = detect_change_point(weekly)
            if cap_id in trends:
                trends[str(cap_id)]["change_point"] = cp
            else:
                trends[str(cap_id)] = {"change_point": cp}
    return trends
