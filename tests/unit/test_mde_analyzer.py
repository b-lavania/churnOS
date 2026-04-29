"""
Unit tests for MDE analyzer.

Tests the calculate_mde() function to ensure correct calculations, input validation,
inverse relationship with sample size, and e-commerce CVR range note generation.

**Validates: Requirements 4.1, 4.2, 4.4, 4.6**
"""

import pytest
import numpy as np
from analytics.conversion import calculate_mde, calculate_sample_size


class TestMDECalculation:
    """Tests for MDE calculation correctness."""
    
    def test_typical_ecommerce_scenario(self):
        """Test MDE calculation for typical e-commerce scenario.
        
        **Validates: Requirements 4.1, 4.2**
        """
        result = calculate_mde(
            baseline_cvr=0.03,  # 3% CVR - typical for e-commerce
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        # Verify all required keys are present
        assert 'mde_relative' in result
        assert 'mde_absolute' in result
        assert 'target_cvr' in result
        assert 'baseline_cvr' in result
        assert 'sample_size_per_variant' in result
        assert 'power' in result
        assert 'alpha' in result
        assert 'ecommerce_note' in result
        
        # Verify MDE values are positive
        assert result['mde_relative'] > 0
        assert result['mde_absolute'] > 0
        
        # Verify target CVR is greater than baseline
        assert result['target_cvr'] > result['baseline_cvr']
        
        # Verify parameters are preserved
        assert result['baseline_cvr'] == 0.03
        assert result['sample_size_per_variant'] == 5000
        assert result['power'] == 0.80
        assert result['alpha'] == 0.05
    
    def test_mde_dual_representation_consistency(self):
        """Test that absolute and relative MDE are mathematically consistent.
        
        **Validates: Requirements 4.2**
        """
        result = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        # Verify: absolute_mde = baseline_cvr * relative_mde
        expected_absolute = result['baseline_cvr'] * result['mde_relative']
        assert abs(result['mde_absolute'] - expected_absolute) < 1e-10
        
        # Verify: target_cvr = baseline_cvr + absolute_mde
        expected_target = result['baseline_cvr'] + result['mde_absolute']
        assert abs(result['target_cvr'] - expected_target) < 1e-10
    
    def test_larger_sample_produces_smaller_mde(self):
        """Test that larger samples can detect smaller effects (smaller MDE).
        
        **Validates: Requirements 4.1**
        """
        result_small_sample = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=1000,
            power=0.80,
            alpha=0.05
        )
        
        result_large_sample = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=10000,
            power=0.80,
            alpha=0.05
        )
        
        # Larger sample should produce smaller MDE
        assert result_large_sample['mde_relative'] < result_small_sample['mde_relative']
        assert result_large_sample['mde_absolute'] < result_small_sample['mde_absolute']
    
    def test_higher_power_produces_larger_mde(self):
        """Test that higher power requires larger MDE (for same sample size).
        
        **Validates: Requirements 4.1**
        """
        result_low_power = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=5000,
            power=0.70,
            alpha=0.05
        )
        
        result_high_power = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=5000,
            power=0.90,
            alpha=0.05
        )
        
        # Higher power should produce larger MDE (less stringent)
        assert result_high_power['mde_relative'] > result_low_power['mde_relative']
        assert result_high_power['mde_absolute'] > result_low_power['mde_absolute']
    
    def test_more_stringent_alpha_produces_larger_mde(self):
        """Test that more stringent alpha (lower) produces larger MDE.
        
        **Validates: Requirements 4.1**
        """
        result_lenient_alpha = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.10
        )
        
        result_stringent_alpha = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.01
        )
        
        # More stringent alpha should produce larger MDE
        assert result_stringent_alpha['mde_relative'] > result_lenient_alpha['mde_relative']
        assert result_stringent_alpha['mde_absolute'] > result_lenient_alpha['mde_absolute']


