"""Recorder module for shadow trading artifacts.

This module provides:
- TradeJournal: Original trade journal class (from .pyc)
- journal_schema: Canonical journal column definitions
- shadow_artifacts: Artifact writer with atomic writes and sanitization
"""

# Re-export from submodules
from .journal_schema import JOURNAL_COLUMNS, normalize_row_for_csv, SCHEMA_VERSION
from .shadow_artifacts import (
    write_shadow_artifacts,
    sanitize_text,
    resolve_artifacts_dir,
    atomic_write_json,
    atomic_write_csv_bounded,
)

# Try to import TradeJournal from the existing .pyc
# This may fail if the .pyc is incompatible, but we don't want to break imports
try:
    from .trade_journal import TradeJournal
except ImportError:
    TradeJournal = None  # type: ignore

__all__ = [
    # Journal schema
    "JOURNAL_COLUMNS",
    "SCHEMA_VERSION",
    "normalize_row_for_csv",
    # Shadow artifacts
    "write_shadow_artifacts",
    "sanitize_text",
    "resolve_artifacts_dir",
    "atomic_write_json",
    "atomic_write_csv_bounded",
    # Original trade journal (may be None if import fails)
    "TradeJournal",
]
