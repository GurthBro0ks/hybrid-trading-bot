"""Shadow artifacts writer with atomic writes and secret sanitization.

This module implements the Shadow Artifacts Contract v1.0.
See docs/artifacts/SHADOW_ARTIFACTS_CONTRACT.md for details.

Key guarantees:
- Atomic writes (tmp + fsync + os.replace)
- No secrets in output (sanitization)
- Bounded journal (configurable max rows)
- Stable paths and schemas
"""

from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .journal_schema import JOURNAL_COLUMNS, normalize_row_for_csv

# Default values
DEFAULT_ARTIFACTS_DIR = "artifacts/shadow"
DEFAULT_MAX_ROWS = 500
MAX_TEXT_LENGTH = 200

# Secret patterns to remove (case-insensitive)
# Matches the keyword and any following value, handling:
# - "keyword=value" (e.g., "api_key=abc123")
# - "keyword: value" (e.g., "authorization: Bearer token")
# - "keyword value" (e.g., "Bearer abc123")
# The pattern captures up to 2 space-separated tokens after the keyword
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|authorization|bearer|private[_-]?key|password)"
    r"[=:\s]*"          # Optional separators (=, :, space)
    r"[^\s]*"           # First token (may be empty)
    r"(?:\s+[^\s]+)?",  # Optional second token (e.g., "Bearer TOKEN")
    re.IGNORECASE,
)

# File names (stable contract paths)
SUMMARY_FILE = "latest_summary.json"
JOURNAL_FILE = "latest_journal.csv"
HEALTH_FILE = "health.json"


def resolve_artifacts_dir(override: Optional[str] = None) -> Path:
    """Resolve the artifacts directory path.

    Priority:
    1. override parameter (if provided)
    2. SHADOW_ARTIFACTS_DIR environment variable
    3. Default: artifacts/shadow

    Args:
        override: Optional directory path override

    Returns:
        Path to artifacts directory
    """
    if override:
        return Path(override)
    return Path(os.environ.get("SHADOW_ARTIFACTS_DIR", DEFAULT_ARTIFACTS_DIR))


def get_max_rows() -> int:
    """Get maximum journal rows from environment.

    Returns:
        Max rows (default 500)
    """
    try:
        return int(os.environ.get("SHADOW_JOURNAL_MAX_ROWS", DEFAULT_MAX_ROWS))
    except (ValueError, TypeError):
        return DEFAULT_MAX_ROWS


def sanitize_text(text: Optional[str]) -> str:
    """Sanitize text by removing secrets and limiting length.

    Operations:
    1. Remove secret patterns (api_key, token, etc.)
    2. Strip newlines (replace with space)
    3. Cap at MAX_TEXT_LENGTH characters

    Args:
        text: Input text (may be None)

    Returns:
        Sanitized text string
    """
    if text is None:
        return ""

    text = str(text)

    # Remove secret patterns
    text = SECRET_PATTERN.sub("[REDACTED]", text)

    # Strip newlines
    text = text.replace("\n", " ").replace("\r", " ")

    # Cap length
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH - 3] + "..."

    return text


def atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    """Write JSON atomically using tmp + fsync + replace.

    Args:
        path: Target file path
        obj: Dictionary to serialize as JSON

    Raises:
        ValueError: If resulting JSON exceeds 10KB
    """
    content = json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2)

    # Check size limit (10KB)
    if len(content.encode("utf-8")) > 10240:
        raise ValueError(f"JSON content exceeds 10KB limit: {len(content)} bytes")

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file, fsync, then replace
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_write_csv_bounded(
    path: Path,
    header_cols: List[str],
    rows: List[Dict[str, Any]],
    max_rows: int,
    check_existing_header: bool = True,
) -> bool:
    """Write CSV atomically with bounded rows.

    Args:
        path: Target file path
        header_cols: Column header list
        rows: List of row dictionaries
        max_rows: Maximum number of rows to keep (newest)
        check_existing_header: If True, preserve existing header if different

    Returns:
        True if schema matches expected, False if mismatch detected

    Raises:
        ValueError: If header_cols is empty
    """
    if not header_cols:
        raise ValueError("header_cols cannot be empty")

    # Check existing header for schema mismatch
    schema_mismatch = False
    actual_header = header_cols

    if check_existing_header and path.exists():
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                existing_header = next(reader, None)
                if existing_header and existing_header != header_cols:
                    # Schema mismatch - preserve existing header
                    actual_header = existing_header
                    schema_mismatch = True
        except Exception:
            # If we can't read existing file, use new header
            pass

    # Bound rows (keep newest)
    if len(rows) > max_rows:
        rows = rows[-max_rows:]

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file, fsync, then replace
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=actual_header, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                # Normalize row to have all columns
                normalized = {col: row.get(col, "") for col in actual_header}
                writer.writerow(normalized)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return not schema_mismatch


