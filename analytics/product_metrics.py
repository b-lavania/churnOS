"""
Product lifecycle & engagement proxies built from transactional data.

These metrics are intentional *proxies*: purchase timestamps differ from authenticated product DAU/WAU from
instrumentation. Each exported helper names outputs honestly.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

import numpy as np
import pandas as pd

_CUSTOMER_CORE = frozenset({"customer_id", "signup_date"})
_TXN_CORE = frozenset({"customer_id", "date"})
_EVENT_CORE = frozenset({"customer_id", "event_ts", "event_name"})


def _ensure_cols(df: pd.DataFrame, required: Iterable[str], name: str) -> None:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise KeyError(f"{name} missing columns: {missing}")


def cohort_signups_by_month(customers: pd.DataFrame) -> pd.DataFrame:
    """Count new signups per calendar cohort month."""
    _ensure_cols(customers, _CUSTOMER_CORE, "customers")
    c = customers.copy()
    c["signup_dt"] = pd.to_datetime(c["signup_date"]).dt.normalize()
    c["cohort_month"] = c["signup_dt"].dt.to_period("M").astype(str)
    return (
        c.groupby("cohort_month").size().reset_index(name="signups").sort_values("cohort_month")
    )


def signup_momentum_latest_vs_prior_month(cohort_signups: pd.DataFrame) -> dict[str, Any]:
    """Momentum using the last two chronological cohort months in the table."""

    if cohort_signups.empty:
        return {"delta_pct": np.nan, "notes": "no cohort data"}

    ds = cohort_signups.sort_values("cohort_month")
    tail = ds.tail(2).reset_index(drop=True)
    if len(tail) < 2:
        return {
            "delta_pct": np.nan,
            "latest_month": tail.iloc[-1]["cohort_month"],
            "notes": "need two cohort months",
        }

    latest = int(tail.iloc[-1]["signups"])
    prior = int(tail.iloc[-2]["signups"])
    delta_pct = (latest - prior) / prior * 100.0 if prior else np.nan

    return {
        "delta_pct": round(float(delta_pct), 2) if not np.isnan(delta_pct) else np.nan,
        "latest_month": tail.iloc[-1]["cohort_month"],
        "prior_month": tail.iloc[-2]["cohort_month"],
        "latest_signups": latest,
        "prior_signups": prior,
        "notes": "month‑over‑month on signup cohort buckets (synthetic cadence)",
    }


def activation_and_ttf_metrics(
    customers: pd.DataFrame,
    transactions: pd.DataFrame,
    *,
    activation_windows_days: tuple[int, ...] = (7, 14, 28),
    min_net_revenue_for_order: float = 0.0,
) -> dict[str, Any]:
    """
    Activation = first qualifying order within N calendar days since signup.

    Rows with ``net_revenue`` at or below ``min_net_revenue_for_order`` (e.g. stockouts)
    never count toward first / second orders.
    """
    _ensure_cols(customers, _CUSTOMER_CORE, "customers")
    _ensure_cols(transactions, _TXN_CORE, "transactions")

    txn = transactions.copy()
    txn["date"] = pd.to_datetime(txn["date"]).dt.normalize()
    cust = customers[["customer_id", "signup_date"]].copy()
    cust["signup_date"] = pd.to_datetime(cust["signup_date"]).dt.normalize()

    if "net_revenue" not in txn.columns:
        txn["_qual"] = True
    else:
        txn["_qual"] = txn["net_revenue"].fillna(0) > float(min_net_revenue_for_order)

    sub = txn[txn["_qual"]].sort_values(["customer_id", "date"])

    first_txn = sub.groupby("customer_id")["date"].min().reset_index().rename(columns={"date": "first_order_date"})

    merged = cust.merge(first_txn, on="customer_id", how="left")

    merged["days_to_first_purchase"] = (merged["first_order_date"] - merged["signup_date"]).dt.days

    deltas_to_second: list[float] = []

    signup_lookup = merged.set_index("customer_id")["signup_date"]

    for cid, grp in sub.groupby("customer_id"):
        dates_sorted = pd.Series(grp["date"].unique()).sort_values()
        if len(dates_sorted) < 2 or cid not in signup_lookup.index:

            continue

        deltas_to_second.append(float((dates_sorted.iloc[1] - signup_lookup.loc[cid]).days))

    n = len(merged)
    activation_rates = {}
    for w in activation_windows_days:
        mask = merged["days_to_first_purchase"].notna() & (merged["days_to_first_purchase"] <= int(w))
        activation_rates[f"pct_first_order_within_{w}d"] = round(mask.sum() / n * 100, 2) if n else 0.0

    ttf = merged["days_to_first_purchase"].dropna()

    mop = monetization_orders_per_buyer(txn, merged["customer_id"])

    median_tts = (
        float(round(float(np.nanmedian(np.array(deltas_to_second))), 1)) if deltas_to_second else None
    )

    return {
        "n_customers": n,
        **activation_rates,
        "median_days_to_first_purchase": float(round(ttf.median(), 2)) if not ttf.empty else None,
        "median_days_to_second_order_from_signup": median_tts,
        "pct_never_ordered": round((merged["first_order_date"].isna()).sum() / n * 100, 2) if n else 0.0,
        "monetization": mop,
    }


def monetization_orders_per_buyer(transactions: pd.DataFrame, customer_subset: Iterable[str]) -> dict[str, float]:
    txn = transactions[transactions["customer_id"].isin(customer_subset)].copy()
    if txn.empty:
        return {"orders_per_buyer": 0.0, "pct_orders_discounted": 0.0, "margin_over_revenue_pct": None}

    grp = txn.groupby("customer_id").size()
    pct_disc = float(txn["discount_applied"].mean() * 100) if "discount_applied" in txn.columns else 0.0
    margin_pct: float | None = None

    nr_col = txn.get("net_revenue")

    gm_col = txn.get("gross_margin")

    gr_col = txn.get("gross_revenue")

    if gm_col is not None and nr_col is not None:
        denom = nr_col.fillna(gr_col.fillna(0))

        denom = denom.replace({0: np.nan})

        if denom.sum(skipna=True) != 0 and not denom.isna().all():

            total_gm = gm_col.fillna(0).sum()

            denom_sum = denom.sum(skipna=True)

            margin_pct = round(float(total_gm / denom_sum) * 100, 2) if denom_sum else None

    return {
        "orders_per_buyer": float(round(float(grp.mean()), 4)),
        "pct_orders_discounted": round(float(pct_disc), 2),
        "margin_over_revenue_pct": margin_pct,
    }


def inter_purchase_gap_distribution(transactions: pd.DataFrame) -> dict[str, float | int | None]:
    _ensure_cols(transactions, _TXN_CORE, "transactions")

    txn = transactions.copy()

    txn["date"] = pd.to_datetime(txn["date"])

    gaps: list[float] = []

    for _, grp in txn.groupby("customer_id")["date"]:

        d = grp.sort_values().diff().dropna().dt.days.values.astype(float)

        gaps.extend(float(x) for x in d)

    if not gaps:

        return {"median_gap_days": None, "q25_gap_days": None, "q75_gap_days": None, "n_gaps": 0}

    arr = np.array(gaps, dtype=float)

    return {

        "median_gap_days": float(round(np.percentile(arr, 50), 2)),

        "q25_gap_days": float(round(np.percentile(arr, 25), 2)),

        "q75_gap_days": float(round(np.percentile(arr, 75), 2)),

        "n_gaps": int(arr.size),

    }


def purchase_dau_over_wau_proxy(transactions: pd.DataFrame) -> dict[str, Any]:
    """

    Mean over ISO weeks of (mean daily unique purchasers) / (weekly unique purchasers).


    Proxies habitual repeat purchase within-week concentration.

    """

    _ensure_cols(transactions, _TXN_CORE, "transactions")

    txn = transactions.copy()

    txn["dt"] = pd.to_datetime(txn["date"]).dt.normalize()

    txn["iso_year"] = txn["dt"].dt.isocalendar().year.astype(int)

    txn["iso_week"] = txn["dt"].dt.isocalendar().week.astype(int)

    ratios: list[float] = []

    for (_, _), grp in txn.groupby(["iso_year", "iso_week"]):

        daily = grp.groupby("dt")["customer_id"].nunique()

        if daily.empty:

            continue

        wau = grp["customer_id"].nunique()

        if not wau:

            continue

        ratios.append(float(daily.mean()) / float(wau))

    if not ratios:

        return {"mean_ratio": None, "weeks_observed": 0, "definition": "purchase‑based analogue of DAU/WAU"}

    return {

        "mean_ratio": float(round(float(np.mean(ratios)), 4)),

        "weeks_observed": len(ratios),

        "definition": "(mean daily unique purchasers in ISO week) / (weekly unique purchasers)",

    }


def refund_exposure_rates(transactions: pd.DataFrame) -> dict[str, float]:

    if "is_refunded" not in transactions.columns:

        return {"refund_rate_all_orders_pct": np.nan}

    txn = transactions

    rr = txn["is_refunded"].astype(bool).mean() * 100

    out: dict[str, float] = {"refund_rate_all_orders_pct": round(float(rr), 2)}

    if "discount_applied" in txn.columns:

        sub = txn[txn["discount_applied"].fillna(False)]

        if len(sub):

            rr_d = sub["is_refunded"].astype(bool).mean() * 100

            out["refund_rate_discounted_orders_pct"] = round(float(rr_d), 2)

        else:

            out["refund_rate_discounted_orders_pct"] = np.nan

    else:

        out["refund_rate_discounted_orders_pct"] = np.nan

    return out


def conversion_lift_orders_margin(
    baseline_cvr_pct: float,

    relative_lift_pct: float,

    *,

    baseline_sessions: int,

    margin_per_incremental_buyer_monthly: float,

    buyer_clv_24: float,

) -> dict[str, Any]:

    dc = baseline_cvr_pct / 100.0

    new_c = dc * (1 + relative_lift_pct / 100.0)

    add_buyers_via_sessions = float(baseline_sessions) * (new_c - dc)

    ratio_metric_notes = (
        "Session CVR ignores visit frequency changes. Prefer buyer‑level KPIs when those move. "
        "Novelty & learning effects shrink real‑world uplift."
    )

    return {

        "delta_additional_session_buyers_approx": round(float(add_buyers_via_sessions), 4),

        "estimated_monthly_margin_gain_usd": round(float(add_buyers_via_sessions * margin_per_incremental_buyer_monthly), 2),

        "estimated_total_clv_gain_24m_usd": round(float(add_buyers_via_sessions * buyer_clv_24), 2),

        "absolute_cvr_lift_points": round(float((new_c - dc) * 100), 4),

        "ratio_metric_notes": ratio_metric_notes,

    }


def sessionize_product_events(events: pd.DataFrame, gap_minutes: int = 30) -> pd.DataFrame:

    _ensure_cols(events, _EVENT_CORE, "product_events")

    evt = events.copy()

    evt["event_ts"] = pd.to_datetime(evt["event_ts"])

    evt.sort_values(["customer_id", "event_ts"], kind="mergesort", inplace=True)

    gap = pd.Timedelta(minutes=int(gap_minutes))

    ordinal: dict[Any, int] = defaultdict(int)

    last_ts_by_customer: dict[Any, pd.Timestamp] = {}

    sess_ids = []

    for row in evt.itertuples(index=False):

        cid = row.customer_id

        ts = pd.Timestamp(row.event_ts)

        if cid not in last_ts_by_customer:

            ordinal[cid] += 1

        else:

            prev = last_ts_by_customer[cid]

            if ts - prev > gap:

                ordinal[cid] += 1

        last_ts_by_customer[cid] = ts

        sess_ids.append(_format_session(cid, ordinal[cid]))

    out = evt.reset_index(drop=True)

    out["session_id"] = sess_ids

    return out


def _format_session(customer_id: Any, ordinal: int) -> str:

    return f"{customer_id}|sess{ordinal:05d}"


def cohort_event_adoption(
    customers: pd.DataFrame,

    events: pd.DataFrame,

    *,

    event_name: str,

    within_days_since_signup: int = 30,

) -> pd.DataFrame:

    _ensure_cols(customers, _CUSTOMER_CORE, "customers")

    _ensure_cols(events, _EVENT_CORE, "product_events")

    c = customers.copy()

    c["signup_dt"] = pd.to_datetime(c["signup_date"])

    cohort_col = "_cohort_month"

    c[cohort_col] = c["signup_dt"].dt.to_period("M").astype(str)

    cohort_size = (

        c.groupby(cohort_col)["customer_id"].nunique().reset_index(name="cohort_buyers")

    )

    ev = events[events["event_name"] == event_name][["customer_id", "event_ts"]].copy()

    ev["event_ts"] = pd.to_datetime(ev["event_ts"])

    m = ev.merge(c[["customer_id", "signup_dt", cohort_col]], on="customer_id", how="inner")

    eligible = (m["event_ts"] - m["signup_dt"]).dt.days.between(0, int(within_days_since_signup))

    adopted = (
        m[eligible]

        .drop_duplicates(["customer_id", cohort_col])

        .groupby(cohort_col)["customer_id"]

        .count()

        .reset_index(name="activated_customers")

    )

    merged = cohort_size.merge(adopted, on=cohort_col, how="left").fillna(0.0)

    merged["activated_customers"] = merged["activated_customers"].astype(int)

    merged["pct_activated_within_window"] = (

        (merged["activated_customers"] / merged["cohort_buyers"]).replace(np.inf, 0).fillna(0) * 100

    ).round(2)

    merged.rename(columns={cohort_col: "signup_cohort_month", "activated_customers": "buyers_who_fired_event"}, inplace=True)

    merged["within_days_since_signup"] = int(within_days_since_signup)

    merged["event_name"] = event_name

    return merged
