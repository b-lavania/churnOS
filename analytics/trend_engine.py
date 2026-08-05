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
