"""Tests for evidence packing."""

import pytest

from analytics.evidence import pack_evidence, validate_evidence, is_rigorous_mode


def test_pack_evidence_valid():
    ev = pack_evidence(
        model_id="test",
        claim_type="simulated",
        estimand="churn_rate",
        posterior_mean=0.1,
        ci95=(0.05, 0.15),
        n=100,
    )
    assert not validate_evidence(ev)


def test_causal_requires_experiment():
    with pytest.raises(ValueError):
        pack_evidence(
            model_id="test",
            claim_type="causal",
            estimand="uplift",
            posterior_mean=0.1,
            ci95=(0.05, 0.15),
            n=100,
        )


def test_rigorous_mode():
    assert not is_rigorous_mode({"priors": {"math_mode": "heuristic"}})
    assert is_rigorous_mode({"priors": {"math_mode": "rigorous"}})
