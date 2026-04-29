"""
Unit tests for multivariate test planner.

Tests the plan_multivariate_test() function to ensure correct combination calculations,
Bonferroni correction application, traffic split calculations, and warning generation.

**Validates: Requirements 10.1-10.6**
"""

import pytest
from analytics.conversion import plan_multivariate_test


class TestCombinationCalculation:
    """Tests for multivariate combination calculation."""
    
    def test_two_elements_two_variations_each(self):
        """Test combination calculation for 2 elements with 2 variations each.
        
        Total combinations = 2 * 2 = 4
        
        **Validates: Requirements 10.1**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'headline', 'n_variations': 2},
                {'name': 'button_color', 'n_variations': 2}
            ]
        )
        
        assert result['total_combinations'] == 4
        assert result['traffic_split_pct'] == 25.0  # 100 / 4
        assert result['bonferroni_alpha'] == 0.0125  # 0.05 / 4
    
    def test_three_elements_two_variations_each(self):
        """Test combination calculation for 3 elements with 2 variations each.
        
        Total combinations = 2 * 2 * 2 = 8
        
        **Validates: Requirements 10.1**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'headline', 'n_variations': 2},
                {'name': 'button_color', 'n_variations': 2},
                {'name': 'image', 'n_variations': 2}
            ]
        )
        
        assert result['total_combinations'] == 8
        assert result['traffic_split_pct'] == 12.5  # 100 / 8
        assert result['bonferroni_alpha'] == 0.00625  # 0.05 / 8
    
    def test_multiple_variations_per_element(self):
        """Test combination calculation with varying variations per element.
        
        Total combinations = 3 * 2 * 4 = 24
        
        **Validates: Requirements 10.1**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'headline', 'n_variations': 3},
                {'name': 'button_color', 'n_variations': 2},
                {'name': 'layout', 'n_variations': 4}
            ]
        )
        
        assert result['total_combinations'] == 24
        assert result['traffic_split_pct'] == 100 / 24  # ~4.17%
        assert result['bonferroni_alpha'] == 0.05 / 24  # ~0.00208
    
    def test_single_element_multiple_variations(self):
        """Test combination calculation for single element with multiple variations.
        
        Total combinations = 5
        
        **Validates: Requirements 10.1**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'pricing_table', 'n_variations': 5}
            ]
        )
        
        assert result['total_combinations'] == 5
        assert result['traffic_split_pct'] == 20.0  # 100 / 5
        assert result['bonferroni_alpha'] == 0.01  # 0.05 / 5
    
    def test_many_elements_many_variations(self):
        """Test combination calculation for many elements with many variations.
        
        Total combinations = 3 * 4 * 3 * 2 * 2 = 144
        
        **Validates: Requirements 10.1**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'headline', 'n_variations': 3},
                {'name': 'subheadline', 'n_variations': 4},
                {'name': 'button_color', 'n_variations': 3},
                {'name': 'button_text', 'n_variations': 2},
                {'name': 'image', 'n_variations': 2}
            ]
        )
        
        assert result['total_combinations'] == 144
        assert result['traffic_split_pct'] == 100 / 144  # ~0.69%
        assert result['bonferroni_alpha'] == 0.05 / 144  # ~0.000347


class TestBonferroniCorrection:
    """Tests for Bonferroni correction application."""
    
    def test_bonferroni_alpha_calculation(self):
        """Test that Bonferroni correction is applied correctly.
        
        alpha_corrected = alpha / total_combinations
        
        **Validates: Requirements 10.5**
        """
        test_cases = [
            (0.05, 4, 0.0125),
            (0.05, 8, 0.00625),
            (0.05, 10, 0.005),
            (0.05, 20, 0.0025),
            (0.01, 5, 0.002),
            (0.10, 10, 0.01),
        ]
        
        for alpha, n_combinations, expected_alpha in test_cases:
            # Create elements to get exact number of combinations
            if n_combinations == 4:
                elements = [{'name': 'a', 'n_variations': 2}, {'name': 'b', 'n_variations': 2}]
            elif n_combinations == 8:
                elements = [{'name': 'a', 'n_variations': 2}, {'name': 'b', 'n_variations': 2}, {'name': 'c', 'n_variations': 2}]
            elif n_combinations == 10:
                elements = [{'name': 'element', 'n_variations': 10}]
            elif n_combinations == 20:
                elements = [{'name': 'element', 'n_variations': 20}]
            elif n_combinations == 5:
                elements = [{'name': 'element', 'n_variations': 5}]
            else:
                # For other cases, create elements that multiply to n_combinations
                elements = []
                remaining = n_combinations
                for i in range(3, 0, -1):
                    if remaining % i == 0:
                        elements.append({'name': f'element_{i}', 'n_variations': i})
                        remaining //= i
                if remaining > 1:
                    elements.append({'name': 'element_final', 'n_variations': remaining})
            
            result = plan_multivariate_test(
                baseline_cvr=0.03,
                elements=elements,
                alpha=alpha
            )
            
            # Bonferroni alpha should be calculated correctly
            assert result['bonferroni_alpha'] == expected_alpha, \
                f"Expected {expected_alpha}, got {result['bonferroni_alpha']} for alpha={alpha}, combinations={n_combinations}"
    
    def test_bonferroni_alpha_is_smaller_than_original(self):
        """Test that Bonferroni-corrected alpha is always smaller than original.
        
        **Validates: Requirements 10.5**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 3},
                {'name': 'element2', 'n_variations': 2}
            ],
            alpha=0.05
        )
        
        assert result['bonferroni_alpha'] < 0.05
        assert result['bonferroni_alpha'] == 0.05 / 6  # 0.05 / (3*2)


