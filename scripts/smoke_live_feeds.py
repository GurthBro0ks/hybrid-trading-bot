#!/usr/bin/env python3
"""Smoke test for official feeds."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feeds.router import get_official_price

def main():
    print(f"{'SOURCE':<10} {'STATUS':<10} {'LATENCY':<10} {'PRICE':<12} {'QUOTE_TS':<15} {'STALE_MS':<10}")
    print("-" * 75)
    
    start = time.time()
    res = get_official_price("BTC/USD")
    end = time.time()
    latency_ms = int((end - start) * 1000)
    
    if res:
        mid, venue_ts_ms, local_ts_ms, source = res
        now_ms = int(time.time() * 1000)
        stale_ms = now_ms - venue_ts_ms
        print(f"{source:<10} {'OK':<10} {latency_ms:<10} {mid:<12.2f} {venue_ts_ms:<15} {stale_ms:<10}")
        sys.exit(0)
    else:
        print(f"{'ROUTER':<10} {'FAIL':<10} {latency_ms:<10} {'N/A':<12} {'N/A':<15} {'N/A':<10}")
        sys.exit(1)

if __name__ == "__main__":
    main()