class TestMDESampleSizeInverseRelationship:
    """Tests for inverse relationship between MDE and sample size calculations."""
    
    def test_round_trip_sample_size_to_mde(self):
        """Test that MDE calculation is inverse of sample size calculation.
        
        **Validates: Requirements 4.1, 4.6**
        """
        baseline_cvr = 0.03
        mde_input = 0.10
        power = 0.80
        alpha = 0.05
        
        # Calculate sample size for given MDE
        ss_result = calculate_sample_size(baseline_cvr, mde_input, power, alpha)
        sample_size = ss_result['sample_size_per_variant']
        
        # Calculate MDE for that sample size
        mde_result = calculate_mde(baseline_cvr, sample_size, power, alpha)
        
        # MDE should match original input (within 1% tolerance)
        assert abs(mde_result['mde_relative'] - mde_input) / mde_input < 0.01
    
    def test_round_trip_multiple_scenarios(self):
        """Test round-trip for multiple test scenarios.
        
        **Validates: Requirements 4.1, 4.6**
        """
        test_scenarios = [
            (0.02, 0.05, 0.80, 0.05),  # Low CVR, small MDE
            (0.05, 0.15, 0.85, 0.05),  # Medium CVR, medium MDE
            (0.10, 0.20, 0.90, 0.01),  # High CVR, large MDE, stringent alpha
            (0.03, 0.10, 0.70, 0.10),  # Typical, low power, lenient alpha
        ]
        
        for baseline_cvr, mde_input, power, alpha in test_scenarios:
            # Calculate sample size for given MDE
            ss_result = calculate_sample_size(baseline_cvr, mde_input, power, alpha)
            sample_size = ss_result['sample_size_per_variant']
            
            # Calculate MDE for that sample size
            mde_result = calculate_mde(baseline_cvr, sample_size, power, alpha)
            
            # MDE should match original input (within 1% tolerance)
            tolerance = 0.01
            assert abs(mde_result['mde_relative'] - mde_input) / mde_input < tolerance, \
                f"Round-trip failed for scenario: baseline={baseline_cvr}, mde={mde_input}, power={power}, alpha={alpha}"


