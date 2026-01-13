"""Tests for shadow artifacts contract compliance.

These tests verify that the artifact writer produces files that conform
to the Shadow Artifacts Contract v1.0.
"""

import csv
import json
import os
import pytest
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recorder.shadow_artifacts import (
    write_shadow_artifacts,
    resolve_artifacts_dir,
    atomic_write_json,
    atomic_write_csv_bounded,
    SUMMARY_FILE,
    JOURNAL_FILE,
    HEALTH_FILE,
)
from recorder.journal_schema import JOURNAL_COLUMNS, normalize_row_for_csv


@pytest.fixture
def tmp_artifacts_dir(tmp_path, monkeypatch):
    """Create a temporary artifacts directory and set env var."""
    artifacts_dir = tmp_path / "artifacts" / "shadow"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SHADOW_ARTIFACTS_DIR", str(artifacts_dir))
    return artifacts_dir


@pytest.fixture
def sample_summary():
    """Create a valid sample summary."""
    return {
        "schema_version": "shadow_summary_v1",
        "mode": "SHADOW",
        "last_refresh": datetime.now(timezone.utc).isoformat(),
        "strategy": "test_strategy",
        "run_id": "test_run_001",
        "market": "TEST-MARKET-123",
        "decision": "NO_TRADE",
        "reason": "TEST_REASON",
        "subreason": "",
        "edge_bps": None,
        "pm_yes_mid": 50.0,
        "fair_yes_prob": 0.5,
        "notes": "",
        "last_error": "",
    }


@pytest.fixture
def sample_health():
    """Create a valid sample health dict."""
    return {
        "schema_version": "shadow_health_v1",
        "mode": "SHADOW",
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_success_at": None,
        "last_error_at": None,
        "last_error": "",
        "last_latency_ms": 100,
        "artifacts_written": True,
        "journal_rows": 1,
        "build": {"git_sha": "abc1234", "version": None},
        "uptime_sec": 60,
    }


@pytest.fixture
def sample_journal_row():
    """Create a valid sample journal row."""
    return {
        "ts": 1704067200000,
        "market_id": "TEST-MARKET",
        "now": 1704067200000,
        "market_end_ts": 0,
        "venue": "TEST",
        "symbol": "TEST-SYMBOL",
        "official_required_venue": "TEST",
        "official_used_venue": "TEST",
        "official_used_endpoint": "API",
        "official_mid": None,
        "official_ok": False,
        "official_err": "TEST",
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
        "market_class": "TEST",
        "required_symbol": "TEST",
        "rules_end_ts": None,
        "end_ts_source": "TEST",
        "regime": "NORMAL",
        "action": "NO_TRADE",
        "reason": "TEST",
        "filter_reason": "",
        "microstructure_flags": "[]",
        "daily_pnl": 0.0,
        "daily_loss": 0.0,
        "total_loss": 0.0,
        "open_markets": 0,
        "kill_switch": False,
        "params_hash": "",
    }


class TestResolveArtifactsDir:
    """Tests for resolve_artifacts_dir function."""

    def test_uses_override_when_provided(self, tmp_path):
        """Override parameter takes precedence."""
        result = resolve_artifacts_dir(str(tmp_path / "custom"))
        assert result == tmp_path / "custom"

    def test_uses_env_var(self, tmp_path, monkeypatch):
        """Uses SHADOW_ARTIFACTS_DIR env var when set."""
        monkeypatch.setenv("SHADOW_ARTIFACTS_DIR", str(tmp_path / "from_env"))
        result = resolve_artifacts_dir()
        assert result == tmp_path / "from_env"

    def test_uses_default(self, monkeypatch):
        """Uses default path when no override or env var."""
        monkeypatch.delenv("SHADOW_ARTIFACTS_DIR", raising=False)
        result = resolve_artifacts_dir()
        assert result == Path("artifacts/shadow")


class TestAtomicWriteJson:
    """Tests for atomic JSON writing."""

    def test_creates_file(self, tmp_path):
        """Creates JSON file with correct content."""
        path = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        atomic_write_json(path, data)

        assert path.exists()
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_creates_parent_dirs(self, tmp_path):
        """Creates parent directories if they don't exist."""
        path = tmp_path / "deep" / "nested" / "test.json"
        atomic_write_json(path, {"test": True})
        assert path.exists()

    def test_sorts_keys(self, tmp_path):
        """JSON keys are sorted for reproducibility."""
        path = tmp_path / "test.json"
        atomic_write_json(path, {"z": 1, "a": 2, "m": 3})

        with open(path) as f:
            content = f.read()
        # a should appear before m, m before z
        assert content.index('"a"') < content.index('"m"') < content.index('"z"')

    def test_size_limit_enforced(self, tmp_path):
        """Raises ValueError if JSON exceeds 10KB."""
        path = tmp_path / "test.json"
        # Create data larger than 10KB
        large_data = {"key": "x" * 15000}
        with pytest.raises(ValueError, match="exceeds 10KB"):
            atomic_write_json(path, large_data)


