"""
Pricing analytics for marketplaces — take-rate analysis, price elasticity,
commission tiers, and buyer/seller fee split modeling.
"""

import numpy as np
import pandas as pd


def take_rate_analysis(marketplace: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze effective take rates by category.
    Returns aggregated metrics per category: GMV, net revenue, effective take rate.
    """
    grouped = marketplace.groupby("category").agg(
        num_sellers=("seller_id", "nunique"),
        total_gmv=("monthly_gmv", "sum"),
        total_net_revenue=("net_revenue", "sum"),
        avg_take_rate=("take_rate", "mean"),
        avg_buyer_fee=("buyer_fee_pct", "mean"),
        avg_seller_fee=("seller_fee_pct", "mean"),
    ).reset_index()
    
    grouped["effective_take_rate"] = (grouped["total_net_revenue"] / grouped["total_gmv"] * 100).round(2)
    grouped["total_gmv"] = grouped["total_gmv"].round(0)
    grouped["total_net_revenue"] = grouped["total_net_revenue"].round(0)
    grouped["avg_take_rate"] = (grouped["avg_take_rate"] * 100).round(2)
    grouped["avg_buyer_fee"] = (grouped["avg_buyer_fee"] * 100).round(2)
    grouped["avg_seller_fee"] = (grouped["avg_seller_fee"] * 100).round(2)
    
    return grouped.sort_values("total_gmv", ascending=False).reset_index(drop=True)


def price_elasticity_sim(
    base_price: float = 50.0,
    elasticity: float = -1.5,
    price_range: tuple = (0.5, 2.0),
    n_points: int = 50,
) -> pd.DataFrame:
    """
    Simulate demand and revenue curves based on price elasticity of demand.
    
    Q = Q0 * (P / P0) ^ elasticity
    Revenue = P * Q
    
    Args:
        base_price: Reference price point
        elasticity: Price elasticity (typically negative)
        price_range: Multiplier range around base price
        n_points: Number of simulation points
    """
    base_quantity = 1000  # normalized base demand
    
    price_multipliers = np.linspace(price_range[0], price_range[1], n_points)
    prices = base_price * price_multipliers
    quantities = base_quantity * (price_multipliers ** elasticity)
    revenues = prices * quantities
    
    return pd.DataFrame({
        "price": np.round(prices, 2),
        "price_multiplier": np.round(price_multipliers, 2),
        "demand": np.round(quantities, 0).astype(int),
        "revenue": np.round(revenues, 2),
        "margin_index": np.round(revenues / revenues.max() * 100, 1),
    })


def commission_tier_model(marketplace: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze revenue by commission tier.
    Returns per-tier metrics.
    """
    grouped = marketplace.groupby("commission_tier").agg(
        num_sellers=("seller_id", "nunique"),
        total_gmv=("monthly_gmv", "sum"),
        total_net_revenue=("net_revenue", "sum"),
        avg_take_rate=("take_rate", "mean"),
        avg_order_value=("avg_order_value", "mean"),
    ).reset_index()
    
    grouped["effective_take_rate"] = (grouped["total_net_revenue"] / grouped["total_gmv"] * 100).round(2)
    grouped["gmv_share"] = (grouped["total_gmv"] / grouped["total_gmv"].sum() * 100).round(1)
    grouped["revenue_share"] = (grouped["total_net_revenue"] / grouped["total_net_revenue"].sum() * 100).round(1)
    grouped["total_gmv"] = grouped["total_gmv"].round(0)
    grouped["total_net_revenue"] = grouped["total_net_revenue"].round(0)
    grouped["avg_take_rate"] = (grouped["avg_take_rate"] * 100).round(2)
    grouped["avg_order_value"] = grouped["avg_order_value"].round(2)
    
    # Sort by tier order
    tier_order = {"Starter": 0, "Growth": 1, "Pro": 2, "Enterprise": 3}
    grouped["sort_key"] = grouped["commission_tier"].map(tier_order)
    grouped = grouped.sort_values("sort_key").drop("sort_key", axis=1).reset_index(drop=True)
    
    return grouped


def fee_split_scenario(
    gmv: float = 1_000_000,
    buyer_fee_pct: float = 3.0,
    seller_fee_pct: float = 12.0,
    scenarios: list = None,
) -> pd.DataFrame:
    """
    Model fee-split scenarios: what happens if you shift fees between buyer and seller.
    
    Args:
        gmv: Total Gross Merchandise Volume
        buyer_fee_pct: Current buyer fee %
        seller_fee_pct: Current seller fee %
        scenarios: List of (buyer_fee, seller_fee) tuples to model; if None uses defaults
    """
    if scenarios is None:
        total = buyer_fee_pct + seller_fee_pct
        scenarios = [
            (0, total),                          # All on seller
            (buyer_fee_pct / 2, total - buyer_fee_pct / 2),
            (buyer_fee_pct, seller_fee_pct),     # Current split
            (total / 2, total / 2),              # 50/50
            (total - seller_fee_pct / 2, seller_fee_pct / 2),
            (total, 0),                          # All on buyer
        ]
    
    rows = []
    for bf, sf in scenarios:
        buyer_revenue = gmv * bf / 100
        seller_revenue = gmv * sf / 100
        total_revenue = buyer_revenue + seller_revenue
        rows.append({
            "scenario": f"Buyer {bf:.1f}% / Seller {sf:.1f}%",
            "buyer_fee_pct": bf,
            "seller_fee_pct": sf,
            "total_take_rate": round(bf + sf, 2),
            "buyer_revenue": round(buyer_revenue, 2),
            "seller_revenue": round(seller_revenue, 2),
            "total_revenue": round(total_revenue, 2),
        })
    
    return pd.DataFrame(rows)
