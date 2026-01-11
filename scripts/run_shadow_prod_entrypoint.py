#!/usr/bin/env python3
"""Repo-owned entrypoint for a single SHADOW runner cycle."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _prepend_env_path(env_name: str, path: str) -> None:
    existing = os.environ.get(env_name, "")
    parts = [p for p in existing.split(os.pathsep) if p]
    if path not in parts:
        os.environ[env_name] = os.pathsep.join([path] + parts)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    artifacts_dir = Path(
        os.environ.get("SHADOW_ARTIFACTS_DIR", "/opt/hybrid-trading-bot/artifacts/shadow")
    )
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    os.environ["SHADOW_ARTIFACTS_DIR"] = str(artifacts_dir)

    _prepend_env_path("PYTHONPATH", str(repo_root))
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    runner_path = os.environ.get("SHADOW_RUNNER_PATH", "/opt/scripts/run_shadow_enhanced.py")
    ticker = os.environ.get("SHADOW_RUN_TICKER", "KALSHI-TEST-DEEP")
    output_path = os.environ.get(
        "SHADOW_RUNNER_OUTPUT", str(artifacts_dir / "flight_recorder.csv")
    )

    if not Path(runner_path).exists():
        print(f"ERROR: runner not found at {runner_path}", file=sys.stderr)
        return 2

    cmd = [
        sys.executable,
        runner_path,
        "--once",
        "--ticker",
        ticker,
        "--output",
        output_path,
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
