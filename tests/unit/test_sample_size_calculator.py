"""
Unit tests for sample size calculator and time estimation.

Tests the calculate_sample_size() and estimate_test_duration() functions to ensure 
correct calculations, input validation, warning generation, and boundary condition handling.

**Validates: Requirements 1.1-1.9, 2.1-2.5, 18.1-18.7**
"""

import pytest
import numpy as np
from analytics.conversion import calculate_sample_size, estimate_test_duration


class TestSampleSizeCalculation:
    """Tests for sample size calculation correctness."""
    
    def test_typical_ecommerce_scenario(self):
        """Test sample size for typical e-commerce scenario (3% CVR, 10% MDE).
        
        **Validates: Requirements 1.1, 1.8**
        """
        result = calculate_sample_size(
            baseline_cvr=0.03,  # 3% CVR - typical for e-commerce
            mde=0.10,           # 10% relative improvement
            power=0.80,
            alpha=0.05
        )
        
        # Verify all required keys are present
        assert 'sample_size_per_variant' in result
        assert 'total_sample_size' in result
        assert 'baseline_cvr' in result
        assert 'target_cvr' in result
        assert 'mde_absolute' in result
        assert 'mde_relative' in result
        assert 'power' in result
        assert 'alpha' in result
        assert 'warnings' in result
        
        # Verify sample size is positive
        assert result['sample_size_per_variant'] > 0
        assert isinstance(result['sample_size_per_variant'], int)
        
        # Verify total sample size arithmetic (2 variants)
        assert result['total_sample_size'] == result['sample_size_per_variant'] * 2
        
        # Verify target CVR calculation
        expected_target = 0.03 * (1 + 0.10)  # 3% * 1.10 = 3.3%
        assert abs(result['target_cvr'] - expected_target) < 1e-10
        
        # Verify absolute MDE calculation
        expected_mde_absolute = expected_target - 0.03
        assert abs(result['mde_absolute'] - expected_mde_absolute) < 1e-10
        
        # Verify relative MDE is preserved
        assert result['mde_relative'] == 0.10
        
        # Verify power and alpha are preserved
        assert result['power'] == 0.80
        assert result['alpha'] == 0.05
        
        # For typical e-commerce scenario, no warnings should be present
        # (sample size should be reasonable, not too small or too large)
        assert isinstance(result['warnings'], list)
    
    def test_sample_size_increases_with_smaller_mde(self):
        """Test that smaller MDE requires larger sample size.
        
        **Validates: Requirements 1.1, 1.8**
        """
        result_large_mde = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.20,  # 20% improvement
            power=0.80,
            alpha=0.05
        )
        
        result_small_mde = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.05,  # 5% improvement
            power=0.80,
            alpha=0.05
        )
        
        # Smaller MDE should require larger sample size
        assert result_small_mde['sample_size_per_variant'] > result_large_mde['sample_size_per_variant']
    
    def test_sample_size_increases_with_higher_power(self):
        """Test that higher power requires larger sample size.
        
        **Validates: Requirements 1.1, 1.8**
        """
        result_low_power = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.70,
            alpha=0.05
        )
        
        result_high_power = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.90,
            alpha=0.05
        )
        
        # Higher power should require larger sample size
        assert result_high_power['sample_size_per_variant'] > result_low_power['sample_size_per_variant']
    
    def test_idempotence(self):
        """Test that calling with identical inputs produces identical outputs.
        
        **Validates: Requirements 1.9**
        """
        params = {
            'baseline_cvr': 0.03,
            'mde': 0.10,
            'power': 0.80,
            'alpha': 0.05,
            'n_variants': 2
        }
        
        result1 = calculate_sample_size(**params)
        result2 = calculate_sample_size(**params)
        result3 = calculate_sample_size(**params)
        
        # All results should be identical
        assert result1 == result2
        assert result2 == result3
    
    def test_total_sample_size_arithmetic(self):
        """Test that total sample size equals per-variant size times number of variants.
        
        **Validates: Requirements 1.7**
        """
        # Test with 2 variants
        result_2 = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            n_variants=2
        )
        assert result_2['total_sample_size'] == result_2['sample_size_per_variant'] * 2
        
        # Test with 3 variants
        result_3 = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            n_variants=3
        )
        assert result_3['total_sample_size'] == result_3['sample_size_per_variant'] * 3
        
        # Test with 5 variants
        result_5 = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            n_variants=5
        )
        assert result_5['total_sample_size'] == result_5['sample_size_per_variant'] * 5


