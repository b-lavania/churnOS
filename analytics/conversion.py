"""
Conversion funnel analytics : funnel summary, drop-off analysis, segment breakdowns, A/B testing.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
from scipy import stats


# ============================================================================
# Data Models for CRO Analytics Enhancement
# ============================================================================

@dataclass
class TestConfiguration:
    """Configuration for an A/B or multivariate test.
    
    Attributes:
        baseline_cvr: Current conversion rate (0.001 to 1.0)
        mde: Minimum detectable effect as relative change (0.01 to 1.0)
        power: Statistical power (0.50 to 0.99), default 0.80
        alpha: Significance level (0.01 to 0.20), default 0.05
        n_variants: Number of variants including control (default 2)
        daily_traffic: Daily visitor count (default 0)
    """
    baseline_cvr: float
    mde: float
    power: float = 0.80
    alpha: float = 0.05
    n_variants: int = 2
    daily_traffic: int = 0
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors.
        
        Returns:
            List of error messages. Empty list if all validations pass.
        """
        errors = []
        
        if not (0.001 <= self.baseline_cvr <= 1.0):
            errors.append(
                f"baseline_cvr must be between 0.001 and 1.0 (0.1% to 100%). "
                f"You entered {self.baseline_cvr:.4f}. "
                f"Conversion rates below 0.1% are extremely rare and may indicate data quality issues."
            )
        
        if not (0.01 <= self.mde <= 1.0):
            errors.append(
                f"mde must be between 0.01 and 1.0 (1% to 100% relative change). "
                f"You entered {self.mde:.4f}. "
                f"Effects below 1% are very difficult to detect reliably."
            )
        
        if not (0.50 <= self.power <= 0.99):
            errors.append(
                f"power must be between 0.50 and 0.99 (50% to 99%). "
                f"You entered {self.power:.4f}. "
                f"Statistical power below 50% means you're more likely to miss real effects than detect them."
            )
        
        if not (0.01 <= self.alpha <= 0.20):
            errors.append(
                f"alpha must be between 0.01 and 0.20 (1% to 20%). "
                f"You entered {self.alpha:.4f}. "
                f"Significance levels outside this range are rarely used in practice."
            )
        
        if self.n_variants < 2:
            errors.append(
                f"n_variants must be at least 2 (control + variant). "
                f"You entered {self.n_variants}."
            )
        
        if self.daily_traffic < 0:
            errors.append(
                f"daily_traffic must be non-negative. "
                f"You entered {self.daily_traffic}."
            )
        
        return errors


@dataclass
class TestResult:
    """Results from an A/B test.
    
    Attributes:
        control_visitors: Number of visitors in control group
        control_conversions: Number of conversions in control group
        variant_visitors: Number of visitors in variant group
        variant_conversions: Number of conversions in variant group
        test_duration_days: Duration of test in days
        control_rate: Control conversion rate (as percentage)
        variant_rate: Variant conversion rate (as percentage)
        lift_pct: Percentage lift from control to variant
        p_value: Statistical significance p-value
        is_significant: Whether result is statistically significant
        confidence_interval: Tuple of (lower, upper) bounds for lift
        confidence_level: Confidence level used (e.g., 0.95 for 95%)
    """
    control_visitors: int
    control_conversions: int
    variant_visitors: int
    variant_conversions: int
    test_duration_days: int
    control_rate: float
    variant_rate: float
    lift_pct: float
    p_value: float
    is_significant: bool
    confidence_interval: tuple[float, float]
    confidence_level: float


