#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from venuebook.types import BookFailReason, BookStatus, VenueBook

DEFAULT_TS = 1234567890.0


def _assert_numeric(value: object) -> None:
    assert isinstance(value, (int, float))
    assert not isinstance(value, bool)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic VenueBook contract samples.")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--ts", type=float, default=DEFAULT_TS, help="Override fixed timestamp")
    args = parser.parse_args()

    ts = float(args.ts)

    ok_book = VenueBook(
        venue="contract",
        ts=ts,
        best_bid=0.25,
        best_ask=0.30,
        depth_qty_total=1000.0,
        depth_notional_total_usd=250.0,
        status=BookStatus.OK,
        fail_reason=None,
        raw=None,
    )
    no_trade_book = VenueBook(
        venue="contract",
        ts=ts,
        best_bid=None,
        best_ask=None,
        depth_qty_total=0.0,
        depth_notional_total_usd=None,
        status=BookStatus.NO_TRADE,
        fail_reason=BookFailReason.PARSE_AMBIGUOUS,
        raw=None,
    )

    ok_payload = ok_book.to_json_dict()
    no_trade_payload = no_trade_book.to_json_dict()

    assert ok_payload["status"] == "OK"
    assert ok_payload["fail_reason"] is None
    _assert_numeric(ok_payload["best_bid"])
    _assert_numeric(ok_payload["best_ask"])

    assert no_trade_payload["status"] == "NO_TRADE"
    assert no_trade_payload["fail_reason"] in {reason.name for reason in BookFailReason}
    assert no_trade_payload["best_bid"] is None
    assert no_trade_payload["best_ask"] is None

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ok": ok_payload, "no_trade": no_trade_payload}
    with out_path.open("w") as f:
        json.dump(payload, f, sort_keys=True)

    print(f"Wrote VenueBook contract heartbeat to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
