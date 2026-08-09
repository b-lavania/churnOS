"""Churn taxonomy report — monthly reason codes + intervention stub."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.workspace import Workspace
from ontology.exception_taxonomy import CHURN_REASON_CODES

CHURN_CATS = list(CHURN_REASON_CODES) if CHURN_REASON_CODES else [
    "tourist", "value_failure", "efficiency", "price", "champion_departure", "displacement", "product_gap",
]


def churn_taxonomy_summary(
    workspace: Workspace,
    records: list[dict[str, Any]],
) -> pd.DataFrame:
    """Aggregate churn reason codes from account GDR exceptions."""
    accounts = getattr(workspace, "accounts", workspace.workspaces)
    churned_ids = set()
    if not workspace.seats.empty and "is_churned" in workspace.seats.columns:
        churned = workspace.seats[workspace.seats["is_churned"]]
        if "workspace_id" in churned.columns:
            churned_ids = set(churned["workspace_id"].unique())
        elif "account_id" in churned.columns:
            churned_ids = set(churned["account_id"].unique())

    rows = []
    for cat in CHURN_CATS:
        flagged = [r for r in records if r.get("subject", {}).get("entity_type") == "account"
                   and any(e.get("category") == cat for e in r.get("exceptions", []))]
        churned_flagged = [r for r in flagged if r.get("subject", {}).get("account_id") in churned_ids]
        intervened = [r for r in flagged if r.get("decision", {}).get("final_action") != r.get("decision", {}).get("recommended_action")]
        saved = [r for r in flagged if r.get("outcome") and not r.get("outcome", {}).get("churn_happened")]
        rows.append({
            "reason_code": cat,
            "flagged": len(flagged),
            "pct_of_churn": f"{len(churned_flagged) / max(len(churned_ids), 1) * 100:.0f}%",
            "intervened": len(intervened),
            "churned_despite": len([r for r in intervened if r.get("outcome", {}).get("churn_happened")]),
            "saved": len(saved),
        })
    return pd.DataFrame(rows)


def exception_counts_from_records(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rec in records:
        for exc in rec.get("exceptions", []):
            cat = exc.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
    return counts
