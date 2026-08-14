"""Always-valid confidence sequences — teaching asymptotic bounds."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def cs_mean(samples: np.ndarray | list, alpha: float = 0.05) -> dict[str, Any]:
    """Asymptotic confidence sequence radius for a running mean."""
    arr = np.asarray(samples, dtype=float)
    n = len(arr)
    if n == 0:
        return {"n": 0, "mean": 0.0, "lo": 0.0, "hi": 0.0, "radius": 0.0}
    mean = float(arr.mean())
    z = 1.96 if alpha <= 0.05 else 1.64
    radius = z * math.sqrt((math.log(max(n, 2)) + 1) / n) * max(float(arr.std(ddof=1)), 0.01)
    return {
        "n": n,
        "mean": round(mean, 4),
        "lo": round(mean - radius, 4),
        "hi": round(mean + radius, 4),
        "radius": round(radius, 4),
    }


def cs_two_proportion(
    s_control: int,
    n_control: int,
    s_variant: int,
    n_variant: int,
    *,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Confidence sequence on proportion difference p_v - p_c at cumulative n."""
    if n_control < 1 or n_variant < 1:
        return {"delta": 0.0, "lo": -1.0, "hi": 1.0, "series": []}
    n_total = n_control + n_variant
    p_c = s_control / n_control
    p_v = s_variant / n_variant
    delta = p_v - p_c
    z = 1.96 if alpha <= 0.05 else 1.64
    radius = z * math.sqrt((math.log(max(n_total, 2)) + 1) / n_total) * 0.5
    series = []
    for k in range(1, n_total + 1, max(1, n_total // 20)):
        r = z * math.sqrt((math.log(max(k, 2)) + 1) / k) * 0.5
        series.append({"n": k, "delta": round(delta, 4), "lo": round(delta - r, 4), "hi": round(delta + r, 4)})
    return {
        "delta": round(delta, 4),
        "lo": round(delta - radius, 4),
        "hi": round(delta + radius, 4),
        "series": series,
        "n_total": n_total,
    }


def cs_covers(true_value: float, lo: float, hi: float) -> bool:
    return lo <= true_value <= hi
