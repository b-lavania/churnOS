"""
Conversion funnel analytics : funnel summary, drop-off analysis, segment breakdowns, A/B testing.
"""

import numpy as np
import pandas as pd
from scipy import stats


FUNNEL_ORDER = ["Visit", "Product View", "Add to Cart", "Checkout", "Purchase"]


def funnel_summary(funnel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute conversion funnel summary with counts, conversion rate, and drop-off at each step.
    """
    totals = funnel_df.groupby("funnel_step")["session_id"].nunique().reindex(FUNNEL_ORDER).fillna(0).astype(int)
    
    df = pd.DataFrame({
        "step": FUNNEL_ORDER,
        "sessions": totals.values,
    })
    df["conversion_rate"] = (df["sessions"] / df["sessions"].iloc[0] * 100).round(2)
    df["drop_off"] = df["sessions"].diff().fillna(0).astype(int)
    df["drop_off_pct"] = 0.0
    for i in range(1, len(df)):
        if df.loc[i - 1, "sessions"] > 0:
            df.loc[i, "drop_off_pct"] = round(
                (1 - df.loc[i, "sessions"] / df.loc[i - 1, "sessions"]) * 100, 2
            )
    
    return df


def drop_off_analysis(funnel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify the biggest drop-off points in the funnel.
    Returns sorted by drop_off_pct descending.
    """
    summary = funnel_summary(funnel_df)
    return summary[summary["drop_off_pct"] > 0].sort_values("drop_off_pct", ascending=False).reset_index(drop=True)


def segment_conversion(funnel_df: pd.DataFrame, by: str = "device") -> pd.DataFrame:
    """
    Compute funnel conversion rate broken down by a dimension (device, source).
    Returns purchase conversion rate for each segment.
    """
    total_sessions = funnel_df.groupby(by)["session_id"].nunique().reset_index()
    total_sessions.columns = [by, "total_sessions"]
    
    purchases = funnel_df[funnel_df["funnel_step"] == "Purchase"].groupby(by)["session_id"].nunique().reset_index()
    purchases.columns = [by, "purchases"]
    
    merged = total_sessions.merge(purchases, on=by, how="left").fillna(0)
    merged["purchases"] = merged["purchases"].astype(int)
    merged["conversion_rate"] = (merged["purchases"] / merged["total_sessions"] * 100).round(2)
    
    return merged.sort_values("conversion_rate", ascending=False).reset_index(drop=True)


def ab_test_significance(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    confidence_level: float = 0.95,
) -> dict:
    """
    Perform a two-proportion Z-test for A/B test significance.
    
    Returns dict with:
        - control_rate, variant_rate
        - lift (% improvement)
        - z_score, p_value
        - is_significant
        - confidence_interval for the lift
    """
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    
    lift = (p2 - p1) / p1 * 100 if p1 > 0 else 0
    
    # Pooled proportion
    p_pool = (control_conversions + variant_conversions) / (control_visitors + variant_visitors)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / control_visitors + 1 / variant_visitors))
    
    z_score = (p2 - p1) / se if se > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    alpha = 1 - confidence_level
    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_lower = (p2 - p1) - z_crit * se
    ci_upper = (p2 - p1) + z_crit * se
    
    return {
        "control_rate": round(p1 * 100, 3),
        "variant_rate": round(p2 * 100, 3),
        "lift_pct": round(lift, 2),
        "z_score": round(z_score, 4),
        "p_value": round(p_value, 6),
        "is_significant": p_value < alpha,
        "confidence_interval": (round(ci_lower * 100, 3), round(ci_upper * 100, 3)),
        "confidence_level": confidence_level,
    }
