"""Decision journaling for stale-edge strategy."""

from __future__ import annotations

import csv
import os
from typing import Dict, List


COLUMNS: List[str] = [
    "ts",
    "market_id",
    "now",
    "market_end_ts",
    "official_mid",
    "official_age_ms",
    "pm_yes_bid",
    "pm_yes_ask",
    "pm_no_bid",
    "pm_no_ask",
    "pm_book_age_ms",
    "implied_yes",
    "implied_no",
    "fair_up_prob",
    "edge_yes",
    "edge_no",
    "action",
    "reason",
    "thin_book_reason",
    "thin_book_threshold_depth_usd",
    "thin_book_threshold_qty",
    "thin_book_spread_bps",
    "params_hash",
]


class TradeJournal:
    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()

    def record_decision(self, row: Dict[str, object]) -> None:
        with open(self.path, "a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writerow({key: row.get(key, "") for key in COLUMNS})
