"""Tests for always-valid confidence sequences."""

import numpy as np

from analytics.inference.confidence_sequences import cs_covers, cs_mean, cs_two_proportion


def test_cs_mean_nonempty():
    out = cs_mean([0.1, 0.2, 0.3, 0.4])
    assert out["n"] == 4
    assert out["lo"] <= out["mean"] <= out["hi"]


def test_cs_two_proportion_series():
    out = cs_two_proportion(30, 100, 40, 100)
    assert out["n_total"] == 200
    assert len(out["series"]) > 0
    assert out["lo"] <= out["delta"] <= out["hi"]


def test_cs_covers():
    assert cs_covers(0.5, 0.4, 0.6)
    assert not cs_covers(0.9, 0.4, 0.6)
