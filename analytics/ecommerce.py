import pandas as pd
import numpy as np

def calculate_rfm_segments(transactions: pd.DataFrame, reference_date=pd.Timestamp('2025-12-31')) -> pd.DataFrame:
    """Calculate Recency, Frequency, and Monetary value for each customer."""
    valid_txns = transactions[~transactions['is_stockout']].copy()
    
    if valid_txns.empty:
        return pd.DataFrame()
        
    rfm = valid_txns.groupby('customer_id').agg({
        'date': lambda x: (reference_date - x.max()).days,
        'transaction_id': 'count',
        'net_revenue': 'sum'
    }).reset_index()
    
    rfm.columns = ['customer_id', 'Recency', 'Frequency', 'Monetary']
    
    try:
        rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1], duplicates='drop')
    except ValueError:
        rfm['R_Score'] = 2
        
    try:
        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
    except ValueError:
        rfm['F_Score'] = 2
        
    try:
        rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4], duplicates='drop')
    except ValueError:
        rfm['M_Score'] = 2
    
    def segment_customer(row):
        r, f = int(row['R_Score']), int(row['F_Score'])
        if r >= 3 and f >= 3:
            return 'Champions'
        elif r >= 2 and f >= 2:
            return 'Loyal Customers'
        elif r <= 2 and f >= 3:
            return 'At Risk'
        elif r <= 2 and f <= 2:
            return 'Hibernating'
        else:
            return 'Potential Loyalist'
            
    rfm['Segment'] = rfm.apply(segment_customer, axis=1)
    return rfm

def inventory_volatility_impact(transactions: pd.DataFrame) -> dict:
    """Models the revenue lost to stockouts and the impact of dynamic COGS."""
    if transactions.empty:
        return {}
        
    stockouts = transactions[transactions['is_stockout']]
    valid_txns = transactions[~transactions['is_stockout']]
    
    avg_txn_value = valid_txns['gross_revenue'].mean() if not valid_txns.empty else 0
    lost_revenue = len(stockouts) * avg_txn_value
    
    actual_cogs = valid_txns['cogs'].sum()
    # Approximate base cogs as 40% if not provided
    estimated_base_cogs = valid_txns['gross_revenue'].sum() * 0.40
    cogs_variance = actual_cogs - estimated_base_cogs
    
    total_rev = valid_txns['gross_revenue'].sum()
    margin_compression_pct = (cogs_variance / total_rev) * 100 if total_rev > 0 else 0
    
    return {
        "stockout_count": len(stockouts),
        "lost_revenue_est": lost_revenue,
        "actual_cogs": actual_cogs,
        "cogs_variance": cogs_variance,
        "margin_compression_pct": margin_compression_pct
    }

def discount_cannibalization_analysis(transactions: pd.DataFrame) -> dict:
    """Estimates the true incremental margin of promotions versus cannibalized full-price sales."""
    if transactions.empty:
        return {}
        
    discounted = transactions[transactions['discount_applied'] & ~transactions['is_stockout']]
    
    incremental = discounted[discounted['is_incremental']]
    cannibalized = discounted[discounted['is_cannibalized']]
    
    inc_margin = incremental['gross_margin'].sum()
    
    estimated_full_margin = cannibalized['gross_revenue'].sum() - cannibalized['cogs'].sum()
    actual_margin = cannibalized['gross_margin'].sum()
    margin_lost_to_cannibalization = estimated_full_margin - actual_margin
    
    return {
        "discount_events": len(discounted),
        "incremental_events": len(incremental),
        "cannibalized_events": len(cannibalized),
        "incremental_margin": inc_margin,
        "margin_lost_to_cannibalization": margin_lost_to_cannibalization,
        "net_promo_value": inc_margin - margin_lost_to_cannibalization
    }
