"""
Synthetic data generator for ecommerce & marketplace analytics.
Produces realistic datasets for churn, retention, conversion, and pricing analysis.
"""

import numpy as np
import pandas as pd
from datetime import timedelta

SEED = 42


def generate_customers(n: int = 5000, seed: int = SEED, churn_multiplier: float = 1.0, premium_mix: float = 0.0, subscribe_ratio: float = 0.0) -> pd.DataFrame:
    """Generate a customer table with signup info, segment, and churn status."""
    rng = np.random.default_rng(seed)

    channels = ["Organic", "Paid Search", "Social Media", "Referral", "Email", "Affiliate"]
    segments = ["Budget", "Mid-Range", "Premium", "Enterprise"]
    channel_weights = [0.30, 0.25, 0.20, 0.10, 0.10, 0.05]
    
    # Base segment weights: [0.35, 0.35, 0.20, 0.10]
    # premium_mix shifts weight from budget/mid to premium/enterprise.
    shift = premium_mix / 2
    raw_weights = [max(0.01, 0.35 - shift), max(0.01, 0.35 - shift), max(0.01, 0.20 + shift), max(0.01, 0.10 + shift)]
    seg_sum = sum(raw_weights)
    segment_weights = [w / seg_sum for w in raw_weights]

    start_date = pd.Timestamp("2023-01-01")
    end_date = pd.Timestamp("2025-12-31")
    date_range_days = (end_date - start_date).days

    signup_dates = start_date + pd.to_timedelta(
        rng.integers(0, date_range_days, size=n), unit="D"
    )

    # Churn probability varies by segment and is scaled by the multiplier
    segment_churn_prob = {
        "Budget": min(0.99, 0.40 * churn_multiplier), 
        "Mid-Range": min(0.99, 0.25 * churn_multiplier), 
        "Premium": min(0.99, 0.15 * churn_multiplier), 
        "Enterprise": min(0.99, 0.10 * churn_multiplier)
    }

    segments_arr = rng.choice(segments, size=n, p=segment_weights)
    channels_arr = rng.choice(channels, size=n, p=channel_weights)

    is_subscriber = rng.random(size=n) < subscribe_ratio

    is_churned = np.array([
        rng.random() < (segment_churn_prob[seg] * (0.2 if sub else 1.0)) 
        for seg, sub in zip(segments_arr, is_subscriber)
    ])

    # Churn happens between 30-365 days after signup (subscribers stay longer)
    days_to_churn = [
        rng.integers(180, 730) if sub else rng.integers(30, 365)
        for sub in is_subscriber
    ]
    churn_dates = pd.NaT
    churn_date_series = pd.Series([
        signup_dates[i] + timedelta(days=int(days_to_churn[i])) if is_churned[i] else pd.NaT
        for i in range(n)
    ])

    # Monthly spend varies by segment
    segment_spend = {"Budget": (15, 40), "Mid-Range": (40, 120), "Premium": (120, 350), "Enterprise": (350, 1200)}
    monthly_spend = np.array([
        rng.uniform(*segment_spend[seg]) for seg in segments_arr
    ])

    df = pd.DataFrame({
        "customer_id": [f"CUST-{i:05d}" for i in range(n)],
        "signup_date": signup_dates,
        "acquisition_channel": channels_arr,
        "segment": segments_arr,
        "is_subscriber": is_subscriber,
        "monthly_spend": np.round(monthly_spend, 2),
        "is_churned": is_churned,
        "churn_date": churn_date_series,
    })
    df["signup_month"] = df["signup_date"].dt.to_period("M")
    return df


