"""
Property-based tests for CRO metrics calculator.

Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
Validates: Requirements 7.1, 7.2, 7.3, 7.4, 9.1, 9.2, 9.3, 9.4, 20.1, 20.2, 20.3, 20.4, 20.5
"""

import pytest
from hypothesis import given, strategies as st
import pandas as pd
import numpy as np
from analytics.conversion import calculate_cro_metrics


# Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
@given(
    num_sessions=st.integers(min_value=1, max_value=1000),
    primary_conversion_rate=st.floats(min_value=0.0, max_value=1.0),
    secondary_conversion_rates=st.dictionaries(
        keys=st.text(min_size=3, max_size=20),
        values=st.floats(min_value=0.0, max_value=1.0),
        min_size=0,
        max_size=5
    )
)
def test_conversion_rate_calculation_consistency(num_sessions, primary_conversion_rate, secondary_conversion_rates):
    """
    Property 15: Conversion Rate Calculation Consistency
    
    For any dataset with visitors and conversions, the conversion rate SHALL equal
    conversions divided by visitors, expressed as a percentage, and this calculation
    SHALL be consistent across all segments and metrics.
    """
    # Generate funnel data
    data = []
    
    # Primary conversion (Purchase)
    primary_conversions = int(num_sessions * primary_conversion_rate)
    
    for i in range(num_sessions):
        session_id = f'sess_{i}'
        data.append({
            'session_id': session_id,
            'funnel_step': 'Visit'
        })
        
        # Primary conversion
        if i < primary_conversions:
            data.append({
                'session_id': session_id,
                'funnel_step': 'Purchase'
            })
        
        # Secondary conversions
        for goal, rate in secondary_conversion_rates.items():
            if i < int(num_sessions * rate):
                data.append({
                    'session_id': session_id,
                    'funnel_step': goal
                })
    
    df = pd.DataFrame(data)
    
    # Calculate metrics
    result = calculate_cro_metrics(df)
    
    # Verify primary conversion rate calculation
    # Note: If no Purchase step exists, the function uses the max step as primary
    # So we only check when Purchase step exists
    if 'Purchase' in df['funnel_step'].values:
        expected_primary_rate = round((primary_conversions / num_sessions) * 100, 2)
        assert abs(result['primary_conversion_rate'] - expected_primary_rate) < 0.1, \
            f"Primary conversion rate mismatch: expected {expected_primary_rate}, got {result['primary_conversion_rate']}"
    
    # Verify secondary conversion rates
    for goal, expected_rate in secondary_conversion_rates.items():
        if goal in result['secondary_conversion_rates']:
            actual_rate = result['secondary_conversion_rates'][goal]
            expected_value = round((int(num_sessions * expected_rate) / num_sessions) * 100, 2)
            assert abs(actual_rate - expected_value) < 0.1, \
                f"Secondary conversion rate for {goal} mismatch: expected {expected_value}, got {actual_rate}"


# Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
@given(
    num_sessions=st.integers(min_value=10, max_value=500),
    bounce_rate=st.floats(min_value=0.0, max_value=1.0)
)
def test_bounce_rate_calculation(num_sessions, bounce_rate):
    """
    Property 15: Bounce rate is calculated as single-page sessions / total sessions.
    """
    # Generate funnel data with controlled bounce rate
    data = []
    single_page_sessions = int(num_sessions * bounce_rate)
    
    for i in range(num_sessions):
        session_id = f'sess_{i}'
        
        if i < single_page_sessions:
            # Single-page session (bounced)
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
        else:
            # Multi-page session (not bounced)
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            data.append({
                'session_id': session_id,
                'funnel_step': 'Product View'
            })
    
    df = pd.DataFrame(data)
    result = calculate_cro_metrics(df)
    
    # Verify bounce rate calculation
    expected_bounce_rate = round((single_page_sessions / num_sessions) * 100, 2)
    assert abs(result['bounce_rate'] - expected_bounce_rate) < 0.1, \
        f"Bounce rate mismatch: expected {expected_bounce_rate}, got {result['bounce_rate']}"


# Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
@given(
    num_sessions=st.integers(min_value=10, max_value=500),
    engagement_rate=st.floats(min_value=0.0, max_value=1.0)
)
def test_engagement_rate_calculation(num_sessions, engagement_rate):
    """
    Property 15: Engagement rates are calculated as engaged sessions / total sessions.
    """
    # Generate funnel data with controlled engagement
    data = []
    engaged_sessions = int(num_sessions * engagement_rate)
    
    for i in range(num_sessions):
        session_id = f'sess_{i}'
        data.append({
            'session_id': session_id,
            'funnel_step': 'Visit',
            'scroll_depth': 90 if i < engaged_sessions else 20
        })
    
    df = pd.DataFrame(data)
    result = calculate_cro_metrics(df)
    
    # Verify engagement rate calculation
    expected_engagement_rate = round((engaged_sessions / num_sessions) * 100, 2)
    
    # Above-fold engagement should match (scroll > 50)
    assert abs(result['above_fold_engagement'] - expected_engagement_rate) < 0.1, \
        f"Above-fold engagement mismatch: expected {expected_engagement_rate}, got {result['above_fold_engagement']}"


# Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
@given(
    num_sessions=st.integers(min_value=10, max_value=500),
    ctr=st.floats(min_value=0.0, max_value=1.0)
)
def test_ctr_calculation(num_sessions, ctr):
    """
    Property 15: CTR is calculated as clicks / impressions.
    """
    # Generate funnel data with controlled CTR
    data = []
    num_clicks = int(num_sessions * ctr)
    
    for i in range(num_sessions):
        session_id = f'sess_{i}'
        data.append({
            'session_id': session_id,
            'funnel_step': 'Visit',
            'page_element': 'call_to_action',
            'click_event': 1 if i < num_clicks else 0
        })
    
    df = pd.DataFrame(data)
    result = calculate_cro_metrics(df)
    
    # Verify CTR calculation
    expected_ctr = round((num_clicks / num_sessions) * 100, 2)
    
    if 'call_to_action' in result['ctr_by_element']:
        actual_ctr = result['ctr_by_element']['call_to_action']
        assert abs(actual_ctr - expected_ctr) < 0.1, \
            f"CTR mismatch: expected {expected_ctr}, got {actual_ctr}"


# Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
@given(
    num_sessions=st.integers(min_value=10, max_value=500),
    avg_time=st.floats(min_value=0.1, max_value=300.0)
)
def test_avg_time_on_page_calculation(num_sessions, avg_time):
    """
    Property 15: Average time on page is calculated as sum of times / sessions with time data.
    """
    # Generate funnel data with controlled average time
    data = []
    
    for i in range(num_sessions):
        session_id = f'sess_{i}'
        # Use fixed time to ensure average matches expected value
        data.append({
            'session_id': session_id,
            'funnel_step': 'Visit',
            'time_on_page': avg_time
        })
    
    df = pd.DataFrame(data)
    result = calculate_cro_metrics(df)
    
    # Verify average time calculation
    assert abs(result['avg_time_on_page'] - avg_time) < 0.1, \
        f"Avg time mismatch: expected {avg_time}, got {result['avg_time_on_page']}"


# Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
@given(
    num_sessions=st.integers(min_value=10, max_value=500),
    primary_rate=st.floats(min_value=0.0, max_value=1.0),
    secondary_rate=st.floats(min_value=0.0, max_value=1.0)
)
def test_multiple_conversion_rates_consistency(num_sessions, primary_rate, secondary_rate):
    """
    Property 15: Multiple conversion rates (primary + secondary) are all calculated consistently.
    """
    # Generate funnel data with both primary and secondary conversions
    data = []
    primary_conversions = int(num_sessions * primary_rate)
    secondary_conversions = int(num_sessions * secondary_rate)
    
    for i in range(num_sessions):
        session_id = f'sess_{i}'
        data.append({
            'session_id': session_id,
            'funnel_step': 'Visit'
        })
        
        # Primary conversion
        if i < primary_conversions:
            data.append({
                'session_id': session_id,
                'funnel_step': 'Purchase'
            })
        
        # Secondary conversion
        if i < secondary_conversions:
            data.append({
                'session_id': session_id,
                'funnel_step': 'Newsletter Signup'
            })
    
    df = pd.DataFrame(data)
    result = calculate_cro_metrics(df)
    
    # Verify both conversion rates
    # Note: If no Purchase step exists, the function uses the max step as primary
    if 'Purchase' in df['funnel_step'].values:
        expected_primary = round((primary_conversions / num_sessions) * 100, 2)
        assert abs(result['primary_conversion_rate'] - expected_primary) < 0.1, \
            f"Primary rate mismatch: expected {expected_primary}, got {result['primary_conversion_rate']}"
    
    if 'Newsletter Signup' in result['secondary_conversion_rates']:
        expected_secondary = round((secondary_conversions / num_sessions) * 100, 2)
        actual_secondary = result['secondary_conversion_rates']['Newsletter Signup']
        assert abs(actual_secondary - expected_secondary) < 0.1, \
            f"Secondary rate mismatch: expected {expected_secondary}, got {actual_secondary}"


# Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
@given(
    num_sessions=st.integers(min_value=10, max_value=500),
    num_elements=st.integers(min_value=1, max_value=5)
)
def test_ctr_across_multiple_elements(num_sessions, num_elements):
    """
    Property 15: CTR is calculated consistently across multiple page elements.
    """
    # Generate funnel data with multiple elements
    data = []
    element_names = [f'element_{i}' for i in range(num_elements)]
    
    for i in range(num_sessions):
        session_id = f'sess_{i}'
        data.append({
            'session_id': session_id,
            'funnel_step': 'Visit'
        })
        
        # Each element has different CTR
        for j, element in enumerate(element_names):
            # Vary CTR by element index
            ctr = 0.1 * (j + 1)  # 10%, 20%, 30%, etc.
            num_clicks = int(num_sessions * ctr)
            
            if i < num_clicks:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'page_element': element,
                    'click_event': 1
                })
            else:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'page_element': element,
                    'click_event': 0
                })
    
    df = pd.DataFrame(data)
    result = calculate_cro_metrics(df)
    
    # Verify CTR for each element
    for j, element in enumerate(element_names):
        expected_ctr = round((int(num_sessions * 0.1 * (j + 1)) / num_sessions) * 100, 2)
        
        if element in result['ctr_by_element']:
            actual_ctr = result['ctr_by_element'][element]
            assert abs(actual_ctr - expected_ctr) < 0.1, \
                f"CTR for {element} mismatch: expected {expected_ctr}, got {actual_ctr}"


# Feature: cro-analytics-enhancement, Property 15: Conversion Rate Calculation Consistency
@given(
    num_sessions=st.integers(min_value=10, max_value=500),
    date_filter_ratio=st.floats(min_value=0.1, max_value=0.9)
)
def test_conversion_rate_with_date_filtering(num_sessions, date_filter_ratio):
    """
    Property 15: Conversion rates are calculated consistently with date range filtering.
    """
    # Generate funnel data with dates
    data = []
    
    for i in range(num_sessions):
        session_id = f'sess_{i}'
        date = f'2024-01-{(i % 28) + 1:02d}'
        
        data.append({
            'session_id': session_id,
            'funnel_step': 'Visit',
            'date': date
        })
        
        # 30% conversion rate
        if i < int(num_sessions * 0.3):
            data.append({
                'session_id': session_id,
                'funnel_step': 'Purchase',
                'date': date
            })
    
    df = pd.DataFrame(data)
    
    # Filter to first portion of sessions (not by date, but by session index)
    filter_point = int(num_sessions * date_filter_ratio)
    filtered_sessions = [f'sess_{i}' for i in range(filter_point)]
    
    # Manually filter the dataframe
    filtered_df = df[df['session_id'].isin(filtered_sessions)]
    
    result = calculate_cro_metrics(filtered_df)
    
    # Verify conversion rate is calculated on filtered data
    # Count actual conversions in filtered data
    filtered_primary = filtered_df[filtered_df['funnel_step'] == 'Purchase']['session_id'].nunique()
    filtered_total = filtered_df['session_id'].nunique()
    
    if filtered_total > 0:
        expected_rate = round((filtered_primary / filtered_total) * 100, 2)
        assert abs(result['primary_conversion_rate'] - expected_rate) < 0.1, \
            f"Filtered conversion rate mismatch: expected {expected_rate}, got {result['primary_conversion_rate']}"