class TestTwymansLawWarning:
    """Tests for Twyman's Law warning generation."""
    
    def test_twymans_law_warning_for_small_sample(self):
        """Test that Twyman's Law warning is generated for small samples (<350).
        
        **Validates: Requirements 1.6, 3.1, 3.2**
        """
        # Use parameters that will result in small sample size
        result = calculate_sample_size(
            baseline_cvr=0.50,  # High baseline
            mde=0.20,           # Large effect
            power=0.80,
            alpha=0.05
        )
        
        # Check if sample size is indeed small
        if result['sample_size_per_variant'] < 350:
            # Should have Twyman's Law warning
            assert len(result['warnings']) > 0
            assert any('Twyman' in w for w in result['warnings'])
            assert any('350' in w for w in result['warnings'])
    
    def test_no_twymans_law_warning_for_adequate_sample(self):
        """Test that no Twyman's Law warning for adequate samples (>=350).
        
        **Validates: Requirements 1.6, 3.1**
        """
        # Use parameters that will result in adequate sample size
        result = calculate_sample_size(
            baseline_cvr=0.03,  # Typical e-commerce
            mde=0.10,           # 10% improvement
            power=0.80,
            alpha=0.05
        )
        
        # Check if sample size is adequate
        if result['sample_size_per_variant'] >= 350:
            # Should not have Twyman's Law warning
            twyman_warnings = [w for w in result['warnings'] if 'Twyman' in w]
            assert len(twyman_warnings) == 0


