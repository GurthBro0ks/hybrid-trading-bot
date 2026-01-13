"""Kalshi-specific eligibility and rules logic."""

from __future__ import annotations

import logging
import re
import time
from enum import Enum
from typing import Optional, Tuple

from sources.resolution_source import ResolutionSource, resolution_source_from_metadata, is_unknown

logger = logging.getLogger("kalshi_rules")


class EligibilityResult(Enum):
    ELIGIBLE = "ELIGIBLE"
    UNSUPPORTED_RULES = "UNSUPPORTED_RULES"
    MISSING_CLOSE_TIME = "MISSING_CLOSE_TIME"
    MARKET_CLOSED = "MARKET_CLOSED"
    FEED_ROUTING_UNKNOWN = "FEED_ROUTING_UNKNOWN"


def is_market_open(now_ts: float, close_ts: float, buffer_sec: float = 0.0) -> bool:
    """
    Returns True if market is open and not within buffer of closing.
    Strict inequality: must be strictly less than close_ts - buffer.
    """
    return now_ts < (close_ts - buffer_sec)


def check_kalshi_eligibility(
    market_metadata: dict,
    now_ts: Optional[float] = None,
    time_buffer_sec: float = 5.0,
) -> Tuple[EligibilityResult, Optional[ResolutionSource]]:
    """
    Validates if a Kalshi market is eligible for trading.
    Returns (Result, ResolutionSource).
    """
    if now_ts is None:
        now_ts = time.time()

    # 1. Rules/Feed Check
    # We rely on resolution_source logic to parse rules.
    # We construct a metadata dict compatible with resolution_source_from_metadata
    # Kalshi API fields: "rules_primary", "rules_secondary" -> we combine or check primary.
    # Usually "rules_primary" contains the text we need.
    rules_text = market_metadata.get("rules_primary") or market_metadata.get("rules") or ""
    
    # Fail if empty
    if not rules_text:
        return EligibilityResult.UNSUPPORTED_RULES, None

    # Use shared source resolver
    # Note: resolution_source_from_metadata expects dict with "rules_text" or similar
    source = resolution_source_from_metadata({"rules_text": rules_text})
    if is_unknown(source):
        return EligibilityResult.UNSUPPORTED_RULES, None

    # Check if we assume we can route this source.
    # Currently we only really support official feeds for BTC/ETH on Coinbase/Gemini/Binance
    # The source object tells us the venue/symbol. We need to verify if we have a feed for it.
    # For now, we assume if resolution_source matched a known pattern, it's supported.
    # But strictly, we should check if it's one of our targeted mappings? 
    # The user req says: "underlying feed mapping is known... fail-closed by default"
    # The ResolutionSource has 'venue' and 'symbol'.
    if source.venue not in ("coinbase", "gemini", "binance"):
        return EligibilityResult.FEED_ROUTING_UNKNOWN, source

    # 2. Time Check
    # Kalshi fields: "close_time", "expiration_time". usually close_time is what we want.
    # It sends ISO strings usually, but verify what fetch_market returns.
    # Assuming fetch_market returns parsed JSON, dates are likely strings.
    # We need to parse them.
    # Actually, looking at Kalshi API docs (or standard behavior), timestamps are often strings.
    # But wait, let's look at what we receive.
    # If the response is raw JSON, it's ISO strings.
    # We need a helper to parse ISO.
    
    # Wait, let's verify if we need to implement date parsing.
    # Standard python methods.
    
    close_time_str = market_metadata.get("close_time")
    if not close_time_str:
        return EligibilityResult.MISSING_CLOSE_TIME, source
        
    try:
        # Robust ISO parse
        # If python 3.11+, fromisoformat handles Z.
        # Else replace Z.
        if close_time_str.endswith('Z'):
            close_time_str = close_time_str[:-1] + '+00:00'
        
        from datetime import datetime
        close_dt = datetime.fromisoformat(close_time_str)
        close_ts = close_dt.timestamp()
    except (ValueError, TypeError):
         return EligibilityResult.MISSING_CLOSE_TIME, source

    if not is_market_open(now_ts, close_ts, time_buffer_sec):
         return EligibilityResult.MARKET_CLOSED, source

    return EligibilityResult.ELIGIBLE, source
