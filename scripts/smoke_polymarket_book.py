#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from venues.polymarket import fetch_polymarket_venuebook


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Polymarket book and emit VenueBook JSON.")
    parser.add_argument("--market", required=True, help="Polymarket token_id")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        vbook = fetch_polymarket_venuebook(args.market)
    except Exception as exc:
        print(f"Status: FAILED (Unexpected) {exc}", file=sys.stderr)
        return 1

    payload = vbook.to_json_dict()
    with out_path.open("w") as f:
        json.dump(payload, f, sort_keys=True)

    print(f"Status: {payload.get('status')} out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
