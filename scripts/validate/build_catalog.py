#!/usr/bin/env python3
"""Catalog build wrapper that runs compliance validation and emits a report."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    validator = repo_root / "scripts" / "validate" / "validate_catalog.py"
    catalog = repo_root / "data" / "catalog" / "imported-games.json"
    report = repo_root / "data" / "reports" / "compliance-report.md"

    cmd = [sys.executable, str(validator), str(catalog), "--report-path", str(report)]
    proc = subprocess.run(cmd, cwd=repo_root)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
