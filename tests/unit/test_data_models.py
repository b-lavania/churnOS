"""
Unit tests for CRO Analytics data models.

Tests the TestConfiguration, TestResult, ValidationResult, and CROMetrics
dataclasses to ensure they are properly defined and functional.
"""

import pytest
from analytics.conversion import (
    TestConfiguration,
    TestResult,
    ValidationResult,
    CROMetrics,
)


class TestTestConfiguration:
    """Tests for TestConfiguration dataclass."""
    
    def test_create_valid_configuration(self):
        """Test creating a valid test configuration."""
        config = TestConfiguration(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.80,
            alpha=0.05,
            n_variants=2,
            daily_traffic=1000
        )
        
        assert config.baseline_cvr == 0.03
        assert config.mde == 0.10
        assert config.power == 0.80
        assert config.alpha == 0.05
        assert config.n_variants == 2
        assert config.daily_traffic == 1000
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = TestConfiguration(
            baseline_cvr=0.03,
            mde=0.10
        )
        
        assert config.power == 0.80
        assert config.alpha == 0.05
        assert config.n_variants == 2
        assert config.daily_traffic == 0
    
    def test_validate_valid_configuration(self):
        """Test validation passes for valid configuration."""
        config = TestConfiguration(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.80,
            alpha=0.05
        )
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validate_invalid_baseline_cvr_too_low(self):
        """Test validation fails for baseline_cvr below minimum."""
        config = TestConfiguration(
            baseline_cvr=0.0005,  # Below 0.001
            mde=0.10
        )
        
        errors = config.validate()
        assert len(errors) == 1
        assert "baseline_cvr must be between 0.001 and 1.0" in errors[0]
    
    def test_validate_invalid_baseline_cvr_too_high(self):
        """Test validation fails for baseline_cvr above maximum."""
        config = TestConfiguration(
            baseline_cvr=1.5,  # Above 1.0
            mde=0.10
        )
        
        errors = config.validate()
        assert len(errors) == 1
        assert "baseline_cvr must be between 0.001 and 1.0" in errors[0]
    
    def test_validate_invalid_mde_too_low(self):
        """Test validation fails for mde below minimum."""
        config = TestConfiguration(
            baseline_cvr=0.03,
            mde=0.005  # Below 0.01
        )
        
        errors = config.validate()
        assert len(errors) == 1
        assert "mde must be between 0.01 and 1.0" in errors[0]
    
    def test_validate_invalid_power_too_low(self):
        """Test validation fails for power below minimum."""
        config = TestConfiguration(
            baseline_cvr=0.03,
            mde=0.10,
            power=0.40  # Below 0.50
        )
        
        errors = config.validate()
        assert len(errors) == 1
        assert "power must be between 0.50 and 0.99" in errors[0]
    
    def test_validate_invalid_alpha_too_high(self):
        """Test validation fails for alpha above maximum."""
        config = TestConfiguration(
            baseline_cvr=0.03,
            mde=0.10,
            alpha=0.25  # Above 0.20
        )
        
        errors = config.validate()
        assert len(errors) == 1
        assert "alpha must be between 0.01 and 0.20" in errors[0]
    
    def test_validate_invalid_n_variants(self):
        """Test validation fails for n_variants less than 2."""
        config = TestConfiguration(
            baseline_cvr=0.03,
            mde=0.10,
            n_variants=1  # Less than 2
        )
        
        errors = config.validate()
        assert len(errors) == 1
        assert "n_variants must be at least 2" in errors[0]
    
    def test_validate_invalid_daily_traffic(self):
        """Test validation fails for negative daily_traffic."""
        config = TestConfiguration(
            baseline_cvr=0.03,
            mde=0.10,
            daily_traffic=-100  # Negative
        )
        
        errors = config.validate()
        assert len(errors) == 1
        assert "daily_traffic must be non-negative" in errors[0]
    
    def test_validate_multiple_errors(self):
        """Test validation returns all errors for multiple invalid fields."""
        config = TestConfiguration(
            baseline_cvr=1.5,  # Invalid
            mde=0.005,  # Invalid
            power=0.40,  # Invalid
            alpha=0.25,  # Invalid
            n_variants=1,  # Invalid
            daily_traffic=-100  # Invalid
        )
        
        errors = config.validate()
        assert len(errors) == 6


