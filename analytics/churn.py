"""
Churn analysis module : churn rates, survival analysis, and churn driver identification.
"""

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


def compute_churn_rate(customers: pd.DataFrame, by: str = None) -> pd.DataFrame:
    """
    Compute overall or grouped churn rate.
    
    Args:
        customers: DataFrame with 'is_churned' column
        by: Optional column name to group by (e.g. 'segment', 'acquisition_channel')
    
    Returns:
        DataFrame with total_customers, churned, churn_rate columns
    """
    if by:
        grouped = customers.groupby(by).agg(
            total_customers=("customer_id", "count"),
            churned=("is_churned", "sum"),
        ).reset_index()
    else:
        grouped = pd.DataFrame([{
            "group": "Overall",
            "total_customers": len(customers),
            "churned": customers["is_churned"].sum(),
        }])
    
    grouped["churn_rate"] = (grouped["churned"] / grouped["total_customers"] * 100).round(2)
    return grouped


def compute_cohort_churn(customers: pd.DataFrame) -> pd.DataFrame:
    """Compute churn rate by signup month cohort."""
    customers = customers.copy()
    customers["cohort"] = customers["signup_date"].dt.to_period("M").astype(str)
    return compute_churn_rate(customers, by="cohort")


def revenue_vs_logo_churn(customers: pd.DataFrame) -> dict:
    """
    Compare logo churn (customer count) vs revenue churn (monthly spend lost).
    
    Returns dict with logo_churn_rate, revenue_churn_rate, and the gap.
    """
    total_customers = len(customers)
    churned_customers = customers["is_churned"].sum()
    logo_churn = churned_customers / total_customers * 100

    total_revenue = customers["monthly_spend"].sum()
    churned_revenue = customers.loc[customers["is_churned"], "monthly_spend"].sum()
    revenue_churn = churned_revenue / total_revenue * 100

    return {
        "logo_churn_rate": round(logo_churn, 2),
        "revenue_churn_rate": round(revenue_churn, 2),
        "gap": round(revenue_churn - logo_churn, 2),
    }


def churn_drivers(customers: pd.DataFrame) -> pd.DataFrame:
    """
    Identify top churn drivers using a Random Forest classifier.
    
    Returns DataFrame with feature names and importances, sorted descending.
    """
    df = customers.copy()
    
    feature_cols = ["monthly_spend"]
    le_segment = LabelEncoder()
    le_channel = LabelEncoder()
    df["segment_enc"] = le_segment.fit_transform(df["segment"])
    df["channel_enc"] = le_channel.fit_transform(df["acquisition_channel"])
    feature_cols += ["segment_enc", "channel_enc"]
    
    # Add tenure in days
    reference_date = pd.Timestamp("2025-12-31")
    df["tenure_days"] = (
        df["churn_date"].fillna(reference_date) - df["signup_date"]
    ).dt.days
    feature_cols.append("tenure_days")

    X = df[feature_cols].values
    y = df["is_churned"].astype(int).values

    clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=6)
    clf.fit(X, y)

    importances = pd.DataFrame({
        "feature": ["Monthly Spend", "Segment", "Acquisition Channel", "Tenure (days)"],
        "importance": clf.feature_importances_,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    return importances


def survival_analysis(customers: pd.DataFrame) -> dict:
    """
    Perform Kaplan-Meier survival analysis.
    
    Returns:
        dict with 'overall' KaplanMeierFitter and 'by_segment' dict of fitters
    """
    df = customers.copy()
    reference_date = pd.Timestamp("2025-12-31")
    df["duration"] = (df["churn_date"].fillna(reference_date) - df["signup_date"]).dt.days
    df["observed"] = df["is_churned"].astype(int)

    # Overall
    kmf_overall = KaplanMeierFitter()
    kmf_overall.fit(df["duration"], event_observed=df["observed"], label="Overall")

    # By segment
    by_segment = {}
    for seg in df["segment"].unique():
        mask = df["segment"] == seg
        kmf = KaplanMeierFitter()
        kmf.fit(df.loc[mask, "duration"], event_observed=df.loc[mask, "observed"], label=seg)
        by_segment[seg] = kmf

    return {"overall": kmf_overall, "by_segment": by_segment}
