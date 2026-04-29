"""
Property-based tests for statistical power calculator.

This module tests properties of the calculate_power() function:
- Property 11: Power Monotonicity with Sample Size
- Property 12: Error Rate Relationships

**Validates: Requirements 5.1, 5.5, 5.6**
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from scipy import stats
from analytics.conversion import calculate_power


# Feature: cro-analytics-enhancement, Property 11: Power Monotonicity with Sample Size
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    effect_size=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    sample_size_1=st.integers(min_value=100, max_value=50000),
    sample_size_2=st.integers(min_value=100, max_value=50000),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_power_monotonicity_with_sample_size(baseline_cvr, effect_size, sample_size_1, sample_size_2, alpha):
    """
    Property 11: For any fixed baseline conversion rate, effect size, and significance level,
    as sample size increases, statistical power SHALL increase monotonically.
    
    **Validates: Requirements 5.1**
    """
    # Ensure target CVR doesn't exceed 1.0
    target_cvr = baseline_cvr * (1 + effect_size)
    assume(target_cvr <= 1.0)
    
    # Ensure we have two different sample sizes
    assume(sample_size_1 != sample_size_2)
    
    # Determine which is larger
    smaller_sample = min(sample_size_1, sample_size_2)
    larger_sample = max(sample_size_1, sample_size_2)
    
    # Calculate power for both sample sizes
    result_small = calculate_power(baseline_cvr, effect_size, smaller_sample, alpha)
    result_large = calculate_power(baseline_cvr, effect_size, larger_sample, alpha)
    
    # Power should increase with larger sample size
    assert result_large['power'] >= result_small['power'], \
        f"Power should increase with sample size. " \
        f"Small sample ({smaller_sample}): {result_small['power']:.4f}, " \
        f"Large sample ({larger_sample}): {result_large['power']:.4f}"
    
    # power_pct should also increase
    assert result_large['power_pct'] >= result_small['power_pct'], \
        f"Power percentage should increase with sample size. " \
        f"Small sample ({smaller_sample}): {result_small['power_pct']:.2f}%, " \
        f"Large sample ({larger_sample}): {result_large['power_pct']:.2f}%"


# Feature: cro-analytics-enhancement, Property 12: Error Rate Relationships
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    effect_size=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    sample_size=st.integers(min_value=100, max_value=100000),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_error_rate_relationships(baseline_cvr, effect_size, sample_size, alpha):
    """
    Property 12: For any power calculation, Type I error (alpha) SHALL equal the
    significance level, and Type II error (beta) SHALL equal 1 minus the statistical power.
    
    **Validates: Requirements 5.5, 5.6**
    """
    # Ensure target CVR doesn't exceed 1.0
    target_cvr = baseline_cvr * (1 + effect_size)
    assume(target_cvr <= 1.0)
    
    result = calculate_power(baseline_cvr, effect_size, sample_size, alpha)
    
    # Type I error (alpha) should equal the significance level
    assert result['alpha'] == alpha, \
        f"Type I error (alpha) should equal significance level. " \
        f"Expected: {alpha}, Got: {result['alpha']}"
    
    # Type II error (beta) should equal 1 - power
    expected_beta = 1 - result['power']
    assert abs(result['beta'] - expected_beta) < 1e-10, \
        f"Type II error (beta) should equal 1 - power. " \
        f"Expected: {expected_beta:.10f}, Got: {result['beta']:.10f}"
    
    # Verify that alpha + beta is not necessarily 1 (they're independent)
    # But verify that both are valid probabilities
    assert 0 <= result['alpha'] <= 1, \
        f"Type I error (alpha) should be between 0 and 1. Got: {result['alpha']}"
    assert 0 <= result['beta'] <= 1, \
        f"Type II error (beta) should be between 0 and 1. Got: {result['beta']}"
    
    # Verify power is between 0 and 1
    assert 0 <= result['power'] <= 1, \
        f"Power should be between 0 and 1. Got: {result['power']}"
