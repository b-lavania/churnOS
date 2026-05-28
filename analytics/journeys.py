"""
Event-first journey / funnel analytics (Heap-style retroactive steps).
"""

from __future__ import annotations

from typing import Sequence

import pandas as pd


DEFAULT_JOURNEY_STEPS = [
    "view_item",
    "add_to_cart",
    "purchase_complete",
]


def event_funnel(
    events: pd.DataFrame,
    steps: Sequence[str] | None = None,
    *,
    group_col: str | None = None,
) -> pd.DataFrame:
    """
    Compute step-through counts on product_events.

    A user counts at step k if they fired steps[0..k] in order (not necessarily consecutive rows).
    """
    steps = list(steps or DEFAULT_JOURNEY_STEPS)
    if not steps:
        return pd.DataFrame(columns=["step", "users", "conversion_rate", "drop_off_pct"])

    ev = events.copy()
    ev["event_ts"] = pd.to_datetime(ev["event_ts"])

    groups = [None] if group_col is None else ev[group_col].dropna().unique().tolist()
    rows = []

    for grp in groups:
        sub = ev if grp is None else ev[ev[group_col] == grp]
        cohort_users = sub["customer_id"].nunique()
        prev_count = cohort_users

        for i, step in enumerate(steps):
            users_at_step = (
                sub[sub["event_name"] == step]["customer_id"].nunique()
            )
            if i == 0:
                eligible = users_at_step
            else:
                prior_users = set(
                    sub[sub["event_name"].isin(steps[:i])]["customer_id"].unique()
                )
                step_users = set(sub[sub["event_name"] == step]["customer_id"].unique())
                eligible = len(prior_users & step_users)

            conv = eligible / cohort_users * 100 if cohort_users else 0
            drop = (1 - eligible / prev_count) * 100 if prev_count else 0
            rows.append(
                {
                    "step": step,
                    "users": int(eligible),
                    "conversion_rate": round(conv, 2),
                    "drop_off_pct": round(max(0, drop), 2),
                    "group": grp if grp is not None else "all",
                }
            )
            prev_count = eligible

    return pd.DataFrame(rows)
