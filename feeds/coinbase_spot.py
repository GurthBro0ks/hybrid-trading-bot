"""Coinbase spot mid-price adapter."""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

COINBASE_TICKER_URL = "https://api.exchange.coinbase.com/products/{symbol}/ticker"

def get_mid_price(
    symbol: str = "BTC-USD",
    timeout_sec: float = 5.0,
) -> Optional[Tuple[float, int, int]]:
    """
    Return (mid, venue_ts_ms, local_ts_ms). Returns None on failure.
    """
    req = urllib.request.Request(
        COINBASE_TICKER_URL.format(symbol=symbol),
        headers={"User-Agent": "pm-updown-bot/0.1"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read())
            bid = float(data["bid"])
            ask = float(data["ask"])
            # Example: "2026-01-10T18:30:36.428971Z"
            # We can parse this or just use local_ts if it's too complex for minimal script.
            # But let's try a simple parse if possible.
            venue_ts_raw = data["time"]
            # ISO format: 2026-01-10T18:30:36.428971134Z
            # Simple fallback to local_ts if parsing fails
            try:
                # Remove nanoseconds if more than 6 digits
                main_ts, suffix = venue_ts_raw.split(".")
                suffix = suffix[:-1] # remove Z
                if len(suffix) > 6:
                    suffix = suffix[:6]
                ts_iso = f"{main_ts}.{suffix}Z"
                from datetime import datetime
                dt = datetime.strptime(ts_iso, "%Y-%m-%dT%H:%M:%S.%fZ")
                venue_ts_ms = int(dt.timestamp() * 1000)
            except Exception:
                venue_ts_ms = int(time.time() * 1000)
            
            mid = (bid + ask) / 2.0
            return mid, venue_ts_ms, int(time.time() * 1000)
    except Exception as exc:
        logger.warning("Coinbase feed error: %s", exc)
        return None
