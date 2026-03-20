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
            
            cogs = round(revenue * cogs_pct, 2)
            # Subscribers get free shipping, or randomly applied
            ship = 0.0 if cust.get("is_subscriber", False) else shipping_cost
            net_revenue = 0.0 if is_refunded else revenue
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


def generate_marketplace_pricing(n_sellers: int = 500, take_rate_multiplier: float = 1.0, buyer_fee_split: float = 0.4, fixed_fee: float = 0.0, seed: int = SEED) -> pd.DataFrame:
    """Generate marketplace seller data with GMV, take rates, and commission tiers."""
    rng = np.random.default_rng(seed)

    categories = ["Electronics", "Fashion", "Home & Garden", "Beauty", "Sports", "Food & Beverage", "Books", "Toys"]
    tiers = ["Starter", "Growth", "Pro", "Enterprise"]
    tier_rates = {"Starter": (0.15, 0.20), "Growth": (0.12, 0.17), "Pro": (0.08, 0.14), "Enterprise": (0.05, 0.10)}
    tier_weights = [0.40, 0.30, 0.20, 0.10]

    rows = []
    for i in range(n_sellers):
        tier = rng.choice(tiers, p=tier_weights)
        cat = rng.choice(categories)
        gmv = round(float(rng.lognormal(10, 1.2)), 2)  # wide range of seller sizes
        base_take = round(float(rng.uniform(*tier_rates[tier])), 4)
        take_rate = min(0.99, base_take * take_rate_multiplier)
        buyer_fee_pct = round(take_rate * buyer_fee_split, 4)
        seller_fee_pct = round(take_rate - buyer_fee_pct, 4)
        
        aov = round(float(rng.lognormal(3.5, 0.8)), 2)
        transactions = int(gmv / max(1.0, aov))
        total_fixed_fees = transactions * fixed_fee

        rows.append({
            "seller_id": f"SELL-{i:04d}",
            "category": cat,
            "commission_tier": tier,
            "monthly_gmv": gmv,
            "take_rate": take_rate,
            "buyer_fee_pct": buyer_fee_pct,
            "seller_fee_pct": seller_fee_pct,
            "fixed_fee_revenue": round(total_fixed_fees, 2),
            "net_revenue": round((gmv * take_rate) + total_fixed_fees, 2),
            "active_listings": int(rng.integers(5, 500)),
            "est_transactions": transactions,
            "avg_order_value": aov,
        })

    return pd.DataFrame(rows)


# Convenience function to generate all datasets
def generate_all_data(seed: int = SEED):
    """Return all four datasets as a dict."""
    customers = generate_customers(seed=seed)
    transactions = generate_transactions(customers, seed=seed)
    funnel = generate_funnel_events(seed=seed)
    marketplace = generate_marketplace_pricing(seed=seed)
    return {
        "customers": customers,
        "transactions": transactions,
        "funnel": funnel,
        "marketplace": marketplace,
    }
