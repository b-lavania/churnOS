"""
Property-based tests for MDE analyzer.

This module tests properties of the calculate_mde() function:
- Property 8: MDE-Sample Size Inverse Relationship
- Property 9: MDE Dual Representation Consistency
- Property 10: MDE Monotonicity with Sample Size

**Validates: Requirements 4.1, 4.2, 4.6**
"""

import pytest
from hypothesis import given, strategies as st, assume
import numpy as np
from scipy import stats
from analytics.conversion import calculate_mde, calculate_sample_size


# Feature: cro-analytics-enhancement, Property 8: MDE-Sample Size Inverse Relationship
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.70, max_value=0.90, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.10, allow_nan=False, allow_infinity=False)
)
def test_mde_sample_size_inverse_relationship(baseline_cvr, mde, power, alpha):
    """
    Property 8: For any baseline conversion rate, statistical power, and significance level,
    calculating the sample size for a given MDE and then calculating the MDE for that sample
    size SHALL return the original MDE within numerical precision tolerance (round-trip property).
    
    **Validates: Requirements 4.1, 4.6**
    """
    # Ensure target CVR doesn't exceed 1.0
    target_cvr = baseline_cvr * (1 + mde)
    assume(target_cvr <= 1.0)
    
    # Step 1: Calculate sample size for given MDE
    ss_result = calculate_sample_size(baseline_cvr, mde, power, alpha)
    sample_size = ss_result['sample_size_per_variant']
    
    # Step 2: Calculate MDE for that sample size
    mde_result = calculate_mde(baseline_cvr, sample_size, power, alpha)
    
    # Step 3: Verify round-trip property
    # The calculated MDE should match the original MDE within tolerance
    # Use relative tolerance of 2% to account for numerical precision
    # (especially for edge cases with high baseline CVR and large MDE)
    tolerance = 0.02
    
    if mde > 0:
        relative_error = abs(mde_result['mde_relative'] - mde) / mde
        assert relative_error < tolerance, \
            f"Round-trip failed: original MDE={mde}, calculated MDE={mde_result['mde_relative']}, " \
            f"relative error={relative_error:.4f}"
    else:
        # If MDE is very small, use absolute tolerance
        assert abs(mde_result['mde_relative'] - mde) < 1e-6, \
            f"Round-trip failed for small MDE: original={mde}, calculated={mde_result['mde_relative']}"


# Feature: cro-analytics-enhancement, Property 9: MDE Dual Representation Consistency
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    sample_size_per_variant=st.integers(min_value=100, max_value=100000),
    power=st.floats(min_value=0.50, max_value=0.99, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_mde_dual_representation_consistency(baseline_cvr, sample_size_per_variant, power, alpha):
    """
    Property 9: For any calculated MDE, the absolute MDE (in percentage points) SHALL equal
    the baseline conversion rate multiplied by the relative MDE (as a decimal), ensuring both
    representations are mathematically consistent.
    
    **Validates: Requirements 4.2**
    """
    result = calculate_mde(baseline_cvr, sample_size_per_variant, power, alpha)
    
    # Verify: absolute_mde = baseline_cvr * relative_mde
    expected_absolute = result['baseline_cvr'] * result['mde_relative']
    
    # Allow for small numerical precision differences
    assert abs(result['mde_absolute'] - expected_absolute) < 1e-10, \
        f"Dual representation inconsistency: " \
        f"absolute={result['mde_absolute']}, " \
        f"baseline * relative={expected_absolute}"
    
    # Verify: target_cvr = baseline_cvr + absolute_mde
    expected_target = result['baseline_cvr'] + result['mde_absolute']
    assert abs(result['target_cvr'] - expected_target) < 1e-10, \
        f"Target CVR inconsistency: " \
        f"target={result['target_cvr']}, " \
        f"baseline + absolute={expected_target}"
    
    # Verify: target_cvr = baseline_cvr * (1 + relative_mde)
    expected_target_from_relative = result['baseline_cvr'] * (1 + result['mde_relative'])
    assert abs(result['target_cvr'] - expected_target_from_relative) < 1e-10, \
        f"Target CVR from relative MDE inconsistency: " \
        f"target={result['target_cvr']}, " \
        f"baseline * (1 + relative)={expected_target_from_relative}"


# Feature: cro-analytics-enhancement, Property 10: MDE Monotonicity with Sample Size
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=0.95, allow_nan=False, allow_infinity=False),
    sample_size_1=st.integers(min_value=100, max_value=50000),
    sample_size_2=st.integers(min_value=50001, max_value=100000),
    power=st.floats(min_value=0.50, max_value=0.99, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_mde_monotonicity_with_sample_size(baseline_cvr, sample_size_1, sample_size_2, power, alpha):
    """
    Property 10: For any fixed baseline conversion rate, statistical power, and significance level,
    as sample size increases, the minimum detectable effect SHALL decrease (larger samples can
    detect smaller effects).
    
    **Validates: Requirements 4.1**
    """
    # Ensure sample_size_1 < sample_size_2
    assume(sample_size_1 < sample_size_2)
    
    # Calculate MDE for smaller sample size
    result_small = calculate_mde(baseline_cvr, sample_size_1, power, alpha)
    
    # Calculate MDE for larger sample size
    result_large = calculate_mde(baseline_cvr, sample_size_2, power, alpha)
    
    # Verify monotonicity: larger sample should have smaller MDE
    assert result_large['mde_relative'] < result_small['mde_relative'], \
        f"MDE not monotonically decreasing with sample size: " \
        f"sample_size_1={sample_size_1}, MDE_1={result_small['mde_relative']}, " \
        f"sample_size_2={sample_size_2}, MDE_2={result_large['mde_relative']}"
    
    assert result_large['mde_absolute'] < result_small['mde_absolute'], \
        f"Absolute MDE not monotonically decreasing with sample size: " \
        f"sample_size_1={sample_size_1}, MDE_1={result_small['mde_absolute']}, " \
        f"sample_size_2={sample_size_2}, MDE_2={result_large['mde_absolute']}"
    
    # Verify target CVR is also monotonically decreasing
    assert result_large['target_cvr'] < result_small['target_cvr'], \
        f"Target CVR not monotonically decreasing with sample size: " \
        f"sample_size_1={sample_size_1}, target_1={result_small['target_cvr']}, " \
        f"sample_size_2={sample_size_2}, target_2={result_large['target_cvr']}"
