"""Ontology schema validation tests."""

import json
from pathlib import Path

from ontology.validate import validate_record

EXAMPLES = Path(__file__).resolve().parents[2] / "ontology" / "examples"


def test_example_capability_harm_validates():
    record = json.loads((EXAMPLES / "capability_harm.minimal.json").read_text())
    errors = validate_record(record, "capability_lifecycle")
    assert errors == []


def test_example_account_tourist_validates():
    record = json.loads((EXAMPLES / "account_tourist.minimal.json").read_text())
    errors = validate_record(record, "capability_lifecycle")
    assert errors == []
