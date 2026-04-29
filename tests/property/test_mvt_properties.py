"""
Property-based tests for multivariate test planner.

This module tests properties of the plan_multivariate_test() function:
- Property 18: Multivariate Combination Calculation
- Property 19: Multivariate Traffic Split Uniformity
- Property 20: Bonferroni Correction Application

**Validates: Requirements 10.1, 10.3, 10.5**
"""

import pytest
from hypothesis import given, strategies as st, assume
from analytics.conversion import plan_multivariate_test


# Feature: cro-analytics-enhancement, Property 18: Multivariate Combination Calculation
@given(
    n_elements=st.integers(min_value=1, max_value=4),
    n_variations=st.integers(min_value=2, max_value=4)
)
def test_multivariate_combination_calculation(n_elements, n_variations):
    """
    Property 18: For any multivariate test with n elements where element i has v_i variations,
    the total number of combinations SHALL equal the product of all v_i values.
    
    **Validates: Requirements 10.1**
    """
    # Create elements list
    elements = [
        {'name': f'element_{i}', 'n_variations': n_variations}
        for i in range(n_elements)
    ]
    
    # Calculate expected combinations
    expected_combinations = n_variations ** n_elements
    
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=elements
    )
    
    # Total combinations should equal product of all n_variations
    assert result['total_combinations'] == expected_combinations, \
        f"Expected {expected_combinations} combinations, got {result['total_combinations']}"
    
    # Verify the calculation is correct by checking the breakdown
    for element in elements:
        assert f"{element['name']}: {element['n_variations']} variations" in result['combinations_breakdown']


# Feature: cro-analytics-enhancement, Property 18: Multivariate Combination Calculation (Mixed Variations)
@given(
    n_elements=st.integers(min_value=2, max_value=4),
    base_variations=st.integers(min_value=1, max_value=3)
)
def test_multivariate_combination_calculation_mixed_variations(n_elements, base_variations):
    """
    Property 18: Test combination calculation with varying variations per element.
    
    **Validates: Requirements 10.1**
    """
    # Create elements with varying number of variations
    elements = []
    for i in range(n_elements):
        # Each element has a different number of variations
        n_variations = base_variations + i
        elements.append({
            'name': f'element_{i}',
            'n_variations': n_variations
        })
    
    # Calculate expected combinations as product
    expected_combinations = 1
    for element in elements:
        expected_combinations *= element['n_variations']
    
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=elements
    )
    
    # Total combinations should equal product of all n_variations
    assert result['total_combinations'] == expected_combinations, \
        f"Expected {expected_combinations} combinations, got {result['total_combinations']}"


# Feature: cro-analytics-enhancement, Property 18: Multivariate Combination Calculation (Edge Cases)
def test_combination_calculation_edge_cases():
    """
    Property 18: Test edge cases for combination calculation.
    
    **Validates: Requirements 10.1**
    """
    # Single element with two variations (minimum for MVT)
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'element', 'n_variations': 2}
        ]
    )
    assert result['total_combinations'] == 2
    
    # Single element with many variations
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'element', 'n_variations': 10}
        ]
    )
    assert result['total_combinations'] == 10
    
    # Many elements with two variations each
    elements = [{'name': f'element_{i}', 'n_variations': 2} for i in range(3)]
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=elements
    )
    assert result['total_combinations'] == 8  # 2 * 2 * 2


# Feature: cro-analytics-enhancement, Property 19: Multivariate Traffic Split Uniformity
@given(
    n_elements=st.integers(min_value=1, max_value=4),
    n_variations=st.integers(min_value=2, max_value=4)
)
def test_multivariate_traffic_split_uniformity(n_elements, n_variations):
    """
    Property 19: For any multivariate test with n combinations, the traffic split
    percentage for each combination SHALL equal 100/n, and the sum of all traffic
    splits SHALL equal 100%.
    
    **Validates: Requirements 10.3**
    """
    # Create elements list
    elements = [
        {'name': f'element_{i}', 'n_variations': n_variations}
        for i in range(n_elements)
    ]
    
    # Calculate expected combinations and traffic split
    total_combinations = n_variations ** n_elements
    expected_traffic_split = 100 / total_combinations
    
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=elements
    )
    
    # Traffic split should equal 100 / total_combinations
    assert result['traffic_split_pct'] == expected_traffic_split, \
        f"Expected traffic split {expected_traffic_split}, got {result['traffic_split_pct']}"
    
    # Sum of all traffic splits should equal 100%
    sum_of_splits = result['traffic_split_pct'] * total_combinations
    assert abs(sum_of_splits - 100.0) < 1e-9, \
        f"Sum of traffic splits {sum_of_splits} does not equal 100%"


