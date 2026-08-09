"""
Probabilistic CLV (BG/NBD + Gamma-Gamma) for legacy e-commerce customers.
Not used for agentic account retention — see analytics/survival.py.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _validate_txn(transactions: pd.DataFrame) -> None:
    for col in ("customer_id", "date", "gross_revenue"):
        if col not in transactions.columns:
            raise ValueError(f"transactions missing {col}")


def bg_nbd_clv(
    customers: pd.DataFrame,
    transactions: pd.DataFrame,
    *,
    horizon_months: int = 12,
    discount_rate: float = 0.01,
) -> pd.DataFrame:
    """
    Teaching BG/NBD-style CLV on legacy transaction data.

    Uses simplified moment-matching estimators (Fader-Hardie teaching approximation).
    """
    _validate_txn(transactions)
    ref = pd.Timestamp("2025-12-31")
    tx = transactions.copy()
    tx["date"] = pd.to_datetime(tx["date"])

    freq = tx.groupby("customer_id").agg(
        n_orders=("customer_id", "count"),
        last_purchase=("date", "max"),
        monetary=("gross_revenue", "mean"),
    ).reset_index()

    cust = customers.merge(freq, on="customer_id", how="left")
    cust["n_orders"] = cust["n_orders"].fillna(0)
    cust["monetary"] = cust["monetary"].fillna(0)
    cust["last_purchase"] = pd.to_datetime(cust["last_purchase"])
    cust["signup_date"] = pd.to_datetime(cust["signup_date"])
    cust["T"] = ((ref - cust["signup_date"]).dt.days / 30.44).clip(lower=1)
    cust["recency"] = ((ref - cust["last_purchase"]).dt.days / 30.44).fillna(cust["T"])

    # Teaching: expected future transactions ∝ (n/T) * horizon * exp(-recency/T)
    cust["purchase_rate"] = cust["n_orders"] / cust["T"]
    cust["expected_future_orders"] = (
        cust["purchase_rate"] * horizon_months * np.exp(-cust["recency"] / cust["T"].clip(lower=1))
    ).clip(lower=0)
    discount = sum(1 / (1 + discount_rate) ** m for m in range(1, horizon_months + 1))
    cust["clv_probabilistic"] = (cust["expected_future_orders"] * cust["monetary"] * discount / horizon_months).round(2)

    return cust[["customer_id", "segment", "n_orders", "purchase_rate", "expected_future_orders", "clv_probabilistic"]]


def clv_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or "clv_probabilistic" not in df.columns:
        return {"mean_clv": 0.0, "median_clv": 0.0, "n": 0}
    return {
        "mean_clv": round(float(df["clv_probabilistic"].mean()), 2),
        "median_clv": round(float(df["clv_probabilistic"].median()), 2),
        "n": len(df),
    }
