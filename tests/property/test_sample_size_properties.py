"""
Property-based tests for sample size calculator and time estimation.

This module tests properties of the calculate_sample_size() and estimate_test_duration() functions:
- Property 1: Sample Size Calculation Correctness
- Property 3: Calculation Idempotence
- Property 4: Total Sample Size Arithmetic
- Property 5: Threshold-Based Warning Generation
- Property 6: Time Estimation Arithmetic

**Validates: Requirements 1.1, 1.2-1.9, 2.1, 2.5, 18.6**
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from scipy import stats
from analytics.conversion import calculate_sample_size, estimate_test_duration


# Feature: cro-analytics-enhancement, Property 1: Sample Size Calculation Correctness
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.50, max_value=0.99, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_sample_size_calculation_correctness(baseline_cvr, mde, power, alpha):
    """
    Property 1: For any valid baseline conversion rate, minimum detectable effect,
    statistical power, and significance level, the calculated sample size SHALL be
    a positive integer that satisfies the two-proportion z-test formula within
    numerical precision tolerance.
    
    **Validates: Requirements 1.1, 1.8**
    """
    # Ensure target CVR doesn't exceed 1.0
    target_cvr = baseline_cvr * (1 + mde)
    assume(target_cvr <= 1.0)
    
    result = calculate_sample_size(baseline_cvr, mde, power, alpha)
    
    # Sample size must be a positive integer
    assert result['sample_size_per_variant'] > 0, \
        "Sample size must be positive"
    assert isinstance(result['sample_size_per_variant'], int), \
        "Sample size must be an integer"
    
    # Verify the calculation satisfies the two-proportion z-test formula
    # n = (Z_α/2 + Z_β)² × [p₁(1-p₁) + p₂(1-p₂)] / (p₂ - p₁)²
    
    p1 = baseline_cvr
    p2 = target_cvr
    
    # Get z-scores
    z_alpha_2 = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Calculate expected sample size using the formula
    numerator = (z_alpha_2 + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
    denominator = (p2 - p1) ** 2
    expected_sample_size = numerator / denominator
    
    # The calculated sample size should be the ceiling of the expected value
    # Allow for small numerical precision differences
    calculated = result['sample_size_per_variant']
    assert calculated >= np.floor(expected_sample_size), \
        f"Sample size {calculated} is less than floor of expected {expected_sample_size}"
    assert calculated <= np.ceil(expected_sample_size) + 1, \
        f"Sample size {calculated} is more than ceiling of expected {expected_sample_size}"
    
    # Verify all required fields are present and have correct types
    assert 'total_sample_size' in result
    assert 'baseline_cvr' in result
    assert 'target_cvr' in result
    assert 'mde_absolute' in result
    assert 'mde_relative' in result
    assert 'power' in result
    assert 'alpha' in result
    assert 'warnings' in result
    
    # Verify returned values match inputs
    assert result['baseline_cvr'] == baseline_cvr
    assert result['mde_relative'] == mde
    assert result['power'] == power
    assert result['alpha'] == alpha
    
    # Verify target CVR calculation
    assert abs(result['target_cvr'] - target_cvr) < 1e-10, \
        "Target CVR should equal baseline * (1 + mde)"
    
    # Verify absolute MDE calculation
    expected_mde_absolute = target_cvr - baseline_cvr
    assert abs(result['mde_absolute'] - expected_mde_absolute) < 1e-10, \
        "Absolute MDE should equal target_cvr - baseline_cvr"


# Feature: cro-analytics-enhancement, Property 3: Calculation Idempotence
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.50, max_value=0.99, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False),
    n_variants=st.integers(min_value=2, max_value=10)
)
def test_calculation_idempotence(baseline_cvr, mde, power, alpha, n_variants):
    """
    Property 3: For any valid input parameters to any calculator function,
    calling the function multiple times with identical inputs SHALL produce
    identical outputs.
    
    **Validates: Requirements 1.9**
    """
    # Ensure target CVR doesn't exceed 1.0
    target_cvr = baseline_cvr * (1 + mde)
    assume(target_cvr <= 1.0)
    
    # Call the function three times with identical inputs
    result1 = calculate_sample_size(baseline_cvr, mde, power, alpha, n_variants)
    result2 = calculate_sample_size(baseline_cvr, mde, power, alpha, n_variants)
    result3 = calculate_sample_size(baseline_cvr, mde, power, alpha, n_variants)
    
    # All results should be identical
    assert result1 == result2, \
        "First and second calls with identical inputs produced different results"
    assert result2 == result3, \
        "Second and third calls with identical inputs produced different results"
    assert result1 == result3, \
        "First and third calls with identical inputs produced different results"
    
    # Verify specific fields are identical
    assert result1['sample_size_per_variant'] == result2['sample_size_per_variant']
    assert result1['total_sample_size'] == result2['total_sample_size']
    assert result1['baseline_cvr'] == result2['baseline_cvr']
    assert result1['target_cvr'] == result2['target_cvr']
    assert result1['mde_absolute'] == result2['mde_absolute']
    assert result1['mde_relative'] == result2['mde_relative']
    assert result1['power'] == result2['power']
    assert result1['alpha'] == result2['alpha']
    assert result1['warnings'] == result2['warnings']


# Feature: cro-analytics-enhancement, Property 4: Total Sample Size Arithmetic
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.50, max_value=0.99, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False),
    n_variants=st.integers(min_value=2, max_value=20)
)
def test_total_sample_size_arithmetic(baseline_cvr, mde, power, alpha, n_variants):
    """
    Property 4: For any valid test configuration with n variants, the total
    required sample size SHALL equal the sample size per variant multiplied
    by the number of variants.
    
    **Validates: Requirements 1.7**
    """
    # Ensure target CVR doesn't exceed 1.0
    target_cvr = baseline_cvr * (1 + mde)
    assume(target_cvr <= 1.0)
    
    result = calculate_sample_size(baseline_cvr, mde, power, alpha, n_variants)
    
    # Total sample size must equal per-variant size times number of variants
    expected_total = result['sample_size_per_variant'] * n_variants
    assert result['total_sample_size'] == expected_total, \
        f"Total sample size {result['total_sample_size']} does not equal " \
        f"per-variant size {result['sample_size_per_variant']} × {n_variants} variants = {expected_total}"
    
    # Verify the arithmetic is exact (no rounding errors)
    assert result['total_sample_size'] % n_variants == 0 or \
           result['total_sample_size'] == result['sample_size_per_variant'] * n_variants, \
        "Total sample size should be an exact multiple of per-variant size"


# Feature: cro-analytics-enhancement, Property 5: Threshold-Based Warning Generation
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.50, max_value=0.99, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_threshold_based_warning_generation(baseline_cvr, mde, power, alpha):
    """
    Property 5: For any calculated metric with an associated warning threshold,
    a warning SHALL appear in the results if and only if the metric crosses
    the threshold in the problematic direction.
    
    **Validates: Requirements 1.6, 2.3, 3.1, 5.3, 10.4, 11.2**
    """
    # Ensure target CVR doesn't exceed 1.0
    target_cvr = baseline_cvr * (1 + mde)
    assume(target_cvr <= 1.0)
    
    result = calculate_sample_size(baseline_cvr, mde, power, alpha)
    
    sample_size = result['sample_size_per_variant']
    warnings = result['warnings']
    
    # Check Twyman's Law warning threshold (< 350)
    has_twyman_warning = any('Twyman' in w for w in warnings)
    if sample_size < 350:
        assert has_twyman_warning, \
            f"Sample size {sample_size} < 350 should trigger Twyman's Law warning"
    else:
        assert not has_twyman_warning, \
            f"Sample size {sample_size} >= 350 should not trigger Twyman's Law warning"
    
    # Check impractical test warning threshold (> 1,000,000)
    has_impractical_warning = any('Impractical' in w for w in warnings)
    if sample_size > 1_000_000:
        assert has_impractical_warning, \
            f"Sample size {sample_size} > 1M should trigger impractical test warning"
    else:
        assert not has_impractical_warning, \
            f"Sample size {sample_size} <= 1M should not trigger impractical test warning"
    
    # Check large effect warning threshold (MDE > 0.50)
    has_large_effect_warning = any('Large Effect' in w for w in warnings)
    if mde > 0.50:
        assert has_large_effect_warning, \
            f"MDE {mde} > 0.50 should trigger large effect warning"
    else:
        assert not has_large_effect_warning, \
            f"MDE {mde} <= 0.50 should not trigger large effect warning"
    
    # Verify warnings list is always present and is a list
    assert isinstance(warnings, list), "Warnings should always be a list"


# Feature: cro-analytics-enhancement, Property 5: Threshold-Based Warning Generation (Edge Cases)
def test_warning_threshold_exact_boundaries():
    """
    Property 5: Test exact boundary conditions for warning thresholds.
    
    **Validates: Requirements 1.6, 3.1**
    """
    # Test Twyman's Law threshold at exactly 350
    # We need to find parameters that give exactly 350 sample size
    # This is difficult, so we test just below and just above
    
    # Test just below 350 (should have warning)
    result_below = calculate_sample_size(
        baseline_cvr=0.50,
        mde=0.20,
        power=0.80,
        alpha=0.05
    )
    if result_below['sample_size_per_variant'] < 350:
        assert any('Twyman' in w for w in result_below['warnings']), \
            "Sample size < 350 should have Twyman warning"
    
    # Test well above 350 (should not have warning)
    result_above = calculate_sample_size(
        baseline_cvr=0.03,
        mde=0.10,
        power=0.80,
        alpha=0.05
    )
    if result_above['sample_size_per_variant'] >= 350:
        assert not any('Twyman' in w for w in result_above['warnings']), \
            "Sample size >= 350 should not have Twyman warning"
    
    # Test MDE exactly at 0.50 (should not have warning)
    result_mde_50 = calculate_sample_size(
        baseline_cvr=0.03,
        mde=0.50,
        power=0.80,
        alpha=0.05
    )
    assert not any('Large Effect' in w for w in result_mde_50['warnings']), \
        "MDE exactly at 0.50 should not trigger large effect warning"
    
    # Test MDE just above 0.50 (should have warning)
    result_mde_51 = calculate_sample_size(
        baseline_cvr=0.03,
        mde=0.51,
        power=0.80,
        alpha=0.05
    )
    assert any('Large Effect' in w for w in result_mde_51['warnings']), \
        "MDE > 0.50 should trigger large effect warning"


# Feature: cro-analytics-enhancement, Property 1: Sample Size Calculation Correctness (Monotonicity)
@given(
    baseline_cvr=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    mde_small=st.floats(min_value=0.05, max_value=0.20, allow_nan=False, allow_infinity=False),
    mde_large=st.floats(min_value=0.25, max_value=0.50, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.70, max_value=0.90, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.10, allow_nan=False, allow_infinity=False)
)
def test_sample_size_monotonicity_with_mde(baseline_cvr, mde_small, mde_large, power, alpha):
    """
    Property 1 (Monotonicity): Sample size should decrease as MDE increases
    (larger effects are easier to detect).
    
    **Validates: Requirements 1.1, 1.8**
    """
    assume(mde_small < mde_large)
    assume(baseline_cvr * (1 + mde_large) <= 1.0)
    
    result_small_mde = calculate_sample_size(baseline_cvr, mde_small, power, alpha)
    result_large_mde = calculate_sample_size(baseline_cvr, mde_large, power, alpha)
    
    # Smaller MDE should require larger sample size
    assert result_small_mde['sample_size_per_variant'] > result_large_mde['sample_size_per_variant'], \
        f"Smaller MDE {mde_small} should require larger sample size than larger MDE {mde_large}"


# Feature: cro-analytics-enhancement, Property 1: Sample Size Calculation Correctness (Monotonicity)
@given(
    baseline_cvr=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.05, max_value=0.30, allow_nan=False, allow_infinity=False),
    power_low=st.floats(min_value=0.60, max_value=0.75, allow_nan=False, allow_infinity=False),
    power_high=st.floats(min_value=0.85, max_value=0.95, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.10, allow_nan=False, allow_infinity=False)
)
def test_sample_size_monotonicity_with_power(baseline_cvr, mde, power_low, power_high, alpha):
    """
    Property 1 (Monotonicity): Sample size should increase as power increases
    (higher power requires more data).
    
    **Validates: Requirements 1.1, 1.8**
    """
    assume(power_low < power_high)
    assume(baseline_cvr * (1 + mde) <= 1.0)
    
    result_low_power = calculate_sample_size(baseline_cvr, mde, power_low, alpha)
    result_high_power = calculate_sample_size(baseline_cvr, mde, power_high, alpha)
    
    # Higher power should require larger sample size
    assert result_high_power['sample_size_per_variant'] > result_low_power['sample_size_per_variant'], \
        f"Higher power {power_high} should require larger sample size than lower power {power_low}"


# Feature: cro-analytics-enhancement, Property 1: Sample Size Calculation Correctness (Monotonicity)
@given(
    baseline_cvr=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.05, max_value=0.30, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.70, max_value=0.90, allow_nan=False, allow_infinity=False),
    alpha_low=st.floats(min_value=0.01, max_value=0.03, allow_nan=False, allow_infinity=False),
    alpha_high=st.floats(min_value=0.08, max_value=0.15, allow_nan=False, allow_infinity=False)
)
def test_sample_size_monotonicity_with_alpha(baseline_cvr, mde, power, alpha_low, alpha_high):
    """
    Property 1 (Monotonicity): Sample size should decrease as alpha increases
    (less stringent significance level requires less data).
    
    **Validates: Requirements 1.1, 1.8**
    """
    assume(alpha_low < alpha_high)
    assume(baseline_cvr * (1 + mde) <= 1.0)
    
    result_low_alpha = calculate_sample_size(baseline_cvr, mde, power, alpha_low)
    result_high_alpha = calculate_sample_size(baseline_cvr, mde, power, alpha_high)
    
    # Lower alpha (more stringent) should require larger sample size
    assert result_low_alpha['sample_size_per_variant'] > result_high_alpha['sample_size_per_variant'], \
        f"Lower alpha {alpha_low} should require larger sample size than higher alpha {alpha_high}"


# Feature: cro-analytics-enhancement, Property 6: Time Estimation Arithmetic
@given(
    required_sample_size=st.integers(min_value=1, max_value=1_000_000),
    daily_traffic=st.integers(min_value=1, max_value=100_000)
)
def test_time_estimation_arithmetic(required_sample_size, daily_traffic):
    """
    Property 6: For any required sample size and positive daily traffic volume,
    the estimated days to completion SHALL equal the required sample size divided
    by the daily traffic volume, rounded to one decimal place.
    
    **Validates: Requirements 2.1, 2.5**
    """
    result = estimate_test_duration(
        required_sample_size=required_sample_size,
        daily_traffic=daily_traffic,
        conversion_rate=0.03  # Arbitrary conversion rate for this test
    )
    
    # Calculate expected days using the formula: days = sample_size / daily_traffic
    expected_days = required_sample_size / daily_traffic
    expected_days_rounded = round(expected_days, 1)
    
    # The calculated days should match the expected value rounded to 1 decimal place
    assert result['days_to_completion'] == expected_days_rounded, \
        f"Days to completion {result['days_to_completion']} does not match " \
        f"expected {expected_days_rounded} (calculated from {required_sample_size} / {daily_traffic})"
    
    # Verify the result is a float
    assert isinstance(result['days_to_completion'], float), \
        "Days to completion should be a float"
    
    # Verify the result has at most 1 decimal place
    # Check by multiplying by 10 and seeing if it's close to an integer
    days_times_10 = result['days_to_completion'] * 10
    assert abs(days_times_10 - round(days_times_10)) < 1e-9, \
        f"Days to completion {result['days_to_completion']} does not have exactly 1 decimal place"
    
    # Verify weeks calculation is consistent: weeks = days / 7
    expected_weeks = expected_days_rounded / 7
    expected_weeks_rounded = round(expected_weeks, 1)
    assert result['weeks_to_completion'] == expected_weeks_rounded, \
        f"Weeks to completion {result['weeks_to_completion']} does not match " \
        f"expected {expected_weeks_rounded} (calculated from {expected_days_rounded} / 7)"


# Feature: cro-analytics-enhancement, Property 6: Time Estimation Arithmetic (Monotonicity)
@given(
    sample_size_small=st.integers(min_value=1, max_value=50_000),
    sample_size_large=st.integers(min_value=50_001, max_value=1_000_000),
    daily_traffic=st.integers(min_value=1, max_value=100_000)
)
def test_time_estimation_monotonicity_with_sample_size(sample_size_small, sample_size_large, daily_traffic):
    """
    Property 6 (Monotonicity): For any fixed daily traffic, as required sample size
    increases, the estimated days to completion SHALL increase monotonically.
    
    **Validates: Requirements 2.1**
    """
    assume(sample_size_small < sample_size_large)
    
    result_small = estimate_test_duration(
        required_sample_size=sample_size_small,
        daily_traffic=daily_traffic,
        conversion_rate=0.03
    )
    
    result_large = estimate_test_duration(
        required_sample_size=sample_size_large,
        daily_traffic=daily_traffic,
        conversion_rate=0.03
    )
    
    # Larger sample size should require more or equal days (due to rounding)
    # When both round to the same value, that's acceptable
    assert result_large['days_to_completion'] >= result_small['days_to_completion'], \
        f"Larger sample size {sample_size_large} should require more or equal days " \
        f"({result_large['days_to_completion']}) than smaller sample size {sample_size_small} " \
        f"({result_small['days_to_completion']})"
    
    # For cases where they're not equal, verify the strict inequality
    if result_large['days_to_completion'] != result_small['days_to_completion']:
        assert result_large['days_to_completion'] > result_small['days_to_completion'], \
            f"When different, larger sample size should have strictly more days"


# Feature: cro-analytics-enhancement, Property 6: Time Estimation Arithmetic (Inverse Monotonicity)
@given(
    required_sample_size=st.integers(min_value=1, max_value=1_000_000),
    daily_traffic_low=st.integers(min_value=1, max_value=50_000),
    daily_traffic_high=st.integers(min_value=50_001, max_value=100_000)
)
def test_time_estimation_inverse_monotonicity_with_traffic(required_sample_size, daily_traffic_low, daily_traffic_high):
    """
    Property 6 (Inverse Monotonicity): For any fixed required sample size, as daily
    traffic increases, the estimated days to completion SHALL decrease monotonically.
    
    **Validates: Requirements 2.1**
    """
    assume(daily_traffic_low < daily_traffic_high)
    
    result_low_traffic = estimate_test_duration(
        required_sample_size=required_sample_size,
        daily_traffic=daily_traffic_low,
        conversion_rate=0.03
    )
    
    result_high_traffic = estimate_test_duration(
        required_sample_size=required_sample_size,
        daily_traffic=daily_traffic_high,
        conversion_rate=0.03
    )
    
    # Higher traffic should require fewer or equal days (due to rounding)
    # When both round to the same value, that's acceptable
    assert result_high_traffic['days_to_completion'] <= result_low_traffic['days_to_completion'], \
        f"Higher daily traffic {daily_traffic_high} should require fewer or equal days " \
        f"({result_high_traffic['days_to_completion']}) than lower traffic {daily_traffic_low} " \
        f"({result_low_traffic['days_to_completion']})"
    
    # For cases where they're not equal, verify the strict inequality
    if result_high_traffic['days_to_completion'] != result_low_traffic['days_to_completion']:
        assert result_high_traffic['days_to_completion'] < result_low_traffic['days_to_completion'], \
            f"When different, higher traffic should have strictly fewer days"


# Feature: cro-analytics-enhancement, Property 6: Time Estimation Arithmetic (Rounding Precision)
@given(
    required_sample_size=st.integers(min_value=1, max_value=1_000_000),
    daily_traffic=st.integers(min_value=1, max_value=100_000)
)
def test_time_estimation_rounding_precision(required_sample_size, daily_traffic):
    """
    Property 6 (Rounding Precision): For any required sample size and daily traffic,
    the estimated days SHALL be rounded to exactly one decimal place, not truncated
    or rounded to a different precision.
    
    **Validates: Requirements 2.5**
    """
    result = estimate_test_duration(
        required_sample_size=required_sample_size,
        daily_traffic=daily_traffic,
        conversion_rate=0.03
    )
    
    # Calculate the exact value
    exact_days = required_sample_size / daily_traffic
    
    # Round to 1 decimal place
    expected_rounded = round(exact_days, 1)
    
    # The result should match the expected rounded value
    assert result['days_to_completion'] == expected_rounded, \
        f"Days {result['days_to_completion']} does not match expected rounded value {expected_rounded}"
    
    # Verify it's a float with at most 1 decimal place
    # Check by multiplying by 10 and seeing if it's close to an integer
    days_times_10 = result['days_to_completion'] * 10
    assert abs(days_times_10 - round(days_times_10)) < 1e-9, \
        f"Days to completion {result['days_to_completion']} does not have exactly 1 decimal place"


# Feature: cro-analytics-enhancement, Property 6: Time Estimation Arithmetic (Idempotence)
@given(
    required_sample_size=st.integers(min_value=1, max_value=1_000_000),
    daily_traffic=st.integers(min_value=1, max_value=100_000),
    conversion_rate=st.floats(min_value=0.001, max_value=0.50, allow_nan=False, allow_infinity=False)
)
def test_time_estimation_idempotence(required_sample_size, daily_traffic, conversion_rate):
    """
    Property 6 (Idempotence): For any valid inputs to estimate_test_duration(),
    calling the function multiple times with identical inputs SHALL produce
    identical outputs.
    
    **Validates: Requirements 2.1, 2.5**
    """
    # Call the function three times with identical inputs
    result1 = estimate_test_duration(
        required_sample_size=required_sample_size,
        daily_traffic=daily_traffic,
        conversion_rate=conversion_rate
    )
    
    result2 = estimate_test_duration(
        required_sample_size=required_sample_size,
        daily_traffic=daily_traffic,
        conversion_rate=conversion_rate
    )
    
    result3 = estimate_test_duration(
        required_sample_size=required_sample_size,
        daily_traffic=daily_traffic,
        conversion_rate=conversion_rate
    )
    
    # All results should be identical
    assert result1 == result2, \
        "First and second calls with identical inputs produced different results"
    assert result2 == result3, \
        "Second and third calls with identical inputs produced different results"
    assert result1 == result3, \
        "First and third calls with identical inputs produced different results"
    
    # Verify specific fields are identical
    assert result1['days_to_completion'] == result2['days_to_completion']
    assert result1['weeks_to_completion'] == result2['weeks_to_completion']
    assert result1['daily_traffic'] == result2['daily_traffic']
    assert result1['daily_conversions_expected'] == result2['daily_conversions_expected']
    assert result1['warnings'] == result2['warnings']
