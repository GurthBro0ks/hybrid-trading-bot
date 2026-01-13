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
OPTIONAL_KEYS = {"raw", "depth_notional_total_usd"}


def _assert_payload_shape(payload: dict) -> None:
    keys = set(payload.keys())
    assert REQUIRED_KEYS.issubset(keys)
    unexpected = keys.difference(REQUIRED_KEYS | OPTIONAL_KEYS)
    assert not unexpected

    assert payload["status"] in {item.name for item in BookStatus}
    if payload["fail_reason"] is not None:
        assert payload["fail_reason"] in {item.name for item in BookFailReason}

    assert isinstance(payload["ts"], (int, float))
    assert isinstance(payload["depth_qty_total"], (int, float))

    if payload["status"] == "OK":
        assert isinstance(payload["best_bid"], (int, float))
        assert isinstance(payload["best_ask"], (int, float))
        assert payload["fail_reason"] is None
    else:
        assert payload["best_bid"] is None
        assert payload["best_ask"] is None


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
    _assert_payload_shape(payload)


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
    _assert_payload_shape(payload)
