from venuebook.types import BookFailReason, BookStatus, VenueBook

REQUIRED_KEYS = {
    "venue",
    "ts",
    "best_bid",
    "best_ask",
    "depth_qty_total",
    "status",
    "fail_reason",
}


def _assert_payload_basics(payload: dict) -> None:
    keys = set(payload.keys())
    assert REQUIRED_KEYS.issubset(keys)

    assert payload["status"] in {item.name for item in BookStatus}
    if payload["fail_reason"] is not None:
        assert payload["fail_reason"] in {item.name for item in BookFailReason}


def test_venuebook_ok_contract_serialization() -> None:
    book = VenueBook(
        venue="polymarket",
        ts=123.0,
        best_bid=0.45,
        best_ask=0.46,
        depth_qty_total=150.0,
        depth_notional_total_usd=67.5,
        status=BookStatus.OK,
        fail_reason=None,
    )
    payload = book.to_json_dict()
    _assert_payload_basics(payload)


def test_venuebook_no_trade_contract_serialization() -> None:
    book = VenueBook(
        venue="polymarket",
        ts=123.0,
        best_bid=None,
        best_ask=None,
        depth_qty_total=0.0,
        depth_notional_total_usd=None,
        status=BookStatus.NO_TRADE,
        fail_reason=BookFailReason.NO_BBO,
    )
    payload = book.to_json_dict()
    _assert_payload_basics(payload)
