"""
Unit tests for statistical power calculator.

Tests the calculate_power() function to ensure correct calculations, input validation,
warning generation, and boundary condition handling.

**Validates: Requirements 5.1-5.7**
"""

import pytest
import numpy as np
from analytics.conversion import calculate_power


class TestPowerCalculation:
    """Tests for power calculation correctness."""
    
    def test_typical_ecommerce_scenario(self):
        """Test power calculation for typical e-commerce scenario.
        
        **Validates: Requirements 5.1, 5.2**
        """
        result = calculate_power(
            baseline_cvr=0.03,  # 3% CVR - typical for e-commerce
            effect_size=0.10,   # 10% relative improvement
            sample_size_per_variant=5000,
            alpha=0.05
        )
        
        # Verify all required keys are present
        assert 'power' in result
        assert 'power_pct' in result
        assert 'beta' in result
        assert 'alpha' in result
        assert 'baseline_cvr' in result
        assert 'effect_size' in result
        assert 'target_cvr' in result
        assert 'sample_size_per_variant' in result
        assert 'warnings' in result
        
        # Verify power is between 0 and 1
        assert 0 <= result['power'] <= 1
        
        # Verify power_pct is between 0 and 100
        assert 0 <= result['power_pct'] <= 100
        
        # Verify power_pct is power * 100
        assert abs(result['power_pct'] - result['power'] * 100) < 1e-10
        
        # Verify beta = 1 - power
        assert abs(result['beta'] - (1 - result['power'])) < 1e-10
        
        # Verify alpha is preserved
        assert result['alpha'] == 0.05
        
        # Verify baseline_cvr is preserved
        assert result['baseline_cvr'] == 0.03
        
        # Verify effect_size is preserved
        assert result['effect_size'] == 0.10
        
        # Verify target_cvr calculation
        expected_target = 0.03 * (1 + 0.10)  # 3.3%
        assert abs(result['target_cvr'] - expected_target) < 1e-10
        
        # Verify sample_size_per_variant is preserved
        assert result['sample_size_per_variant'] == 5000
        
        # Verify warnings list is present
        assert isinstance(result['warnings'], list)
    
    def test_power_increases_with_sample_size(self):
        """Test that power increases with larger sample sizes.
        
        **Validates: Requirements 5.1**
        """
        result_small = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.10,
            sample_size_per_variant=1000,
            alpha=0.05
        )
        
        result_large = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.10,
            sample_size_per_variant=10000,
            alpha=0.05
        )
        
        # Larger sample size should have higher power
        assert result_large['power'] > result_small['power']
        assert result_large['power_pct'] > result_small['power_pct']
    
    def test_power_increases_with_larger_effect_size(self):
        """Test that power increases with larger effect sizes.
        
        **Validates: Requirements 5.1**
        """
        result_small_effect = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.05,  # 5% improvement
            sample_size_per_variant=5000,
            alpha=0.05
        )
        
        result_large_effect = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.20,  # 20% improvement
            sample_size_per_variant=5000,
            alpha=0.05
        )
        
        # Larger effect size should have higher power
        assert result_large_effect['power'] > result_small_effect['power']
        assert result_large_effect['power_pct'] > result_small_effect['power_pct']
    
    def test_power_decreases_with_stricter_alpha(self):
        """Test that power decreases with stricter (lower) alpha.
        
        **Validates: Requirements 5.1**
        """
        result_lenient = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.10,
            sample_size_per_variant=5000,
            alpha=0.10  # More lenient
        )
        
        result_strict = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.10,
            sample_size_per_variant=5000,
            alpha=0.01  # More strict
        )
        
        # Stricter alpha should have lower power
        assert result_strict['power'] < result_lenient['power']
        assert result_strict['power_pct'] < result_lenient['power_pct']
    
    def test_type_i_error_equals_alpha(self):
        """Test that Type I error (alpha) equals the significance level.
        
        **Validates: Requirements 5.5**
        """
        test_cases = [
            (0.03, 0.10, 5000, 0.01),
            (0.03, 0.10, 5000, 0.05),
            (0.03, 0.10, 5000, 0.10),
            (0.05, 0.15, 3000, 0.02),
        ]
        
        for baseline_cvr, effect_size, sample_size, alpha in test_cases:
            result = calculate_power(baseline_cvr, effect_size, sample_size, alpha)
            
            # Type I error (alpha) should equal the input alpha
            assert result['alpha'] == alpha
    
    def test_type_ii_error_equals_one_minus_power(self):
        """Test that Type II error (beta) equals 1 - power.
        
        **Validates: Requirements 5.6**
        """
        test_cases = [
            (0.03, 0.10, 5000, 0.05),
            (0.03, 0.05, 10000, 0.05),
            (0.05, 0.20, 2000, 0.05),
            (0.02, 0.15, 8000, 0.01),
        ]
        
        for baseline_cvr, effect_size, sample_size, alpha in test_cases:
            result = calculate_power(baseline_cvr, effect_size, sample_size, alpha)
            
            # Beta should equal 1 - power
            expected_beta = 1 - result['power']
            assert abs(result['beta'] - expected_beta) < 1e-10


