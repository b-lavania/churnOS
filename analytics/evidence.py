"""
Pack and validate statistical evidence blocks for GDR exceptions.
"""

from __future__ import annotations

from typing import Any, Literal

ClaimType = Literal["associational", "causal", "simulated"]

VALID_CLAIM_TYPES = frozenset({"associational", "causal", "simulated"})


def pack_evidence(
    *,
    model_id: str,
    claim_type: ClaimType,
    estimand: str,
    posterior_mean: float,
    ci95: tuple[float, float] | list[float],
    n: int,
    experiment_id: str | None = None,
    calibration: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an evidence dict conforming to the GDR extension schema."""
    if claim_type not in VALID_CLAIM_TYPES:
        raise ValueError(f"Invalid claim_type: {claim_type}")
    if claim_type == "causal" and not experiment_id:
        raise ValueError("claim_type 'causal' requires experiment_id per honesty.md")

    lo, hi = float(ci95[0]), float(ci95[1])
    block: dict[str, Any] = {
        "model_id": model_id,
        "claim_type": claim_type,
        "estimand": estimand,
        "posterior": {"mean": round(posterior_mean, 6), "ci95": [round(lo, 6), round(hi, 6)]},
        "n": int(n),
        "experiment_id": experiment_id,
    }
    if calibration:
        block["calibration"] = calibration
    if extra:
        block.update(extra)
    return block


def validate_evidence(evidence: dict[str, Any]) -> list[str]:
    """Return validation errors; empty list if valid."""
    errors: list[str] = []
    if not evidence:
        return errors
    for key in ("model_id", "claim_type", "estimand", "posterior", "n"):
        if key not in evidence:
            errors.append(f"Missing evidence.{key}")
    ct = evidence.get("claim_type")
    if ct and ct not in VALID_CLAIM_TYPES:
        errors.append(f"Invalid claim_type: {ct}")
    if ct == "causal" and not evidence.get("experiment_id"):
        errors.append("causal claim requires experiment_id")
    post = evidence.get("posterior") or {}
    if "mean" not in post or "ci95" not in post:
        errors.append("posterior must include mean and ci95")
    return errors


def is_rigorous_mode(profile: dict[str, Any]) -> bool:
    return profile.get("priors", {}).get("math_mode", "heuristic") == "rigorous"


def churn_rate_evidence(
    successes: int,
    trials: int,
    *,
    claim_type: ClaimType = "simulated",
    experiment_id: str | None = None,
) -> dict[str, Any]:
    from analytics.inference.binomial import beta_binomial_posterior

    post = beta_binomial_posterior(successes, trials)
    return pack_evidence(
        model_id=post["model_id"],
        claim_type=claim_type,
        estimand="churn_rate",
        posterior_mean=post["mean"],
        ci95=post["ci95"],
        n=post["n"],
        experiment_id=experiment_id,
    )


def compute_evsi(
    evidence: dict[str, Any] | None,
    primary_metric_usd: float,
    human_review_cost_usd: float = 150.0,
) -> dict[str, Any]:
    """
    Expected Value of Sample Information for review gate.
    EVSI ≈ (ci_width × primary_metric_usd) − human_review_cost_usd
    """
    if not evidence:
        return {"evsi_usd": 0.0, "requires_review_evsi": False}
    post = evidence.get("posterior") or {}
    ci = post.get("ci95", [post.get("mean", 0), post.get("mean", 0)])
    width = abs(float(ci[1]) - float(ci[0]))
    evsi = width * primary_metric_usd - human_review_cost_usd
    return {
        "evsi_usd": round(evsi, 2),
        "ci_width": round(width, 4),
        "human_review_cost_usd": human_review_cost_usd,
        "requires_review_evsi": evsi > 0,
    }


def apply_evsi_review_gate(
    record: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Augment decision.requires_review when EVSI > 0."""
    priors = profile.get("priors", {})
    review_cost = float(priors.get("human_review_cost_usd", 150.0))
    econ = record.get("economics") or {}
    primary = float(econ.get("primary_metric_usd", 0))
    evidence = record.get("evidence")
    if not evidence:
        for exc in record.get("exceptions", []):
            if exc.get("evidence"):
                evidence = exc["evidence"]
                break
    evsi = compute_evsi(evidence, primary, review_cost)
    decision = dict(record.get("decision") or {})
    if evsi["requires_review_evsi"]:
        decision["requires_review"] = True
        decision["evsi_usd"] = evsi["evsi_usd"]
        rationale = decision.get("rationale", "")
        decision["rationale"] = (
            f"EVSI ${evsi['evsi_usd']:,.0f} > 0 — review warranted. {rationale}"
        )
    updated = dict(record)
    updated["decision"] = decision
    updated["evsi"] = evsi
    return updated
