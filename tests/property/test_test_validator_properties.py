"""
Property-based tests for test reliability validator.

Tests the validate_test_reliability() function using property-based testing
to verify universal properties hold across all valid inputs.

**Validates: Requirements 3.3, 11.1-11.7**
"""

import pytest
from hypothesis import given, strategies as st
from analytics.conversion import validate_test_reliability


# ============================================================================
# Property 7: Twyman's Law Compound Condition
# ============================================================================
# For any test result where observed lift exceeds 50% AND sample size per variant
# is less than 1000, the Test_Validator SHALL flag the result as potentially
# unreliable due to Twyman's Law.

@given(
    control_visitors=st.integers(min_value=100, max_value=10000),
    control_conversions=st.integers(min_value=10, max_value=500),
    variant_visitors=st.integers(min_value=100, max_value=10000),
    variant_conversions=st.integers(min_value=10, max_value=500),
    test_duration_days=st.integers(min_value=7, max_value=30),
)
def test_twyman_law_compound_condition(control_visitors, control_conversions, variant_visitors, variant_conversions, test_duration_days):
    """Property 7: Twyman's Law Compound Condition.
    
    For any test where observed lift > 50% AND minimum sample size < 1000,
    the validator should flag Twyman's Law violation.
    
    **Validates: Requirements 3.3**
    """
    # Calculate observed lift
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors
    observed_lift = (variant_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0
    
    # Only test cases where lift > 50%
    if observed_lift > 50:
        min_sample_size = min(control_conversions, variant_conversions)
        
        # If sample size < 1000, Twyman's Law should be violated
        if min_sample_size < 1000:
            result = validate_test_reliability(
                control_visitors=control_visitors,
                control_conversions=control_conversions,
                variant_visitors=variant_visitors,
                variant_conversions=variant_conversions,
                test_duration_days=test_duration_days,
                observed_lift=observed_lift
            )
            
            # Twyman's Law check should fail
            assert result['checks']['twymans_law'] == False
            
            # Should have Twyman's Law warning
            assert any('Twyman' in w for w in result['warnings'])
            
            # Test should be unreliable
            assert result['is_reliable'] == False


# ============================================================================
# Property 21: Test Reliability Score Bounds
# ============================================================================
# For any test validation result, the reliability score SHALL be an integer
# between 0 and 100 inclusive, and SHALL increase monotonically as more
# reliability checks pass.

@given(
    control_visitors=st.integers(min_value=100, max_value=20000),
    control_conversions=st.integers(min_value=10, max_value=1000),
    variant_visitors=st.integers(min_value=100, max_value=20000),
    variant_conversions=st.integers(min_value=10, max_value=1000),
    test_duration_days=st.integers(min_value=1, max_value=30),
)
def test_reliability_score_bounds(control_visitors, control_conversions, variant_visitors, variant_conversions, test_duration_days):
    """Property 21: Test Reliability Score Bounds.
    
    For any test validation result, the reliability score should be an integer
    between 0 and 100 inclusive.
    
    **Validates: Requirements 11.7**
    """
    # Calculate observed lift
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors
    observed_lift = (variant_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0
    
    result = validate_test_reliability(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        test_duration_days=test_duration_days,
        observed_lift=observed_lift
    )
    
    # Score should be an integer between 0 and 100
    assert isinstance(result['reliability_score'], int)
    assert 0 <= result['reliability_score'] <= 100


@given(
    control_visitors=st.integers(min_value=1000, max_value=20000),
    control_conversions=st.integers(min_value=350, max_value=1000),
    variant_visitors=st.integers(min_value=1000, max_value=20000),
    variant_conversions=st.integers(min_value=350, max_value=1000),
    test_duration_days=st.integers(min_value=14, max_value=30),
)
def test_reliability_score_monotonicity(control_visitors, control_conversions, variant_visitors, variant_conversions, test_duration_days):
    """Property 21: Test Reliability Score Monotonicity.
    
    As more reliability checks pass, the score should increase.
    
    **Validates: Requirements 11.7**
    """
    # Calculate observed lift
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors
    observed_lift = (variant_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0
    
    result = validate_test_reliability(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        test_duration_days=test_duration_days,
        observed_lift=observed_lift
    )
    
    # Calculate expected score based on checks passed
    checks = result['checks']
    expected_score = 0
    expected_score += 30 if checks['minimum_sample_size'] else 0
    expected_score += 25 if checks['minimum_duration'] else 0
    expected_score += 20 if checks['business_cycles'] else 0
    expected_score += 15 if checks['twymans_law'] else 0
    expected_score += 10 if checks['statistical_significance'] else 0
    
    # Score should match expected calculation
    assert result['reliability_score'] == expected_score


# ============================================================================
# Property 22: Reliability Check Completeness
# ============================================================================
# For any test result, the Test_Validator SHALL perform all five reliability
# checks (minimum sample size, minimum duration, business cycles, Twyman's Law,
# statistical significance) and report the status of each check.

@given(
    control_visitors=st.integers(min_value=100, max_value=20000),
    control_conversions=st.integers(min_value=10, max_value=1000),
    variant_visitors=st.integers(min_value=100, max_value=20000),
    variant_conversions=st.integers(min_value=10, max_value=1000),
    test_duration_days=st.integers(min_value=1, max_value=30),
)
def test_reliability_check_completeness(control_visitors, control_conversions, variant_visitors, variant_conversions, test_duration_days):
    """Property 22: Reliability Check Completeness.
    
    The validator should perform all five reliability checks and report
    the status of each check.
    
    **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**
    """
    # Calculate observed lift
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors
    observed_lift = (variant_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0
    
    result = validate_test_reliability(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        test_duration_days=test_duration_days,
        observed_lift=observed_lift
    )
    
    # All five checks should be present
    assert 'minimum_sample_size' in result['checks']
    assert 'minimum_duration' in result['checks']
    assert 'business_cycles' in result['checks']
    assert 'twymans_law' in result['checks']
    assert 'statistical_significance' in result['checks']
    
    # All checks should be boolean values (True or False)
    for check_name, check_result in result['checks'].items():
        assert check_result in [True, False]


# ============================================================================
# Additional Properties
# ============================================================================

@given(
    control_visitors=st.integers(min_value=100, max_value=20000),
    control_conversions=st.integers(min_value=10, max_value=1000),
    variant_visitors=st.integers(min_value=100, max_value=20000),
    variant_conversions=st.integers(min_value=10, max_value=1000),
    test_duration_days=st.integers(min_value=1, max_value=30),
)
def test_reliability_is_all_checks_pass(control_visitors, control_conversions, variant_visitors, variant_conversions, test_duration_days):
    """Additional Property: is_reliable equals all checks passing.
    
    The test is reliable if and only if all checks pass.
    
    **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**
    """
    # Calculate observed lift
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors
    observed_lift = (variant_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0
    
    result = validate_test_reliability(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        test_duration_days=test_duration_days,
        observed_lift=observed_lift
    )
    
    # is_reliable should equal all checks passing
    all_checks_pass = all(result['checks'].values())
    assert result['is_reliable'] == all_checks_pass


@given(
    control_visitors=st.integers(min_value=100, max_value=20000),
    control_conversions=st.integers(min_value=10, max_value=1000),
    variant_visitors=st.integers(min_value=100, max_value=20000),
    variant_conversions=st.integers(min_value=10, max_value=1000),
    test_duration_days=st.integers(min_value=1, max_value=30),
)
def test_warnings_and_recommendations_present(control_visitors, control_conversions, variant_visitors, variant_conversions, test_duration_days):
    """Additional Property: warnings and recommendations are always lists.
    
    The validator should always return warnings and recommendations as lists,
    even if empty.
    
    **Validates: Requirements 11.6**
    """
    # Calculate observed lift
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors
    observed_lift = (variant_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0
    
    result = validate_test_reliability(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        test_duration_days=test_duration_days,
        observed_lift=observed_lift
    )
    
    # Warnings and recommendations should always be lists
    assert isinstance(result['warnings'], list)
    assert isinstance(result['recommendations'], list)
    
    # Warnings should contain strings
    for warning in result['warnings']:
        assert isinstance(warning, str)
        assert len(warning) > 0
    
    # Recommendations should contain strings
    for recommendation in result['recommendations']:
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0


@given(
    control_visitors=st.integers(min_value=100, max_value=20000),
    control_conversions=st.integers(min_value=10, max_value=1000),
    variant_visitors=st.integers(min_value=100, max_value=20000),
    variant_conversions=st.integers(min_value=10, max_value=1000),
    test_duration_days=st.integers(min_value=1, max_value=30),
)
def test_significance_result_included(control_visitors, control_conversions, variant_visitors, variant_conversions, test_duration_days):
    """Additional Property: significance result is always included.
    
    The validator should always include the significance result in the output.
    
    **Validates: Requirements 11.6**
    """
    # Calculate observed lift
    control_rate = control_conversions / control_visitors
    variant_rate = variant_conversions / variant_visitors
    observed_lift = (variant_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0
    
    result = validate_test_reliability(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        test_duration_days=test_duration_days,
        observed_lift=observed_lift
    )
    
    # Significance result should be included
    assert 'significance_result' in result
    assert 'p_value' in result['significance_result']
    assert 'is_significant' in result['significance_result']
