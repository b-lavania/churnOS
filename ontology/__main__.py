"""CLI: python -m ontology.validate --examples"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ontology.validate import validate_record

EXAMPLES = Path(__file__).resolve().parent / "examples"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", action="store_true", help="Validate example records")
    args = parser.parse_args()
    if not args.examples:
        parser.print_help()
        return 0

    errors_found = False
    for path in EXAMPLES.glob("*.json"):
        record = json.loads(path.read_text())
        vertical = record.get("vertical", "capability_lifecycle")
        errors = validate_record(record, vertical)
        if errors:
            print(f"FAIL {path.name}: {errors}")
            errors_found = True
        else:
            print(f"OK {path.name}")
    return 1 if errors_found else 0


if __name__ == "__main__":
    sys.exit(main())