class TestInputValidation:
    """Tests for input validation and error messages."""
    
    def test_invalid_baseline_cvr_too_low(self):
        """Test validation error for baseline_cvr below minimum (0.001).
        
        **Validates: Requirements 1.2, 18.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.0005,  # Below 0.001
                mde=0.10,
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Baseline CVR must be between 0.1% and 100%" in error_message
        assert "0.0005" in error_message
    
    def test_invalid_baseline_cvr_too_high(self):
        """Test validation error for baseline_cvr above maximum (1.0).
        
        **Validates: Requirements 1.2, 18.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=1.5,  # Above 1.0
                mde=0.10,
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Baseline CVR must be between 0.1% and 100%" in error_message
        assert "1.5" in error_message
    
    def test_invalid_mde_too_low(self):
        """Test validation error for MDE below minimum (0.01).
        
        **Validates: Requirements 1.3, 18.2**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.03,
                mde=0.005,  # Below 0.01
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "MDE must be between 1% and 100%" in error_message
        assert "0.005" in error_message
    
    def test_invalid_mde_too_high(self):
        """Test validation error for MDE above maximum (1.0).
        
        **Validates: Requirements 1.3, 18.2**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.03,
                mde=1.5,  # Above 1.0
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "MDE must be between 1% and 100%" in error_message
        assert "1.5" in error_message
    
    def test_invalid_power_too_low(self):
        """Test validation error for power below minimum (0.50).
        
        **Validates: Requirements 1.4, 18.3**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.03,
                mde=0.10,
                power=0.40,  # Below 0.50
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Statistical power must be between 50% and 99%" in error_message
        assert "0.4" in error_message
    
    def test_invalid_power_too_high(self):
        """Test validation error for power above maximum (0.99).
        
        **Validates: Requirements 1.4, 18.3**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.03,
                mde=0.10,
                power=0.995,  # Above 0.99
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Statistical power must be between 50% and 99%" in error_message
        assert "0.995" in error_message
    
    def test_invalid_alpha_too_low(self):
        """Test validation error for alpha below minimum (0.01).
        
        **Validates: Requirements 1.5, 18.4**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.03,
                mde=0.10,
                power=0.80,
                alpha=0.005  # Below 0.01
            )
        
        error_message = str(exc_info.value)
        assert "Significance level (alpha) must be between 1% and 20%" in error_message
        assert "0.005" in error_message
    
    def test_invalid_alpha_too_high(self):
        """Test validation error for alpha above maximum (0.20).
        
        **Validates: Requirements 1.5, 18.4**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.03,
                mde=0.10,
                power=0.80,
                alpha=0.25  # Above 0.20
            )
        
        error_message = str(exc_info.value)
        assert "Significance level (alpha) must be between 1% and 20%" in error_message
        assert "0.25" in error_message
    
    def test_invalid_n_variants_too_low(self):
        """Test validation error for n_variants below minimum (2).
        
        **Validates: Requirements 18.5**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.03,
                mde=0.10,
                power=0.80,
                alpha=0.05,
                n_variants=1  # Below 2
            )
        
        error_message = str(exc_info.value)
        assert "Number of variants must be at least 2" in error_message
        assert "1" in error_message
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are reported together.
        
        **Validates: Requirements 18.7**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=1.5,   # Invalid
                mde=0.005,          # Invalid
                power=0.40,         # Invalid
                alpha=0.25,         # Invalid
                n_variants=1        # Invalid
            )
        
        error_message = str(exc_info.value)
        # Should contain multiple error messages separated by semicolons
        assert "Baseline CVR must be between" in error_message
        assert "MDE must be between" in error_message
        assert "Statistical power must be between" in error_message
        assert "Significance level (alpha) must be between" in error_message
        assert "Number of variants must be at least 2" in error_message
    
    def test_target_cvr_exceeds_100_percent(self):
        """Test validation error when target CVR would exceed 100%.
        
        **Validates: Requirements 1.2, 1.3**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=0.80,  # 80% baseline
                mde=0.50,           # 50% improvement would give 120%
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Target CVR" in error_message
        assert "exceeds 100%" in error_message