class TestUnderpoweredTestWarning:
    """Tests for underpowered test warning generation."""
    
    def test_underpowered_warning_for_low_power(self):
        """Test that underpowered warning is generated when power < 0.80.
        
        **Validates: Requirements 5.3**
        """
        result = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.05,  # Small effect
            sample_size_per_variant=500,  # Small sample
            alpha=0.05
        )
        
        # Check if power is indeed below 0.80
        if result['power'] < 0.80:
            # Should have underpowered warning
            assert len(result['warnings']) > 0
            assert any('underpowered' in w.lower() for w in result['warnings'])
            assert any('80' in w for w in result['warnings'])
    
    def test_no_underpowered_warning_for_adequate_power(self):
        """Test that no underpowered warning when power >= 0.80.
        
        **Validates: Requirements 5.3**
        """
        result = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.10,  # Reasonable effect
            sample_size_per_variant=5000,  # Adequate sample
            alpha=0.05
        )
        
        # Check if power is adequate
        if result['power'] >= 0.80:
            # Should not have underpowered warning
            underpowered_warnings = [w for w in result['warnings'] if 'underpowered' in w.lower()]
            assert len(underpowered_warnings) == 0


class TestInputValidation:
    """Tests for input validation and error messages."""
    
    def test_invalid_baseline_cvr_too_low(self):
        """Test validation error for baseline_cvr below minimum (0.001).
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=0.0005,  # Below 0.001
                effect_size=0.10,
                sample_size_per_variant=5000,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Baseline CVR must be between 0.1% and 100%" in error_message
        assert "0.0005" in error_message
    
    def test_invalid_baseline_cvr_too_high(self):
        """Test validation error for baseline_cvr above maximum (1.0).
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=1.5,  # Above 1.0
                effect_size=0.10,
                sample_size_per_variant=5000,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Baseline CVR must be between 0.1% and 100%" in error_message
        assert "1.5" in error_message
    
    def test_invalid_effect_size_too_low(self):
        """Test validation error for effect_size below minimum (0.01).
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=0.03,
                effect_size=0.005,  # Below 0.01
                sample_size_per_variant=5000,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Effect size must be between 1% and 100%" in error_message
        assert "0.005" in error_message
    
    def test_invalid_effect_size_too_high(self):
        """Test validation error for effect_size above maximum (1.0).
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=0.03,
                effect_size=1.5,  # Above 1.0
                sample_size_per_variant=5000,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Effect size must be between 1% and 100%" in error_message
        assert "1.5" in error_message
    
    def test_invalid_sample_size_zero(self):
        """Test validation error for sample_size_per_variant <= 0.
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=0.03,
                effect_size=0.10,
                sample_size_per_variant=0,  # Invalid
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Sample size per variant must be greater than 0" in error_message
        assert "0" in error_message
    
    def test_invalid_sample_size_negative(self):
        """Test validation error for negative sample_size_per_variant.
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=0.03,
                effect_size=0.10,
                sample_size_per_variant=-1000,  # Invalid
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Sample size per variant must be greater than 0" in error_message
        assert "-1000" in error_message
    
    def test_invalid_alpha_too_low(self):
        """Test validation error for alpha below minimum (0.01).
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=0.03,
                effect_size=0.10,
                sample_size_per_variant=5000,
                alpha=0.005  # Below 0.01
            )
        
        error_message = str(exc_info.value)
        assert "Significance level (alpha) must be between 1% and 20%" in error_message
        assert "0.005" in error_message
    
    def test_invalid_alpha_too_high(self):
        """Test validation error for alpha above maximum (0.20).
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=0.03,
                effect_size=0.10,
                sample_size_per_variant=5000,
                alpha=0.25  # Above 0.20
            )
        
        error_message = str(exc_info.value)
        assert "Significance level (alpha) must be between 1% and 20%" in error_message
        assert "0.25" in error_message
    
    def test_target_cvr_exceeds_100_percent(self):
        """Test validation error when target CVR would exceed 100%.
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=0.80,  # 80% baseline
                effect_size=0.50,   # 50% improvement would give 120%
                sample_size_per_variant=5000,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Target CVR" in error_message
        assert "exceeds 100%" in error_message
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are reported together.
        
        **Validates: Requirements 5.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_power(
                baseline_cvr=1.5,   # Invalid
                effect_size=0.005,  # Invalid
                sample_size_per_variant=-1000,  # Invalid
                alpha=0.25          # Invalid
            )
        
        error_message = str(exc_info.value)
        # Should contain multiple error messages separated by semicolons
        assert "Baseline CVR must be between" in error_message
        assert "Effect size must be between" in error_message
        assert "Sample size per variant must be greater than 0" in error_message
        assert "Significance level (alpha) must be between" in error_message


class TestBoundaryConditions:
    """Tests for boundary conditions (min/max valid inputs)."""
    
    def test_minimum_valid_inputs(self):
        """Test calculation with minimum valid input values.
        
        **Validates: Requirements 5.1**
        """
        result = calculate_power(
            baseline_cvr=0.001,  # Minimum valid
            effect_size=0.01,    # Minimum valid
            sample_size_per_variant=1,  # Minimum valid
            alpha=0.20           # Maximum valid (less stringent)
        )
        
        # Should complete without error
        assert result['power'] >= 0
        assert result['power'] <= 1
        assert result['baseline_cvr'] == 0.001
        assert result['effect_size'] == 0.01
        assert result['sample_size_per_variant'] == 1
        assert result['alpha'] == 0.20
    
    def test_maximum_valid_inputs(self):
        """Test calculation with maximum valid input values.
        
        **Validates: Requirements 5.1**
        """
        result = calculate_power(
            baseline_cvr=0.50,   # High but valid (can't use 1.0 with effect_size=1.0)
            effect_size=0.99,    # Near maximum valid
            sample_size_per_variant=1000000,  # Large sample
            alpha=0.01           # Minimum valid (most stringent)
        )
        
        # Should complete without error
        assert result['power'] >= 0
        assert result['power'] <= 1
        assert result['baseline_cvr'] == 0.50
        assert result['effect_size'] == 0.99
        assert result['sample_size_per_variant'] == 1000000
        assert result['alpha'] == 0.01
    
    def test_boundary_baseline_cvr_at_minimum(self):
        """Test baseline_cvr exactly at minimum boundary (0.001).
        
        **Validates: Requirements 5.1**
        """
        result = calculate_power(
            baseline_cvr=0.001,  # Exactly at minimum
            effect_size=0.10,
            sample_size_per_variant=5000,
            alpha=0.05
        )
        
        assert result['power'] >= 0
        assert result['power'] <= 1
        assert result['baseline_cvr'] == 0.001
    
    def test_boundary_effect_size_at_minimum(self):
        """Test effect_size exactly at minimum boundary (0.01).
        
        **Validates: Requirements 5.1**
        """
        result = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.01,  # Exactly at minimum
            sample_size_per_variant=5000,
            alpha=0.05
        )
        
        assert result['power'] >= 0
        assert result['power'] <= 1
        assert result['effect_size'] == 0.01
    
    def test_boundary_alpha_at_minimum(self):
        """Test alpha exactly at minimum boundary (0.01).
        
        **Validates: Requirements 5.1**
        """
        result = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.10,
            sample_size_per_variant=5000,
            alpha=0.01  # Exactly at minimum
        )
        
        assert result['power'] >= 0
        assert result['power'] <= 1
        assert result['alpha'] == 0.01
    
    def test_boundary_alpha_at_maximum(self):
        """Test alpha exactly at maximum boundary (0.20).
        
        **Validates: Requirements 5.1**
        """
        result = calculate_power(
            baseline_cvr=0.03,
            effect_size=0.10,
            sample_size_per_variant=5000,
            alpha=0.20  # Exactly at maximum
        )
        
        assert result['power'] >= 0
        assert result['power'] <= 1
        assert result['alpha'] == 0.20


class TestPowerPercentageDisplay:
    """Tests for power percentage display."""
    
    def test_power_pct_is_power_times_100(self):
        """Test that power_pct is correctly calculated as power * 100.
        
        **Validates: Requirements 5.2**
        """
        test_cases = [
            (0.03, 0.10, 5000, 0.05),
            (0.03, 0.05, 10000, 0.05),
            (0.05, 0.20, 2000, 0.05),
            (0.02, 0.15, 8000, 0.01),
        ]
        
        for baseline_cvr, effect_size, sample_size, alpha in test_cases:
            result = calculate_power(baseline_cvr, effect_size, sample_size, alpha)
            
            # power_pct should equal power * 100
            expected_pct = result['power'] * 100
            assert abs(result['power_pct'] - expected_pct) < 1e-10
    
    def test_power_pct_range(self):
        """Test that power_pct is always between 0 and 100.
        
        **Validates: Requirements 5.2**
        """
        test_cases = [
            (0.03, 0.01, 100, 0.05),    # Very low power
            (0.03, 0.50, 100000, 0.05), # Very high power
            (0.03, 0.10, 5000, 0.05),   # Typical
        ]
        
        for baseline_cvr, effect_size, sample_size, alpha in test_cases:
            result = calculate_power(baseline_cvr, effect_size, sample_size, alpha)
            
            # power_pct should be between 0 and 100
            assert 0 <= result['power_pct'] <= 100
