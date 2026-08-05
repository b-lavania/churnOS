"""
Mock OTEL / LLM trace generator for ingestion pipeline development (P1).

Writes scrubbed metadata-only spans to JSONL — no prompt bodies.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import numpy as np

from analytics.agentic_profile import get_preset


def generate_otel_traces(
    profile: dict[str, Any] | None = None,
    *,
    num_traces: int = 50,
    seed: int = 42,
    output_path: str | Path = "data/mock_traces.jsonl",
) -> Path:
    """Generate multi-span traces with parent-child links and loop iterations."""
    if profile is None:
        profile = get_preset("assistant_heavy")
    priors = profile.get("priors", {})
    n_caps = int(priors.get("n_capabilities", 10))
    max_loops = int(profile.get("max_loops_threshold", 8))
    rng = np.random.default_rng(seed)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for _ in range(num_traces):
        trace_id = uuid.uuid4().hex
        cap_id = f"CAP-{int(rng.integers(0, n_caps)):03d}"
        success = rng.random() > 0.15
        loops = int(rng.geometric(0.7 if success else 0.15))
        loops = int(np.clip(loops, 1, max_loops + 4))

        parent_span: str | None = None
        for i in range(loops):
            span_id = uuid.uuid4().hex[:16]
            tokens = int(rng.integers(200, 2500))
            rows.append(
                {
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "parent_span_id": parent_span,
                    "capability_id": cap_id,
                    "loop_iteration": i + 1,
                    "tokens_used": tokens,
                    "success": bool(success if i == loops - 1 else True),
                    "scrubbed": True,
                    "model_id": profile.get("default_model", "gpt-4o"),
                }
            )
            parent_span = span_id

    with open(out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return out


def load_otel_traces(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