class TestTrafficSplit:
    """Tests for traffic split calculation."""
    
    def test_traffic_split_uniformity(self):
        """Test that traffic is split evenly across all combinations.
        
        **Validates: Requirements 10.3**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 3},
                {'name': 'element2', 'n_variations': 2}
            ]
        )
        
        total_combinations = result['total_combinations']
        expected_split = 100 / total_combinations
        
        assert result['traffic_split_pct'] == expected_split
        
        # Verify that sum of all splits equals 100%
        # (with floating point tolerance)
        sum_of_splits = result['traffic_split_pct'] * total_combinations
        assert abs(sum_of_splits - 100.0) < 1e-9
    
    def test_traffic_split_decreases_with_more_combinations(self):
        """Test that traffic split per combination decreases as combinations increase.
        
        **Validates: Requirements 10.3**
        """
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
        
        assert result_4['traffic_split_pct'] > result_8['traffic_split_pct']
        assert result_4['traffic_split_pct'] == 25.0
        assert result_8['traffic_split_pct'] == 12.5
    
    def test_traffic_split_with_available_traffic(self):
        """Test traffic split calculation with available traffic parameter.
        
        **Validates: Requirements 10.3**
        """
        # Use a very low traffic value that will trigger the warning
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 3},
                {'name': 'element2', 'n_variations': 2}
            ],
            available_traffic=100  # Very low traffic
        )
        
        # Traffic split should still be calculated correctly
        assert result['traffic_split_pct'] == 100 / 6  # ~16.67%
        
        # Should have warnings about insufficient traffic
        assert len(result['warnings']) > 0
        assert any('Insufficient Traffic' in w for w in result['warnings'])


class TestSampleSizeCalculation:
    """Tests for sample size calculation with Bonferroni correction."""
    
    def test_sample_size_increases_with_more_combinations(self):
        """Test that sample size increases with more combinations (due to Bonferroni).
        
        **Validates: Requirements 10.2**
        """
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
        
        # More combinations means smaller alpha per test, requiring larger sample
        assert result_8['sample_size_per_combination'] > result_4['sample_size_per_combination']
        assert result_8['total_sample_size'] > result_4['total_sample_size']
    
    def test_sample_size_per_combination_is_positive(self):
        """Test that sample size per combination is always positive.
        
        **Validates: Requirements 10.2**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 3},
                {'name': 'element2', 'n_variations': 2}
            ]
        )
        
        assert result['sample_size_per_combination'] > 0
        assert isinstance(result['sample_size_per_combination'], int)


class TestWarnings:
    """Tests for warning generation."""
    
    def test_warning_for_too_many_combinations(self):
        """Test warning when combinations exceed 8.
        
        **Validates: Requirements 10.4**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 3},
                {'name': 'element2', 'n_variations': 3},
                {'name': 'element3', 'n_variations': 2}
            ]
        )
        
        # 3 * 3 * 2 = 18 combinations > 8
        assert result['total_combinations'] == 18
        assert len(result['warnings']) > 0
        assert any('Too Many Combinations' in w for w in result['warnings'])
        assert any('8' in w for w in result['warnings'])
    
    def test_no_warning_for_8_or_fewer_combinations(self):
        """Test no warning when combinations are 8 or fewer.
        
        **Validates: Requirements 10.4**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 2},
                {'name': 'element2', 'n_variations': 2},
                {'name': 'element3', 'n_variations': 2}
            ]
        )
        
        # 2 * 2 * 2 = 8 combinations (exactly at threshold)
        assert result['total_combinations'] == 8
        # Should not have too many combinations warning
        many_combination_warnings = [w for w in result['warnings'] if 'Too Many Combinations' in w]
        assert len(many_combination_warnings) == 0
    
    def test_insufficient_traffic_warning(self):
        """Test warning when available traffic is insufficient.
        
        **Validates: Requirements 10.6**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 3},
                {'name': 'element2', 'n_variations': 2}
            ],
            available_traffic=1000  # Very low traffic
        )
        
        # Should have insufficient traffic warning
        assert len(result['warnings']) > 0
        assert any('Insufficient Traffic' in w for w in result['warnings'])
    
    def test_warnings_list_is_always_present(self):
        """Test that warnings list is always present, even if empty.
        
        **Validates: Requirements 10.4, 10.6**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 2}
            ]
        )
        
        assert 'warnings' in result
        assert isinstance(result['warnings'], list)


