"""
Marketplace analytics — Overall, Seller, and Buyer metrics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def calculate_overall_metrics_timebased(
    marketplace: pd.DataFrame, 
    buyers: pd.DataFrame, 
    transactions: pd.DataFrame,
    reference_date: pd.Timestamp = None
) -> dict:
    """
    Calculate overall marketplace metrics for a specific time period.
    """
    if reference_date is None:
        reference_date = pd.Timestamp("2025-12-31")
    
    # Filter to sellers/buyers active up to reference date
    mp_filtered = marketplace  # Marketplace is point-in-time snapshot
    buyers_filtered = buyers[buyers["signup_date"] <= reference_date]
    
    # GMV calculations
    total_gmv = mp_filtered["monthly_gmv"].sum()
    avg_gmv_per_seller = mp_filtered["monthly_gmv"].mean()
    
    # Transaction metrics
    total_transactions = mp_filtered["est_transactions"].sum()
    avg_order_value = mp_filtered["avg_order_value"].mean()
    
    # Take rate
    avg_take_rate = mp_filtered["take_rate"].mean()
    
    # Revenue breakdown
    transaction_fee_revenue = (mp_filtered["monthly_gmv"] * mp_filtered["take_rate"]).sum()
    fixed_fee_revenue = mp_filtered["fixed_fee_revenue"].sum()
    total_revenue = transaction_fee_revenue + fixed_fee_revenue
    
    # Buyer-to-Seller Ratio
    buyer_to_seller_ratio = len(buyers_filtered) / len(mp_filtered) if len(mp_filtered) > 0 else 0
    
    # Total CAC as % of Revenue
    total_buyer_cac = buyers_filtered["cac_total"].sum()
    total_cac_pct_revenue = (total_buyer_cac / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "gmv": total_gmv,
        "total_transactions": total_transactions,
        "aov": avg_order_value,
        "avg_take_rate": avg_take_rate,
        "total_revenue": total_revenue,
        "transaction_fee_revenue": transaction_fee_revenue,
        "fixed_fee_revenue": fixed_fee_revenue,
        "buyer_to_seller_ratio": buyer_to_seller_ratio,
        "total_cac_pct_revenue": total_cac_pct_revenue,
        "num_sellers": len(mp_filtered),
        "num_buyers": len(buyers_filtered),
        "avg_gmv_per_seller": avg_gmv_per_seller,
    }


def calculate_growth_rates(current: dict, previous: dict) -> dict:
    """Calculate MoM and YoY growth rates."""
    growth = {}
    for key in current:
        if key in previous and previous[key] != 0:
            growth[f"{key}_growth"] = ((current[key] - previous[key]) / previous[key] * 100)
        else:
            growth[f"{key}_growth"] = 0
    return growth


def simulate_scenario(
    marketplace: pd.DataFrame,
    buyers: pd.DataFrame,
    take_rate_multiplier: float = 1.0,
    cac_multiplier: float = 1.0,
    new_seller_growth: float = 0.0,
    new_buyer_growth: float = 0.0,
) -> dict:
    """
    Simulate marketplace metrics with adjusted parameters.
    """
    # Adjust take rate
    simulated_take_rate = marketplace["take_rate"] * take_rate_multiplier
    
    # Calculate new revenue
    transaction_fee_revenue = (marketplace["monthly_gmv"] * simulated_take_rate).sum()
    fixed_fee_revenue = marketplace["fixed_fee_revenue"].sum()
    total_revenue = transaction_fee_revenue + fixed_fee_revenue
    
    # Adjust CAC
    total_buyer_cac = buyers["cac_total"].sum() * cac_multiplier
    cac_pct_revenue = (total_buyer_cac / total_revenue * 100) if total_revenue > 0 else 0
    
    # Growth projections
    projected_sellers = int(len(marketplace) * (1 + new_seller_growth))
    projected_buyers = int(len(buyers) * (1 + new_buyer_growth))
    
    return {
        "revenue": total_revenue,
        "revenue_delta": total_revenue - ((marketplace["monthly_gmv"] * marketplace["take_rate"]).sum() + fixed_fee_revenue),
        "cac": total_buyer_cac,
        "cac_pct_revenue": cac_pct_revenue,
        "projected_sellers": projected_sellers,
        "projected_buyers": projected_buyers,
        "take_rate_avg": simulated_take_rate.mean(),
    }


def calculate_overall_metrics(marketplace: pd.DataFrame, buyers: pd.DataFrame, transactions: pd.DataFrame) -> dict:
    """
    Calculate overall marketplace metrics.
    """
    # GMV calculations
    total_gmv = marketplace["monthly_gmv"].sum()
    avg_gmv_per_seller = marketplace["monthly_gmv"].mean()
    
    # Transaction metrics
    total_transactions = marketplace["est_transactions"].sum()
    avg_order_value = marketplace["avg_order_value"].mean()
    
    # Take rate
    avg_take_rate = marketplace["take_rate"].mean()
    
    # Revenue breakdown
    transaction_fee_revenue = (marketplace["monthly_gmv"] * marketplace["take_rate"]).sum()
    fixed_fee_revenue = marketplace["fixed_fee_revenue"].sum()
    total_revenue = transaction_fee_revenue + fixed_fee_revenue
    
    # Buyer-to-Seller Ratio
    buyer_to_seller_ratio = len(buyers) / len(marketplace) if len(marketplace) > 0 else 0
    
    # Total CAC as % of Revenue
    total_buyer_cac = buyers["cac_total"].sum()
    total_cac_pct_revenue = (total_buyer_cac / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "gmv": total_gmv,
        "total_transactions": total_transactions,
        "aov": avg_order_value,
        "avg_take_rate": avg_take_rate,
        "total_revenue": total_revenue,
        "transaction_fee_revenue": transaction_fee_revenue,
        "fixed_fee_revenue": fixed_fee_revenue,
        "buyer_to_seller_ratio": buyer_to_seller_ratio,
        "total_cac_pct_revenue": total_cac_pct_revenue,
        "num_sellers": len(marketplace),
        "num_buyers": len(buyers),
        "avg_gmv_per_seller": avg_gmv_per_seller,
    }


def calculate_seller_metrics(marketplace: pd.DataFrame) -> dict:
    """
    Calculate seller/supplier metrics.
    """
    total_sellers = len(marketplace)
    
    # Retention metrics (simulated based on seller tier and GMV)
    # Higher GMV and higher tier = better retention
    retention_1m = marketplace.apply(
        lambda x: 0.85 if x["commission_tier"] in ["Pro", "Enterprise"] else 0.70, axis=1
    ).mean() * 100
    
    retention_1y = marketplace.apply(
        lambda x: 0.55 if x["commission_tier"] in ["Pro", "Enterprise"] else 0.35, axis=1
    ).mean() * 100
    
    # Average revenue per seller
    avg_revenue_per_seller = marketplace["net_revenue"].mean()
    
    # Top 20% sellers revenue contribution
    top_20_count = int(len(marketplace) * 0.2)
    top_20_revenue = marketplace.nlargest(top_20_count, "monthly_gmv")["monthly_gmv"].sum()
    total_gmv = marketplace["monthly_gmv"].sum()
    top_20_pct_revenue = (top_20_revenue / total_gmv * 100) if total_gmv > 0 else 0
    
    # Seller CAC (estimated based on tier acquisition cost)
    tier_cac = {"Starter": 25, "Growth": 50, "Pro": 120, "Enterprise": 300}
    seller_cac_paid = marketplace["commission_tier"].map(tier_cac).fillna(50)
    avg_seller_cac = seller_cac_paid.mean()
    avg_seller_cac_paid = seller_cac_paid.mean()
    
    # % acquired through paid channels (estimate)
    pct_paid_acquisition = 45.0
    
    # Listing metrics
    total_listings = marketplace["active_listings"].sum()
    avg_listings_per_seller = marketplace["active_listings"].mean()
    avg_listing_price = marketplace["monthly_gmv"].sum() / total_listings if total_listings > 0 else 0
    
    # Sell-through rate (transactions / listings)
    sell_through_rate = (marketplace["est_transactions"].sum() / total_listings * 100) if total_listings > 0 else 0
    
    return {
        "total_sellers": total_sellers,
        "retention_1m_pct": retention_1m,
        "retention_1y_pct": retention_1y,
        "avg_revenue_per_seller": avg_revenue_per_seller,
        "top_20_pct_revenue": top_20_pct_revenue,
        "avg_seller_cac": avg_seller_cac,
        "avg_seller_cac_paid": avg_seller_cac_paid,
        "pct_paid_acquisition": pct_paid_acquisition,
        "total_listings": total_listings,
        "avg_listings_per_seller": avg_listings_per_seller,
        "avg_listing_price": avg_listing_price,
        "sell_through_rate": sell_through_rate,
    }


def calculate_buyer_metrics(buyers: pd.DataFrame) -> dict:
    """
    Calculate buyer metrics.
    """
    total_buyers = len(buyers)
    
    # New buyers (signed up in last 30 days simulation)
    new_buyers = total_buyers // 12  # ~8% monthly growth
    
    # Growth rates (simulated)
    buyer_growth_mom = 8.5
    buyer_growth_yoy = 45.2
    
    # Repeat buyer rate
    repeat_buyer_pct = (buyers["repeat_buyer"].sum() / total_buyers * 100) if total_buyers > 0 else 0
    
    # GMV from repeat buyers
    repeat_buyer_gmv = buyers[buyers["repeat_buyer"]]["monthly_spend"].sum()
    total_gmv = buyers["monthly_spend"].sum()
    gmv_from_repeat_pct = (repeat_buyer_gmv / total_gmv * 100) if total_gmv > 0 else 0
    
    # Category diversity
    avg_category_diversity = buyers["category_diversity_pct"].mean()
    
    # Average purchase per buyer
    avg_purchase_per_buyer = buyers["monthly_spend"].mean()
    
    # Average orders per buyer
    avg_orders_per_buyer = buyers["total_orders"].mean()
    
    # Top 20% buyers revenue contribution
    top_20_count = int(total_buyers * 0.2)
    top_20_gmv = buyers.nlargest(top_20_count, "monthly_spend")["monthly_spend"].sum()
    top_20_pct_revenue = (top_20_gmv / total_gmv * 100) if total_gmv > 0 else 0
    
    # Buyer CAC
    avg_buyer_cac = buyers["cac_total"].mean()
    avg_buyer_cac_paid = buyers[buyers["cac_paid"] > 0]["cac_paid"].mean()
    
    # % acquired through paid channels
    pct_paid_acquisition = (buyers["cac_paid"] > 0).sum() / total_buyers * 100 if total_buyers > 0 else 0
    
    # Buyer NPS
    avg_nps = buyers["nps"].mean()
    
    return {
        "total_buyers": total_buyers,
        "new_buyers": new_buyers,
        "buyer_growth_mom": buyer_growth_mom,
        "buyer_growth_yoy": buyer_growth_yoy,
        "repeat_buyer_pct": repeat_buyer_pct,
        "gmv_from_repeat_pct": gmv_from_repeat_pct,
        "avg_category_diversity": avg_category_diversity,
        "avg_purchase_per_buyer": avg_purchase_per_buyer,
        "avg_orders_per_buyer": avg_orders_per_buyer,
        "top_20_pct_revenue": top_20_pct_revenue,
        "avg_buyer_cac": avg_buyer_cac,
        "avg_buyer_cac_paid": avg_buyer_cac_paid,
        "pct_paid_acquisition": pct_paid_acquisition,
        "avg_nps": avg_nps,
    }


def get_seller_tier_distribution(marketplace: pd.DataFrame) -> pd.DataFrame:
    """Get distribution of sellers by tier."""
    return marketplace.groupby("commission_tier").agg(
        count=("seller_id", "count"),
        total_gmv=("monthly_gmv", "sum"),
        avg_take_rate=("take_rate", "mean"),
    ).reset_index()


def get_buyer_segment_distribution(buyers: pd.DataFrame) -> pd.DataFrame:
    """Get distribution of buyers by segment."""
    return buyers.groupby("segment").agg(
        count=("buyer_id", "count"),
        total_spend=("monthly_spend", "sum"),
        avg_orders=("total_orders", "mean"),
        avg_nps=("nps", "mean"),
    ).reset_index()


def get_category_performance(marketplace: pd.DataFrame) -> pd.DataFrame:
    """Get GMV and metrics by category."""
    return marketplace.groupby("category").agg(
        sellers=("seller_id", "count"),
        total_gmv=("monthly_gmv", "sum"),
        avg_take_rate=("take_rate", "mean"),
        total_listings=("active_listings", "sum"),
    ).reset_index().sort_values("total_gmv", ascending=False)