class TestEcommerceNoteGeneration:
    """Tests for e-commerce CVR range note generation."""
    
    def test_ecommerce_note_for_typical_cvr(self):
        """Test that e-commerce note is generated for typical CVR (2-5%).
        
        **Validates: Requirements 4.4**
        """
        # Test at lower bound (2%)
        result_lower = calculate_mde(
            baseline_cvr=0.02,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        assert result_lower['ecommerce_note'] is not None
        assert 'e-commerce' in result_lower['ecommerce_note'].lower()
        assert '2-5%' in result_lower['ecommerce_note'] or '2-5' in result_lower['ecommerce_note']
        
        # Test at midpoint (3.5%)
        result_mid = calculate_mde(
            baseline_cvr=0.035,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        assert result_mid['ecommerce_note'] is not None
        assert 'e-commerce' in result_mid['ecommerce_note'].lower()
        
        # Test at upper bound (5%)
        result_upper = calculate_mde(
            baseline_cvr=0.05,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        assert result_upper['ecommerce_note'] is not None
        assert 'e-commerce' in result_upper['ecommerce_note'].lower()
    
    def test_no_ecommerce_note_for_low_cvr(self):
        """Test that no e-commerce note for CVR below 2%.
        
        **Validates: Requirements 4.4**
        """
        result = calculate_mde(
            baseline_cvr=0.01,  # 1% - below typical range
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        assert result['ecommerce_note'] is None
    
    def test_no_ecommerce_note_for_high_cvr(self):
        """Test that no e-commerce note for CVR above 5%.
        
        **Validates: Requirements 4.4**
        """
        result = calculate_mde(
            baseline_cvr=0.10,  # 10% - above typical range
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        assert result['ecommerce_note'] is None
    
    def test_ecommerce_note_content(self):
        """Test that e-commerce note contains helpful information.
        
        **Validates: Requirements 4.4**
        """
        result = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        note = result['ecommerce_note']
        assert note is not None
        
        # Should mention it's typical
        assert 'typical' in note.lower()
        
        # Should mention the range
        assert '2' in note and '5' in note
        
        # Should be encouraging/informative
        assert 'good baseline' in note.lower() or 'baseline' in note.lower()


class TestInputValidation:
    """Tests for input validation and error messages."""
    
    def test_invalid_baseline_cvr_too_low(self):
        """Test validation error for baseline_cvr below minimum (0.001).
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=0.0005,  # Below 0.001
                sample_size_per_variant=5000,
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Baseline CVR must be between 0.1% and 100%" in error_message
    
    def test_invalid_baseline_cvr_too_high(self):
        """Test validation error for baseline_cvr above maximum (1.0).
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=1.5,  # Above 1.0
                sample_size_per_variant=5000,
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Baseline CVR must be between 0.1% and 100%" in error_message
    
    def test_invalid_sample_size_zero(self):
        """Test validation error for sample_size_per_variant of zero.
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=0.03,
                sample_size_per_variant=0,  # Invalid
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Sample size per variant must be greater than 0" in error_message
    
    def test_invalid_sample_size_negative(self):
        """Test validation error for negative sample_size_per_variant.
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=0.03,
                sample_size_per_variant=-1000,  # Invalid
                power=0.80,
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Sample size per variant must be greater than 0" in error_message
    
    def test_invalid_power_too_low(self):
        """Test validation error for power below minimum (0.50).
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=0.03,
                sample_size_per_variant=5000,
                power=0.40,  # Below 0.50
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Statistical power must be between 50% and 99%" in error_message
    
    def test_invalid_power_too_high(self):
        """Test validation error for power above maximum (0.99).
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=0.03,
                sample_size_per_variant=5000,
                power=0.995,  # Above 0.99
                alpha=0.05
            )
        
        error_message = str(exc_info.value)
        assert "Statistical power must be between 50% and 99%" in error_message
    
    def test_invalid_alpha_too_low(self):
        """Test validation error for alpha below minimum (0.01).
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=0.03,
                sample_size_per_variant=5000,
                power=0.80,
                alpha=0.005  # Below 0.01
            )
        
        error_message = str(exc_info.value)
        assert "Significance level (alpha) must be between 1% and 20%" in error_message
    
    def test_invalid_alpha_too_high(self):
        """Test validation error for alpha above maximum (0.20).
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=0.03,
                sample_size_per_variant=5000,
                power=0.80,
                alpha=0.25  # Above 0.20
            )
        
        error_message = str(exc_info.value)
        assert "Significance level (alpha) must be between 1% and 20%" in error_message
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are reported together.
        
        **Validates: Requirements 4.1**
        """
        with pytest.raises(ValueError) as exc_info:
            calculate_mde(
                baseline_cvr=1.5,   # Invalid
                sample_size_per_variant=-1000,  # Invalid
                power=0.40,         # Invalid
                alpha=0.25          # Invalid
            )
        
        error_message = str(exc_info.value)
        # Should contain multiple error messages
        assert "Baseline CVR must be between" in error_message
        assert "Sample size per variant must be greater than 0" in error_message
        assert "Statistical power must be between" in error_message
        assert "Significance level (alpha) must be between" in error_message


class TestBoundaryConditions:
    """Tests for boundary conditions (min/max valid inputs)."""
    
    def test_minimum_valid_inputs(self):
        """Test MDE calculation with minimum valid input values.
        
        **Validates: Requirements 4.1**
        """
        result = calculate_mde(
            baseline_cvr=0.001,  # Minimum valid
            sample_size_per_variant=1,  # Minimum valid
            power=0.50,          # Minimum valid
            alpha=0.20           # Maximum valid (less stringent)
        )
        
        # Should complete without error
        assert result['mde_relative'] > 0
        assert result['mde_absolute'] > 0
        assert result['baseline_cvr'] == 0.001
        assert result['power'] == 0.50
        assert result['alpha'] == 0.20
    
    def test_maximum_valid_inputs(self):
        """Test MDE calculation with maximum valid input values.
        
        **Validates: Requirements 4.1**
        """
        result = calculate_mde(
            baseline_cvr=0.50,   # High but valid
            sample_size_per_variant=1_000_000,  # Very large
            power=0.99,          # Maximum valid
            alpha=0.01           # Minimum valid (most stringent)
        )
        
        # Should complete without error
        assert result['mde_relative'] > 0
        assert result['mde_absolute'] > 0
        assert result['baseline_cvr'] == 0.50
        assert result['power'] == 0.99
        assert result['alpha'] == 0.01
    
    def test_very_large_sample_produces_very_small_mde(self):
        """Test that very large samples produce very small detectable effects.
        
        **Validates: Requirements 4.1**
        """
        result = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=1_000_000,  # Very large
            power=0.80,
            alpha=0.05
        )
        
        # MDE should be very small (less than 3%)
        assert result['mde_relative'] < 0.03
        assert result['mde_absolute'] < 0.001  # Less than 0.1 percentage points
    
    def test_small_sample_produces_large_mde(self):
        """Test that small samples produce large detectable effects.
        
        **Validates: Requirements 4.1**
        """
        result = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=100,  # Small
            power=0.80,
            alpha=0.05
        )
        
        # MDE should be relatively large
        assert result['mde_relative'] > 0.20  # More than 20%
        assert result['mde_absolute'] > 0.006  # More than 0.6 percentage points


class TestTargetCVRCalculation:
    """Tests for target CVR calculation."""
    
    def test_target_cvr_within_valid_range(self):
        """Test that target CVR stays within valid range [0, 1].
        
        **Validates: Requirements 4.2**
        """
        test_cases = [
            (0.001, 1000),
            (0.03, 5000),
            (0.10, 10000),
            (0.50, 50000),
        ]
        
        for baseline_cvr, sample_size in test_cases:
            result = calculate_mde(
                baseline_cvr=baseline_cvr,
                sample_size_per_variant=sample_size,
                power=0.80,
                alpha=0.05
            )
            
            # Target CVR should be within valid range
            assert 0 <= result['target_cvr'] <= 1.0, \
                f"Target CVR {result['target_cvr']} out of range for baseline {baseline_cvr}"
    
    def test_target_cvr_greater_than_baseline(self):
        """Test that target CVR is always greater than baseline CVR.
        
        **Validates: Requirements 4.2**
        """
        result = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        assert result['target_cvr'] > result['baseline_cvr']
    
    def test_target_cvr_calculation_consistency(self):
        """Test that target_cvr = baseline_cvr + mde_absolute.
        
        **Validates: Requirements 4.2**
        """
        result = calculate_mde(
            baseline_cvr=0.03,
            sample_size_per_variant=5000,
            power=0.80,
            alpha=0.05
        )
        
        expected_target = result['baseline_cvr'] + result['mde_absolute']
        assert abs(result['target_cvr'] - expected_target) < 1e-10


class TestMonotonicity:
    """Tests for monotonic relationships."""
    
    def test_mde_monotonicity_with_sample_size(self):
        """Test that MDE decreases monotonically as sample size increases.
        
        **Validates: Requirements 4.1**
        """
        sample_sizes = [100, 500, 1000, 5000, 10000, 50000]
        mdes = []
        
        for sample_size in sample_sizes:
            result = calculate_mde(
                baseline_cvr=0.03,
                sample_size_per_variant=sample_size,
                power=0.80,
                alpha=0.05
            )
            mdes.append(result['mde_relative'])
        
        # MDE should decrease as sample size increases
        for i in range(len(mdes) - 1):
            assert mdes[i] > mdes[i + 1], \
                f"MDE not monotonically decreasing: {mdes[i]} > {mdes[i+1]}"
    
    def test_mde_monotonicity_with_power(self):
        """Test that MDE increases monotonically as power increases.
        
        **Validates: Requirements 4.1**
        """
        powers = [0.50, 0.60, 0.70, 0.80, 0.90, 0.99]
        mdes = []
        
        for power in powers:
            result = calculate_mde(
                baseline_cvr=0.03,
                sample_size_per_variant=5000,
                power=power,
                alpha=0.05
            )
            mdes.append(result['mde_relative'])
        
        # MDE should increase as power increases
        for i in range(len(mdes) - 1):
            assert mdes[i] < mdes[i + 1], \
                f"MDE not monotonically increasing with power: {mdes[i]} < {mdes[i+1]}"
