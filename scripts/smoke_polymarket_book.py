#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from venues.polymarket_fetch import fetch_book, PolymarketFetchError
from venues.polymarket import parse_polymarket_book
from shared.venue_book import VenueBook

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, help="Polymarket token_id")
    args = parser.parse_args()

    print(f"--- Polymarket Smoke Test: {args.market} ---")
    
    t0 = time.time()
    try:
        raw = fetch_book(args.market)
        latency_ms = int((time.time() - t0) * 1000)
        
        vbook = parse_polymarket_book(raw)
        
        bb = vbook.best_bid()
        ba = vbook.best_ask()
        spread = vbook.spread()
        spread_bps = (spread / bb * 10000) if bb and spread is not None else 0
        depth = vbook.total_depth()
        
        print(f"Status:   OK")
        print(f"Latency:  {latency_ms}ms")
        print(f"Best Bid: {bb}")
        print(f"Best Ask: {ba}")
        print(f"Spread:   {spread:.6f} ({spread_bps:.1f} bps)")
        print(f"Depth:    {depth:.2f}")
        
    except PolymarketFetchError as e:
        print(f"Status:   FAILED (FetchError)")
        print(f"Reason:   {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"Status:   FAILED (Unexpected)")
        print(f"Error:    {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