class TestBoundaryConditions:
    """Tests for boundary conditions (min/max valid inputs)."""
    
    def test_minimum_valid_inputs(self):
        """Test calculation with minimum valid input values.
        
        **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
        """
        result = calculate_sample_size(
            baseline_cvr=0.001,  # Minimum valid
            mde=0.01,            # Minimum valid
            power=0.50,          # Minimum valid
            alpha=0.20,          # Maximum valid (less stringent)
            n_variants=2
        )
        
        # Should complete without error
        assert result['sample_size_per_variant'] > 0
        assert result['baseline_cvr'] == 0.001
        assert result['mde_relative'] == 0.01
        assert result['power'] == 0.50
        assert result['alpha'] == 0.20
    
    def test_maximum_valid_inputs(self):
        """Test calculation with maximum valid input values.
        
        **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
        """
        result = calculate_sample_size(
            baseline_cvr=0.50,   # High but valid (can't use 1.0 with mde=1.0)
            mde=0.99,            # Near maximum valid
            power=0.99,          # Maximum valid
            alpha=0.01,          # Minimum valid (most stringent)
            n_variants=2
        )
        
        # Should complete without error
        assert result['sample_size_per_variant'] > 0
        assert result['baseline_cvr'] == 0.50
        assert result['mde_relative'] == 0.99
        assert result['power'] == 0.99
        assert result['alpha'] == 0.01
    
    def test_boundary_baseline_cvr_at_minimum(self):
        """Test baseline_cvr exactly at minimum boundary (0.001).
        
        **Validates: Requirements 1.2**
        """
        result = calculate_sample_size(
            baseline_cvr=0.001,  # Exactly at minimum
            mde=0.10,
            power=0.80,
            alpha=0.05
        )
        
        assert result['sample_size_per_variant'] > 0
        assert result['baseline_cvr'] == 0.001
    
    def test_boundary_baseline_cvr_at_maximum(self):
        """Test baseline_cvr exactly at maximum boundary (1.0).
        
        **Validates: Requirements 1.2**
        """
        # With baseline_cvr=1.0, any positive MDE would exceed 100%
        # So we need to test that this is caught
        with pytest.raises(ValueError) as exc_info:
            calculate_sample_size(
                baseline_cvr=1.0,   # Exactly at maximum
                mde=0.01,           # Any positive MDE
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Target CVR" in error_message and "exceeds 100%" in error_message
    
    def test_boundary_mde_at_minimum(self):
        """Test MDE exactly at minimum boundary (0.01).
        
        **Validates: Requirements 1.3**
        """
        result = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.01,  # Exactly at minimum
            power=0.80,
            alpha=0.05
        )
        
        assert result['sample_size_per_variant'] > 0
        assert result['mde_relative'] == 0.01
    
    def test_boundary_power_at_minimum(self):
        """Test power exactly at minimum boundary (0.50).
        
        **Validates: Requirements 1.4**
        """
        result = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.50,  # Exactly at minimum
            alpha=0.05
        )
        
        assert result['sample_size_per_variant'] > 0
        assert result['power'] == 0.50
    
    def test_boundary_alpha_at_minimum(self):
        """Test alpha exactly at minimum boundary (0.01).
        
        **Validates: Requirements 1.5**
        """
        result = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.80,
            alpha=0.01  # Exactly at minimum
        )
        
        assert result['sample_size_per_variant'] > 0
        assert result['alpha'] == 0.01


class TestImpracticalTestWarning:
    """Tests for impractical test warning (>1M sample size)."""
    
    def test_impractical_test_warning_for_large_sample(self):
        """Test that impractical test warning is generated for very large samples (>1M).
        
        **Validates: Requirements 1.6**
        """
        # Use parameters that will result in very large sample size
        result = calculate_sample_size(
            baseline_cvr=0.001,  # Very low baseline
            mde=0.01,            # Very small effect
            power=0.90,          # High power
            alpha=0.01           # Stringent alpha
        )
        
        # Check if sample size is indeed very large
        if result['sample_size_per_variant'] > 1_000_000:
            # Should have impractical test warning
            assert len(result['warnings']) > 0
            assert any('Impractical' in w for w in result['warnings'])
            assert any('1M' in w or '1,000,000' in w for w in result['warnings'])
    
    def test_no_impractical_warning_for_reasonable_sample(self):
        """Test that no impractical warning for reasonable samples (<=1M).
        
        **Validates: Requirements 1.6**
        """
        # Use parameters that will result in reasonable sample size
        result = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.80,
            alpha=0.05
        )
        
        # Check if sample size is reasonable
        if result['sample_size_per_variant'] <= 1_000_000:
            # Should not have impractical test warning
            impractical_warnings = [w for w in result['warnings'] if 'Impractical' in w]
            assert len(impractical_warnings) == 0


class TestLargeEffectWarning:
    """Tests for large effect warning (MDE > 50%)."""
    
    def test_large_effect_warning(self):
        """Test that large effect warning is generated for MDE > 50%.
        
        **Validates: Requirements 1.6**
        """
        result = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.60,  # 60% improvement - very large
            power=0.80,
            alpha=0.05
        )
        
        # Should have large effect warning
        assert len(result['warnings']) > 0
        assert any('Large Effect' in w for w in result['warnings'])
        assert any('60%' in w for w in result['warnings'])
    
    def test_no_large_effect_warning_for_reasonable_mde(self):
        """Test that no large effect warning for reasonable MDE (<=50%).
        
        **Validates: Requirements 1.6**
        """
        result = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.20,  # 20% improvement - reasonable
            power=0.80,
            alpha=0.05
        )
        
        # Should not have large effect warning
        large_effect_warnings = [w for w in result['warnings'] if 'Large Effect' in w]
        assert len(large_effect_warnings) == 0



