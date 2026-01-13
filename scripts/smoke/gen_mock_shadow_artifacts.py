#!/usr/bin/env python3
"""Generate mock shadow artifacts for CI verification.

This script creates mock artifacts with intentionally secret-laden data
to verify that the sanitizer properly removes all sensitive information.

Usage:
    export SHADOW_ARTIFACTS_DIR=/tmp/test_artifacts/shadow
    python3 scripts/smoke/gen_mock_shadow_artifacts.py

Exit codes:
    0: Success - artifacts generated
    1: Failure - error during generation
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from recorder.shadow_artifacts import write_shadow_artifacts
from recorder.journal_schema import JOURNAL_COLUMNS


def generate_mock_artifacts() -> bool:
    """Generate mock artifacts with secret-laden test data.

    Returns:
        True if successful, False otherwise
    """
    # Intentionally include ALL secret patterns that should be sanitized
    raw_error_with_secrets = (
        "Failed to connect: "
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 "
        "api_key=sk-live-abc123456789 "
        "secret=mysupersecretvalue "
        "token=tok_1234567890abcdef "
        "private_key=MIIEvgIBADANBgkqhkiG9w0BAQ "
        "password=hunter2 "
        "API-KEY=another-key-value "
        "apikey=yetanotherkey"
    )

    # Create summary with secrets in error field
    summary = {
        "schema_version": "shadow_summary_v1",
        "mode": "SHADOW",
        "last_refresh": datetime.now(timezone.utc).isoformat(),
        "strategy": "mock_test_strategy",
        "run_id": "mock_run_001",
        "market": "MOCK-MARKET-TEST",
        "decision": "NO_TRADE",
        "reason": "MOCK_TEST",
        "subreason": "",
        "edge_bps": None,
        "pm_yes_mid": 50.0,
        "fair_yes_prob": 0.5,
        "notes": "This is a mock test with secret=hidden inside",
        "last_error": raw_error_with_secrets,
    }

    # Create health with secrets in error field
    health = {
        "schema_version": "shadow_health_v1",
        "mode": "SHADOW",
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_success_at": None,
        "last_error_at": datetime.now(timezone.utc).isoformat(),
        "last_error": raw_error_with_secrets,
        "last_latency_ms": 100,
        "artifacts_written": True,
        "journal_rows": 3,
        "build": {"git_sha": "mock123", "version": "mock-v1"},
        "uptime_sec": 60,
    }

    # Create multiple journal rows
    journal_rows = []
    for i in range(3):
        row = {
            "ts": 1704067200000 + i * 1000,
            "market_id": "MOCK-MARKET",
            "now": 1704067200000 + i * 1000,
            "market_end_ts": 0,
            "venue": "MOCK",
            "symbol": "MOCK-SYMBOL",
            "official_required_venue": "MOCK",
            "official_used_venue": "MOCK",
            "official_used_endpoint": "MOCK",
            "official_mid": None,
            "official_ok": False,
            "official_err": "MOCK",
            "official_age_ms": 0,
            "pm_yes_bid": 45.0,
            "pm_yes_ask": 55.0,
            "pm_no_bid": 45.0,
            "pm_no_ask": 55.0,
            "book_ok": True,
            "book_err": "",
            "pm_book_age_ms": 0,
            "implied_yes": 0.5,
            "implied_no": 0.5,
            "fair_up_prob": 0.5,
            "edge_yes": None,
            "edge_no": None,
            "edge_gross_bps": None,
            "edge_net_bps": None,
            "spread_bps": 100.0,
            "depth_total": 1000.0,
            "market_class": "MOCK",
            "required_symbol": "MOCK",
            "rules_end_ts": None,
            "end_ts_source": "MOCK",
            "regime": "NORMAL",
            "action": "NO_TRADE",
            "reason": "MOCK",
            "filter_reason": "",
            "microstructure_flags": "[]",
            "daily_pnl": 0.0,
            "daily_loss": 0.0,
            "total_loss": 0.0,
            "open_markets": 0,
            "kill_switch": False,
            "params_hash": "",
            # Signal columns (empty for mock)
            "signal_book_arbitrage_edge_bps": "",
            "signal_book_arbitrage_reason": "",
            "signal_book_arbitrage_confidence": "",
            "signal_book_staleness_edge_bps": "",
            "signal_book_staleness_reason": "",
            "signal_book_staleness_confidence": "",
            "arb_cost_cents": "",
            "arb_edge_cents": "",
        }
        journal_rows.append(row)

    try:
        write_shadow_artifacts(
            summary,
            journal_rows,
            health,
            header_cols=JOURNAL_COLUMNS,
        )
        return True
    except Exception as e:
        print(f"ERROR: Failed to generate mock artifacts: {e}", file=sys.stderr)
        return False


def main() -> int:
    """Main entry point."""
    # Check that SHADOW_ARTIFACTS_DIR is set
    artifacts_dir = os.environ.get("SHADOW_ARTIFACTS_DIR")
    if not artifacts_dir:
        print(
            "ERROR: SHADOW_ARTIFACTS_DIR environment variable must be set",
            file=sys.stderr,
        )
        return 1

    print(f"Generating mock artifacts in: {artifacts_dir}")

    if generate_mock_artifacts():
        print("SUCCESS: Mock artifacts generated")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
