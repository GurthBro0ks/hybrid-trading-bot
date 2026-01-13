#!/usr/bin/env python3
import argparse
import sys
import time
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from venues.kalshi import fetch_kalshi_venuebook
from venues.kalshi_fetch import fetch_market
from eligibility.kalshi_rules import check_kalshi_eligibility, EligibilityResult
from venuebook.types import BookStatus

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--token", default=None)
    parser.add_argument("--fixture-meta", help="Path to market metadata json fixture")
    parser.add_argument("--fixture-book", help="Path to orderbook json fixture")
    args = parser.parse_args()

    # Mocking if fixtures provided
    if args.fixture_meta or args.fixture_book:
        def mock_get(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            
            if "orderbook" in url and args.fixture_book:
                with open(args.fixture_book) as f:
                    data = json.load(f)
                mock_resp.json.return_value = data
            elif "markets" in url and args.fixture_meta:
                with open(args.fixture_meta) as f:
                    data = json.load(f)
                mock_resp.json.return_value = {"market": data}
            else:
                mock_resp.status_code = 404
            return mock_resp

        p = patch("requests.get", side_effect=mock_get)
        p.start()
        # Suppress fixture noise in stdout
        # print(" [!] Running with FIXTURES (requests.get mocked)")

    metadata_ok = False
    eligibility_ok = False
    book_ok = False
    
    # 1. Metadata & Eligibility
    try:
        meta = fetch_market(args.ticker, token=args.token)
        metadata_ok = True
        print(f"METADATA=OK")
        
        eligibility, source = check_kalshi_eligibility(meta)
        
        if eligibility == EligibilityResult.ELIGIBLE:
            eligibility_ok = True
            print(f"ELIGIBILITY=ELIGIBLE source={source.venue if source else 'None'}")
        else:
            print(f"ELIGIBILITY=NOT_ELIGIBLE reason={eligibility.name}")
            
    except Exception as e:
        print(f"METADATA=FAIL reason={e}")
        # If metadata fails, we can't really judge eligibility safely
        print(f"ELIGIBILITY=FAIL reason=MetadataFetchError")
    
    # 2. Book
    try:
        book = fetch_kalshi_venuebook(args.ticker, token=args.token)
        if book.status == BookStatus.OK:
            book_ok = True
            print(f"BOOK_PARSE=OK depth={book.depth_qty_total}")
        else:
            reason = book.fail_reason.name if book.fail_reason else "UNKNOWN"
            print(f"BOOK_PARSE=FAIL reason={reason}")
    except Exception as e:
        print(f"BOOK_PARSE=FAIL reason={e}")

    # 3. Final Result
    if metadata_ok and eligibility_ok and book_ok:
        print("RESULT=PASS")
        sys.exit(0)
    elif not metadata_ok or not book_ok:
        # Parse/Fetch failure
        print("RESULT=FAIL")
        sys.exit(2)
    elif not eligibility_ok:
        # Eligibility failure
        print("RESULT=FAIL")
        sys.exit(3)
    else:
        # Fallback
        print("RESULT=FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
