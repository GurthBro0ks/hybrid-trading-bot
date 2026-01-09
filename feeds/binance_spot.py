"""Minimal Binance spot mid-price adapter with retries and time sync."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Optional, Tuple


BINANCE_TIME_URL = "https://api.binance.com/api/v3/time"
BINANCE_BOOK_URL = "https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"

logger = logging.getLogger(__name__)


def _http_get_json(url: str, timeout_sec: float) -> Optional[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "pm-updown-bot/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            payload = resp.read()
            return json.loads(payload)
    except urllib.error.HTTPError as exc:
        if exc.code == 451:
            logger.error("FEED_BLOCKED: HTTP 451 from %s", url)
            return None
        logger.warning("HTTP error from %s: %s", url, exc)
    except urllib.error.URLError as exc:
        logger.warning("URL error from %s: %s", url, exc)
    except json.JSONDecodeError as exc:
        logger.warning("JSON decode error from %s: %s", url, exc)
    return None


def get_server_time_ms(timeout_sec: float) -> Optional[int]:
    payload = _http_get_json(BINANCE_TIME_URL, timeout_sec)
    if not payload:
        return None
    server_ms = payload.get("serverTime")
    if isinstance(server_ms, int):
        return server_ms
    return None


def get_mid_price(
    symbol: str = "BTCUSDT",
    timeout_sec: float = 5.0,
    max_retries: int = 3,
    backoff_sec: float = 0.5,
) -> Optional[Tuple[float, int, int]]:
    """
    Return (mid, venue_ts_ms, local_ts_ms). Returns None on failure or block.
    """
    for attempt in range(max_retries):
        server_ts = get_server_time_ms(timeout_sec)
        payload = _http_get_json(BINANCE_BOOK_URL.format(symbol=symbol), timeout_sec)
        if payload is None:
            if attempt < max_retries - 1:
                time.sleep(backoff_sec * (2**attempt))
                continue
            return None
        try:
            bid = float(payload["bidPrice"])
            ask = float(payload["askPrice"])
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Invalid book payload: %s", exc)
            if attempt < max_retries - 1:
                time.sleep(backoff_sec * (2**attempt))
                continue
            return None

        mid = (bid + ask) / 2.0
        local_ts = int(time.time() * 1000)
        venue_ts = server_ts if server_ts is not None else local_ts
        return mid, venue_ts, local_ts

    return None
