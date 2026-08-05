"""Load semantics YAML for agents and Concepts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ontology.validate import ONTOLOGY_ROOT, VERTICALS


def load_semantics(vertical: str) -> dict[str, Any]:
    path = VERTICALS[vertical]["semantics"]
    with open(path) as f:
        return yaml.safe_load(f)


def load_all_semantics() -> dict[str, dict[str, Any]]:
    return {v: load_semantics(v) for v in VERTICALS}
