"""
Unit tests for test reliability validator.

Tests the validate_test_reliability() function to ensure correct validation checks,
reliability score calculation, warning generation, and recommendation production.

**Validates: Requirements 3.1-3.5, 11.1-11.7**
"""

import pytest
from analytics.conversion import validate_test_reliability


class TestReliableTestScenario:
    """Tests for a reliable test scenario where all checks pass."""
    
    def test_all_checks_pass_reliable_test(self):
        """Test validation of a reliable test with all checks passing.
        
        **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=350,
            variant_visitors=10000,
            variant_conversions=420,
            test_duration_days=14,
            observed_lift=20.0
        )
        
        # Verify all required keys are present
        assert 'is_reliable' in result
        assert 'reliability_score' in result
        assert 'checks' in result
        assert 'warnings' in result
        assert 'recommendations' in result
        
        # Test should be reliable
        assert result['is_reliable'] is True
        
        # Reliability score should be 100 (all checks pass)
        assert result['reliability_score'] == 100
        
        # All checks should pass
        assert result['checks']['minimum_sample_size'] == True
        assert result['checks']['minimum_duration'] == True
        assert result['checks']['business_cycles'] == True
        assert result['checks']['twymans_law'] == True
        assert result['checks']['statistical_significance'] == True
        
        # No warnings for reliable test
        assert len(result['warnings']) == 0
        
        # Recommendations should be empty or minimal
        assert isinstance(result['recommendations'], list)
    
    def test_reliability_score_calculation_all_checks(self):
        """Test that reliability score is correctly calculated when all checks pass.
        
        **Validates: Requirement 11.7**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=400,
            variant_visitors=10000,
            variant_conversions=480,
            test_duration_days=21,
            observed_lift=20.0
        )
        
        # Score should be 100 (30 + 25 + 20 + 15 + 10)
        assert result['reliability_score'] == 100
    
    def test_significance_result_included(self):
        """Test that significance result is included in output.
        
        **Validates: Requirement 11.6**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=350,
            variant_visitors=10000,
            variant_conversions=420,
            test_duration_days=14,
            observed_lift=20.0
        )
        
        # Significance result should be included
        assert 'significance_result' in result
        assert 'p_value' in result['significance_result']
        assert 'is_significant' in result['significance_result']


class TestUnreliableSmallSample:
    """Tests for unreliable test due to small sample size."""
    
    def test_small_sample_size_warning(self):
        """Test that small sample size (<350) generates warning.
        
        **Validates: Requirements 3.1, 11.1**
        """
        result = validate_test_reliability(
            control_visitors=1000,
            control_conversions=30,  # < 350
            variant_visitors=1000,
            variant_conversions=36,
            test_duration_days=14,
            observed_lift=20.0
        )
        
        # Test should be unreliable
        assert result['is_reliable'] is False
        
        # Sample size check should fail
        assert result['checks']['minimum_sample_size'] is False
        
        # Should have sample size warning
        assert len(result['warnings']) > 0
        assert any('Small Sample Size' in w for w in result['warnings'])
        assert any('350' in w for w in result['warnings'])
        
        # Should have recommendation
        assert len(result['recommendations']) > 0
        assert any('350' in r for r in result['recommendations'])
    
    def test_small_sample_reduces_score(self):
        """Test that small sample size reduces reliability score.
        
        **Validates: Requirement 11.7**
        """
        # Use parameters that will pass significance check but fail sample size
        # Need larger sample to get significance, but still < 350
        # Using 300 and 360 with 20% lift should be significant
        result = validate_test_reliability(
            control_visitors=1500,
            control_conversions=300,  # 20% CVR
            variant_visitors=1500,
            variant_conversions=360,  # 24% CVR, 20% lift
            test_duration_days=14,
            observed_lift=20.0
        )
        
        # Score should be less than 100 (sample size check failed: -30)
        # Expected: 0 + 25 + 20 + 15 + 10 = 70
        assert result['reliability_score'] == 70
    
    def test_both_variants_must_meet_minimum(self):
        """Test that both control and variant must meet minimum sample size.
        
        **Validates: Requirements 3.1, 11.1**
        """
        # Control has 300, variant has 400 (one below minimum)
        result = validate_test_reliability(
            control_visitors=1000,
            control_conversions=300,  # < 350
            variant_visitors=1000,
            variant_conversions=400,  # >= 350
            test_duration_days=14,
            observed_lift=20.0
        )
        
        # Should fail because min(300, 400) = 300 < 350
        assert result['checks']['minimum_sample_size'] is False
        assert result['is_reliable'] is False


class TestTwymansLawViolation:
    """Tests for Twyman's Law violation detection."""
    
    def test_twyman_violation_high_lift_small_sample(self):
        """Test Twyman's Law violation when lift > 50% and sample size < 1000.
        
        **Validates: Requirements 3.3, 11.4**
        """
        result = validate_test_reliability(
            control_visitors=500,
            control_conversions=50,
            variant_visitors=500,
            variant_conversions=100,  # 100% lift
            test_duration_days=14,
            observed_lift=100.0
        )
        
        # Twyman's Law check should fail
        assert result['checks']['twymans_law'] is False
        
        # Should have Twyman's Law warning
        assert len(result['warnings']) > 0
        assert any('Twyman' in w for w in result['warnings'])
        assert any('50%' in w for w in result['warnings'])
        assert any('1000' in w for w in result['warnings'])
        
        # Should have recommendation
        assert any('1000' in r for r in result['recommendations'])
    
    def test_no_twyman_violation_high_lift_large_sample(self):
        """Test no Twyman's Law violation when lift > 50% but sample size >= 1000.
        
        **Validates: Requirements 3.3, 11.4**
        """
        result = validate_test_reliability(
            control_visitors=2000,
            control_conversions=1000,  # >= 1000
            variant_visitors=2000,
            variant_conversions=2000,  # >= 1000
            test_duration_days=14,
            observed_lift=100.0
        )
        
        # Twyman's Law check should pass (sample size >= 1000)
        assert result['checks']['twymans_law'] is True
        
        # Should not have Twyman's Law warning
        twyman_warnings = [w for w in result['warnings'] if 'Twyman' in w]
        assert len(twyman_warnings) == 0
    
    def test_no_twyman_violation_low_lift(self):
        """Test no Twyman's Law violation when lift <= 50%.
        
        **Validates: Requirements 3.3, 11.4**
        """
        result = validate_test_reliability(
            control_visitors=500,
            control_conversions=50,
            variant_visitors=500,
            variant_conversions=75,  # 50% lift (exactly at threshold)
            test_duration_days=14,
            observed_lift=50.0
        )
        
        # Twyman's Law should not apply (lift <= 50%)
        assert result['checks']['twymans_law'] is True
        
        # Should not have Twyman's Law warning
        twyman_warnings = [w for w in result['warnings'] if 'Twyman' in w]
        assert len(twyman_warnings) == 0
    
    def test_twyman_violation_reduces_score(self):
        """Test that Twyman's Law violation reduces reliability score.
        
        **Validates: Requirement 11.7**
        """
        result = validate_test_reliability(
            control_visitors=500,
            control_conversions=50,
            variant_visitors=500,
            variant_conversions=100,
            test_duration_days=14,
            observed_lift=100.0
        )
        
        # Score should be less than 100 (Twyman's Law check failed: -15)
        # Expected: 30 + 25 + 20 + 0 + 10 = 85
        # But sample size check also fails (50 < 350)
        # Score: 0 + 25 + 20 + 0 + 10 = 55
        assert result['reliability_score'] == 55


