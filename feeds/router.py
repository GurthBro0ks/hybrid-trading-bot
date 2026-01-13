"""Router for official feeds with priority and US-reachability focus."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from feeds import binance_spot, coinbase_spot, gemini_spot

logger = logging.getLogger(__name__)

def get_official_price(
    symbol_pair: str = "BTC/USD",
    timeout_sec: float = 5.0,
) -> Optional[Tuple[float, int, int, str]]:
    """
    Tries multiple feeds in priority order.
    Returns (mid, venue_ts_ms, local_ts_ms, source_name) or None.
    """
    # Map BTC/USD to venue symbols
    symbol_map = {
        "BTC/USD": {
            "coinbase": "BTC-USD",
            "gemini": "btcusd",
            "binance": "BTCUSDT",
        },
        "BTC/USDT": {
            "coinbase": "BTC-USD",
            "gemini": "btcusd",
            "binance": "BTCUSDT",
        },
        "ETH/USD": {
            "coinbase": "ETH-USD",
            "gemini": "ethusd",
            "binance": "ETHUSDT",
        },
        "ETH/USDT": {
            "coinbase": "ETH-USD",
            "gemini": "ethusd",
            "binance": "ETHUSDT",
        }
    }
    
    mapping = symbol_map.get(symbol_pair, {})
    
    # Priority 1: Coinbase
    cb_symbol = mapping.get("coinbase")
    if cb_symbol:
        res = coinbase_spot.get_mid_price(cb_symbol, timeout_sec)
        if res:
            return (*res, "coinbase")
            
    # Priority 2: Gemini
    gem_symbol = mapping.get("gemini")
    if gem_symbol:
        res = gemini_spot.get_mid_price(gem_symbol, timeout_sec)
        if res:
            return (*res, "gemini")
            
    # Priority 3: Binance (Fallback)
    bin_symbol = mapping.get("binance")
    if bin_symbol:
        res = binance_spot.get_mid_price(bin_symbol, timeout_sec)
        if res:
            return (*res, "binance")
            
    return None
