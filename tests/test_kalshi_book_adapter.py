import importlib.util
import json
from pathlib import Path
from typing import Optional

import pytest

import venues.kalshi as kalshi
from venuebook.types import BookFailReason, BookStatus
from venues.kalshi_fetch import KalshiFetchError

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "kalshi"


def _load_fixture(name: str) -> dict:
    path = FIXTURE_DIR / name
    with path.open("r") as f:
        return json.load(f)


def test_kalshi_adapter_ok_fixture() -> None:
    raw = _load_fixture("ok_book.json")
    book = kalshi.parse_kalshi_book(raw, ts=123.0)

    assert book.status == BookStatus.OK
    assert book.fail_reason is None
    assert isinstance(book.best_bid, float)
    assert isinstance(book.best_ask, float)


def test_kalshi_adapter_no_bbo_fixture() -> None:
    raw = _load_fixture("no_bbo.json")
    book = kalshi.parse_kalshi_book(raw, ts=123.0)

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.NO_BBO
    assert book.best_bid is None
    assert book.best_ask is None


def test_kalshi_adapter_depth_below_fixture() -> None:
    raw = _load_fixture("depth_below.json")
    book = kalshi.parse_kalshi_book(raw, ts=123.0)

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.DEPTH_BELOW_THRESHOLD
    assert book.best_bid is None
    assert book.best_ask is None


def test_kalshi_adapter_spread_wide_fixture() -> None:
    raw = _load_fixture("spread_wide.json")
    book = kalshi.parse_kalshi_book(raw, ts=123.0)

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.SPREAD_WIDE
    assert book.best_bid is None
    assert book.best_ask is None


def test_kalshi_adapter_ambiguous_fixture_fail_closed() -> None:
    raw = _load_fixture("ambiguous.json")
    book = kalshi.parse_kalshi_book(raw, ts=123.0)

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.PARSE_AMBIGUOUS
    assert book.best_bid is None
    assert book.best_ask is None


def test_kalshi_adapter_never_raises_on_fixtures() -> None:
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        raw = _load_fixture(path.name)
        book = kalshi.parse_kalshi_book(raw, ts=123.0)
        assert book.status in {BookStatus.OK, BookStatus.NO_TRADE}


def test_kalshi_fetch_failure_maps_to_book_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_: str, token: Optional[str] = None, timeout_s: float = 5.0) -> dict:
        raise KalshiFetchError("HTTP_404", status_code=404)

    monkeypatch.setattr(kalshi, "fetch_book", _boom)
    book = kalshi.fetch_kalshi_venuebook("missing-market")

    assert book.status == BookStatus.NO_TRADE
    assert book.fail_reason == BookFailReason.BOOK_UNAVAILABLE


def test_kalshi_invalid_env_depth_notional_min_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = Path(__file__).resolve().parents[1] / "venues" / "kalshi.py"
    monkeypatch.setenv("KALSHI_DEPTH_NOTIONAL_MIN", "not-a-number")
    monkeypatch.delenv("K_DEPTH_NOTIONAL_MIN", raising=False)
    monkeypatch.setenv("KALSHI_SPREAD_MAX", "0.05")
    monkeypatch.delenv("K_SPREAD_MAX", raising=False)

    spec = importlib.util.spec_from_file_location("kalshi_env_invalid_depth", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with pytest.raises(ValueError, match="KALSHI_DEPTH_NOTIONAL_MIN"):
        spec.loader.exec_module(module)


def test_kalshi_invalid_env_spread_max_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = Path(__file__).resolve().parents[1] / "venues" / "kalshi.py"
    monkeypatch.setenv("KALSHI_DEPTH_NOTIONAL_MIN", "100")
    monkeypatch.delenv("K_DEPTH_NOTIONAL_MIN", raising=False)
    monkeypatch.setenv("KALSHI_SPREAD_MAX", "-0.1")
    monkeypatch.delenv("K_SPREAD_MAX", raising=False)

    spec = importlib.util.spec_from_file_location("kalshi_env_invalid_spread", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with pytest.raises(ValueError, match="KALSHI_SPREAD_MAX"):
        spec.loader.exec_module(module)
