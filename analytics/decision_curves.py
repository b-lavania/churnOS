"""Decision-curve / net-benefit analysis for threshold policies."""

from __future__ import annotations

from typing import Any

import numpy as np


def net_benefit_curve(
    y_true: np.ndarray | list,
    y_score: np.ndarray | list,
    thresholds: np.ndarray | list | None = None,
    *,
    cost_fp: float = 1.0,
    cost_fn: float = 5.0,
) -> list[dict[str, float]]:
    """
    Net benefit across a threshold grid.
    Treat positive prediction as intervene (rollback/throttle); y_true=1 is event (churn/harm).
    """
    yt = np.asarray(y_true, dtype=int)
    ys = np.asarray(y_score, dtype=float)
    n = len(yt)
    if n == 0:
        return []

    if thresholds is None:
        thresholds = np.linspace(0.05, 0.95, 19)

    curve: list[dict[str, float]] = []
    for t in thresholds:
        pred_pos = ys >= t
        tp = int(((pred_pos) & (yt == 1)).sum())
        fp = int(((pred_pos) & (yt == 0)).sum())
        fn = int(((~pred_pos) & (yt == 1)).sum())
        tn = int(((~pred_pos) & (yt == 0)).sum())
        nb = (tp / n) * cost_fn - (fp / n) * cost_fp
        curve.append({
            "threshold": round(float(t), 3),
            "net_benefit": round(float(nb), 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "treat_all": round(float(cost_fn * yt.mean() - cost_fp * (1 - yt.mean())), 4),
            "treat_none": 0.0,
        })
    return curve


def optimal_threshold(curve: list[dict[str, float]]) -> dict[str, float] | None:
    """Peak net-benefit point on the curve."""
    if not curve:
        return None
    best = max(curve, key=lambda x: x["net_benefit"])
    return {"threshold": best["threshold"], "net_benefit": best["net_benefit"]}


def operating_point_from_semantics(semantics_overlay: dict[str, Any] | None) -> dict[str, float]:
    """Read decision threshold from semantics overlay."""
    overlay = semantics_overlay or {}
    pt = overlay.get("classification", {}).get("posterior_thresholds", {})
    return {
        "p_churn_30d_min": float(pt.get("p_churn_30d_min", 0.5)),
        "cost_fp": float(pt.get("cost_false_positive", 1.0)),
        "cost_fn": float(pt.get("cost_false_negative", 5.0)),
    }
