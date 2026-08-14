"""Agent-mediated marketplace economics — platform margin after inference."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.workspace import Workspace


def _txn(ws: Workspace) -> pd.DataFrame:
    return getattr(ws, "agent_transactions", pd.DataFrame())


def agent_assisted_take_rate(ws: Workspace) -> dict[str, float]:
    txn = _txn(ws)
    if txn.empty:
        return {"assisted": 0.0, "manual": 0.0, "lift": 0.0}
    assisted = txn[txn["agent_assist_type"] != "none"]
    manual = txn[txn["agent_assist_type"] == "none"]
    a_rate = float(assisted["take_rate"].mean()) if not assisted.empty else 0.0
    m_rate = float(manual["take_rate"].mean()) if not manual.empty else 0.0
    return {"assisted": a_rate, "manual": m_rate, "lift": a_rate - m_rate}


def platform_margin_after_inference(ws: Workspace) -> dict[str, Any]:
    txn = _txn(ws)
    if txn.empty:
        return {"margin_usd": 0.0, "margin_pct": 0.0, "n": 0}
    assisted = txn[txn["agent_assist_type"] != "none"]
    if assisted.empty:
        return {"margin_usd": 0.0, "margin_pct": 0.0, "n": 0}
    rev = float(assisted["platform_revenue_usd"].sum())
    cost = float(assisted["agent_inference_cost_usd"].sum())
    margin = rev - cost
    gmv = float(assisted["gmv_usd"].sum())
    return {
        "margin_usd": round(margin, 2),
        "margin_pct": round(margin / max(gmv, 1), 4),
        "revenue_usd": round(rev, 2),
        "inference_usd": round(cost, 2),
        "gmv_usd": round(gmv, 2),
        "n": len(assisted),
    }


def transaction_cpso(ws: Workspace) -> dict[str, float]:
    txn = _txn(ws)
    if txn.empty:
        return {"cpso": 0.0, "n_verified": 0}
    ok = txn[(txn["success"]) & (txn["verified"])]
    if ok.empty:
        return {"cpso": 0.0, "n_verified": 0}
    cost = float(ok["agent_inference_cost_usd"].sum())
    n = len(ok)
    return {"cpso": round(cost / n, 2), "n_verified": n}


def agent_gmv_attribution(ws: Workspace) -> pd.DataFrame:
    txn = _txn(ws)
    if txn.empty:
        return pd.DataFrame(columns=[
            "assist_type", "capability_id", "gmv_usd", "platform_revenue_usd",
            "agent_inference_cost_usd", "net_margin_usd",
        ])
    assisted = txn[txn["agent_assist_type"] != "none"].copy()
    assisted["net_margin_usd"] = assisted["platform_revenue_usd"] - assisted["agent_inference_cost_usd"]
    agg = (
        assisted.groupby(["agent_assist_type", "capability_id"], as_index=False)
        .agg(
            gmv_usd=("gmv_usd", "sum"),
            platform_revenue_usd=("platform_revenue_usd", "sum"),
            agent_inference_cost_usd=("agent_inference_cost_usd", "sum"),
            net_margin_usd=("net_margin_usd", "sum"),
        )
        .rename(columns={"agent_assist_type": "assist_type"})
    )
    return agg


def workflow_unit_economics(ws: Workspace, capability_id: str) -> dict[str, Any]:
    txn = _txn(ws)
    sub = txn[(txn["capability_id"] == capability_id) & (txn["agent_assist_type"] != "none")]
    if sub.empty:
        return {"capability_id": capability_id, "cpso": 0.0, "take_per_txn": 0.0, "net_margin": 0.0}
    rev = float(sub["platform_revenue_usd"].sum())
    cost = float(sub["agent_inference_cost_usd"].sum())
    n = max(1, len(sub))
    return {
        "capability_id": capability_id,
        "cpso": round(cost / n, 2),
        "take_per_txn": round(rev / n, 2),
        "net_margin": round(rev - cost, 2),
        "n_txn": n,
    }


def seller_margin_table(ws: Workspace) -> pd.DataFrame:
    txn = _txn(ws)
    if txn.empty:
        return pd.DataFrame(columns=[
            "seller_id", "gmv_usd", "assist_share", "net_margin", "verified_rate",
        ])
    rows = []
    for seller_id, grp in txn.groupby("seller_id"):
        assisted = grp[grp["agent_assist_type"] != "none"]
        gmv = float(grp["gmv_usd"].sum())
        assist_share = len(assisted) / max(1, len(grp))
        rev = float(assisted["platform_revenue_usd"].sum()) if not assisted.empty else 0.0
        cost = float(assisted["agent_inference_cost_usd"].sum()) if not assisted.empty else 0.0
        verified_rate = float(assisted["verified"].mean()) if not assisted.empty else 1.0
        rows.append({
            "seller_id": seller_id,
            "gmv_usd": round(gmv, 2),
            "assist_share": round(assist_share, 3),
            "net_margin": round(rev - cost, 2),
            "verified_rate": round(verified_rate, 3),
        })
    return pd.DataFrame(rows).sort_values("net_margin")


def marketplace_summary_chips(ws: Workspace) -> dict[str, float]:
    txn = _txn(ws)
    if txn.empty:
        return {"gmv_assisted": 0.0, "take_usd": 0.0, "inference_usd": 0.0, "net_margin_usd": 0.0, "margin_pct": 0.0}
    assisted = txn[txn["agent_assist_type"] != "none"]
    m = platform_margin_after_inference(ws)
    return {
        "gmv_assisted": float(assisted["gmv_usd"].sum()),
        "take_usd": m["revenue_usd"],
        "inference_usd": m["inference_usd"],
        "net_margin_usd": m["margin_usd"],
        "margin_pct": m["margin_pct"],
    }


def marketplace_margin_shock(ws: Workspace, shock_pct: float = 0.0) -> dict[str, Any]:
    """Recompute platform margin if inference costs rise by shock_pct."""
    txn = _txn(ws)
    if txn.empty:
        return {"net_margin_usd": 0.0, "delta_usd": 0.0, "margin_pct": 0.0}
    assisted = txn[txn["agent_assist_type"] != "none"].copy()
    if assisted.empty:
        return {"net_margin_usd": 0.0, "delta_usd": 0.0, "margin_pct": 0.0}
    base_rev = float(assisted["platform_revenue_usd"].sum())
    base_cost = float(assisted["agent_inference_cost_usd"].sum())
    shocked_cost = base_cost * (1 + shock_pct)
    net = base_rev - shocked_cost
    gmv = float(assisted["gmv_usd"].sum())
    base_net = base_rev - base_cost
    return {
        "net_margin_usd": round(net, 2),
        "delta_usd": round(net - base_net, 2),
        "margin_pct": round(net / max(gmv, 1), 4),
        "shock_pct": shock_pct,
    }
