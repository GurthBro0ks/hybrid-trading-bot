"""Canonical journal schema for shadow trading artifacts.

This module defines the single source of truth for journal CSV columns.
All columns are STATIC and always emitted. Missing values use empty string.

STABILITY CONTRACT:
- New columns may only be APPENDED to the end
- Existing columns MUST NOT be renamed, removed, or reordered
- This is the v1 schema; additive-only changes permitted
"""

from typing import Dict, Any, List

SCHEMA_VERSION = "journal_v1"

# Static column list - always emit all columns
JOURNAL_COLUMNS: List[str] = [
    # Core timing
    "ts",
    "market_id",
    "now",
    "market_end_ts",
    # Venue/symbol
    "venue",
    "symbol",
    # Official price source
    "official_required_venue",
    "official_used_venue",
    "official_used_endpoint",
    "official_mid",
    "official_ok",
    "official_err",
    "official_age_ms",
    # PM orderbook
    "pm_yes_bid",
    "pm_yes_ask",
    "pm_no_bid",
    "pm_no_ask",
    "book_ok",
    "book_err",
    "pm_book_age_ms",
    # Strategy outputs
    "implied_yes",
    "implied_no",
    "fair_up_prob",
    "edge_yes",
    "edge_no",
    "edge_gross_bps",
    "edge_net_bps",
    "spread_bps",
    "depth_total",
    # Market metadata
    "market_class",
    "required_symbol",
    "rules_end_ts",
    "end_ts_source",
    # Decision
    "regime",
    "action",
    "reason",
    "filter_reason",
    "microstructure_flags",
    # PnL state
    "daily_pnl",
    "daily_loss",
    "total_loss",
    "open_markets",
    "kill_switch",
    "params_hash",
    # --- Signal columns (STATIC, always emitted, empty if not computed) ---
    "signal_book_arbitrage_edge_bps",
    "signal_book_arbitrage_reason",
    "signal_book_arbitrage_confidence",
    "signal_book_staleness_edge_bps",
    "signal_book_staleness_reason",
    "signal_book_staleness_confidence",
    # Arbitrage-specific
    "arb_cost_cents",
    "arb_edge_cents",
]


def normalize_row_for_csv(row: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all JOURNAL_COLUMNS are present with defaults for missing keys.

    Args:
        row: Dictionary with journal data (may have missing keys)

    Returns:
        Dictionary with all JOURNAL_COLUMNS keys, missing values as empty string
    """
    return {col: row.get(col, "") for col in JOURNAL_COLUMNS}


def get_column_count() -> int:
    """Return the number of columns in the journal schema."""
    return len(JOURNAL_COLUMNS)