# Feature: cro-analytics-enhancement, Property 19: Multivariate Traffic Split Uniformity (Edge Cases)
def test_traffic_split_edge_cases():
    """
    Property 19: Test edge cases for traffic split calculation.
    
    **Validates: Requirements 10.3**
    """
    # Two combinations (50% each)
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'element', 'n_variations': 2}
        ]
    )
    assert result['traffic_split_pct'] == 50.0
    
    # Four combinations (25% each)
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'a', 'n_variations': 2},
            {'name': 'b', 'n_variations': 2}
        ]
    )
    assert result['traffic_split_pct'] == 25.0
    
    # Eight combinations (12.5% each)
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'a', 'n_variations': 2},
            {'name': 'b', 'n_variations': 2},
            {'name': 'c', 'n_variations': 2}
        ]
    )
    assert result['traffic_split_pct'] == 12.5


# Feature: cro-analytics-enhancement, Property 19: Multivariate Traffic Split Uniformity (Monotonicity)
def test_traffic_split_monotonicity():
    """
    Property 19: Traffic split per combination should decrease as number of combinations increases.
    
    **Validates: Requirements 10.3**
    """
    result_2 = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'element', 'n_variations': 2}
        ]
    )
    
    result_4 = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'a', 'n_variations': 2},
            {'name': 'b', 'n_variations': 2}
        ]
    )
    
    result_8 = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'a', 'n_variations': 2},
            {'name': 'b', 'n_variations': 2},
            {'name': 'c', 'n_variations': 2}
        ]
    )
    
    # More combinations means smaller traffic split per combination
    assert result_2['traffic_split_pct'] > result_4['traffic_split_pct']
    assert result_4['traffic_split_pct'] > result_8['traffic_split_pct']
    
    assert result_2['traffic_split_pct'] == 50.0
    assert result_4['traffic_split_pct'] == 25.0
    assert result_8['traffic_split_pct'] == 12.5


# Feature: cro-analytics-enhancement, Property 20: Bonferroni Correction Application
@given(
    n_elements=st.integers(min_value=1, max_value=4),
    n_variations=st.integers(min_value=2, max_value=4),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_bonferroni_correction_application(n_elements, n_variations, alpha):
    """
    Property 20: For any multivariate test with n combinations and significance level alpha,
    the Bonferroni-corrected significance level SHALL equal alpha divided by n.
    
    **Validates: Requirements 10.5**
    """
    # Create elements list
    elements = [
        {'name': f'element_{i}', 'n_variations': n_variations}
        for i in range(n_elements)
    ]
    
    # Calculate expected combinations and Bonferroni-corrected alpha
    total_combinations = n_variations ** n_elements
    expected_bonferroni_alpha = alpha / total_combinations
    
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=elements,
        alpha=alpha
    )
    
    # Bonferroni-corrected alpha should equal alpha / total_combinations
    assert result['bonferroni_alpha'] == expected_bonferroni_alpha, \
        f"Expected Bonferroni alpha {expected_bonferroni_alpha}, got {result['bonferroni_alpha']}"
    
    # Bonferroni-corrected alpha should always be smaller than original alpha
    assert result['bonferroni_alpha'] < alpha, \
        f"Bonferroni-corrected alpha {result['bonferroni_alpha']} should be smaller than original alpha {alpha}"