class TestAtomicWriteCsvBounded:
    """Tests for atomic CSV writing with bounding."""

    def test_creates_file_with_header(self, tmp_path):
        """Creates CSV file with correct header."""
        path = tmp_path / "test.csv"
        headers = ["col1", "col2", "col3"]
        rows = [{"col1": "a", "col2": "b", "col3": "c"}]
        atomic_write_csv_bounded(path, headers, rows, max_rows=100)

        assert path.exists()
        with open(path) as f:
            reader = csv.reader(f)
            header_row = next(reader)
        assert header_row == headers

    def test_bounds_rows(self, tmp_path, monkeypatch):
        """Keeps only max_rows newest rows."""
        monkeypatch.setenv("SHADOW_JOURNAL_MAX_ROWS", "5")
        path = tmp_path / "test.csv"
        headers = ["id", "value"]
        rows = [{"id": str(i), "value": f"val{i}"} for i in range(10)]

        atomic_write_csv_bounded(path, headers, rows, max_rows=5)

        with open(path) as f:
            reader = csv.DictReader(f)
            read_rows = list(reader)

        # Should have only 5 rows (newest: 5-9)
        assert len(read_rows) == 5
        assert read_rows[0]["id"] == "5"
        assert read_rows[4]["id"] == "9"

    def test_empty_rows_writes_header_only(self, tmp_path):
        """Empty rows list still writes header."""
        path = tmp_path / "test.csv"
        headers = ["col1", "col2"]
        atomic_write_csv_bounded(path, headers, [], max_rows=100)

        with open(path) as f:
            content = f.read()
        assert "col1" in content
        assert "col2" in content

    def test_raises_on_empty_header(self, tmp_path):
        """Raises ValueError if header_cols is empty."""
        path = tmp_path / "test.csv"
        with pytest.raises(ValueError, match="cannot be empty"):
            atomic_write_csv_bounded(path, [], [], max_rows=100)


