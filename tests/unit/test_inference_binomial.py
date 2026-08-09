"""Unit tests for Beta–Binomial inference."""

import pytest

from analytics.inference.binomial import beta_binomial_posterior, wilson_ci


def test_beta_binomial_posterior_mean():
    post = beta_binomial_posterior(30, 100)
    assert 0.25 < post["mean"] < 0.35
    assert post["ci95"][0] <= post["mean"] <= post["ci95"][1]


def test_wilson_ci_contains_rate():
    lo, hi = wilson_ci(50, 100)
    assert lo <= 0.5 <= hi


def test_beta_binomial_invalid():
    with pytest.raises(ValueError):
        beta_binomial_posterior(10, 5)
