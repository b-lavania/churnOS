"""Batch OTEL mock ingest into methodology measurement tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data.otel_mock_generator import generate_otel_traces, load_otel_traces


def ingest_otel_into_agentic(
    agentic: dict[str, pd.DataFrame],
    profile: dict[str, Any],
    *,
    seed: int = 42,
    otel_path: str | Path | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Merge OTEL trace spans into agent_runs/spans tables.
    Generates mock traces when path missing; scrubs prompt bodies (metadata only).
    """
    path = Path(otel_path or "data/mock_traces.jsonl")
    if not path.exists():
        generate_otel_traces(profile, seed=seed, output_path=path)
    traces = load_otel_traces(path)
    if not traces:
        return agentic

    rng = np.random.default_rng(seed)
    seats = agentic["seats"]
    runs = agentic["runs"]
    if runs.empty:
        return agentic

    span_rows: list[dict[str, Any]] = []
    run_updates: dict[str, dict[str, Any]] = {}

    for trace in traces:
        trace_id = trace.get("trace_id", "")
        cap_id = trace.get("capability_id", "CAP-000")
        seat_id = seats["seat_id"].iloc[int(rng.integers(0, len(seats)))]
        existing = runs[runs["capability_id"] == cap_id]
        if len(existing):
            run_id = existing.iloc[int(rng.integers(0, len(existing)))]["run_id"]
        else:
            run_id = runs.iloc[int(rng.integers(0, len(runs)))]["run_id"]

        span_id = trace.get("span_id", f"SPN-{trace_id[:8]}")
        loop_i = int(trace.get("loop_iteration", 1))
        tokens = int(trace.get("tokens_used", 500))
        span_rows.append(
            {
                "span_id": span_id,
                "agent_run_id": run_id,
                "session_id": f"SES-OTEL-{trace_id[:8]}",
                "loop_iteration": loop_i,
                "tokens_in": tokens,
                "tokens_out": int(tokens * 0.25),
                "success": bool(trace.get("success", True)),
                "trace_id": trace_id,
                "data_source": "otel",
            }
        )
        run_updates[run_id] = {
            "loop_count": max(run_updates.get(run_id, {}).get("loop_count", 0), loop_i),
            "tokens_in": run_updates.get(run_id, {}).get("tokens_in", 0) + tokens,
        }

    otel_spans = pd.DataFrame(span_rows)
    agentic["spans"] = (
        pd.concat([agentic.get("spans", pd.DataFrame()), otel_spans], ignore_index=True)
        if len(agentic.get("spans", pd.DataFrame()))
        else otel_spans
    )

    for run_id, upd in run_updates.items():
        mask = runs["run_id"] == run_id
        if mask.any():
            runs.loc[mask, "loop_count"] = upd["loop_count"]
            if "tokens_in" in runs.columns:
                runs.loc[mask, "tokens_in"] = upd["tokens_in"]

    agentic["runs"] = runs
    if not agentic.get("agent_runs", pd.DataFrame()).empty:
        agentic["agent_runs"] = runs.copy()
        agentic["agent_runs"]["agent_run_id"] = runs["run_id"]
    return agentic