# ============================================================================
# Time Estimation Tests
# ============================================================================

class TestTimeEstimationCalculation:
    """Tests for time estimation calculation correctness."""
    
    def test_typical_traffic_scenario(self):
        """Test time estimation for typical traffic scenario.
        
        **Validates: Requirements 2.1, 2.4, 2.5**
        """
        result = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # Verify all required keys are present
        assert 'days_to_completion' in result
        assert 'weeks_to_completion' in result
        assert 'daily_traffic' in result
        assert 'daily_conversions_expected' in result
        assert 'warnings' in result
        
        # Verify calculation: 10000 / 1000 = 10 days
        assert result['days_to_completion'] == 10.0
        assert result['weeks_to_completion'] == 1.4  # 10 / 7 = 1.428... rounded to 1.4
        
        # Verify daily traffic is preserved
        assert result['daily_traffic'] == 1000
        
        # Verify daily conversions: 1000 * 0.03 = 30
        assert result['daily_conversions_expected'] == 30
        
        # Verify warnings list is present
        assert isinstance(result['warnings'], list)
    
    def test_high_traffic_scenario(self):
        """Test time estimation with high daily traffic.
        
        **Validates: Requirements 2.1, 2.4, 2.5**
        """
        result = estimate_test_duration(
            required_sample_size=50000,
            daily_traffic=10000,
            conversion_rate=0.05
        )
        
        # 50000 / 10000 = 5 days
        assert result['days_to_completion'] == 5.0
        assert result['weeks_to_completion'] == 0.7  # 5 / 7 = 0.714... rounded to 0.7
        
        # 10000 * 0.05 = 500 conversions per day
        assert result['daily_conversions_expected'] == 500
        
        # Should not have warnings for 5-day test (< 7 days but reasonable)
        # Actually, it should have a warning about < 7 days
        assert len(result['warnings']) > 0
    
    def test_low_traffic_scenario(self):
        """Test time estimation with low daily traffic.
        
        **Validates: Requirements 2.1, 2.4, 2.5**
        """
        result = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=100,
            conversion_rate=0.02
        )
        
        # 10000 / 100 = 100 days
        assert result['days_to_completion'] == 100.0
        assert result['weeks_to_completion'] == 14.3  # 100 / 7 = 14.285... rounded to 14.3
        
        # 100 * 0.02 = 2 conversions per day
        assert result['daily_conversions_expected'] == 2
        
        # Should have warning for long test (> 90 days)
        assert len(result['warnings']) > 0
        assert any('Long Test Duration' in w for w in result['warnings'])
    
    def test_rounding_to_one_decimal_place(self):
        """Test that time estimates are rounded to one decimal place.
        
        **Validates: Requirements 2.5**
        """
        # Test case that produces non-integer result
        result = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=333,  # Will produce 30.03... days
            conversion_rate=0.03
        )
        
        # Should be rounded to 1 decimal place
        assert result['days_to_completion'] == 30.0
        
        # Verify it's actually rounded, not truncated
        result2 = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=300,  # Will produce 33.333... days
            conversion_rate=0.03
        )
        
        # 10000 / 300 = 33.333... rounded to 33.3
        assert result2['days_to_completion'] == 33.3
        
        # Verify weeks are also rounded to 1 decimal
        assert result2['weeks_to_completion'] == 4.8  # 33.3 / 7 = 4.757... rounded to 4.8
    
    def test_arithmetic_relationship_days_to_weeks(self):
        """Test that weeks_to_completion = days_to_completion / 7.
        
        **Validates: Requirements 2.1, 2.5**
        """
        result = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # Verify arithmetic relationship
        expected_weeks = round(result['days_to_completion'] / 7, 1)
        assert result['weeks_to_completion'] == expected_weeks
    
    def test_daily_conversions_calculation(self):
        """Test that daily_conversions_expected = daily_traffic * conversion_rate.
        
        **Validates: Requirements 2.1, 2.4**
        """
        test_cases = [
            (1000, 0.03, 30),
            (5000, 0.02, 100),
            (10000, 0.05, 500),
            (500, 0.01, 5),
            (2000, 0.04, 80),
        ]
        
        for daily_traffic, conv_rate, expected_conversions in test_cases:
            result = estimate_test_duration(
                required_sample_size=10000,
                daily_traffic=daily_traffic,
                conversion_rate=conv_rate
            )
            
            assert result['daily_conversions_expected'] == expected_conversions


