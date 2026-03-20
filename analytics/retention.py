"""
Retention analytics — cohort retention matrix, CLV, and retention curves.
"""

import numpy as np
import pandas as pd


# Data schema version - bump when changing expected columns
DATA_VERSION = "1.0"


def _validate_txn_columns(transactions: pd.DataFrame) -> None:
    """Validate that transactions DataFrame has required columns."""
    required = {"gross_margin", "gross_revenue", "transaction_id", "customer_id"}
    missing = required - set(transactions.columns)
    if missing:
        raise KeyError(
            f"Missing required columns in transactions: {sorted(missing)}. "
            f"Available columns: {sorted(transactions.columns)}. "
            f"Please refresh the page to regenerate data with the correct schema."
        )


def cohort_retention_matrix(transactions: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """
    Build a cohort retention triangle.
    
    Rows = signup cohort month, Columns = period index (0, 1, 2, …),
    Values = percentage of cohort still active in that period.
    """
    txns = transactions.merge(
        customers[["customer_id", "signup_date"]], on="customer_id", how="left"
    )
    txns["signup_cohort"] = txns["signup_date"].dt.to_period("M")
    txns["txn_period"] = txns["date"].dt.to_period("M")
    txns["period_index"] = (
        txns["txn_period"].astype("int64") - txns["signup_cohort"].astype("int64")
    )
    # Remove negative periods (shouldn't happen with clean data)
    txns = txns[txns["period_index"] >= 0]

    # Count unique customers per cohort-period
    cohort_data = txns.groupby(["signup_cohort", "period_index"])["customer_id"].nunique().reset_index()
    cohort_data.columns = ["signup_cohort", "period_index", "customers"]

    cohort_sizes = cohort_data[cohort_data["period_index"] == 0].set_index("signup_cohort")["customers"]

    retention = cohort_data.pivot(index="signup_cohort", columns="period_index", values="customers")
    retention = retention.divide(cohort_sizes, axis=0) * 100

    # Limit to first 12 periods for readability
    cols = [c for c in retention.columns if c <= 12]
    retention = retention[cols]
    retention.index = retention.index.astype(str)
    retention.columns = [f"M{int(c)}" for c in retention.columns]
    
    return retention.round(1)


def clv_estimate(customers: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate Customer Lifetime Value using:
    CLV = Avg Order Value × Purchase Frequency × Avg Customer Lifespan (months)
    
    Returns a DataFrame with per-customer CLV.
    """
    _validate_txn_columns(transactions)
    
    reference_date = pd.Timestamp("2025-12-31")
    
    txn_stats = transactions.groupby("customer_id").agg(
        total_margin=("gross_margin", "sum"),
        num_orders=("transaction_id", "count"),
        avg_order_value=("gross_revenue", "mean"),
        avg_margin=("gross_margin", "mean"),
    ).reset_index()

    cust = customers.merge(txn_stats, on="customer_id", how="left")
    
    # Lifespan in months
    end_date = cust["churn_date"].fillna(reference_date)
    cust["lifespan_months"] = ((end_date - cust["signup_date"]).dt.days / 30.44).round(1)
    cust["lifespan_months"] = cust["lifespan_months"].clip(lower=1)

    # Monthly purchase frequency
    cust["monthly_frequency"] = (cust["num_orders"] / cust["lifespan_months"]).round(2)

    # True Margin CLV
    cust["clv"] = (cust["avg_margin"] * cust["monthly_frequency"] * cust["lifespan_months"]).round(2)
    
    return cust[["customer_id", "segment", "acquisition_channel", "avg_order_value",
                 "monthly_frequency", "lifespan_months", "clv", "avg_margin"]]


def retention_curve(customers: pd.DataFrame, transactions: pd.DataFrame, by: str = "acquisition_channel") -> pd.DataFrame:
    """
    Compute retention percentage at each month interval, grouped by a dimension.
    Returns a long-form DataFrame: group, month, retention_pct
    """
    reference_date = pd.Timestamp("2025-12-31")
    txns = transactions.merge(
        customers[["customer_id", "signup_date", by]], on="customer_id", how="left"
    )
    txns["months_since_signup"] = (
        (txns["date"] - txns["signup_date"]).dt.days / 30.44
    ).astype(int)
    txns = txns[txns["months_since_signup"] >= 0]

    # Count unique customers per group per month bucket
    activity = txns.groupby([by, "months_since_signup"])["customer_id"].nunique().reset_index()
    activity.columns = [by, "month", "active_customers"]

    # Cohort size per group
    cohort_sizes = customers.groupby(by)["customer_id"].nunique().reset_index()
    cohort_sizes.columns = [by, "cohort_size"]

    merged = activity.merge(cohort_sizes, on=by)
    merged["retention_pct"] = (merged["active_customers"] / merged["cohort_size"] * 100).round(1)

    # Limit to 12 months
    merged = merged[merged["month"] <= 12]
    return merged


def day_n_retention(customers: pd.DataFrame, transactions: pd.DataFrame, days: list = None) -> pd.DataFrame:
    """
    Compute Day-N retention (e.g. D1, D7, D30, D90).
    Returns DataFrame with day and retention percentage.
    """
    if days is None:
        days = [1, 7, 14, 30, 60, 90]
    
    txns = transactions.merge(
        customers[["customer_id", "signup_date"]], on="customer_id", how="left"
    )
    txns["days_since_signup"] = (txns["date"] - txns["signup_date"]).dt.days
    
    total_customers = customers["customer_id"].nunique()
    
    results = []
    for d in days:
        active = txns[txns["days_since_signup"] >= d]["customer_id"].nunique()
        results.append({
            "day": f"D{d}",
            "retained_customers": active,
            "retention_pct": round(active / total_customers * 100, 1),
        })
    
    return pd.DataFrame(results)
