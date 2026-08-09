"""Sequential probability ratio test for version monitoring."""

from __future__ import annotations

from typing import Any

from scipy.stats import norm


def sprt_two_proportion(
    s_control: int,
    n_control: int,
    s_variant: int,
    n_variant: int,
    *,
    p0: float = 0.75,
    p1: float = 0.65,
    alpha: float = 0.05,
    beta: float = 0.20,
) -> dict[str, Any]:
    """
    Wald SPRT for H0: p_variant >= p_control vs H1: p_variant < p_control - delta.

    Uses log-likelihood ratio on pooled counts; teaching implementation.
    """
    if n_control < 1 or n_variant < 1:
        return {
            "decision": "continue",
            "llr": 0.0,
            "boundary_lower": None,
            "boundary_upper": None,
            "n_total": n_control + n_variant,
        }

    p_c = s_control / n_control
    p_v = s_variant / n_variant
    # Log-likelihood ratio under simple alternative
    ll_h0 = s_variant * __import__("math").log(max(p0, 1e-9)) + (n_variant - s_variant) * __import__("math").log(max(1 - p0, 1e-9))
    ll_h1 = s_variant * __import__("math").log(max(p1, 1e-9)) + (n_variant - s_variant) * __import__("math").log(max(1 - p1, 1e-9))
    llr = ll_h1 - ll_h0

    upper = __import__("math").log((1 - beta) / alpha)
    lower = __import__("math").log(beta / (1 - alpha))

    decision = "continue"
    if llr >= upper:
        decision = "rollback"
    elif llr <= lower:
        decision = "ship"

    return {
        "decision": decision,
        "llr": round(llr, 4),
        "boundary_lower": round(lower, 4),
        "boundary_upper": round(upper, 4),
        "n_total": n_control + n_variant,
        "rate_control": round(p_c, 4),
        "rate_variant": round(p_v, 4),
        "delta_pp": round(p_v - p_c, 4),
    }
