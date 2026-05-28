"""
Unified product-analytics workspace: one seed, one event spine, experiment tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import numpy as np
import pandas as pd

from data.generator import (
    SEED,
    generate_all_data,
    generate_funnel_events,
)


@dataclass
class Workspace:
    """Container for all synthetic tables powering churnOS surfaces."""

    seed: int
    model_config: dict[str, Any]
    built_at: pd.Timestamp
    customers: pd.DataFrame
    transactions: pd.DataFrame
    product_events: pd.DataFrame
    funnel: pd.DataFrame
    marketplace: pd.DataFrame
    buyers: pd.DataFrame
    marketing: pd.DataFrame
    experiment_assignments: pd.DataFrame
    experiment_exposures: pd.DataFrame
    experiment_outcomes: pd.DataFrame
    default_experiment_id: str = "EXP-WORKSPACE-001"
    meta: dict[str, Any] = field(default_factory=dict)


def _assign_customers_to_experiment(
    customers: pd.DataFrame,
    experiment_id: str,
    seed: int,
    control_share: float = 0.5,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(customers)
    variants = rng.choice(
        ["control", "variant"],
        size=n,
        p=[control_share, 1.0 - control_share],
    )
    signup = pd.to_datetime(customers["signup_date"])
    offsets = rng.integers(0, 14, size=n)
    assigned_at = signup + pd.to_timedelta(offsets, unit="D")

    return pd.DataFrame(
        {
            "user_id": customers["customer_id"],
            "experiment_id": experiment_id,
            "variant": variants,
            "assigned_at": assigned_at,
        }
    )


def _tag_funnel_with_assignment(
    funnel: pd.DataFrame,
    assignments: pd.DataFrame,
    seed: int,
) -> pd.DataFrame:
    """Map session-level funnel rows to experiment variants via synthetic user linkage."""

    rng = np.random.default_rng(seed + 17)
    users = assignments[["user_id", "variant", "experiment_id", "assigned_at"]].copy()
    users = users.rename(columns={"assigned_at": "user_assigned_at"})

    sessions = funnel["session_id"].unique()
    session_users = pd.DataFrame(
        {
            "session_id": sessions,
            "user_id": rng.choice(users["user_id"].values, size=len(sessions)),
        }
    )

    tagged = funnel.merge(session_users, on="session_id", how="left")
    tagged = tagged.merge(users, on="user_id", how="left")
    tagged["session_ts"] = pd.to_datetime(tagged["timestamp"])
    tagged["is_post_assignment"] = tagged["session_ts"] >= tagged["user_assigned_at"]
    return tagged


def _build_exposure_and_outcomes(
    tagged_funnel: pd.DataFrame,
    experiment_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    exposed = tagged_funnel[tagged_funnel["is_post_assignment"].fillna(False)].copy()

    first_exp = (
        exposed.groupby(["user_id", "variant"], as_index=False)["session_ts"]
        .min()
        .rename(columns={"session_ts": "first_exposure_ts"})
    )
    first_exp["experiment_id"] = experiment_id

    purchase_sessions = exposed[exposed["funnel_step"] == "Purchase"]["session_id"].unique()

    session_variant = exposed.groupby("session_id")["variant"].first()

    outcomes_rows = []
    for variant in ("control", "variant"):
        v_sess = session_variant[session_variant == variant].index
        visitors = len(v_sess)
        conversions = len(set(v_sess) & set(purchase_sessions))
        outcomes_rows.append(
            {
                "experiment_id": experiment_id,
                "variant": variant,
                "visitors": int(visitors),
                "conversions": int(conversions),
                "conversion_rate_pct": round(conversions / visitors * 100, 3) if visitors else 0.0,
            }
        )

    outcomes = pd.DataFrame(outcomes_rows)
    return first_exp, outcomes


def build_workspace(
    model_config: dict[str, Any] | None = None,
    *,
    seed: int = SEED,
    n_sessions: int = 30_000,
    experiment_id: str = "EXP-WORKSPACE-001",
) -> Workspace:
    """
    Build a coherent synthetic warehouse for all analytics pages.

    Parameters
    ----------
    model_config : optional dict persisted from Business Model (stored for resync).
    seed : RNG seed shared across generators.
    n_sessions : funnel session volume (aligned with conversion page defaults).
    """
    bundle = generate_all_data(seed=seed)

    funnel = generate_funnel_events(n_sessions=n_sessions, seed=seed)

    customers = bundle["customers"]
    assignments = _assign_customers_to_experiment(customers, experiment_id, seed)
    tagged_funnel = _tag_funnel_with_assignment(funnel, assignments, seed)
    exposures, outcomes = _build_exposure_and_outcomes(tagged_funnel, experiment_id)

    return Workspace(
        seed=int(seed),
        model_config=dict(model_config or {}),
        built_at=pd.Timestamp.utcnow(),
        customers=customers,
        transactions=bundle["transactions"],
        product_events=bundle["product_events"],
        funnel=tagged_funnel,
        marketplace=bundle["marketplace"],
        buyers=bundle["buyers"],
        marketing=bundle["marketing"],
        experiment_assignments=assignments,
        experiment_exposures=exposures,
        experiment_outcomes=outcomes,
        default_experiment_id=experiment_id,
        meta={"n_sessions": n_sessions},
    )


def workspace_to_dict(ws: Workspace) -> dict[str, Any]:
    """Serialize workspace tables for Streamlit session_state (plain dict)."""
    return {
        "seed": ws.seed,
        "model_config": ws.model_config,
        "built_at": ws.built_at.isoformat(),
        "customers": ws.customers,
        "transactions": ws.transactions,
        "product_events": ws.product_events,
        "funnel": ws.funnel,
        "marketplace": ws.marketplace,
        "buyers": ws.buyers,
        "marketing": ws.marketing,
        "experiment_assignments": ws.experiment_assignments,
        "experiment_exposures": ws.experiment_exposures,
        "experiment_outcomes": ws.experiment_outcomes,
        "default_experiment_id": ws.default_experiment_id,
        "meta": ws.meta,
    }


def workspace_from_dict(data: dict[str, Any]) -> Workspace:
    return Workspace(
        seed=int(data["seed"]),
        model_config=data.get("model_config", {}),
        built_at=pd.Timestamp(data.get("built_at", pd.Timestamp.utcnow().isoformat())),
        customers=data["customers"],
        transactions=data["transactions"],
        product_events=data["product_events"],
        funnel=data["funnel"],
        marketplace=data["marketplace"],
        buyers=data["buyers"],
        marketing=data["marketing"],
        experiment_assignments=data["experiment_assignments"],
        experiment_exposures=data["experiment_exposures"],
        experiment_outcomes=data["experiment_outcomes"],
        default_experiment_id=data.get("default_experiment_id", "EXP-WORKSPACE-001"),
        meta=data.get("meta", {}),
    )


def get_workspace_from_session(session_state: Any) -> Workspace | None:
    raw = session_state.get("workspace")
    if raw is None:
        return None
    if isinstance(raw, Workspace):
        return raw
    return workspace_from_dict(raw)


def sync_workspace_to_session(session_state: Any, ws: Workspace) -> None:
    session_state["workspace"] = workspace_to_dict(ws)
    session_state["workspace_seed"] = ws.seed