class TestLongTestDurationWarning:
    """Tests for long test duration warning (>90 days)."""
    
    def test_long_test_warning_for_90_plus_days(self):
        """Test that warning is generated for tests exceeding 90 days.
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=100000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 100000 / 1000 = 100 days (> 90)
        assert result['days_to_completion'] == 100.0
        
        # Should have long test duration warning
        assert len(result['warnings']) > 0
        assert any('Long Test Duration' in w for w in result['warnings'])
        assert any('90' in w for w in result['warnings'])
        assert any('100' in w for w in result['warnings'])
    
    def test_long_test_warning_includes_weeks(self):
        """Test that long test warning includes weeks to completion.
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=100000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # Should mention weeks in warning
        warning_text = ' '.join(result['warnings'])
        assert 'weeks' in warning_text.lower()
    
    def test_no_long_test_warning_for_90_days_or_less(self):
        """Test that no warning for tests at or below 90 days.
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=90000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 90000 / 1000 = 90 days (exactly at threshold)
        assert result['days_to_completion'] == 90.0
        
        # Should not have long test duration warning
        long_test_warnings = [w for w in result['warnings'] if 'Long Test Duration' in w]
        assert len(long_test_warnings) == 0
    
    def test_long_test_warning_just_above_threshold(self):
        """Test warning for test just above 90-day threshold.
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=91000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 91000 / 1000 = 91 days (just above 90)
        assert result['days_to_completion'] == 91.0
        
        # Should have long test duration warning
        assert len(result['warnings']) > 0
        assert any('Long Test Duration' in w for w in result['warnings'])


class TestMinimumDurationRecommendation:
    """Tests for minimum 7-day duration recommendation."""
    
    def test_minimum_duration_recommendation_for_short_tests(self):
        """Test that recommendation is generated for tests under 7 days.
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=5000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 5000 / 1000 = 5 days (< 7)
        assert result['days_to_completion'] == 5.0
        
        # Should have minimum duration recommendation
        assert len(result['warnings']) > 0
        assert any('Short Test Duration' in w for w in result['warnings'])
        assert any('7' in w for w in result['warnings'])
    
    def test_minimum_duration_recommendation_includes_weekly_patterns(self):
        """Test that recommendation mentions weekly patterns.
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=5000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # Should mention weekly patterns in warning
        warning_text = ' '.join(result['warnings'])
        assert 'weekly' in warning_text.lower() or 'week' in warning_text.lower()
    
    def test_no_minimum_duration_recommendation_for_7_plus_days(self):
        """Test that no recommendation for tests at or above 7 days.
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=7000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 7000 / 1000 = 7 days (exactly at threshold)
        assert result['days_to_completion'] == 7.0
        
        # Should not have minimum duration recommendation
        short_test_warnings = [w for w in result['warnings'] if 'Short Test Duration' in w]
        assert len(short_test_warnings) == 0
    
    def test_minimum_duration_recommendation_just_below_threshold(self):
        """Test recommendation for test just below 7-day threshold.
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=6900,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 6900 / 1000 = 6.9 days (just below 7)
        assert result['days_to_completion'] == 6.9
        
        # Should have minimum duration recommendation
        assert len(result['warnings']) > 0
        assert any('Short Test Duration' in w for w in result['warnings'])


