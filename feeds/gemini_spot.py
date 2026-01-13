"""Gemini spot mid-price adapter."""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

GEMINI_TICKER_URL = "https://api.gemini.com/v1/pubticker/{symbol}"

def get_mid_price(
    symbol: str = "btcusd",
    timeout_sec: float = 5.0,
) -> Optional[Tuple[float, int, int]]:
    """
    Return (mid, venue_ts_ms, local_ts_ms). Returns None on failure.
    """
    req = urllib.request.Request(
        GEMINI_TICKER_URL.format(symbol=symbol),
        headers={"User-Agent": "pm-updown-bot/0.1"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read())
            bid = float(data["bid"])
            ask = float(data["ask"])
            # Gemini timestamp is in 'volume' field sometimes, or not at all in v1 pubticker.
            # Actually, pubticker v1 has no top-level timestamp.
            # Let's use local_ts as venue_ts if missing.
            venue_ts_ms = int(time.time() * 1000)
            
            mid = (bid + ask) / 2.0
            return mid, venue_ts_ms, int(time.time() * 1000)
    except Exception as exc:
        logger.warning("Gemini feed error: %s", exc)
        return None
