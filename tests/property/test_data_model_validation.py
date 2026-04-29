"""
Property-based tests for data model validation.

This module tests Property 2: Input Validation Completeness
**Validates: Requirements 1.2, 1.3, 1.4, 1.5, 2.2, 18.1-18.7**
"""

import pytest
from hypothesis import given, strategies as st, assume
from analytics.conversion import TestConfiguration


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=1.0, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.50, max_value=0.99, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False),
    n_variants=st.integers(min_value=2, max_value=10),
    daily_traffic=st.integers(min_value=0, max_value=1000000)
)
def test_valid_inputs_accepted(baseline_cvr, mde, power, alpha, n_variants, daily_traffic):
    """
    Property 2: For any input parameter within valid range, validation SHALL pass.
    
    **Validates: Requirements 1.2, 1.3, 1.4, 1.5, 2.2**
    """
    config = TestConfiguration(
        baseline_cvr=baseline_cvr,
        mde=mde,
        power=power,
        alpha=alpha,
        n_variants=n_variants,
        daily_traffic=daily_traffic
    )
    
    errors = config.validate()
    
    # All inputs are within valid ranges, so no errors should be returned
    assert errors == [], f"Valid inputs produced errors: {errors}"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    baseline_cvr=st.one_of(
        st.floats(max_value=0.0009, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1.001, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
)
def test_invalid_baseline_cvr_rejected(baseline_cvr):
    """
    Property 2: baseline_cvr outside [0.001, 1.0] SHALL raise ValueError.
    
    **Validates: Requirements 1.2, 18.1**
    """
    config = TestConfiguration(
        baseline_cvr=baseline_cvr,
        mde=0.10,
        power=0.80,
        alpha=0.05
    )
    
    errors = config.validate()
    
    # Should have at least one error about baseline_cvr
    assert len(errors) > 0, "Invalid baseline_cvr should produce validation error"
    assert any("baseline_cvr" in error.lower() for error in errors), \
        f"Error should mention baseline_cvr, got: {errors}"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    mde=st.one_of(
        st.floats(max_value=0.009, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1.001, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
)
def test_invalid_mde_rejected(mde):
    """
    Property 2: mde outside [0.01, 1.0] SHALL raise ValueError.
    
    **Validates: Requirements 1.3, 18.2**
    """
    config = TestConfiguration(
        baseline_cvr=0.03,
        mde=mde,
        power=0.80,
        alpha=0.05
    )
    
    errors = config.validate()
    
    # Should have at least one error about mde
    assert len(errors) > 0, "Invalid mde should produce validation error"
    assert any("mde" in error.lower() for error in errors), \
        f"Error should mention mde, got: {errors}"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    power=st.one_of(
        st.floats(max_value=0.49, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.991, max_value=1.5, allow_nan=False, allow_infinity=False)
    )
)
def test_invalid_power_rejected(power):
    """
    Property 2: power outside [0.50, 0.99] SHALL raise ValueError.
    
    **Validates: Requirements 1.4, 18.3**
    """
    config = TestConfiguration(
        baseline_cvr=0.03,
        mde=0.10,
        power=power,
        alpha=0.05
    )
    
    errors = config.validate()
    
    # Should have at least one error about power
    assert len(errors) > 0, "Invalid power should produce validation error"
    assert any("power" in error.lower() for error in errors), \
        f"Error should mention power, got: {errors}"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    alpha=st.one_of(
        st.floats(max_value=0.009, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.201, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
)
def test_invalid_alpha_rejected(alpha):
    """
    Property 2: alpha outside [0.01, 0.20] SHALL raise ValueError.
    
    **Validates: Requirements 1.5, 18.4**
    """
    config = TestConfiguration(
        baseline_cvr=0.03,
        mde=0.10,
        power=0.80,
        alpha=alpha
    )
    
    errors = config.validate()
    
    # Should have at least one error about alpha
    assert len(errors) > 0, "Invalid alpha should produce validation error"
    assert any("alpha" in error.lower() for error in errors), \
        f"Error should mention alpha, got: {errors}"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    n_variants=st.integers(max_value=1)
)
def test_invalid_n_variants_rejected(n_variants):
    """
    Property 2: n_variants < 2 SHALL raise ValueError.
    
    **Validates: Requirements 18.5**
    """
    config = TestConfiguration(
        baseline_cvr=0.03,
        mde=0.10,
        power=0.80,
        alpha=0.05,
        n_variants=n_variants
    )
    
    errors = config.validate()
    
    # Should have at least one error about n_variants
    assert len(errors) > 0, "Invalid n_variants should produce validation error"
    assert any("n_variants" in error.lower() for error in errors), \
        f"Error should mention n_variants, got: {errors}"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    daily_traffic=st.integers(max_value=-1)
)
def test_invalid_daily_traffic_rejected(daily_traffic):
    """
    Property 2: daily_traffic < 0 SHALL raise ValueError.
    
    **Validates: Requirements 2.2, 18.5**
    """
    config = TestConfiguration(
        baseline_cvr=0.03,
        mde=0.10,
        power=0.80,
        alpha=0.05,
        daily_traffic=daily_traffic
    )
    
    errors = config.validate()
    
    # Should have at least one error about daily_traffic
    assert len(errors) > 0, "Invalid daily_traffic should produce validation error"
    assert any("daily_traffic" in error.lower() for error in errors), \
        f"Error should mention daily_traffic, got: {errors}"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    baseline_cvr=st.one_of(
        st.floats(max_value=0.0009, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1.001, max_value=10.0, allow_nan=False, allow_infinity=False)
    ),
    mde=st.one_of(
        st.floats(max_value=0.009, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1.001, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
)
def test_multiple_invalid_inputs_all_reported(baseline_cvr, mde):
    """
    Property 2: Multiple invalid inputs SHALL all be reported in error list.
    
    **Validates: Requirements 18.6, 18.7**
    """
    config = TestConfiguration(
        baseline_cvr=baseline_cvr,
        mde=mde,
        power=0.80,
        alpha=0.05
    )
    
    errors = config.validate()
    
    # Should have at least two errors (one for baseline_cvr, one for mde)
    assert len(errors) >= 2, f"Expected at least 2 errors, got {len(errors)}: {errors}"
    
    # Both parameters should be mentioned
    error_text = " ".join(errors).lower()
    assert "baseline_cvr" in error_text, "baseline_cvr error should be reported"
    assert "mde" in error_text, "mde error should be reported"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
@given(
    baseline_cvr=st.floats(min_value=0.001, max_value=1.0, allow_nan=False, allow_infinity=False),
    mde=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.50, max_value=0.99, allow_nan=False, allow_infinity=False),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_error_messages_include_valid_range(baseline_cvr, mde, power, alpha):
    """
    Property 2: Error messages SHALL include valid range information.
    
    **Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.7**
    """
    # Create an invalid config by using an out-of-range baseline_cvr
    config = TestConfiguration(
        baseline_cvr=1.5,  # Invalid
        mde=mde,
        power=power,
        alpha=alpha
    )
    
    errors = config.validate()
    
    # Error message should mention the valid range
    assert len(errors) > 0, "Should have validation errors"
    baseline_error = [e for e in errors if "baseline_cvr" in e.lower()][0]
    assert "0.001" in baseline_error or "0.1%" in baseline_error, \
        f"Error should mention minimum valid value: {baseline_error}"
    assert "1.0" in baseline_error or "100%" in baseline_error, \
        f"Error should mention maximum valid value: {baseline_error}"


# Feature: cro-analytics-enhancement, Property 2: Input Validation Completeness
def test_boundary_values_accepted():
    """
    Property 2: Boundary values at exact limits SHALL be accepted.
    
    **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    """
    # Test minimum boundary values
    config_min = TestConfiguration(
        baseline_cvr=0.001,
        mde=0.01,
        power=0.50,
        alpha=0.01,
        n_variants=2,
        daily_traffic=0
    )
    assert config_min.validate() == [], "Minimum boundary values should be valid"
    
    # Test maximum boundary values
    config_max = TestConfiguration(
        baseline_cvr=1.0,
        mde=1.0,
        power=0.99,
        alpha=0.20,
        n_variants=100,
        daily_traffic=1000000
    )
    assert config_max.validate() == [], "Maximum boundary values should be valid"
