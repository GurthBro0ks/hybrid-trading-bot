#!/usr/bin/env python3
"""
Phase 5 Shadow Strategy Runner Gate Script

Minimal wrapper ensuring:
- SHADOW mode (read-only, no trading)
- Single iteration execution
- Stable artifact outputs
- No secrets in artifacts

This script is a thin alias for the canonical production entrypoint.
It forces SHADOW mode with single-cycle execution and defaults to INXD-26JAN17.
"""
import os
import sys
import subprocess
from pathlib import Path


def main():
    # Handle --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        print("\nUsage: python3 run_shadow_stale_edge.py [--once]")
        print("\nEnvironment Variables:")
        print("  SHADOW_RUNNER_TICKER       Market ticker (default: INXD-26JAN17)")
        print("  SHADOW_RUNNER_OUTPUT       Output file path (optional)")
        print("  SHADOW_RUNNER_EXTRA_ARGS   Extra CLI arguments (optional)")
        print("  SHADOW_ARTIFACTS_DIR       Artifacts directory (default: artifacts/shadow)")
        print("\nNote: --once flag is accepted but has no effect (already forced via SHADOW_ONCE=1)")
        sys.exit(0)

    # Ensure repo root
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)

    # Environment configuration
    env = os.environ.copy()
    env.setdefault("SHADOW_ONCE", "1")  # Force single iteration
    env.setdefault("SHADOW_ARTIFACTS_DIR", "artifacts/shadow")
    env.setdefault("SHADOW_RUNNER_TICKER", "INXD-26JAN17")  # Default ticker

    # Minimal output (safe, no secrets)
    print("mode=SHADOW runner=stale_edge_alias once=1", flush=True)

    # Delegate to canonical production entrypoint
    entrypoint = repo_root / "scripts" / "run_shadow_prod_entrypoint.py"
    result = subprocess.run([sys.executable, str(entrypoint)], env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
