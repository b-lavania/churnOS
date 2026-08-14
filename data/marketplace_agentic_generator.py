"""Synthetic agent-assisted marketplace transactions from agentic warehouse."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

ASSIST_TYPES = [
    "quote_generated",
    "listing_optimized",
    "checkout_completed",
    "negotiation_assisted",
    "none",
]


def generate_agent_transactions(
    runs: pd.DataFrame,
    seats: pd.DataFrame,
    capabilities: pd.DataFrame,
    profile: dict[str, Any],
    *,
    seed: int = 42,
) -> pd.DataFrame:
    """Build agent_transactions from priced runs + seats."""
    priors = profile.get("priors", {})
    assist_share = float(priors.get("agent_assist_share", 0.45))
    take_rate = float(priors.get("take_rate", 0.12))
    verification_rate = float(priors.get("verification_rate", 0.75))
    rng = np.random.default_rng(seed)

    cols = [
        "transaction_id", "occurred_at", "seller_id", "buyer_id",
        "capability_id", "agent_run_id", "gmv_usd", "take_rate",
        "platform_revenue_usd", "agent_inference_cost_usd",
        "agent_assist_type", "verified", "verified_by", "success",
    ]
    if runs.empty or seats.empty:
        return pd.DataFrame(columns=cols)

    ws_ids = seats["workspace_id"].unique().tolist()
    if len(ws_ids) < 2:
        ws_ids = ws_ids * 2

    cap_ids = capabilities["capability_id"].tolist() if not capabilities.empty else ["CAP-001"]
    negative_caps = set(rng.choice(cap_ids, size=min(2, len(cap_ids)), replace=False))

    run_cost_map = (
        runs.set_index("run_id")["run_cost_usd"].to_dict()
        if "run_cost_usd" in runs.columns
        else {}
    )
    ok_runs = runs[runs["success"].astype(bool)] if "success" in runs.columns else runs

    n_txn = max(80, len(ok_runs) // 3)
    rows: list[dict[str, Any]] = []
    planted_negative: list[str] = []

    for i in range(n_txn):
        assisted = rng.random() < assist_share
        cap_id = str(rng.choice(cap_ids))
        assist_type = str(rng.choice(ASSIST_TYPES[:-1])) if assisted else "none"
        gmv = float(rng.uniform(50, 500))
        rev = gmv * take_rate

        run_id = None
        inference = 0.0
        if assisted and not ok_runs.empty:
            sub = ok_runs[ok_runs["capability_id"] == cap_id] if "capability_id" in ok_runs.columns else ok_runs
            if sub.empty:
                sub = ok_runs
            pick = sub.iloc[int(rng.integers(0, len(sub)))]
            run_id = pick.get("run_id")
            inference = float(run_cost_map.get(run_id, priors.get("run_cost_per_success", 0.5)))

        if cap_id in negative_caps and assisted:
            inference = rev * float(rng.uniform(1.1, 1.8))
            planted_negative.append(cap_id)

        verified = bool(rng.random() < verification_rate) if assisted else True
        verified_by = "deterministic" if verified else "none"
        if assisted and verified:
            verified_by = str(rng.choice(["deterministic", "webhook", "llm_judge"]))
        success = assisted and (verified or rng.random() < 0.85)
        if assisted and not verified and rng.random() < 0.3:
            success = True  # verification gap

        seller_id = str(rng.choice(ws_ids))
        buyer_id = str(rng.choice([w for w in ws_ids if w != seller_id] or ws_ids))
        ts = pd.Timestamp("2025-06-01") + pd.Timedelta(days=int(rng.integers(0, 180)))

        rows.append({
            "transaction_id": f"TXN-{i:06d}",
            "occurred_at": ts,
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "capability_id": cap_id if assisted else None,
            "agent_run_id": run_id,
            "gmv_usd": round(gmv, 2),
            "take_rate": take_rate,
            "platform_revenue_usd": round(rev, 2),
            "agent_inference_cost_usd": round(inference, 2),
            "agent_assist_type": assist_type,
            "verified": verified,
            "verified_by": verified_by,
            "success": success,
        })

    df = pd.DataFrame(rows)
    from data.ground_truth import get, register

    gt = get(seed)
    if gt is not None:
        gt.planted_take_rate = take_rate
        gt.planted_assist_share = assist_share
        gt.planted_negative_margin_workflows = list(set(planted_negative))
        if len(df):
            gap = df[df["agent_assist_type"] != "none"]
            gt.planted_verification_gap_rate = float((gap["success"] & ~gap["verified"]).mean()) if len(gap) else 0.0
        register(gt)

    return df