class TestShortDurationWarning:
    """Tests for short duration warning."""
    
    def test_short_duration_warning(self):
        """Test that short duration (<7 days) generates warning.
        
        **Validates: Requirements 3.2, 11.2**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=350,
            variant_visitors=10000,
            variant_conversions=420,
            test_duration_days=5,  # < 7
            observed_lift=20.0
        )
        
        # Test should be unreliable
        assert result['is_reliable'] is False
        
        # Duration check should fail
        assert result['checks']['minimum_duration'] is False
        
        # Should have duration warning
        assert len(result['warnings']) > 0
        assert any('Short Test Duration' in w for w in result['warnings'])
        assert any('7' in w for w in result['warnings'])
        
        # Should have recommendation
        assert any('7' in r for r in result['recommendations'])
    
    def test_short_duration_reduces_score(self):
        """Test that short duration reduces reliability score.
        
        **Validates: Requirement 11.7**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=350,
            variant_visitors=10000,
            variant_conversions=420,
            test_duration_days=5,  # < 7
            observed_lift=20.0
        )
        
        # Score should be less than 100 (duration check failed: -25)
        # Expected: 30 + 0 + 20 + 15 + 10 = 75
        # But business cycles check also fails (5 < 14)
        # Score: 30 + 0 + 0 + 15 + 10 = 55
        assert result['reliability_score'] == 55
    
    def test_exactly_7_days_passes(self):
        """Test that exactly 7 days passes the duration check.
        
        **Validates: Requirements 3.2, 11.2**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=350,
            variant_visitors=10000,
            variant_conversions=420,
            test_duration_days=7,  # Exactly 7
            observed_lift=20.0
        )
        
        # Duration check should pass
        assert result['checks']['minimum_duration'] is True


class TestInsufficientBusinessCycles:
    """Tests for insufficient business cycles warning."""
    
    def test_insufficient_business_cycles_warning(self):
        """Test that < 2 business cycles generates warning.
        
        **Validates: Requirements 3.4, 11.3**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=350,
            variant_visitors=10000,
            variant_conversions=420,
            test_duration_days=10,  # < 14 days (2 cycles)
            observed_lift=20.0
        )
        
        # Test should be unreliable
        assert result['is_reliable'] is False
        
        # Business cycles check should fail
        assert result['checks']['business_cycles'] is False
        
        # Should have business cycles warning
        assert len(result['warnings']) > 0
        assert any('Business Cycles' in w for w in result['warnings'])
        assert any('2' in w for w in result['warnings'])
        
        # Should have recommendation
        assert any('14' in r for r in result['recommendations'])
    
    def test_insufficient_business_cycles_reduces_score(self):
        """Test that insufficient business cycles reduces reliability score.
        
        **Validates: Requirement 11.7**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=350,
            variant_visitors=10000,
            variant_conversions=420,
            test_duration_days=10,  # < 14 days
            observed_lift=20.0
        )
        
        # Score should be less than 100 (business cycles check failed: -20)
        # Expected: 30 + 25 + 0 + 15 + 10 = 80
        assert result['reliability_score'] == 80
    
    def test_exactly_14_days_passes(self):
        """Test that exactly 14 days (2 cycles) passes the business cycles check.
        
        **Validates: Requirements 3.4, 11.3**
        """
        result = validate_test_reliability(
            control_visitors=10000,
            control_conversions=350,
            variant_visitors=10000,
            variant_conversions=420,
            test_duration_days=14,  # Exactly 14 days (2 cycles)
            observed_lift=20.0
        )
        
        # Business cycles check should pass
        assert result['checks']['business_cycles'] is True


class TestStatisticalSignificance:
    """Tests for statistical significance check."""
    
    def test_not_significant_warning(self):
        """Test that non-significant result generates warning.
        
        **Validates: Requirements 3.5, 11.5**
        """
        # Use parameters that will result in non-significant test
        result = validate_test_reliability(
            control_visitors=1000,
            control_conversions=100,
            variant_visitors=1000,
            variant_conversions=110,  # Small lift, likely not significant
            test_duration_days=14,
            observed_lift=10.0
        )
        
        # Check if test is not significant
        assert result['checks']['statistical_significance'] == False
        
        # Test should be unreliable
        assert result['is_reliable'] == False
        
        # Significance check should fail
        assert result['checks']['statistical_significance'] == False
        
        # Should have significance warning
        assert len(result['warnings']) > 0
        assert any('Not Statistically Significant' in w for w in result['warnings'])
        assert any('p-value' in w.lower() for w in result['warnings'])
        
        # Should have recommendation
        assert any('p-value' in r.lower() for r in result['recommendations'])
    
    def test_not_significant_reduces_score(self):
        """Test that non-significant result reduces reliability score.
        
        **Validates: Requirement 11.7**
        """
        result = validate_test_reliability(
            control_visitors=1000,
            control_conversions=100,
            variant_visitors=1000,
            variant_conversions=110,
            test_duration_days=14,
            observed_lift=10.0
        )
        
        # Score should be less than 100 (significance check failed: -10)
        # Expected: 30 + 25 + 20 + 15 + 0 = 90
        # But sample size check also fails (100 < 350)
        # Score: 0 + 25 + 20 + 15 + 0 = 60
        assert result['reliability_score'] == 60


class TestMultipleFailures:
    """Tests for tests with multiple failed checks."""
    
    def test_multiple_checks_fail(self):
        """Test validation when multiple checks fail.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
        """
        result = validate_test_reliability(
            control_visitors=500,
            control_conversions=30,  # < 350
            variant_visitors=500,
            variant_conversions=36,  # < 350
            test_duration_days=5,    # < 7
            observed_lift=100.0      # > 50%
        )
        
        # Test should be unreliable
        assert result['is_reliable'] is False
        
        # Multiple checks should fail
        assert result['checks']['minimum_sample_size'] is False
        assert result['checks']['minimum_duration'] is False
        assert result['checks']['business_cycles'] is False
        assert result['checks']['twymans_law'] is False
        
        # Should have multiple warnings
        assert len(result['warnings']) >= 4
        
        # Should have multiple recommendations
        assert len(result['recommendations']) >= 1
    
    def test_all_checks_fail_score(self):
        """Test reliability score when all checks fail.
        
        **Validates: Requirement 11.7**
        """
        result = validate_test_reliability(
            control_visitors=500,
            control_conversions=30,
            variant_visitors=500,
            variant_conversions=36,
            test_duration_days=5,
            observed_lift=100.0
        )
        
        # Score should be 0 (all checks failed)
        assert result['reliability_score'] == 0


class TestReliabilityScoreBounds:
    """Tests for reliability score bounds and calculation."""
    
    def test_score_is_between_0_and_100(self):
        """Test that reliability score is always between 0 and 100.
        
        **Validates: Requirement 11.7**
        """
        # Test various scenarios
        test_cases = [
            # (control_visitors, control_conversions, variant_visitors, variant_conversions, duration, lift)
            (10000, 350, 10000, 420, 14, 20.0),   # All pass
            (500, 30, 500, 36, 5, 100.0),          # All fail
            (10000, 350, 10000, 420, 5, 20.0),     # Duration fails
            (500, 30, 500, 36, 14, 20.0),          # Sample size fails
        ]
        
        for params in test_cases:
            result = validate_test_reliability(
                control_visitors=params[0],
                control_conversions=params[1],
                variant_visitors=params[2],
                variant_conversions=params[3],
                test_duration_days=params[4],
                observed_lift=params[5]
            )
            
            # Score should be between 0 and 100
            assert 0 <= result['reliability_score'] <= 100
            assert isinstance(result['reliability_score'], int)
    
    def test_score_monotonically_increases_with_passed_checks(self):
        """Test that score increases as more checks pass.
        
        **Validates: Requirement 11.7**
        """
        # Base case: all checks pass
        result_all_pass = validate_test_reliability(
            control_visitors=10000,
            control_conversions=400,
            variant_visitors=10000,
            variant_conversions=480,
            test_duration_days=21,
            observed_lift=20.0
        )
        
        # One check fails
        result_one_fail = validate_test_reliability(
            control_visitors=1000,
            control_conversions=30,
            variant_visitors=10000,
            variant_conversions=480,
            test_duration_days=21,
            observed_lift=20.0
        )
        
        # All pass should have higher score
        assert result_all_pass['reliability_score'] > result_one_fail['reliability_score']


class TestRecommendations:
    """Tests for recommendations generation."""
    
    def test_recommendations_include_failed_checks(self):
        """Test that recommendations include list of failed checks.
        
        **Validates: Requirement 11.6**
        """
        result = validate_test_reliability(
            control_visitors=500,
            control_conversions=30,
            variant_visitors=500,
            variant_conversions=36,
            test_duration_days=5,
            observed_lift=100.0
        )
        
        # Should have recommendations
        assert len(result['recommendations']) > 0
        
        # Last recommendation should include failed checks
        last_recommendation = result['recommendations'][-1]
        assert 'failed checks' in last_recommendation.lower() or 'failed' in last_recommendation.lower()
    
    def test_recommendations_are_actionable(self):
        """Test that recommendations are actionable and specific.
        
        **Validates: Requirement 11.6**
        """
        result = validate_test_reliability(
            control_visitors=500,
            control_conversions=30,
            variant_visitors=500,
            variant_conversions=36,
            test_duration_days=5,
            observed_lift=100.0
        )
        
        # All recommendations should be strings
        for rec in result['recommendations']:
            assert isinstance(rec, str)
            assert len(rec) > 10  # Should be meaningful


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_zero_conversions(self):
        """Test validation with zero conversions.
        
        **Validates: Requirements 3.1, 11.1**
        """
        result = validate_test_reliability(
            control_visitors=1000,
            control_conversions=0,
            variant_visitors=1000,
            variant_conversions=0,
            test_duration_days=14,
            observed_lift=0.0
        )
        
        # Should be unreliable (sample size check fails)
        assert result['is_reliable'] is False
        assert result['checks']['minimum_sample_size'] is False
    
    def test_very_high_lift(self):
        """Test validation with very high lift (>100%).
        
        **Validates: Requirements 3.3, 11.4**
        """
        result = validate_test_reliability(
            control_visitors=2000,
            control_conversions=100,
            variant_visitors=2000,
            variant_conversions=500,  # 400% lift
            test_duration_days=14,
            observed_lift=400.0
        )
        
        # Twyman's Law should apply (lift > 50%)
        # With 100 conversions, sample size check should fail
        assert result['checks']['twymans_law'] is False
    
    def test_exactly_threshold_values(self):
        """Test validation with values exactly at thresholds.
        
        **Validates: Requirements 3.1, 3.2, 3.4**
        """
        # Exactly at minimum sample size (350)
        result1 = validate_test_reliability(
            control_visitors=1000,
            control_conversions=350,
            variant_visitors=1000,
            variant_conversions=350,
            test_duration_days=14,
            observed_lift=20.0
        )
        
        # Should pass sample size check
        assert result1['checks']['minimum_sample_size'] is True
        
        # Exactly at minimum duration (7 days)
        result2 = validate_test_reliability(
            control_visitors=1000,
            control_conversions=400,
            variant_visitors=1000,
            variant_conversions=480,
            test_duration_days=7,
            observed_lift=20.0
        )
        
        # Should pass duration check
        assert result2['checks']['minimum_duration'] is True
        
        # Exactly at business cycles (14 days = 2 cycles)
        result3 = validate_test_reliability(
            control_visitors=1000,
            control_conversions=400,
            variant_visitors=1000,
            variant_conversions=480,
            test_duration_days=14,
            observed_lift=20.0
        )
        
        # Should pass business cycles check
        assert result3['checks']['business_cycles'] is True