def generate_transactions(
    customers: pd.DataFrame, 
    avg_per_customer: int = 12, 
    aov_multiplier: float = 1.0, 
    discount_freq: float = 0.25, 
    refund_rate: float = 0.05,
    cogs_pct: float = 0.40,
    shipping_cost: float = 5.0,
    seed: int = SEED
) -> pd.DataFrame:
    """Generate a transaction log linked to customers."""
    rng = np.random.default_rng(seed)
    rows = []
    tid = 0

    for _, cust in customers.iterrows():
        # Active customers buy more
        n_txns = rng.poisson(avg_per_customer if not cust["is_churned"] else avg_per_customer // 3)
        n_txns = max(1, n_txns)

        end = cust["churn_date"] if pd.notna(cust["churn_date"]) else pd.Timestamp("2025-12-31")
        span_days = max(1, (end - cust["signup_date"]).days)

        for _ in range(n_txns):
            offset = rng.integers(0, span_days)
            txn_date = cust["signup_date"] + timedelta(days=int(offset))
            revenue = round(float(rng.lognormal(np.log((cust["monthly_spend"] / 3) * aov_multiplier), 0.5)), 2)
            items = int(rng.integers(1, 8))
            discount = bool(rng.random() < discount_freq)
            is_refunded = bool(rng.random() < refund_rate)
            
            # E-commerce extensions
            inventory_level = int(rng.poisson(20))
            is_stockout = inventory_level == 0
            
            if is_stockout:
                revenue = 0.0
                items = 0
                discount = False
                is_refunded = False
                
            dynamic_cogs_pct = cogs_pct
            if inventory_level < 5 and not is_stockout:
                dynamic_cogs_pct = min(0.9, cogs_pct * 1.3)
                
            cogs = round(revenue * dynamic_cogs_pct, 2)
            
            is_incremental = False
            is_cannibalized = False
            if discount and not is_stockout:
                is_cannibalized = bool(rng.random() < (0.6 if discount_freq > 0.3 else 0.3))
                is_incremental = not is_cannibalized

            # Subscribers get free shipping, or randomly applied
            ship = 0.0 if cust.get("is_subscriber", False) else shipping_cost
            net_revenue = 0.0 if is_refunded or is_stockout else revenue
            gross_margin = net_revenue - cogs - ship

            rows.append({
                "transaction_id": f"TXN-{tid:07d}",
                "customer_id": cust["customer_id"],
                "date": txn_date,
                "gross_revenue": revenue,
                "net_revenue": net_revenue,
                "cogs": cogs,
                "shipping": ship,
                "gross_margin": round(gross_margin, 2),
                "items": items,
                "discount_applied": discount,
                "is_refunded": is_refunded,
                "inventory_level": inventory_level,
                "is_stockout": is_stockout,
                "is_incremental": is_incremental,
                "is_cannibalized": is_cannibalized,
            })
            tid += 1

    return pd.DataFrame(rows)


def generate_funnel_events(n_sessions: int = 30000, checkout_dropoff_modifier: float = 1.0, mobile_share: float = 0.48, free_shipping: bool = False, seed: int = SEED) -> pd.DataFrame:
    """Generate conversion funnel events: Visit → Product View → Add to Cart → Checkout → Purchase."""
    rng = np.random.default_rng(seed)

    steps = ["Visit", "Product View", "Add to Cart", "Checkout", "Purchase"]
    # drop-off probability at each step (% who proceed)
    fs_boost = 1.25 if free_shipping else 1.0
    step_rates = {
        "Visit": 1.0, 
        "Product View": 0.65, 
        "Add to Cart": min(0.99, 0.35 * fs_boost), 
        "Checkout": min(0.99, 0.22 * checkout_dropoff_modifier * fs_boost), 
        "Purchase": min(0.99, 0.14 * checkout_dropoff_modifier * (fs_boost ** 0.5))
    }

    devices = ["Desktop", "Mobile", "Tablet"]
    sources = ["Organic", "Paid Search", "Social", "Direct", "Email"]
    
    tablet_w = 0.12
    dt_w = max(0.01, 1.0 - tablet_w - mobile_share)
    raw_dw = [dt_w, mobile_share, tablet_w]
    sw = sum(raw_dw)
    device_weights = [w / sw for w in raw_dw]
    
    source_weights = [0.30, 0.25, 0.20, 0.15, 0.10]

    start_date = pd.Timestamp("2024-01-01")

    rows = []
    for sid in range(n_sessions):
        device = rng.choice(devices, p=device_weights)
        source = rng.choice(sources, p=source_weights)
        session_date = start_date + timedelta(days=int(rng.integers(0, 365)))

        # Device affects conversion: mobile converts worse
        device_modifier = {"Desktop": 1.0, "Mobile": 0.78, "Tablet": 0.88}[device]

        for step in steps:
            effective_rate = step_rates[step] * device_modifier if step != "Visit" else 1.0
            if rng.random() > effective_rate:
                break
            rows.append({
                "session_id": f"SESS-{sid:06d}",
                "timestamp": session_date,
                "funnel_step": step,
                "device": device,
                "source": source,
            })

    return pd.DataFrame(rows)


def generate_marketplace_pricing(
    n_sellers: int = 500,
    take_rate_multiplier: float = 1.0,
    buyer_fee_split: float = 0.4,
    fixed_fee: float = 0.0,
    categories: list | None = None,
    tiers: list | None = None,
    tier_rates: dict | None = None,
    tier_weights: list | None = None,
    gmv_mu: float = 10.0,
    gmv_sigma: float = 1.2,
    aov_mu: float = 3.5,
    aov_sigma: float = 0.8,
    listings_min: int = 5,
    listings_max: int = 500,
    seed: int = SEED,
) -> pd.DataFrame:
    """Generate marketplace seller data with GMV, take rates, and commission tiers.

    This function accepts optional parameters to control the distributions and
    categorical choices used when synthesizing marketplace data. Defaults
    preserve previous behaviour if parameters are not passed.
    """
    rng = np.random.default_rng(seed)

    if categories is None:
        categories = [
            "Electronics",
            "Fashion",
            "Home & Garden",
            "Beauty",
            "Sports",
            "Food & Beverage",
            "Books",
            "Toys",
        ]
    if tiers is None:
        tiers = ["Starter", "Growth", "Pro", "Enterprise"]
    if tier_rates is None:
        tier_rates = {
            "Starter": (0.15, 0.20),
            "Growth": (0.12, 0.17),
            "Pro": (0.08, 0.14),
            "Enterprise": (0.05, 0.10),
        }
    if tier_weights is None:
        tier_weights = [0.40, 0.30, 0.20, 0.10]

    start_date = pd.Timestamp("2023-01-01")
    end_date = pd.Timestamp("2025-12-31")
    date_range_days = (end_date - start_date).days

    rows = []
    for i in range(n_sellers):
        tier = rng.choice(tiers, p=tier_weights)
        cat = rng.choice(categories)
        gmv = round(float(rng.lognormal(gmv_mu, gmv_sigma)), 2)  # wide range of seller sizes
        base_take = round(float(rng.uniform(*tier_rates.get(tier, (0.08, 0.14)))), 4)
        take_rate = min(0.99, base_take * take_rate_multiplier)
        buyer_fee_pct = round(take_rate * buyer_fee_split, 4)
        seller_fee_pct = round(take_rate - buyer_fee_pct, 4)

        aov = round(float(rng.lognormal(aov_mu, aov_sigma)), 2)
        transactions = int(gmv / max(1.0, aov))
        total_fixed_fees = transactions * fixed_fee
        
        # Marketplace Seller Cohorts
        signup_offset = rng.integers(0, date_range_days)
        signup_date = start_date + timedelta(days=int(signup_offset))
        
        tier_churn_prob = {"Starter": 0.5, "Growth": 0.3, "Pro": 0.15, "Enterprise": 0.05}
        is_churned = rng.random() < tier_churn_prob.get(tier, 0.2)
        days_to_churn = int(rng.integers(30, 365 * 2))
        churn_date = signup_date + timedelta(days=days_to_churn) if is_churned else pd.NaT
        
        time_to_first_sale_days = int(rng.integers(1, 45)) if rng.random() < 0.8 else int(rng.integers(46, 120))

        rows.append(
            {
                "seller_id": f"SELL-{i:04d}",
                "category": cat,
                "commission_tier": tier,
                "signup_date": signup_date,
                "churn_date": churn_date,
                "is_churned": is_churned,
                "time_to_first_sale_days": time_to_first_sale_days,
                "monthly_gmv": gmv,
                "take_rate": take_rate,
                "buyer_fee_pct": buyer_fee_pct,
                "seller_fee_pct": seller_fee_pct,
                "fixed_fee_revenue": round(total_fixed_fees, 2),
                "net_revenue": round((gmv * take_rate) + total_fixed_fees, 2),
                "active_listings": int(rng.integers(listings_min, listings_max + 1)),
                "est_transactions": transactions,
                "avg_order_value": aov,
            }
        )

    return pd.DataFrame(rows)


def generate_buyers(n_buyers: int = 10000, seed: int = SEED) -> pd.DataFrame:
    """Generate marketplace buyer data with purchase behavior metrics."""
    rng = np.random.default_rng(seed)

    acquisition_channels = ["Organic", "Paid Search", "Social Media", "Referral", "Email", "Affiliate"]
    channel_weights = [0.30, 0.25, 0.20, 0.10, 0.10, 0.05]
    
    start_date = pd.Timestamp("2023-01-01")
    end_date = pd.Timestamp("2025-12-31")
    date_range_days = (end_date - start_date).days

    signup_dates = start_date + pd.to_timedelta(
        rng.integers(0, date_range_days, size=n_buyers), unit="D"
    )

    # Segment-based purchase behavior
    segments = ["Budget", "Mid-Range", "Premium", "Enterprise"]
    segment_weights = [0.35, 0.35, 0.20, 0.10]
    segments_arr = rng.choice(segments, size=n_buyers, p=segment_weights)
    
    channels_arr = rng.choice(acquisition_channels, size=n_buyers, p=channel_weights)
    
    # Monthly purchase amounts by segment
    segment_spend = {"Budget": (20, 60), "Mid-Range": (60, 200), "Premium": (200, 600), "Enterprise": (600, 2500)}
    monthly_spend = np.array([rng.uniform(*segment_spend[seg]) for seg in segments_arr])
    
    # Number of orders
    orders = rng.poisson(monthly_spend / 80, size=n_buyers).clip(min=1, max=50)
    
    # Retention metrics
    is_retained_1m = rng.random(size=n_buyers) < 0.65
    is_retained_1y = rng.random(size=n_buyers) < 0.35
    
    # CAC values
    cac_paid = np.where(rng.random(size=n_buyers) < 0.4, rng.uniform(15, 80, size=n_buyers), 0)
    cac_total = cac_paid + rng.uniform(5, 25, size=n_buyers)  # blended with organic
    
    # NPS scores
    nps = rng.integers(0, 11, size=n_buyers)
    
    # Category diversity (percentage of buyers who buy from multiple categories)
    category_diversity = rng.random(size=n_buyers)

    df = pd.DataFrame({
        "buyer_id": [f"BUY-{i:06d}" for i in range(n_buyers)],
        "signup_date": signup_dates,
        "acquisition_channel": channels_arr,
        "segment": segments_arr,
        "monthly_spend": np.round(monthly_spend, 2),
        "total_orders": orders,
        "is_retained_1m": is_retained_1m,
        "is_retained_1y": is_retained_1y,
        "cac_total": np.round(cac_total, 2),
        "cac_paid": np.round(cac_paid, 2),
        "nps": nps,
        "category_diversity_pct": np.round(category_diversity * 100, 1),
        "repeat_buyer": rng.random(size=n_buyers) < 0.45,
    })
    return df


def generate_marketing_spend(days: int = 365, seed: int = SEED) -> pd.DataFrame:
    """Generate daily marketing spend and ground-truth sales for Bayesian MMM."""
    rng = np.random.default_rng(seed)
    
    start_date = pd.Timestamp("2024-01-01")
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    spend_meta = np.abs(1000 + 300 * np.sin(np.linspace(0, 10, days)) + rng.normal(0, 150, days))
    spend_google = np.abs(800 + 100 * np.sin(np.linspace(0, 10, days) + 2) + rng.normal(0, 100, days))
    spend_tiktok = np.abs(500 + 400 * np.sin(np.linspace(0, 15, days) + 1) + rng.normal(0, 200, days))
    spend_email = np.abs(100 + 20 * np.sin(np.linspace(0, 20, days)) + rng.normal(0, 10, days))
    
    def apply_adstock(spend, retain_rate):
        adstocked = np.zeros_like(spend)
        adstocked[0] = spend[0]
        for t in range(1, len(spend)):
            adstocked[t] = spend[t] + retain_rate * adstocked[t-1]
        return adstocked

    def apply_saturation(spend, alpha, lam):
        return alpha * spend / (lam + spend)

    params = {
        "Meta": {"adstock": 0.3, "alpha": 3000, "lam": 1000},
        "Google": {"adstock": 0.1, "alpha": 2500, "lam": 800},
        "TikTok": {"adstock": 0.6, "alpha": 4000, "lam": 2000},
        "Email": {"adstock": 0.05, "alpha": 800, "lam": 100}
    }
    
    adstocked_meta = apply_adstock(spend_meta, params["Meta"]["adstock"])
    adstocked_google = apply_adstock(spend_google, params["Google"]["adstock"])
    adstocked_tiktok = apply_adstock(spend_tiktok, params["TikTok"]["adstock"])
    adstocked_email = apply_adstock(spend_email, params["Email"]["adstock"])
    
    sales_meta = apply_saturation(adstocked_meta, params["Meta"]["alpha"], params["Meta"]["lam"])
    sales_google = apply_saturation(adstocked_google, params["Google"]["alpha"], params["Google"]["lam"])
    sales_tiktok = apply_saturation(adstocked_tiktok, params["TikTok"]["alpha"], params["TikTok"]["lam"])
    sales_email = apply_saturation(adstocked_email, params["Email"]["alpha"], params["Email"]["lam"])
    
    baseline_sales = 2000 + 500 * np.sin(np.linspace(0, 6.28, days)) # seasonality
    noise = rng.normal(0, 300, days)
    
    total_sales = baseline_sales + sales_meta + sales_google + sales_tiktok + sales_email + noise
    
    df = pd.DataFrame({
        "Date": dates,
        "Spend_Meta": spend_meta,
        "Spend_Google": spend_google,
        "Spend_TikTok": spend_tiktok,
        "Spend_Email": spend_email,
        "Sales": np.maximum(0, total_sales)
    })
    
    return df

# Convenience function to generate all datasets
def generate_all_data(seed: int = SEED):
    """Return all datasets as a dict."""
    customers = generate_customers(seed=seed)
    transactions = generate_transactions(customers, seed=seed)
    funnel = generate_funnel_events(seed=seed)
    marketplace = generate_marketplace_pricing(seed=seed)
    buyers = generate_buyers(seed=seed)
    marketing = generate_marketing_spend(seed=seed)
    return {
        "customers": customers,
        "transactions": transactions,
        "funnel": funnel,
        "marketplace": marketplace,
        "buyers": buyers,
        "marketing": marketing,
    }
