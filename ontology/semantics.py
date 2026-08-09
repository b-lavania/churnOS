"""Load semantics YAML for agents and Concepts."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from ontology.validate import ONTOLOGY_ROOT, VERTICALS


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, val in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def load_semantics(vertical: str, overlay: dict[str, Any] | None = None) -> dict[str, Any]:
    path = VERTICALS[vertical]["semantics"]
    with open(path) as f:
        base = yaml.safe_load(f)
    if overlay:
        return _deep_merge(base, overlay)
    return base


def load_all_semantics() -> dict[str, dict[str, Any]]:
    return {v: load_semantics(v) for v in VERTICALS}