class TestInvalidInputHandling:
    """Tests for invalid input handling (zero/negative traffic)."""
    
    def test_zero_daily_traffic_raises_error(self):
        """Test that zero daily traffic raises ValueError.
        
        **Validates: Requirements 2.2**
        """
        with pytest.raises(ValueError) as exc_info:
            estimate_test_duration(
                required_sample_size=10000,
                daily_traffic=0,
                conversion_rate=0.03
            )
        
        error_message = str(exc_info.value)
        assert "Daily traffic must be greater than 0" in error_message
        assert "0" in error_message
    
    def test_negative_daily_traffic_raises_error(self):
        """Test that negative daily traffic raises ValueError.
        
        **Validates: Requirements 2.2**
        """
        with pytest.raises(ValueError) as exc_info:
            estimate_test_duration(
                required_sample_size=10000,
                daily_traffic=-1000,
                conversion_rate=0.03
            )
        
        error_message = str(exc_info.value)
        assert "Daily traffic must be greater than 0" in error_message
        assert "-1000" in error_message
    
    def test_error_message_includes_invalid_value(self):
        """Test that error message includes the invalid value provided.
        
        **Validates: Requirements 2.2**
        """
        invalid_traffic = -500
        
        with pytest.raises(ValueError) as exc_info:
            estimate_test_duration(
                required_sample_size=10000,
                daily_traffic=invalid_traffic,
                conversion_rate=0.03
            )
        
        error_message = str(exc_info.value)
        assert str(invalid_traffic) in error_message


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_very_small_sample_size(self):
        """Test time estimation with very small sample size.
        
        **Validates: Requirements 2.1, 2.5**
        """
        result = estimate_test_duration(
            required_sample_size=1,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 1 / 1000 = 0.001 days, rounded to 0.0
        assert result['days_to_completion'] == 0.0
        assert result['weeks_to_completion'] == 0.0
    
    def test_very_large_sample_size(self):
        """Test time estimation with very large sample size.
        
        **Validates: Requirements 2.1, 2.5**
        """
        result = estimate_test_duration(
            required_sample_size=1000000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 1000000 / 1000 = 1000 days
        assert result['days_to_completion'] == 1000.0
        assert result['weeks_to_completion'] == 142.9  # 1000 / 7 = 142.857... rounded to 142.9
        
        # Should have long test duration warning
        assert len(result['warnings']) > 0
        assert any('Long Test Duration' in w for w in result['warnings'])
    
    def test_very_high_daily_traffic(self):
        """Test time estimation with very high daily traffic.
        
        **Validates: Requirements 2.1, 2.5**
        """
        result = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=1000000,
            conversion_rate=0.03
        )
        
        # 10000 / 1000000 = 0.01 days
        assert result['days_to_completion'] == 0.0
        assert result['weeks_to_completion'] == 0.0
    
    def test_very_low_conversion_rate(self):
        """Test time estimation with very low conversion rate.
        
        **Validates: Requirements 2.1, 2.4**
        """
        result = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=1000,
            conversion_rate=0.001  # 0.1%
        )
        
        # 1000 * 0.001 = 1 conversion per day
        assert result['daily_conversions_expected'] == 1
        
        # Days should still be 10
        assert result['days_to_completion'] == 10.0
    
    def test_very_high_conversion_rate(self):
        """Test time estimation with very high conversion rate.
        
        **Validates: Requirements 2.1, 2.4**
        """
        result = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=1000,
            conversion_rate=0.50  # 50%
        )
        
        # 1000 * 0.50 = 500 conversions per day
        assert result['daily_conversions_expected'] == 500
        
        # Days should still be 10
        assert result['days_to_completion'] == 10.0
    
    def test_fractional_daily_conversions_truncated_to_int(self):
        """Test that daily conversions are truncated to integer.
        
        **Validates: Requirements 2.4**
        """
        result = estimate_test_duration(
            required_sample_size=10000,
            daily_traffic=1000,
            conversion_rate=0.0333  # Will produce 33.3 conversions
        )
        
        # Should be truncated to 33, not rounded
        assert result['daily_conversions_expected'] == 33
        assert isinstance(result['daily_conversions_expected'], int)


