#!/usr/bin/env python3
"""Repo-owned entrypoint for a SHADOW runner cycle (config-driven)."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path


def _prepend_env_path(env_name: str, path: str) -> None:
    existing = os.environ.get(env_name, "")
    parts = [p for p in existing.split(os.pathsep) if p]
    if path not in parts:
        os.environ[env_name] = os.pathsep.join([path] + parts)


def _get_env_value(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _truthy_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    artifacts_dir = Path(
        os.environ.get(
            "SHADOW_ARTIFACTS_DIR", str(repo_root / "artifacts" / "shadow")
        )
    )
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    os.environ["SHADOW_ARTIFACTS_DIR"] = str(artifacts_dir)

    _prepend_env_path("PYTHONPATH", str(repo_root))
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    runner_path = repo_root / "scripts" / "run_shadow_enhanced.py"
    ticker = _get_env_value("SHADOW_RUNNER_TICKER")
    output_path = _get_env_value("SHADOW_RUNNER_OUTPUT") or str(
        artifacts_dir / "flight_recorder.csv"
    )
    extra_args = _get_env_value("SHADOW_RUNNER_EXTRA_ARGS")
    run_once = _truthy_env("SHADOW_ONCE", True)

    if not runner_path.exists():
        print(f"ERROR: runner not found at {runner_path}", file=sys.stderr)
        return 2

    print(
        "SHADOW_RUNNER_CONFIG"
        f" mode=SHADOW ticker={ticker or 'NONE'}"
        f" output={output_path} artifacts_dir={artifacts_dir}"
    )

    cmd = [sys.executable, str(runner_path)]
    if run_once:
        cmd.append("--once")
    if ticker:
        cmd.extend(["--ticker", ticker])
    if output_path:
        cmd.extend(["--output", output_path])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
