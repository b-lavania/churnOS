"""JSONL record store for GrowthDecisionRecords."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "records"


def append_record(record: dict[str, Any], store_dir: Path | None = None) -> Path:
    store_dir = store_dir or STORE_DIR
    store_dir.mkdir(parents=True, exist_ok=True)
    vertical = record.get("vertical", "unknown")
    path = store_dir / f"{vertical}.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return path


def read_records(vertical: str | None = None, store_dir: Path | None = None) -> list[dict[str, Any]]:
    store_dir = store_dir or STORE_DIR
    if not store_dir.exists():
        return []
    paths = list(store_dir.glob("*.jsonl"))
    if vertical:
        paths = [p for p in paths if p.stem == vertical]
    records = []
    for p in paths:
        for line in p.read_text().splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records