def write_shadow_artifacts(
    summary: Dict[str, Any],
    journal_rows: List[Dict[str, Any]],
    health: Dict[str, Any],
    *,
    artifacts_dir: Optional[str] = None,
    header_cols: Optional[List[str]] = None,
) -> bool:
    """Write all shadow artifacts atomically.

    This is the main entry point for writing shadow artifacts.
    All writes are atomic and sanitized.

    Args:
        summary: Summary data (will be sanitized)
        journal_rows: List of journal row dicts
        health: Health data (will be sanitized)
        artifacts_dir: Optional directory override
        header_cols: Optional column list (defaults to JOURNAL_COLUMNS)

    Returns:
        True if all writes successful and schema matches,
        False if schema mismatch detected

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Resolve paths
    base_dir = resolve_artifacts_dir(artifacts_dir)
    summary_path = base_dir / SUMMARY_FILE
    journal_path = base_dir / JOURNAL_FILE
    health_path = base_dir / HEALTH_FILE

    # Use provided header or default
    cols = header_cols if header_cols is not None else JOURNAL_COLUMNS

    # Get max rows at call time (not import time)
    max_rows = get_max_rows()

    # Validate and sanitize summary
    _validate_summary(summary)
    sanitized_summary = _sanitize_summary(summary)

    # Normalize journal rows
    normalized_rows = [normalize_row_for_csv(row) for row in journal_rows]

    # Write CSV first (may detect schema mismatch)
    schema_ok = atomic_write_csv_bounded(
        journal_path, cols, normalized_rows, max_rows
    )

    # Update health with schema mismatch status
    health["schema_mismatch"] = not schema_ok

    # Validate and sanitize health
    _validate_health(health)
    sanitized_health = _sanitize_health(health)

    # Write JSON files
    atomic_write_json(summary_path, sanitized_summary)
    atomic_write_json(health_path, sanitized_health)

    return schema_ok


def _validate_summary(summary: Dict[str, Any]) -> None:
    """Validate required summary fields.

    Raises:
        ValueError: If required fields are missing
    """
    required = [
        "schema_version",
        "mode",
        "last_refresh",
        "strategy",
        "run_id",
        "market",
        "decision",
        "reason",
    ]
    missing = [f for f in required if f not in summary]
    if missing:
        raise ValueError(f"Missing required summary fields: {missing}")

    if summary.get("schema_version") != "shadow_summary_v1":
        raise ValueError(
            f"Invalid schema_version: {summary.get('schema_version')}, "
            "expected 'shadow_summary_v1'"
        )

    if summary.get("mode") != "SHADOW":
        raise ValueError(
            f"Invalid mode: {summary.get('mode')}, expected 'SHADOW'"
        )


def _validate_health(health: Dict[str, Any]) -> None:
    """Validate required health fields.

    Raises:
        ValueError: If required fields are missing
    """
    required = [
        "schema_version",
        "mode",
        "last_run_at",
        "artifacts_written",
        "journal_rows",
    ]
    missing = [f for f in required if f not in health]
    if missing:
        raise ValueError(f"Missing required health fields: {missing}")

    if health.get("schema_version") != "shadow_health_v1":
        raise ValueError(
            f"Invalid schema_version: {health.get('schema_version')}, "
            "expected 'shadow_health_v1'"
        )

    if health.get("mode") != "SHADOW":
        raise ValueError(
            f"Invalid mode: {health.get('mode')}, expected 'SHADOW'"
        )


def _sanitize_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize summary by removing secrets from text fields."""
    result = dict(summary)

    # Sanitize text fields
    text_fields = ["notes", "last_error", "reason", "subreason"]
    for field in text_fields:
        if field in result:
            result[field] = sanitize_text(result.get(field))

    return result


def _sanitize_health(health: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize health by removing secrets from text fields."""
    result = dict(health)

    # Sanitize text fields
    if "last_error" in result:
        result["last_error"] = sanitize_text(result.get("last_error"))

    return result
