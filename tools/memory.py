#!/usr/bin/env python3
"""
Helper for reading and appending entries to MEMORY.md

Usage:
  - Read: python tools/memory.py --read
  - Append: python tools/memory.py --mistake "Description" --pattern "Pattern to avoid" --better "Better approach"

This script is intentionally simple and safe.
"""
from __future__ import annotations
import argparse
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "MEMORY.md"


def read_memory(path: Path = FILE) -> str:
    if not path.exists():
        return "(no MEMORY.md found)"
    return path.read_text(encoding="utf-8")


def append_entry(mistake: str, pattern: str = "", better: str = "", path: Path = FILE) -> None:
    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    entry_lines = [
        "\n### Entry — " + ts,
        "",
        "**Mistake:** " + mistake,
        "",
        "**Patterns to avoid:**",
    ]
    if pattern:
        for p in pattern.split(";;"):
            entry_lines.append("- " + p.strip())
    else:
        entry_lines.append("- (none provided)")
    entry_lines.append("")
    entry_lines.append("**Better approaches:**")
    if better:
        for b in better.split(";;"):
            entry_lines.append("- " + b.strip())
    else:
        entry_lines.append("- (none provided)")
    entry_lines.append("")
    path.write_text(path.read_text(encoding="utf-8") + "\n" + "\n".join(entry_lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read or append to MEMORY.md")
    parser.add_argument("--read", action="store_true", help="Print MEMORY.md to stdout")
    parser.add_argument("--mistake", type=str, help="Short description of the mistake to append")
    parser.add_argument("--pattern", type=str, default="", help="Patterns to avoid (use ';;' to separate multiple)" )
    parser.add_argument("--better", type=str, default="", help="Better approaches (use ';;' to separate multiple)")
    args = parser.parse_args()

    if args.read:
        print(read_memory())
    elif args.mistake:
        append_entry(args.mistake, args.pattern, args.better)
        print("Appended entry to MEMORY.md")
    else:
        parser.print_help()
