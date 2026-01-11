"""Minimal trade journal writer for shadow runner output."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, Dict

from .journal_schema import JOURNAL_COLUMNS, normalize_row_for_csv


class TradeJournal:
    """Append-only CSV journal with a stable header."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record_decision(self, row: Dict[str, Any]) -> None:
        normalized = normalize_row_for_csv(row)
        write_header = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=JOURNAL_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(normalized)
            handle.flush()
            os.fsync(handle.fileno())