@dataclass
class ValidationResult:
    """Results from test reliability validation.
    
    Attributes:
        is_reliable: Overall reliability assessment
        reliability_score: Score from 0-100 based on checks passed
        checks: Dictionary mapping check names to pass/fail status
        warnings: List of warning messages for failed checks
        recommendations: List of actionable recommendations
    """
    is_reliable: bool
    reliability_score: int  # 0-100
    checks: dict[str, bool]
    warnings: list[str]
    recommendations: list[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of validation result.
        """
        return {
            'is_reliable': self.is_reliable,
            'reliability_score': self.reliability_score,
            'checks': self.checks,
            'warnings': self.warnings,
            'recommendations': self.recommendations
        }


@dataclass
class CROMetrics:
    """Comprehensive CRO metrics.
    
    Attributes:
        bounce_rate: Percentage of single-page sessions
        above_fold_engagement: Engagement rate for above-the-fold content
        below_fold_engagement: Engagement rate for below-the-fold content
        primary_conversion_rate: Primary conversion goal rate
        secondary_conversion_rates: Dictionary of secondary goal rates
        ctr_by_element: Dictionary of click-through rates by element
        avg_time_on_page: Average time spent on page (seconds)
        date_range: Tuple of (start_date, end_date) for metrics
    """
    bounce_rate: float
    above_fold_engagement: float
    below_fold_engagement: float
    primary_conversion_rate: float
    secondary_conversion_rates: dict[str, float]
    ctr_by_element: dict[str, float]
    avg_time_on_page: float
    date_range: tuple[str, str]


# ============================================================================
# CRO Analytics Enhancement Functions
# ============================================================================

def calculate_sample_size(
    baseline_cvr: float,
    mde: float,
    power: float = 0.80,
    alpha: float = 0.05,
    n_variants: int = 2
) -> dict:
    """
    Calculate required sample size for A/B test using two-proportion z-test formula.
    
    Args:
        baseline_cvr: Current conversion rate (0.001 to 1.0)
        mde: Minimum detectable effect as relative change (0.01 to 1.0)
        power: Statistical power (0.50 to 0.99), default 0.80
        alpha: Significance level (0.01 to 0.20), default 0.05
        n_variants: Number of variants including control (default 2)
    
    Returns:
        dict with keys:
            - sample_size_per_variant: int
            - total_sample_size: int
            - baseline_cvr: float
            - target_cvr: float (baseline * (1 + mde))
            - mde_absolute: float (absolute percentage point change)
            - mde_relative: float (relative percentage change)
            - power: float
            - alpha: float
            - warnings: list of str
    
    Raises:
        ValueError: If inputs are outside valid ranges
    
    Example:
        >>> result = calculate_sample_size(baseline_cvr=0.03, mde=0.10)
        >>> print(f"Need {result['sample_size_per_variant']} per variant")
    """
    # Input validation
    errors = []
    
    if not (0.001 <= baseline_cvr <= 1.0):
        errors.append(
            f"Baseline CVR must be between 0.1% and 100%. "
            f"You entered {baseline_cvr:.4f}. "
            f"Conversion rates below 0.1% are extremely rare and may indicate data quality issues."
        )
    
    if not (0.01 <= mde <= 1.0):
        errors.append(
            f"MDE must be between 1% and 100% relative change. "
            f"You entered {mde:.4f}. "
            f"Effects below 1% are very difficult to detect reliably."
        )
    
    if not (0.50 <= power <= 0.99):
        errors.append(
            f"Statistical power must be between 50% and 99%. "
            f"You entered {power:.4f}. "
            f"Power below 50% means you're more likely to miss real effects than detect them."
        )
    
    if not (0.01 <= alpha <= 0.20):
        errors.append(
            f"Significance level (alpha) must be between 1% and 20%. "
            f"You entered {alpha:.4f}. "
            f"Significance levels outside this range are rarely used in practice."
        )
    
    if n_variants < 2:
        errors.append(
            f"Number of variants must be at least 2 (control + variant). "
            f"You entered {n_variants}."
        )
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Calculate target CVR
    target_cvr = baseline_cvr * (1 + mde)
    
    # Validate that target CVR doesn't exceed 100%
    if target_cvr > 1.0:
        raise ValueError(
            f"Target CVR ({target_cvr:.4f}) exceeds 100%. "
            f"With baseline CVR of {baseline_cvr:.2%} and MDE of {mde:.2%}, "
            f"the target would be {target_cvr:.2%}. "
            f"Please reduce the MDE or baseline CVR."
        )
    
    # Calculate absolute MDE (percentage points)
    mde_absolute = target_cvr - baseline_cvr
    
    # Get z-scores for alpha (two-tailed) and beta (power)
    z_alpha_2 = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Two-proportion z-test formula for sample size
    # n = (Z_α/2 + Z_β)² × [p₁(1-p₁) + p₂(1-p₂)] / (p₂ - p₁)²
    p1 = baseline_cvr
    p2 = target_cvr
    
    numerator = (z_alpha_2 + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
    denominator = (p2 - p1) ** 2
    
    sample_size_per_variant = int(np.ceil(numerator / denominator))
    total_sample_size = sample_size_per_variant * n_variants
    
    # Generate warnings
    warnings = []
    
    # Twyman's Law warning for small samples
    if sample_size_per_variant < 350:
        warnings.append(
            f"⚠️ Twyman's Law Warning: Sample size ({sample_size_per_variant} per variant) "
            f"is below the recommended minimum of 350. Small samples tend to exaggerate effects "
            f"and results may be unreliable. Consider increasing your sample size or accepting "
            f"a larger MDE."
        )
    
    # Impractical test warning for very large samples
    if sample_size_per_variant > 1_000_000:
        warnings.append(
            f"⚠️ Impractical Test Warning: Sample size ({sample_size_per_variant:,} per variant) "
            f"is extremely large (>1M). This test may take an impractically long time to complete. "
            f"Consider testing a larger effect size (MDE) or accepting lower statistical power."
        )
    
    # Large effect warning
    if mde > 0.50:
        warnings.append(
            f"⚠️ Large Effect Warning: You're testing for a {mde*100:.0f}% improvement. "
            f"Effects this large are rare in CRO. Make sure this is a realistic expectation "
            f"for your test."
        )
    
    return {
        'sample_size_per_variant': sample_size_per_variant,
        'total_sample_size': total_sample_size,
        'baseline_cvr': baseline_cvr,
        'target_cvr': target_cvr,
        'mde_absolute': mde_absolute,
        'mde_relative': mde,
        'power': power,
        'alpha': alpha,
        'warnings': warnings
    }


def estimate_test_duration(
    required_sample_size: int,
    daily_traffic: int,
    conversion_rate: float
) -> dict:
    """
    Estimate test duration in days.
    
    Args:
        required_sample_size: Total sample size needed
        daily_traffic: Daily visitor count
        conversion_rate: Expected conversion rate
    
    Returns:
        dict with keys:
            - days_to_completion: float (rounded to 1 decimal)
            - weeks_to_completion: float (rounded to 1 decimal)
            - daily_traffic: int
            - daily_conversions_expected: int
            - warnings: list of str
    
    Raises:
        ValueError: If daily_traffic is zero or negative
    
    Example:
        >>> result = estimate_test_duration(
        ...     required_sample_size=10000,
        ...     daily_traffic=1000,
        ...     conversion_rate=0.03
        ... )
        >>> print(f"Test will take {result['days_to_completion']} days")
    """
    # Input validation
    if daily_traffic <= 0:
        raise ValueError(
            f"Daily traffic must be greater than 0. "
            f"You entered {daily_traffic}."
        )
    
    # Calculate days to completion
    days_to_completion = required_sample_size / daily_traffic
    days_to_completion = round(days_to_completion, 1)
    
    # Calculate weeks to completion
    weeks_to_completion = days_to_completion / 7
    weeks_to_completion = round(weeks_to_completion, 1)
    
    # Calculate expected daily conversions
    daily_conversions_expected = int(daily_traffic * conversion_rate)
    
    # Generate warnings
    warnings = []
    
    # Warning for tests exceeding 90 days
    if days_to_completion > 90:
        warnings.append(
            f"⚠️ Long Test Duration Warning: Test will take {days_to_completion} days "
            f"({weeks_to_completion} weeks) to complete. Tests longer than 90 days may be "
            f"impractical due to external factors (seasonality, market changes, product updates). "
            f"Consider increasing traffic, accepting a larger MDE, or reducing statistical power."
        )
    
    # Recommendation for minimum 7-day duration
    if days_to_completion < 7:
        warnings.append(
            f"⚠️ Short Test Duration Warning: Test will complete in {days_to_completion} days. "
            f"We recommend running tests for at least 7 days to account for weekly traffic patterns "
            f"(weekday vs weekend behavior). Consider reducing your sample size target or waiting "
            f"to accumulate a full week of data."
        )
    
    return {
        'days_to_completion': days_to_completion,
        'weeks_to_completion': weeks_to_completion,
        'daily_traffic': daily_traffic,
        'daily_conversions_expected': daily_conversions_expected,
        'warnings': warnings
    }


def calculate_mde(
    baseline_cvr: float,
    sample_size_per_variant: int,
    power: float = 0.80,
    alpha: float = 0.05
) -> dict:
    """
    Calculate minimum detectable effect (MDE) for given sample size.
    
    This is the inverse of the sample size calculation - given a sample size,
    determine what effect size can be reliably detected.
    
    Args:
        baseline_cvr: Current conversion rate (0.001 to 1.0)
        sample_size_per_variant: Sample size per variant
        power: Statistical power (0.50 to 0.99), default 0.80
        alpha: Significance level (0.01 to 0.20), default 0.05
    
    Returns:
        dict with keys:
            - mde_relative: float (relative % change as decimal)
            - mde_absolute: float (absolute percentage points)
            - target_cvr: float (baseline_cvr * (1 + mde_relative))
            - baseline_cvr: float
            - sample_size_per_variant: int
            - power: float
            - alpha: float
            - ecommerce_note: str or None (note if baseline is in typical e-commerce range)
    
    Raises:
        ValueError: If inputs are outside valid ranges
    
    Example:
        >>> result = calculate_mde(baseline_cvr=0.03, sample_size_per_variant=5000)
        >>> print(f"Can detect {result['mde_relative']*100:.1f}% relative change")
    """
    # Input validation
    errors = []
    
    if not (0.001 <= baseline_cvr <= 1.0):
        errors.append(
            f"Baseline CVR must be between 0.1% and 100%. "
            f"You entered {baseline_cvr:.4f}."
        )
    
    if sample_size_per_variant <= 0:
        errors.append(
            f"Sample size per variant must be greater than 0. "
            f"You entered {sample_size_per_variant}."
        )
    
    if not (0.50 <= power <= 0.99):
        errors.append(
            f"Statistical power must be between 50% and 99%. "
            f"You entered {power:.4f}."
        )
    
    if not (0.01 <= alpha <= 0.20):
        errors.append(
            f"Significance level (alpha) must be between 1% and 20%. "
            f"You entered {alpha:.4f}."
        )
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Get z-scores for alpha (two-tailed) and beta (power)
    z_alpha_2 = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Solve for MDE using the two-proportion z-test formula
    # n = (Z_α/2 + Z_β)² × [p₁(1-p₁) + p₂(1-p₂)] / (p₂ - p₁)²
    # Rearranged to solve for (p₂ - p₁):
    # (p₂ - p₁) = (Z_α/2 + Z_β) × √([p₁(1-p₁) + p₂(1-p₂)] / n)
    
    # Since p₂ depends on MDE, we need to solve iteratively
    p1 = baseline_cvr
    
    # Use Newton-Raphson method to solve for the absolute MDE
    # Start with an initial estimate assuming p₂ ≈ p₁ (small effect)
    se_initial = np.sqrt(2 * p1 * (1 - p1) / sample_size_per_variant)
    mde_absolute = (z_alpha_2 + z_beta) * se_initial
    
    # Refine with Newton-Raphson iterations
    for _ in range(10):  # Usually converges in 2-3 iterations
        p2 = p1 + mde_absolute
        
        # Clamp p2 to valid range [0, 1]
        p2 = np.clip(p2, 0, 1)
        
        # Calculate standard error with current p2
        se = np.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / sample_size_per_variant)
        
        # Calculate new MDE estimate
        mde_absolute_new = (z_alpha_2 + z_beta) * se
        
        # Check for convergence
        if abs(mde_absolute_new - mde_absolute) < 1e-10:
            break
        
        mde_absolute = mde_absolute_new
    
    # Ensure target CVR doesn't exceed 100%
    target_cvr = min(p1 + mde_absolute, 1.0)
    
    # Calculate relative MDE
    mde_relative = (target_cvr - p1) / p1 if p1 > 0 else 0
    
    # Generate e-commerce note if baseline is in typical range
    ecommerce_note = None
    if 0.02 <= baseline_cvr <= 0.05:
        ecommerce_note = (
            f"💡 E-commerce Note: Your baseline CVR of {baseline_cvr*100:.1f}% is typical for "
            f"e-commerce (typical range: 2-5%). This is a good baseline for planning tests."
        )
    
    return {
        'mde_relative': mde_relative,
        'mde_absolute': mde_absolute,
        'target_cvr': target_cvr,
        'baseline_cvr': baseline_cvr,
        'sample_size_per_variant': sample_size_per_variant,
        'power': power,
        'alpha': alpha,
        'ecommerce_note': ecommerce_note
    }


def calculate_power(
    baseline_cvr: float,
    effect_size: float,
    sample_size_per_variant: int,
    alpha: float = 0.05
) -> dict:
    """
    Calculate statistical power for given test parameters using two-proportion z-test.
    
    Power is the probability of detecting a true effect (1 - Type II error).
    
    Args:
        baseline_cvr: Current conversion rate (0.001 to 1.0)
        effect_size: Expected relative change (0.01 to 1.0)
        sample_size_per_variant: Sample size per variant
        alpha: Significance level (0.01 to 0.20), default 0.05
    
    Returns:
        dict with keys:
            - power: float (0 to 1, probability of detecting effect)
            - power_pct: float (0 to 100, power as percentage)
            - beta: float (Type II error rate = 1 - power)
            - alpha: float (Type I error rate, same as input)
            - baseline_cvr: float
            - effect_size: float
            - target_cvr: float (baseline_cvr * (1 + effect_size))
            - sample_size_per_variant: int
            - warnings: list of str
    
    Raises:
        ValueError: If inputs are outside valid ranges
    
    Example:
        >>> result = calculate_power(
        ...     baseline_cvr=0.03,
        ...     effect_size=0.10,
        ...     sample_size_per_variant=5000
        ... )
        >>> print(f"Power: {result['power_pct']:.1f}%")
    """
    # Input validation
    errors = []
    
    if not (0.001 <= baseline_cvr <= 1.0):
        errors.append(
            f"Baseline CVR must be between 0.1% and 100%. "
            f"You entered {baseline_cvr:.4f}."
        )
    
    if not (0.01 <= effect_size <= 1.0):
        errors.append(
            f"Effect size must be between 1% and 100% relative change. "
            f"You entered {effect_size:.4f}."
        )
    
    if sample_size_per_variant <= 0:
        errors.append(
            f"Sample size per variant must be greater than 0. "
            f"You entered {sample_size_per_variant}."
        )
    
    if not (0.01 <= alpha <= 0.20):
        errors.append(
            f"Significance level (alpha) must be between 1% and 20%. "
            f"You entered {alpha:.4f}."
        )
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Calculate target CVR
    target_cvr = baseline_cvr * (1 + effect_size)
    
    # Validate that target CVR doesn't exceed 100%
    if target_cvr > 1.0:
        raise ValueError(
            f"Target CVR ({target_cvr:.4f}) exceeds 100%. "
            f"With baseline CVR of {baseline_cvr:.2%} and effect size of {effect_size:.2%}, "
            f"the target would be {target_cvr:.2%}. "
            f"Please reduce the effect size or baseline CVR."
        )
    
    # Get z-score for alpha (two-tailed)
    z_alpha_2 = stats.norm.ppf(1 - alpha / 2)
    
    # Calculate standard error
    p1 = baseline_cvr
    p2 = target_cvr
    se = np.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / sample_size_per_variant)
    
    # Calculate test statistic (Z-score for the effect)
    # Z = (p2 - p1) / SE
    z_effect = (p2 - p1) / se if se > 0 else 0
    
    # Calculate power using the non-central normal distribution
    # Power = Φ(Z_effect - Z_α/2)
    # where Φ is the standard normal CDF
    power = stats.norm.cdf(z_effect - z_alpha_2)
    
    # Calculate Type II error (beta)
    beta = 1 - power
    
    # Convert power to percentage
    power_pct = power * 100
    
    # Generate warnings
    warnings = []
    
    # Warning for underpowered tests
    if power < 0.80:
        warnings.append(
            f"⚠️ Underpowered Test Warning: Statistical power is {power_pct:.1f}%, "
            f"which is below the recommended minimum of 80%. This means there's only a "
            f"{power_pct:.1f}% chance of detecting the effect if it truly exists. "
            f"Consider increasing sample size, accepting a larger effect size, or increasing alpha."
        )
    
    return {
        'power': power,
        'power_pct': power_pct,
        'beta': beta,
        'alpha': alpha,
        'baseline_cvr': baseline_cvr,
        'effect_size': effect_size,
        'target_cvr': target_cvr,
        'sample_size_per_variant': sample_size_per_variant,
        'warnings': warnings
    }


# ============================================================================
# Test Reliability Validator
# ============================================================================

def plan_multivariate_test(
    baseline_cvr: float,
    elements: list[dict],
    power: float = 0.80,
    alpha: float = 0.05,
    available_traffic: int = 0
) -> dict:
    """
    Plan multivariate test with multiple elements and variations.
    
    Applies Bonferroni correction for multiple comparisons:
    alpha_corrected = alpha / total_combinations
    
    Args:
        baseline_cvr: Current conversion rate (0.001 to 1.0)
        elements: List of dicts with keys 'name' and 'n_variations'
        power: Statistical power (0.50 to 0.99), default 0.80
        alpha: Significance level (0.01 to 0.20), default 0.05
        available_traffic: Optional daily traffic for traffic split warnings
    
    Returns:
        dict with keys:
            - total_combinations: int
            - sample_size_per_combination: int
            - total_sample_size: int
            - traffic_split_pct: float
            - bonferroni_alpha: float
            - warnings: list of str
            - recommendations: list of str
    
    Raises:
        ValueError: If inputs are outside valid ranges
    
    Example:
        >>> result = plan_multivariate_test(
        ...     baseline_cvr=0.03,
        ...     elements=[
        ...         {'name': 'headline', 'n_variations': 3},
        ...         {'name': 'button_color', 'n_variations': 2}
        ...     ]
        ... )
        >>> print(f"Total combinations: {result['total_combinations']}")
    """
    # Input validation
    errors = []
    
    if not (0.001 <= baseline_cvr <= 1.0):
        errors.append(
            f"Baseline CVR must be between 0.1% and 100%. "
            f"You entered {baseline_cvr:.4f}."
        )
    
    if not (0.50 <= power <= 0.99):
        errors.append(
            f"Statistical power must be between 50% and 99%. "
            f"You entered {power:.4f}."
        )
    
    if not (0.01 <= alpha <= 0.20):
        errors.append(
            f"Significance level (alpha) must be between 1% and 20%. "
            f"You entered {alpha:.4f}."
        )
    
    if not isinstance(elements, list):
        errors.append(
            f"Elements must be a list. You entered {type(elements).__name__}."
        )
    elif len(elements) == 0:
        errors.append(
            "Elements list cannot be empty. Please specify at least one element to test."
        )
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Validate each element
    for i, element in enumerate(elements):
        if not isinstance(element, dict):
            errors.append(
                f"Element {i} must be a dict with 'name' and 'n_variations' keys. "
                f"Got {type(element).__name__}."
            )
            continue
        
        if 'name' not in element:
            errors.append(
                f"Element {i} is missing required 'name' key."
            )
        
        if 'n_variations' not in element:
            errors.append(
                f"Element {i} is missing required 'n_variations' key."
            )
        elif not isinstance(element['n_variations'], int):
            errors.append(
                f"Element '{element.get('name', i)}' n_variations must be an integer. "
                f"Got {type(element['n_variations']).__name__}."
            )
        elif element['n_variations'] < 1:
            errors.append(
                f"Element '{element.get('name', i)}' n_variations must be at least 1. "
                f"You entered {element['n_variations']}."
            )
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Calculate total combinations (product of all n_variations)
    total_combinations = 1
    for element in elements:
        total_combinations *= element['n_variations']
    
    # Apply Bonferroni correction
    bonferroni_alpha = alpha / total_combinations
    
    # Calculate sample size per combination using corrected alpha
    # We use a default MDE of 0.10 (10%) since MVT requires detecting smaller effects
    # due to multiple comparisons
    
    # Ensure bonferroni_alpha doesn't go below minimum valid range (0.01)
    # If it does, use the minimum valid alpha
    effective_alpha = max(bonferroni_alpha, 0.01)
    
    sample_size_result = calculate_sample_size(
        baseline_cvr=baseline_cvr,
        mde=0.10,  # Default MDE for MVT
        power=power,
        alpha=effective_alpha,
        n_variants=total_combinations
    )
    
    sample_size_per_combination = sample_size_result['sample_size_per_variant']
    total_sample_size = sample_size_result['total_sample_size']
    
    # Calculate traffic split percentage
    traffic_split_pct = 100 / total_combinations if total_combinations > 0 else 0
    
    # Generate warnings
    warnings = []
    
    # Warning for too many combinations (>8)
    if total_combinations > 8:
        warnings.append(
            f"⚠️ Too Many Combinations Warning: This test has {total_combinations} combinations, "
            f"which exceeds the recommended maximum of 8. Multivariate tests with too many "
            f"combinations require excessive traffic and may take a very long time to complete. "
            f"Consider reducing the number of elements or variations per element."
        )
    
    # Warning for insufficient traffic
    if available_traffic > 0:
        # Estimate days needed with available traffic
        # Assume we need at least 350 conversions per combination for reliable results
        min_conversions_per_combination = 350
        required_daily_traffic = (min_conversions_per_combination / traffic_split_pct) * 100
        
        if available_traffic < required_daily_traffic:
            traffic_ratio = required_daily_traffic / available_traffic
            warnings.append(
                f"⚠️ Insufficient Traffic Warning: Your daily traffic ({available_traffic:,}) "
                f"is insufficient for this test. You need at least {required_daily_traffic:,.0f} "
                f"daily visitors to achieve reliable results. "
                f"This test requires {traffic_ratio:.1f}x more traffic than you currently have."
            )
    
    # Generate recommendations
    recommendations = []
    
    # Recommendation to reduce variations if too many combinations
    if total_combinations > 8:
        recommendations.append(
            f"Reduce total combinations from {total_combinations} to 8 or fewer by:"
        )
        recommendations.append(
            f"- Testing fewer elements (remove elements with smaller impact)"
        )
        recommendations.append(
            f"- Reducing variations per element (use 2 variations instead of 3+)"
        )
        recommendations.append(
            f"- Using sequential testing (run multiple A/B tests instead of one MVT)"
        )
    
    # Recommendation for traffic
    if available_traffic > 0 and available_traffic < required_daily_traffic:
        recommendations.append(
            f"Consider running this test on a higher-traffic page or campaign."
        )
        recommendations.append(
            f"Alternatively, reduce the number of combinations to match your traffic capacity."
        )
    
    return {
        'total_combinations': total_combinations,
        'sample_size_per_combination': sample_size_per_combination,
        'total_sample_size': total_sample_size,
        'traffic_split_pct': traffic_split_pct,
        'bonferroni_alpha': bonferroni_alpha,
        'effective_alpha': effective_alpha,  # Alpha actually used (may be clamped to minimum)
        'warnings': warnings,
        'recommendations': recommendations,
        # Include element details for reference
        'elements': elements,
        'combinations_breakdown': [f"{e['name']}: {e['n_variations']} variations" for e in elements]
    }


def validate_test_reliability(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    test_duration_days: int,
    observed_lift: float,
) -> dict:
    """
    Validate A/B test reliability against statistical best practices.
    
    Performs five reliability checks:
    1. Minimum sample size (>= 350 conversions per variant)
    2. Minimum duration (>= 7 days)
    3. Business cycles (>= 2 weekday/weekend cycles)
    4. Twyman's Law (if lift > 50%, sample size >= 1000)
    5. Statistical significance using existing ab_test_significance function
    
    Calculates reliability score (0-100) based on weighted checks:
    - Sample size: 30%
    - Duration: 25%
    - Business cycles: 20%
    - Twyman's Law: 15%
    - Significance: 10%
    
    Args:
        control_visitors: Number of visitors in control group
        control_conversions: Number of conversions in control group
        variant_visitors: Number of visitors in variant group
        variant_conversions: Number of conversions in variant group
        test_duration_days: Duration of test in days
        observed_lift: Observed lift percentage (variant - control)
    
    Returns:
        dict with keys:
            - is_reliable: bool (overall reliability assessment)
            - reliability_score: int (0-100)
            - checks: dict of check results (passed/failed)
            - warnings: list of warning messages
            - recommendations: list of actionable recommendations
    
    Example:
        >>> result = validate_test_reliability(
        ...     control_visitors=10000,
        ...     control_conversions=350,
        ...     variant_visitors=10000,
        ...     variant_conversions=420,
        ...     test_duration_days=14,
        ...     observed_lift=20.0
        ... )
        >>> print(f"Reliability: {result['is_reliable']}, Score: {result['reliability_score']}")
    """
    # Calculate sample sizes per variant
    control_sample_size = control_conversions
    variant_sample_size = variant_conversions
    min_sample_size = min(control_sample_size, variant_sample_size)
    
    # Initialize checks dictionary
    checks = {}
    
    # Initialize warnings and recommendations lists
    warnings = []
    recommendations = []
    
    # ============================================================================
    # Check 1: Minimum Sample Size (>= 350 per variant)
    # ============================================================================
    min_sample_size_threshold = 350
    sample_size_passed = min_sample_size >= min_sample_size_threshold
    checks['minimum_sample_size'] = sample_size_passed
    
    if not sample_size_passed:
        warnings.append(
            f"⚠️ Small Sample Size Warning: Minimum conversions per variant is {min_sample_size}, "
            f"which is below the recommended minimum of {min_sample_size_threshold}. "
            f"Small samples exaggerate effects and results may be unreliable."
        )
        recommendations.append(
            f"Increase sample size to achieve at least {min_sample_size_threshold} conversions per variant. "
            f"Current total sample size is {control_sample_size + variant_sample_size}."
        )
    
    # ============================================================================
    # Check 2: Minimum Duration (>= 7 days)
    # ============================================================================
    min_duration_threshold = 7
    duration_passed = test_duration_days >= min_duration_threshold
    checks['minimum_duration'] = duration_passed
    
    if not duration_passed:
        warnings.append(
            f"⚠️ Short Test Duration Warning: Test ran for only {test_duration_days} days, "
            f"which is below the recommended minimum of {min_duration_threshold} days. "
            f"Short tests may not capture weekly patterns and seasonal variations."
        )
        recommendations.append(
            f"Extend test duration to at least {min_duration_threshold} days to account for weekly patterns. "
            f"Current duration is {test_duration_days} days."
        )
    
    # ============================================================================
    # Check 3: Business Cycles (>= 2 weekday/weekend cycles)
    # ============================================================================
    # A business cycle is typically 7 days (1 week)
    # We need at least 2 full cycles (14 days) to capture weekday/weekend patterns
    min_business_cycles = 2
    business_cycles_passed = test_duration_days >= (min_business_cycles * 7)
    checks['business_cycles'] = business_cycles_passed
    
    if not business_cycles_passed:
        warnings.append(
            f"⚠️ Insufficient Business Cycles Warning: Test duration of {test_duration_days} days "
            f"provides fewer than {min_business_cycles} full business cycles. "
            f"Results may be skewed by weekday/weekend effects."
        )
        recommendations.append(
            f"Extend test duration to at least {min_business_cycles * 7} days to capture at least "
            f"{min_business_cycles} full business cycles. This ensures coverage of both weekday and weekend patterns."
        )
    
    # ============================================================================
    # Check 4: Twyman's Law (if lift > 50%, sample size >= 1000)
    # ============================================================================
    twyman_lift_threshold = 50.0
    twyman_sample_size_threshold = 1000
    twyman_passed = True  # Default pass
    
    if observed_lift > twyman_lift_threshold:
        # Twyman's Law applies - check if sample size is adequate
        twyman_passed = min_sample_size >= twyman_sample_size_threshold
        if not twyman_passed:
            warnings.append(
                f"⚠️ Twyman's Law Violation Warning: Observed lift of {observed_lift:.1f}% exceeds 50%, "
                f"but minimum sample size ({min_sample_size}) is below {twyman_sample_size_threshold}. "
                f"Extreme results from small samples are likely unreliable."
            )
            recommendations.append(
                f"With such a large observed lift ({observed_lift:.1f}%), increase sample size to at least "
                f"{twyman_sample_size_threshold} per variant to confirm the result is reliable. "
                f"Current minimum sample size is {min_sample_size}."
            )
    
    checks['twymans_law'] = twyman_passed
    
    # ============================================================================
    # Check 5: Statistical Significance
    # ============================================================================
    # Use existing ab_test_significance function
    significance_result = ab_test_significance(
        control_visitors=control_visitors,
        control_conversions=control_conversions,
        variant_visitors=variant_visitors,
        variant_conversions=variant_conversions,
        confidence_level=0.95,
    )
    significance_passed = significance_result['is_significant']
    checks['statistical_significance'] = significance_passed
    
    if not significance_passed:
        warnings.append(
            f"⚠️ Not Statistically Significant: Test p-value is {significance_result['p_value']:.4f}, "
            f"which is above the 0.05 significance threshold. "
            f"The observed lift of {observed_lift:.2f}% may be due to random chance."
        )
        recommendations.append(
            f"Continue running the test to gather more data, or accept that the current result is not statistically significant. "
            f"The p-value of {significance_result['p_value']:.4f} indicates insufficient evidence to reject the null hypothesis."
        )
    
    # ============================================================================
    # Calculate Reliability Score (0-100)
    # ============================================================================
    # Weighted scoring:
    # - Sample size: 30%
    # - Duration: 25%
    # - Business cycles: 20%
    # - Twyman's Law: 15%
    # - Significance: 10%
    
    score = 0
    score += 30 if sample_size_passed else 0      # Sample size: 30%
    score += 25 if duration_passed else 0         # Duration: 25%
    score += 20 if business_cycles_passed else 0  # Business cycles: 20%
    score += 15 if twyman_passed else 0           # Twyman's Law: 15%
    score += 10 if significance_passed else 0     # Significance: 10%
    
    reliability_score = score
    
    # ============================================================================
    # Determine Overall Reliability
    # ============================================================================
    # Test is reliable only if all checks pass
    is_reliable = all(bool(v) for v in checks.values())
    
    # Add general recommendations if test is not reliable
    if not is_reliable:
        failed_checks = [check for check, passed in checks.items() if not passed]
        recommendations.append(
            f"Address the following failed checks to improve reliability: {', '.join(failed_checks)}."
        )
    
    return {
        'is_reliable': is_reliable,
        'reliability_score': reliability_score,
        'checks': checks,
        'warnings': warnings,
        'recommendations': recommendations,
        # Include significance details for reference
        'significance_result': significance_result,
    }


# ============================================================================
# Existing Conversion Analytics Functions
# ============================================================================

FUNNEL_ORDER = ["Visit", "Product View", "Add to Cart", "Checkout", "Purchase"]


def funnel_summary(funnel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute conversion funnel summary with counts, conversion rate, and drop-off at each step.
    """
    totals = funnel_df.groupby("funnel_step")["session_id"].nunique().reindex(FUNNEL_ORDER).fillna(0).astype(int)
    
    df = pd.DataFrame({
        "step": FUNNEL_ORDER,
        "sessions": totals.values,
    })
    df["conversion_rate"] = (df["sessions"] / df["sessions"].iloc[0] * 100).round(2)
    df["drop_off"] = df["sessions"].diff().fillna(0).astype(int)
    df["drop_off_pct"] = 0.0
    for i in range(1, len(df)):
        if df.loc[i - 1, "sessions"] > 0:
            df.loc[i, "drop_off_pct"] = round(
                (1 - df.loc[i, "sessions"] / df.loc[i - 1, "sessions"]) * 100, 2
            )
    
    return df


def drop_off_analysis(funnel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify the biggest drop-off points in the funnel.
    Returns sorted by drop_off_pct descending.
    """
    summary = funnel_summary(funnel_df)
    return summary[summary["drop_off_pct"] > 0].sort_values("drop_off_pct", ascending=False).reset_index(drop=True)


def segment_conversion(funnel_df: pd.DataFrame, by: str = "device") -> pd.DataFrame:
    """
    Compute funnel conversion rate broken down by a dimension (device, source).
    Returns purchase conversion rate for each segment.
    """
    total_sessions = funnel_df.groupby(by)["session_id"].nunique().reset_index()
    total_sessions.columns = [by, "total_sessions"]
    
    purchases = funnel_df[funnel_df["funnel_step"] == "Purchase"].groupby(by)["session_id"].nunique().reset_index()
    purchases.columns = [by, "purchases"]
    
    merged = total_sessions.merge(purchases, on=by, how="left").fillna(0)
    merged["purchases"] = merged["purchases"].astype(int)
    merged["conversion_rate"] = (merged["purchases"] / merged["total_sessions"] * 100).round(2)
    
    return merged.sort_values("conversion_rate", ascending=False).reset_index(drop=True)


def ab_test_significance(
    control_visitors: int,
    control_conversions: int,
    variant_visitors: int,
    variant_conversions: int,
    confidence_level: float = 0.95,
) -> dict:
    """
    Perform a two-proportion Z-test for A/B test significance.
    
    Returns dict with:
        - control_rate, variant_rate
        - lift (% improvement)
        - z_score, p_value
        - is_significant
        - confidence_interval for the lift
    """
    p1 = control_conversions / control_visitors
    p2 = variant_conversions / variant_visitors
    
    lift = (p2 - p1) / p1 * 100 if p1 > 0 else 0
    
    # Pooled proportion
    p_pool = (control_conversions + variant_conversions) / (control_visitors + variant_visitors)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / control_visitors + 1 / variant_visitors))
    
    z_score = (p2 - p1) / se if se > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    alpha = 1 - confidence_level
    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_lower = (p2 - p1) - z_crit * se
    ci_upper = (p2 - p1) + z_crit * se
    
    return {
        "control_rate": round(p1 * 100, 3),
        "variant_rate": round(p2 * 100, 3),
        "lift_pct": round(lift, 2),
        "z_score": round(z_score, 4),
        "p_value": round(p_value, 6),
        "is_significant": p_value < alpha,
        "confidence_interval": (round(ci_lower * 100, 3), round(ci_upper * 100, 3)),
        "confidence_level": confidence_level,
    }

def calculate_cro_metrics(
    funnel_df: pd.DataFrame,
    date_range: tuple[str, str] = None
) -> dict:
    """
    Calculate comprehensive CRO metrics from funnel data.
    
    Args:
        funnel_df: DataFrame with columns including session_id, funnel_step,
                   and optionally: page_element, click_event, scroll_depth,
                   time_on_page, device, traffic_source
        date_range: Optional tuple of (start_date, end_date) for filtering
    
    Returns:
        dict with keys:
            - bounce_rate: float (percentage of single-page sessions)
            - above_fold_engagement: float (percentage scrolled past fold)
            - below_fold_engagement: float (percentage scrolled below fold)
            - primary_conversion_rate: float (percentage reached primary goal)
            - secondary_conversion_rates: dict of secondary goal rates
            - ctr_by_element: dict of click-through rates by element
            - avg_time_on_page: float (average time in seconds)
    
    Raises:
        ValueError: If funnel_df is empty or missing required columns
    
    Example:
        >>> result = calculate_cro_metrics(funnel_df)
        >>> print(f"Bounce rate: {result['bounce_rate']:.2f}%")
    """
    # Input validation
    if funnel_df.empty:
        raise ValueError("funnel_df cannot be empty")
    
    required_columns = ['session_id', 'funnel_step']
    missing_columns = [col for col in required_columns if col not in funnel_df.columns]
    if missing_columns:
        raise ValueError(
            f"funnel_df missing required columns: {missing_columns}. "
            f"Required columns: {required_columns}"
        )
    
    # Filter by date range if provided
    if date_range is not None:
        if len(date_range) != 2:
            raise ValueError(
                f"date_range must be a tuple of (start_date, end_date). "
                f"Got {len(date_range)} elements."
            )
        
        # Check if date columns exist
        date_columns = [col for col in ['date', 'timestamp', 'event_date'] 
                       if col in funnel_df.columns]
        
        if date_columns:
            date_col = date_columns[0]
            start_date, end_date = date_range
            
            # Convert to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(funnel_df[date_col]):
                funnel_df = funnel_df.copy()
                funnel_df[date_col] = pd.to_datetime(funnel_df[date_col])
            
            funnel_df = funnel_df[
                (funnel_df[date_col] >= start_date) & 
                (funnel_df[date_col] <= end_date)
            ]
    
    # Get total unique sessions
    total_sessions = funnel_df['session_id'].nunique()
    
    if total_sessions == 0:
        raise ValueError("No sessions found in funnel data")
    
    # ============================================================================
    # Calculate Bounce Rate
    # ============================================================================
    # Bounce rate = sessions with only one pageview / total sessions
    session_pageviews = funnel_df.groupby('session_id')['funnel_step'].nunique()
    single_page_sessions = (session_pageviews == 1).sum()
    bounce_rate = (single_page_sessions / total_sessions) * 100
    
    # ============================================================================
    # Calculate Engagement Rates
    # ============================================================================
    # Check for scroll depth or engagement columns
    above_fold_sessions = 0
    below_fold_sessions = 0
    
    if 'scroll_depth' in funnel_df.columns:
        # Sessions that scrolled past fold (e.g., > 50% scroll depth)
        above_fold_sessions = (funnel_df['scroll_depth'] > 50).groupby(
            funnel_df['session_id']
        ).any().sum()
        
        # Sessions that scrolled below fold (e.g., > 80% scroll depth)
        below_fold_sessions = (funnel_df['scroll_depth'] > 80).groupby(
            funnel_df['session_id']
        ).any().sum()
    elif 'engagement_score' in funnel_df.columns:
        # Use engagement score if available
        above_fold_sessions = (funnel_df['engagement_score'] >= 50).groupby(
            funnel_df['session_id']
        ).any().sum()
        
        below_fold_sessions = (funnel_df['engagement_score'] >= 80).groupby(
            funnel_df['session_id']
        ).any().sum()
    else:
        # Estimate engagement from funnel steps
        # Sessions that reached at least "Product View" are considered engaged
        engaged_sessions = funnel_df[funnel_df['funnel_step'].isin(
            ['Product View', 'Add to Cart', 'Checkout', 'Purchase']
        )]['session_id'].nunique()
        
        # Assume half of engaged sessions scrolled past fold, half scrolled below
        above_fold_sessions = engaged_sessions
        below_fold_sessions = engaged_sessions // 2
    
    above_fold_engagement = (above_fold_sessions / total_sessions) * 100
    below_fold_engagement = (below_fold_sessions / total_sessions) * 100
    
    # ============================================================================
    # Calculate Primary Conversion Rate
    # ============================================================================
    # Primary conversion = sessions that reached primary goal / total sessions
    # Default primary goal is "Purchase"
    primary_goal = 'Purchase'
    if primary_goal in funnel_df['funnel_step'].values:
        primary_conversion_sessions = funnel_df[
            funnel_df['funnel_step'] == primary_goal
        ]['session_id'].nunique()
    else:
        # If no Purchase step, use the last step in FUNNEL_ORDER
        primary_conversion_sessions = funnel_df[
            funnel_df['funnel_step'] == funnel_df['funnel_step'].max()
        ]['session_id'].nunique()
    
    primary_conversion_rate = (primary_conversion_sessions / total_sessions) * 100
    
    # ============================================================================
    # Calculate Secondary Conversion Rates (up to 5 goals)
    # ============================================================================
    # Secondary goals are all steps except the primary goal
    secondary_goals = funnel_df['funnel_step'].unique().tolist()
    if primary_goal in secondary_goals:
        secondary_goals.remove(primary_goal)
    
    # Limit to top 5 secondary goals by session count
    secondary_conversion_rates = {}
    for goal in secondary_goals[:5]:
        goal_sessions = funnel_df[
            funnel_df['funnel_step'] == goal
        ]['session_id'].nunique()
        secondary_conversion_rates[goal] = (goal_sessions / total_sessions) * 100
    
    # ============================================================================
    # Calculate CTR by Page Element
    # ============================================================================
    ctr_by_element = {}
    
    if 'page_element' in funnel_df.columns and 'click_event' in funnel_df.columns:
        # Calculate clicks and impressions per element
        element_stats = funnel_df.groupby('page_element').agg({
            'click_event': 'sum',  # clicks
            'session_id': 'nunique'  # impressions (sessions that saw the element)
        }).reset_index()
        
        for _, row in element_stats.iterrows():
            element = row['page_element']
            clicks = row['click_event']
            impressions = row['session_id']
            
            if impressions > 0:
                ctr_by_element[element] = (clicks / impressions) * 100
    elif 'page_element' in funnel_df.columns:
        # If only page_element exists, estimate CTR from click counts
        element_clicks = funnel_df.groupby('page_element').size()
        for element, clicks in element_clicks.items():
            # Assume each session sees the element once
            impressions = funnel_df[
                funnel_df['page_element'] == element
            ]['session_id'].nunique()
            
            if impressions > 0:
                ctr_by_element[element] = (clicks / impressions) * 100
    
    # ============================================================================
    # Calculate Average Time on Page
    # ============================================================================
    avg_time_on_page = 0.0
    
    if 'time_on_page' in funnel_df.columns:
        # Filter out zero or negative times
        valid_times = funnel_df[funnel_df['time_on_page'] > 0]['time_on_page']
        
        if len(valid_times) > 0:
            avg_time_on_page = valid_times.mean()
    
    return {
        'bounce_rate': round(bounce_rate, 2),
        'above_fold_engagement': round(above_fold_engagement, 2),
        'below_fold_engagement': round(below_fold_engagement, 2),
        'primary_conversion_rate': round(primary_conversion_rate, 2),
        'secondary_conversion_rates': {
            k: round(v, 2) for k, v in secondary_conversion_rates.items()
        },
        'ctr_by_element': {k: round(v, 2) for k, v in ctr_by_element.items()},
        'avg_time_on_page': round(avg_time_on_page, 2)
    }

def analyze_segment_performance(
    funnel_df: pd.DataFrame,
    segment_by: str
) -> dict:
    """
    Analyze conversion performance by segments with recommendations.
    
    Args:
        funnel_df: Funnel events DataFrame with columns:
                   session_id, device, source, region, visitor_type, funnel_step
        segment_by: Dimension to segment by ('device', 'source', 'region', 'visitor_type')
    
    Returns:
        dict with keys:
            - segments: pd.DataFrame with conversion rates sorted descending
            - overall_cvr: float (overall conversion rate)
            - underperforming_segments: list of dicts with segment info
            - recommendations: list of str with optimization recommendations
    
    Raises:
        ValueError: If segment_by is not a valid dimension or funnel_df is invalid
    
    Example:
        >>> result = analyze_segment_performance(funnel_df, 'device')
        >>> print(f"Overall CVR: {result['overall_cvr']:.2f}%")
        >>> for seg in result['underperforming_segments']:
        ...     print(f"Underperforming: {seg['segment']} ({seg['cvr']:.2f}%)")
    """
    # Input validation
    if funnel_df.empty:
        raise ValueError("funnel_df cannot be empty")
    
    required_columns = ['session_id', 'funnel_step', segment_by]
    missing_columns = [col for col in required_columns if col not in funnel_df.columns]
    if missing_columns:
        raise ValueError(
            f"funnel_df missing required columns for segment_by='{segment_by}': "
            f"{missing_columns}. Required columns: {required_columns}"
        )
    
    valid_segments = ['device', 'source', 'region', 'visitor_type']
    if segment_by not in valid_segments:
        raise ValueError(
            f"segment_by must be one of {valid_segments}. Got '{segment_by}'"
        )
    
    # Calculate overall conversion rate
    total_sessions = funnel_df['session_id'].nunique()
    total_purchases = funnel_df[funnel_df['funnel_step'] == 'Purchase']['session_id'].nunique()
    overall_cvr = (total_purchases / total_sessions * 100) if total_sessions > 0 else 0.0
    
    # Calculate conversion rate per segment
    total_by_segment = funnel_df.groupby(segment_by)['session_id'].nunique().reset_index()
    total_by_segment.columns = [segment_by, 'total_sessions']
    
    purchases_by_segment = funnel_df[funnel_df['funnel_step'] == 'Purchase'].groupby(segment_by)['session_id'].nunique().reset_index()
    purchases_by_segment.columns = [segment_by, 'purchases']
    
    merged = total_by_segment.merge(purchases_by_segment, on=segment_by, how='left').fillna(0)
    merged['purchases'] = merged['purchases'].astype(int)
    merged['conversion_rate'] = (merged['purchases'] / merged['total_sessions'] * 100).round(2)
    
    # Sort by conversion rate descending
    segments = merged.sort_values('conversion_rate', ascending=False).reset_index(drop=True)
    
    # Identify underperforming segments
    underperforming_segments = []
    
    # Thresholds: 20% below average for most segments, 30% for traffic sources
    threshold_multiplier = 0.70 if segment_by == 'source' else 0.80
    underperforming_threshold = overall_cvr * threshold_multiplier / 100  # Convert to decimal for comparison
    
    for _, row in segments.iterrows():
        segment_cvr = row['conversion_rate'] / 100  # Convert to decimal
        if segment_cvr < underperforming_threshold:
            underperforming_segments.append({
                'segment': row[segment_by],
                'cvr': row['conversion_rate'],
                'total_sessions': int(row['total_sessions']),
                'purchases': int(row['purchases']),
                'deficit_pct': round((overall_cvr - row['conversion_rate']) / overall_cvr * 100, 1)
            })
    
    # Generate recommendations based on segment type
    recommendations = []
    
    if segment_by == 'device':
        recommendations = _generate_device_recommendations(segments, overall_cvr)
    elif segment_by == 'source':
        recommendations = _generate_source_recommendations(segments, overall_cvr)
    elif segment_by == 'region':
        recommendations = _generate_region_recommendations(segments, overall_cvr)
    elif segment_by == 'visitor_type':
        recommendations = _generate_visitor_type_recommendations(segments, overall_cvr)
    
    return {
        'segments': segments,
        'overall_cvr': round(overall_cvr, 2),
        'underperforming_segments': underperforming_segments,
        'recommendations': recommendations
    }


def _generate_device_recommendations(segments: pd.DataFrame, overall_cvr: float) -> list:
    """Generate device-specific optimization recommendations."""
    recommendations = []
    
    # Get conversion rates for each device
    device_cvr = dict(zip(segments['device'], segments['conversion_rate']))
    
    mobile_cvr = device_cvr.get('mobile', 0)
    desktop_cvr = device_cvr.get('desktop', 0)
    tablet_cvr = device_cvr.get('tablet', 0)
    
    # Mobile recommendations (30%+ below desktop triggers mobile optimization)
    if desktop_cvr > 0 and mobile_cvr < desktop_cvr * 0.70:
        recommendations.append(
            "MOBILE OPTIMIZATION PRIORITY: Mobile conversion rate is significantly below desktop. "
            "Recommendations: 1) Optimize page load speed (target <2s), 2) Simplify forms for mobile, "
            "3) Increase touch target sizes to minimum 44x44px, 4) Test sticky CTA buttons, "
            "5) Implement mobile-specific checkout flow."
        )
    elif mobile_cvr > 0:
        recommendations.append(
            "MOBILE: Mobile conversion rate is acceptable but could be improved. "
            "Recommendations: 1) Monitor page load times, 2) Test simplified checkout, "
            "3) Ensure all CTAs are easily tappable with 44x44px minimum size."
        )
    
    # Tablet recommendations (if tablet traffic > 10%)
    total_sessions = segments['total_sessions'].sum()
    tablet_sessions = segments[segments['device'] == 'tablet']['total_sessions'].sum()
    tablet_ratio = tablet_sessions / total_sessions if total_sessions > 0 else 0
    
    if tablet_ratio > 0.10:
        recommendations.append(
            "TABLET OPTIMIZATION: Tablet traffic exceeds 10%. "
            "Recommendations: 1) Test hybrid mobile/desktop layouts, "
            "2) Optimize for both portrait and landscape modes, "
            "3) Ensure touch targets work well with both touch and mouse input."
        )
    
    # Desktop recommendations
    if desktop_cvr > 0:
        recommendations.append(
            "DESKTOP: Desktop has highest conversion rate. "
            "Recommendations: 1) Ensure above-the-fold content is compelling, "
            "2) Add trust signals (reviews, security badges), "
            "3) Provide detailed product information and comparison features."
        )
    
    return recommendations


def _generate_source_recommendations(segments: pd.DataFrame, overall_cvr: float) -> list:
    """Generate traffic source-specific recommendations."""
    recommendations = []
    
    # Get conversion rates for each source
    source_cvr = dict(zip(segments['source'], segments['conversion_rate']))
    
    # Check each source against overall performance
    for source, cvr in source_cvr.items():
        deficit_pct = (overall_cvr - cvr) / overall_cvr * 100 if overall_cvr > 0 else 0
        
        if deficit_pct >= 30:
            if source == 'organic':
                recommendations.append(
                    f"ORGANIC TRAFFIC: Conversion rate is {deficit_pct:.1f}% below average. "
                    "Recommendations: 1) Review landing page relevance to search intent, "
                    "2) Optimize landing page for target keywords, "
                    "3) Test different headline and value proposition, "
                    "4) Ensure mobile responsiveness for mobile search traffic."
                )
            elif source == 'paid':
                recommendations.append(
                    f"PAID TRAFFIC: Conversion rate is {deficit_pct:.1f}% below average. "
                    "Recommendations: 1) Review ad-to-landing page message match, "
                    "2) Test different ad creatives and copy, "
                    "3) Refine audience targeting, "
                    "4) Add stronger call-to-action in ad copy."
                )
            elif source == 'referral':
                recommendations.append(
                    f"REFERRAL TRAFFIC: Conversion rate is {deficit_pct:.1f}% below average. "
                    "Recommendations: 1) Review referring site quality, "
                    "2) Ensure landing page matches referral context, "
                    "3) Add social proof relevant to referring site audience."
                )
            elif source == 'direct':
                recommendations.append(
                    f"DIRECT TRAFFIC: Conversion rate is {deficit_pct:.1f}% below average. "
                    "Recommendations: 1) Ensure brand messaging is clear, "
                    "2) Add trust signals (reviews, security badges), "
                    "3) Test different value propositions."
                )
            elif source == 'social':
                recommendations.append(
                    f"SOCIAL TRAFFIC: Conversion rate is {deficit_pct:.1f}% below average. "
                    "Recommendations: 1) Review content relevance to platform audience, "
                    "2) Test video content vs static images, "
                    "3) Add urgency/scarcity elements, "
                    "4) Ensure mobile-optimized landing pages."
                )
        else:
            if source == 'organic':
                recommendations.append(
                    "ORGANIC TRAFFIC: Performing well. Continue optimizing for high-intent keywords."
                )
            elif source == 'paid':
                recommendations.append(
                    "PAID TRAFFIC: Performing well. Consider increasing budget for top-performing campaigns."
                )
            elif source == 'referral':
                recommendations.append(
                    "REFERRAL TRAFFIC: Performing well. Explore additional partnership opportunities."
                )
            elif source == 'direct':
                recommendations.append(
                    "DIRECT TRAFFIC: Performing well. Maintain strong brand presence."
                )
            elif source == 'social':
                recommendations.append(
                    "SOCIAL TRAFFIC: Performing well. Continue testing new content formats."
                )
    
    return recommendations


def _generate_region_recommendations(segments: pd.DataFrame, overall_cvr: float) -> list:
    """Generate geographic region-specific recommendations."""
    recommendations = []
    
    # Get conversion rates for each region
    region_cvr = dict(zip(segments['region'], segments['conversion_rate']))
    
    # Find best and worst performing regions
    best_region = max(region_cvr.items(), key=lambda x: x[1]) if region_cvr else (None, 0)
    worst_region = min(region_cvr.items(), key=lambda x: x[1]) if region_cvr else (None, 0)
    
    if best_region[0] and worst_region[0]:
        deficit_pct = (best_region[1] - worst_region[1]) / best_region[1] * 100 if best_region[1] > 0 else 0
        
        if deficit_pct > 20:
            recommendations.append(
                f"REGIONAL DISPARITY: Conversion rate varies by {deficit_pct:.1f}% between best ({best_region[0]}) "
                f"and worst ({worst_region[0]}) performing regions. "
                "Recommendations: 1) Analyze regional marketing strategies, "
                "2) Consider local language/cultural adaptations, "
                "3) Test region-specific offers and promotions, "
                "4) Review regional payment method preferences."
            )
        else:
            recommendations.append(
                "REGIONAL PERFORMANCE: Regional conversion rates are relatively consistent. "
                "Recommendations: Continue monitoring regional performance and test localized content."
            )
    
    # General recommendations
    recommendations.append(
        "GEOGRAPHIC: Consider regional pricing strategies and localized content for better conversion."
    )
    
    return recommendations


def _generate_visitor_type_recommendations(segments: pd.DataFrame, overall_cvr: float) -> list:
    """Generate new vs returning visitor recommendations."""
    recommendations = []
    
    # Get conversion rates for each visitor type
    visitor_cvr = dict(zip(segments['visitor_type'], segments['conversion_rate']))
    
    new_visitor_cvr = visitor_cvr.get('new', 0)
    returning_visitor_cvr = visitor_cvr.get('returning', 0)
    
    # Compare new vs returning visitor performance
    if returning_visitor_cvr > 0 and new_visitor_cvr > 0:
        ratio = returning_visitor_cvr / new_visitor_cvr
        
        if ratio > 1.5:
            recommendations.append(
                f"VISITOR TYPE: Returning visitors convert {ratio:.1f}x more than new visitors. "
                "Recommendations: 1) Focus on retention strategies (email marketing, loyalty programs), "
                "2) Create personalized experiences for returning visitors, "
                "3) Implement abandoned cart recovery for returning users."
            )
        elif ratio > 1.2:
            recommendations.append(
                f"VISITOR TYPE: Returning visitors convert {ratio:.1f}x more than new visitors. "
                "Recommendations: 1) Continue building email list, "
                "2) Implement loyalty/rewards program, "
                "3) Create personalized recommendations for returning users."
            )
        else:
            recommendations.append(
                f"VISITOR TYPE: New and returning visitor conversion is balanced ({ratio:.1f}x). "
                "Recommendations: 1) Focus on converting new visitors, "
                "2) Implement onboarding flows, "
                "3) Create welcome incentives for first-time buyers."
            )
    
    # General recommendations
    if new_visitor_cvr > 0:
        recommendations.append(
            "NEW VISITORS: Focus on building trust and reducing friction. "
            "Recommendations: 1) Add trust signals (reviews, security badges), "
            "2) Simplify checkout process, 3) Offer first-time buyer discounts."
        )
    
    if returning_visitor_cvr > 0:
        recommendations.append(
            "RETURNING VISITORS: Focus on retention and lifetime value. "
            "Recommendations: 1) Implement email marketing automation, "
            "2) Create loyalty/rewards program, 3) Offer personalized recommendations."
        )
    
    return recommendations
