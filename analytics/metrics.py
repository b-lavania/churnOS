"""
Governed metric catalog — single definitions for KPI tiles across pages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from analytics.conversion import funnel_summary
from analytics.product_metrics import (
    activation_and_ttf_metrics,
    cohort_signups_by_month,
    purchase_dau_over_wau_proxy,
    refund_exposure_rates,
    signup_momentum_latest_vs_prior_month,
)
from core.workspace import Workspace

_LEXICON_PATH = Path(__file__).parent.parent / "metrics" / "lexicon.yaml"


def load_lexicon() -> dict[str, Any]:
    if not _LEXICON_PATH.exists():
        return {"metrics": {}}
    with open(_LEXICON_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {"metrics": {}}


def _funnel_cvr(ws: Workspace) -> tuple[float, int, int]:
    summary = funnel_summary(ws.funnel)
    visits = int(summary.loc[summary["step"] == "Visit", "sessions"].iloc[0])
    purchases = int(summary.loc[summary["step"] == "Purchase", "sessions"].iloc[0])
    rate = purchases / visits * 100 if visits else 0.0
    return rate, visits, purchases


def resolve_metric(name: str, workspace: Workspace, *, registry: list | None = None) -> dict[str, Any]:
    """
    Return {name, label, value, display, definition, caveats, meta} for a catalog metric.
    """
    lex = load_lexicon().get("metrics", {})
    spec = lex.get(name, {})
    label = spec.get("label", name)
    caveats = spec.get("caveats", "")
    unit = spec.get("unit", "")

    value: Any = None
    display = "—"
    meta: dict[str, Any] = {}

    if name == "session_to_purchase_cvr":
        rate, visits, purchases = _funnel_cvr(workspace)
        value = rate
        display = f"{rate:.2f}%"
        meta = {"visits": visits, "purchases": purchases}

    elif name == "activated_within_7d":
        act = activation_and_ttf_metrics(workspace.customers, workspace.transactions)
        value = act.get("pct_first_order_within_7d")
        display = f"{value}%" if value is not None else "—"

    elif name == "activated_within_28d":
        act = activation_and_ttf_metrics(workspace.customers, workspace.transactions)
        value = act.get("pct_first_order_within_28d")
        display = f"{value}%" if value is not None else "—"

    elif name == "refund_rate_orders":
        ref = refund_exposure_rates(workspace.transactions)
        value = ref.get("refund_rate_all_orders_pct")
        display = f"{value}%" if value is not None and not pd.isna(value) else "—"

    elif name == "orders_per_active_buyer":
        act = activation_and_ttf_metrics(workspace.customers, workspace.transactions)
        monet = act.get("monetization", {})
        value = monet.get("orders_per_buyer")
        display = f"{value:.3f}" if value is not None else "—"

    elif name == "weekly_purchase_stickiness":
        stick = purchase_dau_over_wau_proxy(workspace.transactions)
        value = stick.get("mean_ratio")
        display = f"{value:.4f}" if value is not None else "—"
        meta = stick

    elif name == "signup_momentum_mom":
        cohorts = cohort_signups_by_month(workspace.customers)
        mom = signup_momentum_latest_vs_prior_month(cohorts)
        value = mom.get("delta_pct")
        display = f"{value:+.2f}%" if value is not None and not pd.isna(value) else "—"
        meta = mom

    elif name == "experiment_active_count":
        reg = registry or []
        value = sum(1 for e in reg if e.get("status") == "active")
        display = str(int(value))

    elif name == "north_star_activation_ratio":
        act = activation_and_ttf_metrics(workspace.customers, workspace.transactions)
        n = act.get("n_customers", 0) or 1
        activated = n - (act.get("pct_never_ordered", 0) / 100 * n)
        value = round(activated / n * 100, 2)
        display = f"{value:.1f}%"
        meta = {"activated_buyers_approx": int(activated), "signups": n}

    definition = spec.get("description") or label
    if spec.get("type") == "ratio":
        definition = f"{label}: purchases / visits (session grain)."

    return {
        "name": name,
        "label": label,
        "value": value,
        "display": display,
        "unit": unit,
        "definition": definition,
        "caveats": caveats,
        "meta": meta,
    }


def resolve_pinned_metrics(
    workspace: Workspace,
    names: list[str] | None = None,
    *,
    registry: list | None = None,
) -> list[dict[str, Any]]:
    """Default executive pins."""
    default_names = names or [
        "north_star_activation_ratio",
        "session_to_purchase_cvr",
        "refund_rate_orders",
        "experiment_active_count",
    ]
    return [resolve_metric(n, workspace, registry=registry) for n in default_names]