class TestTestResult:
    """Tests for TestResult dataclass."""
    
    def test_create_test_result(self):
        """Test creating a test result."""
        result = TestResult(
            control_visitors=10000,
            control_conversions=300,
            variant_visitors=10000,
            variant_conversions=330,
            test_duration_days=14,
            control_rate=3.0,
            variant_rate=3.3,
            lift_pct=10.0,
            p_value=0.045,
            is_significant=True,
            confidence_interval=(0.1, 0.5),
            confidence_level=0.95
        )
        
        assert result.control_visitors == 10000
        assert result.control_conversions == 300
        assert result.variant_visitors == 10000
        assert result.variant_conversions == 330
        assert result.test_duration_days == 14
        assert result.control_rate == 3.0
        assert result.variant_rate == 3.3
        assert result.lift_pct == 10.0
        assert result.p_value == 0.045
        assert result.is_significant is True
        assert result.confidence_interval == (0.1, 0.5)
        assert result.confidence_level == 0.95


class TestValidationResult:
    """Tests for ValidationResult dataclass."""
    
    def test_create_validation_result(self):
        """Test creating a validation result."""
        result = ValidationResult(
            is_reliable=True,
            reliability_score=85,
            checks={
                'minimum_sample_size': True,
                'minimum_duration': True,
                'business_cycles': True,
                'twyman_law': True,
                'statistical_significance': True
            },
            warnings=[],
            recommendations=[]
        )
        
        assert result.is_reliable is True
        assert result.reliability_score == 85
        assert len(result.checks) == 5
        assert len(result.warnings) == 0
        assert len(result.recommendations) == 0
    
    def test_to_dict(self):
        """Test converting validation result to dictionary."""
        result = ValidationResult(
            is_reliable=False,
            reliability_score=45,
            checks={
                'minimum_sample_size': False,
                'minimum_duration': True
            },
            warnings=['Sample size too small'],
            recommendations=['Increase sample size to at least 350 per variant']
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['is_reliable'] is False
        assert result_dict['reliability_score'] == 45
        assert result_dict['checks']['minimum_sample_size'] is False
        assert result_dict['checks']['minimum_duration'] is True
        assert len(result_dict['warnings']) == 1
        assert len(result_dict['recommendations']) == 1


class TestCROMetrics:
    """Tests for CROMetrics dataclass."""
    
    def test_create_cro_metrics(self):
        """Test creating CRO metrics."""
        metrics = CROMetrics(
            bounce_rate=45.5,
            above_fold_engagement=65.2,
            below_fold_engagement=34.8,
            primary_conversion_rate=3.2,
            secondary_conversion_rates={
                'newsletter_signup': 8.5,
                'wishlist_add': 12.3
            },
            ctr_by_element={
                'hero_cta': 15.2,
                'footer_cta': 5.8
            },
            avg_time_on_page=125.5,
            date_range=('2024-01-01', '2024-01-31')
        )
        
        assert metrics.bounce_rate == 45.5
        assert metrics.above_fold_engagement == 65.2
        assert metrics.below_fold_engagement == 34.8
        assert metrics.primary_conversion_rate == 3.2
        assert len(metrics.secondary_conversion_rates) == 2
        assert metrics.secondary_conversion_rates['newsletter_signup'] == 8.5
        assert len(metrics.ctr_by_element) == 2
        assert metrics.ctr_by_element['hero_cta'] == 15.2
        assert metrics.avg_time_on_page == 125.5
        assert metrics.date_range == ('2024-01-01', '2024-01-31')