class TestRecommendations:
    """Tests for recommendations generation."""
    
    def test_recommendations_for_too_many_combinations(self):
        """Test recommendations when combinations exceed 8.
        
        **Validates: Requirements 10.6**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 3},
                {'name': 'element2', 'n_variations': 3},
                {'name': 'element3', 'n_variations': 2}
            ]
        )
        
        # Should have recommendations
        assert len(result['recommendations']) > 0
        assert any('Reduce total combinations' in r for r in result['recommendations'])
        assert any('Testing fewer elements' in r for r in result['recommendations'])
    
    def test_recommendations_list_is_always_present(self):
        """Test that recommendations list is always present.
        
        **Validates: Requirements 10.6**
        """
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 2}
            ]
        )
        
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)


class TestInputValidation:
    """Tests for input validation."""
    
    def test_empty_elements_list_raises_error(self):
        """Test that empty elements list raises ValueError.
        
        **Validates: Requirements 10.1**
        """
        with pytest.raises(ValueError) as exc_info:
            plan_multivariate_test(
                baseline_cvr=0.03,
                elements=[]
            )
        
        error_message = str(exc_info.value)
        assert "Elements list cannot be empty" in error_message
    
    def test_invalid_element_structure_raises_error(self):
        """Test that invalid element structure raises ValueError.
        
        **Validates: Requirements 10.1**
        """
        with pytest.raises(ValueError) as exc_info:
            plan_multivariate_test(
                baseline_cvr=0.03,
                elements=[
                    {'name': 'element1'}  # Missing n_variations
                ]
            )
        
        error_message = str(exc_info.value)
        assert "n_variations" in error_message
    
    def test_invalid_baseline_cvr_raises_error(self):
        """Test that invalid baseline_cvr raises ValueError.
        
        **Validates: Requirements 10.1**
        """
        with pytest.raises(ValueError) as exc_info:
            plan_multivariate_test(
                baseline_cvr=1.5,  # Invalid: > 1.0
                elements=[
                    {'name': 'element1', 'n_variations': 2}
                ]
            )
        
        error_message = str(exc_info.value)
        assert "Baseline CVR must be between" in error_message
    
    def test_invalid_power_raises_error(self):
        """Test that invalid power raises ValueError.
        
        **Validates: Requirements 10.1**
        """
        with pytest.raises(ValueError) as exc_info:
            plan_multivariate_test(
                baseline_cvr=0.03,
                elements=[
                    {'name': 'element1', 'n_variations': 2}
                ],
                power=0.40  # Invalid: < 0.50
            )
        
        error_message = str(exc_info.value)
        assert "Statistical power must be between" in error_message
    
    def test_invalid_alpha_raises_error(self):
        """Test that invalid alpha raises ValueError.
        
        **Validates: Requirements 10.1**
        """
        with pytest.raises(ValueError) as exc_info:
            plan_multivariate_test(
                baseline_cvr=0.03,
                elements=[
                    {'name': 'element1', 'n_variations': 2}
                ],
                alpha=0.25  # Invalid: > 0.20
            )
        
        error_message = str(exc_info.value)
        assert "Significance level (alpha) must be between" in error_message


class TestIntegrationWithSampleSizeCalculator:
    """Tests for integration with sample size calculator."""
    
    def test_uses_sample_size_calculator_with_bonferroni_alpha(self):
        """Test that plan_multivariate_test uses calculate_sample_size with corrected alpha.
        
        **Validates: Requirements 10.2**
        """
        # Calculate expected sample size manually
        from analytics.conversion import calculate_sample_size
        
        total_combinations = 6  # 3 * 2
        bonferroni_alpha = 0.05 / total_combinations
        
        # Use effective alpha (clamped to minimum 0.01)
        effective_alpha = max(bonferroni_alpha, 0.01)
        
        expected_result = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,  # Default MDE for MVT
            power=0.80,
            alpha=effective_alpha,
            n_variants=total_combinations
        )
        
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=[
                {'name': 'element1', 'n_variations': 3},
                {'name': 'element2', 'n_variations': 2}
            ]
        )
        
        # Sample size should match
        assert result['sample_size_per_combination'] == expected_result['sample_size_per_variant']
        assert result['total_sample_size'] == expected_result['total_sample_size']


class TestElementDetails:
    """Tests for element details in output."""
    
    def test_elements_included_in_output(self):
        """Test that original elements are included in output.
        
        **Validates: Requirements 10.1**
        """
        elements = [
            {'name': 'headline', 'n_variations': 3},
            {'name': 'button_color', 'n_variations': 2}
        ]
        
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=elements
        )
        
        assert 'elements' in result
        assert result['elements'] == elements
    
    def test_combinations_breakdown_included(self):
        """Test that combinations breakdown is included in output.
        
        **Validates: Requirements 10.1**
        """
        elements = [
            {'name': 'headline', 'n_variations': 3},
            {'name': 'button_color', 'n_variations': 2}
        ]
        
        result = plan_multivariate_test(
            baseline_cvr=0.03,
            elements=elements
        )
        
        assert 'combinations_breakdown' in result
        assert 'headline: 3 variations' in result['combinations_breakdown']
        assert 'button_color: 2 variations' in result['combinations_breakdown']