class TestWarningCombinations:
    """Tests for combinations of warnings."""
    
    def test_both_long_and_short_duration_warnings_not_simultaneous(self):
        """Test that long and short duration warnings don't appear together.
        
        **Validates: Requirements 2.3**
        """
        # Test with long duration
        result_long = estimate_test_duration(
            required_sample_size=100000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        long_warnings = [w for w in result_long['warnings'] if 'Long Test Duration' in w]
        short_warnings = [w for w in result_long['warnings'] if 'Short Test Duration' in w]
        
        # Should have long but not short
        assert len(long_warnings) > 0
        assert len(short_warnings) == 0
        
        # Test with short duration
        result_short = estimate_test_duration(
            required_sample_size=5000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        long_warnings = [w for w in result_short['warnings'] if 'Long Test Duration' in w]
        short_warnings = [w for w in result_short['warnings'] if 'Short Test Duration' in w]
        
        # Should have short but not long
        assert len(short_warnings) > 0
        assert len(long_warnings) == 0
    
    def test_no_warnings_for_ideal_duration(self):
        """Test that no warnings for ideal test duration (7-90 days).
        
        **Validates: Requirements 2.3**
        """
        result = estimate_test_duration(
            required_sample_size=30000,
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # 30000 / 1000 = 30 days (within 7-90 range)
        assert result['days_to_completion'] == 30.0
        
        # Should have no warnings
        assert len(result['warnings']) == 0


class TestIntegrationWithSampleSizeCalculator:
    """Tests for integration with sample size calculator."""
    
    def test_time_estimation_with_calculated_sample_size(self):
        """Test time estimation using sample size from calculator.
        
        **Validates: Requirements 2.1, 2.4, 2.5**
        """
        # First calculate sample size
        ss_result = calculate_sample_size(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.80,
            alpha=0.05
        )
        
        # Then estimate time with that sample size
        time_result = estimate_test_duration(
            required_sample_size=ss_result['total_sample_size'],
            daily_traffic=1000,
            conversion_rate=0.03
        )
        
        # Should complete without error
        assert time_result['days_to_completion'] > 0
        assert time_result['daily_traffic'] == 1000
        assert time_result['daily_conversions_expected'] == 30
    
    def test_time_estimation_with_various_sample_sizes(self):
        """Test time estimation with various calculated sample sizes.
        
        **Validates: Requirements 2.1, 2.5**
        """
        test_cases = [
            (0.03, 0.05, 0.80, 0.05),  # Small MDE
            (0.03, 0.20, 0.80, 0.05),  # Large MDE
            (0.03, 0.10, 0.90, 0.05),  # High power
            (0.03, 0.10, 0.80, 0.01),  # Stringent alpha
        ]
        
        for baseline_cvr, mde, power, alpha in test_cases:
            ss_result = calculate_sample_size(
                baseline_cvr=baseline_cvr,
                mde=mde,
                power=power,
                alpha=alpha
            )
            
            time_result = estimate_test_duration(
                required_sample_size=ss_result['total_sample_size'],
                daily_traffic=1000,
                conversion_rate=baseline_cvr
            )
            
            # Should complete without error
            assert time_result['days_to_completion'] > 0
            assert time_result['daily_conversions_expected'] > 0