# Feature: cro-analytics-enhancement, Property 20: Bonferroni Correction Application (Edge Cases)
def test_bonferroni_correction_edge_cases():
    """
    Property 20: Test edge cases for Bonferroni correction.
    
    **Validates: Requirements 10.5**
    """
    # Two combinations
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'element', 'n_variations': 2}
        ],
        alpha=0.05
    )
    assert result['bonferroni_alpha'] == 0.025  # 0.05 / 2
    
    # Four combinations
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'a', 'n_variations': 2},
            {'name': 'b', 'n_variations': 2}
        ],
        alpha=0.05
    )
    assert result['bonferroni_alpha'] == 0.0125  # 0.05 / 4
    
    # Many combinations
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'a', 'n_variations': 3},
            {'name': 'b', 'n_variations': 3},
            {'name': 'c', 'n_variations': 2}
        ],
        alpha=0.05
    )
    # 3 * 3 * 2 = 18 combinations
    assert result['bonferroni_alpha'] == 0.05 / 18  # ~0.00278


# Feature: cro-analytics-enhancement, Property 20: Bonferroni Correction Application (Monotonicity)
def test_bonferroni_correction_monotonicity():
    """
    Property 20: Bonferroni-corrected alpha should decrease as number of combinations increases.
    
    **Validates: Requirements 10.5**
    """
    result_2 = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'element', 'n_variations': 2}
        ],
        alpha=0.05
    )
    
    result_4 = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'a', 'n_variations': 2},
            {'name': 'b', 'n_variations': 2}
        ],
        alpha=0.05
    )
    
    result_8 = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=[
            {'name': 'a', 'n_variations': 2},
            {'name': 'b', 'n_variations': 2},
            {'name': 'c', 'n_variations': 2}
        ],
        alpha=0.05
    )
    
    # More combinations means smaller Bonferroni-corrected alpha
    assert result_2['bonferroni_alpha'] > result_4['bonferroni_alpha']
    assert result_4['bonferroni_alpha'] > result_8['bonferroni_alpha']
    
    assert result_2['bonferroni_alpha'] == 0.025
    assert result_4['bonferroni_alpha'] == 0.0125
    assert result_8['bonferroni_alpha'] == 0.00625


# Feature: cro-analytics-enhancement, Property 20: Bonferroni Correction Application (Different Alpha Values)
@given(
    n_elements=st.integers(min_value=1, max_value=3),
    n_variations=st.integers(min_value=2, max_value=3),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_bonferroni_correction_with_different_alpha_values(n_elements, n_variations, alpha):
    """
    Property 20: Verify Bonferroni correction works correctly with various alpha values.
    
    **Validates: Requirements 10.5**
    """
    # Create elements list
    elements = [
        {'name': f'element_{i}', 'n_variations': n_variations}
        for i in range(n_elements)
    ]
    
    # Calculate expected combinations
    total_combinations = n_variations ** n_elements
    expected_bonferroni_alpha = alpha / total_combinations
    
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=elements,
        alpha=alpha
    )
    
    # Verify Bonferroni correction
    assert abs(result['bonferroni_alpha'] - expected_bonferroni_alpha) < 1e-10, \
        f"Bonferroni alpha calculation incorrect for alpha={alpha}, combinations={total_combinations}"


# Feature: cro-analytics-enhancement, Property 18-20: Combined Properties
@given(
    n_elements=st.integers(min_value=1, max_value=3),
    n_variations=st.integers(min_value=2, max_value=3),
    alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False)
)
def test_combined_mvt_properties(n_elements, n_variations, alpha):
    """
    Combined test for Properties 18, 19, and 20.
    
    **Validates: Requirements 10.1, 10.3, 10.5**
    """
    # Create elements list
    elements = [
        {'name': f'element_{i}', 'n_variations': n_variations}
        for i in range(n_elements)
    ]
    
    # Calculate expected values
    total_combinations = n_variations ** n_elements
    expected_traffic_split = 100 / total_combinations
    expected_bonferroni_alpha = alpha / total_combinations
    
    result = plan_multivariate_test(
        baseline_cvr=0.03,
        elements=elements,
        alpha=alpha
    )
    
    # Verify all three properties
    assert result['total_combinations'] == total_combinations, \
        "Property 18: Combination calculation incorrect"
    assert result['traffic_split_pct'] == expected_traffic_split, \
        "Property 19: Traffic split calculation incorrect"
    assert result['bonferroni_alpha'] == expected_bonferroni_alpha, \
        "Property 20: Bonferroni correction incorrect"
    
    # Verify sum of traffic splits equals 100%
    assert abs(result['traffic_split_pct'] * total_combinations - 100.0) < 1e-9, \
        "Property 19: Traffic splits do not sum to 100%"
