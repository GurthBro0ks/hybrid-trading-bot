#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from venuebook.types import BookFailReason, BookStatus
from venues.kalshi import fetch_kalshi_venuebook


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Kalshi book and emit VenueBook JSON.")
    parser.add_argument("--market", required=True, help="Kalshi market ticker")
    parser.add_argument("--token", help="Kalshi API bearer token")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        vbook = fetch_kalshi_venuebook(args.market, token=args.token)
    except Exception as exc:
        print(f"Status: FAILED (Unexpected) {exc}", file=sys.stderr)
        return 1

    payload = vbook.to_json_dict()
    status = payload.get("status")
    reason = payload.get("fail_reason")
    valid_status = {item.name for item in BookStatus}
    valid_reasons = {item.name for item in BookFailReason}

    if status not in valid_status:
        print(f"Invalid status value: {status}", file=sys.stderr)
        return 2
    if status == "OK":
        if reason is not None:
            print("Invalid fail_reason for OK status", file=sys.stderr)
            return 2
        if payload.get("best_bid") is None or payload.get("best_ask") is None:
            print("Missing best_bid/best_ask for OK status", file=sys.stderr)
            return 2
    else:
        if reason not in valid_reasons:
            print(f"Invalid fail_reason for NO_TRADE: {reason}", file=sys.stderr)
            return 2
        if payload.get("best_bid") is not None or payload.get("best_ask") is not None:
            print("Unexpected prices for NO_TRADE status", file=sys.stderr)
            return 2

    with out_path.open("w") as f:
        json.dump(payload, f, sort_keys=True)

    print(f"Status: {status} reason={reason} out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