class TestWriteShadowArtifacts:
    """Tests for the main write_shadow_artifacts function."""

    def test_creates_all_files(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """Creates all three artifact files."""
        write_shadow_artifacts(
            sample_summary,
            [sample_journal_row],
            sample_health,
            artifacts_dir=str(tmp_artifacts_dir),
        )

        assert (tmp_artifacts_dir / SUMMARY_FILE).exists()
        assert (tmp_artifacts_dir / JOURNAL_FILE).exists()
        assert (tmp_artifacts_dir / HEALTH_FILE).exists()

    def test_summary_has_required_fields(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """Summary JSON has all required fields."""
        write_shadow_artifacts(
            sample_summary,
            [sample_journal_row],
            sample_health,
            artifacts_dir=str(tmp_artifacts_dir),
        )

        with open(tmp_artifacts_dir / SUMMARY_FILE) as f:
            summary = json.load(f)

        required_fields = [
            "schema_version",
            "mode",
            "last_refresh",
            "strategy",
            "run_id",
            "market",
            "decision",
            "reason",
        ]
        for field in required_fields:
            assert field in summary, f"Missing required field: {field}"

        assert summary["schema_version"] == "shadow_summary_v1"
        assert summary["mode"] == "SHADOW"

    def test_health_has_required_fields(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """Health JSON has all required fields."""
        write_shadow_artifacts(
            sample_summary,
            [sample_journal_row],
            sample_health,
            artifacts_dir=str(tmp_artifacts_dir),
        )

        with open(tmp_artifacts_dir / HEALTH_FILE) as f:
            health = json.load(f)

        required_fields = [
            "schema_version",
            "mode",
            "last_run_at",
            "artifacts_written",
            "journal_rows",
        ]
        for field in required_fields:
            assert field in health, f"Missing required field: {field}"

        assert health["schema_version"] == "shadow_health_v1"
        assert health["mode"] == "SHADOW"

    def test_journal_has_all_columns(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """Journal CSV has all expected columns."""
        write_shadow_artifacts(
            sample_summary,
            [sample_journal_row],
            sample_health,
            artifacts_dir=str(tmp_artifacts_dir),
            header_cols=JOURNAL_COLUMNS,
        )

        with open(tmp_artifacts_dir / JOURNAL_FILE) as f:
            reader = csv.reader(f)
            header = next(reader)

        assert header == JOURNAL_COLUMNS

    def test_files_under_size_limit(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """JSON files are under 10KB limit."""
        write_shadow_artifacts(
            sample_summary,
            [sample_journal_row],
            sample_health,
            artifacts_dir=str(tmp_artifacts_dir),
        )

        summary_size = (tmp_artifacts_dir / SUMMARY_FILE).stat().st_size
        health_size = (tmp_artifacts_dir / HEALTH_FILE).stat().st_size

        assert summary_size < 10240, f"Summary too large: {summary_size} bytes"
        assert health_size < 10240, f"Health too large: {health_size} bytes"

    def test_bounded_journal_rows(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row, monkeypatch
    ):
        """Journal is bounded to max rows."""
        monkeypatch.setenv("SHADOW_JOURNAL_MAX_ROWS", "10")

        # Create 20 rows
        rows = []
        for i in range(20):
            row = dict(sample_journal_row)
            row["ts"] = 1704067200000 + i * 1000
            row["market_id"] = f"TEST-{i}"
            rows.append(row)

        write_shadow_artifacts(
            sample_summary,
            rows,
            sample_health,
            artifacts_dir=str(tmp_artifacts_dir),
            header_cols=JOURNAL_COLUMNS,
        )

        with open(tmp_artifacts_dir / JOURNAL_FILE) as f:
            reader = csv.DictReader(f)
            read_rows = list(reader)

        # Should have only 10 rows
        assert len(read_rows) == 10

        # Should have newest rows (10-19)
        assert read_rows[0]["market_id"] == "TEST-10"
        assert read_rows[9]["market_id"] == "TEST-19"

    def test_validates_summary_schema_version(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """Raises on invalid summary schema_version."""
        sample_summary["schema_version"] = "invalid_v1"
        with pytest.raises(ValueError, match="Invalid schema_version"):
            write_shadow_artifacts(
                sample_summary,
                [sample_journal_row],
                sample_health,
                artifacts_dir=str(tmp_artifacts_dir),
            )

    def test_validates_health_mode(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """Raises on invalid health mode."""
        sample_health["mode"] = "LIVE"
        with pytest.raises(ValueError, match="Invalid mode"):
            write_shadow_artifacts(
                sample_summary,
                [sample_journal_row],
                sample_health,
                artifacts_dir=str(tmp_artifacts_dir),
            )


class TestNormalizeRowForCsv:
    """Tests for normalize_row_for_csv function."""

    def test_fills_missing_columns(self):
        """Missing columns are filled with empty string."""
        row = {"ts": 123, "market_id": "TEST"}
        normalized = normalize_row_for_csv(row)

        assert normalized["ts"] == 123
        assert normalized["market_id"] == "TEST"
        assert normalized["venue"] == ""
        assert normalized["action"] == ""

    def test_preserves_existing_values(self, sample_journal_row):
        """Existing values are preserved."""
        normalized = normalize_row_for_csv(sample_journal_row)
        assert normalized["ts"] == sample_journal_row["ts"]
        assert normalized["venue"] == sample_journal_row["venue"]

    def test_has_all_columns(self):
        """Result has all JOURNAL_COLUMNS."""
        normalized = normalize_row_for_csv({})
        assert set(normalized.keys()) == set(JOURNAL_COLUMNS)


class TestSchemaMismatchDetection:
    """Tests for schema mismatch detection."""

    def test_detects_schema_mismatch(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """Detects when existing CSV has different schema."""
        # Write initial file with different header
        journal_path = tmp_artifacts_dir / JOURNAL_FILE
        with open(journal_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["different", "columns", "here"])
            writer.writerow(["val1", "val2", "val3"])

        # Now write with expected columns
        result = write_shadow_artifacts(
            sample_summary,
            [sample_journal_row],
            sample_health,
            artifacts_dir=str(tmp_artifacts_dir),
            header_cols=JOURNAL_COLUMNS,
        )

        # Should return False indicating mismatch
        assert result is False

        # Health should have schema_mismatch flag
        with open(tmp_artifacts_dir / HEALTH_FILE) as f:
            health = json.load(f)
        assert health["schema_mismatch"] is True

    def test_no_mismatch_when_schemas_match(
        self, tmp_artifacts_dir, sample_summary, sample_health, sample_journal_row
    ):
        """No mismatch when schemas match."""
        # Write initial file with correct header
        journal_path = tmp_artifacts_dir / JOURNAL_FILE
        with open(journal_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=JOURNAL_COLUMNS)
            writer.writeheader()

        # Write again
        result = write_shadow_artifacts(
            sample_summary,
            [sample_journal_row],
            sample_health,
            artifacts_dir=str(tmp_artifacts_dir),
            header_cols=JOURNAL_COLUMNS,
        )

        assert result is True

        with open(tmp_artifacts_dir / HEALTH_FILE) as f:
            health = json.load(f)
        assert health["schema_mismatch"] is False
