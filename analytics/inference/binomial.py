"""
Beta–Binomial and Wilson interval inference for rate estimation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats


def beta_binomial_posterior(
    successes: int,
    trials: int,
    *,
    alpha_prior: float = 1.0,
    beta_prior: float = 1.0,
    ci_level: float = 0.95,
) -> dict[str, Any]:
    """
    Conjugate Beta–Binomial posterior for Bernoulli rate.

    Returns mean, credible interval, and posterior parameters.
    """
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError("Invalid successes/trials for Beta–Binomial posterior.")

    a = alpha_prior + successes
    b = beta_prior + (trials - successes)
    mean = a / (a + b)
    tail = (1.0 - ci_level) / 2.0
    lo = float(stats.beta.ppf(tail, a, b))
    hi = float(stats.beta.ppf(1.0 - tail, a, b))

    return {
        "mean": round(mean, 6),
        "ci95": [round(lo, 6), round(hi, 6)],
        "alpha_post": a,
        "beta_post": b,
        "n": trials,
        "successes": successes,
        "model_id": "beta_binomial_v1",
    }


def wilson_ci(
    successes: int,
    trials: int,
    *,
    ci_level: float = 0.95,
) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if trials == 0:
        return 0.0, 1.0
    z = stats.norm.ppf(0.5 + ci_level / 2.0)
    p_hat = successes / trials
    denom = 1 + z**2 / trials
    centre = p_hat + z**2 / (2 * trials)
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * trials)) / trials)
    lo = (centre - margin) / denom
    hi = (centre + margin) / denom
    return float(max(0.0, lo)), float(min(1.0, hi))
