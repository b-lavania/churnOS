"""
Marketplace analytics : Overall, Seller, and Buyer metrics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# Default configurable constants for marketplace analytics
DEFAULT_MARKETPLACE_CONFIG = {
    "high_retention_tiers": ["Pro", "Enterprise"],
    "retention_1m_high": 0.85,
    "retention_1m_low": 0.70,
    "retention_1y_high": 0.55,
    "retention_1y_low": 0.35,
    "tier_cac": {"Starter": 25, "Growth": 50, "Pro": 120, "Enterprise": 300},
    "pct_paid_acquisition": 45.0,
    "top_percent": 0.2,
    "new_buyer_rate": 1.0 / 12.0,
    "buyer_growth_mom": 8.5,
    "buyer_growth_yoy": 45.2,
}


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


def calculate_seller_metrics(marketplace: pd.DataFrame, config: dict | None = None) -> dict:
    """
    Calculate seller/supplier metrics.
    """
    cfg = dict(DEFAULT_MARKETPLACE_CONFIG)
    if config:
        cfg.update(config)
    total_sellers = len(marketplace)

    # Retention metrics (simulated based on seller tier and GMV)
    high_tiers = cfg.get("high_retention_tiers", ["Pro", "Enterprise"])
    r1m_high = cfg.get("retention_1m_high", 0.85)
    r1m_low = cfg.get("retention_1m_low", 0.70)
    retention_1m = (
        marketplace.apply(lambda x: r1m_high if x["commission_tier"] in high_tiers else r1m_low, axis=1).mean() * 100
    )

    r1y_high = cfg.get("retention_1y_high", 0.55)
    r1y_low = cfg.get("retention_1y_low", 0.35)
    retention_1y = (
        marketplace.apply(lambda x: r1y_high if x["commission_tier"] in high_tiers else r1y_low, axis=1).mean() * 100
    )
    
    # Average revenue per seller
    avg_revenue_per_seller = marketplace["net_revenue"].mean()
    
    # Top 20% sellers revenue contribution
    top_20_count = int(len(marketplace) * 0.2)
    top_20_revenue = marketplace.nlargest(top_20_count, "monthly_gmv")["monthly_gmv"].sum()
    total_gmv = marketplace["monthly_gmv"].sum()
    top_20_pct_revenue = (top_20_revenue / total_gmv * 100) if total_gmv > 0 else 0
    
    # Seller CAC (estimated based on tier acquisition cost)
    tier_cac = cfg.get("tier_cac", {"Starter": 25, "Growth": 50, "Pro": 120, "Enterprise": 300})
    seller_cac_paid = marketplace["commission_tier"].map(tier_cac).fillna(np.mean(list(tier_cac.values())))
    avg_seller_cac = seller_cac_paid.mean()
    avg_seller_cac_paid = seller_cac_paid.mean()

    # % acquired through paid channels (estimate)
    pct_paid_acquisition = cfg.get("pct_paid_acquisition", 45.0)
    
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


def calculate_buyer_metrics(buyers: pd.DataFrame, config: dict | None = None) -> dict:
    """
    Calculate buyer metrics.
    """
    cfg = dict(DEFAULT_MARKETPLACE_CONFIG)
    if config:
        cfg.update(config)

    total_buyers = len(buyers)

    # New buyers (as a proportion) - configurable monthly rate
    new_buyer_rate = cfg.get("new_buyer_rate", 1.0 / 12.0)
    new_buyers = int(total_buyers * new_buyer_rate)

    # Growth rates (simulated)
    buyer_growth_mom = cfg.get("buyer_growth_mom", 8.5)
    buyer_growth_yoy = cfg.get("buyer_growth_yoy", 45.2)
    
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

def calculate_liquidity_metrics(buyers: pd.DataFrame, sellers: pd.DataFrame, transactions: pd.DataFrame) -> dict:
    """Calculates Search-to-Fill Rate and Time-to-First-Sale."""
    # Search-to-fill estimated from conversion rates (proxy for liquidity)
    search_to_fill_rate = min(95.0, (len(transactions) / (len(buyers) * 2)) * 100) if not buyers.empty else 0
    
    # Time to first sale
    avg_time_to_first_sale = sellers["time_to_first_sale_days"].mean() if "time_to_first_sale_days" in sellers.columns else 0
    
    # Buyer-to-seller ratio
    buyer_to_seller_ratio = len(buyers) / len(sellers) if len(sellers) > 0 else 0
    
    return {
        "search_to_fill_rate": search_to_fill_rate,
        "avg_time_to_first_sale_days": avg_time_to_first_sale,
        "buyer_to_seller_ratio": buyer_to_seller_ratio
    }

def supply_side_cohorts(sellers: pd.DataFrame) -> pd.DataFrame:
    """Generates survival curve data for seller retention."""
    if "signup_date" not in sellers.columns:
        return pd.DataFrame()
        
    sellers['signup_month'] = sellers['signup_date'].dt.to_period('M')
    
    # Calculate months active
    end_date = sellers['churn_date'].fillna(pd.Timestamp('2025-12-31'))
    sellers['months_active'] = ((end_date - sellers['signup_date']).dt.days / 30).astype(int)
    
    # Create cohort retention matrix
    max_months = 24
    retention_data = []
    
    for m in range(max_months + 1):
        active_count = len(sellers[sellers['months_active'] >= m])
        retention_pct = (active_count / len(sellers)) * 100 if len(sellers) > 0 else 0
        retention_data.append({"month": m, "active_pct": retention_pct})
        
    return pd.DataFrame(retention_data)

def cross_side_network_effects(buyers: pd.DataFrame, sellers: pd.DataFrame, simulated_seller_growth: float = 0.0) -> dict:
    """Models the causal link between supply density and buyer conversion."""
    base_sellers = len(sellers)
    new_sellers = int(base_sellers * (1 + simulated_seller_growth))
    
    # Assume 10% increase in sellers leads to 2% increase in buyer conversion
    conversion_boost = (simulated_seller_growth * 100) * 0.2
    
    base_conversion = 3.5 # Example base conversion
    new_conversion = base_conversion * (1 + (conversion_boost / 100))
    
    # Projected GMV impact
    total_gmv = sellers["monthly_gmv"].sum()
    new_gmv = total_gmv * (1 + (conversion_boost / 100))
    
    return {
        "projected_sellers": new_sellers,
        "base_conversion_pct": base_conversion,
        "projected_conversion_pct": new_conversion,
        "gmv_lift_pct": conversion_boost,
        "projected_gmv": new_gmv
    }
