"""Segment lift analysis for feature-flag experiments with FDR control."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from analytics.experimentation import benjamini_hochberg
from core.workspace import Workspace


def _two_prop_pvalue(ctrl_ok: int, ctrl_n: int, trt_ok: int, trt_n: int) -> float:
    if ctrl_n < 2 or trt_n < 2:
        return 1.0
    table = np.array([[ctrl_ok, ctrl_n - ctrl_ok], [trt_ok, trt_n - trt_ok]])
    try:
        _, p, _, _ = stats.chi2_contingency(table)
        return float(p)
    except Exception:
        return 1.0


def flag_segment_table(workspace: Workspace, flag_id: str) -> list[dict[str, Any]]:
    """Per-segment treatment vs control lift with raw p-values."""
    agentic = getattr(workspace, "agentic", {}) or {}
    assigns = agentic.get("feature_flag_assignments")
    if assigns is None or (isinstance(assigns, pd.DataFrame) and assigns.empty):
        return []

    assigns = assigns[assigns["flag_id"] == flag_id] if "flag_id" in assigns.columns else assigns.iloc[0:0]
    if assigns.empty:
        return []

    seats = workspace.seats.copy()
    if "account_id" not in seats.columns and "workspace_id" in seats.columns:
        seats["account_id"] = seats["workspace_id"]

    merged = assigns.merge(seats, on="seat_id", how="left")
    runs = workspace.runs
    if runs.empty:
        return []

    run_sr = runs.groupby("seat_id")["success"].mean().reset_index(name="success_rate")
    merged = merged.merge(run_sr, on="seat_id", how="left")
    merged["success_rate"] = merged["success_rate"].fillna(0.0)

    rows: list[dict[str, Any]] = []
    segment_dims = []
    if "tier" in merged.columns:
        segment_dims.append(("tier", merged["tier"].dropna().unique()[:4]))
    if "plan" in merged.columns:
        segment_dims.append(("plan", merged["plan"].dropna().unique()[:4]))
    if "is_activated" in merged.columns:
        segment_dims.append(("activation", ["activated", "not_activated"]))

    for dim, values in segment_dims:
        for val in values:
            if dim == "activation":
                seg = merged[merged["is_activated"] == (val == "activated")]
            else:
                seg = merged[merged[dim] == val]
            ctrl = seg[seg["variant"] == "control"]
            trt = seg[seg["variant"] == "treatment"]
            if len(ctrl) < 3 or len(trt) < 3:
                continue
            p_ctrl = float(ctrl["success_rate"].mean())
            p_trt = float(trt["success_rate"].mean())
            lift_pp = (p_trt - p_ctrl) * 100
            ctrl_ok = int((ctrl["success_rate"] > 0.5).sum())
            trt_ok = int((trt["success_rate"] > 0.5).sum())
            pval = _two_prop_pvalue(ctrl_ok, len(ctrl), trt_ok, len(trt))
            rows.append({
                "segment": f"{dim}={val}",
                "control_rate": round(p_ctrl, 3),
                "treatment_rate": round(p_trt, 3),
                "lift_pp": round(lift_pp, 2),
                "p_value": round(pval, 4),
                "n_control": len(ctrl),
                "n_treatment": len(trt),
            })

    if not rows:
        return rows

    pvals = [r["p_value"] for r in rows]
    sig = benjamini_hochberg(pvals)
    for r, s in zip(rows, sig):
        r["fdr_significant"] = s
    return rows
