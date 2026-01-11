import importlib.util
import json
from pathlib import Path

import pytest

import venues.polymarket as polymarket
from venuebook.types import BookFailReason, BookStatus
from venues.polymarket_fetch import PolymarketFetchError

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "polymarket"


def _load_fixture(name: str) -> dict:
    path = FIXTURE_DIR / name
    with path.open("r") as f:
        return json.load(f)


def test_polymarket_adapter_ok_fixture() -> None:
    raw = _load_fixture("ok_book.json")
    book = polymarket.parse_polymarket_book(raw, ts=123.0)

    assert book.status == BookStatus.OK
    assert book.fail_reason is None
    assert isinstance(book.best_bid, float)
    assert isinstance(book.best_ask, float)


def test_polymarket_adapter_no_bbo_fixture() -> None:
    raw = _load_fixture("no_bbo.json")
    book = polymarket.parse_polymarket_book(raw, ts=123.0)

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.NO_BBO
    assert book.best_bid is None
    assert book.best_ask is None


def test_polymarket_adapter_depth_below_fixture() -> None:
    raw = _load_fixture("depth_below.json")
    book = polymarket.parse_polymarket_book(raw, ts=123.0)

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.DEPTH_BELOW_THRESHOLD
    assert book.best_bid is None
    assert book.best_ask is None


def test_polymarket_adapter_spread_wide_fixture() -> None:
    raw = _load_fixture("spread_wide.json")
    book = polymarket.parse_polymarket_book(raw, ts=123.0)

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.SPREAD_WIDE
    assert book.best_bid is None
    assert book.best_ask is None


def test_polymarket_adapter_ambiguous_fixture_fail_closed() -> None:
    raw = _load_fixture("ambiguous.json")
    book = polymarket.parse_polymarket_book(raw, ts=123.0)

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.PARSE_AMBIGUOUS
    assert book.best_bid is None
    assert book.best_ask is None


def test_polymarket_adapter_never_raises_on_fixtures() -> None:
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        raw = _load_fixture(path.name)
        book = polymarket.parse_polymarket_book(raw, ts=123.0)
        assert book.status in {BookStatus.OK, BookStatus.NO_TRADE}


def test_polymarket_fetch_failure_maps_to_book_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_: str, timeout_s: float = 5.0) -> dict:
        raise PolymarketFetchError("HTTP_404", status_code=404)

    monkeypatch.setattr(polymarket, "fetch_book", _boom)
    book = polymarket.fetch_polymarket_venuebook("missing-market")

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.BOOK_UNAVAILABLE


def test_polymarket_invalid_env_depth_qty_min_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = Path(__file__).resolve().parents[1] / "venues" / "polymarket.py"
    monkeypatch.setenv("PM_DEPTH_QTY_MIN", "not-a-number")
    monkeypatch.setenv("PM_SPREAD_MAX", "0.05")

    spec = importlib.util.spec_from_file_location("polymarket_env_invalid_depth", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with pytest.raises(ValueError, match="PM_DEPTH_QTY_MIN"):
        spec.loader.exec_module(module)


def test_polymarket_invalid_env_spread_max_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = Path(__file__).resolve().parents[1] / "venues" / "polymarket.py"
    monkeypatch.setenv("PM_DEPTH_QTY_MIN", "100")
    monkeypatch.setenv("PM_SPREAD_MAX", "-0.1")

    spec = importlib.util.spec_from_file_location("polymarket_env_invalid_spread", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with pytest.raises(ValueError, match="PM_SPREAD_MAX"):
        spec.loader.exec_module(module)
