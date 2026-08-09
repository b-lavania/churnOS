"""Tests for agentic experimentation extensions."""

from analytics.experimentation import agentic_sample_size, benjamini_hochberg, cuped_adjust
import numpy as np


def test_agentic_sample_size_web_vs_agent():
    web = agentic_sample_size(0.02, 0.001, unit="visitor")
    agent = agentic_sample_size(0.75, 0.05, unit="run")
    assert web["sample_size_per_arm_naive"] > agent["sample_size_per_arm_naive"]


def test_clustering_increases_n():
    naive = agentic_sample_size(0.75, 0.05, unit="account", icc=0.0)
    clustered = agentic_sample_size(0.75, 0.05, unit="account", icc=0.2, runs_per_unit=50)
    assert clustered["sample_size_per_arm_clustered"] >= naive["sample_size_per_arm_naive"]


def test_benjamini_hochberg():
    sig = benjamini_hochberg([0.001, 0.04, 0.5, 0.8])
    assert sig[0] is True
    assert sig[2] is False


def test_cuped_reduces_variance_sometimes():
    rng = np.random.default_rng(0)
    n = 200
    x = rng.normal(0, 1, n)
    y_c = 0.5 * x + rng.normal(0, 0.5, n)
    y_v = 0.5 * x + rng.normal(0.2, 0.5, n)
    out = cuped_adjust(y_c[:100], y_v[100:], x[:100], x[100:])
    assert out["adjusted_lift"] is not None
